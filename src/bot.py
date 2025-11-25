"""
BOT Jeff - Discord Bot para notificações de partidas de CS2
Arquivo principal de inicialização (usando Nextcord)
"""

import nextcord
from nextcord.ext import commands
import os
import logging
from dotenv import load_dotenv
import asyncio

from src.services.pandascore_service import PandaScoreClient
from src.database.cache_manager import MatchCacheManager
from src.services.cache_scheduler import CacheScheduler
from src.services.notification_manager import NotificationManager

# Configurar logging com suporte a UTF-8 em Windows e Linux
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Força UTF-8 no stdout/stderr para Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Verificar tokens necessários
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
PANDASCORE_API_KEY = os.getenv("PANDASCORE_API_KEY")
TESTING_GUILD_ID = int(os.getenv("TESTING_GUILD_ID", "0"))
LIBSQL_URL = os.getenv("LIBSQL_URL", "file:./data/bot.db")
LIBSQL_AUTH_TOKEN = os.getenv("LIBSQL_AUTH_TOKEN")  # Opcional para banco local

if not DISCORD_TOKEN:
    raise ValueError("❌ DISCORD_TOKEN não configurado no arquivo .env!")
if not PANDASCORE_API_KEY:
    raise ValueError("❌ PANDASCORE_API_KEY não configurado no arquivo .env!")
if not TESTING_GUILD_ID:
    logger.warning("⚠️  TESTING_GUILD_ID não configurado - comandos levam até 1h para aparecer!")


class JeffBot(commands.Bot):
    """Bot principal Jeff."""
    
    def __init__(self):
        # Configurar intents
        intents = nextcord.Intents.default()
        intents.guilds = True
        intents.guild_messages = True
        
        # Configurar guild_ids padrão se disponível
        default_guild_ids = [TESTING_GUILD_ID] if TESTING_GUILD_ID else None
        
        super().__init__(
            command_prefix="!",  # Prefix para comandos de texto (opcional)
            intents=intents,
            description="Bot de notificações de partidas de CS2",
            default_guild_ids=default_guild_ids
        )
        
        # Inicializar cliente da API
        self.api_client = PandaScoreClient(PANDASCORE_API_KEY)
        
        # Inicializar gerenciador de cache (libSQL)
        self.cache_manager = MatchCacheManager(LIBSQL_URL, LIBSQL_AUTH_TOKEN)
        
        # Inicializar gerenciador de notificações ANTES do scheduler
        self.notification_manager = NotificationManager(self, self.cache_manager)
        
        # Inicializar agendador de cache com notification manager
        self.cache_scheduler = CacheScheduler(self.api_client, self.cache_manager, self.notification_manager)
        
        logger.info("🤖 BOT Jeff inicializado")
        if default_guild_ids:
            logger.info(f"🎯 Comandos registrados para guild ID: {TESTING_GUILD_ID}")
        
        # Carregar cogs
        self._load_cogs()
    
    def _load_cogs(self):
        """Carrega os cogs do bot."""
        logger.info("⚙️ Carregando cogs...")
        
        cogs = [
            "src.cogs.status",
            "src.cogs.matches",
            "src.cogs.notifications",
            "src.cogs.liquipedia",
        ]
        
        for cog in cogs:
            try:
                self.load_extension(cog)
                logger.info(f"  ✓ Cog carregado: {cog}")
            except Exception as e:
                logger.error(f"  ✗ Erro ao carregar cog {cog}: {e}")
                import traceback
                traceback.print_exc()
        
        logger.info("✓ Cogs carregados!")
    
    async def on_ready(self):
        """Evento chamado quando o bot conecta ao Discord."""
        logger.info("=" * 60)
        logger.info(f"✅ BOT CONECTADO como: {self.user.name} (ID: {self.user.id})")
        logger.info(f"   Servidores: {len(self.guilds)} | Ping: {round(self.latency * 1000)}ms")
        logger.info("=" * 60)
        
        # Listar servidores
        if self.guilds:
            logger.info("📋 SERVIDORES CONECTADOS:")
            for guild in self.guilds:
                logger.info(f"   • {guild.name} (ID: {guild.id})")
        
        # Definir status
        await self.change_presence(
            activity=nextcord.Activity(
                type=nextcord.ActivityType.watching,
                name="partidas de CS2"
            )
        )
        logger.info("🎮 Status: Assistindo partidas de CS2")
        
        # Iniciar agendador de cache
        logger.info("\n[CACHE SCHEDULER]")
        logger.info("⏰ Iniciando agendador de cache...")
        self.cache_scheduler.start()
        logger.info("✅ Agendador de cache ATIVO")
        
        # Iniciar gerenciador de notificações
        logger.info("\n[NOTIFICATION MANAGER]")
        logger.info("📬 Iniciando gerenciador de notificações...")
        self.notification_manager.start_reminder_loop()
        logger.info("✅ Gerenciador de notificações ATIVO")
        
        logger.info("\n" + "=" * 60)
        logger.info("🚀 BOT PRONTO PARA USO")
        logger.info("=" * 60 + "\n")
    
    async def on_guild_join(self, guild: nextcord.Guild):
        """Evento chamado quando o bot entra em um servidor."""
        logger.info(f"✓ Bot adicionado ao servidor: {guild.name} (ID: {guild.id})")
    
    async def on_guild_remove(self, guild: nextcord.Guild):
        """Evento chamado quando o bot sai de um servidor."""
        logger.info(f"✗ Bot removido do servidor: {guild.name} (ID: {guild.id})")
    
    async def on_application_command_error(self, interaction: nextcord.Interaction, error: Exception):
        """Tratamento global de erros de comandos slash."""
        logger.error(f"✗ Erro no comando: {error}")
        
        if isinstance(error, commands.CommandOnCooldown):
            await interaction.response.send_message(f"⏰ Aguarde {error.retry_after:.1f}s para usar este comando novamente.", ephemeral=True)
        elif isinstance(error, commands.MissingPermissions):
            await interaction.response.send_message("❌ Você não tem permissão para usar este comando.", ephemeral=True)
        else:
            try:
                await interaction.response.send_message(f"❌ Ocorreu um erro ao executar o comando: {str(error)}", ephemeral=True)
            except:
                pass  # Já respondido
    
    async def close(self):
        """Chamado ao desligar o bot."""
        logger.info("🔌 Encerrando bot...")
        
        # Parar agendador
        self.cache_scheduler.stop()
        
        # Parar gerenciador de notificações
        self.notification_manager.stop_reminder_loop()
        
        # Fechar cliente da API
        await self.api_client.close()
        
        # Fechar serviço YouTube
        from src.services.youtube_service import close_youtube_service
        await close_youtube_service()
        
        await super().close()
        logger.info("✓ Bot encerrado")


def main():
    """Função principal para iniciar o bot."""
    try:
        bot = JeffBot()
        
        logger.info("🚀 Iniciando bot...")
        bot.run(DISCORD_TOKEN)
        
    except KeyboardInterrupt:
        logger.info("⚠️ Bot interrompido pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}")
        raise


if __name__ == "__main__":
    main()
