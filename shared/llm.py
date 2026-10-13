"""Escolha do provedor de LLM, num lugar só.

Configure no .env:
    LLM_PROVIDER=openai    # ou gemini
    LLM_MODEL=gpt-5-nano   # opcional; sem ele, usa o padrão do provedor

Cada estágio pede o modelo no formato que o seu framework espera:
    complete(prompt)  -> estágio 01 (chamada crua de texto)
    chat_model()      -> estágios 02 e 03 (LangChain / LangGraph)
"""
import os

from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODELS = {
    "gemini": "gemini-3.8-flash",
    "openai": "gpt-5-nano",
}
KEY_VARS = {
    "gemini": "GEMINI_API_KEY",
    "openai": "OPENAI_API_KEY",
}

PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()
if PROVIDER not in DEFAULT_MODELS:
    raise SystemExit(f"LLM_PROVIDER inválido: {PROVIDER!r}. Use: {', '.join(DEFAULT_MODELS)}")

MODEL = os.getenv("LLM_MODEL") or DEFAULT_MODELS[PROVIDER]

if not os.getenv(KEY_VARS[PROVIDER]):
    raise SystemExit(f"{KEY_VARS[PROVIDER]} missing — set it in .env (LLM_PROVIDER={PROVIDER})")


def describe() -> str:
    return f"{PROVIDER}/{MODEL}"


def complete(prompt: str) -> str:
    """Manda um texto e recebe um texto. Sem tool calling nativo: é o que o estágio 01 quer."""
    if PROVIDER == "openai":
        from openai import OpenAI

        client = OpenAI()
        response = client.chat.completions.create(
            model=MODEL, messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content or ""

    from google import genai

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    response = client.models.generate_content(model=MODEL, contents=prompt)
    return response.text or ""


def chat_model():
    """Modelo de chat do LangChain (serve para LangChain e LangGraph)."""
    if PROVIDER == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=MODEL)

    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(model=MODEL, google_api_key=os.getenv("GEMINI_API_KEY"))

