import asyncio
import sys
import os
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

# Adicionar src ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.cogs.status import StatusCog

async def test_status_command():
    print("🧪 Iniciando teste do comando /status...")
    
    # Mock do Bot
    mock_bot = MagicMock()
    mock_bot.latency = 0.050  # 50ms
    
    # Mock dos serviços
    mock_bot.cache_manager.check_health = AsyncMock(return_value={"status": "ok", "latency": 10.5})
    mock_bot.api_client.check_health = AsyncMock(return_value={"status": "ok", "latency": 120.0})
    mock_bot.cache_manager.get_cache_stats = AsyncMock(return_value={
        "total_matches": 100,
        "live_matches": 2,
        "upcoming_matches": 10,
        "finished_matches": 88,
        "newest_update": "2023-10-27 10:00:00"
    })
    mock_bot.notification_manager.get_status = MagicMock(return_value={
        "running": True,
        "next_check": (datetime.now()).isoformat()
    })
    
    # Mock do Liquipedia Cog/Service
    mock_liquipedia_cog = MagicMock()
    mock_liquipedia_service = MagicMock()
    mock_liquipedia_service.check_health = AsyncMock(return_value={"status": "ok", "latency": 200.0})
    mock_liquipedia_cog.liquipedia_service = mock_liquipedia_service
    
    mock_bot.get_cog.return_value = mock_liquipedia_cog
    
    # Inicializar Cog
    cog = StatusCog(mock_bot)
    
    # Mock da Interaction
    mock_interaction = MagicMock()
    mock_interaction.response.defer = AsyncMock()
    mock_interaction.followup.send = AsyncMock()
    mock_interaction.user.display_name = "Tester"
    mock_interaction.user.display_avatar.url = "http://avatar.url"
    
    # Executar comando
    print("🔄 Executando status()...")
    await cog.status(mock_interaction)
    
    # Verificar chamadas
    mock_interaction.response.defer.assert_called_once()
    mock_interaction.followup.send.assert_called_once()
    
    # Verificar conteúdo do embed
    args, kwargs = mock_interaction.followup.send.call_args
    embed = kwargs['embed']
    
    print("✅ Embed gerado com sucesso!")
    print(f"   Título: {embed.title}")
    print(f"   Campos: {len(embed.fields)}")
    for field in embed.fields:
        print(f"   - {field.name}: {field.value[:50]}...")
        
    print("\n🎉 Teste concluído com sucesso!")

if __name__ == "__main__":
    asyncio.run(test_status_command())
