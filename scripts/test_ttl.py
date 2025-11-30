import asyncio
import os
import sys
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()
sys.path.append(os.getcwd())

from src.services.liquipedia_service import LiquipediaService
from src.database.liquipedia_db import get_db_connection

async def test_ttl():
    service = LiquipediaService()
    
    print("\n--- Testando TTL de 15 dias ---")
    
    # 1. Buscar um jogador (deve estar no cache)
    print("\n1. Buscando FalleN (deve estar no cache)...")
    player = await service.get_player("FalleN")
    
    if player:
        # Verificar updated_at no banco
        async with get_db_connection() as db:
            async with db.execute(
                "SELECT updated_at FROM players WHERE id = ?",
                ("FalleN",)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    updated_at = datetime.fromisoformat(row[0])
                    age_days = (datetime.now() - updated_at).days
                    print(f"   ✅ Encontrado! Atualizado há {age_days} dias")
                    print(f"   📅 Data de atualização: {updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("   ⚠️ Não encontrado")
    
    # 2. Simular cache expirado (manualmente alterar updated_at para 20 dias atrás)
    print("\n2. Simulando cache expirado (alterando updated_at para 20 dias atrás)...")
    twenty_days_ago = (datetime.now() - timedelta(days=20)).isoformat()
    
    async with get_db_connection() as db:
        await db.execute(
            "UPDATE players SET updated_at = ? WHERE id = ?",
            (twenty_days_ago, "FalleN")
        )
        await db.commit()
    
    print("   ✅ Cache artificialmente expirado")
    
    # 3. Buscar novamente (deve detectar expiração e revalidar)
    print("\n3. Buscando FalleN novamente (deve detectar expiração)...")
    player = await service.get_player("FalleN")
    
    if player:
        # Verificar se updated_at foi atualizado
        async with get_db_connection() as db:
            async with db.execute(
                "SELECT updated_at FROM players WHERE id = ?",
                ("FalleN",)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    new_updated_at = datetime.fromisoformat(row[0])
                    new_age_days = (datetime.now() - new_updated_at).days
                    print(f"   ✅ Revalidado! Atualizado há {new_age_days} dias")
                    print(f"   📅 Nova data: {new_updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n✅ Teste de TTL concluído!")

if __name__ == "__main__":
    asyncio.run(test_ttl())
