# Estágio 04 — Google ADK

Execução real de 2026-10-13, com `openai/gpt-5-nano`. Saída copiada do terminal, sem edição.

**O que observar:** Declarativo puro: `Agent(name, model, instruction, tools)` e acabou. As ferramentas são funções Python comuns — a docstring vira a descrição e os type hints viram o schema, sem decorador. A execução chega como um **stream de eventos** (`run_async`), que é o que a UI do `adk web` consome.

```text
/Users/leonardo/dev/ia/projects/testing-agents/.venv/lib/python3.14/site-packages/google/adk/models/llm_request.py:306: UserWarning: [EXPERIMENTAL] feature FeatureName.JSON_SCHEMA_FOR_FUNC_DECL is enabled.
  declaration = tool._get_declaration()
MODEL: openai/gpt-5-nano
USER: Qual a população de Tóquio segundo a Wikipedia, e quantas vezes ela é maior que a da minha cidade natal, Curitiba? Busque a de Curitiba se não souber.

--- research_assistant ---
[tool call] wiki_tool({'topic': 'Tokyo'})
[tool call] wiki_tool({'topic': 'Curitiba'})
--- research_assistant ---
[tool result] {'result': 'Tokyo, officially the Tokyo Metropolis, is the capital and most populous city of Japan. The population of the city proper was over 14 million as of 2023. The Greater Tokyo Area, which includes Tokyo and parts of six neighboring prefectures, is the third-most populous metropolitan area in the world, with 33 million residents as of 2025.'}
[tool result] {'result': "Curitiba ( KOOR-ih-CHEE-bə; Brazilian Portuguese: [kuɾiˈtʃibɐ]) is the capital and largest city in the state of Paraná in Southern Brazil. The city's population was 1,829,225 as of 2024, making it the eighth most populous city in Brazil and the largest in Brazil's South Region. The Curitiba metropolitan area comprises 29 municipalities with a total population of over 3,559,366, making it the ninth most populous metropolitan area in the country."}
--- research_assistant ---
[tool call] calc_tool({'expression': '14000000 / 1829225'})
[tool call] calc_tool({'expression': '33000000 / 1829225'})
--- research_assistant ---
[tool result] {'result': '7.653514466509041'}
[tool result] {'result': '18.04042695677131'}
--- research_assistant ---
Resumo reproduzindo dados da Wikipedia:

- Tóquio (cidade própria): mais de 14 milhões de habitantes (dados até 2023).
- Curitiba: 1.829.225 habitantes (dados até 2024).

Razões aproximadas:
- Tóquio versus Curitiba (cidade): ≈7,65 vezes maior.
- Se usar a Área Metropolitana de Tóquio (Greater Tokyo Area): ≈18,0 vezes maior (33 milhões vs 1,829,225).

Observação: os valores variam conforme a definição (cidade própria vs área metropolitana).

FINAL: Resumo reproduzindo dados da Wikipedia:

- Tóquio (cidade própria): mais de 14 milhões de habitantes (dados até 2023).
- Curitiba: 1.829.225 habitantes (dados até 2024).

Razões aproximadas:
- Tóquio versus Curitiba (cidade): ≈7,65 vezes maior.
- Se usar a Área Metropolitana de Tóquio (Greater Tokyo Area): ≈18,0 vezes maior (33 milhões vs 1,829,225).

Observação: os valores variam conforme a definição (cidade própria vs área metropolitana).
```
