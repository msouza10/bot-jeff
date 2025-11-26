import asyncio
import logging
import sys
import os
from dotenv import load_dotenv

load_dotenv()

# Adicionar diretório raiz ao path
sys.path.append(os.getcwd())

from src.services.liquipedia_service import LiquipediaService

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def populate():
    service = LiquipediaService()
    
    if not service.api_key:
        logger.error("LIQUIPEDIA_API_KEY não encontrada.")
        return

    print("\n--- Populando Cache ---")
    
    # 1. Buscar Jogador (Normalization check: lowercase)
    player_name = "fallen" 
    logger.info(f"Buscando jogador: {player_name}")
    await service.get_player(player_name)

    # 2. Buscar Time
    team_name = "FURIA"
    logger.info(f"Buscando time: {team_name}")
    await service.get_team(team_name)
    
    print("✅ Cache populado!")

if __name__ == "__main__":
    asyncio.run(populate())
