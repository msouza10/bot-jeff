"""
Cog para comandos de configuração de notificações de partidas.
"""

import nextcord
from nextcord.ext import commands
from nextcord import SlashOption
import logging

logger = logging.getLogger(__name__)


class NotificationsCog(commands.Cog):
    """Comandos para configurar notificações de partidas."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @nextcord.slash_command(name="notificacoes", description="Configura notificações de partidas")
    async def notificacoes(self, interaction: nextcord.Interaction):
        """Comando principal de notificações (grupo)."""
        pass

    @notificacoes.subcommand(name="ativar", description="Ativa/desativa notificações de partidas no servidor")
    async def ativar(
        self,
        interaction: nextcord.Interaction,
        ativar: bool = SlashOption(
            name="ativar",
            description="Ativar ou desativar notificações",
            required=True
        )
    ):
        """Ativa ou desativa notificações de partidas."""
        
        # Verificar permissões
        if not interaction.user.guild_permissions.administrator:
            embed = nextcord.Embed(
                title="❌ Permissão Negada",
                description="Apenas administradores podem configurar notificações.",
                color=nextcord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        guild_id = interaction.guild_id
        
        try:
            client = await self.bot.cache_manager.get_client()
            
            # Garantir que existe registro de configuração
            await client.execute(
                """
                INSERT OR IGNORE INTO guild_config (guild_id, notify_upcoming, notify_live)
                VALUES (?, 1, 1)
                """,
                [guild_id]
            )
            
            # Atualizar configuração
            await client.execute(
                """
                UPDATE guild_config 
                SET notify_upcoming = ?, notify_live = ?
                WHERE guild_id = ?
                """,
                [1 if ativar else 0, 1 if ativar else 0, guild_id]
            )
            
            status = "✅ **Ativadas**" if ativar else "❌ **Desativadas**"
            
            embed = nextcord.Embed(
                title="Notificações",
                description=f"Notificações de partidas agora estão {status}",
                color=nextcord.Color.green() if ativar else nextcord.Color.red()
            )
            
            if ativar:
                # Agendar lembretes para todas as partidas no cache
                matches = await self.bot.cache_manager.get_cached_matches_fast("not_started", limit=50)
                
                logger.info(f"📋 Comando /notificacoes ativar:true em guild {guild_id}")
                logger.info(f"   📊 Total de partidas em cache: {len(matches) if matches else 0}")
                
                if matches:
                    logger.info(f"   🚀 Iniciando agendamento de lembretes...")
                    scheduled_count = await self.bot.notification_manager.setup_reminders_for_all_matches(
                        guild_id, 
                        matches
                    )
                    embed.add_field(
                        name=f"📬 {scheduled_count} partidas agendadas",
                        value="Lembretes em: 1h, 30min, 15min, 5min e ao vivo",
                        inline=False
                    )
                    logger.info(f"   ✅ Agendamento concluído! {scheduled_count} partidas configuradas")
                else:
                    embed.add_field(
                        name="📬 Nenhuma partida no cache",
                        value="Lembretes serão criados automaticamente quando partidas forem adicionadas",
                        inline=False
                    )
                    logger.warning(f"   ⚠️ Nenhuma partida em cache para agendar")
                
                embed.add_field(
                    name="⚠️ Aviso",
                    value="Configure o canal de notificações com `/notificacoes canal` antes de ativar!",
                    inline=False
                )
            
            embed.set_footer(text="Bot HLTV - Notificações de Partidas")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            logger.info(f"✓ Notificações {'ativadas' if ativar else 'desativadas'} para guild {guild_id}")
            
        except Exception as e:
            logger.error(f"Erro ao configurar notificações: {e}")
            embed = nextcord.Embed(
                title="❌ Erro",
                description=f"Erro ao configurar notificações: {str(e)}",
                color=nextcord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @notificacoes.subcommand(name="canal", description="Define o canal onde as notificações serão enviadas")
    async def canal(
        self,
        interaction: nextcord.Interaction,
        canal: nextcord.TextChannel = SlashOption(
            name="canal",
            description="Selecione o canal para notificações",
            required=True
        )
    ):
        """Define o canal para notificações de partidas."""
        
        # Verificar permissões
        if not interaction.user.guild_permissions.administrator:
            embed = nextcord.Embed(
                title="❌ Permissão Negada",
                description="Apenas administradores podem configurar canais de notificações.",
                color=nextcord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        guild_id = interaction.guild_id
        channel_id = canal.id
        
        try:
            client = await self.bot.cache_manager.get_client()
            
            # Garantir que existe registro de configuração
            await client.execute(
                """
                INSERT OR IGNORE INTO guild_config (guild_id, notification_channel_id)
                VALUES (?, ?)
                """,
                [guild_id, channel_id]
            )
            
            # Atualizar canal
            await client.execute(
                """
                UPDATE guild_config 
                SET notification_channel_id = ?
                WHERE guild_id = ?
                """,
                [channel_id, guild_id]
            )
            
            embed = nextcord.Embed(
                title="✅ Canal Configurado",
                description=f"As notificações serão enviadas em {canal.mention}",
                color=nextcord.Color.green()
            )
            
            embed.add_field(
                name="📋 Informações",
                value=f"Canal ID: `{channel_id}`\nServidor: `{interaction.guild.name}`",
                inline=False
            )
            
            embed.add_field(
                name="⚠️ Próximo Passo",
                value="Use `/notificacoes ativar: verdadeiro` para ativar as notificações",
                inline=False
            )
            
            embed.set_footer(text="Bot HLTV - Notificações de Partidas")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            # Enviar mensagem no canal
            try:
                embed_test = nextcord.Embed(
                    title="🎮 Notificações Configuradas",
                    description="Este canal foi configurado para receber notificações de partidas de CS2!",
                    color=nextcord.Color.blue()
                )
                embed_test.add_field(
                    name="📬 O que você receberá",
                    value="• Lembretes 1 hora antes da partida\n• Lembretes 30 minutos antes\n• Lembretes 15 minutos antes\n• Lembretes 5 minutos antes\n• Notificação quando a partida inicia",
                    inline=False
                )
                embed_test.set_footer(text="Bot HLTV - Notificações de Partidas")
                
                await canal.send(embed=embed_test)
            except Exception as e:
                logger.warning(f"Não foi possível enviar mensagem de teste no canal: {e}")
            
            logger.info(f"✓ Canal de notificações configurado para guild {guild_id}: {channel_id}")
            
        except Exception as e:
            logger.error(f"Erro ao configurar canal de notificações: {e}")
            embed = nextcord.Embed(
                title="❌ Erro",
                description=f"Erro ao configurar canal: {str(e)}",
                color=nextcord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @notificacoes.subcommand(name="resultado", description="Ativa/desativa notificações de RESULTADO de partidas")
    async def resultado(
        self,
        interaction: nextcord.Interaction,
        ativar: bool = SlashOption(
            name="ativar",
            description="Ativar ou desativar notificações de resultado",
            required=True
        )
    ):
        """Ativa ou desativa notificações de RESULTADO de partidas finalizadas."""
        
        # Verificar permissões
        if not interaction.user.guild_permissions.administrator:
            embed = nextcord.Embed(
                title="❌ Permissão Negada",
                description="Apenas administradores podem configurar notificações.",
                color=nextcord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        guild_id = interaction.guild_id
        
        try:
            client = await self.bot.cache_manager.get_client()
            
            # Garantir que existe registro de configuração
            await client.execute(
                """
                INSERT OR IGNORE INTO guild_config (guild_id, notify_results)
                VALUES (?, ?)
                """,
                [guild_id, 1 if ativar else 0]
            )
            
            # Atualizar configuração
            await client.execute(
                """
                UPDATE guild_config 
                SET notify_results = ?
                WHERE guild_id = ?
                """,
                [1 if ativar else 0, guild_id]
            )
            
            status = "✅ **Ativadas**" if ativar else "❌ **Desativadas**"
            
            embed = nextcord.Embed(
                title="Notificações de Resultado",
                description=f"Notificações de RESULTADO agora estão {status}",
                color=nextcord.Color.green() if ativar else nextcord.Color.red()
            )
            
            if ativar:
                embed.add_field(
                    name="📬 O que você receberá",
                    value="Notificações assim que uma partida termina com o resultado final",
                    inline=False
                )
                embed.add_field(
                    name="⏱️ Tempo de Notificação",
                    value="~1-3 minutos após a partida terminar",
                    inline=False
                )
            
            embed.add_field(
                name="ℹ️ Informação",
                value="Configure o canal com `/notificacoes canal` para usar esta funcionalidade",
                inline=False
            )
            
            embed.set_footer(text="Bot HLTV - Notificações de Partidas")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            logger.info(f"✓ Notificações de resultado {'ativadas' if ativar else 'desativadas'} para guild {guild_id}")
            
        except Exception as e:
            logger.error(f"Erro ao configurar notificações de resultado: {e}")
            embed = nextcord.Embed(
                title="❌ Erro",
                description=f"Erro ao configurar: {str(e)}",
                color=nextcord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @nextcord.slash_command(
        name="timezone_info",
        description="Mostra qual timezone (fuso horário) está configurado para o servidor"
    )
    async def timezone_info(self, interaction: nextcord.Interaction):
        """
        Exibe o timezone atualmente configurado do servidor.
        """
        try:
            guild_id = interaction.guild_id
            
            # Obter timezone do cache_manager
            timezone = await self.bot.cache_manager.get_guild_timezone(guild_id)
            
            if not timezone:
                # Se não tem timezone configurado, mostrar mensagem informativa
                embed = nextcord.Embed(
                    title="🌍 Timezone Não Configurado",
                    description="Este servidor ainda não tem um timezone configurado.",
                    color=nextcord.Color.orange()
                )
                
                embed.add_field(
                    name="📌 O que fazer?",
                    value="""
                    Use o comando `/timezone` para configurar o timezone do seu servidor.
                    
                    Exemplo:
                    `/timezone fuso_horario: America/Sao_Paulo`
                    """,
                    inline=False
                )
                
                embed.add_field(
                    name="ℹ️ Por que configurar?",
                    value="""
                    • Todos os horários das partidas serão exibidos no timezone do seu servidor
                    • As notificações serão enviadas no horário correto
                    • Os lembretes respeitarão sua zona horária
                    """,
                    inline=False
                )
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                logger.info(f"🌍 /timezone_info: Timezone não configurado para guild {guild_id}")
                return
            
            from src.utils.timezone_manager import TimezoneManager
            
            # Obter informações do timezone
            tz_abbr = TimezoneManager.get_timezone_abbreviation(timezone)
            tz_offset = TimezoneManager.get_timezone_offset(timezone)
            tz_emoji = TimezoneManager.get_server_timezone_emoji(timezone)
            
            # Obter hora atual neste timezone
            import datetime
            import pytz
            
            tz_obj = pytz.timezone(timezone)
            current_time = datetime.datetime.now(tz_obj)
            current_time_str = current_time.strftime("%H:%M:%S")
            current_date_str = current_time.strftime("%d/%m/%Y")
            
            embed = nextcord.Embed(
                title="🌍 Timezone do Servidor",
                description=f"Este servidor está usando **{timezone}**",
                color=nextcord.Color.blue()
            )
            
            embed.add_field(
                name="📍 Informações do Timezone",
                value=f"""
                **Timezone:** {timezone}
                **Abreviação:** {tz_abbr}
                **Offset UTC:** {tz_offset}
                **Emoji:** {tz_emoji}
                """,
                inline=False
            )
            
            embed.add_field(
                name="⏰ Hora Atual neste Timezone",
                value=f"""
                **Data:** {current_date_str}
                **Horário:** {current_time_str} {tz_abbr}
                """,
                inline=False
            )
            
            embed.add_field(
                name="📋 O que você vê?",
                value=f"""
                • **Partidas:** Convertidas para {tz_abbr}
                • **Notificações:** Enviadas no horário {tz_abbr}
                • **Lembretes:** Usando {tz_abbr}
                • **API:** Continua usando UTC internamente
                """,
                inline=False
            )
            
            embed.add_field(
                name="🔧 Alterar Timezone",
                value="Use `/timezone` para mudar o timezone do servidor.",
                inline=False
            )
            
            embed.set_footer(text="Bot HLTV - Timezone Info")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            logger.info(f"🌍 /timezone_info: Timezone do servidor = {timezone} (Guild: {guild_id})")
            
        except Exception as e:
            logger.error(f"Erro ao exibir timezone_info: {e}")
            embed = nextcord.Embed(
                title="❌ Erro",
                description=f"Erro ao exibir informações de timezone: {str(e)}",
                color=nextcord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @nextcord.slash_command(
        name="timezone",
        description="Configura o timezone (fuso horário) do servidor para exibição de horários"
    )
    async def timezone(
        self,
        interaction: nextcord.Interaction,
        fuso_horario: str = SlashOption(
            name="fuso_horario",
            description="Ex: America/Sao_Paulo, Europe/London, Asia/Tokyo",
            required=True
        )
    ):
        """
        Configura o timezone (fuso horário) do servidor.
        
        Exemplos:
        - Brazil: America/Sao_Paulo
        - USA: America/New_York
        - Europe: Europe/London, Europe/Paris
        - Asia: Asia/Tokyo, Asia/Shanghai
        """
        
        # Verificar permissões
        if not interaction.user.guild_permissions.administrator:
            embed = nextcord.Embed(
                title="❌ Permissão Negada",
                description="Apenas administradores podem configurar o timezone.",
                color=nextcord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        from src.utils.timezone_manager import TimezoneManager
        
        # Validar timezone
        if not TimezoneManager.is_valid_timezone(fuso_horario):
            # Mostrar sugestões
            suggestions = """
            **Timezones válidos (exemplos):**
            
            🇧🇷 **Brasil:** America/Sao_Paulo
            🇺🇸 **EUA - East:** America/New_York
            🇺🇸 **EUA - Chicago:** America/Chicago
            🇺🇸 **EUA - Denver:** America/Denver
            🇺🇸 **EUA - West:** America/Los_Angeles
            
            🇬🇧 **UK:** Europe/London
            🇫🇷 **França:** Europe/Paris
            🇩🇪 **Alemanha:** Europe/Berlin
            🇷🇺 **Rússia:** Europe/Moscow
            
            🇯🇵 **Japão:** Asia/Tokyo
            🇨🇳 **China:** Asia/Shanghai
            🇮🇳 **Índia:** Asia/Kolkata
            🇸🇬 **Singapura:** Asia/Singapore
            🇦🇺 **Austrália:** Australia/Sydney
            
            Para mais timezones, visite: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
            """
            
            embed = nextcord.Embed(
                title="❌ Timezone Inválido",
                description=f"'{fuso_horario}' não é um timezone válido.\n\n{suggestions}",
                color=nextcord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        guild_id = interaction.guild_id
        
        try:
            client = await self.bot.cache_manager.get_client()
            
            # Garantir que existe registro de configuração
            await client.execute(
                """
                INSERT OR IGNORE INTO guild_config (guild_id, timezone)
                VALUES (?, ?)
                """,
                [guild_id, fuso_horario]
            )
            
            # Atualizar timezone
            await client.execute(
                """
                UPDATE guild_config 
                SET timezone = ?
                WHERE guild_id = ?
                """,
                [fuso_horario, guild_id]
            )
            
            # Obter informações do novo timezone
            tz_abbr = TimezoneManager.get_timezone_abbreviation(fuso_horario)
            tz_offset = TimezoneManager.get_timezone_offset(fuso_horario)
            tz_emoji = TimezoneManager.get_server_timezone_emoji(fuso_horario)
            
            embed = nextcord.Embed(
                title="✅ Timezone Configurado",
                description=f"Horários agora serão exibidos em **{fuso_horario}**",
                color=nextcord.Color.green()
            )
            
            embed.add_field(
                name="📍 Informações",
                value=f"""
                **Timezone:** {fuso_horario}
                **Abreviação:** {tz_abbr}
                **Offset:** {tz_offset}
                **Emoji:** {tz_emoji}
                """,
                inline=False
            )
            
            embed.add_field(
                name="⏰ Exemplo",
                value=f"""
                Quando for 15:00 UTC (horário da API):
                Será exibido como: (convertido para seu timezone)
                """,
                inline=False
            )
            
            embed.add_field(
                name="📌 Informações",
                value="""
                • Todos os dados continuam em UTC no banco de dados
                • Conversão acontece apenas na EXIBIÇÃO
                • Se alterar o timezone, novas partidas usarão o novo horário
                • Partidas já agendadas usarão o timezone antigo""",
                inline=False
            )
            
            embed.set_footer(text="Bot HLTV - Timezone Configuration")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            logger.info(f"✓ Timezone configurado para {fuso_horario} na guild {guild_id}")
            
        except Exception as e:
            logger.error(f"Erro ao configurar timezone: {e}")
            embed = nextcord.Embed(
                title="❌ Erro",
                description=f"Erro ao configurar timezone: {str(e)}",
                color=nextcord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)


def setup(bot):
    """Setup do cog."""
    bot.add_cog(NotificationsCog(bot))
    logger.info("✓ NotificationsCog carregado")
