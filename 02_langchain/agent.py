import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain.agents import create_agent
from langchain_core.tools import tool

from shared import llm
from shared.tools import web_search, wikipedia_lookup, calculator


@tool
def search_tool(query: str) -> str:
    """DuckDuckGo web search — returns top 3 snippets."""
    return web_search(query)


@tool
def wiki_tool(topic: str) -> str:
    """Wikipedia summary (English) of a topic."""
    return wikipedia_lookup(topic)


@tool
def calc_tool(expression: str) -> str:
    """Evaluate a math expression like '1234567 / 89012'."""
    return calculator(expression)


SYSTEM_PROMPT = (
    "You are a research assistant. Use tools to answer questions. "
    "Look up facts with wiki_tool or search_tool, then use calc_tool for math."
)

QUERY = (
    "Qual a população de Tóquio segundo a Wikipedia, e quantas vezes ela é "
    "maior que a da minha cidade natal, Curitiba? "
    "Busque a de Curitiba se não souber."
)


def main():
    tools = [search_tool, wiki_tool, calc_tool]
    agent = create_agent(model=llm.chat_model(), tools=tools, system_prompt=SYSTEM_PROMPT)

    print(f"MODEL: {llm.describe()}")
    print(f"USER: {QUERY}\n")
    result = agent.invoke({"messages": [("human", QUERY)]})
    final = result["messages"][-1].content
    print(f"\nFINAL: {final}")


if __name__ == "__main__":
    main()
