# Agentes de IA — do prompt ao Kubernetes

Material de apresentação em duas partes:

1. **O mesmo agente em três camadas de abstração**, rodando no laptop como processo Python.
2. **kagent**: o agente como objeto do Kubernetes, seguindo o quickstart oficial.

---

## Parte 1 — Os três agentes

Um agente de pesquisa com três ferramentas (busca web, Wikipedia e calculadora), implementado três vezes. A pergunta é a mesma nos três:

> *"Qual a população de Tóquio segundo a Wikipedia, e quantas vezes ela é maior que a da minha cidade natal, Curitiba?"*

O que muda entre os estágios é **quem faz o loop**.

| Pasta | O que agrega |
|---|---|
| `01_react_prompt/` | Loop ReAct escrito à mão: prompt + regex + dispatch. Prova que "agente" não é mágica. |
| `02_langchain/` | `create_agent` do LangChain faz o loop. Ferramentas com decorador `@tool`. |
| `03_langgraph/` | Grafo explícito de estados, com tool calling nativo (sem parsing de texto). |

`shared/tools.py` implementa as ferramentas uma única vez — os três importam de lá.

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
```

### Opcional: ver o grafo do LangGraph

```bash
langgraph dev
```

Abre o LangGraph Studio no navegador com o grafo do estágio 03 desenhado (configurado em `langgraph.json`).

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

### 8. Limpar

```bash
kubectl delete -f kubernetes/
kagent uninstall
kind delete cluster
```

O `kind delete cluster` sozinho já resolve tudo, se preferir.
