"""
Cog para comandos relacionados a partidas de CS2 (usando Nextcord).
"""

import asyncio
import nextcord
from nextcord.ext import commands
from nextcord import SlashOption
import logging
from typing import Optional

from src.utils.embeds import create_match_embed, create_result_embed, create_error_embed, create_info_embed, augment_match_with_streams

logger = logging.getLogger(__name__)


class MatchesCog(commands.Cog):
    """Comandos para consultar partidas de CS2."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @nextcord.slash_command(name="partidas", description="Comandos relacionados a partidas de CS2")
    async def partidas(self, interaction: nextcord.Interaction):
        """Comando principal de partidas (grupo)."""
        pass

    def _filter_matches_by_team(self, matches: list, team_name: str) -> list:
        """Filtra lista de partidas por nome do time."""
        if not team_name:
            return matches
            
        team_name_lower = team_name.lower()
        filtered = []
        for match in matches:
            # Verificar nos oponentes
            found = False
            for opponent in match.get("opponents", []):
                opp_name = opponent.get("opponent", {}).get("name", "").lower()
                if team_name_lower in opp_name:
                    found = True
                    break
            
            # Verificar no nome da partida
            if not found and team_name_lower in match.get("name", "").lower():
                found = True
                
            if found:
                filtered.append(match)
        return filtered

    def _filter_matches_by_tournament(self, matches: list, tournament_name: str) -> list:
        """Filtra lista de partidas por nome do torneio."""
        if not tournament_name:
            return matches
            
        tournament_name_lower = tournament_name.lower()
        filtered = []
        for match in matches:
            tourn_name = match.get("tournament", {}).get("name", "").lower()
            league_name = match.get("league", {}).get("name", "").lower()
            
            if tournament_name_lower in tourn_name or tournament_name_lower in league_name:
                filtered.append(match)
        return filtered

    @partidas.subcommand(name="futuras", description="Mostra as próximas partidas de CS2")
    async def futuras(
        self,
        interaction: nextcord.Interaction,
        quantidade: int = SlashOption(
            name="quantidade",
            description="Quantidade de partidas a exibir (máx: 10)",
            min_value=1,
            max_value=10,
            default=5,
            required=False
        ),
        time: str = SlashOption(
            name="time",
            description="Filtrar por nome do time (ex: Furia)",
            required=False
        ),
        torneio: str = SlashOption(
            name="torneio",
            description="Filtrar por nome do torneio (ex: Major)",
            required=False
        )
    ):
        """Lista as próximas partidas de CS2 (do cache rápido)."""
        await interaction.response.defer()
        
        try:
            # 🌍 Obter timezone do guild
            timezone = await self.bot.cache_manager.get_guild_timezone(interaction.guild_id) or "America/Sao_Paulo"
            logger.info(f"🌍 /partidas futuras: Timezone do servidor = {timezone}")
            
            # Primeiro: tentar cache em memória (muito rápido!)
            matches = await self.bot.cache_manager.get_cached_matches_fast("upcoming", quantidade, team_name=time, tournament_name=torneio)
            
            # Se vazio: buscar do banco (mais lento)
            if not matches:
                logger.info("Cache em memória vazio (ou sem match do filtro), buscando do banco...")
                matches = await self.bot.cache_manager.get_cached_matches(
                    status="not_started",
                    limit=quantidade,
                    team_name=time,
                    tournament_name=torneio
                )
            
            # Última opção: API (só se tudo vazio)
            if not matches:
                logger.info("Cache vazio, buscando da API...")
                # API não suporta filtro por nome parcial facilmente, buscamos tudo e filtramos aqui
                all_matches = await self.bot.api_client.get_upcoming_matches(per_page=50) # Buscar mais para filtrar
                matches = self._filter_matches_by_team(all_matches, time)
                matches = self._filter_matches_by_tournament(matches, torneio)
                matches = matches[:quantidade]
            
            if not matches:
                msg = "Não há partidas agendadas no momento."
                if time:
                    msg = f"Não há partidas agendadas para **{time}** no momento."
                if torneio:
                    if time:
                        msg = f"Não há partidas agendadas para **{time}** no torneio **{torneio}** no momento."
                    else:
                        msg = f"Não há partidas agendadas no torneio **{torneio}** no momento."
                
                embed = create_info_embed("Nenhuma partida encontrada", msg)
                await interaction.followup.send(embed=embed)
                return
            
            # Criar embeds para cada partida - augmentar em paralelo
            augmented_matches = await asyncio.gather(
                *[augment_match_with_streams(m, self.bot.cache_manager) for m in matches[:quantidade]],
                return_exceptions=True
            )
            
            embeds = []
            for match in augmented_matches:
                try:
                    if isinstance(match, Exception):
                        logger.error(f"Erro ao augmentar match: {match}")
                        continue
                    embed = create_match_embed(match, timezone=timezone)
                    embeds.append(embed)
                except Exception as e:
                    logger.error(f"Erro ao criar embed: {e}")
            
            if not embeds:
                embed = create_error_embed(
                    "Erro ao processar partidas",
                    "Não foi possível processar as informações das partidas.",
                    timezone=timezone
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Enviar resposta
            title = f"**📋 Próximas {len(embeds)} partidas"
            if time:
                title += f" de {time}"
            if torneio:
                title += f" no torneio {torneio}"
            title += ":** (cache atualizado)"
            
            await interaction.followup.send(
                content=title,
                embeds=embeds[:10]  # Discord limita a 10 embeds por mensagem
            )
            
            logger.info(f"✓ Comando /partidas futuras executado por {interaction.user} (Filtro: {time}, Torneio: {torneio})")
            
        except Exception as e:
            logger.error(f"✗ Erro no comando /partidas futuras: {e}")
            embed = create_error_embed(
                "Erro ao buscar partidas",
                f"Ocorreu um erro ao consultar o cache: {str(e)}",
                timezone=timezone
            )
            await interaction.followup.send(embed=embed)
    
    @partidas.subcommand(name="ao_vivo", description="Mostra partidas de CS2 acontecendo agora")
    async def ao_vivo(
        self, 
        interaction: nextcord.Interaction,
        time: str = SlashOption(
            name="time",
            description="Filtrar por nome do time (ex: Furia)",
            required=False
        ),
        torneio: str = SlashOption(
            name="torneio",
            description="Filtrar por nome do torneio (ex: Major)",
            required=False
        )
    ):
        """Lista partidas ao vivo (do cache rápido)."""
        await interaction.response.defer()
        
        try:
            # 🌍 Obter timezone do guild
            timezone = await self.bot.cache_manager.get_guild_timezone(interaction.guild_id) or "America/Sao_Paulo"
            logger.info(f"🌍 /partidas ao_vivo: Timezone do servidor = {timezone}")
            # Primeiro: tentar cache em memória (muito rápido!)
            matches = await self.bot.cache_manager.get_cached_matches_fast("running", 10, team_name=time, tournament_name=torneio)
            
            # Se vazio: buscar do banco (mais lento)
            if not matches:
                logger.info("Cache em memória vazio, buscando do banco...")
                matches = await self.bot.cache_manager.get_cached_matches(
                    status="running",
                    limit=10,
                    team_name=time,
                    tournament_name=torneio
                )
            
            # Última opção: API
            if not matches:
                logger.info("Nenhuma partida ao vivo no cache, buscando da API...")
                all_matches = await self.bot.api_client.get_running_matches()
                matches = self._filter_matches_by_team(all_matches, time)
                matches = self._filter_matches_by_tournament(matches, torneio)
            
            if not matches:
                msg = "Não há partidas acontecendo no momento."
                if time:
                    msg = f"Não há partidas de **{time}** acontecendo no momento."
                if torneio:
                    if time:
                        msg = f"Não há partidas de **{time}** no torneio **{torneio}** acontecendo no momento."
                    else:
                        msg = f"Não há partidas no torneio **{torneio}** acontecendo no momento."
                    
                embed = create_info_embed("Nenhuma partida ao vivo", msg, timezone=timezone)
                await interaction.followup.send(embed=embed)
                return
            
            # Augmentar todos os matches com streams em paralelo
            augmented_matches = await asyncio.gather(
                *[augment_match_with_streams(m, self.bot.cache_manager) for m in matches[:10]],
                return_exceptions=True
            )
            
            embeds = []
            for match in augmented_matches:
                try:
                    if isinstance(match, Exception):
                        logger.error(f"Erro ao augmentar match: {match}")
                        continue
                    embed = create_match_embed(match, timezone=timezone)
                    embeds.append(embed)
                except Exception as e:
                    logger.error(f"Erro ao criar embed: {e}")
            
            if embeds:
                title = f"**🔴 {len(embeds)} partida(s) ao vivo"
                if time:
                    title += f" de {time}"
                title += ":** (cache atualizado)"
                
                await interaction.followup.send(
                    content=title,
                    embeds=embeds
                )
            
            logger.info(f"✓ Comando /partidas ao_vivo executado por {interaction.user} (Filtro: {time})")
            
        except Exception as e:
            logger.error(f"✗ Erro no comando /partidas ao_vivo: {e}")
            embed = create_error_embed(
                "Erro ao buscar partidas",
                f"Ocorreu um erro: {str(e)}",
                timezone=timezone
            )
            await interaction.followup.send(embed=embed)
    
    @partidas.subcommand(name="resultados", description="Mostra os resultados das últimas 24h")
    async def resultados(
        self, 
        interaction: nextcord.Interaction,
        quantidade: int = SlashOption(
            name="quantidade",
            description="Número de resultados (padrão: 10)",
            required=False,
            default=10,
            min_value=1,
            max_value=20
        ),
        time: str = SlashOption(
            name="time",
            description="Filtrar por nome do time (ex: Furia)",
            required=False
        ),
        torneio: str = SlashOption(
            name="torneio",
            description="Filtrar por nome do torneio (ex: Major)",
            required=False
        )
    ):
        """Lista os resultados das últimas 24h (do cache rápido)."""
        try:
            await interaction.response.defer()
            timezone = await self.bot.cache_manager.get_guild_timezone(interaction.guild_id) or "America/Sao_Paulo"
            logger.info(f"🌍 /partidas resultados: Timezone do servidor = {timezone}")
            
            # Primeiro: tentar cache em memória
            matches = await self.bot.cache_manager.get_cached_matches_fast("finished", quantidade, team_name=time, tournament_name=torneio)
            
            # Se vazio: buscar do banco
            if not matches:
                matches = await self.bot.cache_manager.get_cached_matches(
                    status="results",
                    limit=quantidade,
                    team_name=time,
                    tournament_name=torneio
                )
            
            # Última opção: API
            if not matches:
                logger.info("Nenhum resultado no cache, buscando da API...")
                all_matches = await self.bot.api_client.get_finished_matches()
                matches = self._filter_matches_by_team(all_matches, time)
                matches = self._filter_matches_by_tournament(matches, torneio)
                matches = matches[:quantidade]
            
            if not matches:
                msg = "Nenhum resultado encontrado nas últimas 24h."
                if time:
                    msg = f"Nenhum resultado de **{time}** encontrado nas últimas 24h."
                if torneio:
                    if time:
                        msg = f"Nenhum resultado de **{time}** no torneio **{torneio}** encontrado nas últimas 24h."
                    else:
                        msg = f"Nenhum resultado no torneio **{torneio}** encontrado nas últimas 24h."
                    
                embed = create_info_embed("Nenhum resultado recente", msg, timezone=timezone)
                await interaction.followup.send(embed=embed)
                return

            embeds = []
            for match in matches:
                embed = create_match_embed(match, timezone=timezone)
                embeds.append(embed)
            
            title = f"**🏆 Últimos {len(embeds)} resultados"
            if time:
                title += f" de {time}"
            if torneio:
                title += f" no torneio {torneio}"
            title += ":**"
            
            await interaction.followup.send(
                content=title,
                embeds=embeds[:10]
            )
            
            logger.info(f"✓ Comando /partidas resultados executado por {interaction.user} (Filtro: {time}, Torneio: {torneio})")
            
        except Exception as e:
            logger.error(f"✗ Erro no comando /partidas resultados: {e}")
            embed = create_error_embed(
                "Erro ao buscar resultados",
                f"Ocorreu um erro: {str(e)}",
                timezone=timezone
            )
            await interaction.followup.send(embed=embed)


def setup(bot):
    """Adiciona o cog ao bot."""
    bot.add_cog(MatchesCog(bot))
