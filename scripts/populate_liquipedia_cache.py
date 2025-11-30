#!/usr/bin/env python3
"""
Script para popular o cache da Liquipedia com times e jogadores Tier 1.
Ideal para rodar após limpar o banco ou para "aquecer" o cache.

Uso:
    python scripts/populate_liquipedia_cache.py
"""

import asyncio
import logging
import sys
import os
import time
from dotenv import load_dotenv

# Adicionar diretório raiz ao path
sys.path.append(os.getcwd())

from src.services.liquipedia_service import LiquipediaService

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("PopulateCache")

# Lista VIP de Times (Tier 1 / Brasileiros Populares)
VIP_TEAMS = [
    # Top Global
    "Natus Vincere", "Team Vitality", "G2 Esports", "Team Spirit", "MOUZ", 
    "FaZe Clan", "Team Liquid", "Astralis", "Virtus.pro", "Complexity",
    # Brasileiros / SA
    "FURIA Esports", "MIBR", "paiN Gaming", "Imperial Esports", "RED Canids",
    "Legacy", "Fluxo", "ODDIK", "BESTIA", "9z Team"
]

# Lista VIP de Jogadores (Stars / Brasileiros)
VIP_PLAYERS = [
    # Stars
    "s1mple", "ZywOo", "m0NESY", "donk", "NiKo", "ropz", "broky", "jL", "b1t",
    # Brasileiros
    "FalleN", "KSCERATO", "yuurih", "chelo", "skullz", "biguzera", "insani", "felps", "VINI", "arT"
]

async def populate():
    load_dotenv()
    
    if not os.getenv("LIQUIPEDIA_API_KEY"):
        logger.error("❌ LIQUIPEDIA_API_KEY não encontrada no .env")
        return

    service = LiquipediaService()
    
    print(f"\n🚀 Iniciando População do Cache Liquipedia")
    print(f"📋 Alvos: {len(VIP_TEAMS)} Times, {len(VIP_PLAYERS)} Jogadores")
    print(f"⏱️  Estimativa: {(len(VIP_TEAMS) + len(VIP_PLAYERS)) * 2} segundos (se não houver rate limit)")
    print("-" * 50)

    # 1. Popular Times
    print("\n🏆 Processando Times...")
    for i, team in enumerate(VIP_TEAMS, 1):
        try:
            logger.info(f"[{i}/{len(VIP_TEAMS)}] Buscando Time: {team}")
            start = time.time()
            data = await service.get_team(team)
            elapsed = time.time() - start
            
            if data:
                source = data.get('_cache_metadata', {}).get('source', 'unknown')
                print(f"   ✅ OK ({source}) - {elapsed:.2f}s")
            else:
                print(f"   ⚠️  Não encontrado")
            
            # Delay educado para não estourar o rate limit instantaneamente
            # O service já tem rate limit, mas isso ajuda a distribuir
            await asyncio.sleep(2) 
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar {team}: {e}")

    # 2. Popular Jogadores
    print("\n🎮 Processando Jogadores...")
    for i, player in enumerate(VIP_PLAYERS, 1):
        try:
            logger.info(f"[{i}/{len(VIP_PLAYERS)}] Buscando Jogador: {player}")
            start = time.time()
            data = await service.get_player(player)
            elapsed = time.time() - start
            
            if data:
                source = data.get('_cache_metadata', {}).get('source', 'unknown')
                print(f"   ✅ OK ({source}) - {elapsed:.2f}s")
            else:
                print(f"   ⚠️  Não encontrado")
            
            await asyncio.sleep(2)
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar {player}: {e}")

    print("\n" + "=" * 50)
    print("✅ Processo de população concluído!")
    print("=" * 50)

if __name__ == "__main__":
    try:
        asyncio.run(populate())
    except KeyboardInterrupt:
        print("\n🛑 Interrompido pelo usuário.")
