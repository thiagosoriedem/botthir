import os
import threading
import time
import requests
from bs4 import BeautifulSoup
from flask import Flask
import schedule
from telegram import Bot

# --- CONFIGURAÇÕES ---
TELEGRAM_TOKEN = os.getenv("6620673021:AAEFh0H-0iKNAZCnfEE9IwCnqRYoVeZ3vNY")
CHAT_ID = os.getenv("6325710382")  # Seu ID de usuário ou canal
REGION_URL = "https://www.pciconcursos.com.br/concursos/nordeste/"  # Altere para a região/URL desejada

app = Flask(__name__)
bot = Bot(token=TELEGRAM_TOKEN)


# --- 1. ROTA WEB PARA MANTER O RENDER ACORDADO ---
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
    response = requests.get(REGION_URL, headers=headers)

    if response.status_code != 200:
        return []

    soup = BeautifulSoup(response.content, "html.parser")
    concursos = []

    # Captura os blocos de concursos no site
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

    return concursos[:10]  # Retorna os 10 primeiros da lista


# --- 3. ENVIO PARA O TELEGRAM ---
def send_daily_updates():
    try:
        jobs = fetch_pci_jobs()
        if not jobs:
            bot.send_message(
                chat_id=CHAT_ID,
                text="Nenhum concurso encontrado no momento.",
            )
            return

        message = (
            "🚀 **Atualização Diária - PCI Concursos** 🚀\n\n" + "\n\n".join(jobs)
        )
        # O Telegram limita o envio a 4096 caracteres
        if len(message) > 4000:
            for chunk in [message[i : i + 4000] for i in range(0, len(message), 4000)]:
                bot.send_message(
                    chat_id=CHAT_ID, text=chunk, parse_mode="Markdown"
                )
        else:
            bot.send_message(
                chat_id=CHAT_ID, text=message, parse_mode="Markdown"
            )
    except Exception as e:
        print(f"Erro ao enviar mensagem: {e}")


# --- 4. AGENDAMENTO ---
def run_scheduler():
    # Define o horário diário para envio (Exemplo: 08:00)
    schedule.every().day.at("08:00").do(send_daily_updates)

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    # Inicia o agendador em uma thread separada
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()

    # Inicia o servidor Flask na thread principal
    run_flask()