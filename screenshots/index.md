# Telas para a apresentação

Capturas reais, do cluster e das ferramentas rodando. Serve como plano B se a demo ao vivo não puder acontecer.

Para os quatro agentes em Python, a evidência é texto e está em [`../outputs/`](../outputs/) — o GitHub renderiza, não precisa de imagem.

## LangGraph Studio — estágio 03 (`langgraph dev`)

| Arquivo | O que mostra |
|---|---|
| [08-langgraph-studio-grafo-e-input.png](08-langgraph-studio-grafo-e-input.png) | O grafo explícito antes de rodar: `__start__ → agent`, e de `agent` as duas saídas, `tools` (que volta) e `__end__`. A pergunta da demo no painel de input. |
| [09-langgraph-studio-execucao.png](09-langgraph-studio-execucao.png) | A execução em andamento: o nó ativo aceso no grafo e os eventos aparecendo um a um à direita. |
| [10-langgraph-studio-resposta.png](10-langgraph-studio-resposta.png) | A resposta final, com os números de cada fonte e a conta feita na calculadora. |
| [11-langgraph-studio-tool-calls.png](11-langgraph-studio-tool-calls.png) | O nó `tools` aberto: as duas chamadas de `wiki_tool`, **inclusive a que falhou** (`ambiguous topic`) e a que trouxe Lisboa. O erro faz parte do loop. |
| [12-langgraph-studio-trace-waterfall.png](12-langgraph-studio-trace-waterfall.png) | A aba **Trace**: 86,09 s e 7.092 tokens / $0,0024 na volta inteira, com `agent` 25,24 s e 10,47 s contra 1,25 s das ferramentas. De novo, o tempo é espera do modelo. |

## Google ADK — a UI própria (`adk web google_adk`)

| Arquivo | O que mostra |
|---|---|
| [06-adk-web-eventos.png](06-adk-web-eventos.png) | A conversa como **stream de eventos**: as duas chamadas de `wiki_tool` na mesma volta, os resultados e a resposta. À esquerda, o grafo do agente com as três ferramentas. |
| [07-adk-web-traces.png](07-adk-web-traces.png) | A cascata de tempo: **21,25 s no total, 21,2 s esperando o LLM** e 1,9 s somando as duas buscas na Wikipédia. O argumento visual de onde o tempo de um agente vai. |
| [18-adk-web-sessao-nova.png](18-adk-web-sessao-nova.png) | O Dev UI recém-aberto (ADK 2.11.0, app `google_adk`), com a pergunta digitada e nada ainda no painel. O ponto de partida da demo ao vivo. |
| [19-adk-web-tool-calls-paralelas.png](19-adk-web-tool-calls-paralelas.png) | Três eventos e pronto: o modelo pede `wiki_tool("João Pessoa")` e `wiki_tool("São Paulo")` **na mesma volta**, e os dois resultados voltam juntos. À esquerda, o grafo do `research_assistant` com a ferramenta usada acesa. |
| [20-adk-web-fallback-para-search.png](20-adk-web-fallback-para-search.png) | A mesma pergunta quando a Wikipédia não entrega: 22 eventos, `wiki_tool` repetida, **fallback para `search_tool`** e só então a resposta. O caminho torto é o normal — vale mais que a execução limpa. |
| [21-adk-web-uso-de-tokens.png](21-adk-web-uso-de-tokens.png) | O painel de uso: 1.555 tokens no evento contra **35.531 na sessão**, com 16.896 vindos de cache e 8.128 de *thoughts*. O custo de um agente está nas voltas, não na pergunta. |
| [22-adk-web-request-ao-modelo.png](22-adk-web-request-ao-modelo.png) | O request cru: `model: "openai/gpt-5-nano"` (o ADK falando com a OpenAI via LiteLLM), o system instruction e as `function_declarations` montadas a partir das docstrings e dos type hints. É o estágio 04 provando o que promete. |

## kagent

| Arquivo | O que mostra |
|---|---|
| [01-kagent-ui-wizard.png](01-kagent-ui-wizard.png) | Primeira abertura da UI: o wizard de boas-vindas. |
| [02-lista-de-agentes.png](02-lista-de-agentes.png) | `Agents` com os nossos dois (`pesquisa-agent`, `sre-agent`) ao lado dos que vêm no perfil demo. |
| [03-pesquisa-agent-chat.png](03-pesquisa-agent-chat.png) | O agente da Parte 1 rodando no cluster: **3 tool calls**, `wikipedia_lookup` duas vezes e `calculator`, com as nossas ferramentas no painel da direita. |
| [04-sre-agent-aprovacao.png](04-sre-agent-aprovacao.png) | **O human-in-the-loop.** `k8s_scale` com *Approval required*, os argumentos (`replicas: 2`) e os botões Approve/Reject. O campo de mensagem fica travado em *Awaiting approval*. |
| [05-sre-agent-depois-da-aprovacao.png](05-sre-agent-depois-da-aprovacao.png) | Depois do Approve. O deployment foi mesmo para 2 réplicas no cluster. |

## Tracing no cluster — Grafana + Tempo

O mesmo `pesquisa_agent` do kagent, agora visto por fora: spans OpenTelemetry emitidos pelo kagent e lidos no Grafana.

| Arquivo | O que mostra |
|---|---|
| [13-tempo-trace-pesquisa-agent.png](13-tempo-trace-pesquisa-agent.png) | A lista de traces e a cascata de um deles: `pesquisa_agent POST /` em 2,6 s, **6 spans**, com `invoke_agent` por cima de dois `generate_content` e um `execute_tool`. |
| [14-tempo-span-llm-request.png](14-tempo-span-llm-request.png) | Dentro do span do LLM: o `llm_request` com o `functionCall` que o modelo devolveu — `calculator` com `expression: "123456 / 7"`. A decisão do agente, crua. |
| [15-tempo-span-system-instruction.png](15-tempo-span-system-instruction.png) | O mesmo atributo mais acima: o **system instruction inteiro** e as declarações das ferramentas que foram ao modelo. O prompt não é segredo para quem tem o trace. |
| [16-tempo-span-atributos-gen-ai.png](16-tempo-span-atributos-gen-ai.png) | Os atributos padronizados `gen_ai.*`: modelo, `finish_reason`, 346 tokens de entrada e 18 de saída — mais `kagent.app_name`. Observabilidade de LLM com a convenção do OpenTelemetry. |
| [17-tempo-span-execute-tool.png](17-tempo-span-execute-tool.png) | O span da ferramenta: `execute_tool calculator` em **4,57 ms**, com argumento e resultado. O contraste com os 1,19 s do modelo ao lado. |

## Falta

- A UI do LangSmith. A árvore de execução dos estágios 02 e 03 está em texto em [`../outputs/langsmith.md`](../outputs/langsmith.md); em imagem, o que existe é o LangGraph Studio acima, do estágio 03.
