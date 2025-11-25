"""
Cliente para integração com a PandaScore API.
Fornece métodos para buscar dados de partidas de CS2.
"""

import aiohttp
import os
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class PandaScoreClient:
    """Cliente assíncrono para a API PandaScore."""
    
    BASE_URL = "https://api.pandascore.co"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa o cliente PandaScore.
        
        Args:
            api_key: Token da API PandaScore. Se None, busca de PANDASCORE_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("PANDASCORE_API_KEY")
        if not self.api_key:
            raise ValueError("PandaScore API key não configurada!")
        
        self.session: Optional[aiohttp.ClientSession] = None
        self._headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Retorna ou cria uma sessão HTTP."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(headers=self._headers)
        return self.session
    
    async def _request(self, endpoint: str, params: Optional[Dict] = None) -> List[Dict]:
        """
        Faz requisição à API PandaScore.
        
        Args:
            endpoint: Endpoint da API (ex: '/csgo/matches/upcoming')
            params: Parâmetros query string
            
        Returns:
            Lista de dicionários com os dados retornados
        """
        session = await self._get_session()
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                logger.info(f"✓ Requisição bem-sucedida: {endpoint}")
                return data if isinstance(data, list) else [data]
                
        except aiohttp.ClientResponseError as e:
            logger.error(f"✗ Erro HTTP {e.status}: {endpoint}")
            if e.status == 401:
                logger.error("Token da API inválido ou expirado!")
            elif e.status == 429:
                logger.error("Rate limit excedido! Aguarde alguns minutos.")
            return []
            
        except aiohttp.ClientError as e:
            logger.error(f"✗ Erro de conexão: {e}")
            return []
        
        except Exception as e:
            logger.error(f"✗ Erro inesperado: {e}")
            return []
    
    async def get_upcoming_matches(self, per_page: int = 10) -> List[Dict]:
        """
        Busca próximas partidas de CS2.
        
        Args:
            per_page: Número de partidas a retornar (máx: 100)
            
        Returns:
            Lista de partidas futuras
        """
        params = {
            "filter[status]": "not_started",
            "sort": "scheduled_at",
            "per_page": min(per_page, 100)
        }
        return await self._request("/csgo/matches/upcoming", params)
    
    async def get_running_matches(self) -> List[Dict]:
        """
        Busca partidas de CS2 ao vivo.
        
        Returns:
            Lista de partidas em andamento
        """
        params = {"filter[status]": "running"}
        return await self._request("/csgo/matches/running", params)
    
    async def get_past_matches(self, hours: int = 24, per_page: int = 10, page: int = 1) -> List[Dict]:
        """
        Busca partidas finalizadas recentemente.
        
        Args:
            hours: Buscar partidas das últimas X horas (não usado na API)
            per_page: Número de partidas a retornar por página
            page: Número da página (padrão: 1)
            
        Returns:
            Lista de partidas finalizadas
        """
        # A API PandaScore retorna as partidas passadas ordenadas por data
        # Não precisa filtrar por data, ela já retorna as mais recentes
        # IMPORTANTE: filtrar por status=finished para excluir canceladas
        # OTIMIZAÇÃO: Buscar 100 por página para melhor cobertura
        actual_per_page = min(per_page, 100)
        params = {
            "filter[status]": "finished",
            "sort": "-end_at",
            "per_page": actual_per_page,
            "page": page
        }
        return await self._request("/csgo/matches/past", params)
    
    async def get_canceled_matches(self, per_page: int = 10) -> List[Dict]:
        """
        Busca partidas canceladas ou adiadas recentemente.
        
        Args:
            per_page: Número de partidas a retornar
            
        Returns:
            Lista de partidas canceladas/adiadas
        """
        params = {
            "filter[status]": "canceled,postponed",
            "sort": "-updated_at",
            "per_page": min(per_page, 100)
        }
        return await self._request("/csgo/matches/past", params)
    
    async def get_match_details(self, match_id: int) -> Optional[Dict]:
        """
        Busca detalhes de uma partida específica.
        
        Args:
            match_id: ID da partida
            
        Returns:
            Dados da partida ou None se não encontrada
        """
        result = await self._request(f"/csgo/matches/{match_id}")
        return result[0] if result else None
    
    async def close(self):
        """Fecha a sessão HTTP."""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("✓ Sessão PandaScore fechada")

    async def check_health(self) -> Dict:
        """
        Verifica a saúde da API PandaScore.
        
        Returns:
            Dict com status e latência
        """
        start_time = datetime.now()
        try:
            # Requisição leve para verificar conectividade
            await self.get_upcoming_matches(per_page=1)
            latency = (datetime.now() - start_time).total_seconds() * 1000
            return {"status": "ok", "latency": latency}
        except Exception as e:
            logger.error(f"✗ Erro no health check da PandaScore API: {e}")
            return {"status": "error", "latency": 0, "error": str(e)}
