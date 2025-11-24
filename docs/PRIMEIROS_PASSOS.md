# 🚀 Primeiros Passos - BOT Jeff CS2

Guia prático para começar o desenvolvimento do bot usando Python e Pycord.

---

## 📋 Pré-requisitos

Antes de começar, certifique-se de ter instalado:

- ✅ **Python 3.10+** - [Download](https://www.python.org/downloads/)
- ✅ **pip** (gerenciador de pacotes Python)
- ✅ **Git** - [Download](https://git-scm.com/)
- ✅ **Editor de código** (VS Code recomendado)

### Verificar Instalação

```bash
python --version  # Deve mostrar 3.10 ou superior
pip --version
git --version
```

---

## 🔑 Passo 1: Obter API Keys

### 1.1. PandaScore API Key

1. Acesse [PandaScore](https://pandascore.co/)
2. Clique em "Sign Up" (canto superior direito)
3. Preencha o cadastro:
   - Email
   - Nome da empresa (pode colocar nome pessoal)
   - Selecione "Developer" como tipo
4. Confirme seu email
5. Faça login e vá para [Dashboard](https://pandascore.co/users/me)
6. Clique em "API Keys" no menu lateral
7. Copie sua **API Token** (guarde em local seguro!)
8. Verifique que está no plano **Fixtures** (gratuito)

**Limite do plano gratuito:**
- 1000 requisições por hora
- Acesso a todas as partidas de CS2
- Sem webhooks (usaremos polling)

### 1.2. Discord Bot Token

1. Acesse o [Discord Developer Portal](https://discord.com/developers/applications)
2. Clique em "New Application"
3. Dê um nome ao seu bot (ex: "BOT Jeff CS2")
4. Clique em "Create"

#### Configurar Bot:

5. Vá para aba **"Bot"** no menu lateral
6. Clique em "Add Bot" → "Yes, do it!"
7. Copie o **TOKEN** (botão "Reset Token" se necessário)
   - ⚠️ **NUNCA compartilhe este token!**
8. Em "Privileged Gateway Intents", ative:
   - ✅ **Presence Intent** (opcional)
   - ✅ **Server Members Intent** (opcional)
   - ✅ **Message Content Intent** (se for ler mensagens)

#### Gerar Link de Convite:

9. Vá para aba **"OAuth2"** → **"URL Generator"**
10. Em **"Scopes"**, selecione:
    - ✅ `bot`
    - ✅ `applications.commands`
11. Em **"Bot Permissions"**, selecione:
    - ✅ Send Messages
    - ✅ Embed Links
    - ✅ Read Message History
    - ✅ Use Slash Commands
12. Copie a **URL gerada** no final da página
13. Cole no navegador e adicione o bot ao seu servidor de testes

---

## 📂 Passo 2: Configurar Projeto

### 2.1. Criar Estrutura de Pastas

```bash
# Navegar até pasta do projeto
cd /home/msouza/Documents/bot-hltv

# Criar estrutura
mkdir -p src/{cogs,services,database,models,utils}
mkdir -p data logs config

# Criar arquivos iniciais
touch src/__init__.py
touch src/bot.py
touch src/cogs/{__init__.py,config.py,teams.py,matches.py,help.py}
touch src/services/{__init__.py,pandascore_service.py,notification_service.py,scheduler_service.py}
touch src/database/{__init__.py,db.py,schema.sql}
touch src/models/{__init__.py,match.py,team.py,guild.py}
touch src/utils/{__init__.py,embeds.py,logger.py,helpers.py}
touch config/{__init__.py,settings.py}
```

### 2.2. Criar Ambiente Virtual

```bash
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
# No Linux/Mac:
source venv/bin/activate

# No Windows:
# venv\Scripts\activate

# Verificar ativação (deve mostrar (venv) no prompt)
which python  # Deve apontar para venv/bin/python
```

### 2.3. Criar requirements.txt

```bash
# Criar arquivo requirements.txt
cat > requirements.txt << 'EOF'
# Discord
py-cord>=2.4.0

# HTTP Client
aiohttp>=3.9.0

# Database
aiosqlite>=0.19.0

# Scheduler
APScheduler>=3.10.0

# Environment Variables
python-dotenv>=1.0.0

# Utilities
python-dateutil>=2.8.2
EOF
```

### 2.4. Instalar Dependências

```bash
# Instalar todas as dependências
pip install -r requirements.txt

# Verificar instalação
pip list
```

### 2.5. Criar arquivo .env

```bash
# Criar .env
cat > .env << 'EOF'
# Discord Bot Token
DISCORD_TOKEN=seu_token_discord_aqui

# PandaScore API Key
PANDASCORE_API_KEY=sua_api_key_pandascore_aqui

# Database Path
DATABASE_PATH=data/bot.db

# Polling Intervals (em minutos)
POLLING_STANDARD=15
POLLING_LIVE=5

# Logging Level
LOG_LEVEL=INFO
EOF
```

**⚠️ IMPORTANTE:** 
- Substitua `seu_token_discord_aqui` pelo token real do Discord
- Substitua `sua_api_key_pandascore_aqui` pela API key da PandaScore
- Verifique que `.env` está no `.gitignore`

### 2.6. Atualizar .gitignore

```bash
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
.venv

# Environment
.env
.env.local

# Database
*.db
*.sqlite
*.sqlite3
data/*.db

# Logs
logs/
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Backups
*_OLD.md
*.bak
EOF
```

---

## 🏗️ Passo 3: Implementar Código Base

### 3.1. Criar Schema do Banco (data/schema.sql)

```sql
-- Tabela de configurações de servidores
CREATE TABLE IF NOT EXISTS guilds (
    guild_id TEXT PRIMARY KEY,
    notification_channel_id TEXT NOT NULL,
    language TEXT DEFAULT 'pt-BR',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de times favoritos por servidor
CREATE TABLE IF NOT EXISTS favorite_teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    team_slug TEXT NOT NULL,
    team_name TEXT NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (guild_id) REFERENCES guilds(guild_id) ON DELETE CASCADE,
    UNIQUE(guild_id, team_slug)
);

-- Tabela de notificações enviadas
CREATE TABLE IF NOT EXISTS notifications_sent (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id INTEGER NOT NULL,
    guild_id TEXT NOT NULL,
    notification_type TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (guild_id) REFERENCES guilds(guild_id) ON DELETE CASCADE,
    UNIQUE(match_id, guild_id, notification_type)
);

-- Tabela de cache de partidas
CREATE TABLE IF NOT EXISTS matches_cache (
    match_id INTEGER PRIMARY KEY,
    data TEXT NOT NULL,
    status TEXT NOT NULL,
    scheduled_at TIMESTAMP NOT NULL,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_notifications_match ON notifications_sent(match_id);
CREATE INDEX IF NOT EXISTS idx_notifications_guild ON notifications_sent(guild_id);
CREATE INDEX IF NOT EXISTS idx_favorite_teams_guild ON favorite_teams(guild_id);
CREATE INDEX IF NOT EXISTS idx_matches_status ON matches_cache(status);
CREATE INDEX IF NOT EXISTS idx_matches_scheduled ON matches_cache(scheduled_at);
```

Salve este conteúdo em `data/schema.sql`.

### 3.2. Implementar Cliente da API (src/services/pandascore_service.py)

```python
import aiohttp
import os
from typing import List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class PandaScoreClient:
    def __init__(self):
        self.base_url = "https://api.pandascore.co"
        self.api_token = os.getenv("PANDASCORE_API_KEY")
        self.session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Accept": "application/json"
            }
            self.session = aiohttp.ClientSession(headers=headers)
        return self.session
    
    async def _request(self, endpoint: str, params: dict = None) -> dict:
        session = await self._get_session()
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"Erro na requisição à API: {e}")
            return []
    
    async def get_upcoming_matches(self, game: str = "csgo", limit: int = 50) -> List[dict]:
        params = {
            "filter[status]": "not_started",
            "sort": "scheduled_at",
            "per_page": limit
        }
        return await self._request(f"/{game}/matches/upcoming", params)
    
    async def get_running_matches(self, game: str = "csgo") -> List[dict]:
        params = {"filter[status]": "running"}
        return await self._request(f"/{game}/matches/running", params)
    
    async def get_past_matches(self, game: str = "csgo", hours: int = 24, limit: int = 20) -> List[dict]:
        now = datetime.utcnow()
        since = now - timedelta(hours=hours)
        
        params = {
            "filter[status]": "finished",
            "filter[end_at]": f">{since.isoformat()}Z",
            "sort": "-end_at",
            "per_page": limit
        }
        return await self._request(f"/{game}/matches/past", params)
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
```

### 3.3. Implementar Bot Principal (src/bot.py)

```python
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv

from src.database.db import Database
from src.services.pandascore_service import PandaScoreClient

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Configurar intents
intents = discord.Intents.default()
intents.guilds = True
intents.guild_messages = True

# Criar bot
bot = commands.Bot(
    intents=intents,
    description="Bot de notificações de partidas de CS2"
)

# Inicializar serviços
bot.database = Database()
bot.api_client = PandaScoreClient()

@bot.event
async def on_ready():
    logger.info(f"Bot conectado como {bot.user} (ID: {bot.user.id})")
    logger.info(f"Conectado a {len(bot.guilds)} servidores")
    
    # Conectar ao banco de dados
    await bot.database.connect()
    logger.info("Banco de dados conectado")
    
    # Registrar comandos slash
    await bot.sync_commands()
    logger.info("Comandos slash registrados")

@bot.event
async def on_guild_join(guild):
    logger.info(f"Bot adicionado ao servidor: {guild.name} (ID: {guild.id})")

# Carregar cogs
bot.load_extension("src.cogs.config")
bot.load_extension("src.cogs.teams")
bot.load_extension("src.cogs.matches")
bot.load_extension("src.cogs.help")

if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.error("DISCORD_TOKEN não encontrado no .env")
        exit(1)
    
    bot.run(token)
```

### 3.4. Implementar Database (src/database/db.py)

```python
import aiosqlite
import os
from typing import List, Optional

class Database:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.getenv("DATABASE_PATH", "data/bot.db")
        
    async def connect(self):
        """Inicializa conexão e cria tabelas"""
        # Criar diretório data se não existir
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Executar schema
        async with aiosqlite.connect(self.db_path) as db:
            with open('data/schema.sql', 'r') as f:
                await db.executescript(f.read())
            await db.commit()
    
    async def add_guild(self, guild_id: str, channel_id: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO guilds (guild_id, notification_channel_id) VALUES (?, ?)",
                (guild_id, channel_id)
            )
            await db.commit()
    
    async def get_guild(self, guild_id: str) -> Optional[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM guilds WHERE guild_id = ?", (guild_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    
    async def get_all_guilds(self) -> List[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM guilds") as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def add_favorite_team(self, guild_id: str, team_slug: str, team_name: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR IGNORE INTO favorite_teams (guild_id, team_slug, team_name) VALUES (?, ?, ?)",
                (guild_id, team_slug, team_name)
            )
            await db.commit()
    
    async def remove_favorite_team(self, guild_id: str, team_slug: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "DELETE FROM favorite_teams WHERE guild_id = ? AND team_slug = ?",
                (guild_id, team_slug)
            )
            await db.commit()
    
    async def get_favorite_teams(self, guild_id: str) -> List[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM favorite_teams WHERE guild_id = ?", (guild_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
```

### 3.5. Implementar Cog de Configuração (src/cogs/config.py)

```python
import discord
from discord.ext import commands
from discord.commands import slash_command, Option

class ConfigCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.database
    
    @slash_command(
        name="setup",
        description="Configurar canal de notificações"
    )
    @commands.has_permissions(administrator=True)
    async def setup(
        self,
        ctx: discord.ApplicationContext,
        canal: Option(discord.TextChannel, "Canal para enviar notificações", required=True)
    ):
        await self.db.add_guild(str(ctx.guild_id), str(canal.id))
        
        embed = discord.Embed(
            title="✅ Configuração Concluída",
            description=f"As notificações serão enviadas em {canal.mention}",
            color=0x2ecc71
        )
        embed.add_field(
            name="📌 Próximos Passos",
            value="Use `/seguir [time]` para adicionar times favoritos",
            inline=False
        )
        
        await ctx.respond(embed=embed, ephemeral=True)

def setup(bot):
    bot.add_cog(ConfigCog(bot))
```

---

## 🧪 Passo 4: Testar o Bot

### 4.1. Testar Conexão Básica

```bash
# Ativar ambiente virtual (se não estiver)
source venv/bin/activate

# Executar bot
python -m src.bot
```

**Saída esperada:**
```
INFO - Bot conectado como BotHLTV#1234 (ID: 123456789)
INFO - Conectado a 1 servidores
INFO - Banco de dados conectado
INFO - Comandos slash registrados
```

### 4.2. Testar Comandos no Discord

1. Vá para seu servidor de testes
2. Digite `/setup` e selecione um canal
3. Verifique se o bot responde com confirmação
4. Digite `/ajuda` para ver todos os comandos

### 4.3. Testar API PandaScore

```bash
# Criar script de teste
cat > test_api.py << 'EOF'
import asyncio
from dotenv import load_dotenv
from src.services.pandascore_service import PandaScoreClient

load_dotenv()

async def test():
    client = PandaScoreClient()
    
    print("Testando API PandaScore...")
    matches = await client.get_upcoming_matches(limit=5)
    
    print(f"\nEncontradas {len(matches)} partidas:")
    for match in matches:
        team1 = match['opponents'][0]['opponent']['name']
        team2 = match['opponents'][1]['opponent']['name']
        print(f"- {team1} vs {team2}")
    
    await client.close()

asyncio.run(test())
EOF

# Executar teste
python test_api.py
```

---

## 📦 Passo 5: Próximas Implementações

### 5.1. Checklist MVP

- [x] Setup inicial do projeto
- [x] Configuração de ambiente
- [x] Integração com PandaScore API
- [x] Banco de dados SQLite
- [x] Comando `/setup`
- [ ] Comandos de times (`/seguir`, `/desseguir`, `/meustimes`)
- [ ] Comandos de partidas (`/partidas`, `/aovivo`, `/resultados`)
- [ ] Sistema de notificações automáticas
- [ ] Scheduler com APScheduler
- [ ] Templates de embeds
- [ ] Deploy em produção

### 5.2. Próximos Arquivos a Criar

1. **src/cogs/teams.py** - Comandos de times favoritos
2. **src/cogs/matches.py** - Comandos de partidas
3. **src/cogs/help.py** - Sistema de ajuda
4. **src/services/notification_service.py** - Lógica de notificações
5. **src/services/scheduler_service.py** - Agendamento com APScheduler
6. **src/utils/embeds.py** - Templates de embeds Discord

---

## 🐛 Troubleshooting

### Erro: "DISCORD_TOKEN não encontrado"
```bash
# Verificar .env
cat .env

# Verificar se python-dotenv está instalado
pip list | grep python-dotenv

# Re-instalar se necessário
pip install python-dotenv
```

### Erro: "Module not found"
```bash
# Verificar estrutura de pastas
tree src/  # ou: find src/ -type f

# Criar __init__.py faltantes
touch src/__init__.py
touch src/cogs/__init__.py
touch src/services/__init__.py
```

### Bot não responde a comandos
1. Verificar se bot tem permissão "Use Application Commands"
2. Verificar se comandos foram registrados (`await bot.sync_commands()`)
3. Aguardar até 1 hora para comandos globais propagarem

### Erro de banco de dados
```bash
# Verificar se diretório data/ existe
mkdir -p data

# Verificar se schema.sql existe e está correto
cat data/schema.sql

# Recriar banco (cuidado: apaga dados!)
rm data/bot.db
python -m src.bot
```

---

## 📚 Recursos Adicionais

### Documentação Oficial
- [Pycord Docs](https://docs.pycord.dev/)
- [PandaScore API](https://developers.pandascore.co/docs)
- [Discord Developer Portal](https://discord.com/developers/docs)
- [Python asyncio](https://docs.python.org/3/library/asyncio.html)

### Tutoriais Recomendados
- [Pycord Guide](https://guide.pycord.dev/)
- [Python Async/Await](https://realpython.com/async-io-python/)
- [SQLite with Python](https://docs.python.org/3/library/sqlite3.html)

### Comunidades
- [Pycord Discord](https://discord.gg/pycord)
- [PandaScore Discord](https://discord.gg/pandascore)

---

## ✅ Conclusão

Você agora tem a estrutura base do bot funcionando! 🎉

**Próximos passos:**
1. Implementar os cogs restantes (teams, matches, help)
2. Implementar sistema de notificações automáticas
3. Adicionar scheduler com APScheduler
4. Testar em ambiente de desenvolvimento
5. Deploy em produção (Railway/Render)

Para implementação detalhada de cada componente, consulte:
- [ESPECIFICACAO_TECNICA.md](ESPECIFICACAO_TECNICA.md) - Código completo
- [TODO.md](../plan/TODO.md) - Roadmap detalhado

---

**Boa sorte no desenvolvimento! 🚀**
