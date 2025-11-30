import asyncio
import os
import sys
import json
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.getcwd())

from src.services.liquipedia_service import LiquipediaService

async def generate():
    """
    Gera lista de cache automaticamente da API da Liquipedia.
    
    Estratégia FINAL:
    1. Buscar top teams ativos ordenados por earnings
    2. Para cada team, buscar jogadores usando filtro [[teampagename::Team_Name]]
    3. Adicionar teams participantes das partidas da PandaScore
    """
    
    liquipedia = LiquipediaService()
    
    teams_to_cache = set()
    players_to_cache = set()
    
    # 1. Buscar top teams da Liquipedia (por earnings = times mais importantes)
    print("📊 Fetching top teams from Liquipedia by earnings...")
    
    # Limitando a 40 para evitar rate limit (já que cada time gera +1 request)
    team_params = {
        "wiki": "counterstrike",
        "conditions": "[[status::active]]",
        "limit": 40,
        "order": "earnings DESC"
    }
    
    try:
        team_data = await liquipedia._request("team", team_params, ttl_minutes=1440)
        
        if team_data and "result" in team_data:
            teams = team_data["result"]
            print(f"   ✅ Found {len(teams)} active teams")
            
            # Adicionar todos os times
            for team in teams:
                # Preferir pagename para usar na busca de jogadores
                team_name = team.get('pagename') or team.get('name')
                if team_name:
                    # Normalizar nome para cache (espaços vs underscores)
                    # A API retorna pagename com underscores (ex: FaZe_Clan)
                    # Mas para exibição/cache talvez queiramos o nome normal
                    # Vamos guardar o pagename para busca de players e o name para o cache de times
                    display_name = team.get('name', team_name)
                    teams_to_cache.add(display_name)
                    
                    # Se pagename for diferente, adicionar também para garantir
                    if team.get('pagename'):
                         teams_to_cache.add(team.get('pagename'))
            
            print(f"   📊 {len(teams_to_cache)} teams added to cache list")
        else:
            print("   ⚠️ No teams found")
            
    except Exception as e:
        print(f"   ❌ Error fetching teams: {e}")
    
    # 2. Buscar jogadores para os top teams
    # Vamos usar os pagenames que vieram da busca anterior
    print(f"\n🎮 Fetching players for top teams...")
    
    # Filtrar apenas nomes que parecem pagenames (com underscore) ou usar a lista original
    # Para simplificar, vamos iterar sobre os resultados originais da API
    
    if team_data and "result" in team_data:
        teams_list = team_data["result"]
        total_teams = len(teams_list)
        
        for i, team in enumerate(teams_list, 1):
            team_pagename = team.get('pagename')
            team_name = team.get('name', team_pagename)
            
            if not team_pagename:
                continue
                
            print(f"   [{i}/{total_teams}] Fetching players for {team_name} ({team_pagename})...")
            
            try:
                # Buscar jogadores deste time
                # Nota: Status de player é "Active" (Capitalized), diferente de team que é "active"
                player_params = {
                    "wiki": "counterstrike",
                    "conditions": f"[[teampagename::{team_pagename}]] AND [[status::Active]]",
                    "limit": 10
                }
                
                player_data = await liquipedia._request("player", player_params, ttl_minutes=1440)
                
                if player_data and "result" in player_data:
                    players = player_data["result"]
                    count = 0
                    for player in players:
                        player_id = player.get('id')
                        if player_id:
                            players_to_cache.add(player_id)
                            count += 1
                    
                    print(f"      ✅ Found {count} players")
                else:
                    print(f"      ⚠️ No players found")
                
                # Delay inteligente: A API permite 60 req/h (1 a cada 60s) para chaves normais?
                # Não, a doc diz "Up to 1 request per 2 seconds". 
                # Mas o LiquipediaService já tem rate limiter.
                # Vamos adicionar um pequeno sleep extra por segurança.
                await asyncio.sleep(1.5)
                
            except Exception as e:
                print(f"      ❌ Error: {e}")
    
    print(f"\n   👤 Total players found: {len(players_to_cache)}")
    
    # 3. Adicionar times das partidas da PandaScore (se disponível)
    try:
        from src.services.pandascore_service import PandaScoreClient
        
        print(f"\n📡 Fetching teams from PandaScore matches...")
        client = PandaScoreClient()
        
        # Buscar apenas partidas futuras e running para ser mais rápido
        upcoming = await client.get_upcoming_matches(per_page=50)
        running = await client.get_running_matches()
        
        all_matches = upcoming + running
        print(f"   ✅ Found {len(all_matches)} matches")
        
        for match in all_matches:
            for opponent in match.get('opponents', []):
                team = opponent.get('opponent', {})
                team_name = team.get('name')
                if team_name:
                    teams_to_cache.add(team_name)
        
        print(f"   📊 Total teams after PandaScore: {len(teams_to_cache)}")
        
    except Exception as e:
        print(f"   ⚠️ Could not fetch from PandaScore: {e}")
    
    # 4. Salvar no arquivo
    os.makedirs('src/config', exist_ok=True)
    filepath = 'src/config/gen_cache.txt'
    
    with open(filepath, 'w') as f:
        # Primeiro os times
        for team in sorted(teams_to_cache):
            f.write(f"Team:{team}\n")
        
        # Depois os jogadores
        for player in sorted(players_to_cache):
            f.write(f"Player:{player}\n")
   
    print(f"\n" + "="*60)
    print(f"✅ Generated cache list in {filepath}")
    print(f"   📊 {len(teams_to_cache)} teams")
    print(f"   👤 {len(players_to_cache)} players")
    print(f"   📝 Total: {len(teams_to_cache) + len(players_to_cache)} entries")
    print(f"="*60)
    print(f"\n💡 Next step: python scripts/populate_from_list.py")

if __name__ == "__main__":
    asyncio.run(generate())
