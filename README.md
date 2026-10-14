# Agentes de IA — do prompt ao Kubernetes

Material de apresentação em duas partes:

1. **O mesmo agente em três camadas de abstração**, rodando no laptop como processo Python.
2. **kagent**: o agente como objeto do Kubernetes, seguindo o quickstart oficial.

---

## Parte 1 — Os quatro agentes

Um agente de pesquisa com três ferramentas (busca web, Wikipedia e calculadora), implementado quatro vezes. A pergunta é a mesma em todos:

> *"Qual a população de Tóquio segundo a Wikipedia, e quantas vezes ela é maior que a da minha cidade natal, Curitiba?"*

O que muda entre os estágios é **quem faz o loop**.

| Pasta | O que agrega |
|---|---|
| `01_react_prompt/` | Loop ReAct escrito à mão: prompt + regex + dispatch. Prova que "agente" não é mágica. |
| `02_langchain/` | `create_agent` do LangChain faz o loop. Ferramentas com decorador `@tool`. |
| `03_langgraph/` | Grafo explícito de estados, com tool calling nativo (sem parsing de texto). |
| `google_adk/` | Estágio 04: declarativo puro do Google. Ferramentas são funções Python comuns — a docstring vira a descrição, os type hints viram o schema. |

`shared/tools.py` implementa as ferramentas uma única vez — todos importam de lá.

**Evidência pronta para mostrar:** [`outputs/`](outputs/) tem a saída real dos quatro, e [`screenshots/`](screenshots/) tem as telas das interfaces. Dá para conduzir a apresentação inteira pelo GitHub se a demo ao vivo não puder acontecer.

### Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

No `.env`, escolha `LLM_PROVIDER` (`openai` ou `gemini`) e cole a chave correspondente. O padrão com OpenAI é o `gpt-5-nano`: uma execução completa custa menos de um centavo de dólar.

### Rodar

```bash
python 01_react_prompt/agent.py
python 02_langchain/agent.py
python 03_langgraph/agent.py
python google_adk/agent.py
```

Cada um imprime o rastro completo: qual ferramenta foi chamada, com que argumento e o que voltou. A saída real de todos está em [`outputs/`](outputs/) — dá para mostrar direto do GitHub, sem rodar nada.

> A pasta do estágio 04 se chama `google_adk` e não `04_google_adk` porque o `adk web` importa a pasta como módulo Python, e nome começando com dígito não é identificador válido. Ele recusa com `Invalid agent name`.

### Opcional: tracing no LangSmith

Os estágios 02 e 03 são LangChain e LangGraph puros, então o LangSmith funciona **sem tocar no código** — só três linhas no `.env`:

```bash
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_...
LANGSMITH_PROJECT=agentes-demo
```

Rode qualquer um dos dois e a execução aparece em <https://smith.langchain.com>. A árvore de uma execução real está em [`outputs/langsmith.md`](outputs/langsmith.md) — inclusive a revelação de que o `create_agent` do estágio 02 **é LangGraph por baixo**.

### Opcional: ver o grafo do LangGraph

```bash
langgraph dev
```

Abre o LangGraph Studio no navegador com o grafo do estágio 03 desenhado (configurado em `langgraph.json`).

### Opcional: a UI do Google ADK

```bash
adk web google_adk
```

Em <http://localhost:8000>, o Dev UI do ADK. Duas abas valem a apresentação:

- **Events** — a conversa com cada chamada de ferramenta, e o grafo do agente desenhado à esquerda.
- **Traces** — a cascata de tempo. Numa execução medida aqui: 21,25 s no total, **21,2 s esperando o LLM** e 1,9 s somando as duas chamadas de Wikipédia. É o argumento visual de onde o tempo de um agente realmente vai.

Telas das duas em [`screenshots/`](screenshots/).

---

## Parte 2 — kagent no Kubernetes

Aqui o agente deixa de ser um processo no laptop e passa a ser um **recurso do cluster**: `kubectl get agent` lista ele, o RBAC do Kubernetes limita ele. O fim da seção fecha o círculo — o agente de pesquisa da Parte 1 roda dentro do cluster, com as mesmas três ferramentas.

Isto é o [quickstart oficial](https://kagent.dev/docs/kagent/0.x/getting-started/quickstart/), sem desvios. Versão testada: kagent **0.10.3**.

### 1. Pré-requisitos

Precisa do **Docker** rodando (Docker Desktop, Colima ou Rancher Desktop), com pelo menos 2 GB de memória livre.

```bash
brew install kind kubectl helm kagent
```

No Linux, sem Homebrew, siga as páginas oficiais de instalação do [kind](https://kind.sigs.k8s.io/docs/user/quick-start/), do [kubectl](https://kubernetes.io/docs/tasks/tools/) e do [helm](https://helm.sh/docs/intro/install/), e instale o CLI do kagent com:

```bash
curl https://raw.githubusercontent.com/kagent-dev/kagent/refs/heads/main/scripts/get-kagent | bash
```

No Windows, use o **WSL2** com a integração do Docker Desktop ligada e siga as instruções de Linux dentro do terminal do Ubuntu.

### 2. Criar o cluster

```bash
kind create cluster
```

Cria um cluster de um nó chamado `kind` e já seleciona o contexto `kind-kind` no kubectl. Confira:

```bash
kubectl get nodes
```

### 3. Instalar o kagent

```bash
export OPENAI_API_KEY="sua-chave-aqui"
kagent install --profile demo
```

O perfil `demo` já traz agentes e ferramentas MCP pré-carregados — inclusive um agente de Kubernetes, que é o que a demo usa. (`--profile minimal` instala sem eles.)

> **Primeira instalação leva ~2 minutos**, porque baixa cerca de sete imagens. Depois sobe em ~40 s. **Rode uma vez antes da apresentação** para aquecer o cache do kind.
>
> É normal o pod `kagent-controller` aparecer com 2 ou 3 restarts logo depois do install: ele sobe antes do PostgreSQL aceitar conexão e estabiliza sozinho em cerca de um minuto.

### 4. Abrir o dashboard

```bash
kagent dashboard
```

Abre em <http://localhost:8082> e segura o terminal. Na primeira vez aparece um wizard de boas-vindas — pode seguir ou clicar em **Skip wizard**, já que o perfil `demo` criou os agentes.

Clique no agente de Kubernetes e pergunte algo sobre o cluster, por exemplo:

> *What API resources are running in my cluster?*

A UI mostra as chamadas de ferramenta (**Arguments** / **Results**) por baixo da resposta — é ali que fica claro que o agente está lendo o cluster de verdade, e não inventando.

### 5. Aplicar o nosso agente

Até aqui tudo veio pronto do chart. Agora o ponto da apresentação: **criar um agente é aplicar um YAML**, como qualquer outro objeto do cluster.

`kubernetes/sre-agent.yaml` define o `sre-agent`: um SRE que investiga o cluster com quatro ferramentas de leitura e que **pede aprovação humana** antes de escalar um deployment.

Antes de aplicar, confirme o nome do ModelConfig que o install criou:

```bash
kubectl get modelconfig -n kagent
```

Se não for `default-model-config` (acontece se você criou outro modelo pela UI), troque o campo `modelConfig:` no YAML. Então:

```bash
kubectl apply -f kubernetes/sre-agent.yaml
kubectl -n kagent wait --for=condition=Ready agent/sre-agent --timeout=120s
kubectl get agent -n kagent
```

O `sre-agent` aparece na lista ao lado dos agentes do chart, e o controller sobe um Deployment próprio para ele:

```bash
kubectl -n kagent get deploy sre-agent
```

Volte na UI (recarregue a página) e converse com ele. O próprio cluster já dá material, sem precisar quebrar nada — o `kagent-controller` reinicia algumas vezes na subida:

> *Investigue a causa dos restarts do kagent-controller: cruze o describe do pod, os eventos e os logs, e me diga a causa provável.*

**Dica de palco:** pergunta específica, que já diz o sintoma e o que você quer, tem resposta muito melhor. Com uma pergunta aberta ("algum pod está com problema?") o modelo tende a responder o que achou e perguntar "posso investigar?" em vez de investigar — fica parecendo que travou.

**O momento do human-in-the-loop.** Peça uma alteração:

> *Escale o deployment helm-agent para 2 réplicas.*

O agente propõe a chamada de `k8s_scale` e **pausa**: a UI mostra botões de **Approve** e **Reject**. Nada acontece no cluster até você clicar. Se recusar, pode dar o motivo, e o motivo volta para o modelo como contexto.

Isso vem destas três linhas do YAML — as ferramentas de leitura não estão na lista, então rodam direto:

```yaml
requireApproval:
  - k8s_scale
```

Para voltar ao estado anterior depois da demo:

```bash
kubectl -n kagent scale deploy/helm-agent --replicas=1
```

### 6. O agente de pesquisa, com as nossas ferramentas

Aqui a apresentação fecha o círculo: **o agente da Parte 1 rodando dentro do cluster**, com as mesmas três ferramentas. Não é uma reimplementação — o `shared/tools.py` vai para o cluster como está, no mesmo arquivo que os estágios 01, 02 e 03 importam.

Duas peças em [`kubernetes/pesquisa-agent.yaml`](kubernetes/pesquisa-agent.yaml):

| Resource | O que faz |
|---|---|
| `MCPServer/pesquisa-tools` | Roda o [`mcp-tools/server.py`](mcp-tools/server.py), que embrulha as três funções do `shared/tools.py` em tools MCP. |
| `Agent/pesquisa-agent` | O agente de pesquisa, declarativo, usando só essas três tools — nenhuma de Kubernetes. |

**Sem build de imagem.** O código sobe num ConfigMap e roda na imagem oficial do `uv`; o bloco PEP 723 no topo do `server.py` declara as dependências (`fastmcp`, `ddgs`, `wikipedia`, `numexpr`) e o `uv run` instala na subida do pod.

```bash
kubectl create configmap pesquisa-tools-code -n kagent \
  --from-file=server.py=mcp-tools/server.py \
  --from-file=tools.py=shared/tools.py

kubectl apply -f kubernetes/pesquisa-agent.yaml
kubectl -n kagent wait --for=condition=Ready mcpserver/pesquisa-tools --timeout=300s

# O agente sobe antes do Service do MCP existir e cai no modo de descoberta
# tardia. Um restart depois do MCP pronto resolve.
kubectl -n kagent rollout restart deploy/pesquisa-agent
```

A primeira subida do `pesquisa-tools` leva cerca de um minuto: puxa a imagem do `uv` e instala as dependências. Isso se repete a cada restart do pod, porque o cache não é persistido.

Na UI, o `pesquisa-agent` aceita a mesma pergunta dos estágios 01-03:

> *Qual a população de Tóquio segundo a Wikipédia, e quantas vezes ela é maior que a da minha cidade natal, Curitiba?*

**O detalhe que vale projetar:** o adaptador de transporte na frente do servidor MCP loga cada chamada de ferramenta pelo nome. É a prova de que o agente usou as ferramentas, e não a memória do modelo:

```bash
kubectl -n kagent logs deploy/pesquisa-tools -c mcp-server --tail=20 | grep mcp.tool
```

```
... mcp.tool=wikipedia_lookup duration=1088ms
... mcp.tool=wikipedia_lookup duration=1112ms
... mcp.tool=calculator       duration=13ms
```

Mudou alguma ferramenta no `shared/tools.py`? Recrie o ConfigMap e reinicie os dois pods:

```bash
kubectl create configmap pesquisa-tools-code -n kagent \
  --from-file=server.py=mcp-tools/server.py \
  --from-file=tools.py=shared/tools.py \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl -n kagent rollout restart deploy/pesquisa-tools deploy/pesquisa-agent
```

### 7. Sem navegador: o CLI

```bash
kagent get agent
kagent invoke --agent sre-agent -t "Quais pods do namespace kagent tiveram restarts?"
```

> O `invoke` depende de um port-forward para o controller, que o `kagent dashboard` deixa de pé — rode os dois em terminais separados. E se ele responder `failed to decode response: json: cannot unmarshal object into ... errordetails.Typed`, não é problema do seu agente: é o CLI 0.10.3 engasgando ao formatar um erro vindo do servidor. A causa mais comum é chave da OpenAI inválida; a UI mostra a mensagem real.

Se a chave estiver errada, troque sem reinstalar nada:

```bash
kubectl -n kagent create secret generic kagent-openai \
  --from-literal=OPENAI_API_KEY="$OPENAI_API_KEY" \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl -n kagent rollout restart deploy
```

### Vale mostrar: o RBAC padrão é cluster-admin

Ponto de discussão que rende na apresentação. Por padrão, o ServiceAccount das ferramentas do kagent recebe `*/*/*` — ou seja, **cluster-admin para um pod controlado por um LLM**:

```bash
kubectl auth can-i delete pods --as=system:serviceaccount:kagent:kagent-tools
```

O chart tem como fechar isso (`kagent-tools.rbac.readOnly=true`, que troca o ClusterRole por `get, list, watch`, e `kagent-tools.tools.args=["--read-only"]`, que faz o binário nem registrar as ferramentas de escrita), mas o default é aberto para não quebrar instalações existentes. Vale rodar o comando acima no palco: é uma linha, e a resposta fala por si.

No mesmo espírito, dá para comparar os dois agentes: o `k8s-agent` que vem no perfil `demo` recebe as 18 ferramentas de `k8s_*`, incluindo `k8s_delete_resource` e `k8s_execute_command`, **sem nenhuma na lista de aprovação**. O nosso recebe cinco, e a única de escrita pausa para um humano decidir.

```bash
kubectl -n kagent get agent k8s-agent -o jsonpath='{.spec.declarative.tools}' | tr ',' '\n'
```

### 8. Tracing: ver o loop do agente por dentro

O kagent não guarda trace nenhum — ele exporta OTLP e esquece. Aponte para onde quiser (Tempo, Jaeger, Honeycomb, Datadog) ou para um collector com o exporter `debug`, que imprime o span no log do pod. Aqui usamos **Tempo + Grafana**.

#### Subir

```bash
helm repo add grafana https://grafana.github.io/helm-charts && helm repo update grafana

helm upgrade --install tempo grafana/tempo --version 1.24.4 \
  -n telemetry --create-namespace -f kubernetes/observability/tempo-values.yaml

helm upgrade --install grafana grafana/grafana --version 10.5.15 \
  -n telemetry --create-namespace -f kubernetes/observability/grafana-values.yaml
```

> O chart do Grafana avisa `this chart is deprecated`. Ele instala e funciona; o caminho novo é o `grafana-operator`, mais cerimônia do que uma demo precisa.

#### Ligar no kagent — em dois lugares

```bash
helm upgrade kagent oci://ghcr.io/kagent-dev/kagent/helm/kagent --version 0.10.3 \
  -n kagent --reuse-values \
  --set otel.tracing.enabled=true \
  --set otel.tracing.exporter.otlp.endpoint=http://tempo.telemetry.svc.cluster.local:4317 \
  --set kagent-tools.otel.tracing.enabled=true \
  --set kagent-tools.otel.tracing.exporter.otlp.endpoint=http://tempo.telemetry.svc.cluster.local:4317

# Sem isto você fica olhando tela vazia: o controller injeta as env vars OTEL no
# pod do agente, e env var só entra na criação do pod.
kubectl -n kagent rollout restart deploy -l app.kubernetes.io/part-of=kagent
```

O `--reuse-values` é de propósito. A receita da doc oficial manda fazer `helm get values kagent > values.yaml`, o que **despeja a sua chave da OpenAI num arquivo em disco**.

#### Olhar

```bash
kubectl -n telemetry port-forward svc/grafana 3000:80
```

Em <http://localhost:3000>, **Explore → Tempo**. A senha do admin:

```bash
kubectl -n telemetry get secret grafana -o jsonpath='{.data.admin-password}' | base64 -d
```

Procure pelo service com o **nome do agente, com underscore** (`pesquisa_agent`, `sre_agent`). A doc oficial diz para procurar o service `kagent` e a operação `agent_run [agente]` — isso mudou, e procurando como a doc manda você não acha nada.

#### O que o trace mostra

```
POST /                                4294 ms
└─ invocation                         4277 ms
   └─ invoke_agent pesquisa_agent     4234 ms
      ├─ generate_content gpt-4.1-mini   1530 ms
      ├─ execute_tool wikipedia_lookup   1168 ms
      └─ generate_content gpt-4.1-mini    999 ms
```

O loop do agente desenhado, com a duração de cada etapa. Em geral é aqui que cai a ficha de que **quase todo o tempo é espera do LLM**, não execução de ferramenta.

Os spans seguem as convenções semânticas de GenAI, e trazem o que importa:

| Atributo | O que tem |
|---|---|
| `gen_ai.usage.input_tokens` / `output_tokens` | consumo por chamada |
| `gen_ai.usage.cache_read.input_tokens` | o que veio de cache |
| `gen_ai.request.model` | modelo usado |
| `gcp.vertex.agent.tool_call_args` | argumentos da ferramenta |
| `gcp.vertex.agent.tool_response` | resposta da ferramenta |

> Repare que prompt e resposta de ferramenta **ficam dentro do span**. Ótimo para depurar, atenção em produção: trace com retenção longa é PII com retenção longa.

#### Painéis a partir do trace, sem Prometheus

Com o `metricsGenerator` ligado (está no `tempo-values.yaml`), estas queries TraceQL viram gráfico no Grafana. Todas testadas:

```
{ name =~ "execute_tool.*" } | rate() by (name)
→ execute_tool calculator: 0.0167

{ span.gen_ai.usage.output_tokens > 0 } | sum_over_time(span.gen_ai.usage.output_tokens) by (resource.service.name)
→ pesquisa_agent: 33

{ name =~ "generate_content.*" } | sum_over_time(span.gen_ai.usage.input_tokens) by (name)
→ generate_content gpt-4.1-mini: 730

{ name =~ "generate_content.*" } | avg_over_time(span.gen_ai.usage.output_tokens)
→ 16.5
```

Ou seja: **consumo de token por agente, direto do trace**, sem Prometheus no meio. Isso não existe em métrica em lugar nenhum do kagent — só no span.

#### Duas pegadinhas que custam tempo

1. **`enabled: true` no generator não basta.** Cada processor precisa ser habilitado também em `tempo.overrides.defaults.metrics_generator.processors`. Sem isso a query de métrica falha com `error finding generators: empty ring`.
2. **`local_blocks` guarda só spans de servidor por padrão.** E os spans que interessam (`execute_tool`, `generate_content`) são internos. Sem `filter_server_spans: false` a query volta **vazia, sem erro nenhum** — o pior tipo de falha para depurar.

#### E se você usa Grafana Cloud

Nenhum dos dois blocos `otel` do kagent tem campo de *headers*, então não há onde colocar o token de autenticação. O caminho é um **Alloy ou OTel Collector** dentro do cluster: o kagent exporta para ele em `:4317`, e ele encaminha com a credencial. De brinde você ganha sampling e filtro de conteúdo — relevante por causa do PII acima.

#### Métricas Prometheus que já existem

Independente de tracing, duas métricas já estão contando e servem de painel:

```bash
# tool server embutido: chamadas por ferramenta
kubectl -n kagent port-forward svc/kagent-tools-metrics 8085:8085
# kagent_tools_mcp_invocations_total{tool_name="k8s_get_resources"} 3

# adaptador na frente do nosso MCP: as nossas tools, sem instrumentar o Python
kubectl -n kagent port-forward deploy/pesquisa-tools 15020:15020
# tool_calls_total{server="pesquisa-tools",name="wikipedia_lookup"} 5
```

O `/metrics` do controller (`controller.metrics.enabled=true`) tem só `controller-runtime` e Go — **nada por agente**. E o `ServiceMonitor` existe no `main` do repositório, mas **não na 0.10.3**.

### 9. Limpar

```bash
kubectl delete -f kubernetes/ --recursive
helm uninstall -n telemetry grafana tempo   # se subiu o tracing
kagent uninstall
kind delete cluster
```

O `kind delete cluster` sozinho já resolve tudo, se preferir.
