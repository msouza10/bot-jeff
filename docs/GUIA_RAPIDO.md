# 🎮 BOT Jeff - Guia Rápido

Bot Discord para notificações de partidas de CS2 usando **Nextcord** e **PandaScore API**.

## ✅ Status: Bot funcionando!

O bot está conectado e operacional com os seguintes comandos:

### 📋 Comandos Disponíveis

| Comando | Descrição | Parâmetros |
|---------|-----------|------------|
| `/partidas` | Lista próximas partidas de CS2 | `quantidade` (1-10, padrão: 5) |
| `/aovivo` | Mostra partidas acontecendo agora | - |
| `/resultados` | Resultados recentes | `horas` (1-72, padrão: 24), `quantidade` (1-10, padrão: 5) |

---

## 🚀 Como rodar o bot

### 1. Primeira execução

```bash
# Ativar ambiente virtual
source venv/bin/activate

# Rodar o bot
python -m src.bot
```

### 2. Próximas execuções

```bash
# Atalho direto (sem ativar venv)
venv/bin/python -m src.bot
```

### 3. Rodar em background

```bash
# Com nohup
nohup venv/bin/python -m src.bot > logs/bot.log 2>&1 &

# Ou com screen
screen -S hltv-bot
venv/bin/python -m src.bot
# Ctrl+A+D para detach
```

---

## 🔧 Configuração

### Arquivo `.env` (já configurado)

```bash
DISCORD_TOKEN=seu_token_aqui
PANDASCORE_API_KEY=sua_api_key_aqui
DATABASE_PATH=./data/bot.db
```

### Servidor Discord

O bot está conectado ao servidor: **noobs server** (ID: 1188166184760254594)

---

## 📊 Testando o bot

### No Discord:

1. Vá para o servidor onde o bot está
2. Digite `/partidas` para ver as próximas 5 partidas
3. Digite `/partidas quantidade:10` para ver 10 partidas
4. Digite `/aovivo` para ver partidas ao vivo
5. Digite `/resultados` para ver resultados das últimas 24h

### Exemplo de uso:

```
/partidas quantidade:3
/aovivo
/resultados horas:48 quantidade:5
```

---

## 📁 Estrutura do Projeto

```
bot-hltv/
├── src/
│   ├── bot.py                    # ✅ Bot principal (Nextcord)
│   ├── cogs/
│   │   └── matches.py            # ✅ Comandos de partidas
│   ├── services/
│   │   └── pandascore_service.py # ✅ Cliente PandaScore API
│   └── utils/
│       └── embeds.py             # ✅ Formatação de mensagens
├── data/                         # Banco de dados (futuro)
├── logs/
│   └── bot.log                   # ✅ Logs do bot
├── venv/                         # ✅ Ambiente virtual Python
├── requirements.txt              # ✅ Dependências
├── .env                          # ✅ Configurações (não versionar!)
└── README.md
```

---

## 🐛 Troubleshooting

### Bot não conecta:
- Verifique se o token no `.env` está correto
- Confirme que o bot tem permissões no servidor

### Comandos não aparecem:
- Aguarde alguns minutos (Discord cache)
- Recarregue o Discord (Ctrl+R)

### API não retorna dados:
- Verifique sua API key da PandaScore
- Confirme que tem créditos/requests disponíveis

---

## 🔄 Próximos Passos

- [ ] Implementar sistema de notificações automáticas
- [ ] Adicionar banco de dados SQLite
- [ ] Criar comando `/setup` para configurar canal
- [ ] Adicionar filtros por times favoritos
- [ ] Sistema de agendamento com APScheduler

---

## 📝 Logs

Logs em tempo real:
```bash
tail -f logs/bot.log
```

---

## 🎯 Sucesso Atual

✅ Bot conectado e funcionando  
✅ Integração com PandaScore API  
✅ 3 comandos slash implementados  
✅ Formatação de embeds com logos e informações  
✅ Tratamento de erros básico  
✅ Compatibilidade Python 3.13 (Nextcord)

---

**Desenvolvido com ❤️ usando Python, Nextcord e PandaScore API**

_Última atualização: 15 de novembro de 2025_
