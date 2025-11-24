"""
Script para verificar a lógica de filtro por time.
Simula o funcionamento do cache_manager e do filtro em memória.
"""

import asyncio
import json
import logging
import sys
import os

# Adicionar diretório raiz ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Configurar logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Dados mockados de partidas
MOCK_MATCHES = [
    {
        "id": 1,
        "name": "FURIA vs MIBR",
        "status": "not_started",
        "opponents": [
            {"opponent": {"name": "FURIA"}},
            {"opponent": {"name": "MIBR"}}
        ]
    },
    {
        "id": 2,
        "name": "Liquid vs FaZe",
        "status": "not_started",
        "opponents": [
            {"opponent": {"name": "Team Liquid"}},
            {"opponent": {"name": "FaZe Clan"}}
        ]
    },
    {
        "id": 3,
        "name": "Imperial vs paiN",
        "status": "running",
        "opponents": [
            {"opponent": {"name": "Imperial"}},
            {"opponent": {"name": "paiN Gaming"}}
        ]
    }
]

def filter_matches(matches, team_name):
    """Lógica de filtro duplicada do MatchesCog para teste isolado."""
    if not team_name:
        return matches
        
    team_name_lower = team_name.lower()
    filtered = []
    for match in matches:
        # Verificar nos oponentes
        found = False
        for opponent in match.get("opponents", []):
            opp_name = opponent.get("opponent", {}).get("name", "").lower()
            if team_name_lower in opp_name:
                found = True
                break
        
        # Verificar no nome da partida
        if not found and team_name_lower in match.get("name", "").lower():
            found = True
            
        if found:
            filtered.append(match)
    return filtered

async def main():
    logger.info("🧪 Iniciando teste de filtro de times...")
    
    # Teste 1: Filtro exato
    logger.info("\n🔹 Teste 1: Filtro 'FURIA'")
    results = filter_matches(MOCK_MATCHES, "FURIA")
    assert len(results) == 1
    assert results[0]["name"] == "FURIA vs MIBR"
    logger.info("✅ Passou")
    
    # Teste 2: Filtro parcial (case insensitive)
    logger.info("\n🔹 Teste 2: Filtro 'liquid'")
    results = filter_matches(MOCK_MATCHES, "liquid")
    assert len(results) == 1
    assert results[0]["name"] == "Liquid vs FaZe"
    logger.info("✅ Passou")
    
    # Teste 3: Filtro sem match
    logger.info("\n🔹 Teste 3: Filtro 'Navi'")
    results = filter_matches(MOCK_MATCHES, "Navi")
    assert len(results) == 0
    logger.info("✅ Passou")
    
    # Teste 4: Filtro vazio (retorna tudo)
    logger.info("\n🔹 Teste 4: Filtro None")
    results = filter_matches(MOCK_MATCHES, None)
    assert len(results) == 3
    logger.info("✅ Passou")

    logger.info("\n🎉 Todos os testes passaram!")

if __name__ == "__main__":
    asyncio.run(main())
