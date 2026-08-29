import os
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template_string, request, render_template
import requests
from modules.ia import responder_duvida, get_status_uso
from modules.database import salvar_flashcard, obter_flashcards_usuario, atualizar_progresso_card, editar_flashcard, excluir_flashcard, salvar_tarefa, obter_tarefas_usuario, alternar_status_tarefa, excluir_tarefa
from modules.lembretes import get_tasks_keyboard
from modules.financas import (
    salvar_transacao,
    obter_transacoes_usuario,
    excluir_transacao,
    obter_resumo_financeiro,
    obter_despesas_por_categoria,
    salvar_meta_financeira,
    obter_metas_financeiras,
    atualizar_progresso_meta,
    excluir_meta_financeira,
    salvar_despesa_fixa,
    obter_despesas_fixas,
    alternar_despesa_fixa,
    excluir_despesa_fixa,
    obter_previsao_despesas,
    aplicar_despesas_fixas,
    salvar_investimento,
    obter_investimentos,
    atualizar_investimento,
    excluir_investimento,
    calcular_crescimento_investimento,
    salvar_dividendo,
    obter_dividendos,
    excluir_dividendo,
    calcular_projecao_dividendos,
    buscar_cotacao_b3,
    buscar_dividendos_b3,
    atualizar_cotacoes_investimentos,
)


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

APP_URL = "https://botthir.onrender.com"
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
            [
                {"text": "🧠 Abrir App de Flashcards", "web_app": {"url": f"{APP_URL}/flashcards"}}
            ],
            [
                {"text": "💸 Abrir App Finanças", "web_app": {"url": f"{APP_URL}/financas"}}
            ],
        ]
    }

def editar_mensagem_telegram(chat_id, message_id, texto, reply_markup=None):
    """Edita o texto e o teclado de uma mensagem existente."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/editMessageText"
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": texto,
        "parse_mode": "Markdown"
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
        
    requests.post(url, json=payload)

def setup_bot_commands():
    """Configura o menu pop-up de comandos no Telegram."""
    if not TELEGRAM_TOKEN:
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setMyCommands"
    commands = [
        {"command": "start", "description": "Exibe o menu principal do Agente"},
        {"command": "menu", "description": "Abre o painel interativo"},
        {
            "command": "novocard",
            "description": "Cria card. Ex: /novocard Pergunta | Resposta",
        },
        {
            "command": "editarcard",
            "description": "Edita card. Ex: /editarcard ID | Pergunta | Resposta",
        },
        {
            "command": "deletarcard",
            "description": "Remove card. Ex: /deletarcard ID",
        },
        {
            "command": "gasto",
            "description": "Registra despesa. Ex: /gasto 50,00 Mercado",
        },
        {
            "command": "receita",
            "description": "Registra receita. Ex: /receita 2500,00 Salário",
        },
        {
            "command": "resumo",
            "description": "Mostra resumo financeiro do mês",
        },
    ]

    try:
        response = requests.post(url, json={"commands": commands}, timeout=10)
        if response.status_code == 200:
            print("🤖 Comandos do Telegram registrados com sucesso!")
        else:
            print(f"⚠️ Falha ao registrar comandos: {response.text}")
    except Exception as e:
        print(f"Erro ao conectar com API do Telegram: {e}")


# Executa o registro de comandos na inicialização
setup_bot_commands()

def enviar_menu_jogos(chat_id):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": "🎮 **Central de Mini-Games**\nEscolha o modo de treino desejado:",
        "parse_mode": "Markdown",
        "reply_markup": {
            "inline_keyboard": [
                [
                    {
                        "text": "⚡ Jogo da Memória",
                        "web_app": {
                            "url": "https://botthir.onrender.com/templates/game.html"
                        },
                    }
                ],
                [
                    {
                        "text": "⚡ Jogo Teste",
                        "web_app": {
                            "url": "https://seu-dominio.onrender.com/game2.html"
                        },
                    }
                ],
            ]
        },
    }

    requests.post(url, json=payload)

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

@app.route("/game.html")
def servir_jogo():
    with open("game.html", "r", encoding="utf-8") as f:
        conteudo = f.read()
    return render_template(conteudo)

# Rota que entrega a página HTML do Mini App Flashcards
@app.route("/flashcards")
def flashcards_app():
    return render_template("flashcards.html")

# Rota que entrega a página HTML do Mini App de Finanças
@app.route("/financas")
def financas_app():
    return render_template("financas.html")


# API GET: Lista todos os cards do usuário
@app.route("/api/flashcards/<int:user_id>", methods=["GET"])
def get_user_cards(user_id):
    deck = request.args.get("deck", "Geral")
    cards = obter_flashcards_usuario(user_id, deck)
    return jsonify({"status": "success", "cards": cards})


# API POST: Salva um novo card via Telegram ou WebApp
@app.route("/api/flashcards/<int:user_id>", methods=["POST"])
def add_user_card(user_id):
    data = request.get_json()
    pergunta = data.get("pergunta")
    resposta = data.get("resposta")
    deck = data.get("deck", "Geral")

    if not pergunta or not resposta:
        return jsonify({"status": "error", "message": "Dados incompletos"}), 400

    sucesso, msg = salvar_flashcard(user_id, deck, pergunta, resposta)
    return jsonify({"status": "success" if sucesso else "error", "message": msg})

@app.route("/api/flashcards/<int:user_id>/<card_id>", methods=["PUT"])
def update_user_card(user_id, card_id):
    """Endpoint para editar a pergunta/resposta de um card existente."""
    data = request.get_json() or {}
    pergunta = data.get("pergunta")
    resposta = data.get("resposta")
    deck = data.get("deck", "Geral")

    if not pergunta or not resposta:
        return jsonify({"status": "error", "message": "Dados incompletos"}), 400

    sucesso, msg = editar_flashcard(user_id, deck, card_id, pergunta, resposta)
    return jsonify({"status": "success" if sucesso else "error", "message": msg})

@app.route("/api/flashcards/<int:user_id>/<card_id>", methods=["DELETE"])
def delete_user_card(user_id, card_id):
    """Endpoint para remover um flashcard do banco."""
    deck = request.args.get("deck", "Geral")
    sucesso, msg = excluir_flashcard(user_id, deck, card_id)
    return jsonify({"status": "success" if sucesso else "error", "message": msg})

@app.route("/api/flashcards/<int:user_id>/review", methods=["POST"])
def review_user_card(user_id):
    """Endpoint chamado quando o usuário avalia a dificuldade (Errei, Bom, Fácil) no Mini App."""
    data = request.get_json() or {}
    card_id = data.get("card_id")
    dificuldade = data.get("dificuldade")  # 1 (Errei), 3 (Bom), 5 (Fácil)
    deck = data.get("deck", "Geral")

    if not card_id or dificuldade is None:
        return jsonify({"status": "error", "message": "Parâmetros ausentes"}), 400

    sucesso, msg = atualizar_progresso_card(
        user_id, deck, card_id, dificuldade
    )
    return jsonify({"status": "success" if sucesso else "error", "message": msg})

# ===== API DE FINANÇAS =====

# API GET: Lista transações do usuário (com filtro opcional por mês/ano)
@app.route("/api/financas/<int:user_id>", methods=["GET"])
def get_user_transacoes(user_id):
    mes = request.args.get("mes")
    ano = request.args.get("ano")
    transacoes = obter_transacoes_usuario(user_id, mes, ano)
    return jsonify({"status": "success", "transacoes": transacoes})

# API POST: Salva uma nova transação
@app.route("/api/financas/<int:user_id>", methods=["POST"])
def add_user_transacao(user_id):
    data = request.get_json() or {}
    tipo = data.get("tipo")
    descricao = data.get("descricao")
    valor = data.get("valor")
    categoria = data.get("categoria", "Geral")
    data_transacao = data.get("data")

    if not tipo or not descricao or not valor:
        return jsonify({"status": "error", "message": "Dados incompletos"}), 400

    if tipo not in ["receita", "despesa"]:
        return jsonify({"status": "error", "message": "Tipo inválido"}), 400

    sucesso, msg = salvar_transacao(user_id, tipo, descricao, valor, categoria, data_transacao)
    return jsonify({"status": "success" if sucesso else "error", "message": msg})

# API GET: Resumo financeiro do mês
@app.route("/api/financas/<int:user_id>/resumo", methods=["GET"])
def get_user_resumo_financeiro(user_id):
    mes = request.args.get("mes")
    ano = request.args.get("ano")
    resumo = obter_resumo_financeiro(user_id, mes, ano)
    return jsonify({"status": "success", **resumo})

# API GET: Despesas por categoria
@app.route("/api/financas/<int:user_id>/categorias", methods=["GET"])
def get_user_despesas_categorias(user_id):
    mes = request.args.get("mes")
    ano = request.args.get("ano")
    categorias = obter_despesas_por_categoria(user_id, mes, ano)
    return jsonify({"status": "success", **categorias})

# API GET: Lista metas financeiras
@app.route("/api/financas/<int:user_id>/metas", methods=["GET"])
def get_user_metas(user_id):
    metas = obter_metas_financeiras(user_id)
    return jsonify({"status": "success", "metas": metas})

# API POST: Salva uma nova meta financeira
@app.route("/api/financas/<int:user_id>/metas", methods=["POST"])
def add_user_meta(user_id):
    data = request.get_json() or {}
    titulo = data.get("titulo")
    valor_meta = data.get("valor_meta")
    valor_atual = data.get("valor_atual", 0)

    if not titulo or not valor_meta:
        return jsonify({"status": "error", "message": "Dados incompletos"}), 400

    sucesso, msg = salvar_meta_financeira(user_id, titulo, valor_meta, valor_atual)
    return jsonify({"status": "success" if sucesso else "error", "message": msg})

# API PUT: Atualiza progresso de uma meta
@app.route("/api/financas/<int:user_id>/metas/<meta_id>", methods=["PUT"])
def update_user_meta(user_id, meta_id):
    data = request.get_json() or {}
    valor_atual = data.get("valor_atual")

    if valor_atual is None:
        return jsonify({"status": "error", "message": "Valor atual ausente"}), 400

    sucesso, msg = atualizar_progresso_meta(user_id, meta_id, valor_atual)
    return jsonify({"status": "success" if sucesso else "error", "message": msg})

# API DELETE: Exclui uma meta financeira
@app.route("/api/financas/<int:user_id>/metas/<meta_id>", methods=["DELETE"])
def delete_user_meta(user_id, meta_id):
    sucesso, msg = excluir_meta_financeira(user_id, meta_id)
    return jsonify({"status": "success" if sucesso else "error", "message": msg})

# API DELETE: Exclui uma transação
@app.route("/api/financas/<int:user_id>/<transacao_id>", methods=["DELETE"])
def delete_user_transacao(user_id, transacao_id):
    sucesso, msg = excluir_transacao(user_id, transacao_id)
    return jsonify({"status": "success" if sucesso else "error", "message": msg})

# ===== API DE DESPESAS FIXAS =====

# API GET: Lista despesas fixas
@app.route("/api/financas/<int:user_id>/despesas-fixas", methods=["GET"])
def get_user_despesas_fixas(user_id):
    despesas = obter_despesas_fixas(user_id)
    return jsonify({"status": "success", "despesas_fixas": despesas})

# API POST: Salva uma nova despesa fixa
@app.route("/api/financas/<int:user_id>/despesas-fixas", methods=["POST"])
def add_user_despesa_fixa(user_id):
    data = request.get_json() or {}
    descricao = data.get("descricao")
    valor = data.get("valor")
    dia_vencimento = data.get("dia_vencimento")
    categoria = data.get("categoria", "Geral")

    if not descricao or not valor or not dia_vencimento:
        return jsonify({"status": "error", "message": "Dados incompletos"}), 400

    sucesso, msg = salvar_despesa_fixa(user_id, descricao, valor, dia_vencimento, categoria)
    return jsonify({"status": "success" if sucesso else "error", "message": msg})

# API PUT: Ativa/desativa despesa fixa
@app.route("/api/financas/<int:user_id>/despesas-fixas/<despesa_id>", methods=["PUT"])
def toggle_user_despesa_fixa(user_id, despesa_id):
    sucesso, msg = alternar_despesa_fixa(user_id, despesa_id)
    return jsonify({"status": "success" if sucesso else "error", "message": msg})

# API DELETE: Exclui despesa fixa
@app.route("/api/financas/<int:user_id>/despesas-fixas/<despesa_id>", methods=["DELETE"])
def delete_user_despesa_fixa(user_id, despesa_id):
    sucesso, msg = excluir_despesa_fixa(user_id, despesa_id)
    return jsonify({"status": "success" if sucesso else "error", "message": msg})

# API GET: Previsão de despesas do mês
@app.route("/api/financas/<int:user_id>/previsao", methods=["GET"])
def get_user_previsao_despesas(user_id):
    mes = request.args.get("mes")
    ano = request.args.get("ano")
    previsao = obter_previsao_despesas(user_id, mes, ano)
    return jsonify({"status": "success", **previsao})

# API POST: Aplica despesas fixas do mês como transações
@app.route("/api/financas/<int:user_id>/aplicar-fixas", methods=["POST"])
def apply_user_despesas_fixas(user_id):
    mes = request.args.get("mes")
    ano = request.args.get("ano")
    aplicadas = aplicar_despesas_fixas(user_id, mes, ano)
    return jsonify({"status": "success", "aplicadas": aplicadas})

# ===== API DE INVESTIMENTOS =====

# API GET: Lista investimentos
@app.route("/api/financas/<int:user_id>/investimentos", methods=["GET"])
def get_user_investimentos(user_id):
    investimentos = obter_investimentos(user_id)
    return jsonify({"status": "success", "investimentos": investimentos})

# API POST: Salva um novo investimento
@app.route("/api/financas/<int:user_id>/investimentos", methods=["POST"])
def add_user_investimento(user_id):
    data = request.get_json() or {}
    nome = data.get("nome")
    tipo = data.get("tipo", "outro")
    valor_investido = data.get("valor_investido")
    corretora = data.get("corretora", "")
    taxa_anual = data.get("taxa_anual", 0)
    data_inicio = data.get("data_inicio")
    observacoes = data.get("observacoes", "")

    if not nome or not valor_investido:
        return jsonify({"status": "error", "message": "Dados incompletos"}), 400

    sucesso, msg = salvar_investimento(
        user_id, nome, tipo, valor_investido, corretora, taxa_anual, data_inicio, observacoes
    )
    return jsonify({"status": "success" if sucesso else "error", "message": msg})

# API PUT: Atualiza investimento
@app.route("/api/financas/<int:user_id>/investimentos/<investimento_id>", methods=["PUT"])
def update_user_investimento(user_id, investimento_id):
    data = request.get_json() or {}
    sucesso, msg = atualizar_investimento(user_id, investimento_id, data)
    return jsonify({"status": "success" if sucesso else "error", "message": msg})

# API DELETE: Exclui investimento
@app.route("/api/financas/<int:user_id>/investimentos/<investimento_id>", methods=["DELETE"])
def delete_user_investimento(user_id, investimento_id):
    sucesso, msg = excluir_investimento(user_id, investimento_id)
    return jsonify({"status": "success" if sucesso else "error", "message": msg})

# API GET: Crescimento dos investimentos
@app.route("/api/financas/<int:user_id>/investimentos/crescimento", methods=["GET"])
def get_user_crescimento_investimentos(user_id):
    resultado = calcular_crescimento_investimento(user_id)
    return jsonify({"status": "success", **resultado})

# ===== API DE DIVIDENDOS =====

# API GET: Lista dividendos programados
@app.route("/api/financas/<int:user_id>/dividendos", methods=["GET"])
def get_user_dividendos(user_id):
    dividendos = obter_dividendos(user_id)
    return jsonify({"status": "success", "dividendos": dividendos})

# API POST: Salva um novo dividendo programado
@app.route("/api/financas/<int:user_id>/dividendos", methods=["POST"])
def add_user_dividendo(user_id):
    data = request.get_json() or {}
    investimento_id = data.get("investimento_id")
    descricao = data.get("descricao")
    valor_estimado = data.get("valor_estimado")
    frequencia = data.get("frequencia", "mensal")
    dia_recebimento = data.get("dia_recebimento", 1)

    if not investimento_id or not descricao or not valor_estimado:
        return jsonify({"status": "error", "message": "Dados incompletos"}), 400

    sucesso, msg = salvar_dividendo(
        user_id, investimento_id, descricao, valor_estimado, frequencia, dia_recebimento
    )
    return jsonify({"status": "success" if sucesso else "error", "message": msg})

# API DELETE: Exclui dividendo
@app.route("/api/financas/<int:user_id>/dividendos/<dividendo_id>", methods=["DELETE"])
def delete_user_dividendo(user_id, dividendo_id):
    sucesso, msg = excluir_dividendo(user_id, dividendo_id)
    return jsonify({"status": "success" if sucesso else "error", "message": msg})

# API GET: Projeção de dividendos
@app.route("/api/financas/<int:user_id>/dividendos/projecao", methods=["GET"])
def get_user_projecao_dividendos(user_id):
    meses = int(request.args.get("meses", 12))
    projecao = calcular_projecao_dividendos(user_id, meses)
    return jsonify({"status": "success", **projecao})

# ===== API B3 (yfinance) =====

# API GET: Busca cotação de ativo da B3
@app.route("/api/b3/cotacao/<ticker>", methods=["GET"])
def get_b3_cotacao(ticker):
    cotacao, erro = buscar_cotacao_b3(ticker)
    if erro:
        return jsonify({"status": "error", "message": erro}), 400
    return jsonify({"status": "success", **cotacao})

# API GET: Busca histórico de dividendos de ativo da B3
@app.route("/api/b3/dividendos/<ticker>", methods=["GET"])
def get_b3_dividendos(ticker):
    periodo = request.args.get("periodo", "1y")
    dividendos, erro = buscar_dividendos_b3(ticker, periodo)
    if erro:
        return jsonify({"status": "error", "message": erro}), 400
    return jsonify({"status": "success", "dividendos": dividendos})

# API GET: Atualiza cotações de todos os investimentos do usuário
@app.route("/api/financas/<int:user_id>/investimentos/cotacoes", methods=["GET"])
def get_user_cotacoes_investimentos(user_id):
    cotacoes = atualizar_cotacoes_investimentos(user_id)
    return jsonify({"status": "success", "cotacoes": cotacoes})

@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def telegram_webhook():
    data = request.get_json()
    if not data:
        return jsonify({"status": "ignored"}), 200

# 1. Trata Mensagens / Comandos
    if "message" in data:
        message = data["message"]
        chat_id = message["chat"]["id"]
        user_id = message["from"]["id"]
        text = message.get("text", "").strip()

        if text in ["/start", "/menu"]:
            msg_texto = (
                "🤖 *Olá! Sou o seu Agente Pessoal.*\n\n"
                "Escolha um dos módulos abaixo para acessar:"
            )
            send_telegram_message(
                chat_id, msg_texto, reply_markup=get_main_menu_keyboard()
            )

        # COMANDO PARA CRIAR FLASHCARD DIRETO DO TELEGRAM: /novocard Pergunta | Resposta
        elif text.startswith("/novocard"):
            conteudo = text.replace("/novocard", "").strip()
            if "|" in conteudo:
                pergunta, resposta = [item.strip() for item in conteudo.split("|", 1)]
                sucesso, msg = salvar_flashcard(user_id, "Geral", pergunta, resposta)
                if sucesso:
                    reply = f"✅ *Flashcard salvo com sucesso!*\n\n❓ *P:* {pergunta}\n💡 *R:* {resposta}"
                else:
                    reply = f"❌ Erro ao salvar flashcard: {msg}"
            else:
                reply = (
                    "⚠️ *Formato incorreto!*\n\n"
                    "Envie no formato:\n"
                    "`/novocard Sua pergunta aqui | Sua resposta aqui`"
                )
            send_telegram_message(chat_id, reply)

        # EDITAR FLASHCARD: /editarcard ID | Nova Pergunta | Nova Resposta
        elif text.startswith("/editarcard"):
            conteudo = text.replace("/editarcard", "").strip()
            partes = [p.strip() for p in conteudo.split("|")]
            if len(partes) == 3:
                card_id, nova_pergunta, nova_resposta = partes
                sucesso, msg = editar_flashcard(
                    user_id, "Geral", card_id, nova_pergunta, nova_resposta
                )
                if sucesso:
                    reply = f"✏️ *Flashcard editado com sucesso!*"
                else:
                    reply = f"❌ Erro ao editar flashcard: {msg}"
            else:
                reply = (
                    "⚠️ *Formato incorreto!*\n\n"
                    "Envie no formato:\n"
                    "`/editarcard ID_DO_CARD | Nova Pergunta | Nova Resposta`"
                )
            send_telegram_message(chat_id, reply)

        # DELETAR FLASHCARD: /deletarcard ID
        elif text.startswith("/deletarcard"):
            card_id = text.replace("/deletarcard", "").strip()
            if card_id:
                sucesso, msg = excluir_flashcard(user_id, "Geral", card_id)
                if sucesso:
                    reply = "🗑️ *Flashcard removido com sucesso!*"
                else:
                    reply = f"❌ Erro ao excluir flashcard: {msg}"
            else:
                reply = (
                    "⚠️ *Formato incorreto!*\n\n"
                    "Envie no formato:\n"
                    "`/deletarcard ID_DO_CARD`"
                )
            send_telegram_message(chat_id, reply)

        # ADICIONAR NOVA TAREFA: /novatarefa [Título da Tarefa]
        elif text.startswith("/novatarefa"):
                titulo_tarefa = text.replace("/novatarefa", "").strip()
                if titulo_tarefa:
                    sucesso, msg_resp = salvar_tarefa(user_id, titulo_tarefa)
                    if sucesso:
                        reply = f"✅ Tarefa *'{titulo_tarefa}'* salva com sucesso!"
                    else:
                        reply = f"❌ Erro ao salvar tarefa: {msg_resp}"
                else:
                    reply = "⚠️ Informe o título da tarefa. Exemplo:\n`/novatarefa Comprar material de estudo`"
                send_telegram_message(chat_id, reply)

        # REGISTRAR DESPESA: /gasto 50,00 Mercado
        elif text.startswith("/gasto"):
            conteudo = text.replace("/gasto", "").strip()
            partes = conteudo.split(" ", 1)
            if len(partes) == 2:
                valor_str = partes[0].replace(",", ".")
                descricao = partes[1].strip()
                try:
                    valor = float(valor_str)
                    sucesso, msg = salvar_transacao(user_id, "despesa", descricao, valor, "Outros")
                    if sucesso:
                        reply = f"✅ *Despesa registrada!*\n\n💸 *Valor:* R$ {valor:.2f}\n📝 *Descrição:* {descricao}"
                    else:
                        reply = f"❌ Erro ao registrar despesa: {msg}"
                except ValueError:
                    reply = "⚠️ Valor inválido! Use o formato:\n`/gasto 50,00 Mercado`"
            else:
                reply = "⚠️ Formato incorreto! Use:\n`/gasto 50,00 Mercado`"
            send_telegram_message(chat_id, reply)

        # REGISTRAR RECEITA: /receita 2500,00 Salário
        elif text.startswith("/receita"):
            conteudo = text.replace("/receita", "").strip()
            partes = conteudo.split(" ", 1)
            if len(partes) == 2:
                valor_str = partes[0].replace(",", ".")
                descricao = partes[1].strip()
                try:
                    valor = float(valor_str)
                    sucesso, msg = salvar_transacao(user_id, "receita", descricao, valor, "Salário")
                    if sucesso:
                        reply = f"✅ *Receita registrada!*\n\n💰 *Valor:* R$ {valor:.2f}\n📝 *Descrição:* {descricao}"
                    else:
                        reply = f"❌ Erro ao registrar receita: {msg}"
                except ValueError:
                    reply = "⚠️ Valor inválido! Use o formato:\n`/receita 2500,00 Salário`"
            else:
                reply = "⚠️ Formato incorreto! Use:\n`/receita 2500,00 Salário`"
            send_telegram_message(chat_id, reply)

        # VER RESUMO FINANCEIRO: /resumo
        elif text.startswith("/resumo"):
            resumo = obter_resumo_financeiro(user_id)
            saldo = resumo["saldo"]
            emoji_saldo = "🟢" if saldo >= 0 else "🔴"
            reply = (
                "💸 *Resumo Financeiro do Mês*\n\n"
                f"💰 *Receitas:* R$ {resumo['total_receitas']:.2f}\n"
                f"💸 *Despesas:* R$ {resumo['total_despesas']:.2f}\n"
                f"{emoji_saldo} *Saldo:* R$ {saldo:.2f}\n\n"
                f"📊 *Total de transações:* {resumo['quantidade_transacoes']}"
            )
            keyboard = {"inline_keyboard": [[{"text": "💸 Abrir App de Finanças", "web_app": {"url": f"{APP_URL}/financas"}}]]}
            send_telegram_message(chat_id, reply, reply_markup=keyboard)

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
        user_id = callback["from"]["id"]
        message_id = callback["message"]["message_id"]
        data_code = callback.get("data", "")

        answer_callback_query(callback_id)

        # NAVEGAÇÃO DO MENU PRINCIPAL
        if data_code == "main_menu":
            editar_mensagem_telegram(
                chat_id,
                message_id,
                "🤖 *Painel Principal do Agente Pessoal:*",
                reply_markup=get_main_menu_keyboard(),
            )

        # MÓDULO: CONCURSOS
        elif data_code == "menu_concursos":
            editar_mensagem_telegram(
                chat_id,
                message_id,
                "🏛️ *Módulo de Concursos PCI*\n\nEscolha o estado desejado:",
                reply_markup=get_concursos_state_keyboard(),
            )

        #MODULO IA
        elif data_code == "menu_ia":
            status_limite = get_status_uso()
            msg = (
                "🤖 *Módulo de Inteligência Artificial*\n\n"
                "Envie qualquer mensagem de texto diretamente no chat para tirar suas dúvidas!\n\n"
                f"{status_limite}"
            )
            editar_mensagem_telegram(
                chat_id,
                message_id,
                msg,
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
                editar_mensagem_telegram(
                    chat_id,
                    message_id,
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
                    editar_mensagem_telegram(chat_id, message_id, msg, reply_markup=reply_markup)

        # MÓDULO: LEMBRETES & TAREFAS
        elif data_code == "menu_lembretes":
            tasks = obter_tarefas_usuario(user_id)
            msg = "📝 *Módulo de Lembretes & Tarefas*\n\nSuas tarefas cadastradas:"
            editar_mensagem_telegram(chat_id, message_id, msg, reply_markup=get_tasks_keyboard(tasks))

        elif data_code.startswith("task_toggle_"):
            task_id = data_code.replace("task_toggle_", "")
            alternar_status_tarefa(user_id, task_id)
            
            # Atualiza a lista na mesma mensagem
            tasks = obter_tarefas_usuario(user_id)
            editar_mensagem_telegram(chat_id, message_id, "📝 *Módulo de Lembretes & Tarefas*\n\nSuas tarefas cadastradas:", reply_markup=get_tasks_keyboard(tasks))

        elif data_code.startswith("task_del_"):
            task_id = data_code.replace("task_del_", "")
            excluir_tarefa(user_id, task_id)
            
            # Atualiza a lista na mesma mensagem
            tasks = obter_tarefas_usuario(user_id)
            editar_mensagem_telegram(chat_id, message_id, "📝 *Módulo de Lembretes & Tarefas*\n\nSuas tarefas cadastradas:", reply_markup=get_tasks_keyboard(tasks))

        elif data_code == "task_new_prompt":
            msg = "✍️ Para adicionar uma nova tarefa, envie no chat:\n\n`/novatarefa [Título da Tarefa]`"
            keyboard = {"inline_keyboard": [[{"text": "⬅️ Voltar aos Lembretes", "callback_data": "menu_lembretes"}]]}
            editar_mensagem_telegram(chat_id, message_id, msg, reply_markup=keyboard)

        elif data_code == "menu_financas":
            editar_mensagem_telegram(
                chat_id,
                message_id,
                "💸 *Módulo de Finanças*\n\n"
                "Acesse o app completo de gestão financeira ou registre gastos rápidos:\n\n"
                "📌 *Comandos rápidos:*\n"
                "`/gasto 50,00 Mercado` - Registra despesa\n"
                "`/receita 2500,00 Salário` - Registra receita\n"
                "`/resumo` - Ver resumo do mês",
                reply_markup={
                    "inline_keyboard": [
                        [
                            {
                                "text": "💸 Abrir App de Finanças",
                                "web_app": {"url": f"{APP_URL}/financas"},
                            }
                        ],
                        [{"text": "🏠 Voltar", "callback_data": "main_menu"}],
                    ]
                },
            )

        elif data_code == "menu_ia":
            editar_mensagem_telegram(
                chat_id,
                message_id,
                "🤖 *Módulo de Inteligência Artificial*\n\nEm breve integrado com o Gemini!",
                reply_markup={"inline_keyboard": [[{"text": "🏠 Voltar", "callback_data": "main_menu"}]]},
            )

    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)