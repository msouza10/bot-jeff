import asyncio
import os
import sys
import json
from datetime import datetime, timedelta

from dotenv import load_dotenv

# Adicionar diretório raiz ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Carregar variáveis de ambiente
load_dotenv()

from src.database.cache_manager import MatchCacheManager


async def test_filtering():
    print("🧪 Iniciando teste de filtragem por torneio...")
    
    # Configurar DB de teste (usando o banco real para simplificar, mas cuidado com dados)
    # Melhor usar o banco real mas inserir dados que depois removemos ou apenas consultar dados existentes se houver.
    # Como não sei o estado do banco, vou inserir um dado mockado e depois limpar.
    
    db_url = os.getenv("LIBSQL_URL")
    db_token = os.getenv("LIBSQL_TOKEN")
    
    if not db_url:
        print("❌ LIBSQL_URL não definida")
        return

    cache_manager = MatchCacheManager(db_url, db_token)
    
    # Mock match data
    mock_match_major = {
        "id": 9999991,
        "name": "Team A vs Team B",
        "status": "not_started",
        "begin_at": (datetime.now() + timedelta(hours=1)).isoformat(),
        "tournament": {"name": "PGL Major Copenhagen"},
        "league": {"name": "PGL Major"},
        "opponents": [
            {"opponent": {"name": "Team A"}},
            {"opponent": {"name": "Team B"}}
        ]
    }
    
    mock_match_iem = {
        "id": 9999992,
        "name": "Team C vs Team D",
        "status": "not_started",
        "begin_at": (datetime.now() + timedelta(hours=2)).isoformat(),
        "tournament": {"name": "IEM Katowice"},
        "league": {"name": "IEM"},
        "opponents": [
            {"opponent": {"name": "Team C"}},
            {"opponent": {"name": "Team D"}}
        ]
    }
    
    try:
        print("📝 Inserindo dados de teste...")
        await cache_manager.cache_matches([mock_match_major, mock_match_iem])
        
        # 1. Testar get_cached_matches (DB)
        print("\n🔎 Testando get_cached_matches (DB)...")
        
        # Filtro Major
        matches_major = await cache_manager.get_cached_matches(status="not_started", tournament_name="Major")
        print(f"  Major matches found: {len(matches_major)}")
        if len(matches_major) >= 1 and any(m['id'] == 9999991 for m in matches_major):
            print("  ✅ Filtro 'Major' funcionou (encontrou match 9999991)")
        else:
            print("  ❌ Filtro 'Major' falhou")
            
        # Filtro IEM
        matches_iem = await cache_manager.get_cached_matches(status="not_started", tournament_name="IEM")
        print(f"  IEM matches found: {len(matches_iem)}")
        if len(matches_iem) >= 1 and any(m['id'] == 9999992 for m in matches_iem):
            print("  ✅ Filtro 'IEM' funcionou (encontrou match 9999992)")
        else:
            print("  ❌ Filtro 'IEM' falhou")
            
        # 2. Testar get_cached_matches_fast (Memória)
        print("\n🔎 Testando get_cached_matches_fast (Memória)...")
        
        # Forçar atualização do cache em memória
        client = await cache_manager.get_client()
        await cache_manager._update_memory_cache(client)
        
        # Filtro Major
        fast_major = await cache_manager.get_cached_matches_fast("upcoming", tournament_name="Major")
        print(f"  Fast Major matches found: {len(fast_major)}")
        if len(fast_major) >= 1 and any(m['id'] == 9999991 for m in fast_major):
            print("  ✅ Fast Filtro 'Major' funcionou")
        else:
            print("  ❌ Fast Filtro 'Major' falhou")
            
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("\n🧹 Limpando dados de teste...")
        client = await cache_manager.get_client()
        await client.execute("DELETE FROM matches_cache WHERE match_id IN (9999991, 9999992)")
        print("✨ Teste concluído.")

if __name__ == "__main__":
    asyncio.run(test_filtering())
