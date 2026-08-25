import os
from apscheduler.schedulers.background import BackgroundScheduler
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, jsonify, request
import requests

app = Flask(__name__)
load_dotenv()

# Configurações do ambiente no Render
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
REGION_URL = "https://www.pciconcursos.com.br/concursos/nordeste/"


# --- SCRAPING DO PCI CONCURSOS ---
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
                f"📌 *{titulo}*\n🎯 Vagas/Salário: {vagas}\n🎓 Nível: {nivel}\n🔗 {link}"
            )

        return concursos[:10]
    except Exception as e:
        print(f"Erro no scraping: {e}")
        return []


# --- ENVIO DE MENSAGENS TELEGRAM ---
def send_telegram_message(target_chat_id, text):
    if not TELEGRAM_TOKEN:
        print("TELEGRAM_TOKEN não definido.")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": target_chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }

    response = requests.post(url, json=payload, timeout=10)
    return response.status_code == 200


# --- DISPARO AGENDADO DIÁRIO ---
def scheduled_job():
    print("⏰ Executando disparo agendado das 18:50...")
    if not CHAT_ID:
        print("CHAT_ID não definido para envio automático.")
        return

    jobs = fetch_pci_jobs()
    if not jobs:
        print("Nenhum concurso encontrado no horário agendado.")
        return

    message = "🚀 *Atualização PCI Concursos (Diária)* 🚀\n\n" + "\n\n".join(jobs)

    if len(message) > 4000:
        for chunk in [
            message[i : i + 4000] for i in range(0, len(message), 4000)
        ]:
            send_telegram_message(CHAT_ID, chunk)
    else:
        send_telegram_message(CHAT_ID, message)


# --- CONFIGURAÇÃO DO AGENDADOR (18h50 - Horário de Brasília/Fortaleza) ---
scheduler = BackgroundScheduler(timezone="America/Fortaleza")
scheduler.add_job(scheduled_job, "cron", hour=19, minute=00)
scheduler.start()


# --- ROTAS WEB E WEBHOOK ---


@app.route("/")
def home():
    return "Servidor PCI Concursos Ativo!", 200


@app.route("/concursos")
def trigger_concursos():
    scheduled_job()
    return "✅ Concursos enviados para o Telegram com sucesso!", 200


# Rota Webhook para ler mensagens e comandos do Telegram em tempo real
@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def telegram_webhook():
    data = request.get_json()

    if not data or "message" not in data:
        return jsonify({"status": "ignored"}), 200

    message = data["message"]
    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()

    if text == "/start":
        send_telegram_message(
            chat_id,
            "👋 Olá! Envie o comando */concursos* para receber a lista dos últimos concursos.",
        )
    elif text == "/concursos":
        send_telegram_message(chat_id, "🔎 Buscando concursos no PCI...")
        jobs = fetch_pci_jobs()

        if not jobs:
            send_telegram_message(
                chat_id, "Nenhum concurso encontrado no momento."
            )
        else:
            msg = "🚀 *Últimos Concursos - PCI* 🚀\n\n" + "\n\n".join(jobs)
            if len(msg) > 4000:
                for chunk in [
                    msg[i : i + 4000] for i in range(0, len(msg), 4000)
                ]:
                    send_telegram_message(chat_id, chunk)
            else:
                send_telegram_message(chat_id, msg)

    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)