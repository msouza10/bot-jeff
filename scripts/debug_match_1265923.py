"""
Script para debugar o estado da partida 1265923 no banco de dados.
"""

import asyncio
import json
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
    logger.info(f"🔍 Inspecionando partida 1265923 em {DB_URL}...")
    
    async with libsql_client.create_client(url=DB_URL) as client:
        # 1. Verificar registro na tabela matches_cache
        result = await client.execute("SELECT * FROM matches_cache WHERE match_id = 1265923")
        
        if not result.rows:
            logger.warning("❌ Partida 1265923 NÃO encontrada no banco de dados!")
        else:
            row = result.rows[0]
            logger.info("✅ Partida encontrada!")
            logger.info(f"   Status: {row['status']}")
            logger.info(f"   Updated At: {row['updated_at']}")
            logger.info(f"   Begin At: {row['begin_at']}")
            logger.info(f"   End At: {row['end_at']}")
            
            # Parse JSON para ver detalhes
            try:
                data = json.loads(row['match_data'])
                logger.info(f"   JSON Status: {data.get('status')}")
                logger.info(f"   JSON Name: {data.get('name')}")
            except Exception as e:
                logger.error(f"   Erro ao ler JSON: {e}")

        # 2. Verificar se existe duplicidade (não deveria, pois é PK/Unique)
        count = await client.execute("SELECT COUNT(*) FROM matches_cache WHERE match_id = 1265923")
        logger.info(f"📊 Total de registros para este ID: {count.rows[0][0]}")

if __name__ == "__main__":
    asyncio.run(main())
