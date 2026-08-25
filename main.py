import os
from bs4 import BeautifulSoup
from flask import Flask
import requests
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

# Configurações do ambiente no Render
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
REGION_URL = "https://www.pciconcursos.com.br/concursos/nordeste/"


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


def send_telegram_message(text):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("TELEGRAM_TOKEN ou CHAT_ID não definidos.")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}

    response = requests.post(url, json=payload)
    return response.status_code == 200


# --- ROTAS WEB ---


@app.route("/")
def home():
    # Rota usada pelo UptimeRobot para manter o Render acordado
    return "Servidor PCI Concursos Ativo!", 200


@app.route("/concursos")
def trigger_concursos():
    # Rota que você acessa para disparar as notícias
    jobs = fetch_pci_jobs()

    if not jobs:
        return "Nenhum concurso encontrado.", 404

    message = (
        "🚀 *Atualização PCI Concursos* 🚀\n\n" + "\n\n".join(jobs)
    )

    # Trata limite de caracteres do Telegram (4000)
    if len(message) > 4000:
        for chunk in [
            message[i : i + 4000] for i in range(0, len(message), 4000)
        ]:
            send_telegram_message(chunk)
    else:
        send_telegram_message(message)

    return "✅ Concursos enviados para o Telegram com sucesso!", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)