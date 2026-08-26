import os
from google import genai
from google.genai import types

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Inicializa o cliente se a chave estiver configurada
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

SYSTEM_INSTRUCTION = """
Você é o Assistente Pessoal do Thiago. 
Responda de forma direta, clara, concisa e prestativa. 
Use formatação Markdown simples (negrito, tópicos) quando necessário.
"""

def responder_duvida(pergunta_usuario):
    """Envia a pergunta do usuário para o Gemini 2.5 Flash e retorna a resposta."""
    if not client:
        return "⚠️ A chave `GEMINI_API_KEY` não foi configurada no ambiente."

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=pergunta_usuario,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.7,
                max_output_tokens=1000,
            ),
        )
        return response.text if response.text else "Não consegui gerar uma resposta no momento."
    except Exception as e:
        print(f"Erro ao consultar o Gemini: {e}")
        return f"❌ Ocorreu um erro ao consultar a IA: {e}"