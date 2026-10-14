import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition

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


QUERY = (
    "Qual a população de Tóquio segundo a Wikipedia, e quantas vezes ela é "
    "maior que a da minha cidade natal, Curitiba? "
    "Busque a de Curitiba se não souber."
)


def build_graph():
    tools = [search_tool, wiki_tool, calc_tool]
    llm_with_tools = llm.chat_model().bind_tools(tools)

    def agent_node(state: MessagesState):
        return {"messages": [llm_with_tools.invoke(state["messages"])]}

    builder = StateGraph(MessagesState)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", ToolNode(tools))
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", tools_condition)
    builder.add_edge("tools", "agent")
    return builder.compile()


# No nível do módulo para o `langgraph dev` (LangGraph Studio) encontrar o grafo; ver langgraph.json
graph = build_graph()


def show(messages):
    """Imprime o rastro completo da execução.

    Sem isto o estágio vira uma caixa preta: entra pergunta, sai resposta. O que
    a apresentação precisa mostrar é o meio — qual ferramenta o agente escolheu,
    com que argumento, e o que voltou.
    """
    for msg in messages:
        for call in getattr(msg, "tool_calls", None) or []:
            print(f"[tool call]   {call['name']}({call['args']})")
        if type(msg).__name__ == "ToolMessage":
            texto = str(msg.content).replace("\n", " ")
            corte = "..." if len(texto) > 300 else ""
            print(f"[tool result] {msg.name}: {texto[:300]}{corte}\n")
        elif msg.content and type(msg).__name__ != "HumanMessage":
            print(f"[resposta]    {msg.content}\n")


def main():
    print(f"MODEL: {llm.describe()}")
    print(f"USER: {QUERY}\n")
    result = graph.invoke({"messages": [("user", QUERY)]})
    show(result["messages"][:-1])
    print(f"FINAL: {result['messages'][-1].content}")


if __name__ == "__main__":
    main()
