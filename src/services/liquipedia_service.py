import aiohttp
import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from src.database.liquipedia_db import get_db_connection

logger = logging.getLogger(__name__)

class LiquipediaService:
    BASE_URL = "https://api.liquipedia.net/api/v3"
    RATE_LIMIT = 60  # requests per hour
    RATE_LIMIT_WINDOW = 3600  # seconds

    def __init__(self):
        self.api_key = os.getenv("LIQUIPEDIA_API_KEY")
        if not self.api_key:
            logger.warning("LIQUIPEDIA_API_KEY not found in environment variables.")
        
        self._rate_limit_lock = asyncio.Lock()
        self._request_timestamps = []

    async def _check_rate_limit(self):
        """Ensures we don't exceed 60 requests per hour."""
        logger.debug(f"⚡ Verificando rate limit...")
        async with self._rate_limit_lock:
            now = datetime.now()
            # Remove timestamps older than 1 hour
            self._request_timestamps = [ts for ts in self._request_timestamps if (now - ts).total_seconds() < self.RATE_LIMIT_WINDOW]
            
            if len(self._request_timestamps) >= self.RATE_LIMIT:
                wait_time = self.RATE_LIMIT_WINDOW - (now - self._request_timestamps[0]).total_seconds()
                logger.warning(f"⚠️ RATE LIMIT atingido! ({len(self._request_timestamps)}/{self.RATE_LIMIT} requisições). Aguardando {wait_time:.1f}s...")
                await asyncio.sleep(wait_time)
            else:
                logger.debug(f"✅ Rate limit OK ({len(self._request_timestamps)}/{self.RATE_LIMIT} requisições na última hora)")
            
            self._request_timestamps.append(now)

    async def _get_cached_response(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Retrieves cached response if valid."""
        logger.debug(f"🔍 Verificando cache da API para endpoint '{endpoint}' com params: {params}")
        params_str = json.dumps(params, sort_keys=True)
        async with get_db_connection() as db:
            async with db.execute(
                "SELECT response_json, expires_at FROM api_cache WHERE endpoint = ? AND params = ?",
                (endpoint, params_str)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    expires_at = datetime.fromisoformat(row[1])
                    if datetime.now() < expires_at:
                        logger.info(f"✅ Cache da API HIT para '{endpoint}' (expira em {expires_at.strftime('%Y-%m-%d %H:%M:%S')})")
                        return json.loads(row[0])
                    else:
                        logger.info(f"⏰ Cache da API EXPIRADO para '{endpoint}' (expirou em {expires_at.strftime('%Y-%m-%d %H:%M:%S')})")
        return None

    async def _cache_response(self, endpoint: str, params: Dict[str, Any], response: Dict[str, Any], ttl_minutes: int):
        """Caches an API response."""
        logger.debug(f"💾 Salvando resposta da API no cache para '{endpoint}' (TTL: {ttl_minutes} min)")
        params_str = json.dumps(params, sort_keys=True)
        expires_at = (datetime.now() + timedelta(minutes=ttl_minutes)).isoformat()
        
        try:
            async with get_db_connection() as db:
                await db.execute(
                    """
                    INSERT OR REPLACE INTO api_cache (endpoint, params, response_json, expires_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (endpoint, params_str, json.dumps(response), expires_at)
                )
                await db.commit()
                logger.info(f"✅ Resposta da API salva no cache para '{endpoint}'")
        except Exception as e:
            logger.error(f"❌ Erro ao salvar cache da API: {e}")

    async def _request(self, endpoint: str, params: Dict[str, Any] = None, ttl_minutes: int = 60) -> Optional[Dict[str, Any]]:
        """Makes a request to the Liquipedia API with caching and rate limiting."""
        if params is None:
            params = {}
        
        # Add wiki parameter if not present (default to counterstrike)
        if "wiki" not in params:
            params["wiki"] = "counterstrike"

        # Check cache first
        logger.debug(f"📡 Requisitando endpoint '{endpoint}' com params: {params}")
        cached_data = await self._get_cached_response(endpoint, params)
        if cached_data:
            return cached_data

        if not self.api_key:
            logger.error("Cannot make request: LIQUIPEDIA_API_KEY is missing.")
            return None

        await self._check_rate_limit()

        headers = {
            "Authorization": f"Apikey {self.api_key}",
            "User-Agent": "BOT Jeff/1.0 (Discord Bot; github.com/msouza10/bot-jeff; email@example.com)",
            "Accept-Encoding": "gzip"
        }

        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"✅ API Response 200 OK para '{endpoint}': {json.dumps(data)[:200]}...") # Log first 200 chars
                        await self._cache_response(endpoint, params, data, ttl_minutes)
                        return data
                    elif response.status == 429:
                        logger.error(f"❌ RATE LIMIT 429 da API Liquipedia para '{endpoint}'! Aguarde antes de tentar novamente.")
                        return None
                    elif response.status == 404:
                        error_data = await response.json()
                        logger.error(f"❌ Erro 404 da API Liquipedia para '{endpoint}': {error_data}")
                        return None
                    else:
                        logger.error(f"❌ Status code inesperado da API Liquipedia para '{endpoint}': {response.status} - {await response.text()}")
                        return None
        except Exception as e:
            logger.error(f"Exception during Liquipedia request: {e}")
        
        return None

    async def get_player(self, player_name: str):
        """Fetches player information by name (ID)."""
        logger.info(f"🎮 get_player('{player_name}') - Iniciando busca...")
        
        # PRIMEIRO: Verificar no banco de dados (cache estruturado)
        logger.debug(f"🔍 Verificando cache do banco para player '{player_name}'...")
        async with get_db_connection() as db:
            async with db.execute(
                "SELECT data_json FROM players WHERE id = ?",
                (player_name,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    logger.info(f"✅ Player '{player_name}' encontrado no CACHE DO BANCO!")
                    return json.loads(row[0])
        
        # SE NÃO ENCONTROU: Buscar da API
        logger.info(f"🌐 Player '{player_name}' NÃO encontrado no cache, buscando na API Liquipedia...")
        params = {
            "conditions": f"[[id::{player_name}]]",
            "limit": 1
        }
        
        data = await self._request("player", params, ttl_minutes=1440) # Cache for 24 hours
        
        if data and "result" in data and len(data["result"]) > 0:
            player_data = data["result"][0]
            
            # Helper para serializar JSON ou retornar None
            def to_json(val):
                return json.dumps(val) if val is not None else None
            
            # Save to specific players table for easier access
            async with get_db_connection() as db:
                await db.execute(
                    """
                    INSERT OR REPLACE INTO players (
                        id, pageid, pagename, alternateid, name, localizedname, type,
                        nationality, nationality2, nationality3, region, birthdate, deathdate,
                        teampagename, teamtemplate, links, status, earnings, earningsbyyear,
                        extradata, data_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        player_data.get("id"),
                        player_data.get("pageid"),
                        player_data.get("pagename"),
                        player_data.get("alternateid"),
                        player_data.get("name"),
                        player_data.get("localizedname"),
                        player_data.get("type"),
                        player_data.get("nationality"),
                        player_data.get("nationality2"),
                        player_data.get("nationality3"),
                        player_data.get("region"),
                        player_data.get("birthdate"),
                        player_data.get("deathdate"),
                        player_data.get("teampagename"),
                        player_data.get("teamtemplate"),
                        to_json(player_data.get("links")),
                        player_data.get("status"),
                        player_data.get("earnings"),
                        to_json(player_data.get("earningsbyyear")),
                        to_json(player_data.get("extradata")),
                        json.dumps(player_data)
                    )
                )
                await db.commit()
            
            logger.info(f"💾 Player '{player_name}' salvo no CACHE DO BANCO com sucesso!")
            return player_data
        
        logger.warning(f"⚠️ Player '{player_name}' NÃO encontrado na API Liquipedia.")
        return None

    async def get_team(self, team_name: str) -> Optional[Dict[str, Any]]:
        """Busca informações de um time na Liquipedia."""
        logger.info(f"🏆 get_team('{team_name}') - Iniciando busca...")
        
        # PRIMEIRO: Verificar no banco de dados (cache estruturado)
        logger.debug(f"🔍 Verificando cache do banco para team '{team_name}'...")
        async with get_db_connection() as db:
            async with db.execute(
                "SELECT data_json FROM teams WHERE id = ?",
                (team_name,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    logger.info(f"✅ Team '{team_name}' encontrado no CACHE DO BANCO!")
                    return json.loads(row[0])
        
        # SE NÃO ENCONTROU: Buscar da API
        logger.info(f"🌐 Team '{team_name}' NÃO encontrado no cache, buscando na API Liquipedia...")
        params = {
            "conditions": f"[[pagename::{team_name}]]",
            "limit": 1
        }
        
        data = await self._request("team", params, ttl_minutes=1440) # Cache for 24 hours
        
        if not data or "result" not in data or not data["result"]:
            return None
            
        team_data = data["result"][0]
        
        # Helper para serializar JSON ou retornar None
        def to_json(val):
            return json.dumps(val) if val is not None else None

        # Salva na tabela específica de times
        async with get_db_connection() as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO teams (
                    id, pageid, name, locations, region, logo, logourl, logodark, logodarkurl,
                    textlesslogourl, textlesslogodarkurl, status, createdate, disbanddate,
                    earnings, earningsbyyear, template, links, extradata, data_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    team_data.get("pagename"),
                    team_data.get("pageid"),
                    team_data.get("name"),
                    to_json(team_data.get("locations")),
                    team_data.get("region"),
                    team_data.get("logo"),
                    team_data.get("logourl"),
                    team_data.get("logodark"),
                    team_data.get("logodarkurl"),
                    team_data.get("textlesslogourl"),
                    team_data.get("textlesslogodarkurl"),
                    team_data.get("status"),
                    team_data.get("createdate"),
                    team_data.get("disbanddate"),
                    team_data.get("earnings"),
                    to_json(team_data.get("earningsbyyear")),
                    team_data.get("template"),
                    to_json(team_data.get("links")),
                    to_json(team_data.get("extradata")),
                    json.dumps(team_data)
                )
            )
            await db.commit()
            
        logger.info(f"💾 Team '{team_name}' salvo no CACHE DO BANCO com sucesso!")
        return team_data

    async def check_health(self) -> Dict:
        """
        Verifica a saúde da API Liquipedia.
        
        Returns:
            Dict com status e latência
        """
        start_time = datetime.now()
        try:
            # Tentar buscar um time conhecido para validar a API
            # Usando "Furia" como teste, pois é garantido existir
            params = {
                "conditions": "[[pagename::Furia]]",
                "limit": 1
            }
            # Usar _request diretamente para evitar lógica de cache do método get_team
            # mas ainda aproveitando o cache de requisição se existir
            await self._request("team", params, ttl_minutes=5)
            
            latency = (datetime.now() - start_time).total_seconds() * 1000
            return {"status": "ok", "latency": latency}
        except Exception as e:
            logger.error(f"✗ Erro no health check da Liquipedia API: {e}")
            return {"status": "error", "latency": 0, "error": str(e)}
