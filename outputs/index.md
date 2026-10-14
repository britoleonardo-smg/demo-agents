# Saídas reais dos agentes

A mesma pergunta, nos quatro estágios. Saída copiada do terminal, sem edição — serve para mostrar direto do GitHub, sem depender de rodar nada ao vivo.

| Estágio | Saída | O ponto |
|---|---|---|
| 01 — ReAct à mão | [01_react_prompt.md](01_react_prompt.md) | O modelo responde em texto e o **nosso** código faz o parsing e chama a função. Uma ação por volta. |
| 02 — LangChain | [02_langchain.md](02_langchain.md) | Mesmo resultado sem loop escrito por nós — e **duas ferramentas chamadas na mesma volta**, que o estágio 01 não consegue fazer. |
| 03 — LangGraph | [03_langgraph.md](03_langgraph.md) | Igual ao 02 por fora; por dentro o fluxo virou um grafo explícito, inspecionável e extensível. |
| 04 — Google ADK | [google_adk.md](google_adk.md) | Declarativo puro, e a execução chega como stream de eventos. |

Todas rodaram com `openai/gpt-5-nano`. Os quatro chegaram ao mesmo número: Tóquio ≈ 7,65 vezes Curitiba.
