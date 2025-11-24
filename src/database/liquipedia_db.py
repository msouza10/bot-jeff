import aiosqlite
import os
import logging

from contextlib import asynccontextmanager

# Configuração de Logs
logger = logging.getLogger(__name__)

DB_PATH = os.path.join("data", "liquipedia_cache.db")
SCHEMA_PATH = os.path.join("src", "database", "liquipedia_schema.sql")

@asynccontextmanager
async def get_db_connection():
    """Retorna uma conexão com o banco de dados de cache da Liquipedia."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db

async def init_db():
    """Inicializa o banco de dados de cache da Liquipedia com o schema."""
    if not os.path.exists("data"):
        os.makedirs("data")

    logger.info(f"Inicializando banco de dados Liquipedia em {DB_PATH}...")
    
    async with aiosqlite.connect(DB_PATH) as db:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema = f.read()
        
        await db.executescript(schema)
        await db.commit()
    
    logger.info("Banco de dados Liquipedia inicializado com sucesso.")

if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    asyncio.run(init_db())
