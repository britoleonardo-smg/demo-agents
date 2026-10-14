# /// script
# requires-python = ">=3.10"
# dependencies = ["fastmcp", "ddgs", "wikipedia", "numexpr"]
# ///
"""Expõe as três ferramentas dos agentes Python como um servidor MCP.

O corpo das ferramentas **não** está aqui: vem do `shared/tools.py`, o mesmo
arquivo que os estágios 01, 02 e 03 importam. Este módulo só embrulha cada
função num `@mcp.tool`, para que um agente do kagent consiga chamá-las.

O bloco `# /// script` no topo é PEP 723: declara as dependências dentro do
próprio arquivo, então `uv run server.py` instala e roda sem venv, sem
requirements e sem imagem customizada.

Local (para testar antes de ir para o cluster):
    uv run mcp-tools/server.py

No cluster: o `kubernetes/pesquisa-agent.yaml` monta este arquivo e o
`shared/tools.py` num ConfigMap em /code e roda o mesmo comando.
"""
import sys
from pathlib import Path

HERE = Path(__file__).parent
# Dois caminhos porque o tools.py mora em lugares diferentes nos dois cenários:
# ao lado deste arquivo quando vem do ConfigMap, em ../shared quando é o repo.
sys.path[:0] = [str(HERE), str(HERE.parent / "shared")]

import tools
from fastmcp import FastMCP

mcp = FastMCP("pesquisa-tools")


@mcp.tool
def web_search(query: str) -> str:
    """Busca na web pelo DuckDuckGo e devolve os três primeiros resultados."""
    return tools.web_search(query)


@mcp.tool
def wikipedia_lookup(topic: str) -> str:
    """Resumo da Wikipédia (em inglês) sobre um tópico."""
    return tools.wikipedia_lookup(topic)


@mcp.tool
def calculator(expression: str) -> str:
    """Avalia uma expressão matemática, como '1234567 / 89012'."""
    return tools.calculator(expression)


if __name__ == "__main__":
    mcp.run()
