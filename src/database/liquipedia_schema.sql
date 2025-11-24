-- Schema para o cache da Liquipedia API (separado do bot.db)

-- Tabela genérica para cache de respostas da API
CREATE TABLE IF NOT EXISTS api_cache (
    endpoint TEXT NOT NULL,
    params TEXT NOT NULL,       -- JSON string dos parâmetros
    response_json TEXT,         -- JSON da resposta (pode ser NULL se erro)
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME,        -- Quando esse cache expira
    PRIMARY KEY (endpoint, params)
);

-- Tabela específica para Jogadores (com todos os campos da API)
CREATE TABLE IF NOT EXISTS players (
    id TEXT PRIMARY KEY,        -- ID da Liquipedia (ex: "FalleN")
    pageid INTEGER,
    pagename TEXT,
    alternateid TEXT,
    name TEXT,                  -- Nome real
    localizedname TEXT,
    type TEXT,                  -- "player"
    nationality TEXT,
    nationality2 TEXT,
    nationality3 TEXT,
    region TEXT,
    birthdate TEXT,
    deathdate TEXT,
    teampagename TEXT,
    teamtemplate TEXT,
    links TEXT,                 -- JSON
    status TEXT,
    earnings INTEGER,
    earningsbyyear TEXT,        -- JSON
    extradata TEXT,             -- JSON (roles, etc.)
    data_json TEXT,             -- JSON completo do jogador
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Tabela específica para Times (com todos os campos da API)
CREATE TABLE IF NOT EXISTS teams (
    id TEXT PRIMARY KEY,        -- pagename (ex: "FURIA")
    pageid INTEGER,
    name TEXT,
    locations TEXT,             -- JSON
    region TEXT,
    logo TEXT,
    logourl TEXT,
    logodark TEXT,
    logodarkurl TEXT,
    textlesslogourl TEXT,
    textlesslogodarkurl TEXT,
    status TEXT,
    createdate TEXT,
    disbanddate TEXT,
    earnings INTEGER,
    earningsbyyear TEXT,        -- JSON
    template TEXT,
    links TEXT,                 -- JSON
    extradata TEXT,             -- JSON
    data_json TEXT,             -- JSON completo
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_api_cache_expires ON api_cache(expires_at);
CREATE INDEX IF NOT EXISTS idx_players_name ON players(name);
CREATE INDEX IF NOT EXISTS idx_players_teampagename ON players(teampagename);
