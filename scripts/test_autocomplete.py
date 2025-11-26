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

async def test_autocomplete():
    service = LiquipediaService()
    
    print("\n--- Testando Autocomplete de Jogadores ---")
    # Buscar algo que sabemos que existe (FalleN)
    query = "Fall"
    results = await service.search_players(query)
    print(f"Query: '{query}' -> Resultados: {results}")
    
    if "FalleN" in results or "fallen" in results:
        print("✅ Autocomplete de jogador funcionou!")
    else:
        print("⚠️ Autocomplete de jogador não retornou 'FalleN'.")

    print("\n--- Testando Autocomplete de Times ---")
    # Buscar algo que sabemos que existe (FURIA)
    query = "FUR"
    results = await service.search_teams(query)
    print(f"Query: '{query}' -> Resultados: {results}")
    
    if "FURIA Esports" in results or "FURIA" in results:
        print("✅ Autocomplete de time funcionou!")
    else:
        print("⚠️ Autocomplete de time não retornou 'FURIA'.")

    # 3. Testar Autocomplete Vazio
    print("\n--- Testando Autocomplete Vazio (Últimos) ---")
    empty_results = await service.search_players("")
    print(f"Query: '' -> Resultados: {empty_results}")
    
    if len(empty_results) > 0:
        print("✅ Autocomplete vazio retornou resultados!")
    else:
        print("⚠️ Autocomplete vazio não retornou nada.")

if __name__ == "__main__":
    asyncio.run(test_autocomplete())
