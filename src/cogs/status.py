"""
Cog para verificar o status do bot e seus serviços.
"""

import nextcord
from nextcord.ext import commands
import logging
from datetime import datetime, timedelta
import time
import platform

# Tentar importar psutil para stats de sistema
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from src.services.liquipedia_service import LiquipediaService

logger = logging.getLogger(__name__)


class StatusCog(commands.Cog):
    """Comandos de status e diagnóstico."""
    
    def __init__(self, bot):
        self.bot = bot
        self.start_time = datetime.now()
        logger.info("✅ StatusCog carregado")
    
    def _get_liquipedia_service(self) -> LiquipediaService:
        """
        Tenta obter a instância de LiquipediaService do cog LiquipediaCog
        para compartilhar o rate limiter. Se não conseguir, cria uma nova.
        """
        liquipedia_cog = self.bot.get_cog("LiquipediaCog")
        if liquipedia_cog and hasattr(liquipedia_cog, "liquipedia_service"):
            return liquipedia_cog.liquipedia_service
        
        logger.warning("⚠️ LiquipediaCog não encontrado ou sem service. Criando nova instância (Rate Limit separado!)")
        return LiquipediaService()

    @nextcord.slash_command(
        name="status",
        description="Exibe o status atual do bot, APIs e banco de dados."
    )
    async def status(self, interaction: nextcord.Interaction):
        """Comando que exibe dashboard de status."""
        await interaction.response.defer()
        
        # 1. Latência do Bot (Gateway)
        bot_latency = round(self.bot.latency * 1000)
        
        # 2. Banco de Dados
        db_health = await self.bot.cache_manager.check_health()
        
        # 3. PandaScore API
        pandascore_health = await self.bot.api_client.check_health()
        
        # 4. Liquipedia API
        liquipedia_service = self._get_liquipedia_service()
        liquipedia_health = await liquipedia_service.check_health()
        
        # 5. Cache Stats
        cache_stats = await self.bot.cache_manager.get_cache_stats()
        
        # 6. Notification Manager
        notif_status = self.bot.notification_manager.get_status()
        
        # 7. System Stats
        uptime = datetime.now() - self.start_time
        uptime_str = str(uptime).split('.')[0]  # Remove microsegundos
        
        # Montar Embed
        embed = nextcord.Embed(
            title="📊 Status do Sistema - BOT Jeff",
            color=0x00FF00 if db_health["status"] == "ok" and pandascore_health["status"] == "ok" else 0xFFAA00,
            timestamp=datetime.now()
        )
        
        # --- Conectividade ---
        status_emoji = {
            "ok": "🟢",
            "error": "🔴",
            "warning": "🟡"
        }
        
        conn_desc = (
            f"**Gateway (Ping):** `{bot_latency}ms`\n"
            f"{status_emoji.get(db_health['status'], '❓')} **Banco de Dados:** `{db_health['latency']:.1f}ms`\n"
            f"{status_emoji.get(pandascore_health['status'], '❓')} **PandaScore API:** `{pandascore_health['latency']:.1f}ms`\n"
            f"{status_emoji.get(liquipedia_health['status'], '❓')} **Liquipedia API:** `{liquipedia_health['latency']:.1f}ms`"
        )
        if db_health.get("error"):
            conn_desc += f"\n⚠️ **DB Erro:** {db_health['error']}"
        if pandascore_health.get("error"):
            conn_desc += f"\n⚠️ **Panda Erro:** {pandascore_health['error']}"
        if liquipedia_health.get("error"):
            conn_desc += f"\n⚠️ **Liqui Erro:** {liquipedia_health['error']}"
            
        embed.add_field(name="📡 Conectividade", value=conn_desc, inline=False)
        
        # --- Cache ---
        cache_desc = (
            f"**Total Partidas:** `{cache_stats.get('total_matches', 0)}`\n"
            f"**Ao Vivo:** `{cache_stats.get('live_matches', 0)}` | "
            f"**Futuras:** `{cache_stats.get('upcoming_matches', 0)}`\n"
            f"**Finalizadas:** `{cache_stats.get('finished_matches', 0)}`\n"
            f"**Última Atualização:** `{cache_stats.get('newest_update', 'N/A')}`"
        )
        embed.add_field(name="💾 Cache (DB)", value=cache_desc, inline=True)
        
        # --- Sistema ---
        sys_desc = f"**Uptime:** `{uptime_str}`\n"
        sys_desc += f"**OS:** `{platform.system()} {platform.release()}`\n"
        
        if HAS_PSUTIL:
            process = psutil.Process()
            mem_usage = process.memory_info().rss / 1024 / 1024  # MB
            sys_desc += f"**RAM:** `{mem_usage:.1f} MB`"
        
        embed.add_field(name="🖥️ Sistema", value=sys_desc, inline=True)
        
        # --- Notificações ---
        notif_icon = "✅" if notif_status["running"] else "⛔"
        notif_desc = f"**Status:** {notif_icon} `{'Rodando' if notif_status['running'] else 'Parado'}`"
        if notif_status["next_check"]:
            try:
                next_check = datetime.fromisoformat(notif_status["next_check"])
                delta = next_check - datetime.now()
                seconds = int(delta.total_seconds())
                notif_desc += f"\n**Próx. Check:** em `{seconds}s`"
            except:
                pass
                
        embed.add_field(name="🔔 Notificações", value=notif_desc, inline=True)
        
        embed.set_footer(text=f"Solicitado por {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url if interaction.user.display_avatar else None)
        
        await interaction.followup.send(embed=embed)

    @commands.command(name="sync")
    @commands.has_permissions(administrator=True)
    async def sync(self, ctx, spec: str = None):
        """
        Sincroniza os comandos slash.
        Uso: 
        !sync -> Sincroniza apenas para o servidor atual (rápido)
        !sync global -> Sincroniza globalmente (pode demorar ~1h)
        """
        logger.info(f"🔄 Comando !sync iniciado por {ctx.author} (ID: {ctx.author.id}) no servidor {ctx.guild.name} (ID: {ctx.guild.id}). Spec: {spec}")
        
        try:
            if spec == "global":
                msg = await ctx.send("⏳ Sincronizando comandos **globalmente**... Isso pode demorar para propagar.")
                synced = await self.bot.tree.sync()
                await msg.edit(content=f"✅ Sincronizados {len(synced)} comandos globalmente!")
                logger.info(f"✅ Comandos sincronizados globalmente com sucesso. Total: {len(synced)}")
            else:
                msg = await ctx.send("⏳ Sincronizando comandos para **este servidor**...")
                self.bot.tree.copy_global_to(guild=ctx.guild)
                synced = await self.bot.tree.sync(guild=ctx.guild)
                await msg.edit(content=f"✅ Sincronizados {len(synced)} comandos para este servidor!")
                logger.info(f"✅ Comandos sincronizados para {ctx.guild.name} (ID: {ctx.guild.id}) com sucesso. Total: {len(synced)}")
        except Exception as e:
            logger.error(f"❌ Erro ao executar !sync: {e}", exc_info=True)
            await ctx.send(f"❌ Erro ao sincronizar: {e}")



def setup(bot):
    """Função para carregar o cog."""
    bot.add_cog(StatusCog(bot))
