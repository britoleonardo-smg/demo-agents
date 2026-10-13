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

Aqui o agente deixa de ser um processo no laptop e passa a ser um **recurso do cluster**: `kubectl get agent` lista ele, o RBAC do Kubernetes limita ele.

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

### 5. Sem navegador: o CLI

Se não quiser depender da UI no palco:

```bash
kagent get agent
kagent invoke --agent k8s-agent -t "Quais pods estão com problema no cluster?"
```

### Vale mostrar: o RBAC padrão é cluster-admin

Ponto de discussão que rende na apresentação. Por padrão, o ServiceAccount das ferramentas do kagent recebe `*/*/*` — ou seja, **cluster-admin para um pod controlado por um LLM**:

```bash
kubectl auth can-i delete pods --as=system:serviceaccount:kagent:kagent-tools
```

O chart tem como fechar isso (`kagent-tools.rbac.readOnly=true`, que troca o ClusterRole por `get, list, watch`, e `kagent-tools.tools.args=["--read-only"]`, que faz o binário nem registrar as ferramentas de escrita), mas o default é aberto para não quebrar instalações existentes. Vale rodar o comando acima no palco: é uma linha, e a resposta fala por si.

### 6. Limpar

```bash
kagent uninstall
kind delete cluster
```

O `kind delete cluster` sozinho já resolve tudo, se preferir.
