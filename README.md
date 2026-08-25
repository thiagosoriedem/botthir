
# 🚀 Bot Telegram - PCI Concursos

Bot do Telegram construído em Python e Flask para raspagem automática de dados de novos concursos públicos cadastrados no site **PCI Concursos (Região Nordeste)**. 

O bot disponibiliza consulta sob demanda via comandos no aplicativo, disparo automático em horário agendado e hospedagem gratuita no **Render** com integração ao **UptimeRobot** para execução contínua (24/7).

---

## 📌 Funcionalidades

- **Raspagem de Dados (`BeautifulSoup4`)**: Coleta os últimos 10 concursos listados no PCI Concursos, extraindo título, número de vagas/salário, nível de escolaridade e link oficial.
- **Interação por Webhook**: Resposta instantânea aos comandos `/start` e `/concursos` direto pelo chat do Telegram.
- **Agendamento Diário (`APScheduler`)**: Disparo automático das oportunidades cadastradas todos os dias às **19:50** (Fuso horário: `America/Fortaleza`).
- **Endpoint Web de Disparo Manual**: Rota HTTP (`/concursos`) para acionar o envio sob demanda via navegador.
- **Servidor Web Flask**: Compatível com o servidor WSGI **Gunicorn** no Render.

---

## 🛠️ Tecnologias Utilizadas

- **Linguagem**: Python 3.12+
- **Framework Web**: Flask
- **Raspagem Web**: BeautifulSoup4 + Requests
- **Agendador de Tarefas**: APScheduler
- **Servidor de Produção**: Gunicorn
- **Hospedagem Cloud**: Render (Web Service Free Tier)
- **Keep-Alive**: UptimeRobot

---

## 📁 Estrutura do Projeto

```text
├── main.py              # Script principal com Flask, Scraping, Webhook e Agendador
├── requirements.txt     # Dependências do projeto
├── .env                 # Variáveis de ambiente locais (não versionado)
└── README.md            # Documentação do projeto
```
---

## ⚙️ Configuração Local e Instalação
### 1. Pré-requisitos
- Python 3.10 ou superior instalado.
- Um bot criado no Telegram via @BotFather para obter o TELEGRAM_TOKEN.
- O seu ID do Telegram obtido via @userinfobot para obter o CHAT_ID.

### 2. Criar e ativar ambiente virtual
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate

## Instalar pacotes
pip install -r requirements.txt
3. Configurar Variáveis de Ambiente Locais
Crie um arquivo .env na raiz do projeto:Snippet de códigoTELEGRAM_TOKEN="SEU_TOKEN_DO_BOTFATHER"
CHAT_ID="SEU_CHAT_ID_NUMERICO"
4. Executar o Servidor LocalmenteBashpython main.py
O servidor estará rodando em http://localhost:10000.

## ☁️ Hospedagem e Configuração no Render

Para rodar a aplicação gratuitamente no Render sem que ela entre em modo de hibernação:
1. Criar o Web Service no Render
- Acesse o Dashboard do Render e crie um New Web Service.
- Conecte o seu repositório do GitHub.
- Defina as configurações de build:Environment: Python 3
- Build Command: pip install -r requirements.txt
- Start Command: gunicorn main:app

2. Cadastrar Variáveis de Ambiente (Environment Variables) na aba Environment do serviço no Render, adicione as chaves:
- TELEGRAM_TOKEN Token do bot fornecido pelo BotFather
- CHAT_ID Seu ID numérico no Telegram

## 🔗 Ativação do Webhook do Telegram
Para que o bot escute os comandos /concursos e /start enviados no aplicativo, é necessário registrar a URL do seu servidor Flask na API do Telegram. Substitua SEU_TOKEN e a URL do seu app no link abaixo e abra no navegador:

[https://api.telegram.org/botSEU_TOKEN/setWebhook?url=https://SUA_URL_API.onrender.com/SEU_TOKEN](https://api.telegram.org/botSEU_TOKEN/setWebhook?url=https://SUA_URL_API.onrender.com/SEU_TOKEN)

Resposta de confirmação esperada:
```text
JSON{
  "ok": true,
  "result": true,
  "description": "Webhook was set"
}
```

## ⏰ Manter o Bot Ativo 24/7 (UptimeRobot):
Como o plano gratuito do Render hiberna aplicações web após 15 minutos de inatividade, utilize o UptimeRobot para manter o servidor acordado:

1. Crie uma conta no [UptimeRobot](https://uptimerobot.com/).
2. Adicione um novo monitor com as seguintes opções:
- Monitor Type: HTTP(s)Friendly 
- Name: Bot PCI Concursos URL: https://SUA_URL_API.onrender.com/ 
- Interval: A cada 5 minutos

Dessa forma, o ping do UptimeRobot manterá o container Flask ativo, permitindo que o agendador do APScheduler execute o envio diário das 19:00 pontualmente.

## 📱 Comandos Disponíveis no Telegram
/start - Envia uma mensagem de boas-vindas com as instruções do bot.

/concursos - Realiza a raspagem no PCI Concursos em tempo real e exibe as 10 principais oportunidades encontradas.

Mais comandos em breve...