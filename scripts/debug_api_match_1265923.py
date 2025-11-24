"""
Script para verificar em quais endpoints da API a partida 1265923 aparece.
"""

import asyncio
import logging
import sys
import os
from dotenv import load_dotenv

# Adicionar diretório raiz ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.services.pandascore_service import PandaScoreClient

# Configurar logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

async def main():
    load_dotenv()
    api_client = PandaScoreClient()
    
    match_id = 1265923
    logger.info(f"🔍 Buscando partida {match_id} na API...")
    
    # 1. Buscar detalhes diretos
    logger.info("\n1. Detalhes diretos (/matches/{id}):")
    details = await api_client.get_match_details(match_id)
    if details:
        logger.info(f"   Status: {details.get('status')}")
        logger.info(f"   Begin At: {details.get('begin_at')}")
        logger.info(f"   End At: {details.get('end_at')}")
    else:
        logger.warning("   ❌ Não encontrada!")

    # 2. Buscar em Upcoming
    logger.info("\n2. Buscando em Upcoming (limit 100):")
    upcoming = await api_client.get_upcoming_matches(per_page=100)
    found_upcoming = next((m for m in upcoming if m['id'] == match_id), None)
    if found_upcoming:
        logger.warning(f"   ⚠️ ENCONTRADA EM UPCOMING! Status: {found_upcoming.get('status')}")
    else:
        logger.info("   ✅ Não encontrada em Upcoming")

    # 3. Buscar em Running
    logger.info("\n3. Buscando em Running:")
    running = await api_client.get_running_matches()
    found_running = next((m for m in running if m['id'] == match_id), None)
    if found_running:
        logger.warning(f"   ⚠️ ENCONTRADA EM RUNNING! Status: {found_running.get('status')}")
    else:
        logger.info("   ✅ Não encontrada em Running")

    # 4. Buscar em Past
    logger.info("\n4. Buscando em Past (limit 100):")
    past = await api_client.get_past_matches(per_page=100)
    found_past = next((m for m in past if m['id'] == match_id), None)
    if found_past:
        logger.info(f"   ✅ ENCONTRADA EM PAST! Status: {found_past.get('status')}")
    else:
        logger.warning("   ❌ Não encontrada em Past")

    await api_client.close()

if __name__ == "__main__":
    asyncio.run(main())
