"""Estágio 02 — o mesmo agente, com o loop por conta do LangChain.

Delta em relação ao estágio 01:

1. **O loop sumiu.** O `create_agent` faz pensa-age-observa por você. O que era
   um `for` com parser vira uma chamada.
2. **Tool calling nativo.** Não há mais contrato de texto nem regex: o modelo
   devolve a chamada estruturada e a biblioteca executa. Some a classe inteira
   de bug "o modelo saiu do formato".
3. **Mais de uma ferramenta por volta.** Consequência do item anterior, e dá
   para ver na saída: `wiki_tool(Tokyo)` e `wiki_tool(Curitiba)` juntas.

O que se perde: visibilidade. O loop virou caixa preta — daí o `show()` lá
embaixo, e daí a utilidade do LangSmith neste estágio.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain.agents import create_agent
from langchain_core.tools import tool

from shared import llm
from shared.tools import web_search, wikipedia_lookup, calculator


# O decorador transforma a função numa ferramenta que o modelo enxerga. Repare
# de onde vem a descrição: **a docstring**. É ela que o modelo lê para decidir
# quando usar esta ferramenta, e o type hint vira o schema do argumento. Docstring
# ruim aqui é ferramenta mal usada lá.
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
    tools = [search_tool, wiki_tool, calc_tool]
    # Uma linha no lugar do loop inteiro do estágio 01. O `create_agent` monta o
    # ciclo, executa as ferramentas e decide quando parar.
    agent = create_agent(model=llm.chat_model(), tools=tools, system_prompt=SYSTEM_PROMPT)

    print(f"MODEL: {llm.describe()}")
    print(f"USER: {QUERY}\n")
    # O estado de um agente LangChain é uma lista de mensagens: a pergunta, as
    # chamadas de ferramenta, os resultados e a resposta. O `transcript` em texto
    # do estágio 01 virou estrutura.
    result = agent.invoke({"messages": [("human", QUERY)]})
    show(result["messages"][:-1])
    print(f"FINAL: {result['messages'][-1].content}")


if __name__ == "__main__":
    main()
