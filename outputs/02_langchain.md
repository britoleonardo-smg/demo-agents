# Estágio 02 — LangChain

Execução real de 2026-10-13, com `openai/gpt-5-nano`. Saída copiada do terminal, sem edição.

**O que observar:** O mesmo resultado, sem loop escrito por nós: o `create_agent` cuida disso. E aparece algo que o estágio 01 não consegue fazer: **duas chamadas de ferramenta na mesma volta** (`Tokyo` e `Curitiba` juntas), porque aqui é tool calling nativo do modelo, não parsing de texto.

```text
MODEL: openai/gpt-5-nano
USER: Qual a população de Tóquio segundo a Wikipedia, e quantas vezes ela é maior que a da minha cidade natal, Curitiba? Busque a de Curitiba se não souber.

[tool call]   wiki_tool({'topic': 'Tokyo'})
[tool call]   wiki_tool({'topic': 'Curitiba'})
[tool result] wiki_tool: Tokyo, officially the Tokyo Metropolis, is the capital and most populous city of Japan. The population of the city proper was over 14 million as of 2023. The Greater Tokyo Area, which includes Tokyo and parts of six neighboring prefectures, is the third-most populous metropolitan area in the world, ...

[tool result] wiki_tool: Curitiba ( KOOR-ih-CHEE-bə; Brazilian Portuguese: [kuɾiˈtʃibɐ]) is the capital and largest city in the state of Paraná in Southern Brazil. The city's population was 1,829,225 as of 2024, making it the eighth most populous city in Brazil and the largest in Brazil's South Region. The Curitiba metropol...

[tool call]   calc_tool({'expression': '14000000 / 1829225'})
[tool call]   calc_tool({'expression': '33000000 / 1829225'})
[tool result] calc_tool: 7.653514466509041

[tool result] calc_tool: 18.04042695677131

FINAL: Resumo direto, com base na Wikipedia (as fontes indicam duas medidas para Tóquio):

- Tóquio (cidade propriamente dita): ≈ 14 milhões de habitantes (2023).
- Área metropolitana de Tóquio (Greater Tokyo Area): ≈ 33 milhões de habitantes (2025).
- Curitiba: 1.829.225 habitantes (2024).

Razões de comparação:
- Usando a população da cidade de Tóquio: 14.000.000 / 1.829.225 ≈ 7,65 vezes maior que Curitiba.
- Usando a população da área metropolitana de Tóquio: 33.000.000 / 1.829.225 ≈ 18,04 vezes maior que Curitiba.

Se quiser, eu mantenho apenas uma das referências (cidade ou área metropolitana) ou atualizo com números mais recentes.
```
