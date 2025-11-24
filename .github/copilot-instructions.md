# AI Agent Instructions for bot-hltv

**Project**: Discord bot for CS2 (Counter-Strike 2) match notifications with live stream detection via PandaScore API  
**Stack**: Python 3.10+, Nextcord, libSQL (Turso), APScheduler, Twitch/YouTube APIs  
**Status**: Production-ready with 42h temporal cache, multi-stream support, and result notifications

## Architecture Overview

### High-Level Data Flow

```
PandaScore API ──→ pandascore_service.py ──→ cache_scheduler.py
      ↓                                             ↓
streams_list                        cache_matches() + cache_streams()
      ↓                                             ↓
{twitch, kick, youtube, ...} ──→ temporal_cache.py (42h window)
                                     ↓
                        libSQL Cache (match_streams table)
                                     ↓
augment_match_with_streams() ──→ embeds.py (with 📡 Streams field)
                                     ↓
NotificationManager (5-point reminders + result notifications)
                                     ↓
                        Discord Guild Channels
```

**Key insights**:
- **Temporal coverage**: 42-hour sliding window ensures consistent data freshness
- **Stream integration**: Automatic detection from PandaScore `streams_list` API field
- **3-tier cache**: Memory (fast) → DB (persistent) → API fallback (graceful degradation)
- **Parallel augmentation**: Matches augmented with streams concurrently before embed creation
- **Fast interactions**: <3s timeout enforced, memory cache prioritized

### Core Components

1. **bot.py**: Entry point. Initializes in order: PandaScoreClient → MatchCacheManager → NotificationManager → CacheScheduler. Loads cogs and manages Discord lifecycle.

2. **pandascore_service.py**: Async HTTP client for CS2 endpoints (`/upcoming`, `/running`, `/past?filter=finished`, `/past?filter=canceled`). Returns match objects with **`streams_list` array** for each match. Rate limit: 1000 req/h with exponential backoff.

3. **cache_scheduler.py**: Discord Tasks-based scheduler running:
   - `update_all_matches()`: Every 15 min (50 upcoming + 2 running + 20 finished)
   - `update_live_matches()`: Every 5 min (only running matches)
   - Ensures matches stay within **42-hour temporal window** via `temporal_cache.py`

4. **cache_manager.py**: libSQL async operations with locks for race conditions. Implements dual cache:
   - `get_cached_matches_fast()`: In-memory dict (<100ms)
   - `get_cached_matches()`: DB queries with indices (<3s)
   - New: `cache_streams()`, `get_match_streams()` for stream persistence

5. **temporal_cache.py**: Maintains 42-hour sliding window. Queries `begin_at` field to keep cache relevant without manual cleanup.

6. **{twitch_search_service, youtube_service}.py**: Optional enrichment for Twitch/YouTube stream metadata (used when `streams_list` is sparse).

7. **notification_manager.py**: Schedules reminders at [60, 30, 15, 5, 0] minutes before match. Fetches augmented matches with streams for reminder embeds.

8. **cogs/{matches, notifications, ping}.py**: Slash commands (`/partidas`, `/aovivo`, `/resultados`, `/notificacoes`). All commands call `augment_match_with_streams()` before embed creation.

### Database Schema

**Critical tables**:
- `matches_cache`: Match data as JSON with status (not_started/running/finished/canceled), indexed by `begin_at` and `status`
- `match_streams` ✨ NEW: Platform, channel_name, language, official/main flags. Foreign key to matches_cache. Indexed for fast lookups.
- `match_reminders`: Reminder scheduling (guild_id, match_id, minutes_before, scheduled_time, sent flag)
- `guild_config`: Per-guild notification settings with `notification_channel_id`
- `guild_favorite_teams`: Team filtering by guild
- `notification_history`: Deduplication using (guild_id, match_id, notification_type) UNIQUE constraint

## Developer Workflows

### Running the Bot
```bash
source venv/bin/activate
python -m src.bot
```

### Database Setup
```bash
python -m src.database.build_db  # Creates/resets schema
```

### Debugging
- Check logs in `logs/bot.log` (auto-created with UTF-8)
- Use scripts in `scripts/check_*.py` for API/cache inspection
- `scripts/monitor_reminders_realtime.py` for notification flow tracing

### Adding New Features
1. If it's a slash command: Create in `src/cogs/` with Nextcord decorators (`@nextcord.slash_command`)
2. If it accesses cache: Use `self.bot.cache_manager` (await-based async)
3. If it needs scheduling: Add task to `CacheScheduler` using `@tasks.loop()`
4. Always handle `asyncio.TimeoutError` and db connection failures gracefully

## Project-Specific Conventions

### Async Patterns
- **Never block**: All I/O uses `async`/`await`. Use `asyncio.Lock()` for shared state.
- **Timeout enforcement**: `MatchCacheManager.QUERY_TIMEOUT = 3.0` prevents Discord interaction timeouts. Always wrap DB calls in try/except.
- **Session pooling**: `pandascore_service.py` reuses single `aiohttp.ClientSession` (lazily created in `_get_session()`).

### Logging
- Use `logging.getLogger(__name__)` in every module
- Log format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- UTF-8 encoding hardcoded for Windows compatibility (see `bot.py` line 31-33)
- Include emoji prefixes for clarity: ✅ success, ✗ error, ⏰ scheduled, 📅 time-related, etc.

### Cache Hierarchy (Critical Pattern)
1. **Memory cache** (`_memory_cache` dict): <100ms, holds recent results
2. **libSQL DB**: <3s, persistent across restarts
3. **API fallback**: If cache fails, fetch live (expensive, avoid in hot paths)

Example in `matches.py`:
```python
matches = await self.bot.cache_manager.get_cached_matches_fast("upcoming", 5)
if not matches:  # Fallback to DB
    matches = await self.bot.cache_manager.get_cached_matches("not_started", 5)
```

### Error Handling Conventions
- HTTP errors from API: Log, return empty list (graceful degradation)
- DB connection errors: Respect `QUERY_TIMEOUT`, retry if transient
- Invalid match data: Skip silently (don't crash scheduler)
- Discord interaction failures: Acknowledge with error embed using `create_error_embed()`

### Embed Formatting
All embeds use `src/utils/embeds.py` functions:
- `create_match_embed()`: For upcoming/running (blue ⏰ / red 🔴)
- `create_result_embed()`: For finished/canceled (green ✅)
- `create_error_embed()`: For failures
- Colors mapped in `color_map` dict; status emoji in `status_emoji` dict

### Notification Deduplication
Prevent spam via `notification_history` table:
```python
UNIQUE(guild_id, match_id, notification_type)  # Enforced in schema.sql
```
Always check `notification_history` before sending; mark sent in `match_reminders.sent_at`.

## Integration Points & External Dependencies

### PandaScore API
- Base URL: `https://api.pandascore.co`
- Auth: Bearer token in header
- Rate limit: 1000 requests/hour
- Key endpoints:
  - `GET /csgo/matches/upcoming` (50 per_page default)
  - `GET /csgo/matches/running` (no pagination needed)
  - `GET /csgo/matches/past?filter[status]=finished`
  - `GET /csgo/matches/past?filter[status]=canceled`
- **Key Field**: `streams_list` array contains stream metadata (platform, channel, language, official flags)

#### ⚠️ CRITICAL: PandaScore API Response Variations by Match Status

**ALWAYS consider these differences when processing match data:**

1. **UPCOMING** (`status: "not_started"`)
   - ✅ `begin_at`: ALWAYS populated (ISO 8601 timestamp)
   - ✅ `scheduled_at`: Equals `begin_at`
   - ❌ `end_at`: Always null
   - ❌ `winner`: Always null
   - ✅ `games[*].status`: All "not_started"
   - ✅ `results[*].score`: Both 0

2. **RUNNING** (`status: "running"`)
   - ✅ `begin_at`: Actual start time (may differ from `scheduled_at`)
   - ✅ `scheduled_at`: Original planned time
   - ❌ `end_at`: Always null (match in progress)
   - ❌ `winner`: Always null (undecided)
   - 🔀 `games[*].status`: Mix of "finished" (completed games) and "running" (current game)
   - ✅ `games[*].length`: Duration in seconds for finished games
   - ✅ `results[*].score`: Partial score (e.g., 1-1 for 2 games played)

3. **FINISHED/CANCELED** (`status: "finished"` or `"canceled"`)
   - ❌ `begin_at`: **ALWAYS null** (no temporal data in historical data!)
   - ❌ `scheduled_at`: Always null
   - ❌ `end_at`: Always null (API limitation)
   - ✅ `winner`: Populated for finished matches, null for canceled
   - ✅ `winner_id`: Team ID of winner (if finished)
   - ✅ `games[*].status`: All "finished"
   - ✅ `results[*].score`: Final score (loser: 0, winner: 2 for BO3)
   - ⚠️ `games[*].begin_at`: May be null even when finished
   - ⚠️ `games[*].end_at`: May be null even when finished
   - **FALLBACK**: Use `modified_at` timestamp as proxy for when match occurred

**Response Headers (always check):**
- `X-Rate-Limit-Remaining`: Stop if < 50 (hourly quota near limit)
- `X-Total`: Total matches available (check if more pages needed)
- `X-Page` / `X-Per-Page`: Pagination info
- `Link`: Contains `rel="next"` URL for pagination

**Edge Cases to Handle:**
- `opponents[*].dark_mode_image_url`: Can be null → fallback to `image_url`
- `opponents[*].acronym`: Can be null → fallback to first 3 chars of `name`
- `opponents[*].location`: Can be empty string → handle as "Unknown"
- `tournament.prizepool`: Can be null → display as "N/A"
- `games[*].forfeit`: true = non-competitive win (add "W.O." badge)
- `games[*].length`: null for some finished games (partial data)

**See `docs/ANALISE_ESTRUTURA_API_PANDASCORE.md` for complete field reference.**

### Discord via Nextcord
- Slash command registration: Use `@nextcord.slash_command(name="...", description="...")` decorator
- Interactions must defer with `await interaction.response.defer()` if >3s processing expected
- Use `nextcord.Intents.default()` with `guilds=True` and `guild_messages=True`
- Set `default_guild_ids` to TESTING_GUILD_ID for instant command propagation (vs 1h global)

### Twitch & YouTube Services
- **TwitchSearchService**: Fallback search when `streams_list` is sparse. Uses OAuth2 client credentials flow. Token cached 1h.
- **YouTubeService**: Extracts channel info from YouTube URLs. Supports video IDs, channel handles, and live URLs. Optional (YOUTUBE_API_KEY in .env).
- Both services are **optional enrichment** - primary stream data comes from PandaScore `streams_list`

### Temporal Cache (42-hour window)
- **Purpose**: Keep cache relevant without manual cleanup. Uses `begin_at` field for temporal ordering.
- **Implementation**: `temporal_cache.py` maintains sliding window. Queries filter by `begin_at >= now - 42h` and `begin_at <= now + some_buffer`
- **Used by**: Cache scheduler to decide which matches to keep, avoiding stale data
- **Pattern**: Call `ensure_temporal_coverage()` before rendering match lists

### libSQL (Turso)
- Connection: `libsql_client.create_client(url=db_url, auth_token=auth_token)`
- Local dev: `file:./data/bot.db`
- Remote prod: `libsql://...` with auth_token
- Always use connection pooling; call `client.execute()` for queries

### Environment Variables (`.env`)
```
DISCORD_TOKEN=<bot_token>
PANDASCORE_API_KEY=<api_key>
TESTING_GUILD_ID=<guild_id>  # For instant command registration
LIBSQL_URL=file:./data/bot.db  # Or libsql://... for Turso
LIBSQL_AUTH_TOKEN=<optional_auth>  # Only for remote DB
```

## Common Pitfalls & Solutions

| Issue | Solution |
|-------|----------|
| Slash commands don't appear for 1h | Set `TESTING_GUILD_ID` for instant propagation |
| `asyncio.TimeoutError` on interaction | Check if DB query exceeds `QUERY_TIMEOUT` (3s); use memory cache first |
| Duplicate notifications sent | Always check `notification_history` BEFORE sending; race conditions need `asyncio.Lock()` |
| API rate limit hit | Backoff with exponential delay; cache handles this—don't retry immediately |
| Match data incomplete (null fields) | Check PandaScore API response; skip invalid matches in cache logic |
| UTF-8 encoding errors on Windows | Already fixed in `bot.py` (lines 31-33); don't remove |

## Directory Organization Map

**CRITICAL**: Always respect this hierarchy. Create new files ONLY in their designated directories.

### `/src/` - Production Code (Core Application)
```
src/
├── bot.py                              # Bot initialization & lifecycle (never move)
├── cogs/                               # Discord slash commands
│   ├── __init__.py
│   ├── matches.py                      # /partidas, /aovivo, /resultados commands
│   ├── notifications.py                # /notificacoes, /canal-notificacoes commands
│   └── ping.py                         # /ping health check
├── database/                           # Persistence layer
│   ├── __init__.py
│   ├── build_db.py                     # Database initialization
│   ├── cache_manager.py                # libSQL cache operations
│   ├── schema.sql                      # Database schema (never edit manually)
│   └── debug_cache.py                  # Cache debugging utilities
├── services/                           # Business logic & integrations
│   ├── __init__.py
│   ├── pandascore_service.py           # PandaScore API client
│   ├── cache_scheduler.py              # Background task scheduling
│   └── notification_manager.py         # Reminder & notification scheduling
└── utils/                              # Shared utilities
    ├── __init__.py
    └── embeds.py                       # Discord embed formatting functions
```

**Rules**:
- ✅ Add slash commands: `/src/cogs/new_feature.py`
- ✅ Add API integrations: `/src/services/new_service.py`
- ✅ Add utilities: `/src/utils/new_utility.py`
- ✅ Add database tables: Modify `/src/database/schema.sql`, then run `build_db.py`
- ❌ NEVER create production files outside `src/`

### `/scripts/` - Development & Testing Scripts
```
scripts/
├── README.md                           # Scripts documentation
├── check_*.py                          # API/cache verification scripts
│   ├── check_api_status_filter.py      # Validate PandaScore API responses
│   ├── check_api_structure.py          # Inspect API data structure
│   ├── check_cache_content.py          # Dump current cache state
│   ├── check_reminders_detailed.py     # Inspect reminder scheduling
│   └── check_status.py                 # Overall system health
├── analyze_*.py                        # Data analysis scripts
│   ├── analyze_match_status.py         # Match status distribution
│   ├── debug_api_structure.py          # Deep API inspection
│   └── debug_match_*.py                # Match-specific debugging
├── init_db.py                          # Quick database initialization
├── monitor_reminders_realtime.py       # Real-time reminder flow tracing
├── preview_embed.py                    # Preview Discord embed rendering
├── test_*.py                           # Feature tests
│   └── test_reminder_now.py            # Test reminder scheduling immediately
└── fix_*.py                            # Data repair scripts
    ├── fix_stuck_matches.py            # Unstuck matches in wrong status
    ├── clean_old_reminders.py          # Remove expired reminders
    └── run_scheduling_status.py        # Check scheduler status
```

**Rules**:
- ✅ Create debug/analysis scripts: `/scripts/analyze_*.py` or `/scripts/debug_*.py`
- ✅ Create test utilities: `/scripts/test_*.py`
- ✅ Create data repair scripts: `/scripts/fix_*.py` or `/scripts/clean_*.py`
- ✅ Create monitoring tools: `/scripts/monitor_*.py`
- ✅ Create verification tools: `/scripts/check_*.py`
- ❌ NEVER put production code in scripts/
- ⚠️ Keep scripts independent (can run standalone without bot running)

### `/docs/` - Documentation & Design Docs
```
docs/
├── README.md                           # Documentation index
├── COMECE_AQUI.md                      # Quick start guide (português)
├── ARQUITETURA_*.md                    # Architecture & design decisions
│   ├── ARQUITETURA_FINAL.md            # Complete data flow diagram
│   ├── ARQUITETURA_CACHE.md            # Cache hierarchy explanation
│   └── FLUXO_CACHE_EXPLICADO.md        # Cache flow walkthrough
├── GUIA_*.md                           # Usage guides
│   ├── GUIA_RAPIDO.md                  # Quick reference
│   ├── GUIA_STATUS_PARTIDA.md          # Match status states
│   ├── GUIA_TESTE_FINAL.md             # Testing guide
│   └── GUIA_THUMBNAIL_MELHORADO.md     # UI/UX improvements
├── MELHORIAS_*.md                      # Feature documentation
│   ├── MELHORIAS_CACHE_EMBEDS_v2.md    # Cache & embed improvements
│   ├── MELHORIAS_EMBEDS_FINAIS.md      # Final embed design
│   ├── MELHORIAS_RESULTADOS.md         # Result display improvements
│   └── MELHORIAS_THUMBNAIL_v3.md       # Thumbnail enhancements
├── INVESTIGACAO_*.md                   # Problem investigations
│   ├── INVESTIGACAO_BEGIN_AT.md        # begin_at field analysis
│   ├── CONCLUSAO_*.md                  # Investigation conclusions
│   └── VALIDACAO_*.md                  # Validation reports
├── LOGS_*.md                           # Logging documentation
│   ├── LOGS_DETALHADOS.md              # Detailed logging spec
│   ├── LOGS_README.md                  # Logging guide
│   └── MUDANCAS_LOGS.md                # Logging change log
├── SUMARIO_*.md                        # Executive summaries
│   ├── SUMARIO_FINAL.md                # Final summary
│   ├── RESUMO_EXECUTIVO.md             # Executive overview
│   └── RESUMO_MELHORIAS_*.txt          # Feature summaries
└── ESPECIFICACAO_*.md                  # Technical specifications
    ├── ESPECIFICACAO_TECNICA.md        # Full technical spec
    ├── INDICE_CORRECOES.md             # Bug fix index
    └── INDICE_ARQUIVOS.md              # File index
```

**Rules**:
- ✅ Create design docs: `/docs/ARQUITETURA_*.md`
- ✅ Create investigation reports: `/docs/INVESTIGACAO_*.md`
- ✅ Create feature docs: `/docs/MELHORIAS_*.md`
- ✅ Create guides: `/docs/GUIA_*.md`
- ✅ Use PREFIX_description.md naming (easy to group by prefix)
- ❌ NEVER put code in docs/
- ❌ NEVER commit large binary files
- 📝 Always update docs/ when architecture changes

### `/plan/` - Project Planning
```
plan/
├── INDEX.md                            # Planning index
├── TODO.md                             # Main task list (master source of truth)
├── ROADMAP.md                          # Feature roadmap & timeline
├── DUVIDAS.md                          # Open questions & uncertainties
├── MELHORIAS_FUTURAS.md                # Backlog of future improvements
├── CONCLUSAO.md                        # Project conclusions
└── SUMARIO_MELHORIAS.md                # Improvement summary
```

**Rules**:
- ✅ Track progress: Update `/plan/TODO.md` when starting/completing tasks
- ✅ Document decisions: Add to `/plan/DUVIDAS.md` or `/plan/ROADMAP.md`
- ❌ NEVER put code or detailed design here (use docs/ instead)

### `/logs/` - Runtime Logs (Gitignored)
```
logs/
└── bot.log                             # Auto-created by logging config
                                        # Contains all runtime logs with timestamps
```

**Rules**:
- ✅ Auto-created on first run (in `bot.py`)
- ✅ UTF-8 encoded for Windows compatibility
- ❌ NEVER commit (gitignored)
- 📊 Tail for real-time debugging: `tail -f logs/bot.log`

### `/data/` - Database & Local Data (Gitignored)
```
data/
└── bot.db                              # libSQL database file (SQLite format)
```

**Rules**:
- ✅ Auto-created on first run by `build_db.py`
- ❌ NEVER commit (gitignored)
- 🔄 Reset with: `python -m src.database.build_db`

### Root-Level Config Files (Commit)
```
.github/
├── copilot-instructions.md             # THIS FILE - AI agent guidance
├── ...                                 # Other GitHub-specific config

.env.example                            # Template for .env (commit this)
requirements.txt                        # Python dependencies (commit)
setup.py                                # Package setup (commit)
SETUP.md                                # Setup instructions (commit)
ENTREGA_FINAL.md                        # Delivery documentation (commit)
```

**Rules**:
- ✅ Commit: `requirements.txt`, `setup.py`, `.env.example`, all `.md` files
- ❌ NEVER commit: `.env`, `.db`, `venv/`, `__pycache__/`, `logs/`, `data/`

## Testing & Validation

- **Unit tests**: Scripts in `scripts/` (e.g., `check_api_status_filter.py`, `validate_cache_full.py`)
- **Integration**: Use TESTING_GUILD_ID for safe testing without affecting production
- **Logging inspection**: Tail `logs/bot.log` for real-time debugging
- **Cache inspection**: `scripts/check_cache_content.py` dumps DB state

## Key Files Reference

| File | Purpose | Key Functions |
|------|---------|----------------|
| `src/bot.py` | Bot lifecycle & component initialization | `HLTVBot.__init__()`, `on_ready()` |
| `src/services/pandascore_service.py` | API client | `get_upcoming_matches()`, `get_running_matches()`, `get_past_matches()` |
| `src/services/cache_scheduler.py` | Background task scheduler | `update_all_matches()`, `update_live_matches()` |
| `src/services/twitch_search_service.py` | Twitch stream search (fallback) | `_get_access_token()`, `search_streams()` |
| `src/services/youtube_service.py` | YouTube channel/video info (fallback) | `_extract_channel_id_from_url()`, `get_channel_info()` |
| `src/database/cache_manager.py` | Cache operations | `cache_matches()`, `get_cached_matches()`, `cache_streams()`, `get_match_streams()` |
| `src/database/temporal_cache.py` | 42h temporal window management | `get_temporal_window()`, `get_match_temporal_anchor()` |
| `src/services/notification_manager.py` | Reminder scheduling | `setup_reminders_for_match()`, `start_reminder_loop()` |
| `src/cogs/matches.py` | Match query commands | `/partidas`, `/aovivo`, `/resultados` |
| `src/database/schema.sql` | Database schema | 7 tables + indexes |
| `src/utils/embeds.py` | Discord embeds & stream formatting | `create_match_embed()`, `augment_match_with_streams()`, `format_streams_field()` |

---

## 🔌 Liquipedia API Integration Rules

> **Status**: Optional integration for additional CS2 data (teams, players, tournaments)
> **Documentation**: See `liquipedia-doc/` for full API specs and terms

### ⚠️ CRITICAL - Rate Limits (Violation = Ban)

**LiquipediaDB API (REST v3):**
- **Maximum: 60 requests per hour** (strict limit)
- Requires API key: `Authorization: Apikey YOUR_KEY`

**MediaWiki API:**
- **General requests: 1 every 2 seconds** (max 30/min)
- **`action=parse` requests: 1 every 30 seconds** (resource-intensive)

### 🛡️ Required HTTP Headers

```python
headers = {
    # MANDATORY: Custom User-Agent with contact info
    "User-Agent": "bot-hltv/1.0 (Discord Bot; github.com/msouza10/bot-hltv; email@example.com)",
    
    # MANDATORY: Accept gzip encoding
    "Accept-Encoding": "gzip",
    
    # For LiquipediaDB API:
    "Authorization": "Apikey YOUR_API_KEY"
}
```

> ❌ **Generic User-Agents (`Python-requests`, `Go-http-client`) WILL BE BLOCKED!**

### 💾 Cache Requirements (Mandatory)

**From Terms**: *"Re-use / cache your API results for as long as possible"*

- Implement dual cache: Memory + Database (like PandaScore integration)
- Recommended TTL:
  - **Upcoming matches**: 5 minutes
  - **Finished matches**: 1 hour
  - **Teams/players**: 24 hours
  - **Tournaments**: 24 hours

### ⚖️ Attribution (CC-BY-SA 3.0)

**MANDATORY**: Credit Liquipedia in Discord embeds when using their data

```python
# Add to embed footer
embed.set_footer(text="Dados: Liquipedia (liquipedia.net/counterstrike)")
```

**License**: Content is CC-BY-SA 3.0 (derivative works must use same license)

### 📡 REST API v3 Quick Reference

**Base URL**: `https://api.liquipedia.net/api/v3`

**Key Endpoints**:
- `/match` - Match data (match2 table)
- `/player` - Player information
- `/team` - Team information
- `/tournament` - Tournament data
- `/transfer` - Player transfers
- `/series` - Match series

**Parameters**:
```python
params = {
    "wiki": "counterstrike",  # REQUIRED
    "limit": 50,              # Default: 20, Max: 1000
    "conditions": "[[date::>2024-11-24]] AND [[team::FURIA]]",  # SQL-like filters
    "query": "pagename,date,team",  # Fields to return (omit for all)
    "order": "date DESC",     # Ordering
    "groupby": "team ASC"     # Grouping
}
```

**Filter Syntax**:
```python
# Operators
"[[field::value]]"      # equals
"[[field::!value]]"     # not equals
"[[field::>value]]"     # greater than
"[[field::<value]]"     # less than

# Combine with logic
"[[date::>2024-11-01]] AND ([[tier::1]] OR [[type::!online]])"

# Date functions
"[[date_year::2024]] AND [[date_month::11]]"
```

### 📊 HTTP Response Codes

| Code | Meaning | Action |
|------|---------|--------|
| **200** | ✅ Success | Continue |
| **403** | 🔒 Invalid API key | Check credentials |
| **404** | ❌ Data not found | Adjust query |
| **429** | ⏸️ Over API limit | **STOP** - Wait 1 hour |

### 🚫 Absolute Prohibitions

1. ❌ **Automated HTML scraping** (APIs only)
2. ❌ **Sharing API keys** (personal use only)
3. ❌ **Exceeding rate limits** (60 req/h for REST)
4. ❌ **Generic User-Agents** (will be blocked)
5. ❌ **Omitting attribution** (license violation)

**Violations result in temporary or permanent IP bans.**

### ✅ Implementation Checklist

When integrating Liquipedia API:

- [ ] Custom User-Agent header configured
- [ ] Accept-Encoding: gzip header configured
- [ ] Rate limiter implemented (60 req/h max)
- [ ] Dual cache system (memory + DB)
- [ ] Attribution in embeds/responses
- [ ] API key in `.env` (never hardcode)
- [ ] Retry logic with exponential backoff for 429 errors
- [ ] Error handling for 403, 404, 429 responses
- [ ] No HTML scraping (API endpoints only)

### 📝 Example Implementation

```python
import aiohttp
from datetime import datetime, timedelta

class LiquipediaService:
    BASE_URL = "https://api.liquipedia.net/api/v3"
    RATE_LIMIT = 60  # requests per hour
    
    def __init__(self, api_key: str):
        self.headers = {
            "User-Agent": "bot-hltv/1.0 (Discord; github.com/msouza10/bot-hltv)",
            "Accept-Encoding": "gzip",
            "Authorization": f"Apikey {api_key}"
        }
        self._request_times = []  # Track requests for rate limiting
    
    async def _check_rate_limit(self):
        """Enforce 60 requests per hour."""
        now = datetime.now()
        # Remove requests older than 1 hour
        self._request_times = [t for t in self._request_times 
                               if now - t < timedelta(hours=1)]
        
        if len(self._request_times) >= self.RATE_LIMIT:
            # Wait until oldest request expires
            wait_time = (self._request_times[0] + timedelta(hours=1) - now).total_seconds()
            raise RateLimitError(f"Rate limit reached. Wait {wait_time:.0f}s")
        
        self._request_times.append(now)
    
    async def get_matches(self, conditions: str = None, limit: int = 50):
        """Fetch matches from Liquipedia."""
        await self._check_rate_limit()
        
        params = {
            "wiki": "counterstrike",
            "limit": limit,
        }
        if conditions:
            params["conditions"] = conditions
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.BASE_URL}/match",
                headers=self.headers,
                params=params
            ) as resp:
                if resp.status == 429:
                    raise RateLimitError("API rate limit exceeded")
                elif resp.status == 403:
                    raise AuthError("Invalid API key")
                
                data = await resp.json()
                return data.get("result", [])
```

### 🔗 Documentation References

- **Full API docs**: `liquipedia-doc/documentation-api-v3.md`
- **OpenAPI spec**: `liquipedia-doc/api-calls.md`
- **Terms of use**: `liquipedia-doc/liquipedia-use-terms.md`
- **License**: `liquipedia-doc/liquipedia-license.md`

