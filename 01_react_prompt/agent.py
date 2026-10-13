import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared import llm
from shared.tools import web_search, wikipedia_lookup, calculator

TOOLS = {
    "web_search": web_search,
    "wikipedia_lookup": wikipedia_lookup,
    "calculator": calculator,
}

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
    transcript = f"{SYSTEM_PROMPT}\n\nUser: {QUERY}\n"
    print(f"MODEL: {llm.describe()}")
    print(f"USER: {QUERY}\n")

    for i in range(MAX_ITERATIONS):
        step = llm.complete(transcript).strip()
        print(f"--- iteration {i + 1} ---\n{step}\n")

        kind, payload = parse(step)
        if kind == "final":
            print(f"FINAL: {payload}")
            return
        if kind == "action":
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
