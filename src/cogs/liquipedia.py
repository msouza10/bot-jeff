"""
Cog para comandos relacionados à Liquipedia (usando Nextcord).
"""

import nextcord
from nextcord.ext import commands
from nextcord import SlashOption
import logging
import json
from datetime import datetime

from src.services.liquipedia_service import LiquipediaService

logger = logging.getLogger(__name__)


class LiquipediaCog(commands.Cog):
    """Comandos para consultar informações da Liquipedia (jogadores e times)."""
    
    def __init__(self, bot):
        self.bot = bot
        self.liquipedia_service = LiquipediaService()
    
    @nextcord.slash_command(name="jogador", description="Busca informações de um jogador de CS2 na Liquipedia")
    async def jogador(
        self,
        interaction: nextcord.Interaction,
        nome: str = SlashOption(
            name="nome",
            description="Nome do jogador (ex: FalleN, s1mple, ZywOo)",
            required=True
        )
    ):
        """Busca informações de um jogador na Liquipedia."""
        logger.info(f"📥 Comando /jogador recebido de {interaction.user} (guild: {interaction.guild.name if interaction.guild else 'DM'})")
        logger.info(f"   └─ Parâmetro 'nome': '{nome}'")
        await interaction.response.defer()
        
        try:
            logger.debug(f"🔄 Chamando liquipedia_service.get_player('{nome}')...")
            player_data = await self.liquipedia_service.get_player(nome)
            
            if not player_data:
                logger.warning(f"⚠️ Jogador '{nome}' não encontrado.")
                embed = nextcord.Embed(
                    title="❌ Jogador não encontrado",
                    description=f"Não foi possível encontrar o jogador **{nome}** na Liquipedia.\n\n*Dica: Verifique se o nome está correto (ex: 'FalleN' com N maiúsculo)*",
                    color=0xFF0000
                )
                await interaction.followup.send(embed=embed)
                return
            
            logger.info(f"✅ Jogador '{nome}' encontrado! Criando embed...")
            # Criar embed com as informações do jogador
            embed = nextcord.Embed(
                title=f"🎮 {player_data.get('name', nome)}",
                url=f"https://liquipedia.net/counterstrike/{player_data.get('pagename', nome)}",
                color=0x00FF00,
                timestamp=datetime.utcnow()
            )
            
            # Campo: ID / IGN
            embed.add_field(
                name="ID", 
                value=player_data.get('id', 'N/A'),
                inline=True
            )
            
            # Campo: Nacionalidade
            nationality = player_data.get('nationality', 'N/A')
            if player_data.get('nationality2'):
                nationality += f" / {player_data.get('nationality2')}"
            embed.add_field(
                name="Nacionalidade",
                value=nationality,
                inline=True
            )
            
            # Campo: Time Atual
            team = player_data.get('teampagename')
            if team:
                embed.add_field(
                    name="Time Atual",
                    value=f"[{team}](https://liquipedia.net/counterstrike/{team.replace(' ', '_')})",
                    inline=True
                )
            
            # Campo: Região
            if player_data.get('region'):
                embed.add_field(
                    name="Região",
                    value=player_data.get('region'),
                    inline=True
                )
            
            # Campo: Data de Nascimento
            if player_data.get('birthdate') and player_data.get('birthdate') != '0000-01-01':
                try:
                    birth_date = datetime.strptime(player_data['birthdate'], '%Y-%m-%d')
                    age = (datetime.now() - birth_date).days // 365
                    embed.add_field(
                        name="Idade",
                        value=f"{age} anos ({birth_date.strftime('%d/%m/%Y')})",
                        inline=True
                    )
                except:
                    pass
            
            # Campo: Status
            status_emoji = "✅" if player_data.get('status') == 'Active' else "⚠️"
            embed.add_field(
                name="Status",
                value=f"{status_emoji} {player_data.get('status', 'N/A')}",
                inline=True
            )
            
            # Campo: Prize Money
            if player_data.get('earnings'):
                earnings = player_data['earnings']
                embed.add_field(
                    name="💰 Prize Money Total",
                    value=f"${earnings:,}",
                    inline=True
                )
            
            # Campo: Roles
            extradata = player_data.get('extradata', {})
            if isinstance(extradata, str):
                try:
                    extradata = json.loads(extradata)
                except:
                    extradata = {}
            
            roles = []
            if extradata.get('role'):
                roles.append(extradata['role'])
            if extradata.get('role2'):
                roles.append(extradata['role2'])
            
            if roles:
                embed.add_field(
                    name="Funções",
                    value=" / ".join(roles).upper(),
                    inline=True
                )
            
            # Links de redes sociais
            links = player_data.get('links', {})
            if isinstance(links, str):
                try:
                    links = json.loads(links)
                except:
                    links = {}
            
            social_links = []
            if links.get('twitch'):
                social_links.append(f"[Twitch]({links['twitch']})")
            if links.get('twitter'):
                social_links.append(f"[Twitter]({links['twitter']})")
            if links.get('instagram'):
                social_links.append(f"[Instagram]({links['instagram']})")
            
            if social_links:
                embed.add_field(
                    name="🔗 Redes Sociais",
                    value=" • ".join(social_links),
                    inline=False
                )
            
            # Footer com metadados do cache
            metadata = player_data.get('_cache_metadata', {})
            source = metadata.get('source', 'unknown')
            updated_at_str = metadata.get('updated_at', '')
            
            # Formatar data/hora
            if updated_at_str:
                try:
                    import pytz
                    
                    updated_dt = datetime.fromisoformat(updated_at_str)
                    # Converter para BRT (UTC-3)
                    brt = pytz.timezone('America/Sao_Paulo')
                    updated_brt = updated_dt.astimezone(brt) if updated_dt.tzinfo else brt.localize(updated_dt)
                    
                    cache_date = updated_brt.strftime('%d/%m/%Y, %H:%M')
                    source_text = "Cache" if source == "cache" else "API"
                    
                    footer_text = f"Dados fornecidos por Liquipedia (CC-BY-SA 3.0) • {source_text} {cache_date} • BRT (UTC-3)"
                except:
                    footer_text = "Dados fornecidos por Liquipedia (CC-BY-SA 3.0)"
            else:
                footer_text = "Dados fornecidos por Liquipedia (CC-BY-SA 3.0)"
            
            embed.set_footer(text=footer_text)
            
            logger.debug(f"📤 Enviando embed para o usuário...")
            await interaction.followup.send(embed=embed)
            logger.info(f"✅ Comando /jogador executado com SUCESSO por {interaction.user} (Jogador: {nome})")
            
        except Exception as e:
            logger.error(f"❌ ERRO no comando /jogador: {e}", exc_info=True)
            embed = nextcord.Embed(
                title="❌ Erro",
                description=f"Ocorreu um erro ao buscar informações do jogador: {str(e)}",
                color=0xFF0000
            )
            await interaction.followup.send(embed=embed)
    
    @jogador.on_autocomplete("nome")
    async def jogador_autocomplete(self, interaction: nextcord.Interaction, nome: str):
        """Autocomplete para o nome do jogador."""
        # Buscar sugestões no cache (mesmo se vazio)
        suggestions = await self.liquipedia_service.search_players(nome)
        await interaction.response.send_autocomplete(suggestions)

    @nextcord.slash_command(name="time", description="Busca informações de um time de CS2 na Liquipedia")
    async def team(
        self,
        interaction: nextcord.Interaction,
        nome: str = SlashOption(
            name="nome",
            description="Nome do time (ex: FURIA, Natus Vincere, FaZe Clan)",
            required=True
        )
    ):
        """Busca informações de um time na Liquipedia."""
        logger.info(f"📥 Comando /team recebido de {interaction.user} (guild: {interaction.guild.name if interaction.guild else 'DM'})")
        logger.info(f"   └─ Parâmetro 'nome': '{nome}'")
        await interaction.response.defer()
        
        try:
            logger.debug(f"🔄 Chamando liquipedia_service.get_team('{nome}')...")
            team_data = await self.liquipedia_service.get_team(nome)
            
            if not team_data:
                logger.warning(f"⚠️ Time '{nome}' não encontrado.")
                embed = nextcord.Embed(
                    title="❌ Time não encontrado",
                    description=f"Não foi possível encontrar o time **{nome}** na Liquipedia.\n\n*Dica: Verifique se o nome está correto (ex: 'FURIA', 'Natus Vincere')*",
                    color=0xFF0000
                )
                await interaction.followup.send(embed=embed)
                return
            
            logger.info(f"✅ Time '{nome}' encontrado! Criando embed...")
            # Criar embed com as informações do time
            embed = nextcord.Embed(
                title=f"🏆 {team_data.get('name', nome)}",
                url=f"https://liquipedia.net/counterstrike/{team_data.get('pagename', nome).replace(' ', '_')}",
                color=0x0099FF,
                timestamp=datetime.utcnow()
            )
            
            # Logo do time (se disponível)
            if team_data.get('logourl'):
                embed.set_thumbnail(url=team_data['logourl'])
            
            # Campo: Região
            if team_data.get('region'):
                embed.add_field(
                    name="Região",
                    value=team_data['region'],
                    inline=True
                )
            
            # Campo: Status
            status_emoji = "✅" if team_data.get('status') == 'active' else "⚠️"
            embed.add_field(
                name="Status",
                value=f"{status_emoji} {team_data.get('status', 'N/A').capitalize()}",
                inline=True
            )
            
            # Campo: Data de Criação
            if team_data.get('createdate') and team_data.get('createdate') != '0000-01-01':
                try:
                    create_date = datetime.strptime(team_data['createdate'], '%Y-%m-%d')
                    embed.add_field(
                        name="Fundação",
                        value=create_date.strftime('%d/%m/%Y'),
                        inline=True
                    )
                except:
                    pass
            
            # Campo: Prize Money
            if team_data.get('earnings'):
                earnings = team_data['earnings']
                embed.add_field(
                    name="💰 Prize Money Total",
                    value=f"${earnings:,}",
                    inline=True
                )
            
            # Links de redes sociais
            links = team_data.get('links', {})
            if isinstance(links, str):
                try:
                    links = json.loads(links)
                except:
                    links = {}
            
            social_links = []
            if links.get('home'):
                social_links.append(f"[Website]({links['home']})")
            if links.get('twitter'):
                social_links.append(f"[Twitter]({links['twitter']})")
            if links.get('instagram'):
                social_links.append(f"[Instagram]({links['instagram']})")
            if links.get('twitch'):
                social_links.append(f"[Twitch]({links['twitch']})")
            
            if social_links:
                embed.add_field(
                    name="🔗 Links",
                    value=" • ".join(social_links),
                    inline=False
                )
            
            # Footer com metadados do cache
            metadata = team_data.get('_cache_metadata', {})
            source = metadata.get('source', 'unknown')
            updated_at_str = metadata.get('updated_at', '')
            
            # Formatar data/hora
            if updated_at_str:
                try:
                    import pytz
                    
                    updated_dt = datetime.fromisoformat(updated_at_str)
                    # Converter para BRT (UTC-3)
                    brt = pytz.timezone('America/Sao_Paulo')
                    updated_brt = updated_dt.astimezone(brt) if updated_dt.tzinfo else brt.localize(updated_dt)
                    
                    cache_date = updated_brt.strftime('%d/%m/%Y, %H:%M')
                    source_text = "Cache" if source == "cache" else "API"
                    
                    footer_text = f"Dados fornecidos por Liquipedia (CC-BY-SA 3.0) • {source_text} {cache_date} • BRT (UTC-3)"
                except:
                    footer_text = "Dados fornecidos por Liquipedia (CC-BY-SA 3.0)"
            else:
                footer_text = "Dados fornecidos por Liquipedia (CC-BY-SA 3.0)"
            
            embed.set_footer(text=footer_text)
            
            logger.debug(f"📤 Enviando embed para o usuário...")
            await interaction.followup.send(embed=embed)
            logger.info(f"✅ Comando /team executado com SUCESSO por {interaction.user} (Time: {nome})")
            
        except Exception as e:
            logger.error(f"❌ ERRO no comando /team: {e}", exc_info=True)
            embed = nextcord.Embed(
                title="❌ Erro",
                description=f"Ocorreu um erro ao buscar informações do time: {str(e)}",
                color=0xFF0000
            )
            await interaction.followup.send(embed=embed)

    @team.on_autocomplete("nome")
    async def team_autocomplete(self, interaction: nextcord.Interaction, nome: str):
        """Autocomplete para o nome do time."""
        # Buscar sugestões no cache (mesmo se vazio)
        suggestions = await self.liquipedia_service.search_teams(nome)
        await interaction.response.send_autocomplete(suggestions)


def setup(bot):
    """Adiciona o cog ao bot."""
    bot.add_cog(LiquipediaCog(bot))
