---
trigger: always_on
---



# Instruções para Agente AI (Gemini/Antigravity) - bot-hltv

**Contexto**: Você está trabalhando no `bot-hltv`, um bot de Discord para notificações de partidas de CS2 usando a API PandaScore.
**Linguagem Principal**: Python 3.10+
**Idioma de Comunicação**: Português Brasileiro (PT-BR)

## 🚨 Regras de Ouro (Invioláveis)

1.  **Respeite a Estrutura de Diretórios**:
    *   `src/`: **Apenas** código de produção.
    *   `scripts/`: **Apenas** scripts de teste, verificação e ferramentas de dev. NUNCA coloque código de produção aqui.
    *   `docs/`: **Apenas** documentação.
    *   `data/`: Banco de dados SQLite (não commitar).

2.  **Verificação Obrigatória**:
    *   **Sempre** que modificar código, rode um script de verificação relevante em `scripts/`.
    *   Se não existir um script para o que você mudou, **crie um** em `scripts/test_NOME_FEATURE.py`.
    *   Use `python scripts/check_status.py` para health check geral.

3.  **Banco de Dados (libSQL/SQLite)**:
    *   Use `src/database/schema.sql` como fonte da verdade.
    *   Para aplicar mudanças de schema: Edite `schema.sql` -> Rode `python -m src.database.build_db`.
    *   Sempre use `asyncio.Lock()` para operações de escrita concorrentes se necessário (embora o `cache_manager` já gerencie muito disso).

4.  **Async/Await**:
    *   Todo I/O (DB, API, Discord) deve ser assíncrono.
    *   Cuidado com `asyncio.TimeoutError` em interações do Discord (>3s).

## 🗺️ Mapa do Projeto

*   **Entry Point**: `src/bot.py`
*   **Comandos**: `src/cogs/` (ex: `matches.py` para `/partidas`)
*   **Cache**: `src/database/cache_manager.py` (Camada dupla: Memória + DB)
*   **API Client**: `src/services/pandascore_service.py`
*   **Scheduler**: `src/services/cache_scheduler.py` (Atualiza dados a cada 5/15 min)
*   **Notificações**: `src/services/notification_manager.py`

## 🛠️ Workflow de Desenvolvimento

1.  **Planejar**: Leia `docs/` relevantes. Se for uma feature nova, crie um plano.
2.  **Implementar**: Edite arquivos em `src/`.
3.  **Verificar**:
    *   Rode `python scripts/check_api_structure.py` se mexeu na API.
    *   Rode `python scripts/preview_embed.py` se mexeu em Embeds.
    *   Rode `python scripts/check_reminders_detailed.py` se mexeu em Notificações.
4.  **Documentar**: Atualize `docs/` se a arquitetura mudou.

## ⚠️ Pitfalls Comuns

*   **Timeouts do Discord**: O Discord exige resposta em <3s. Se o comando for demorado, use `await interaction.response.defer()`.
*   **Rate Limits**: A API PandaScore tem limite de 1000 req/h. O `pandascore_service.py` já trata isso, não faça chamadas diretas sem passar por ele ou sem cache.
*   **Timezones**: O servidor roda em UTC, mas usuários podem estar em outros fusos. O código tenta normalizar, mas fique atento a conversões de data.
*   **Null Safety**: A API PandaScore retorna `null` frequentemente (ex: `end_at` em jogos não finalizados). Sempre verifique antes de acessar.

## 📝 Comandos Úteis

```bash
# Rodar o bot
python -m src.bot

# Rebuildar DB (CUIDADO: Apaga dados locais)
python -m src.database.build_db

# Verificar integridade do cache
python scripts/check_cache_content.py
```

---

## 🔌 Regras da API Liquipedia (Se Integrada)

### ⚠️ CRÍTICO - Rate Limits Obrigatórios

**LiquipediaDB API (REST v3):**
- **Máximo: 60 requisições por hora**
- Requer chave de API: `Authorization: Apikey SUA_CHAVE`

**MediaWiki API:**
- **Requisições gerais: 1 a cada 2 segundos** (máx 30/min)
- **Requisições `action=parse`: 1 a cada 30 segundos**

### 🛡️ Headers HTTP Obrigatórios

```python
headers = {
    # OBRIGATÓRIO: User-Agent personalizado com contato
    "User-Agent": "bot-hltv/1.0 (Discord Bot; github.com/msouza10/bot-hltv; email@example.com)",
    
    # OBRIGATÓRIO: Aceitar gzip
    "Accept-Encoding": "gzip",
    
    # Se usar LiquipediaDB API:
    "Authorization": "Apikey SUA_CHAVE_API"
}
```

> ❌ **User-Agents genéricos (`Python-requests`, `Go-http-client`) SERÃO BLOQUEADOS!**

### 💾 Cache Obrigatório

- **"Re-use / cache your API results for as long as possible"**
- Implementar cache em memória + banco de dados
- TTL recomendado:
  - Partidas futuras: 5 minutos
  - Partidas finalizadas: 1 hora
  - Dados de times/jogadores: 24 horas

### ⚖️ Atribuição (CC-BY-SA 3.0)

**OBRIGATÓRIO dar crédito**:
```markdown
"Dados fornecidos por Liquipedia (https://liquipedia.net/counterstrike)"
```

### 📊 Códigos de Resposta HTTP

| Código | Ação |
|--------|------|
| **200** | ✅ Continue |
| **403** | 🔒 Chave API inválida - Verifique credenciais |
| **404** | ❌ Dados não existem - Ajuste query |
| **429** | ⏸️ **PARE IMEDIATAMENTE** - Aguarde 1 hora |

### ✅ Checklist de Implementação

- [ ] User-Agent personalizado configurado
- [ ] Accept-Encoding: gzip configurado
- [ ] Rate limiter implementado (60 req/h para REST)
- [ ] Sistema de cache robusto funcionando
- [ ] Atribuição à Liquipedia visível
- [ ] Chave de API em variável de ambiente (não no código)
- [ ] Retry logic para erros 429 com backoff exponencial
- [ ] Não acessar HTML diretamente (apenas APIs)
- [ ] Não compartilhar chave de API

### 📍 Endpoint Principal para CS2

```python
# Base URL
url = "https://api.liquipedia.net/api/v3/match"

# Parâmetros
params = {
    "wiki": "counterstrike",  # OBRIGATÓRIO
    "limit": 50,              # Máx: 1000
    "conditions": "[[date::>2024-11-24]]",  # Filtros SQL-like
    "order": "date ASC"
}
```

### 🚫 Proibições Absolutas

1. ❌ Acesso automatizado a páginas HTML (apenas APIs)
2. ❌ Compartilhar chaves de API com terceiros
3. ❌ Exceder rate limits
4. ❌ Usar User-Agents genéricos
5. ❌ Omitir atribuição à Liquipedia

**Violações podem resultar em ban temporário ou permanente.**

---

**Documentação completa**: Ver `liquipedia-doc/` para detalhes da API v3, termos de uso e licença.