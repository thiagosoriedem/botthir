from datetime import datetime
from modules.database import db


def salvar_transacao(user_id, tipo, descricao, valor, categoria="Geral", data=None):
    """Salva uma nova transação financeira (receita ou despesa)."""
    if not db:
        return False, "Database offline"

    try:
        doc_ref = (
            db.collection("users")
            .document(str(user_id))
            .collection("financas")
            .document()
        )

        if data is None:
            data = datetime.now().strftime("%Y-%m-%d")

        transacao_data = {
            "tipo": tipo,  # "receita" ou "despesa"
            "descricao": descricao,
            "valor": float(valor),
            "categoria": categoria,
            "data": data,
            "criado_em": datetime.now(),
        }

        doc_ref.set(transacao_data)
        return True, "Transação salva com sucesso!"
    except Exception as e:
        print(f"Erro ao salvar transação no Firebase: {e}")
        return False, str(e)


def obter_transacoes_usuario(user_id, mes=None, ano=None):
    """Retorna todas as transações de um usuário, opcionalmente filtradas por mês/ano."""
    if not db:
        return []

    try:
        transacoes_ref = (
            db.collection("users")
            .document(str(user_id))
            .collection("financas")
            .stream()
        )

        transacoes = []
        for doc in transacoes_ref:
            data = doc.to_dict()
            data["id"] = doc.id

            # Filtro por mês/ano se especificado
            if mes and ano:
                data_transacao = data.get("data", "")
                if data_transacao:
                    try:
                        dt = datetime.strptime(data_transacao, "%Y-%m-%d")
                        if dt.month != int(mes) or dt.year != int(ano):
                            continue
                    except ValueError:
                        pass

            transacoes.append(data)

        # Ordena por data (mais recente primeiro)
        transacoes.sort(key=lambda x: x.get("data", ""), reverse=True)
        return transacoes
    except Exception as e:
        print(f"Erro ao buscar transações no Firebase: {e}")
        return []


def excluir_transacao(user_id, transacao_id):
    """Remove uma transação financeira pelo ID."""
    if not db:
        return False, "Database offline"

    try:
        doc_ref = (
            db.collection("users")
            .document(str(user_id))
            .collection("financas")
            .document(transacao_id)
        )
        doc_ref.delete()
        return True, "Transação excluída com sucesso!"
    except Exception as e:
        print(f"Erro ao excluir transação no Firebase: {e}")
        return False, str(e)


def obter_resumo_financeiro(user_id, mes=None, ano=None):
    """Calcula o resumo financeiro: saldo, total de receitas e despesas."""
    transacoes = obter_transacoes_usuario(user_id, mes, ano)

    total_receitas = 0.0
    total_despesas = 0.0

    for t in transacoes:
        valor = float(t.get("valor", 0))
        if t.get("tipo") == "receita":
            total_receitas += valor
        elif t.get("tipo") == "despesa":
            total_despesas += valor

    saldo = total_receitas - total_despesas

    return {
        "saldo": round(saldo, 2),
        "total_receitas": round(total_receitas, 2),
        "total_despesas": round(total_despesas, 2),
        "quantidade_transacoes": len(transacoes),
    }


def obter_despesas_por_categoria(user_id, mes=None, ano=None):
    """Agrupa as despesas por categoria para exibição em gráficos."""
    transacoes = obter_transacoes_usuario(user_id, mes, ano)

    categorias = {}
    for t in transacoes:
        if t.get("tipo") == "despesa":
            categoria = t.get("categoria", "Geral")
            valor = float(t.get("valor", 0))
            categorias[categoria] = categorias.get(categoria, 0) + valor

    # Ordena por valor decrescente
    categorias_ordenadas = dict(
        sorted(categorias.items(), key=lambda item: item[1], reverse=True)
    )
    return categorias_ordenadas


def salvar_meta_financeira(user_id, titulo, valor_meta, valor_atual=0.0):
    """Salva uma meta financeira para o usuário."""
    if not db:
        return False, "Database offline"

    try:
        doc_ref = (
            db.collection("users")
            .document(str(user_id))
            .collection("metas_financeiras")
            .document()
        )

        meta_data = {
            "titulo": titulo,
            "valor_meta": float(valor_meta),
            "valor_atual": float(valor_atual),
            "criado_em": datetime.now(),
        }

        doc_ref.set(meta_data)
        return True, "Meta financeira salva com sucesso!"
    except Exception as e:
        print(f"Erro ao salvar meta no Firebase: {e}")
        return False, str(e)


def obter_metas_financeiras(user_id):
    """Retorna todas as metas financeiras do usuário."""
    if not db:
        return []

    try:
        metas_ref = (
            db.collection("users")
            .document(str(user_id))
            .collection("metas_financeiras")
            .stream()
        )

        metas = []
        for doc in metas_ref:
            data = doc.to_dict()
            data["id"] = doc.id
            # Calcula percentual de progresso
            valor_meta = float(data.get("valor_meta", 0))
            valor_atual = float(data.get("valor_atual", 0))
            if valor_meta > 0:
                data["percentual"] = round((valor_atual / valor_meta) * 100, 1)
            else:
                data["percentual"] = 0
            metas.append(data)

        return metas
    except Exception as e:
        print(f"Erro ao buscar metas no Firebase: {e}")
        return []


def atualizar_progresso_meta(user_id, meta_id, novo_valor):
    """Atualiza o valor atual de uma meta financeira."""
    if not db:
        return False, "Database offline"

    try:
        doc_ref = (
            db.collection("users")
            .document(str(user_id))
            .collection("metas_financeiras")
            .document(meta_id)
        )
        doc_ref.update({"valor_atual": float(novo_valor)})
        return True, "Meta atualizada com sucesso!"
    except Exception as e:
        print(f"Erro ao atualizar meta no Firebase: {e}")
        return False, str(e)


def excluir_meta_financeira(user_id, meta_id):
    """Remove uma meta financeira."""
    if not db:
        return False, "Database offline"

    try:
        doc_ref = (
            db.collection("users")
            .document(str(user_id))
            .collection("metas_financeiras")
            .document(meta_id)
        )
        doc_ref.delete()
        return True, "Meta excluída com sucesso!"
    except Exception as e:
        print(f"Erro ao excluir meta no Firebase: {e}")
        return False, str(e)