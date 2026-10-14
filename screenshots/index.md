# Telas para a apresentação

Capturas reais, do cluster e das ferramentas rodando. Serve como plano B se a demo ao vivo não puder acontecer.

Para os quatro agentes em Python, a evidência é texto e está em [`../outputs/`](../outputs/) — o GitHub renderiza, não precisa de imagem.

## Google ADK — a UI própria (`adk web google_adk`)

| Arquivo | O que mostra |
|---|---|
| [06-adk-web-eventos.png](06-adk-web-eventos.png) | A conversa como **stream de eventos**: as duas chamadas de `wiki_tool` na mesma volta, os resultados e a resposta. À esquerda, o grafo do agente com as três ferramentas. |
| [07-adk-web-traces.png](07-adk-web-traces.png) | A cascata de tempo: **21,25 s no total, 21,2 s esperando o LLM** e 1,9 s somando as duas buscas na Wikipédia. O argumento visual de onde o tempo de um agente vai. |

## kagent

| Arquivo | O que mostra |
|---|---|
| [01-kagent-ui-wizard.png](01-kagent-ui-wizard.png) | Primeira abertura da UI: o wizard de boas-vindas. |
| [02-lista-de-agentes.png](02-lista-de-agentes.png) | `Agents` com os nossos dois (`pesquisa-agent`, `sre-agent`) ao lado dos que vêm no perfil demo. |
| [03-pesquisa-agent-chat.png](03-pesquisa-agent-chat.png) | O agente da Parte 1 rodando no cluster: **3 tool calls**, `wikipedia_lookup` duas vezes e `calculator`, com as nossas ferramentas no painel da direita. |
| [04-sre-agent-aprovacao.png](04-sre-agent-aprovacao.png) | **O human-in-the-loop.** `k8s_scale` com *Approval required*, os argumentos (`replicas: 2`) e os botões Approve/Reject. O campo de mensagem fica travado em *Awaiting approval*. |
| [05-sre-agent-depois-da-aprovacao.png](05-sre-agent-depois-da-aprovacao.png) | Depois do Approve. O deployment foi mesmo para 2 réplicas no cluster. |

## Falta

- LangSmith nos estágios 02 e 03 — depende de conta e API key.
