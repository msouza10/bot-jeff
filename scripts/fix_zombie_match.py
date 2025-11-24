"""
Script para remover a partida 1265923 do cache.
"""

import asyncio
import logging
import sys
import os
import libsql_client

# Adicionar diretório raiz ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Configurar logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

DB_URL = "file:data/bot.db"

async def main():
    logger.info(f"🗑️ Removendo partida 1265923 de {DB_URL}...")
    
    async with libsql_client.create_client(url=DB_URL) as client:
        await client.execute("DELETE FROM matches_cache WHERE match_id = 1265923")
        logger.info("✅ Partida removida com sucesso!")

if __name__ == "__main__":
    asyncio.run(main())
