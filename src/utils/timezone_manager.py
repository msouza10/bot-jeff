"""
🕐 Gerenciador de Timezone para BOT Jeff

Estratégia:
1. Todos os dados no banco estão em UTC (não mudam)
2. Conversão acontece apenas na EXIBIÇÃO (embeds, mensagens, etc)
3. Cada servidor Discord tem seu próprio timezone configurável
4. Detecção automática por IP do servidor (fallback para America/Sao_Paulo)
5. Usuários podem fazer override manual com /timezone

Exemplo:
  - Jogo às 15:00 UTC
  - No Brasil (UTC-3): 12:00
  - Na Europa (UTC+1): 16:00
"""

import logging
from datetime import datetime, timezone as dt_timezone
from typing import Optional
import pytz

logger = logging.getLogger(__name__)

# Mapa de timezones comuns por região/país
COMMON_TIMEZONES = {
    # Brasil
    "brazil": "America/Sao_Paulo",
    "pt-BR": "America/Sao_Paulo",
    "br": "America/Sao_Paulo",
    
    # EUA
    "usa": "America/New_York",
    "us": "America/New_York",
    "en-US": "America/New_York",
    
    # Europa
    "eu": "Europe/London",
    "europe": "Europe/London",
    "en-GB": "Europe/London",
    
    # Ásia
    "asia": "Asia/Tokyo",
    "ja": "Asia/Tokyo",
    
    # UTC (fallback)
    "utc": "UTC",
    "default": "America/Sao_Paulo",  # Default para Brasil
}

# Timezones válidos do pytz
VALID_TIMEZONES = pytz.all_timezones

# Mapa manual de timezone -> abreviação
# pytz.strftime("%Z") frequentemente retorna offset como "-03" ao invés de "BRT"
# Essa tabela garante os nomes corretos
TIMEZONE_ABBREVIATIONS = {
    # 
    # Americas (South/Latin America)
    "America/Sao_Paulo": "BRT",
    "America/Fortaleza": "BRT",
    "America/Belem": "BRT",
    "America/Maceio": "BRT",
    "America/Bahia": "BRT",
    "America/Araguaina": "BRT",
    "America/Recife": "BRT",
    "America/Noronha": "FNT",
    "America/Manaus": "AMT",
    "America/Boa_Vista": "AMT",
    "America/Campo_Grande": "AMT",
    "America/Eirunepe": "ACT",
    "America/Rio_Branco": "ACT",
    "America/Montevideo": "UYT",
    "America/Asuncion": "PYT",
    "America/La_Paz": "BOT",
    "America/Santiago": "CLT",
    "America/Bogota": "COT",
    "America/Lima": "PET",

    # North America (US/Canada/Mexico)
    "America/New_York": {"std": "EST", "dst": "EDT"},
    "America/Toronto": "EST",
    "America/Chicago": {"std": "CST", "dst": "CDT"},
    "America/Winnipeg": "CST",
    "America/Denver": {"std": "MST", "dst": "MDT"},
    "America/Phoenix": "MST",
    "America/Edmonton": "MST",
    "America/Los_Angeles": {"std": "PST", "dst": "PDT"},
    "America/Vancouver": "PST",
    "America/Mexico_City": "CST",
    "America/Guatemala": "CST",

    # Caribbean
    "America/Havana": "CST",
    "America/Santo_Domingo": "AST",

    # Atlantic
    "America/Halifax": "ADT",
    "America/St_Johns": "NST",

    # Europe
    "Europe/London": {"std": "GMT", "dst": "BST"},
    "Europe/Dublin": "GMT",
    "Europe/Lisbon": "WET",
    "Europe/Paris": {"std": "CET", "dst": "CEST"},
    "Europe/Berlin": {"std": "CET", "dst": "CEST"},
    "Europe/Madrid": {"std": "CET", "dst": "CEST"},
    "Europe/Amsterdam": {"std": "CET", "dst": "CEST"},
    "Europe/Brussels": {"std": "CET", "dst": "CEST"},
    "Europe/Vienna": "CET",
    "Europe/Rome": "CET",
    "Europe/Stockholm": "CET",
    "Europe/Oslo": "CET",
    "Europe/Copenhagen": "CET",
    "Europe/Warsaw": "CET",
    "Europe/Prague": "CET",
    "Europe/Budapest": "CET",
    "Europe/Athens": "EET",
    "Europe/Istanbul": "TRT",
    "Europe/Moscow": "MSK",

    # Africa
    "Africa/Johannesburg": "SAST",
    "Africa/Cairo": "EET",
    "Africa/Maputo": "CAT",
    "Africa/Nairobi": "EAT",

    # Asia
    "Asia/Tokyo": "JST",
    "Asia/Seoul": "KST",
    "Asia/Shanghai": "CST",
    "Asia/Hong_Kong": "HKT",
    "Asia/Singapore": "SGT",
    "Asia/Bangkok": "ICT",
    "Asia/Jakarta": "WIB",
    "Asia/Kuala_Lumpur": "MYT",
    "Asia/Dubai": "GST",
    "Asia/Kolkata": "IST",
    "Asia/Kathmandu": "NPT",
    "Asia/Ho_Chi_Minh": "ICT",

    # Oceania
    "Australia/Sydney": {"std": "AEST", "dst": "AEDT"},
    "Australia/Melbourne": {"std": "AEST", "dst": "AEDT"},
    "Australia/Brisbane": "AEST",
    "Australia/Adelaide": "ACST",
    "Australia/Perth": "AWST",
    "Pacific/Auckland": "NZST",
    "Pacific/Fiji": "FJT",

    # Common UTC aliases
    "UTC": "UTC",
    "Etc/UTC": "UTC",
    "GMT": "GMT",
}


class TimezoneManager:
    """
    Gerencia conversão de timestamps entre UTC e timezones locais.
    
    Todos os dados no banco estão em UTC.
    Conversão acontece apenas para exibição.
    """
    
    @staticmethod
    def get_default_timezone() -> str:
        """
        Retorna timezone padrão (Brasil).
        
        Returns:
            str: "America/Sao_Paulo"
        """
        return "America/Sao_Paulo"
    
    @staticmethod
    def get_timezone_for_locale(locale: str) -> str:
        """
        Retorna timezone baseado no locale (idioma/país).
        
        Args:
            locale: Idioma/país (ex: "pt-BR", "en-US", "ru")
            
        Returns:
            str: Timezone válido do pytz
        """
        locale_lower = locale.lower().replace("_", "-")
        
        # Procurar correspondência exata
        if locale_lower in COMMON_TIMEZONES:
            return COMMON_TIMEZONES[locale_lower]
        
        # Procurar por prefixo (ex: pt-BR -> pt)
        prefix = locale_lower.split("-")[0]
        if prefix in COMMON_TIMEZONES:
            return COMMON_TIMEZONES[prefix]
        
        # Fallback
        return COMMON_TIMEZONES["default"]
    
    @staticmethod
    def is_valid_timezone(tz_name: str) -> bool:
        """
        Verifica se um timezone é válido no pytz.
        
        Args:
            tz_name: Nome do timezone (ex: "America/Sao_Paulo")
            
        Returns:
            bool: True se válido
        """
        return tz_name in VALID_TIMEZONES
    
    @staticmethod
    def convert_utc_to_timezone(
        utc_datetime: Optional[datetime],
        timezone_name: str
    ) -> Optional[datetime]:
        """
        Converte um datetime UTC para um timezone específico.
        
        Args:
            utc_datetime: datetime em UTC (com ou sem timezone info)
            timezone_name: Nome do timezone (ex: "America/Sao_Paulo")
            
        Returns:
            datetime com timezone convertido, ou None se inválido
            
        Exemplo:
            >>> dt = datetime(2025, 11, 18, 15, 0, 0)  # 15:00 UTC
            >>> converted = TimezoneManager.convert_utc_to_timezone(dt, "America/Sao_Paulo")
            >>> converted.strftime("%H:%M")
            '12:00'  # 15:00 UTC -> 12:00 BRT (UTC-3)
        """
        if not utc_datetime:
            return None
        
        # Validar timezone
        if not TimezoneManager.is_valid_timezone(timezone_name):
            logger.warning(f"⚠️ Timezone inválido: {timezone_name}, usando UTC")
            return utc_datetime
        
        try:
            # Se não tiver timezone, assumir UTC
            if utc_datetime.tzinfo is None:
                utc_datetime = pytz.UTC.localize(utc_datetime)
            elif utc_datetime.tzinfo != pytz.UTC:
                # Se tiver timezone diferente, converter para UTC
                utc_datetime = utc_datetime.astimezone(pytz.UTC)
            
            # Converter para timezone desejado
            tz = pytz.timezone(timezone_name)
            converted = utc_datetime.astimezone(tz)
            
            return converted
            
        except Exception as e:
            logger.error(f"❌ Erro ao converter timezone: {e}")
            return utc_datetime
    
    @staticmethod
    def format_datetime_for_display(
        dt: Optional[datetime],
        timezone_name: str,
        format_str: str = "%d/%m/%Y %H:%M"
    ) -> Optional[str]:
        """
        Converte datetime UTC e formata para exibição com timezone.
        
        Args:
            dt: datetime em UTC
            timezone_name: Nome do timezone
            format_str: Formato strftime desejado
            
        Returns:
            String formatada com horário convertido
            
        Exemplo:
            >>> dt = datetime(2025, 11, 18, 15, 0, 0)
            >>> formatted = TimezoneManager.format_datetime_for_display(
            ...     dt, "America/Sao_Paulo", "%d/%m %H:%M"
            ... )
            >>> formatted
            '18/11 12:00'
        """
        converted = TimezoneManager.convert_utc_to_timezone(dt, timezone_name)
        if not converted:
            return None
        
        try:
            return converted.strftime(format_str)
        except Exception as e:
            logger.error(f"❌ Erro ao formatar datetime: {e}")
            return None
    
    @staticmethod
    def get_timezone_abbreviation(timezone_name: str, dt: Optional[datetime] = None) -> str:
        """
        Retorna abreviação do timezone.
        
        IMPORTANTE: Usa tabela manual porque pytz.strftime("%Z") frequentemente
        retorna offset como "-03" ao invés de "BRT" para horário de verão.
        
        Args:
            timezone_name: Nome do timezone
            dt: Optional datetime to determine DST-aware abbreviation (if provided)
            
        Returns:
            str: Abreviação (ex: "BRT", "EST", "CET")
            Note: `TIMEZONE_ABBREVIATIONS` entries may be either a string or a dict like {"std":"EST","dst":"EDT"}.
            
        Exemplo:
            >>> TimezoneManager.get_timezone_abbreviation("America/Sao_Paulo")
            'BRT'  # Brazil Time
        """
        if not TimezoneManager.is_valid_timezone(timezone_name):
            return "UTC"
        
        # ✅ Use mapping as single source of truth for abbreviation
        abbr_entry = TIMEZONE_ABBREVIATIONS.get(timezone_name)
        if abbr_entry:
            # If it's a simple string, return it
            if isinstance(abbr_entry, str):
                return abbr_entry
            # If it's a dict with 'std'/'dst', decide based on dt (if present) or current time
            if isinstance(abbr_entry, dict):
                try:
                    # If dt is not provided, use current time in the timezone
                    tz = pytz.timezone(timezone_name)
                    if dt is None:
                        dt_local = datetime.now(tz)
                    else:
                        dt_local = dt.astimezone(tz)
                    # choose DST if present
                    dt_dst = dt_local.dst()
                    if dt_dst and getattr(dt_dst, "total_seconds", lambda: 0)() != 0:
                        return abbr_entry.get("dst") or abbr_entry.get("std") or "UTC"
                    return abbr_entry.get("std") or list(abbr_entry.values())[0]
                except Exception:
                    # fallback to 'std' if anything fails
                    return abbr_entry.get("std") or "UTC"

        # If mapping is not found, fallback to UTC offset format as a clear indicator
        try:
            offset = TimezoneManager.get_timezone_offset(timezone_name)
            return offset if offset else "UTC"
        except Exception:
            return "UTC"
    
    @staticmethod
    def get_timezone_offset(timezone_name: str) -> str:
        """
        Retorna offset do timezone em relação a UTC.
        
        Args:
            timezone_name: Nome do timezone
            
        Returns:
            str: Offset (ex: "UTC-3", "UTC+1")
            
        Exemplo:
            >>> TimezoneManager.get_timezone_offset("America/Sao_Paulo")
            'UTC-3'
        """
        if not TimezoneManager.is_valid_timezone(timezone_name):
            return "UTC±0"
        
        try:
            tz = pytz.timezone(timezone_name)
            now = datetime.now(tz)
            offset = now.utcoffset()
            
            if offset is None:
                return "UTC±0"
            
            total_seconds = int(offset.total_seconds())
            hours = total_seconds // 3600
            minutes = (abs(total_seconds) % 3600) // 60
            
            sign = "+" if hours >= 0 else "-"
            hours = abs(hours)
            
            if minutes:
                return f"UTC{sign}{hours}:{minutes:02d}"
            else:
                return f"UTC{sign}{hours}"
        except Exception:
            return "UTC±0"
    
    @staticmethod
    def parse_iso_datetime(iso_string: str) -> Optional[datetime]:
        """
        Faz parse de datetime no formato ISO 8601 (formato da PandaScore API).
        
        Args:
            iso_string: String ISO 8601 (ex: "2025-11-18T15:00:00Z")
            
        Returns:
            datetime em UTC, ou None se inválido
            
        Exemplo:
            >>> dt = TimezoneManager.parse_iso_datetime("2025-11-18T15:00:00Z")
            >>> dt.tzinfo
            tzutc()
        """
        if not iso_string:
            return None
        
        try:
            # Normalizar: remover 'Z' e adicionar '+00:00'
            if iso_string.endswith('Z'):
                iso_string = iso_string[:-1] + '+00:00'
            
            dt = datetime.fromisoformat(iso_string)
            
            # Garantir timezone UTC
            if dt.tzinfo is None:
                dt = pytz.UTC.localize(dt)
            
            return dt
        except Exception as e:
            logger.warning(f"⚠️ Erro ao fazer parse de datetime: {iso_string} - {e}")
            return None
    
    @staticmethod
    def discord_timestamp(
        utc_datetime: Optional[datetime],
        timezone_name: str,
        format_type: str = "F"
    ) -> Optional[str]:
        """
        Gera timestamp do Discord que respeita timezone do cliente.
        
        O Discord converte automaticamente para timezone local do usuário.
        Este método retorna o timestamp UNIX do datetime convertido.
        
        Formatos Discord:
            - t: Short time (12:00)
            - T: Long time (12:00:34)
            - d: Short date (18/11/2025)
            - D: Long date (Tuesday, November 18, 2025)
            - f: Short date/time (18/11/2025 12:00)
            - F: Long date/time (Tuesday, November 18, 2025 12:00)
            - R: Relative (2 hours ago)
        
        Args:
            utc_datetime: datetime em UTC
            timezone_name: Nome do timezone (para referência)
            format_type: Tipo de formato Discord
            
        Returns:
            String formatada para Discord
            
        Exemplo:
            >>> dt = datetime(2025, 11, 18, 15, 0, 0)
            >>> timestamp = TimezoneManager.discord_timestamp(dt, "America/Sao_Paulo")
            >>> timestamp
            '<t:1747768800:F>'
        """
        if not utc_datetime:
            return None
        
        try:
            # Converter para UTC se necessário
            if utc_datetime.tzinfo is None:
                utc_datetime = pytz.UTC.localize(utc_datetime)
            elif utc_datetime.tzinfo != pytz.UTC:
                utc_datetime = utc_datetime.astimezone(pytz.UTC)
            
            # Obter timestamp UNIX
            unix_timestamp = int(utc_datetime.timestamp())
            
            return f"<t:{unix_timestamp}:{format_type}>"
        except Exception as e:
            logger.error(f"❌ Erro ao criar Discord timestamp: {e}")
            return None
    
    @staticmethod
    def get_server_timezone_emoji(timezone_name: str) -> str:
        """
        Retorna emoji para o timezone.
        
        Args:
            timezone_name: Nome do timezone
            
        Returns:
            str: Emoji representativo
        """
        tz_lower = timezone_name.lower()
        
        # Mapa de emojis por timezone
        emoji_map = {
            # América
            "america/sao_paulo": "🇧🇷",
            "america/new_york": "🇺🇸",
            "america/chicago": "🇺🇸",
            "america/denver": "🇺🇸",
            "america/los_angeles": "🇺🇸",
            "america/mexico_city": "🇲🇽",
            "america/argentina/buenos_aires": "🇦🇷",
            
            # Europa
            "europe/london": "🇬🇧",
            "europe/paris": "🇫🇷",
            "europe/berlin": "🇩🇪",
            "europe/madrid": "🇪🇸",
            "europe/rome": "🇮🇹",
            "europe/moscow": "🇷🇺",
            
            # Ásia
            "asia/tokyo": "🇯🇵",
            "asia/shanghai": "🇨🇳",
            "asia/hong_kong": "🇭🇰",
            "asia/bangkok": "🇹🇭",
            "asia/singapore": "🇸🇬",
            "asia/seoul": "🇰🇷",
            "asia/kolkata": "🇮🇳",
            
            # Oceania
            "australia/sydney": "🇦🇺",
            "pacific/auckland": "🇳🇿",
        }
        
        if tz_lower in emoji_map:
            return emoji_map[tz_lower]
        
        # Procurar por prefixo
        for tz_key, emoji in emoji_map.items():
            if tz_lower.startswith(tz_key.split("/")[0]):
                return emoji
        
        return "🌍"  # Fallback global
