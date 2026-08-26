import os
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from flask import Flask, jsonify, request
import requests
from modules.ia import responder_duvida

# Importação dos Módulos
from modules.concursos import (
    fetch_pci_jobs,
    get_concursos_pagination_keyboard,
    get_concursos_state_keyboard,
)

app = Flask(__name__)
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
ESTADO_FILTRO_PADRAO = os.getenv("ESTADO_FILTRO", "PB").upper()


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


# --- MENUS DO AGENTE PESSOAL ---
def get_main_menu_keyboard():
    """Menu Principal do seu Agente Pessoal."""
    return {
        "inline_keyboard": [
            [
                {"text": "🏛️ Concursos Públicos", "callback_data": "menu_concursos"},
                {"text": "📝 Lembretes & Tarefas", "callback_data": "menu_lembretes"},
            ],
            [
                {"text": "💸 Gestão Financeira", "callback_data": "menu_financas"},
                {"text": "🤖 Perguntar à IA", "callback_data": "menu_ia"},
            ],
        ]
    }


# --- AGENDADOR DIÁRIO ---
def scheduled_job():
    print("⏰ Executando disparo agendado de concursos...")
    if not CHAT_ID:
        return

    all_jobs = fetch_pci_jobs(filtro_estado=ESTADO_FILTRO_PADRAO)
    tag_foco = f"Foco: {ESTADO_FILTRO_PADRAO}" if all_jobs else "Nordeste (Geral)"
    if not all_jobs:
        all_jobs = fetch_pci_jobs()

    if not all_jobs:
        return

    jobs = all_jobs[:5]
    message = f"🚀 *Atualização PCI Concursos ({tag_foco})* 🚀\n\n" + "\n\n".join(jobs)
    reply_markup = get_concursos_pagination_keyboard(
        ESTADO_FILTRO_PADRAO if all_jobs else "ALL", 5, len(all_jobs)
    )
    send_telegram_message(CHAT_ID, message, reply_markup=reply_markup)


scheduler = BackgroundScheduler(timezone="America/Fortaleza")
scheduler.add_job(scheduled_job, "cron", hour=18, minute=50)
scheduler.start()


# --- ROTAS WEB E WEBHOOK ---
@app.route("/")
def home():
    return "Servidor Agente Pessoal Ativo!", 200


@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def telegram_webhook():
    data = request.get_json()
    if not data:
        return jsonify({"status": "ignored"}), 200

# 1. Trata Mensagens / Comandos
    if "message" in data:
        message = data["message"]
        chat_id = message["chat"]["id"]
        text = message.get("text", "").strip()

        if text in ["/start", "/menu"]:
            msg_texto = (
                "🤖 *Olá! Sou o seu Agente Pessoal.*\n\n"
                "Escolha um dos módulos abaixo para acessar:"
            )
            send_telegram_message(
                chat_id, msg_texto, reply_markup=get_main_menu_keyboard()
            )
        
        # Qualquer outro texto enviado é processado como dúvida para a IA
        elif text:
            send_telegram_message(chat_id, "🧠 *Pensando...*")
            resposta_ia = responder_duvida(text)
            
            # Teclado para voltar ao menu
            keyboard = {"inline_keyboard": [[{"text": "🏠 Menu Principal", "callback_data": "main_menu"}]]}
            send_telegram_message(chat_id, resposta_ia, reply_markup=keyboard)

    # 2. Trata Cliques em Botões Inline
    elif "callback_query" in data:
        callback = data["callback_query"]
        callback_id = callback["id"]
        chat_id = callback["message"]["chat"]["id"]
        data_code = callback.get("data", "")

        answer_callback_query(callback_id)

        # NAVEGAÇÃO DO MENU PRINCIPAL
        if data_code == "main_menu":
            send_telegram_message(
                chat_id,
                "🤖 *Painel Principal do Agente Pessoal:*",
                reply_markup=get_main_menu_keyboard(),
            )

        # MÓDULO: CONCURSOS
        elif data_code == "menu_concursos":
            send_telegram_message(
                chat_id,
                "🏛️ *Módulo de Concursos PCI*\n\nEscolha o estado desejado:",
                reply_markup=get_concursos_state_keyboard(),
            )

        #MODULO IA
        elif data_code == "menu_ia":
            send_telegram_message(
                chat_id,
                "🤖 *Módulo de Inteligência Artificial*\n\n"
                "Pode me enviar qualquer dúvida, pergunta de estudo ou texto diretamente aqui no chat que eu te respondo!",
                reply_markup={"inline_keyboard": [[{"text": "🏠 Voltar", "callback_data": "main_menu"}]]},
            )

        elif data_code.startswith("page_"):
            _, sigla, offset_str = data_code.split("_")
            offset = int(offset_str)
            limit = 5

            filtro = "" if sigla == "ALL" else sigla
            label_estado = "Nordeste (Geral)" if sigla == "ALL" else f"Estado: {sigla}"

            all_jobs = fetch_pci_jobs(filtro_estado=filtro)
            total_items = len(all_jobs)

            if not all_jobs:
                send_telegram_message(
                    chat_id,
                    f"Nenhum concurso encontrado para *{label_estado}*.",
                    reply_markup=get_concursos_state_keyboard(),
                )
            else:
                page_jobs = all_jobs[offset : offset + limit]
                next_offset = offset + len(page_jobs)
                if page_jobs:
                    msg = (
                        f"🚀 *Concursos ({label_estado})* [{offset + 1}-{next_offset} de {total_items}]\n\n"
                        + "\n\n".join(page_jobs)
                    )
                    reply_markup = get_concursos_pagination_keyboard(
                        sigla, next_offset, total_items
                    )
                    send_telegram_message(chat_id, msg, reply_markup=reply_markup)

        # MÓDULOS FUTUROS (STUBS)
        elif data_code == "menu_lembretes":
            send_telegram_message(
                chat_id,
                "📝 *Módulo de Lembretes*\n\nEm breve você poderá gerenciar suas tarefas aqui!",
                reply_markup={"inline_keyboard": [[{"text": "🏠 Voltar", "callback_data": "main_menu"}]]},
            )

        elif data_code == "menu_financas":
            send_telegram_message(
                chat_id,
                "💸 *Módulo de Finanças*\n\nEm breve você poderá registrar seus gastos rápidos aqui!",
                reply_markup={"inline_keyboard": [[{"text": "🏠 Voltar", "callback_data": "main_menu"}]]},
            )

        elif data_code == "menu_ia":
            send_telegram_message(
                chat_id,
                "🤖 *Módulo de Inteligência Artificial*\n\nEm breve integrado com o Gemini!",
                reply_markup={"inline_keyboard": [[{"text": "🏠 Voltar", "callback_data": "main_menu"}]]},
            )

    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)