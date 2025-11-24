#!/usr/bin/env python3
"""
Script para testar chamadas à API da Liquipedia e salvar respostas em JSON.
Salva os arquivos em data/liquipedia_samples/
"""

import asyncio
import json
import os
from dotenv import load_dotenv
from datetime import datetime

# Adiciona o diretório raiz ao path
import sys
sys.path.append(os.getcwd())

from src.services.liquipedia_service import LiquipediaService

# Carregar variáveis de ambiente
load_dotenv()

# Criar diretório para samples se não existir
SAMPLE_DIR = "data/liquipedia_samples"
os.makedirs(SAMPLE_DIR, exist_ok=True)


async def save_player_sample(service: LiquipediaService, player_name: str):
    """Busca dados de um jogador e salva em JSON."""
    print(f"\n🎮 Buscando dados do jogador: {player_name}")
    
    player_data = await service.get_player(player_name)
    
    if player_data:
        filename = f"{SAMPLE_DIR}/player_{player_name.lower()}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(player_data, f, indent=2, ensure_ascii=False)
        print(f"✅ Salvo em: {filename}")
        print(f"📊 Campos disponíveis: {', '.join(player_data.keys())}")
    else:
        print(f"❌ Jogador {player_name} não encontrado")


async def save_team_sample(service: LiquipediaService, team_name: str):
    """Busca dados de um time e salva em JSON."""
    print(f"\n🏆 Buscando dados do time: {team_name}")
    
    team_data = await service.get_team(team_name)
    
    if team_data:
        filename = f"{SAMPLE_DIR}/team_{team_name.lower()}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(team_data, f, indent=2, ensure_ascii=False)
        print(f"✅ Salvo em: {filename}")
        print(f"📊 Campos disponíveis: {', '.join(team_data.keys())}")
    else:
        print(f"❌ Time {team_name} não encontrado")


async def main():
    print("=" * 60)
    print("🔬 Script de Teste da API Liquipedia")
    print("=" * 60)
    
    if not os.getenv("LIQUIPEDIA_API_KEY"):
        print("❌ LIQUIPEDIA_API_KEY não encontrada no .env")
        return
    
    service = LiquipediaService()
    
    # Lista de jogadores para testar
    players_to_test = [
        "FalleN",
        "s1mple",
        "ZywOo",
        "coldzera"
    ]
    
    # Lista de times para testar
    teams_to_test = [
        "FURIA",
        "Natus Vincere",
        "FaZe Clan",
        "G2 Esports"
    ]
    
    # Buscar jogadores
    print("\n" + "=" * 60)
    print("👥 BUSCANDO JOGADORES")
    print("=" * 60)
    
    for player in players_to_test:
        try:
            await save_player_sample(service, player)
            await asyncio.sleep(1)  # Delay para não bater no rate limit
        except Exception as e:
            print(f"❌ Erro ao buscar {player}: {e}")
    
    # Buscar times
    print("\n" + "=" * 60)
    print("🏆 BUSCANDO TIMES")
    print("=" * 60)
    
    for team in teams_to_test:
        try:
            await save_team_sample(service, team)
            await asyncio.sleep(1)  # Delay para não bater no rate limit
        except Exception as e:
            print(f"❌ Erro ao buscar {team}: {e}")
    
    # Criar arquivo resumo
    print("\n" + "=" * 60)
    print("📝 CRIANDO RESUMO")
    print("=" * 60)
    
    summary = {
        "timestamp": datetime.now().isoformat(),
        "samples_directory": SAMPLE_DIR,
        "players_tested": players_to_test,
        "teams_tested": teams_to_test,
        "notes": {
            "player_fields": "Veja player_*.json para campos completos",
            "team_fields": "Veja team_*.json para campos completos"
        }
    }
    
    summary_file = f"{SAMPLE_DIR}/README.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Resumo salvo em: {summary_file}")
    print("\n" + "=" * 60)
    print("✅ CONCLUÍDO!")
    print(f"📂 Arquivos salvos em: {SAMPLE_DIR}/")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
