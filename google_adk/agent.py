"""Estágio 04 — o mesmo agente, declarativo, com o ADK do Google.

Delta em relação ao estágio 03:

1. **Sem grafo, sem decorador.** `Agent(name, model, instruction, tools)` e
   acabou. As ferramentas são funções Python comuns — a docstring vira a
   descrição e os type hints viram o schema, sem nenhuma anotação.
2. **Runtime incluído.** `Runner` e `SessionService` trazem sessão e histórico
   prontos, em vez de você montar.
3. **Streaming por evento.** A execução chega como um fluxo assíncrono, não como
   um resultado no fim. É o que a UI do `adk web` consome para desenhar a
   conversa e a cascata de tempo.

A troca: menos código que todos os anteriores, e menos controle sobre o loop.
Se você precisa intervir no meio do raciocínio, o grafo do estágio 03 é o lugar.
"""
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from shared import llm
from shared.tools import web_search, wikipedia_lookup, calculator


# Nenhum decorador: função Python pura. O ADK inspeciona a assinatura e a
# docstring para montar o schema que vai ao modelo. É o mesmo princípio do
# estágio 02 — a docstring é a interface com o modelo — com menos cerimônia.
def search_tool(query: str) -> str:
    """DuckDuckGo web search. Returns top 3 result snippets as text."""
    return web_search(query)


def wiki_tool(topic: str) -> str:
    """Wikipedia summary (English) of a topic. Returns a short paragraph."""
    return wikipedia_lookup(topic)


def calc_tool(expression: str) -> str:
    """Evaluate a math expression, e.g. '1234567 / 89012'. Returns the numeric result."""
    return calculator(expression)


# A declaração inteira do agente. Compare com o `build_graph()` do estágio 03:
# o mesmo comportamento, sem descrever o fluxo — aqui você diz o que o agente é,
# não como ele roda.
agent = Agent(
    name="research_assistant",
    model=llm.adk_model(),
    instruction="You are a research assistant. Use the tools to answer the user's question, then respond in the user's language.",
    tools=[search_tool, wiki_tool, calc_tool],
)

# O `adk web` (a UI de desenvolvimento do ADK) procura por `root_agent` dentro de
# um pacote Python. O alias deixa o mesmo arquivo servir para os dois caminhos:
# `python 04_google_adk/agent.py` no terminal e `adk web` no navegador.
root_agent = agent

QUERY = (
    "Qual a população de Tóquio segundo a Wikipedia, e quantas vezes ela é "
    "maior que a da minha cidade natal, Curitiba? "
    "Busque a de Curitiba se não souber."
)


async def run():
    # O runtime que o ADK traz pronto. `SessionService` guarda o histórico (aqui
    # em memória; em produção seria um banco) e o `Runner` conduz a execução.
    # Nos estágios anteriores isso era uma lista de mensagens na mão.
    session_service = InMemorySessionService()
    app_name = "research_app"
    user_id = "user"
    session = await session_service.create_session(app_name=app_name, user_id=user_id)
    runner = Runner(agent=agent, app_name=app_name, session_service=session_service)

    print(f"MODEL: {llm.describe()}")
    print(f"USER: {QUERY}\n")
    content = types.Content(role="user", parts=[types.Part(text=QUERY)])
    last_text = ""
    # A execução chega como stream de eventos, não como um resultado no fim:
    # cada pensamento, cada chamada de ferramenta e cada resposta é um evento
    # assim que acontece. É o que permite mostrar o agente trabalhando ao vivo.
    async for event in runner.run_async(user_id=user_id, session_id=session.id, new_message=content):
        print(f"--- {event.author} ---")
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(part.text)
                    last_text = part.text
                if part.function_call:
                    print(f"[tool call] {part.function_call.name}({dict(part.function_call.args)})")
                if part.function_response:
                    print(f"[tool result] {part.function_response.response}")
    print(f"\nFINAL: {last_text}")


if __name__ == "__main__":
    asyncio.run(run())
