"""Estágio 01 — o loop ReAct escrito à mão.

Nenhum framework. O que existe aqui é o que existe em qualquer agente, sem
açúcar: um prompt que define um contrato de formato, uma chamada ao modelo, um
parser que lê a resposta e um dicionário que despacha para a função certa.

O ponto deste estágio na apresentação: **"agente" não é uma tecnologia, é um
padrão de uso do modelo.** O modelo não executa nada — ele escreve texto dizendo
o que quer que seja executado, e o nosso código obedece.

A fragilidade também é o ponto: o contrato é texto livre, então o parser é regex
e o modelo pode sair do formato. Os estágios seguintes resolvem isso trocando
texto por tool calling nativo.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared import llm
from shared.tools import web_search, wikipedia_lookup, calculator

# A "tabela de despacho": o modelo escreve o nome da ferramenta como texto e é
# este dicionário que transforma esse texto numa chamada de função Python.
# É literalmente tudo que separa "o modelo falou" de "a ação aconteceu".
TOOLS = {
    "web_search": web_search,
    "wikipedia_lookup": wikipedia_lookup,
    "calculator": calculator,
}

# O contrato com o modelo. Como não existe tool calling aqui, as ferramentas são
# descritas em prosa e o formato da resposta é combinado por escrito. Tudo que o
# parser entende precisa estar explicado aqui — prompt e parser são duas metades
# da mesma coisa, e mexer em um sem o outro quebra o agente.
SYSTEM_PROMPT = """You are a research assistant that uses tools in a strict ReAct loop.

Available tools:
- web_search(query): DuckDuckGo web search, returns top 3 snippets.
- wikipedia_lookup(topic): Wikipedia summary (English) of a topic.
- calculator(expression): evaluate a math expression like "1234567 / 89012".

On every turn respond in ONE of two formats — nothing else.

Format A (use a tool):
Thought: <your reasoning>
Action: <tool_name>
Action Input: <single argument>

Format B (final answer):
Thought: <reasoning>
Final Answer: <answer to the user>

Rules:
- Never do arithmetic yourself, always use the calculator tool.
- Exactly one Action per turn. Wait for the Observation before deciding the next step.
- Never invent Observations. Never call a tool not in the list.
- Final Answer must contain the complete answer, with the actual numbers in it.
  Never announce a next step there ("I will now calculate...", "waiting for the
  result"): if work is still missing, use Format A instead.
- When you have enough info, produce Final Answer.
"""

QUERY = (
    "Qual a população de Tóquio segundo a Wikipedia, e quantas vezes ela é "
    "maior que a da minha cidade natal, Curitiba? "
    "Busque a de Curitiba se não souber."
)

# 8 e não 6: o loop é feito à mão e o modelo às vezes gasta uma rodada
# devolvendo algo fora do formato. A folga evita terminar sem Final Answer.
MAX_ITERATIONS = 8


def parse(text: str):
    """Lê a resposta do modelo e decide o que fazer: agir, encerrar ou reclamar.

    Esta função é a parte frágil do estágio — e é de propósito. Interpretar texto
    livre com regex é o que os frameworks eliminam ao usar tool calling nativo,
    em que o modelo devolve JSON estruturado em vez de prosa.
    """
    if "Final Answer:" in text:
        answer = text.split("Final Answer:", 1)[1].strip()
        # Final Answer vazio não é resposta: trata como saída fora do formato
        return ("final", answer) if answer else ("unknown", text)
    action_match = re.search(r"Action:\s*(\w+)", text)
    input_match = re.search(r"Action Input:\s*(.+?)(?:\n|$)", text, re.DOTALL)
    if action_match and input_match:
        return "action", (action_match.group(1).strip(), input_match.group(1).strip())
    return "unknown", text


def main():
    # O modelo não tem memória entre chamadas: cada requisição é independente.
    # Por isso o `transcript` acumula tudo — prompt, pergunta, o que o modelo
    # respondeu e cada observação — e é reenviado inteiro a cada volta. É daqui
    # que vem o crescimento de tokens que aparece no trace dos outros estágios.
    transcript = f"{SYSTEM_PROMPT}\n\nUser: {QUERY}\n"
    print(f"MODEL: {llm.describe()}")
    print(f"USER: {QUERY}\n")

    # O loop ReAct: pensa, age, observa — e repete com a observação no contexto.
    for i in range(MAX_ITERATIONS):
        step = llm.complete(transcript).strip()
        print(f"--- iteration {i + 1} ---\n{step}\n")

        kind, payload = parse(step)
        if kind == "final":
            print(f"FINAL: {payload}")
            return
        if kind == "action":
            # Uma ação por volta: é a regra do formato. Repare que os estágios 02
            # e 03 chamam duas ferramentas na mesma rodada — tool calling nativo
            # permite isso, um contrato de texto como este não.
            tool, arg = payload
            if tool not in TOOLS:
                observation = f"Error: unknown tool {tool}"
            else:
                observation = TOOLS[tool](arg)
            print(f"OBSERVATION: {observation}\n")
            transcript += f"{step}\nObservation: {observation}\n"
            continue
        # Saída fora do formato: em vez de desistir, devolve o erro ao modelo para ele se corrigir
        observation = (
            "Error: your last response did not follow Format A or Format B "
            "(or Final Answer was empty). Respond again using exactly one of the two formats."
        )
        print(f"OBSERVATION: {observation}\n")
        transcript += f"{step}\nObservation: {observation}\n"

    print(f"Hit max iterations ({MAX_ITERATIONS}) without Final Answer.")


if __name__ == "__main__":
    main()
