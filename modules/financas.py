from datetime import datetime, timedelta
from modules.database import db

# ============================================
# TRANSAÇÕES
# ============================================

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


# ============================================
# DESPESAS FIXAS
# ============================================

def salvar_despesa_fixa(user_id, descricao, valor, dia_vencimento, categoria="Geral", ativa=True, data_fim=None):
    """Salva uma despesa fixa recorrente (ex: aluguel todo dia 5)."""
    if not db:
        return False, "Database offline"

    try:
        doc_ref = (
            db.collection("users")
            .document(str(user_id))
            .collection("despesas_fixas")
            .document()
        )

        despesa_data = {
            "descricao": descricao,
            "valor": float(valor),
            "dia_vencimento": int(dia_vencimento),
            "categoria": categoria,
            "ativa": ativa,
            "data_fim": data_fim or "",  # Data opcional de término (YYYY-MM-DD) ou "" para indeterminada
            "criado_em": datetime.now(),
        }

        doc_ref.set(despesa_data)
        return True, "Despesa fixa salva com sucesso!"
    except Exception as e:
        print(f"Erro ao salvar despesa fixa no Firebase: {e}")
        return False, str(e)


def atualizar_despesa_fixa(user_id, despesa_id, dados_atualizados):
    """Atualiza uma despesa fixa existente."""
    if not db:
        return False, "Database offline"

    try:
        doc_ref = (
            db.collection("users")
            .document(str(user_id))
            .collection("despesas_fixas")
            .document(despesa_id)
        )
        doc_ref.update(dados_atualizados)
        return True, "Despesa fixa atualizada com sucesso!"
    except Exception as e:
        print(f"Erro ao atualizar despesa fixa: {e}")
        return False, str(e)


def obter_despesas_fixas(user_id, ativa=None):
    """Retorna todas as despesas fixas do usuário."""
    if not db:
        return []

    try:
        despesas_ref = (
            db.collection("users")
            .document(str(user_id))
            .collection("despesas_fixas")
            .stream()
        )

        despesas = []
        for doc in despesas_ref:
            data = doc.to_dict()
            data["id"] = doc.id
            if ativa is not None and data.get("ativa", True) != ativa:
                continue
            despesas.append(data)

        # Ordena por dia de vencimento
        despesas.sort(key=lambda x: x.get("dia_vencimento", 1))
        return despesas
    except Exception as e:
        print(f"Erro ao buscar despesas fixas no Firebase: {e}")
        return []


def alternar_despesa_fixa(user_id, despesa_id):
    """Ativa/desativa uma despesa fixa."""
    if not db:
        return False, "Database offline"

    try:
        doc_ref = (
            db.collection("users")
            .document(str(user_id))
            .collection("despesas_fixas")
            .document(despesa_id)
        )
        doc = doc_ref.get()
        if doc.exists:
            ativa_atual = doc.to_dict().get("ativa", True)
            doc_ref.update({"ativa": not ativa_atual})
            return True, "Despesa fixa atualizada!"
        return False, "Despesa fixa não encontrada"
    except Exception as e:
        print(f"Erro ao alternar despesa fixa: {e}")
        return False, str(e)


def excluir_despesa_fixa(user_id, despesa_id):
    """Remove uma despesa fixa."""
    if not db:
        return False, "Database offline"

    try:
        doc_ref = (
            db.collection("users")
            .document(str(user_id))
            .collection("despesas_fixas")
            .document(despesa_id)
        )
        doc_ref.delete()
        return True, "Despesa fixa excluída com sucesso!"
    except Exception as e:
        print(f"Erro ao excluir despesa fixa: {e}")
        return False, str(e)


def obter_previsao_despesas(user_id, mes=None, ano=None):
    """Calcula a previsão de despesas do mês baseado nas despesas fixas."""
    if mes is None:
        mes = datetime.now().month
    if ano is None:
        ano = datetime.now().year

    despesas_fixas = obter_despesas_fixas(user_id, ativa=True)
    transacoes = obter_transacoes_usuario(user_id, mes, ano)

    # Despesas já registradas no mês
    despesas_registradas = [
        t for t in transacoes if t.get("tipo") == "despesa"
    ]
    total_registrado = sum(float(t.get("valor", 0)) for t in despesas_registradas)

    # Despesas fixas que ainda vão vencer no mês
    hoje = datetime.now()
    despesas_pendentes = []
    total_pendente = 0.0

    for df in despesas_fixas:
        dia = df.get("dia_vencimento", 1)
        # Verifica se a despesa fixa já foi paga neste mês
        ja_paga = False
        for t in despesas_registradas:
            if t.get("descricao", "").lower() == df.get("descricao", "").lower():
                try:
                    dt = datetime.strptime(t.get("data", ""), "%Y-%m-%d")
                    if dt.month == mes and dt.year == ano:
                        ja_paga = True
                        break
                except ValueError:
                    pass

        if not ja_paga:
            valor = float(df.get("valor", 0))
            despesas_pendentes.append({
                "id": df.get("id"),
                "descricao": df.get("descricao"),
                "valor": valor,
                "dia_vencimento": dia,
                "categoria": df.get("categoria", "Geral"),
            })
            total_pendente += valor

    total_previsao = total_registrado + total_pendente

    return {
        "mes": mes,
        "ano": ano,
        "total_registrado": round(total_registrado, 2),
        "total_pendente": round(total_pendente, 2),
        "total_previsao": round(total_previsao, 2),
        "despesas_pendentes": despesas_pendentes,
        "quantidade_fixas": len(despesas_fixas),
    }


def aplicar_despesas_fixas(user_id, mes=None, ano=None):
    """Aplica automaticamente as despesas fixas vencidas do mês como transações."""
    if mes is None:
        mes = datetime.now().month
    if ano is None:
        ano = datetime.now().year

    despesas_fixas = obter_despesas_fixas(user_id, ativa=True)
    transacoes = obter_transacoes_usuario(user_id, mes, ano)
    despesas_registradas = [
        t for t in transacoes if t.get("tipo") == "despesa"
    ]

    aplicadas = 0
    for df in despesas_fixas:
        dia = df.get("dia_vencimento", 1)
        # Verifica se já foi aplicada
        ja_aplicada = False
        for t in despesas_registradas:
            if t.get("descricao", "").lower() == df.get("descricao", "").lower():
                ja_aplicada = True
                break

        if not ja_aplicada:
            data_vencimento = f"{ano:04d}-{mes:02d}-{dia:02d}"
            salvar_transacao(
                user_id,
                "despesa",
                df.get("descricao", "Despesa Fixa"),
                df.get("valor", 0),
                df.get("categoria", "Geral"),
                data_vencimento,
            )
            aplicadas += 1

    return aplicadas


# ============================================
# RECEITAS FIXAS
# ============================================

def salvar_receita_fixa(user_id, descricao, valor, dia_recebimento, categoria="Salário", ativa=True, data_fim=None):
    """Salva uma receita fixa recorrente (ex: salário todo dia 5)."""
    if not db:
        return False, "Database offline"

    try:
        doc_ref = (
            db.collection("users")
            .document(str(user_id))
            .collection("receitas_fixas")
            .document()
        )

        receita_data = {
            "descricao": descricao,
            "valor": float(valor),
            "dia_recebimento": int(dia_recebimento),
            "categoria": categoria,
            "ativa": ativa,
            "data_fim": data_fim or "",  # Data opcional de término (YYYY-MM-DD) ou "" para indeterminada
            "criado_em": datetime.now(),
        }

        doc_ref.set(receita_data)
        return True, "Receita fixa salva com sucesso!"
    except Exception as e:
        print(f"Erro ao salvar receita fixa no Firebase: {e}")
        return False, str(e)


def obter_receitas_fixas(user_id, ativa=None):
    """Retorna todas as receitas fixas do usuário."""
    if not db:
        return []

    try:
        receitas_ref = (
            db.collection("users")
            .document(str(user_id))
            .collection("receitas_fixas")
            .stream()
        )

        receitas = []
        for doc in receitas_ref:
            data = doc.to_dict()
            data["id"] = doc.id
            if ativa is not None and data.get("ativa", True) != ativa:
                continue
            receitas.append(data)

        # Ordena por dia de recebimento
        receitas.sort(key=lambda x: x.get("dia_recebimento", 1))
        return receitas
    except Exception as e:
        print(f"Erro ao buscar receitas fixas no Firebase: {e}")
        return []


def atualizar_receita_fixa(user_id, receita_id, dados_atualizados):
    """Atualiza uma receita fixa existente."""
    if not db:
        return False, "Database offline"

    try:
        doc_ref = (
            db.collection("users")
            .document(str(user_id))
            .collection("receitas_fixas")
            .document(receita_id)
        )
        doc_ref.update(dados_atualizados)
        return True, "Receita fixa atualizada com sucesso!"
    except Exception as e:
        print(f"Erro ao atualizar receita fixa: {e}")
        return False, str(e)


def alternar_receita_fixa(user_id, receita_id):
    """Ativa/desativa uma receita fixa."""
    if not db:
        return False, "Database offline"

    try:
        doc_ref = (
            db.collection("users")
            .document(str(user_id))
            .collection("receitas_fixas")
            .document(receita_id)
        )
        doc = doc_ref.get()
        if doc.exists:
            ativa_atual = doc.to_dict().get("ativa", True)
            doc_ref.update({"ativa": not ativa_atual})
            return True, "Receita fixa atualizada!"
        return False, "Receita fixa não encontrada"
    except Exception as e:
        print(f"Erro ao alternar receita fixa: {e}")
        return False, str(e)


def excluir_receita_fixa(user_id, receita_id):
    """Remove uma receita fixa."""
    if not db:
        return False, "Database offline"

    try:
        doc_ref = (
            db.collection("users")
            .document(str(user_id))
            .collection("receitas_fixas")
            .document(receita_id)
        )
        doc_ref.delete()
        return True, "Receita fixa excluída com sucesso!"
    except Exception as e:
        print(f"Erro ao excluir receita fixa: {e}")
        return False, str(e)


def obter_previsao_receitas(user_id, mes=None, ano=None):
    """Calcula a previsão de receitas do mês baseado nas receitas fixas."""
    if mes is None:
        mes = datetime.now().month
    if ano is None:
        ano = datetime.now().year

    receitas_fixas = obter_receitas_fixas(user_id, ativa=True)
    transacoes = obter_transacoes_usuario(user_id, mes, ano)

    # Receitas já registradas no mês
    receitas_registradas = [
        t for t in transacoes if t.get("tipo") == "receita"
    ]
    total_registrado = sum(float(t.get("valor", 0)) for t in receitas_registradas)

    # Receitas fixas que ainda vão ser recebidas no mês
    receitas_pendentes = []
    total_pendente = 0.0

    for rf in receitas_fixas:
        dia = rf.get("dia_recebimento", 1)
        # Verifica se a receita fixa já foi recebida neste mês
        ja_recebida = False
        for t in receitas_registradas:
            if t.get("descricao", "").lower() == rf.get("descricao", "").lower():
                try:
                    dt = datetime.strptime(t.get("data", ""), "%Y-%m-%d")
                    if dt.month == mes and dt.year == ano:
                        ja_recebida = True
                        break
                except ValueError:
                    pass

        if not ja_recebida:
            valor = float(rf.get("valor", 0))
            receitas_pendentes.append({
                "id": rf.get("id"),
                "descricao": rf.get("descricao"),
                "valor": valor,
                "dia_recebimento": dia,
                "categoria": rf.get("categoria", "Salário"),
            })
            total_pendente += valor

    total_previsao = total_registrado + total_pendente

    return {
        "mes": mes,
        "ano": ano,
        "total_registrado": round(total_registrado, 2),
        "total_pendente": round(total_pendente, 2),
        "total_previsao": round(total_previsao, 2),
        "receitas_pendentes": receitas_pendentes,
        "quantidade_fixas": len(receitas_fixas),
    }


def aplicar_receitas_fixas(user_id, mes=None, ano=None):
    """Aplica automaticamente as receitas fixas do mês como transações."""
    if mes is None:
        mes = datetime.now().month
    if ano is None:
        ano = datetime.now().year

    receitas_fixas = obter_receitas_fixas(user_id, ativa=True)
    transacoes = obter_transacoes_usuario(user_id, mes, ano)
    receitas_registradas = [
        t for t in transacoes if t.get("tipo") == "receita"
    ]

    aplicadas = 0
    for rf in receitas_fixas:
        dia = rf.get("dia_recebimento", 1)
        # Verifica se já foi aplicada
        ja_aplicada = False
        for t in receitas_registradas:
            if t.get("descricao", "").lower() == rf.get("descricao", "").lower():
                ja_aplicada = True
                break

        if not ja_aplicada:
            data_recebimento = f"{ano:04d}-{mes:02d}-{dia:02d}"
            salvar_transacao(
                user_id,
                "receita",
                rf.get("descricao", "Receita Fixa"),
                rf.get("valor", 0),
                rf.get("categoria", "Salário"),
                data_recebimento,
            )
            aplicadas += 1

    return aplicadas


# ============================================
# INVESTIMENTOS
# ============================================

def salvar_investimento(user_id, nome, tipo, valor_investido, corretora="",
                        taxa_anual=0.0, data_inicio=None, observacoes=""):
    """Salva um investimento (corretora, banco digital, etc)."""
    if not db:
        return False, "Database offline"

    try:
        doc_ref = (
            db.collection("users")
            .document(str(user_id))
            .collection("investimentos")
            .document()
        )

        if data_inicio is None:
            data_inicio = datetime.now().strftime("%Y-%m-%d")

        investimento_data = {
            "nome": nome,
            "tipo": tipo,  # "acao", "fii", "tesouro", "cdb", "poupanca", "cripto", "outro"
            "valor_investido": float(valor_investido),
            "corretora": corretora,
            "taxa_anual": float(taxa_anual),  # Taxa de rendimento anual estimada (%)
            "data_inicio": data_inicio,
            "observacoes": observacoes,
            "criado_em": datetime.now(),
        }

        doc_ref.set(investimento_data)
        return True, "Investimento salvo com sucesso!"
    except Exception as e:
        print(f"Erro ao salvar investimento no Firebase: {e}")
        return False, str(e)


def obter_investimentos(user_id):
    """Retorna todos os investimentos do usuário."""
    if not db:
        return []

    try:
        investimentos_ref = (
            db.collection("users")
            .document(str(user_id))
            .collection("investimentos")
            .stream()
        )

        investimentos = []
        for doc in investimentos_ref:
            data = doc.to_dict()
            data["id"] = doc.id
            investimentos.append(data)

        return investimentos
    except Exception as e:
        print(f"Erro ao buscar investimentos no Firebase: {e}")
        return []


def atualizar_investimento(user_id, investimento_id, dados_atualizados):
    """Atualiza um investimento existente."""
    if not db:
        return False, "Database offline"

    try:
        doc_ref = (
            db.collection("users")
            .document(str(user_id))
            .collection("investimentos")
            .document(investimento_id)
        )
        doc_ref.update(dados_atualizados)
        return True, "Investimento atualizado com sucesso!"
    except Exception as e:
        print(f"Erro ao atualizar investimento: {e}")
        return False, str(e)


def excluir_investimento(user_id, investimento_id):
    """Remove um investimento."""
    if not db:
        return False, "Database offline"

    try:
        doc_ref = (
            db.collection("users")
            .document(str(user_id))
            .collection("investimentos")
            .document(investimento_id)
        )
        doc_ref.delete()
        return True, "Investimento excluído com sucesso!"
    except Exception as e:
        print(f"Erro ao excluir investimento: {e}")
        return False, str(e)


def calcular_crescimento_investimento(user_id, investimento_id=None):
    """Calcula o crescimento estimado dos investimentos considerando taxas."""
    investimentos = obter_investimentos(user_id)
    if investimento_id:
        investimentos = [inv for inv in investimentos if inv.get("id") == investimento_id]

    resultados = []
    total_investido = 0.0
    total_projetado = 0.0

    hoje = datetime.now()

    for inv in investimentos:
        valor_investido = float(inv.get("valor_investido", 0))
        taxa_anual = float(inv.get("taxa_anual", 0)) / 100.0
        data_inicio_str = inv.get("data_inicio", "")

        # Calcula meses desde o início
        meses = 0
        if data_inicio_str:
            try:
                data_inicio = datetime.strptime(data_inicio_str, "%Y-%m-%d")
                meses = max(0, (hoje.year - data_inicio.year) * 12 + (hoje.month - data_inicio.month))
            except ValueError:
                pass

        # Crescimento composto mensal
        taxa_mensal = taxa_anual / 12.0 if taxa_anual > 0 else 0
        valor_atual_estimado = valor_investido * ((1 + taxa_mensal) ** meses) if meses > 0 else valor_investido
        crescimento = valor_atual_estimado - valor_investido

        # Projeção para 12 meses
        valor_projetado_12m = valor_investido * ((1 + taxa_mensal) ** 12) if taxa_mensal > 0 else valor_investido

        resultados.append({
            "id": inv.get("id"),
            "nome": inv.get("nome"),
            "tipo": inv.get("tipo"),
            "corretora": inv.get("corretora", ""),
            "valor_investido": round(valor_investido, 2),
            "taxa_anual": float(inv.get("taxa_anual", 0)),
            "meses_desde_inicio": meses,
            "valor_atual_estimado": round(valor_atual_estimado, 2),
            "crescimento": round(crescimento, 2),
            "crescimento_percentual": round((crescimento / valor_investido * 100), 2) if valor_investido > 0 else 0,
            "valor_projetado_12m": round(valor_projetado_12m, 2),
        })

        total_investido += valor_investido
        total_projetado += valor_atual_estimado

    return {
        "investimentos": resultados,
        "total_investido": round(total_investido, 2),
        "total_atual_estimado": round(total_projetado, 2),
        "total_crescimento": round(total_projetado - total_investido, 2),
        "total_crescimento_percentual": round((total_projetado - total_investido) / total_investido * 100, 2) if total_investido > 0 else 0,
    }


# ============================================
# DIVIDENDOS
# ============================================

def salvar_dividendo(user_id, investimento_id, descricao, valor_estimado,
                     frequencia="mensal", dia_recebimento=1, proximo_pagamento=None):
    """Salva um dividendo programado de um investimento."""
    if not db:
        return False, "Database offline"

    try:
        doc_ref = (
            db.collection("users")
            .document(str(user_id))
            .collection("dividendos")
            .document()
        )

        if proximo_pagamento is None:
            hoje = datetime.now()
            proximo_pagamento = f"{hoje.year:04d}-{hoje.month:02d}-{dia_recebimento:02d}"

        dividendo_data = {
            "investimento_id": investimento_id,
            "descricao": descricao,
            "valor_estimado": float(valor_estimado),
            "frequencia": frequencia,  # "mensal", "trimestral", "semestral", "anual"
            "dia_recebimento": int(dia_recebimento),
            "proximo_pagamento": proximo_pagamento,
            "criado_em": datetime.now(),
        }

        doc_ref.set(dividendo_data)
        return True, "Dividendo salvo com sucesso!"
    except Exception as e:
        print(f"Erro ao salvar dividendo no Firebase: {e}")
        return False, str(e)


def obter_dividendos(user_id):
    """Retorna todos os dividendos programados do usuário."""
    if not db:
        return []

    try:
        dividendos_ref = (
            db.collection("users")
            .document(str(user_id))
            .collection("dividendos")
            .stream()
        )

        dividendos = []
        investimentos = obter_investimentos(user_id)
        investimentos_map = {inv.get("id"): inv.get("nome", "Investimento") for inv in investimentos}

        for doc in dividendos_ref:
            data = doc.to_dict()
            data["id"] = doc.id
            data["investimento_nome"] = investimentos_map.get(
                data.get("investimento_id"), "Investimento"
            )
            dividendos.append(data)

        # Ordena por próximo pagamento
        dividendos.sort(key=lambda x: x.get("proximo_pagamento", ""))
        return dividendos
    except Exception as e:
        print(f"Erro ao buscar dividendos no Firebase: {e}")
        return []


def atualizar_dividendo(user_id, dividendo_id, dados_atualizados):
    """Atualiza um dividendo programado existente."""
    if not db:
        return False, "Database offline"

    try:
        doc_ref = (
            db.collection("users")
            .document(str(user_id))
            .collection("dividendos")
            .document(dividendo_id)
        )
        doc_ref.update(dados_atualizados)
        return True, "Dividendo atualizado com sucesso!"
    except Exception as e:
        print(f"Erro ao atualizar dividendo: {e}")
        return False, str(e)


def excluir_dividendo(user_id, dividendo_id):
    """Remove um dividendo programado."""
    if not db:
        return False, "Database offline"

    try:
        doc_ref = (
            db.collection("users")
            .document(str(user_id))
            .collection("dividendos")
            .document(dividendo_id)
        )
        doc_ref.delete()
        return True, "Dividendo excluído com sucesso!"
    except Exception as e:
        print(f"Erro ao excluir dividendo: {e}")
        return False, str(e)


def aplicar_dividendos_como_receita(user_id, mes=None, ano=None):
    """Contabiliza automaticamente os dividendos do mês como receitas."""
    if mes is None:
        mes = datetime.now().month
    if ano is None:
        ano = datetime.now().year

    dividendos = obter_dividendos(user_id)
    transacoes = obter_transacoes_usuario(user_id, mes, ano)
    receitas_registradas = [
        t for t in transacoes if t.get("tipo") == "receita"
    ]

    aplicados = 0
    for div in dividendos:
        valor = float(div.get("valor_estimado", 0))
        dia = int(div.get("dia_recebimento", 1))
        frequencia = div.get("frequencia", "mensal")
        descricao = div.get("descricao", "Dividendos")

        # Verifica se o dividendo cai neste mês
        recebe = False
        if frequencia == "mensal":
            recebe = True
        elif frequencia == "trimestral":
            recebe = (mes - 1) % 3 == 0
        elif frequencia == "semestral":
            recebe = (mes - 1) % 6 == 0
        elif frequencia == "anual":
            recebe = mes == 1

        if not recebe:
            continue

        # Verifica se já foi contabilizado
        ja_aplicado = False
        for t in receitas_registradas:
            if t.get("descricao", "").lower() == descricao.lower():
                ja_aplicado = True
                break

        if not ja_aplicado:
            data_recebimento = f"{ano:04d}-{mes:02d}-{dia:02d}"
            salvar_transacao(
                user_id,
                "receita",
                descricao,
                valor,
                "Dividendos",
                data_recebimento,
            )
            aplicados += 1

    return aplicados


def calcular_projecao_dividendos(user_id, meses=12):
    """Projeta os dividendos esperados para os próximos meses."""
    dividendos = obter_dividendos(user_id)
    hoje = datetime.now()

    projecao = []
    total_anual = 0.0

    for i in range(meses):
        data_projecao = hoje.replace(day=1) + timedelta(days=32 * i)
        mes_projecao = data_projecao.month
        ano_projecao = data_projecao.year
        total_mes = 0.0
        dividendos_mes = []

        for div in dividendos:
            valor = float(div.get("valor_estimado", 0))
            dia = int(div.get("dia_recebimento", 1))
            frequencia = div.get("frequencia", "mensal")

            # Verifica se o dividendo cai neste mês
            recebe = False
            if frequencia == "mensal":
                recebe = True
            elif frequencia == "trimestral":
                recebe = (mes_projecao - 1) % 3 == 0
            elif frequencia == "semestral":
                recebe = (mes_projecao - 1) % 6 == 0
            elif frequencia == "anual":
                recebe = mes_projecao == 1  # Janeiro

            if recebe:
                total_mes += valor
                dividendos_mes.append({
                    "descricao": div.get("descricao"),
                    "investimento": div.get("investimento_nome"),
                    "valor": valor,
                    "dia": dia,
                })

        projecao.append({
            "mes": mes_projecao,
            "ano": ano_projecao,
            "total": round(total_mes, 2),
            "dividendos": dividendos_mes,
        })
        total_anual += total_mes

    return {
        "projecao": projecao,
        "total_anual_estimado": round(total_anual, 2),
        "media_mensal": round(total_anual / meses, 2) if meses > 0 else 0,
    }


# ============================================
# INTEGRAÇÃO B3
# ============================================

def buscar_cotacao_b3(ticker):
    """Busca a cotação atual de um ativo da B3 usando a API pública da B3."""
    import requests as req

    ticker = ticker.upper().replace(".SA", "")

    # 1. Tenta API oficial da B3 (cotacao.b3.com.br/mds)
    try:
        url = f"https://cotacao.b3.com.br/mds/api/v1/DailyFluctuationHistory/{ticker}"
        response = req.get(url, timeout=10, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
        })

        if response.status_code == 200:
            data = response.json()
            if data.get("BizSts", {}).get("cd") == "OK":
                scty = data.get("TradgFlr", {}).get("scty", {})
                lst_qtn = scty.get("lstQtn", [])

                if lst_qtn:
                    # Última cotação do dia
                    ultima = lst_qtn[-1]
                    preco_atual = float(ultima.get("closPric", 0) or 0)
                    variacao = float(ultima.get("prcFlcn", 0) or 0)  # Já vem em percentual

                    # Busca a primeira cotação do dia para referência
                    primeira = lst_qtn[0]
                    preco_abertura = float(primeira.get("closPric", 0) or 0)

                    if preco_atual > 0:
                        return {
                            "ticker": ticker,
                            "preco_atual": round(preco_atual, 2),
                            "variacao_percentual": round(variacao, 2),
                            "preco_abertura": round(preco_abertura, 2),
                            "ultimo_dividendo": 0,
                            "dividend_yield": 0,
                            "fonte": "B3",
                        }, None
    except Exception as e:
        print(f"Erro na API B3: {e}")

    # 2. Fallback: API brapi.dev (gratuita, sem rate limit agressivo)
    try:
        url = f"https://brapi.dev/api/quote/{ticker}?token="
        response = req.get(url, timeout=10, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        })

        if response.status_code == 200:
            data = response.json()
            if data.get("results") and len(data["results"]) > 0:
                ativo = data["results"][0]
                preco_atual = float(ativo.get("regularMarketPrice", 0) or 0)
                variacao = float(ativo.get("regularMarketChangePercent", 0) or 0)
                preco_abertura = float(ativo.get("regularMarketOpen", 0) or 0)
                ultimo_dividendo = float(ativo.get("dividendsYield", 0) or 0)

                if preco_atual > 0:
                    return {
                        "ticker": ticker,
                        "preco_atual": round(preco_atual, 2),
                        "variacao_percentual": round(variacao, 2),
                        "preco_abertura": round(preco_abertura, 2),
                        "ultimo_dividendo": round(ultimo_dividendo, 2),
                        "dividend_yield": round(ultimo_dividendo, 2),
                        "fonte": "Brapi",
                    }, None
    except Exception as e:
        print(f"Erro na API Brapi: {e}")

    # 3. Fallback: Yahoo Finance (último recurso)
    try:
        import yfinance as yf

        ativo = yf.Ticker(f"{ticker}.SA")
        hist = ativo.history(period="5d")

        if not hist.empty:
            preco_atual = float(hist["Close"].iloc[-1])
            preco_anterior = float(hist["Close"].iloc[-2]) if len(hist) > 1 else preco_atual
            variacao = ((preco_atual - preco_anterior) / preco_anterior * 100) if preco_anterior > 0 else 0

            dividendos = ativo.dividends
            ultimo_dividendo = float(dividendos.iloc[-1]) if not dividendos.empty else 0
            dividend_yield = (ultimo_dividendo / preco_atual * 100) if preco_atual > 0 else 0

            return {
                "ticker": ticker,
                "preco_atual": round(preco_atual, 2),
                "variacao_percentual": round(variacao, 2),
                "preco_abertura": round(preco_anterior, 2),
                "ultimo_dividendo": round(ultimo_dividendo, 2),
                "dividend_yield": round(dividend_yield, 2),
                "fonte": "Yahoo",
            }, None
    except ImportError:
        pass
    except Exception as e:
        print(f"Erro na API Yahoo: {e}")

    return None, f"Não foi possível buscar cotação de {ticker}. Verifique o ticker ou tente novamente."


def atualizar_cotacoes_investimentos(user_id):
    """Busca cotações automáticas para todos os investimentos do tipo ação/FII do usuário."""
    investimentos = obter_investimentos(user_id)
    resultados = []

    for inv in investimentos:
        tipo = inv.get("tipo", "")
        nome = inv.get("nome", "")

        # Só busca cotação para ações e FIIs (têm ticker na B3)
        if tipo not in ["acao", "fii"]:
            continue

        # Extrai ticker do nome (ex: "PETR4" ou "MXRF11")
        ticker = nome.strip().upper()
        if not ticker:
            continue

        cotacao, erro = buscar_cotacao_b3(ticker)
        if cotacao:
            resultados.append({
                "investimento_id": inv.get("id"),
                "nome": nome,
                "ticker": ticker,
                "preco_atual": cotacao["preco_atual"],
                "variacao_percentual": cotacao["variacao_percentual"],
                "fonte": cotacao["fonte"],
            })

    return resultados


def buscar_dividendos_b3(ticker, periodo="1y"):
    """Busca o histórico de dividendos de um ativo da B3."""
    import requests as req

    ticker = ticker.upper().replace(".SA", "")

    # Tenta brapi.dev primeiro (tem histórico de dividendos)
    try:
        url = f"https://brapi.dev/api/quote/{ticker}?token=&range=1y&interval=1d&fundamental=true"
        response = req.get(url, timeout=10, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        })

        if response.status_code == 200:
            data = response.json()
            if data.get("results") and len(data["results"]) > 0:
                ativo = data["results"][0]
                dividendos = ativo.get("dividendsData", [])
                if dividendos:
                    resultado = []
                    for div in dividendos:
                        resultado.append({
                            "data": div.get("paymentDate", ""),
                            "valor": round(float(div.get("value", 0)), 4),
                        })
                    return resultado, None
    except Exception as e:
        print(f"Erro na API Brapi dividendos: {e}")

    # Fallback: Yahoo Finance
    try:
        import yfinance as yf

        ativo = yf.Ticker(f"{ticker}.SA")
        dividendos = ativo.dividends

        if not dividendos.empty:
            data_corte = datetime.now() - timedelta(days=365 if periodo == "1y" else 730)
            dividendos_filtrados = dividendos[dividendos.index >= data_corte]

            resultado = []
            for data, valor in dividendos_filtrados.items():
                resultado.append({
                    "data": data.strftime("%Y-%m-%d"),
                    "valor": round(float(valor), 4),
                })
            return resultado, None
    except ImportError:
        pass
    except Exception as e:
        print(f"Erro na API Yahoo dividendos: {e}")

    return [], "Nenhum dividendo encontrado para este ativo"


# ============================================
# METAS FINANCEIRAS
# ============================================

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