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

**Por que este estágio é async e os outros não.** Não é preferência de estilo,
são três fatos da API:

- `runner.run_async()` é um *async generator*: ele entrega evento por evento
  conforme acontecem. Consumir isso exige `async for`, que só existe dentro de
  uma função `async`.
- `session_service.create_session()` é coroutine — já obriga um `await`.
- O ADK existe para rodar dentro de um servidor (é o que o `adk web` é), onde
  já há um event loop. A interface assíncrona é a principal; o `Runner.run()`
  síncrono existe, mas a própria docstring dele avisa que é "only for local
  testing and convenience purpose".

A razão de fundo: nos estágios 02 e 03 o modelo mental é requisição-resposta —
`invoke()` entra, resultado sai, e o meio do caminho você só vê depois, no
LangSmith. Aqui o meio do caminho **é** a interface. Quem fala com o agente é um
consumidor de stream, e stream em Python é asyncio.

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


# Repare que as três ferramentas são síncronas, e isso é permitido: o ADK aceita
# função comum ou coroutine. Quem precisa ser async é o runtime, não a tool.
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
# um pacote Python — daí o `from . import agent` no `__init__.py` deste diretório.
# O alias deixa o mesmo arquivo servir para os dois caminhos:
# `python google_adk/agent.py` no terminal e `adk web` no navegador.
root_agent = agent

QUERY = (
    "Qual a população de Tóquio segundo a Wikipedia, e quantas vezes ela é "
    "maior que a da minha cidade natal, Curitiba? "
    "Busque a de Curitiba se não souber."
)


# `async def` porque o corpo tem um `await` e um `async for` (ver o docstring do
# módulo). Toda função que chama algo assíncrono vira assíncrona também — é a
# propriedade que faz o async "subir" pela pilha até o `asyncio.run()` no fim.
async def run():
    # O runtime que o ADK traz pronto. `SessionService` guarda o histórico (aqui
    # em memória; em produção seria um banco) e o `Runner` conduz a execução.
    # Nos estágios anteriores isso era uma lista de mensagens na mão.
    session_service = InMemorySessionService()
    app_name = "research_app"
    user_id = "user"
    # `create_session` é coroutine mesmo na implementação em memória: a interface
    # é a mesma de um backend com I/O de verdade, e é isso que permite trocar
    # este `InMemorySessionService` por um banco sem mudar o resto do código.
    session = await session_service.create_session(app_name=app_name, user_id=user_id)
    # O `Runner` amarra as três peças: quem pensa (agent), onde guarda (session_service)
    # e sob que aplicação (app_name, que a UI usa para separar os agentes).
    runner = Runner(agent=agent, app_name=app_name, session_service=session_service)

    print(f"MODEL: {llm.describe()}")
    print(f"USER: {QUERY}\n")
    # A mensagem não é string: o ADK usa o tipo `Content` do google-genai, com
    # papel e lista de partes. É o mesmo formato que a API do Gemini espera, e é
    # por isso que texto, imagem e áudio cabem no mesmo caminho.
    content = types.Content(role="user", parts=[types.Part(text=QUERY)])
    # Guarda o último texto visto para imprimir no fim. Precisamos disto porque
    # no stream não existe "a resposta": existe o último evento que trouxe texto.
    last_text = ""
    # A execução chega como stream de eventos, não como um resultado no fim:
    # cada pensamento, cada chamada de ferramenta e cada resposta é um evento
    # assim que acontece. É o que permite mostrar o agente trabalhando ao vivo.
    #
    # `async for` é a razão de tudo isto ser async: a cada volta o loop devolve o
    # controle ao event loop enquanto espera o próximo evento chegar da rede, em
    # vez de bloquear a thread. Num servidor, é o que deixa outras sessões
    # avançarem durante a espera.
    async for event in runner.run_async(user_id=user_id, session_id=session.id, new_message=content):
        # `author` diz quem produziu o evento — o usuário, o agente, ou uma
        # ferramenta. Num sistema multi-agente é aqui que se vê quem falou.
        print(f"--- {event.author} ---")
        if event.content and event.content.parts:
            # Um evento pode trazer várias partes, e cada parte é de um tipo:
            # texto, pedido de ferramenta ou resultado de ferramenta. Este
            # if/if/if é o equivalente ao `show()` do estágio 03 — a diferença é
            # que lá percorríamos o histórico depois, e aqui vemos ao vivo.
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
    # A fronteira entre o mundo síncrono (o script) e o assíncrono (o ADK):
    # `asyncio.run` cria o event loop, executa a coroutine até o fim e fecha o
    # loop. Dentro do `adk web` esta linha não existe — o servidor já tem o seu.
    asyncio.run(run())
