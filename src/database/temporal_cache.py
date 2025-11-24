"""
🕐 Gestor de Cache Temporal (42 horas)
Mantém o cache com cobertura de exatamente 42 horas usando datas da API
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
import json

logger = logging.getLogger(__name__)


class TemporalCacheManager:
    """Gerencia cache com cobertura temporal de 42 horas."""
    
    # Janela temporal alvo
    CACHE_WINDOW_HOURS = 42
    
    @staticmethod
    def get_temporal_window() -> Tuple[datetime, datetime]:
        """
        Retorna a janela temporal de 42 horas.
        
        Returns:
            (start_time, end_time) em UTC com timezone info
        """
        # Usar UTC timezone-aware
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=TemporalCacheManager.CACHE_WINDOW_HOURS)
        return start_time, end_time
    
    @staticmethod
    def parse_api_datetime(dt_str: Optional[str]) -> Optional[datetime]:
        """
        Parse datetime da API PandaScore (ISO 8601 format).
        
        Args:
            dt_str: String com data (ex: "2025-11-16T13:15:35Z")
            
        Returns:
            datetime ou None
        """
        if not dt_str:
            return None
        
        try:
            # Remove 'Z' e substitui por +00:00
            if dt_str.endswith('Z'):
                dt_str = dt_str[:-1] + '+00:00'
            
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except Exception as e:
            logger.warning(f"⚠️ Erro ao fazer parse de data: {dt_str} - {e}")
            return None
    
    @staticmethod
    def get_match_temporal_anchor(match: Dict) -> Optional[datetime]:
        """
        Retorna o timestamp de referência de uma partida.
        Usa end_at (partida finalizada), begin_at (agendada) ou updated_at.
        
        Args:
            match: Dados da partida
            
        Returns:
            datetime ou None
        """
        # Prioridade: end_at > begin_at > updated_at
        if match.get('end_at'):
            return TemporalCacheManager.parse_api_datetime(match['end_at'])
        
        if match.get('begin_at'):
            return TemporalCacheManager.parse_api_datetime(match['begin_at'])
        
        return None
    
    @staticmethod
    def is_within_temporal_window(match: Dict) -> bool:
        """
        Verifica se uma partida está dentro da janela de 42 horas.
        
        Args:
            match: Dados da partida
            
        Returns:
            True se a partida deve estar no cache
        """
        anchor = TemporalCacheManager.get_match_temporal_anchor(match)
        if not anchor:
            logger.debug(f"⚠️ Match {match.get('id')} sem data de referência")
            return True  # Se sem data, manter no cache
        
        start_time, _ = TemporalCacheManager.get_temporal_window()
        # Manter se for mais recente que o limite de corte (incluindo futuro)
        return anchor >= start_time


async def cleanup_expired_cache(client) -> Dict:
    """
    Remove partidas mais antigas que 42 horas do cache.
    
    Args:
        client: Cliente libSQL
        
    Returns:
        Dict com estatísticas da limpeza
    """
    stats = {
        "total_before": 0,
        "deleted": 0,
        "by_status": {},
        "total_after": 0
    }
    
    try:
        # Contar antes
        result = await client.execute("SELECT COUNT(*) as count FROM matches_cache")
        stats["total_before"] = result.rows[0][0] if result.rows else 0
        
        logger.info(f"🧹 Iniciando limpeza temporal de cache ({stats['total_before']} partidas)")
        
        # Buscar todas as partidas
        result = await client.execute("SELECT match_id, match_data, status FROM matches_cache")
        
        cutoff_time, _ = TemporalCacheManager.get_temporal_window()
        cutoff_iso = cutoff_time.isoformat() + "Z"
        
        deleted_count = 0
        
        for match_id, match_data_json, status in result.rows:
            try:
                match_data = json.loads(match_data_json)
                
                # Checar se está fora da janela
                if not TemporalCacheManager.is_within_temporal_window(match_data):
                    await client.execute(
                        "DELETE FROM matches_cache WHERE match_id = ?",
                        [match_id]
                    )
                    deleted_count += 1
                    
                    # Contabilizar por status
                    if status not in stats["by_status"]:
                        stats["by_status"][status] = 0
                    stats["by_status"][status] += 1
                    
                    anchor = TemporalCacheManager.get_match_temporal_anchor(match_data)
                    logger.debug(f"   🗑️ Deletado: {match_id} ({status}) - Anchor: {anchor}")
                    
            except Exception as e:
                logger.error(f"✗ Erro ao processar match {match_id}: {e}")
        
        stats["deleted"] = deleted_count
        
        # Contar depois
        result = await client.execute("SELECT COUNT(*) as count FROM matches_cache")
        stats["total_after"] = result.rows[0][0] if result.rows else 0
        
        logger.info(f"✅ Limpeza concluída:")
        logger.info(f"   Antes: {stats['total_before']} partidas")
        logger.info(f"   Deletadas: {deleted_count}")
        logger.info(f"   Depois: {stats['total_after']} partidas")
        logger.info(f"   Por status: {stats['by_status']}")
        
        return stats
        
    except Exception as e:
        logger.error(f"✗ Erro durante limpeza de cache: {e}")
        raise


async def ensure_temporal_coverage(
    client,
    api_client,
    minimum_hours: int = 42,
    target_partition_hours: int = 12
) -> Dict:
    """
    Garante que o cache tem cobertura temporal mínima.
    Busca mais dados da API se necessário.
    
    Args:
        client: Cliente libSQL
        api_client: Cliente PandaScore
        minimum_hours: Horas mínimas de cobertura desejada (padrão: 42)
        target_partition_hours: Partição para busca (busca em blocos de X horas)
        
    Returns:
        Dict com estatísticas de cobertura
    """
    stats = {
        "current_coverage_hours": 0,
        "pages_fetched": 0,
        "matches_added": 0,
        "coverage_status": "unknown",
        "oldest_match": None,
        "newest_match": None
    }
    
    try:
        # 1. Analisar cobertura atual
        result = await client.execute("""
            SELECT 
                MIN(CASE 
                    WHEN end_at IS NOT NULL THEN end_at
                    WHEN begin_at IS NOT NULL THEN begin_at
                    ELSE updated_at
                END) as oldest_timestamp,
                MAX(CASE 
                    WHEN end_at IS NOT NULL THEN end_at
                    WHEN begin_at IS NOT NULL THEN begin_at
                    ELSE updated_at
                END) as newest_timestamp
            FROM matches_cache
        """)
        
        if result.rows and result.rows[0][0]:
            oldest_str, newest_str = result.rows[0]
            oldest = TemporalCacheManager.parse_api_datetime(oldest_str)
            newest = TemporalCacheManager.parse_api_datetime(newest_str)
            
            if oldest and newest:
                # Garantir que ambos são timezone-aware para subtração
                if oldest.tzinfo is None:
                    oldest = oldest.replace(tzinfo=timezone.utc)
                if newest.tzinfo is None:
                    newest = newest.replace(tzinfo=timezone.utc)
                
                current_coverage = (newest - oldest).total_seconds() / 3600
                stats["current_coverage_hours"] = round(current_coverage, 1)
                stats["oldest_match"] = oldest_str
                stats["newest_match"] = newest_str
                
                logger.info(f"📊 Cobertura atual: {stats['current_coverage_hours']:.1f} horas")
                logger.info(f"   Mais antigo: {oldest_str}")
                logger.info(f"   Mais recente: {newest_str}")
                
                if current_coverage >= minimum_hours:
                    stats["coverage_status"] = "sufficient"
                    logger.info(f"✅ Cobertura suficiente ({current_coverage:.1f}h >= {minimum_hours}h)")
                    return stats
                else:
                    stats["coverage_status"] = "insufficient"
                    logger.warning(f"⚠️ Cobertura insuficiente ({current_coverage:.1f}h < {minimum_hours}h)")
        else:
            logger.info("ℹ️ Cache vazio, iniciando população...")
            stats["coverage_status"] = "empty"
        
        # 2. Buscar mais dados até atingir cobertura
        logger.info(f"🔍 Buscando partidas para atingir {minimum_hours}h de cobertura...")
        
        page = 1
        total_added = 0
        
        while stats["current_coverage_hours"] < minimum_hours and page <= 20:
            logger.info(f"   📄 Página {page}...")
            
            # Buscar página de finished
            page_matches = await api_client.get_past_matches(per_page=100, page=page)
            
            if not page_matches:
                logger.info(f"   Fim da API (página {page} vazia)")
                break
            
            # Armazenar matches
            inserted = 0
            for match in page_matches:
                # Usar INSERT com ON CONFLICT para não duplicar
                match_id = match.get("id")
                match_data = json.dumps(match)
                status = match.get("status", "finished")
                tournament_name = match.get("tournament", {}).get("name")
                begin_at = match.get("begin_at")
                end_at = match.get("end_at")
                
                await client.execute("""
                    INSERT INTO matches_cache 
                        (match_id, match_data, status, tournament_name, begin_at, end_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(match_id) DO NOTHING
                """, [match_id, match_data, status, tournament_name, begin_at, end_at])
                
                inserted += 1
                total_added += 1
            
            logger.info(f"      ✅ {inserted} partidas adicionadas")
            
            # Recalcular cobertura
            result = await client.execute("""
                SELECT 
                    MIN(CASE 
                        WHEN end_at IS NOT NULL THEN end_at
                        WHEN begin_at IS NOT NULL THEN begin_at
                        ELSE updated_at
                    END) as oldest_timestamp,
                    MAX(CASE 
                        WHEN end_at IS NOT NULL THEN end_at
                        WHEN begin_at IS NOT NULL THEN begin_at
                        ELSE updated_at
                    END) as newest_timestamp
                FROM matches_cache
            """)
            
            if result.rows and result.rows[0][0]:
                oldest_str, newest_str = result.rows[0]
                oldest = TemporalCacheManager.parse_api_datetime(oldest_str)
                newest = TemporalCacheManager.parse_api_datetime(newest_str)
                
                if oldest and newest:
                    # Garantir que ambos são timezone-aware para subtração
                    if oldest.tzinfo is None:
                        oldest = oldest.replace(tzinfo=timezone.utc)
                    if newest.tzinfo is None:
                        newest = newest.replace(tzinfo=timezone.utc)
                    
                    current_coverage = (newest - oldest).total_seconds() / 3600
                    stats["current_coverage_hours"] = round(current_coverage, 1)
            
            page += 1
            stats["pages_fetched"] += 1
        
        stats["matches_added"] = total_added
        
        if stats["current_coverage_hours"] >= minimum_hours:
            stats["coverage_status"] = "sufficient"
            logger.info(f"✅ Cobertura atingida: {stats['current_coverage_hours']:.1f}h >= {minimum_hours}h")
        else:
            stats["coverage_status"] = "best_effort"
            logger.warning(f"⚠️ Cobertura máxima atingida: {stats['current_coverage_hours']:.1f}h (esperado: {minimum_hours}h)")
        
        return stats
        
    except Exception as e:
        logger.error(f"✗ Erro ao garantir cobertura temporal: {e}")
        raise
