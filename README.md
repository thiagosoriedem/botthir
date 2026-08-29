# 🤖 Thir Agent

Bot do Telegram construído em Python e Flask com múltiplos módulos: **Concursos Públicos**, **Lembretes & Tarefas**, **Gestão Financeira**, **Flashcards** e **Mini-Games**.

## 📌 Funcionalidades

### 🏛️ Concursos Públicos
- Raspagem automática de concursos do **PCI Concursos** (Região Nordeste)
- Filtro por estado (configurável via `ESTADO_FILTRO`)
- Disparo diário agendado às **18:50** (Fuso: `America/Fortaleza`)
- Paginação interativa no Telegram

### 📝 Lembretes & Tarefas
- Criar tarefas com `/novatarefa`
- Marcar como concluída/pendente
- Excluir tarefas
- Interface interativa com botões inline

### 💸 Gestão Financeira
- **Transações**: Registrar receitas e despesas com categorias
- **Despesas Fixas**: Recorrentes com dia de vencimento e previsão mensal
- **Investimentos**: Ações, FIIs, Tesouro, CDB, Cripto com cálculo de crescimento
- **Dividendos**: Programação de recebimentos com projeção anual
- **Metas**: Metas financeiras com barra de progresso
- **Integração B3**: Cotações em tempo real via API oficial da B3 + Brapi.dev
- **WebApp completo**: Dashboard com gráficos, transações, investimentos e dividendos

### 🧠 Flashcards
- Sistema de repetição espaçada (algoritmo SM-2)
- Criar, editar e excluir cards
- Avaliação de dificuldade (Errei, Bom, Fácil)
- WebApp interativo

### 🎮 Mini-Games
- Jogo da Memória (Associação Rápida)
- Acesso via `/jogos` ou botão no menu

## 🛠️ Tecnologias Utilizadas

- **Linguagem**: Python 3.12+
- **Framework Web**: Flask
- **Banco de Dados**: Firebase Firestore (NoSQL)
- **IA**: Google Gemini (google-genai)
- **Raspagem Web**: BeautifulSoup4 + Requests
- **Cotações B3**: API oficial B3 + Brapi.dev + yfinance
- **Agendador**: APScheduler
- **Servidor de Produção**: Gunicorn
- **Hospedagem Cloud**: Render (Web Service Free Tier)
- **Keep-Alive**: UptimeRobot

## 📁 Estrutura do Projeto

```text
├── main.py                    # Script principal (Flask, Webhook, Rotas)
├── requirements.txt           # Dependências do projeto
├── .env                       # Variáveis de ambiente locais (não versionado)
├── README.md                  # Documentação do projeto
├── modules/
│   ├── concursos.py           # Raspagem PCI Concursos
│   ├── database.py            # Conexão Firebase Firestore
│   ├── financas.py            # Lógica de finanças (transações, investimentos, B3)
│   ├── ia.py                  # Integração Google Gemini
│   └── lembretes.py           # Lembretes & Tarefas
└── templates/
    ├── financas.html          # WebApp de Gestão Financeira
    ├── flashcards.html        # WebApp de Flashcards
    └── game.html              # Jogo da Memória
```

## ⚙️ Configuração Local e Instalação

### 1. Pré-requisitos
- Python 3.10 ou superior
- Bot criado no Telegram via @BotFather (`TELEGRAM_TOKEN`)
- Seu ID do Telegram via @userinfobot (`CHAT_ID`)
- Projeto Firebase com credenciais de service account (`FIREBASE_CREDENTIALS`)
- Chave da API Google Gemini (`GEMINI_API_KEY`)

### 2. Criar e ativar ambiente virtual

```bash
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

### 3. Instalar pacotes

```bash
pip install -r requirements.txt
```

### 4. Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
TELEGRAM_TOKEN="SEU_TOKEN_DO_BOTFATHER"
CHAT_ID="SEU_CHAT_ID_NUMERICO"
FIREBASE_CREDENTIALS='{"type": "service_account", ...}'
GEMINI_API_KEY="SUA_CHAVE_GEMINI"
ESTADO_FILTRO="PB"
```

### 5. Executar o Servidor Localmente

```bash
python main.py
```

O servidor estará rodando em `http://localhost:10000`.

## ☁️ Hospedagem e Configuração no Render

1. **Criar Web Service** no Render conectado ao repositório GitHub
2. **Configurações**:
   - Environment: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn main:app`
3. **Variáveis de Ambiente** (aba Environment):
   - `TELEGRAM_TOKEN`
   - `CHAT_ID`
   - `FIREBASE_CREDENTIALS` (JSON do service account)
   - `GEMINI_API_KEY`
   - `ESTADO_FILTRO` (opcional, padrão: PB)

## 🔗 Ativação do Webhook do Telegram

Substitua `SEU_TOKEN` e a URL do seu app no link abaixo e abra no navegador:

```
https://api.telegram.org/botSEU_TOKEN/setWebhook?url=https://SUA_URL_API.onrender.com/SEU_TOKEN
```

Resposta esperada:
```json
{
  "ok": true,
  "result": true,
  "description": "Webhook was set"
}
```

## ⏰ Manter o Bot Ativo 24/7 (UptimeRobot)

1. Crie uma conta no [UptimeRobot](https://uptimerobot.com/)
2. Adicione um monitor:
   - Monitor Type: HTTP(s)
   - Name: Thir Agent
   - URL: `https://SUA_URL_API.onrender.com/`
   - Interval: A cada 5 minutos

## 📱 Comandos Disponíveis no Telegram

| Comando | Descrição |
|---------|-----------|
| `/start` | Exibe o menu principal do Agente |
| `/menu` | Abre o painel interativo |
| `/novocard` | Cria flashcard. Ex: `/novocard Pergunta \| Resposta` |
| `/editarcard` | Edita flashcard. Ex: `/editarcard ID \| Pergunta \| Resposta` |
| `/deletarcard` | Remove flashcard. Ex: `/deletarcard ID` |
| `/novatarefa` | Cria tarefa. Ex: `/novatarefa Comprar material` |
| `/gasto` | Registra despesa. Ex: `/gasto 50,00 Mercado` |
| `/receita` | Registra receita. Ex: `/receita 2500,00 Salário` |
| `/resumo` | Mostra resumo financeiro do mês |
| `/jogos` | Abre a central de mini-games |

## 🌐 WebApps Disponíveis

| App | URL | Descrição |
|-----|-----|-----------|
| Finanças | `/financas` | Dashboard, transações, investimentos, dividendos, metas |
| Flashcards | `/flashcards` | Repetição espaçada com algoritmo SM-2 |
| Jogo da Memória | `/game.html` | Jogo de associação rápida |

## 🔄 Atualização de Comandos

Para forçar a atualização dos comandos do bot sem reiniciar o servidor:

```
https://SUA_URL_API.onrender.com/setup_commands
```

Os comandos também são re-registrados automaticamente a cada `/start` ou `/menu`.

## 🔥 Estrutura Firebase

```text
users/{user_id}/
├── decks/{deck_name}/cards/       # Flashcards
├── tasks/                         # Tarefas
├── financas/                      # Transações
├── despesas_fixas/                # Despesas recorrentes
├── investimentos/                 # Investimentos
├── dividendos/                    # Dividendos programados
└── metas_financeiras/             # Metas
```

## 📡 APIs de Cotações B3

O sistema usa **3 fontes em cascata** para buscar cotações:

1. **API Oficial B3**: `https://cotacao.b3.com.br/mds/api/v1/DailyFluctuationHistory/{TICKER}`
2. **Brapi.dev**: `https://brapi.dev/api/quote/{TICKER}` (fallback)
3. **Yahoo Finance**: via yfinance (último recurso)