# Estágio 03 — LangGraph

Execução real de 2026-10-13, com `openai/gpt-5-nano`. Saída copiada do terminal, sem edição.

**O que observar:** Mesmo tool calling nativo do estágio 02, mas agora o fluxo é um **grafo explícito**: nó `agent`, nó `tools` e uma aresta condicional que decide se volta para o modelo ou encerra. O resultado é igual; o que muda é que o caminho virou estrutura, e dá para inspecionar e estender.

```text
MODEL: openai/gpt-5-nano
USER: Qual a população de Tóquio segundo a Wikipedia, e quantas vezes ela é maior que a da minha cidade natal, Curitiba? Busque a de Curitiba se não souber.

[tool call]   wiki_tool({'topic': 'Tokyo'})
[tool call]   wiki_tool({'topic': 'Curitiba'})
[tool result] wiki_tool: Tokyo, officially the Tokyo Metropolis, is the capital and most populous city of Japan. The population of the city proper was over 14 million as of 2023. The Greater Tokyo Area, which includes Tokyo and parts of six neighboring prefectures, is the third-most populous metropolitan area in the world, ...

[tool result] wiki_tool: Curitiba ( KOOR-ih-CHEE-bə; Brazilian Portuguese: [kuɾiˈtʃibɐ]) is the capital and largest city in the state of Paraná in Southern Brazil. The city's population was 1,829,225 as of 2024, making it the eighth most populous city in Brazil and the largest in Brazil's South Region. The Curitiba metropol...

[tool call]   calc_tool({'expression': '14000000 / 1829225'})
[tool result] calc_tool: 7.653514466509041

FINAL: Resumo direto:

- Tóquio (cidade própria): mais de 14 milhões de habitantes (dados da Wikipedia, 2023).
- Curitiba: 1.829.225 habitantes (dados da Wikipedia, 2024).

Comparação:
- 14.000.000 ÷ 1.829.225 ≈ 7,65
- Logo, a população de Tóquio é aproximadamente 7,6 vezes maior que a de Curitiba (considerando a população da cidade, não da área metropolitana).

Observação adicional:
- Se considerar a área metropolitana de Tóquio, a população é em torno de 33 milhões, o que daria cerca de 18 vezes a população de Curitiba.
```
