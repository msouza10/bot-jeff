import asyncio
import logging
import os
import sys
import json
from dotenv import load_dotenv

# Adiciona o diretório raiz ao path para importar os módulos
sys.path.append(os.getcwd())

from src.services.liquipedia_service import LiquipediaService

# Configuração de Logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    load_dotenv()
    
    if not os.getenv("LIQUIPEDIA_API_KEY"):
        logger.error("LIQUIPEDIA_API_KEY não encontrada. Configure no .env para testar.")
        return

    service = LiquipediaService()
    
    team_name = "FURIA Esports" # Tentando nome exato da página, ou apenas FURIA
    logger.info(f"Buscando informações do time: {team_name}")
    
    # Primeiro tenta com o nome exato
    team_data = await service.get_team(team_name)
    
    if not team_data:
        logger.info(f"Tentando apenas 'FURIA'...")
        team_data = await service.get_team("FURIA")

    if team_data:
        logger.info("Time encontrado com sucesso!")
        logger.info(f"JSON Completo: {json.dumps(team_data, indent=2)}")
    else:
        logger.warning(f"Time {team_name} não encontrado ou erro na API.")

if __name__ == "__main__":
    asyncio.run(main())
