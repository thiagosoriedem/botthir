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
            "facilidade": 2.5,  # Factor de facilidade inicial do algoritmo SM-2
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