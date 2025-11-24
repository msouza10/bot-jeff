import asyncio
import logging
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Adiciona o diretório raiz ao path para importar os módulos
sys.path.append(os.getcwd())

from src.services.liquipedia_service import LiquipediaService

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    logger.info("Iniciando teste de busca de jogador na Liquipedia...")
    
    service = LiquipediaService()
    
    if not service.api_key:
        logger.error("LIQUIPEDIA_API_KEY não encontrada. Configure no .env para testar.")
        return

    player_name = "FalleN"
    logger.info(f"Buscando informações do jogador: {player_name}")
    
    player_data = await service.get_player(player_name)
    
    if player_data:
        logger.info("Jogador encontrado com sucesso!")
        logger.info(f"ID: {player_data.get('id')}")
        logger.info(f"Nome: {player_data.get('name')}")
        logger.info(f"Nacionalidade: {player_data.get('nationality')}")
        logger.info(f"Time: {player_data.get('team')}")
        logger.info(f"Imagem: {player_data.get('image')}")
    else:
        logger.warning(f"Jogador {player_name} não encontrado ou erro na API.")

if __name__ == "__main__":
    asyncio.run(main())
