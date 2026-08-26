import os
import re
from apscheduler.schedulers.background import BackgroundScheduler
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, jsonify, request
import requests

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
        sigla_alvo = filtro_estado.upper().strip() if filtro_estado else ""

        for item in soup.select(".ca"):
            link_elem = item.select_one("a")
            if not link_elem:
                continue

            # Extrai a sigla do estado diretamente da div class="cc"
            cc_elem = item.select_one(".cc")
            estado_sigla = cc_elem.text.strip().upper() if cc_elem else ""

            # Filtra pela sigla da div class "cc"
            if (
                sigla_alvo
                and sigla_alvo != "ALL"
                and estado_sigla != sigla_alvo
            ):
                continue

            titulo = link_elem.text.strip()
            link = link_elem["href"]
            if link.startswith("/"):
                link = f"https://www.pciconcursos.com.br{link}"

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

            # Identifica a data limite no formato XX/XX/XXXX
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

            # Extrai o Nível de Escolaridade
            nivel = "N/A"
            niveis_possiveis = [
                "Superior",
                "Técnico",
                "Médio",
                "Fundamental",
                "Alfabetizado",
            ]

            for n in niveis_possiveis:
                if n.lower() in vagas_detalhes.lower():
                    nivel = n
                    vagas_detalhes = re.sub(
                        rf"\b{n}\b", "", vagas_detalhes, flags=re.IGNORECASE
                    ).strip()
                    break

            # Card formatado em Markdown
            card = (
                f"🏛️ *{titulo}* [{estado_sigla}]\n"
                f"🎓 *Nível:* {nivel}\n"
                f"💰 *Vagas / Cargo:* {vagas_detalhes}\n"
                f"⏳ *Inscrições até:* {data_limite}\n"
                f"🔗 [Acessar Edital/Notícia]({link})"
            )

            concursos.append(card)

        return concursos

    except Exception as e:
        print(f"Erro no scraping: {e}")
        return []


# --- FUNÇÕES AUXILIARES DO TELEGRAM ---
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
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/answerCallbackQuery"
    payload = {"callback_query_id": callback_query_id, "text": text}
    requests.post(url, json=payload, timeout=10)


def get_state_keyboard():
    """Teclado de seleção de estado inicial."""
    return {
        "inline_keyboard": [
            [
                {"text": "🌵 Paraíba (PB)", "callback_data": "page_PB_0"},
                {"text": "🌊 Pernambuco (PE)", "callback_data": "page_PE_0"},
            ],
            [
                {"text": "☀️ Ceará (CE)", "callback_data": "page_CE_0"},
                {"text": "🌴 Rio Grande do Norte (RN)", "callback_data": "page_RN_0"},
            ],
            [
                {"text": "🌐 Ver Todos (Nordeste)", "callback_data": "page_ALL_0"}
            ],
        ]
    }


def get_pagination_keyboard(sigla, next_offset, total_items):
    """Teclado interativo de navegação e troca de estado."""
    buttons = []
    
    # Se houver mais resultados, adiciona o botão de carregar mais
    if next_offset < total_items:
        buttons.append([
            {
                "text": f"➕ Carregar Mais ({next_offset}/{total_items})",
                "callback_data": f"page_{sigla}_{next_offset}",
            }
        ])
    
    buttons.append([{"text": "🔙 Voltar ao Menu", "callback_data": "menu_inicial"}])
    
    return {"inline_keyboard": buttons}


# --- AGENDADOR DIÁRIO ---
def scheduled_job():
    print("⏰ Executando disparo agendado...")
    if not CHAT_ID:
        return

    all_jobs = fetch_pci_jobs(filtro_estado=ESTADO_FILTRO_PADRAO)
    tag_foco = f"Foco: {ESTADO_FILTRO_PADRAO}" if all_jobs else "Nordeste (Geral)"
    if not all_jobs:
        all_jobs = fetch_pci_jobs()

    if not all_jobs:
        return

    # Pega os primeiros 5 concursos no disparo agendado
    jobs = all_jobs[:5]
    message = f"🚀 *Atualização PCI Concursos ({tag_foco})* 🚀\n\n" + "\n\n".join(jobs)
    
    reply_markup = get_pagination_keyboard(
        ESTADO_FILTRO_PADRAO if all_jobs else "ALL", 5, len(all_jobs)
    )
    send_telegram_message(CHAT_ID, message, reply_markup=reply_markup)


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

    # 1. Trata Comandos
    if "message" in data:
        message = data["message"]
        chat_id = message["chat"]["id"]
        text = message.get("text", "").strip()

        if text in ["/start", "/concursos"]:
            msg_texto = (
                "👋 *Bem-vindo ao Bot PCI Concursos!*\n\n"
                "Escolha abaixo o estado que deseja consultar:"
            )
            send_telegram_message(
                chat_id, msg_texto, reply_markup=get_state_keyboard()
            )

    # 2. Trata Botões Inline e Paginação
    elif "callback_query" in data:
        callback = data["callback_query"]
        callback_id = callback["id"]
        chat_id = callback["message"]["chat"]["id"]
        data_code = callback.get("data", "")

        answer_callback_query(callback_id, "Carregando...")

        if data_code == "menu_inicial":
            send_telegram_message(
                chat_id,
                "Escolha o estado desejado:",
                reply_markup=get_state_keyboard(),
            )

        elif data_code.startswith("page_"):
            # O callback vem no formato: page_SIGLA_OFFSET (ex: page_PB_0, page_PB_5)
            _, sigla, offset_str = data_code.split("_")
            offset = int(offset_str)
            limit = 5  # Exibe 5 concursos por bloco

            filtro = "" if sigla == "ALL" else sigla
            label_estado = "Nordeste (Geral)" if sigla == "ALL" else f"Estado: {sigla}"

            all_jobs = fetch_pci_jobs(filtro_estado=filtro)
            total_items = len(all_jobs)

            if not all_jobs:
                send_telegram_message(
                    chat_id,
                    f"Nenhum concurso encontrado para *{label_estado}*.",
                    reply_markup=get_state_keyboard(),
                )
            else:
                # Fatiamento da lista para aplicar a paginação
                page_jobs = all_jobs[offset : offset + limit]
                next_offset = offset + len(page_jobs)

                if page_jobs:
                    msg = (
                        f"🚀 *Concursos ({label_estado})* [{offset + 1}-{next_offset} de {total_items}]\n\n"
                        + "\n\n".join(page_jobs)
                    )
                    reply_markup = get_pagination_keyboard(sigla, next_offset, total_items)
                    send_telegram_message(chat_id, msg, reply_markup=reply_markup)

    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)