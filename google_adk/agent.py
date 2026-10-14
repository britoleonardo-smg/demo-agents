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


def search_tool(query: str) -> str:
    """DuckDuckGo web search. Returns top 3 result snippets as text."""
    return web_search(query)


def wiki_tool(topic: str) -> str:
    """Wikipedia summary (English) of a topic. Returns a short paragraph."""
    return wikipedia_lookup(topic)


def calc_tool(expression: str) -> str:
    """Evaluate a math expression, e.g. '1234567 / 89012'. Returns the numeric result."""
    return calculator(expression)


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
    session_service = InMemorySessionService()
    app_name = "research_app"
    user_id = "user"
    session = await session_service.create_session(app_name=app_name, user_id=user_id)
    runner = Runner(agent=agent, app_name=app_name, session_service=session_service)

    print(f"MODEL: {llm.describe()}")
    print(f"USER: {QUERY}\n")
    content = types.Content(role="user", parts=[types.Part(text=QUERY)])
    last_text = ""
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
