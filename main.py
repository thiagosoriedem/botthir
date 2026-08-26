import os
from apscheduler.schedulers.background import BackgroundScheduler
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, jsonify, request
import requests
import re
app = Flask(__name__)
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
REGION_URL = "https://www.pciconcursos.com.br/concursos/nordeste/"
ESTADO_FILTRO_PADRAO = os.getenv("ESTADO_FILTRO", "PB").upper()


# --- SCRAPING DO PCI CONCURSOS ---
def fetch_pci_jobs(filtro_estado=""):
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

            # Extração dos blocos de dados
            cd_text = (
                item.select_one(".cd").text.strip()
                if item.select_one(".cd")
                else ""
            )
            ce_text = (
                item.select_one(".ce").text.strip()
                if item.select_one(".ce")
                else ""
            )

            # Identifica qual das tags contém a data (Formato XX/XX/XXXX)
            data_limite = "N/A"
            vagas_detalhes = ""

            if re.search(r"\d{2}/\d{2}/\d{4}", cd_text):
                data_limite = cd_text
                vagas_detalhes = ce_text
            elif re.search(r"\d{2}/\d{2}/\d{4}", ce_text):
                data_limite = ce_text
                vagas_detalhes = cd_text
            else:
                vagas_detalhes = f"{cd_text} {ce_text}".strip()

            # Extrai e limpa o nível de escolaridade do texto de vagas
            nivel = "N/A"
            niveis_possiveis = [
                "Superior",
                "Técnico",
                "Médio",
                "Fundamental",
                "Alfabetizado",
            ]

            for n in niveis_possiveis:
                if n in vagas_detalhes:
                    nivel = n
                    # Remove repetições do nível no texto de vagas
                    vagas_detalhes = re.sub(
                        rf"\b{n}\b", "", vagas_detalhes, flags=re.IGNORECASE
                    ).strip()
                    break

            # Aplica filtro de estado se necessário
            if filtro_estado and (
                f"/{filtro_estado.lower()}" not in link.lower()
                and f"-{filtro_estado.lower()}" not in titulo.lower()
                and f" {filtro_estado.upper()}" not in titulo.upper()
            ):
                continue

            # Montagem da mensagem formatada em Markdown
            card = (
                f"🏛️ *{titulo}*\n"
                f"🎓 *Nível:* {nivel}\n"
                f"💰 *Vagas / Cargo:* {vagas_detalhes}\n"
                f"⏳ *Inscrições até:* {data_limite}\n"
                f"🔗 [Acessar Edital/Notícia]({link})"
            )

            concursos.append(card)

        return concursos[:10]
    except Exception as e:
        print(f"Erro no scraping: {e}")
        return []

# --- FUNÇÕES TELEGRAM ---
def send_telegram_message(target_chat_id, text, reply_markup=None):
    if not TELEGRAM_TOKEN:
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": target_chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup

    response = requests.post(url, json=payload, timeout=10)
    return response.status_code == 200


def answer_callback_query(callback_query_id, text=""):
    """Notifica o Telegram que o clique no botão foi recebido."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/answerCallbackQuery"
    payload = {"callback_query_id": callback_query_id, "text": text}
    requests.post(url, json=payload, timeout=10)


def get_state_keyboard():
    """Retorna o teclado com botões inline para seleção de estado."""
    return {
        "inline_keyboard": [
            [
                {"text": "🌵 Paraíba (PB)", "callback_data": "filtro_PB"},
                {"text": "🌊 Pernambuco (PE)", "callback_data": "filtro_PE"},
            ],
            [
                {"text": "☀️ Ceará (CE)", "callback_data": "filtro_CE"},
                {"text": "🌴 Rio Grande do Norte (RN)", "callback_data": "filtro_RN"},
            ],
            [
                {"text": "🌐 Ver Todos (Nordeste)", "callback_data": "filtro_ALL"}
            ],
        ]
    }


# --- DISPARO AGENDADO DIÁRIO ---
def scheduled_job():
    print("⏰ Executando disparo agendado das 18:50...")
    if not CHAT_ID:
        return

    jobs = fetch_pci_jobs(filtro_estado=ESTADO_FILTRO_PADRAO)
    tag_foco = f"Foco: {ESTADO_FILTRO_PADRAO}" if jobs else "Nordeste (Geral)"
    if not jobs:
        jobs = fetch_pci_jobs()

    if not jobs:
        return

    message = f"🚀 *Atualização PCI Concursos ({tag_foco})* 🚀\n\n" + "\n\n".join(jobs)

    if len(message) > 4000:
        for chunk in [message[i : i + 4000] for i in range(0, len(message), 4000)]:
            send_telegram_message(CHAT_ID, chunk)
    else:
        send_telegram_message(CHAT_ID, message)


scheduler = BackgroundScheduler(timezone="America/Fortaleza")
scheduler.add_job(scheduled_job, "cron", hour=18, minute=50)
scheduler.start()


# --- ROTAS WEB ---
@app.route("/")
def home():
    return "Servidor PCI Concursos Ativo!", 200


@app.route("/concursos")
def trigger_concursos():
    scheduled_job()
    return "✅ Concursos enviados para o Telegram com sucesso!", 200


@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def telegram_webhook():
    data = request.get_json()
    if not data:
        return jsonify({"status": "ignored"}), 200

    # 1. Trata mensagens normais e comandos (/start, /concursos)
    if "message" in data:
        message = data["message"]
        chat_id = message["chat"]["id"]
        text = message.get("text", "").strip()

        if text == "/start" or text == "/concursos":
            msg_texto = (
                "👋 *Bem-vindo ao Bot PCI Concursos!*\n\n"
                "Escolha abaixo o estado que deseja consultar:"
            )
            send_telegram_message(
                chat_id, msg_texto, reply_markup=get_state_keyboard()
            )

    # 2. Trata cliques nos botões (Callback Queries)
    elif "callback_query" in data:
        callback = data["callback_query"]
        callback_id = callback["id"]
        chat_id = callback["message"]["chat"]["id"]
        data_code = callback.get("data", "")

        # Responde o clique imediatamente para remover a animação de carregamento do botão
        answer_callback_query(callback_id, "Buscando concursos...")

        if data_code.startswith("filtro_"):
            sigla = data_code.replace("filtro_", "")
            filtro = "" if sigla == "ALL" else sigla
            label_estado = "Nordeste (Geral)" if sigla == "ALL" else f"Estado: {sigla}"

            send_telegram_message(chat_id, f"🔎 *Buscando vagas para {label_estado}...*")
            jobs = fetch_pci_jobs(filtro_estado=filtro)

            if not jobs:
                send_telegram_message(
                    chat_id,
                    f"Nenhum concurso aberto encontrado para *{label_estado}* no momento.",
                    reply_markup=get_state_keyboard(),
                )
            else:
                msg = f"🚀 *Últimos Concursos ({label_estado})* 🚀\n\n" + "\n\n".join(jobs)
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