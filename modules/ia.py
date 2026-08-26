import os
from datetime import datetime
from google import genai
from google.genai import types

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# Limite diário gratuito do Gemini 2.5 Flash
LIMITE_DIARIO_GRATUITO = 250

uso_diario = {
    "data": datetime.now().strftime("%Y-%m-%d"),
    "requisicoes": 0
}


def _atualizar_contador():
    """Garante o reset do contador diário à meia-noite."""
    hoje = datetime.now().strftime("%Y-%m-%d")
    if uso_diario["data"] != hoje:
        uso_diario["data"] = hoje
        uso_diario["requisicoes"] = 0


def get_status_uso():
    """Gera barra visual de consumo do limite gratuito."""
    _atualizar_contador()
    usadas = uso_diario["requisicoes"]
    restantes = max(0, LIMITE_DIARIO_GRATUITO - usadas)
    porcentagem = min(100, int((usadas / LIMITE_DIARIO_GRATUITO) * 100))

    blocos_preenchidos = int(porcentagem / 10)
    barra = "▓" * blocos_preenchidos + "░" * (10 - blocos_preenchidos)

    return (
        f"📊 *Uso da IA Hoje ({uso_diario['data']})*\n"
        f"└ Usadas: `{usadas}/{LIMITE_DIARIO_GRATUITO}` ({porcentagem}%)\n"
        f"└ Restantes: `{restantes}`\n"
        f"└ Progresso: `[{barra}]`\n"
    )


def responder_duvida(pergunta_usuario):
    """Envia a pergunta para a IA usando o modelo atualizado gemini-2.5-flash."""
    if not client:
        return "⚠️ A chave `GEMINI_API_KEY` não foi configurada nas variáveis de ambiente."

    _atualizar_contador()

    if uso_diario["requisicoes"] >= LIMITE_DIARIO_GRATUITO:
        return (
            "🚨 *Limite diário atingido!*\n\n"
            f"Você atingiu o limite gratuito de **{LIMITE_DIARIO_GRATUITO} requisições/dia**.\n"
            "O contador será zerado à meia-noite."
        )

    try:
        # Modelo oficial recomendado pela API do Google
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=pergunta_usuario,
            config=types.GenerateContentConfig(
                system_instruction="Você é o Assistente Pessoal do Thiago. Responda de forma direta e concisa.",
                temperature=0.7,
                max_output_tokens=1000,
            ),
        )

        uso_diario["requisicoes"] += 1
        status = get_status_uso()

        texto_resposta = response.text if response.text else "Sem resposta gerada."
        return f"{texto_resposta}\n\n---\n{status}"

    except Exception as e:
        print(f"Erro ao consultar o Gemini: {e}")
        return f"❌ Ocorreu um erro ao consultar a IA: {e}"