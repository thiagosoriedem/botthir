import asyncio
import os
import threading
from bs4 import BeautifulSoup
from flask import Flask
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- CONFIGURAÇÕES ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
REGION_URL = "https://www.pciconcursos.com.br/concursos/nordeste/"

app = Flask(__name__)


# --- 1. ROTA WEB PARA O RENDER ---
@app.route("/")
def health_check():
    return "Bot PCI Concursos está ativo!", 200


def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


# --- 2. SCRAPING DO PCI CONCURSOS ---
def fetch_pci_jobs():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        response = requests.get(REGION_URL, headers=headers, timeout=10)
        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.content, "html.parser")
        concursos = []

        for item in soup.select(".ca"):
            link_elem = item.select_one("a")
            if not link_elem:
                continue

            titulo = link_elem.text.strip()
            link = link_elem["href"]
            vagas = (
                item.select_one(".cd").text.strip()
                if item.select_one(".cd")
                else "N/A"
            )
            nivel = (
                item.select_one(".ce").text.strip()
                if item.select_one(".ce")
                else "N/A"
            )

            concursos.append(
                f"📌 **{titulo}**\n🎯 Vagas/Salário: {vagas}\n🎓 Nível: {nivel}\n🔗 [Link]({link})"
            )

        return concursos[:10]
    except Exception as e:
        print(f"Erro no scraping: {e}")
        return []


# --- 3. COMANDOS DO TELEGRAM ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Olá! Use o comando /concursos para listar as últimas oportunidades do PCI Concursos."
    )


async def concursos_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    await update.message.reply_text("🔎 Buscando concursos atualizados...")
    jobs = fetch_pci_jobs()

    if not jobs:
        await update.message.reply_text("Nenhum concurso encontrado no momento.")
        return

    message = (
        "🚀 **Últimos Concursos - PCI Concursos** 🚀\n\n" + "\n\n".join(jobs)
    )

    if len(message) > 4000:
        for chunk in [
            message[i : i + 4000] for i in range(0, len(message), 4000)
        ]:
            await update.message.reply_text(chunk, parse_mode="Markdown")
    else:
        await update.message.reply_text(message, parse_mode="Markdown")


# --- 4. TAREFA RECORRENTE DIÁRIA ---
async def send_daily_job(context: ContextTypes.DEFAULT_TYPE):
    if not CHAT_ID:
        return

    jobs = fetch_pci_jobs()
    if jobs:
        message = (
            "🚀 **Atualização Diária - PCI Concursos** 🚀\n\n"
            + "\n\n".join(jobs)
        )
        await context.bot.send_message(
            chat_id=CHAT_ID, text=message, parse_mode="Markdown"
        )


# --- 5. INICIALIZAÇÃO DO BOT E SCHEDULER ---
def main():
    if not TELEGRAM_TOKEN:
        raise ValueError(
            "TELEGRAM_TOKEN não foi encontrado nas variáveis de ambiente."
        )

    # Inicia o servidor Flask em background
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Configura a aplicação do Telegram
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Adiciona os manipuladores de comando
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("concursos", concursos_command))

    # Configura o envio automático diário usando o JobQueue interno da biblioteca
    if application.job_queue and CHAT_ID:
        import datetime

        # Agenda para rodar diariamente às 08:00 (UTC)
        application.job_queue.run_daily(
            send_daily_job, time=datetime.time(hour=8, minute=0, second=0)
        )

    # Inicia a escuta de comandos via Polling
    application.run_polling()


if __name__ == "__main__":
    main()