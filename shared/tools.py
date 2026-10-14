"""As três ferramentas do agente, implementadas uma única vez.

Todos os estágios importam deste arquivo — e o servidor MCP em `mcp-tools/`
embrulha estas mesmas funções para que o agente dentro do cluster use as
ferramentas idênticas às do laptop. O que muda entre os estágios é só **como o
agente decide chamá-las**; o corpo da ferramenta nunca muda.

Duas regras valem para qualquer ferramenta de agente, e estão aplicadas aqui:

1. **Erro vira texto, não exceção.** Toda função devolve `"Error: ..."` em vez
   de levantar. A exceção mataria o processo; a string volta ao modelo como
   observação, e ele tenta outro caminho.
2. **A resposta é curta.** Tudo que sai daqui entra no contexto da próxima
   chamada ao LLM e é pago em token — a cada volta do loop, não só uma vez.
"""
from ddgs import DDGS
import wikipedia
import numexpr

# A Wikipedia limita (HTTP 429) o User-Agent genérico da biblioteca, que é
# compartilhado por todos os seus usuários. Um nome próprio evita o bloqueio.
wikipedia.set_user_agent("testing-agents/1.0 (educational demo of AI agents)")


def web_search(query: str) -> str:
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
        if not results:
            return "Error: no results"
        return "\n".join(f"- {r['title']}: {r['body']}" for r in results)
    except Exception as e:
        return f"Error: {e}"


def wikipedia_lookup(topic: str) -> str:
    try:
        # auto_suggest=False: com True, "Curitiba" vira "critica" e a busca falha
        return wikipedia.summary(topic, sentences=3, auto_suggest=False)
    except wikipedia.PageError:
        return f"Error: no Wikipedia page titled {topic!r}. Try another title."
    except wikipedia.DisambiguationError as e:
        return f"Error: ambiguous topic. Options: {', '.join(e.options[:5])}"
    except ValueError:
        # Resposta não-JSON: a Wikipedia devolveu "too many requests" em texto puro
        return "Error: Wikipedia is rate limiting requests right now. Try web_search instead."
    except Exception as e:
        return f"Error: {e}"


def calculator(expression: str) -> str:
    try:
        result = numexpr.evaluate(expression).item()
        return str(result)
    except Exception as e:
        return f"Error: {e}"
