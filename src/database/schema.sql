-- Schema do banco de dados para o BOT Jeff
-- SQLite Database Schema

-- Tabela de cache de partidas
CREATE TABLE IF NOT EXISTS matches_cache (
    id INTEGER PRIMARY KEY,
    match_id INTEGER UNIQUE NOT NULL,
    match_data TEXT NOT NULL,  -- JSON serializado da partida
    status TEXT NOT NULL,      -- not_started, running, finished
    tournament_name TEXT,
    begin_at DATETIME,
    end_at DATETIME,
    cached_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Índices para melhor performance
CREATE INDEX IF NOT EXISTS idx_matches_status ON matches_cache(status);
CREATE INDEX IF NOT EXISTS idx_matches_begin_at ON matches_cache(begin_at);
CREATE INDEX IF NOT EXISTS idx_matches_cached_at ON matches_cache(cached_at);
CREATE INDEX IF NOT EXISTS idx_matches_updated_at ON matches_cache(updated_at);

-- Tabela de configuração de guilds (servidores)
CREATE TABLE IF NOT EXISTS guild_config (
    guild_id INTEGER PRIMARY KEY,
    notification_channel_id INTEGER,
    notify_upcoming BOOLEAN DEFAULT 1,
    notify_live BOOLEAN DEFAULT 1,
    notify_results BOOLEAN DEFAULT 0,
    language TEXT DEFAULT 'pt-BR',
    timezone TEXT DEFAULT 'America/Sao_Paulo',  -- ✨ NEW: Timezone do servidor
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de times favoritos por guild
CREATE TABLE IF NOT EXISTS guild_favorite_teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    team_name TEXT NOT NULL,
    team_slug TEXT NOT NULL,
    added_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (guild_id) REFERENCES guild_config(guild_id) ON DELETE CASCADE,
    UNIQUE(guild_id, team_id)
);

CREATE INDEX IF NOT EXISTS idx_favorite_teams_guild ON guild_favorite_teams(guild_id);
CREATE INDEX IF NOT EXISTS idx_favorite_teams_team ON guild_favorite_teams(team_id);

-- Tabela de histórico de notificações (evita duplicatas)
CREATE TABLE IF NOT EXISTS notification_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    match_id INTEGER NOT NULL,
    notification_type TEXT NOT NULL,  -- upcoming, live, result
    sent_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (guild_id) REFERENCES guild_config(guild_id) ON DELETE CASCADE,
    UNIQUE(guild_id, match_id, notification_type)
);

CREATE INDEX IF NOT EXISTS idx_notification_history_guild ON notification_history(guild_id);
CREATE INDEX IF NOT EXISTS idx_notification_history_match ON notification_history(match_id);
CREATE INDEX IF NOT EXISTS idx_notification_history_sent_at ON notification_history(sent_at);

-- Tabela para rastrear lembretes agendados de partidas
CREATE TABLE IF NOT EXISTS match_reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    match_id INTEGER NOT NULL,
    reminder_minutes_before INTEGER NOT NULL,  -- 60, 30, 15, 5, 0 (em tempo real)
    scheduled_time DATETIME NOT NULL,           -- quando enviar o lembrete
    sent BOOLEAN DEFAULT 0,                     -- se o lembrete foi enviado
    sent_at DATETIME,
    FOREIGN KEY (guild_id) REFERENCES guild_config(guild_id) ON DELETE CASCADE,
    UNIQUE(guild_id, match_id, reminder_minutes_before)
);

CREATE INDEX IF NOT EXISTS idx_reminders_guild ON match_reminders(guild_id);
CREATE INDEX IF NOT EXISTS idx_reminders_match ON match_reminders(match_id);
CREATE INDEX IF NOT EXISTS idx_reminders_scheduled_time ON match_reminders(scheduled_time);
CREATE INDEX IF NOT EXISTS idx_reminders_sent ON match_reminders(sent);

-- Tabela para notificações de RESULTADO de partidas finalizadas
CREATE TABLE IF NOT EXISTS match_result_notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    match_id INTEGER NOT NULL,
    scheduled_time DATETIME NOT NULL,  -- Quando enviar (geralmente NOW)
    sent BOOLEAN DEFAULT 0,            -- Se a notificação foi enviada
    sent_at DATETIME,                  -- Quando foi enviada
    FOREIGN KEY (guild_id) REFERENCES guild_config(guild_id) ON DELETE CASCADE,
    UNIQUE(guild_id, match_id)         -- Uma notificação por partida por guild
);

CREATE INDEX IF NOT EXISTS idx_result_notif_guild ON match_result_notifications(guild_id);
CREATE INDEX IF NOT EXISTS idx_result_notif_match ON match_result_notifications(match_id);
CREATE INDEX IF NOT EXISTS idx_result_notif_scheduled ON match_result_notifications(scheduled_time);
CREATE INDEX IF NOT EXISTS idx_result_notif_sent ON match_result_notifications(sent);

-- Tabela para cache de streams de partidas
CREATE TABLE IF NOT EXISTS match_streams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id INTEGER NOT NULL,
    platform TEXT NOT NULL,         -- twitch, kick, youtube, etc
    channel_name TEXT NOT NULL,     -- Nome do canal
    url TEXT NOT NULL,              -- URL da stream
    raw_url TEXT,                   -- URL raw (sem embed)
    language TEXT NOT NULL,         -- Idioma (en, pt, ru, etc)
    is_official BOOLEAN DEFAULT 0,  -- true = stream oficial
    is_main BOOLEAN DEFAULT 0,      -- true = stream primária
    is_automated BOOLEAN DEFAULT 0, -- true = encontrada automaticamente (🤖)
    viewer_count INTEGER DEFAULT 0, -- Quantidade de viewers (para automatizadas)
    title TEXT,                     -- Título da stream (para automatizadas)
    cached_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (match_id) REFERENCES matches_cache(match_id) ON DELETE CASCADE,
    UNIQUE(match_id, platform, channel_name)
);

CREATE INDEX IF NOT EXISTS idx_streams_match ON match_streams(match_id);
CREATE INDEX IF NOT EXISTS idx_streams_official ON match_streams(is_official);
CREATE INDEX IF NOT EXISTS idx_streams_main ON match_streams(is_main);
CREATE INDEX IF NOT EXISTS idx_streams_language ON match_streams(language);

-- Tabela de logs de atualização do cache
CREATE TABLE IF NOT EXISTS cache_update_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    update_type TEXT NOT NULL,  -- upcoming, running, past, all
    matches_updated INTEGER DEFAULT 0,
    matches_added INTEGER DEFAULT 0,
    matches_removed INTEGER DEFAULT 0,
    duration_seconds REAL,
    status TEXT NOT NULL,       -- success, error, partial
    error_message TEXT,
    started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME
);

CREATE INDEX IF NOT EXISTS idx_cache_log_started_at ON cache_update_log(started_at);
CREATE INDEX IF NOT EXISTS idx_cache_log_status ON cache_update_log(status);

-- View para partidas ativas (últimas 24h ou futuras)
CREATE VIEW IF NOT EXISTS active_matches AS
SELECT 
    match_id,
    match_data,
    status,
    tournament_name,
    begin_at,
    end_at,
    cached_at,
    updated_at
FROM matches_cache
WHERE 
    status IN ('not_started', 'running')
    OR (status = 'finished' AND datetime(end_at) > datetime('now', '-24 hours'))
ORDER BY 
    CASE status
        WHEN 'running' THEN 1
        WHEN 'not_started' THEN 2
        WHEN 'finished' THEN 3
    END,
    begin_at ASC;

-- View para estatísticas do cache
CREATE VIEW IF NOT EXISTS cache_stats AS
SELECT 
    COUNT(*) as total_matches,
    SUM(CASE WHEN status = 'not_started' THEN 1 ELSE 0 END) as upcoming_matches,
    SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) as live_matches,
    SUM(CASE WHEN status = 'finished' THEN 1 ELSE 0 END) as finished_matches,
    SUM(CASE WHEN datetime(updated_at) > datetime('now', '-15 minutes') THEN 1 ELSE 0 END) as recently_updated,
    MIN(updated_at) as oldest_update,
    MAX(updated_at) as newest_update
FROM matches_cache;
