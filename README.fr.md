
![LightAgent Banner](docs/images/lightagent-banner.jpg)
<div align="center">
  <p>
    <a href="https://opensource.org/licenses/Apache-2.0"><img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="License"></a>
    <a href="https://github.com/wanxingai/LightAgent/releases"><img src="https://img.shields.io/github/release/wanxingai/LightAgent.svg" alt="GitHub release"></a>
    <a href="https://github.com/wanxingai/LightAgent/issues"><img src="https://img.shields.io/github/issues/wanxingai/LightAgent.svg" alt="GitHub issues"></a>
    <a href="https://github.com/wanxingai/LightAgent/stargazers"><img src="https://img.shields.io/github/stars/wanxingai/LightAgent.svg" alt="GitHub stars"></a>
    <a href="https://github.com/wanxingai/LightAgent/network"><img src="https://img.shields.io/github/forks/wanxingai/LightAgent.svg" alt="GitHub forks"></a>
    <a href="https://github.com/wanxingai/LightAgent/graphs/contributors"><img src="https://img.shields.io/github/contributors/wanxingai/LightAgent.svg" alt="GitHub contributors"></a>
    <a href="https://sufe-aiflm-lab.github.io/LightAgent/"><img src="https://img.shields.io/badge/docs-latest-brightgreen.svg" alt="Docs"></a>
    <a href="https://pypi.org/project/lightagent/"><img src="https://img.shields.io/pypi/v/lightagent.svg" alt="PyPI"></a>
    <a href="https://pypi.org/project/lightagent/"><img src="https://img.shields.io/pypi/dm/lightagent.svg" alt="Downloads"></a>
    <a href="https://pypi.org/project/lightagent/"><img src="https://img.shields.io/pypi/pyversions/lightagent.svg" alt="Python Version"></a>
    <a href="https://github.com/psf/black"><img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Code Style"></a>
  </p>
</div>
<div align="center">
  <p>
    <a href="README.md">English</a> | 
    <a href="README.zh-CN.md">简体中文</a> | 
    <a href="README.zh-TW.md">繁體中文</a> | 
    <a href="README.es.md">Español</a> | 
    Français | 
    <a href="README.de.md">Deutsch</a> | 
    <a href="README.ja.md">日本語</a> | 
    <a href="README.ko.md">한국어</a> | 
    <a href="README.pt.md">Português</a> | 
    <a href="README.ru.md">Русский</a> 
  </p>
</div>

<div align="center">
  <h1>LightAgent : framework d'agents IA de nouvelle génération</h1>
</div>

**LightAgent** est un framework Python modulaire et open source avec des Skills réutilisables, des outils, une mémoire à long terme optionnelle, ainsi que des modèles et du streaming compatibles OpenAI. `LightSwarm` gère le routage, `LightFlow` les étapes connues et `LightDAG` les tâches dynamiques persistantes et vérifiées. Le runtime optionnel fondé sur les événements ajoute sessions persistantes, exécution asynchrone, politiques et approbations. MCP prend en charge stdio, SSE et Streamable HTTP.

---

## Actualités
- <img src="https://img.alicdn.com/imgextra/i3/O1CN01SFL0Gu26nrQBFKXFR_!!6000000007707-2-tps-500-500.png" alt="new" width="30" height="30"/>**[2026-10-01]** LightAgent v0.11.0 publié : ajoute des DAG dynamiques multi-agents persistants et optionnels, des artefacts immuables soumis à vérification, une reprise avec baux et fencing, et un `SecurityContext` unifié avec permissions uniquement réductibles et contrôles d'approbation.
- **[2026-08-15]** LightAgent v0.10.0 publié : introduit le runtime fondé sur les événements avec sessions persistantes, exécution asynchrone, Capability Registry et Policy, Inbox, Goals, Budgets, Jobs, sous-agents, compactage du contexte et recherche SQLite FTS5.
- **[2026-08-15]** LightAgent v0.9.7 publié : ajoute un contrat Connector léger et sans dépendance avec validation hors ligne et exemples, renforce les contrôles de sécurité de l'exécuteur Python, introduit une matrice de sécurité Mem0 Graph optionnelle et prépare la stabilisation de v1.0 avec un inventaire de compatibilité de l'API publique.
- **[2026-07-30]** LightAgent v0.9.6 publié : ajoute des résumés et exportateurs de traces pour la production, une évaluation déterministe, une approbation humaine persistante pour les outils, les handoffs et LightFlow, ainsi qu'une admission d'écriture fail-closed et des contrôles d'audit pour la mémoire graphique partagée.
- **[2026-06-24]** LightAgent v0.9.0 : ajoute des workflows LightFlow avec checkpoints, reprise/rerun, nœuds d'approbation, états d'étapes plus clairs, métadonnées de trace, modèles Guardrails, contrôles MemoryPolicy et prototype SharedMemoryPool.
- **[2026-06-14]** LightAgent v0.8.1 : ajoute MemoryScope et les filtres MemoryPolicy par provenance, portée et confiance.
- **[2026-06-02]** LightAgent v0.8.0 : introduit LightFlow pour les workflows déterministes multi-étapes.

Les anciennes notes sont disponibles dans [GitHub Releases](https://github.com/wanxingai/LightAgent/releases).

---

## ✨ Fonctionnalités

- **Léger et efficace** : framework Python modulaire et open source, sans LangChain ni LlamaIndex, avec des dépendances ciblées pour les modèles, MCP, la mémoire et les traces.
- **Runtime fondé sur les événements** : sessions persistantes optionnelles, replay, checkpoints, appels asynchrones, Capability et Policy, Inbox, Goals, Budgets, Jobs, sous-agents, compactage du contexte et recherche SQLite FTS5.
- **DAG dynamiques vérifiés** : LightDAG persiste les changements du graphe, exécute les Workers indépendants en parallèle et ne publie les artefacts immuables qu'après vérification définie par l'application.
- **Mémoire** : mémoire à long terme personnalisable par utilisateur, avec intégration optionnelle de `mem0` et contrôle par MemoryPolicy.
- **Apprentissage** : chaque agent peut exploiter la mémoire de ses échanges, sous le contrôle d'administrateurs autorisés.
- **Intégration d'outils** : outils Python personnalisés, génération d'outils et intégration MCP.
- **Objectifs complexes** : le module Tree of Thought (`ToT`) prend en charge la décomposition et le raisonnement en plusieurs étapes.
- **Collaboration multi-agent** : LightSwarm reconnaît les intentions et délègue aux agents spécialisés.
- **Exécution autonome** : tâches et outils s'exécutent dans les limites des politiques et approbations configurées.
- **Modèles multiples** : fournisseurs compatibles OpenAI, dont OpenAI, DeepSeek, Qwen, Zhipu ChatGLM et les serveurs locaux compatibles.
- **API en streaming** : réponses au format OpenAI pour l'intégration aux interfaces de conversation.
- **Génération d'outils** : création d'outils à partir de la documentation d'une API ; voir le [guide des outils](docs/tools.md).
- **Mémoire contextuelle** : conservation des informations pertinentes issues des conversations, selon la politique d'admission.
- **Sélection adaptative des outils** : sélection d'un sous-ensemble pertinent avant l'envoi au modèle afin de limiter la taille du contexte.
- **Orchestration de workflows** 🔁 : LightFlow chaîne des agents dans des workflows déterministes avec dépendances explicites, passage de sorties, retries, checkpoints, reprise/rerun, approbations, agents fallback et traçabilité.
- **Prototype de mémoire partagée** 🧠 : SharedMemoryPool fournit une mémoire partagée en mémoire avec métadonnées de provenance, récupération par portée et résultats compatibles MemoryPolicy.
- **Modèles Guardrails** 🛡️ : règles réutilisables d'entrée, d'outil et de sortie pour bloquer les données privées, confirmer les outils sensibles, valider les paramètres à risque et masquer les sorties.
- **Runtime Hooks** 🧩 : middleware ordonné `hooks=[...]` pour observer, remplacer ou bloquer les phases run, modèle, outil, mémoire et étapes LightFlow.
- **Évaluation et revue humaine** 📊 : `LightEvaluator` exécute des régressions déterministes ; `HumanApprovalHook`, les review stores persistants et les checkpoints LightFlow permettent approbation, rejet, édition des arguments et feedback.

## 🧭 Vue d'ensemble de l'architecture

| Couche | API principale | À utiliser pour |
| --- | --- | --- |
| Runtime mono-agent | `LightAgent` | Un agent avec modèle, outils, mémoire, streaming, trace et guardrails. |
| État persistant du runtime | `Session`, `AgentRuntime` | Replay, checkpoints, Inbox, Goals, Budgets, Jobs et restauration du contexte. |
| Couche de capacités | `CapabilityRegistry`, `PolicyEngine` | Fournisseurs à portée limitée, politiques, cycle de vie et audit. |
| Contexte de sécurité unifié | `SecurityContext`, `CapabilityGate`, `ApprovalToken` | Identité, permissions uniquement réductibles, autorisation et approbations liées à une opération. |
| Routage multi-agent | `LightSwarm` | Délégation par rôle entre agents spécialisés. |
| Workflow déterministe | `LightFlow` | DAG, retries, checkpoints, approbations, reprise et rerun. |
| Workflow dynamique vérifié | `LightDAG` | Décomposition dynamique, vérificateurs, artefacts, Workers parallèles et reprise. |
| Outils et intégrations | `tools`, `ToolRegistry`, MCP | Outils Python, générés, chargement runtime ou serveurs MCP. |
| Frontière mémoire | `MemoryPolicy`, `MemoryScope` | Isolation de tenant, provenance, confiance, expiration et admission d’écriture. |
| Mémoire partagée | `SharedMemoryPool` | Expériences de mémoire partagée entre agents. |
| Sécurité | `input_guardrails`, `tool_guardrails`, `output_guardrails` | Vie privée, confirmation d’outils, paramètres à risque et redaction de sortie. |
| Runtime hooks | `hooks`, `HookContext`, `HookDecision` | Politique, audit, masquage, routage et mutation des payloads aux limites du cycle de vie. |
| Observabilité | `trace=True`, `agent.export_trace()` | Événements structurés de run, modèle, outil, erreur et workflow. |

## Modes d'utilisation principaux

LightAgent garde le chemin d’appel par défaut simple et permet d’ajouter progressivement des contrôles de production.

| Mode | Appel minimal | Notes |
| --- | --- | --- |
| Réponse simple | `agent.run(query)` | Retourne une chaîne par défaut. |
| Streaming | `agent.run(query, stream=True)` | Retourne des chunks compatibles OpenAI. |
| Résultat structuré | `agent.run(query, result_format="object")` | Retourne contenu et métadonnées. |
| Trace | `agent.run(query, trace=True)` | Enregistre les événements sans changer le retour par défaut. |
| Mémoire utilisateur | `agent.run(query, user_id="alice")` | Utilise le backend mémoire et MemoryPolicy configurés. |
| Outils | `LightAgent(..., tools=[fn])` | Les fonctions doivent exposer `tool_info`. |
| Guardrails | `LightAgent(..., input_guardrails=[...])` | Ajoute des politiques d’entrée, outil et sortie. |
| Runtime hooks | `LightAgent(..., hooks=[fn])` | Observe, remplace ou bloque les payloads du cycle de vie. |
| Workflow | `LightFlow().step(...).run(query)` | Pour l’exécution déterministe multi-étapes. |
| Workflow dynamique | `LightDAG(...).create_run(...)` | Proposer des tâches et vérifier les résultats avant publication. |
| Session persistante | `agent.run(query, session_id="project-42")` | Nécessite un SessionStore persistant configuré pour le replay et la reprise. |
| Asynchrone | `await agent.arun(query)` | Point d'entrée non bloquant pour les applications asyncio. |

## v0.11.0 : Workflows dynamiques vérifiés

Utilisez `LightSwarm` pour le routage par rôle, `LightFlow` pour des étapes connues et le `LightDAG` optionnel lorsque les Workers doivent proposer de nouvelles tâches pendant l'exécution.

- `SqliteTaskGraphStore` conserve tâches, tentatives, modifications du graphe, événements et état de reprise. Des instances indépendantes de Worker peuvent s'exécuter en parallèle.
- Les Workers renvoient `TaskOutcome.candidate(...)`, `TaskOutcome.decompose(...)` ou `TaskOutcome.blocked(...)`. Seul un Verifier fixé par l'application peut accepter une décomposition ou publier des artefacts immuables.
- Les baux et le fencing rejettent les tentatives périmées lors d'une reprise. `SecurityContext`, `CapabilityGate` et les `ApprovalToken` liés à une opération rendent explicites identité, permissions uniquement réductibles et approbations.

### Exemple LightDAG hors ligne

Aucun modèle, clé API ou réseau n'est nécessaire. L'exemple utilise une base SQLite et un répertoire d'artefacts temporaires, supprimés à la fin.

```python
from pathlib import Path
from tempfile import TemporaryDirectory

from LightAgent import (
    CallableVerifier, LightDAG, LocalArtifactStore, PermissionSet,
    SecurityContext, SqliteTaskGraphStore, TaskOutcome, TaskSpec,
)

with TemporaryDirectory() as directory:
    root = Path(directory)
    store = SqliteTaskGraphStore(root / "dag.sqlite3")
    try:
        dag = LightDAG(
            store=store,
            artifact_store=LocalArtifactStore(root / "artifacts"),
            verifiers={"exact": CallableVerifier(
                "exact", lambda request: request.candidate_content == b"42",
            )},
        )
        dag.register_worker("local", lambda context: TaskOutcome.candidate("42"))
        dag.create_run([TaskSpec(
            task_id="answer", goal="42",
            acceptance_contract={"equals": "42"},
            worker_key="local", verifier_key="exact",
        )], run_id="readme-demo", context=SecurityContext(
            user_id="alice", tenant_id="demo", project_id="readme",
            permissions=PermissionSet(allowed=frozenset({"dag.task.execute"})),
        ))
        result = dag.run("readme-demo")
        assert result.success
        print(result.status.value)
    finally:
        store.close()
```

Pour conserver les données, utilisez des chemins explicites et durables plutôt que des répertoires temporaires. L'[exemple complet de décomposition et réparation](example/14.dynamic_dag.py) et le [guide LightDAG](docs/lightdag.md) couvrent dépendances, intégration, nouvelles tentatives et reprise.

Le [guide du runtime](docs/runtime_v010.md) explique les sessions persistantes, appels asynchrones, Capability Providers, Policy, Inbox, Goals, Budgets et Jobs.

### Compatibilité et limites de sécurité

- `agent.run(query)`, `stream=True` et `user_id` restent disponibles. LightDAG est optionnel et ne remplace pas LightFlow.
- v0.11.0 fonctionne sur un seul hôte, avec SQLite local et un ordonnanceur actif par exécution. L'exécution est au moins une fois ; les effets externes exigent l'idempotence. Workers distribués, interface web et sandbox de code intégrée sont hors périmètre.
- Les anciens `execute_python_code`, `execute_python_file` et `execute_python_code_stream` sont bloqués dans l'exécution des outils du modèle, même avec `enable_unsafe_python=True` ou un `SandboxProvider` enregistré. Utilisez `safe_expression` ou un outil réellement isolé ; l'appel direct à ces utilitaires ne constitue pas une sandbox de sécurité.
- Les politiques de provenance, d'admission et de promotion mémoire restent nécessaires. Les tests du framework ne certifient pas un backend réel de mémoire graphique partagée ; voir la [sécurité mémoire](docs/memory_security.md).

### Version publiée et branche main actuelle

[v0.11.0](https://github.com/wanxingai/LightAgent/releases/tag/v0.11.0) a été publiée le 2026-10-01. Les corrections ultérieures du JSON de sélection d'outils, des SDK MCP 1.x/2.x et l'exemple optionnel deed.page ont été intégrés après ce tag et peuvent manquer dans le paquet publié. La commande suivante installe `main` actuel, pas le tag initial :

```bash
pip install --upgrade "git+https://github.com/wanxingai/LightAgent.git@main"
```

Consultez [Tools Guide](docs/tools.md), l'[adaptateur Memcode](docs/memcode_memory_adapter.md) optionnel, l'[exemple deed.page](docs/deed_page_mcp.md) et l'[inventaire de compatibilité publique](docs/public_api_compatibility.md). Ces services externes ne sont pas requis par le runtime principal.

## 📋 Documentation

- Pour l'installation, les modèles, outils, mémoire, MCP, Skills, streaming et LightSwarm, consultez [FAQ](docs/FAQ.md).
- Pour les workflows déterministes, checkpoints, reprise/rerun, approbations, agents fallback et états d'étape, consultez [LightFlow](docs/lightflow.md).
- Pour les outils personnalisés, ToolRegistry, ToolLoader, AsyncToolDispatcher et MCP, consultez [Tools Guide](docs/tools.md).
- Pour la mémoire partagée ou graphe, consultez [Memory Security Guidance](docs/memory_security.md).
- Pour SharedMemoryPool, consultez [SharedMemoryPool](docs/shared_memory_pool.md).
- Pour l'admission d'écriture mémoire et l'expiration, consultez [Memory Admission And Mutation Controls](docs/memory_admission.md).
- Pour les politiques de sécurité d'entrée, outil et sortie, consultez [Guardrails](docs/guardrails.md).
- Pour le middleware runtime qui observe, remplace ou bloque les payloads, consultez [Runtime Hooks](docs/runtime_hooks.md).
- Pour OpenRouter, modèles locaux et fournisseurs compatibles OpenAI, consultez [Model Provider Configuration](docs/model_providers.md).
- Pour les traces structurées, consultez [Trace Observability](docs/tracing.md).
- Pour les régressions déterministes, consultez [Evaluation Harness](docs/evaluation.md).
- Pour l'approbation outil/handoff, la revue persistante et le feedback, consultez [Human Review](docs/human_review.md).

## Feuille de route

Consultez la [feuille de route](roadmap.md) pour les étapes livrées et les projets futurs. Inbox, Jobs et sous-agents sont déjà disponibles dans le runtime optionnel.

## 🌟 Pourquoi choisir LightAgent ?

- **Libre et ouvert** : développement communautaire et contributions bienvenues.
- **Prise en main** : documentation et exemples pour intégrer progressivement le framework.
- **Communauté** : échanges, questions et suivi des problèmes sur GitHub.
- **Concurrence** : points d'entrée asynchrones et Workers indépendants pour les tâches parallélisables.

---

## 🛠️ Démarrage rapide

### Installer la dernière version de LightAgent

```bash
pip install lightagent
```

(Optionnel) Installez le paquet Mem0 avec pip :

```bash
pip install mem0ai
```

Vous pouvez aussi utiliser le [service hébergé Mem0](https://www.mem0.ai/).

### Premier exemple

```python
from LightAgent import LightAgent

# Initialize the Agent
agent = LightAgent(model="gpt-4o-mini", api_key="your_api_key", base_url="your_base_url")

# Run the Agent
response = agent.run("Hello, who are you?")
print(response)
```

### Inspecter une trace d’exécution (v0.7.0)

La trace est optionnelle et conserve le comportement par défaut de `agent.run()`.

```python
from LightAgent import LightAgent

agent = LightAgent(model="gpt-4.1", api_key="your_api_key", base_url="your_base_url")

result = agent.run("Hello, who are you?", result_format="object", trace=True)
print(result.content)
print(result.trace_id)
print(result.trace)

for event in agent.export_trace():
    print(event["type"], event["data"])
```

### Checkpoint d’une exécution LightFlow (v0.9.0)

`LightFlow` peut persister des checkpoints et reprendre une exécution échouée sans repartir du premier pas.

```python
from LightAgent import JsonLightFlowStore, LightAgent, LightFlow

research_agent = LightAgent(model="gpt-4.1", api_key="your_api_key", base_url="your_base_url")
writer_agent = LightAgent(model="gpt-4.1", api_key="your_api_key", base_url="your_base_url")

store = JsonLightFlowStore(".lightflow_runs")
flow = (
    LightFlow(store=store)
    .step("research", agent=research_agent, timeout=30)
    .step("write", agent=writer_agent, depends_on=["research"], max_retry=2)
)

result = flow.run("Analyze this company", run_id="report-001", trace=True)

if not result.success:
    result = flow.resume("report-001")

print(result.status)
print(flow.get_run("report-001")["steps"])
```

### Utiliser SharedMemoryPool (v0.9.0)

`SharedMemoryPool` est un prototype léger en mémoire pour les expériences de mémoire partagée multi-agent.

```python
from LightAgent import LightAgent, MemoryPolicy, SharedMemoryPool

shared_memory = SharedMemoryPool(agent_name="writer")

agent = LightAgent(
    name="writer",
    model="gpt-4.1",
    api_key="your_api_key",
    base_url="your_base_url",
    memory=shared_memory,
    memory_policy=MemoryPolicy(
        namespace="tenant-a",
        allow_unattributed_results=False,
        allowed_sources=("user",),
        allowed_scopes=("user",),
    ),
)

agent.run("Remember that I prefer concise reports.", user_id="alice")
print(shared_memory.list_records(user_id="tenant-a:alice"))
```


### Définir le rôle de l'agent avec un message système

```python
from LightAgent import LightAgent

# Initialize the Agent
agent = LightAgent(
     role="Please remember you are LightAgent, a helpful assistant that can help users utilize multiple tools.",  # system role description
     model="deepseek-chat",  # Supported models: openai, chatglm, deepseek, qwen, etc.
     api_key="your_api_key",  # Replace with your large model service provider API Key
     base_url="your_base_url",  # Replace with your large model service provider api url
 )
# Run the Agent
response = agent.run("May I ask who you are?")
print(response)
```

### Exemple d'utilisation d'un outil

```python
from LightAgent import LightAgent

# Define Tool
def get_weather(city_name: str) -> str:
    """
    Get the current weather for `city_name`
    """
    return f"Query result: {city_name} Weather is clear"
# Define tool information within the function
get_weather.tool_info = {
    "tool_name": "get_weather",
    "tool_description": "Get the current weather information for a specified city",
    "tool_params": [
        {"name": "city_name", "description": "The name of the city to query", "type": "string", "required": True},
    ]
}

tools = [get_weather]

# Initialize the Agent
agent = LightAgent(model="qwen-turbo-2024-11-01", api_key="your_api_key", base_url="your_base_url", tools=tools)

# Run the Agent
response = agent.run("Please help me check the weather condition in Shanghai")
print(response)
```
Plusieurs outils personnalisés peuvent être enregistrés.

Exemple de liste : `tools = [search_news, get_weather, get_stock_realtime_data, get_stock_kline_data]`.

---

## Fonctionnalités en détail

Le README garde le modèle d’utilisation principal ; les exemples longs, réglages d’adaptateurs et pratiques de production sont dans les docs dédiées.

### 1. Module mémoire détachable (`mem0`)
LightAgent accepte tout backend mémoire avec `store(data, user_id)` et `retrieve(query, user_id)`. Utilisez `user_id` pour isoler les conversations et `MemoryPolicy` quand la mémoire est partagée.

### 2. Intégration d’outils
Utilisez des fonctions Python avec métadonnées `tool_info` pour exposer des capacités contrôlées. Pour ToolRegistry, ToolLoader, AsyncToolDispatcher et MCP, consultez [Tools Guide](docs/tools.md).

### 3. Générateur d’outils
`agent.create_tool()` peut générer du code d’outil depuis une documentation API ou une description naturelle. Relisez et testez avant production.

### 4. Tree of Thought (ToT)
Activez `tree_of_thought=True` pour les tâches nécessitant planification explicite, réflexion et sélection d’outils.

### 5. Collaboration multi-agent
`LightSwarm` délègue le travail entre agents spécialisés. Gardez des rôles étroits et contrôlez les écritures mémoire.

### 6. API streaming
`agent.run(query, stream=True)` retourne des chunks compatibles OpenAI pour UI chat et longues sorties.

### 7. Auto-apprentissage de l’agent
L’auto-apprentissage doit être combiné à `MemoryPolicy` pour éviter les contenus privés, expirés ou non pertinents.

### 8. Trace et Langfuse
LightAgent permet d’observer l’exécution via trace intégrée ou Langfuse.

### 9. Évaluation des agents
`LightEvaluator` mesure sortie, choix d’outils, événements de politique, reprise, latence, usage et coût estimé.

### 10. Workflows LightFlow
`LightFlow` est la couche workflow déterministe pour exécuter des étapes connues.

- États d’étape : `pending`, `running`, `success`, `failed`, `skipped`, `waiting_approval`.
- Validation DAG : `flow.validate(strict=True)`.
- Contrôles d’étape : `timeout`, `max_retry`, `cancel_if`, `fallback_agent`, `requires_approval`, `approval_handler`.
- Persistance et reprise : `JsonLightFlowStore`, `flow.resume(run_id)`, `flow.rerun_step(run_id, step_name)`, `flow.get_run(run_id)`, `flow.list_runs()`.

Consultez [LightFlow](docs/lightflow.md).

### 11. Guardrails
Les Guardrails sont des hooks légers autour de l’exécution : entrée, outils et sortie.

```python
from LightAgent import (
    LightAgent,
    high_risk_parameter_guardrail,
    output_redaction_guardrail,
    privacy_input_guardrail,
    sensitive_tool_confirmation_guardrail,
)

agent = LightAgent(
    model="gpt-4.1",
    api_key="your_api_key",
    base_url="your_base_url",
    input_guardrails=[privacy_input_guardrail()],
    tool_guardrails=[
        sensitive_tool_confirmation_guardrail(["transfer_money"], approved=False),
        high_risk_parameter_guardrail({"amount": lambda value: float(value) <= 1000}),
    ],
    output_guardrails=[output_redaction_guardrail()],
)
```

Consultez [Guardrails](docs/guardrails.md).

### 12. SharedMemoryPool
`SharedMemoryPool` est un prototype en mémoire pour mémoire partagée multi-agent, à combiner avec `MemoryPolicy`.

## Modèles pris en charge

LightAgent fonctionne avec les endpoints chat completion compatibles OpenAI : OpenAI, OpenRouter, Zhipu ChatGLM, DeepSeek, Qwen, StepFun, Moonshot/Kimi, MiniMax, vLLM, llama.cpp, Ollama et passerelles auto-hébergées.

Pour les paramètres des fournisseurs, les URL de base, les modèles locaux et le dépannage, consultez la [configuration des modèles](docs/model_providers.md).

## Cas d'utilisation

- **Service client** : conversations multi-tours et intégration d'outils métier.
- **Analyse de données** : décomposition des tâches et collaboration entre agents.
- **Automatisation** : création et intégration d'outils personnalisés.
- **Assistance pédagogique** : expériences personnalisées avec mémoire et réponses en streaming.

---
 
## 🛠️ Contribuer

Les contributions au code, à la documentation, aux tests et les retours sont bienvenus. Signalez les problèmes ou proposez vos améliorations dans une issue ou une pull request :

1. **Créer un fork** : copiez le projet vers votre compte avec le bouton `Fork`.
2. **Créer une branche** : créez une branche locale pour vos modifications :
   ```bash
   git checkout -b feature/YourFeature
   ```
3. **Enregistrer les modifications** : après le développement, créez un commit :
   ```bash
   git commit -m 'Add some feature'
   ```
4. **Publier la branche** : envoyez-la vers votre fork :
   ```bash
   git push origin feature/YourFeature
   ```
5. **Ouvrir une pull request** : décrivez les changements et les tests sur GitHub.

Nous examinerons votre contribution dès que possible. Merci de votre soutien.

---

## 🙏 Remerciements

LightAgent s'appuie sur les idées et les contributions des projets open source suivants :

- **mem0** : [module de mémoire](https://github.com/mem0ai/mem0) et gestion du contexte.
- **Swarm** : [principes de collaboration multi-agent](https://github.com/openai/swarm).
- **ChatGLM3** : [modèles et inspiration](https://github.com/THUDM/ChatGLM3).
- **Qwen** : [modèles de langage](https://github.com/QwenLM/Qwen).
- **DeepSeek-V3** : [modèles de langage](https://github.com/deepseek-ai/DeepSeek-V3).
- **StepFun** : [modèles de langage](https://www.stepfun.com/).

---

## 📄 Licence

LightAgent est distribué sous [licence Apache 2.0](LICENSE). Vous pouvez l'utiliser, le modifier et le redistribuer dans le respect de cette licence.

---

## 📬 Nous contacter

Pour toute question ou suggestion :

- **Courriel** : service@wanxingai.com
- **GitHub Issues**: [https://github.com/wanxingai/LightAgent/issues](https://github.com/wanxingai/LightAgent/issues)  

Vos retours contribuent à améliorer LightAgent.


---

<p align="center">
  <strong>LightAgent - Une intelligence plus légère, un avenir plus simple.</strong>
</p>

 
**LightAgent** : un framework d'agents léger, flexible et modulaire pour construire des applications intelligentes.
