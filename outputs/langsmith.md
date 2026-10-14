# LangSmith — a árvore de execução

Execuções reais de 2026-10-13, lidas da API do LangSmith (projeto `TestApp`).
É a mesma informação que a UI mostra, em texto, para caber no GitHub.

**Três coisas para apontar:**

1. **O estágio 02 aparece como `LangGraph`.** Não é erro: o `create_agent` do LangChain é
   construído sobre LangGraph. O estágio 03 só torna explícito o grafo que o 02 já usava
   escondido — e o LangSmith entrega essa informação de graça.
2. **O loop do grafo fica visível:** `agent` → `tools` → `agent` → `tools` → `agent`.
   Cada `agent` é uma ida ao modelo; cada `tools`, a execução das ferramentas que ele pediu.
3. **Os tokens crescem a cada volta** (1.173 → 1.674 → 2.220 → 2.569). É o histórico
   inteiro sendo reenviado a cada chamada: a conta de um agente não é linear no número de
   passos, é quadrática no tamanho do contexto.

## Estágio 02 — LangChain (`create_agent`)

Total **34.2s** e **6785 tokens**. Desses, 33.2s em chamadas ao LLM e 1.9s nas ferramentas.

```text
LangGraph              chain    34.20s   6785 tokens
  model                  chain     5.25s   1075 tokens
    ChatOpenAI             llm       5.24s   1075 tokens
  tools                  chain     0.97s
  tools                  chain     0.97s
    wiki_tool              tool      0.96s
    wiki_tool              tool      0.96s
  model                  chain     7.85s   1492 tokens
    ChatOpenAI             llm       7.84s   1492 tokens
  tools                  chain     0.01s
    calc_tool              tool      0.01s
  model                  chain     8.77s   1918 tokens
    ChatOpenAI             llm       8.76s   1918 tokens
  tools                  chain     0.01s
    calc_tool              tool      0.01s
  model                  chain    11.31s   2300 tokens
    ChatOpenAI             llm      11.31s   2300 tokens
```

## Estágio 03 — LangGraph (grafo explícito)

Total **41.7s** e **7636 tokens**. Desses, 32.1s em chamadas ao LLM e 12.4s nas ferramentas.

```text
LangGraph              chain    41.65s   7636 tokens
  agent                  chain     7.81s   1173 tokens
    ChatOpenAI             llm       7.81s   1173 tokens
    tools_condition        chain     0.00s
  tools                  chain     8.49s
    search_tool            tool      1.88s
    search_tool            tool      8.49s
  agent                  chain     6.57s   1674 tokens
    ChatOpenAI             llm       6.57s   1674 tokens
    tools_condition        chain     0.00s
  tools                  chain     1.03s
    wiki_tool              tool      0.99s
    wiki_tool              tool      1.02s
  agent                  chain     8.25s   2220 tokens
    ChatOpenAI             llm       8.24s   2220 tokens
    tools_condition        chain     0.00s
  tools                  chain     0.00s
    calc_tool              tool      0.00s
  agent                  chain     9.44s   2569 tokens
    ChatOpenAI             llm       9.44s   2569 tokens
    tools_condition        chain     0.00s
```
