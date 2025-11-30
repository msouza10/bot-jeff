import asyncio
import os
import sys
import json
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.getcwd())

from src.services.liquipedia_service import LiquipediaService

async def inspect():
    """
    Testar endpoint /v3/player para ver se conseguimos buscar jogadores por time.
    """
    
    liquipedia = LiquipediaService()
    
    # Testar buscar jogadores de times específicos
    test_teams = [
        "Natus Vincere",
        "FaZe Clan", 
        "G2 Esports"
    ]
    
    print("🔍 Testando busca de jogadores por time\n")
    print("="*80)
    
    for team_name in test_teams:
        print(f"\n{'='*80}")
        print(f"🏆 BUSCANDO JOGADORES DO TIME: {team_name}")
        print(f"{'='*80}\n")
        
        try:
            # Tentar buscar jogadores por teampagename
            player_params = {
                "wiki": "counterstrike",
                "conditions": f"[[teampagename::{team_name.replace(' ', '_')}]]",
                "limit": 10
            }
            
            print(f"📡 Fazendo request com params:")
            print(json.dumps(player_params, indent=2))
            print()
            
            player_data = await liquipedia._request("player", player_params, ttl_minutes=60)
            
            if player_data and "result" in player_data:
                players = player_data["result"]
                print(f"✅ Encontrados {len(players)} jogadores!\n")
                
                for i, player in enumerate(players, 1):
                    player_id = player.get('id', 'N/A')
                    player_name = player.get('name', 'N/A')
                    print(f"  {i}. {player_id} ({player_name})")
                
                # Mostrar estrutura completa do primeiro jogador
                if players:
                    print(f"\n{'─'*80}")
                    print("📋 Estrutura completa do primeiro jogador:")
                    print(f"{'─'*80}\n")
                    print(json.dumps(players[0], indent=2, ensure_ascii=False))
            else:
                print(f"❌ Nenhum jogador encontrado para '{team_name}'")
                if player_data:
                    print(f"Resposta: {json.dumps(player_data, indent=2)}")
            
            # Delay para respeitar rate limit
            await asyncio.sleep(3)
            
        except Exception as e:
            print(f"❌ Erro ao buscar jogadores de '{team_name}': {e}\n")
    
    print(f"\n{'='*80}")
    print("✅ Teste concluído!")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    asyncio.run(inspect())
