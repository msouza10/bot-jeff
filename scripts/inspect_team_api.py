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
    Investigar o que a API da Liquipedia retorna ao buscar dados de um time.
    """
    
    liquipedia = LiquipediaService()
    
    # Times conhecidos para testar
    test_teams = [
        "Natus Vincere",
        "FaZe Clan", 
        "G2 Esports",
        "Team Vitality",
        "FURIA Esports"
    ]
    
    print("🔍 Investigando estrutura de dados da API Liquipedia para times\n")
    print("="*80)
    
    for team_name in test_teams:
        print(f"\n{'='*80}")
        print(f"🏆 TEAM: {team_name}")
        print(f"{'='*80}\n")
        
        try:
            team_data = await liquipedia.get_team(team_name)
            
            if team_data:
                # Mostrar estrutura completa
                print(json.dumps(team_data, indent=2, ensure_ascii=False))
                
                # Análise específica de campos que podem conter jogadores
                print(f"\n{'─'*80}")
                print("📊 ANÁLISE DE CAMPOS RELEVANTES:")
                print(f"{'─'*80}\n")
                
                # Verificar campos principais
                if 'extradata' in team_data:
                    print("✅ Campo 'extradata' encontrado:")
                    extradata = team_data['extradata']
                    if isinstance(extradata, str):
                        try:
                            extradata = json.loads(extradata)
                            print(json.dumps(extradata, indent=2, ensure_ascii=False))
                        except:
                            print(f"   ⚠️ Não é JSON: {extradata[:200]}...")
                    else:
                        print(json.dumps(extradata, indent=2, ensure_ascii=False))
                else:
                    print("❌ Campo 'extradata' NÃO encontrado")
                
                # Procurar por qualquer campo que possa ter jogadores
                potential_player_fields = [
                    'roster', 'players', 'members', 'squad', 'lineup', 
                    'currentroster', 'activeroster', 'teamroster'
                ]
                
                print(f"\n{'─'*40}")
                print("🔎 Procurando campos relacionados a jogadores:")
                print(f"{'─'*40}")
                
                for field in potential_player_fields:
                    if field in team_data:
                        print(f"\n✅ Campo '{field}' encontrado:")
                        print(json.dumps(team_data[field], indent=2, ensure_ascii=False))
                
                # Listar TODOS os campos top-level
                print(f"\n{'─'*40}")
                print("📋 Todos os campos top-level disponíveis:")
                print(f"{'─'*40}")
                for key in team_data.keys():
                    value = team_data[key]
                    value_type = type(value).__name__
                    value_preview = str(value)[:100] if value else "None"
                    print(f"  • {key} ({value_type}): {value_preview}...")
                
            else:
                print(f"❌ Time '{team_name}' não encontrado\n")
            
            # Delay para respeitar rate limit
            await asyncio.sleep(3)
            
        except Exception as e:
            print(f"❌ Erro ao buscar '{team_name}': {e}\n")
    
    print(f"\n{'='*80}")
    print("✅ Investigação concluída!")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    asyncio.run(inspect())
