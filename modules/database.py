import json
import os
from datetime import datetime
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore

# Inicializa o Firebase Admin SDK
load_dotenv()
cred_env = os.getenv("FIREBASE_CREDENTIALS")

if cred_env:
    cred_dict = json.loads(cred_env)
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
else:
    db = None
    print("⚠️ FIREBASE_CREDENTIALS não configurado.")


def salvar_flashcard(user_id, deck_name, pergunta, resposta):
    """Salva um novo flashcard para um usuário específico em um baralho."""
    if not db:
        return False, "Database offline"

    try:
        doc_ref = (
            db.collection("users")
            .document(str(user_id))
            .collection("decks")
            .document(deck_name)
            .collection("cards")
            .document()
        )

        card_data = {
            "pergunta": pergunta,
            "resposta": resposta,
            "intervalo": 1,  # Intervalo inicial de repetição (em dias)
            "repeticoes": 0,
            "facilidade": 2.5,  # Fator de facilidade inicial do algoritmo SM-2
            "proxima_revisao": datetime.now().strftime("%Y-%m-%d"),
            "criado_em": datetime.now(),
        }

        doc_ref.set(card_data)
        return True, "Flashcard salvo com sucesso!"
    except Exception as e:
        print(f"Erro ao salvar card no Firebase: {e}")
        return False, str(e)


def obter_flashcards_usuario(user_id, deck_name="Geral"):
    """Retorna a lista de flashcards de um usuário para um determinado baralho."""
    if not db:
        return []

    try:
        cards_ref = (
            db.collection("users")
            .document(str(user_id))
            .collection("decks")
            .document(deck_name)
            .collection("cards")
            .stream()
        )

        cards = []
        for doc in cards_ref:
            data = doc.to_dict()
            data["id"] = doc.id
            cards.append(data)

        return cards
    except Exception as e:
        print(f"Erro ao buscar cards no Firebase: {e}")
        return []


def editar_flashcard(user_id, deck_name, card_id, nova_pergunta, nova_resposta):
    """Atualiza o conteúdo de pergunta e resposta de um flashcard existente."""
    if not db:
        return False, "Database offline"

    try:
        doc_ref = (
            db.collection("users")
            .document(str(user_id))
            .collection("decks")
            .document(deck_name)
            .collection("cards")
            .document(card_id)
        )

        doc_ref.update(
            {
                "pergunta": nova_pergunta,
                "resposta": nova_resposta,
                "atualizado_em": datetime.now(),
            }
        )
        return True, "Flashcard atualizado com sucesso!"
    except Exception as e:
        print(f"Erro ao editar card no Firebase: {e}")
        return False, str(e)


def excluir_flashcard(user_id, deck_name, card_id):
    """Remove um flashcard do banco de dados pelo seu ID."""
    if not db:
        return False, "Database offline"

    try:
        doc_ref = (
            db.collection("users")
            .document(str(user_id))
            .collection("decks")
            .document(deck_name)
            .collection("cards")
            .document(card_id)
        )

        doc_ref.delete()
        return True, "Flashcard excluído com sucesso!"
    except Exception as e:
        print(f"Erro ao excluir card no Firebase: {e}")
        return False, str(e)


def atualizar_progresso_card(
    user_id, deck_name, card_id, facilidade, intervalo, repeticoes, prox_data
):
    """Atualiza a pontuação do algoritmo de repetição espaçada após a resposta."""
    if not db:
        return False

    try:
        doc_ref = (
            db.collection("users")
            .document(str(user_id))
            .collection("decks")
            .document(deck_name)
            .collection("cards")
            .document(card_id)
        )

        doc_ref.update(
            {
                "facilidade": facilidade,
                "intervalo": intervalo,
                "repeticoes": repeticoes,
                "proxima_revisao": prox_data,
            }
        )
        return True
    except Exception as e:
        print(f"Erro ao atualizar progresso do card: {e}")
        return False

def salvar_tarefa(user_id, titulo, data_vencimento=""):
    """Salva uma nova tarefa para o usuário."""
    if not db:
        return False, "Database offline"
    try:
        doc_ref = db.collection("users").document(str(user_id)).collection("tasks").document()
        task_data = {
            "titulo": titulo,
            "vencimento": data_vencimento,
            "concluida": False,
            "criado_em": datetime.now()
        }
        doc_ref.set(task_data)
        return True, "Tarefa salva com sucesso!"
    except Exception as e:
        return False, str(e)

def obter_tarefas_usuario(user_id):
    """Retorna todas as tarefas de um usuário."""
    if not db:
        return []
    try:
        tasks_ref = db.collection("users").document(str(user_id)).collection("tasks").stream()
        tasks = []
        for doc in tasks_ref:
            data = doc.to_dict()
            data["id"] = doc.id
            tasks.append(data)
        return tasks
    except Exception as e:
        return []

def alternar_status_tarefa(user_id, task_id):
    """Alterna o status de concluída/pendente de uma tarefa."""
    if not db:
        return False
    try:
        doc_ref = db.collection("users").document(str(user_id)).collection("tasks").document(task_id)
        doc = doc_ref.get()
        if doc.exists:
            status_atual = doc.to_dict().get("concluida", False)
            doc_ref.update({"concluida": not status_atual})
            return True
        return False
    except Exception as e:
        return False

def excluir_tarefa(user_id, task_id):
    """Exclui uma tarefa do banco."""
    if not db:
        return False
    try:
        db.collection("users").document(str(user_id)).collection("tasks").document(task_id).delete()
        return True
    except Exception as e:
        return False