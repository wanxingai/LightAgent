
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
  <h1>LightAgent🚀 (Next Generation Agentic AI Framework)</h1>
</div>

**LightAgent** est un cadre agentique actif extrêmement léger avec mémoire (`mem0`), outils (`Tools`), et arbre de pensée (`ToT`), et il est entièrement open source. Il prend en charge une collaboration multi-agents plus simple que OpenAI Swarm, permettant de construire en un seul pas des agents capables d'apprentissage autonome, et prend en charge l'accès au protocole MCP via stdio et sse. Le modèle sous-jacent prend en charge OpenAI, Zhiyu ChatGLM, DeepSeek, Jieyue Xingchen, Qwen Tongyi Qianwen et d'autres grands modèles. De plus, LightAgent prend en charge la sortie de service API au format de flux OpenAI, s'intégrant sans couture aux principaux cadres de chat. 🌟

---

## Actualités
- <img src="https://img.alicdn.com/imgextra/i3/O1CN01SFL0Gu26nrQBFKXFR_!!6000000007707-2-tps-500-500.png" alt="new" width="30" height="30"/>**[2026-06-24]** LightAgent v0.9.0 : ajoute des workflows LightFlow avec checkpoints, reprise/rerun, nœuds d'approbation, états d'étapes plus clairs, métadonnées de trace, modèles Guardrails, contrôles MemoryPolicy et prototype SharedMemoryPool.
- **[2026-06-14]** LightAgent v0.8.1 : ajoute MemoryScope et les filtres MemoryPolicy par provenance, portée et confiance.
- **[2026-06-02]** LightAgent v0.8.0 : introduit LightFlow pour les workflows déterministes multi-étapes.

Les anciennes notes sont disponibles dans [GitHub Releases](https://github.com/wanxingai/LightAgent/releases).

---

## ✨ Features

- **Light and Efficient** 🚀: Minimalist design, rapid deployment, suitable for various application scenarios. (No LangChain, No LlamaIndex) 100% implemented in Python, with no extra dependencies, core code only 1000 lines, completely open source. 
- **Memory Support** 🧠: Supports user-customizable long-term memory for each user, natively supporting `mem0` memory module, automatically managing personalized memory during conversations to make agents smarter.
- **Autonomous Learning** 📚️: Each agent has independent learning capabilities, and authorized administrators can manage each agent.
- **Tool Integration** 🛠️: Supports customizable tools (`Tools`), automated tool generation, and flexible expansion to meet diverse needs.  
- **Complex Goals** 🌳: Built-in reflective Tree of Thought (`ToT`) module supports complex task decomposition and multi-step reasoning, enhancing task processing capabilities.  
- **Multi-agent Collaboration** 🤖: Multi-agent cooperation that is easier to implement than Swarm, with built-in LightSwarm for intent recognition and task transfer capabilities, intelligently handling user input and transferring tasks to other agents as needed. 
- **Independent Execution** 🤖: Tasks are completed autonomously without human intervention.  
- **Multi-model Support** 🔄: Compatible with OpenAI, Zhiyu ChatGLM, Baichuan large models, Jumpshop Star, DeepSeek, Qwen series large models.  
- **Streaming API** 🌊: Supports OpenAI streaming API service output, seamlessly integrating with mainstream chat frameworks, enhancing user experience.  
- **Tools Generator** 🚀: Just hand over your API documentation to the [Tools Generator], and it will automatically create your exclusive tools, helping you quickly build hundreds of personalized custom tools in just one hour, enhancing efficiency and unleashing your creative potential.
- **Agent Self-Learning** 🧠️: Each agent has its own contextual memory capability, enabling self-learning from user conversations.
- **Adaptive Tools Mechanism** 🛠️: Support for adding unlimited tools, allowing the large model to first select a candidate tool set from tens of thousands of tools, filtering out irrelevant tools before submitting context to the large model, significantly reducing token consumption.
- **Orchestration de workflows** 🔁 : LightFlow chaîne des agents dans des workflows déterministes avec dépendances explicites, passage de sorties, retries, checkpoints, reprise/rerun, approbations, agents fallback et traçabilité.
- **Prototype de mémoire partagée** 🧠 : SharedMemoryPool fournit une mémoire partagée en mémoire avec métadonnées de provenance, récupération par portée et résultats compatibles MemoryPolicy.
- **Modèles Guardrails** 🛡️ : règles réutilisables d'entrée, d'outil et de sortie pour bloquer les données privées, confirmer les outils sensibles, valider les paramètres à risque et masquer les sorties.

## 🧭 Vue d'ensemble de l'architecture

| Couche | API principale | À utiliser pour |
| --- | --- | --- |
| Runtime mono-agent | `LightAgent` | Un agent avec modèle, outils, mémoire, streaming, trace et guardrails. |
| Routage multi-agent | `LightSwarm` | Délégation par rôle entre agents spécialisés. |
| Workflow déterministe | `LightFlow` | DAG, retries, checkpoints, approbations, reprise et rerun. |
| Outils et intégrations | `tools`, `ToolRegistry`, MCP | Outils Python, générés, chargement runtime ou serveurs MCP. |
| Frontière mémoire | `MemoryPolicy`, `MemoryScope` | Isolation de tenant, provenance, confiance, expiration et admission d’écriture. |
| Mémoire partagée | `SharedMemoryPool` | Expériences de mémoire partagée entre agents. |
| Sécurité | `input_guardrails`, `tool_guardrails`, `output_guardrails` | Vie privée, confirmation d’outils, paramètres à risque et redaction de sortie. |
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
| Workflow | `LightFlow().step(...).run(query)` | Pour l’exécution déterministe multi-étapes. |

## 📋 Documentation

- Pour l'installation, les modèles, outils, mémoire, MCP, Skills, streaming et LightSwarm, consultez [FAQ](docs/FAQ.md).
- Pour les workflows déterministes, checkpoints, reprise/rerun, approbations, agents fallback et états d'étape, consultez [LightFlow](docs/lightflow.md).
- Pour les outils personnalisés, ToolRegistry, ToolLoader, AsyncToolDispatcher et MCP, consultez [Tools Guide](docs/tools.md).
- Pour la mémoire partagée ou graphe, consultez [Memory Security Guidance](docs/memory_security.md).
- Pour SharedMemoryPool, consultez [SharedMemoryPool](docs/shared_memory_pool.md).
- Pour l'admission d'écriture mémoire et l'expiration, consultez [Memory Admission And Mutation Controls](docs/memory_admission.md).
- Pour les politiques de sécurité d'entrée, outil et sortie, consultez [Guardrails](docs/guardrails.md).
- Pour OpenRouter, modèles locaux et fournisseurs compatibles OpenAI, consultez [Model Provider Configuration](docs/model_providers.md).
- Pour les traces structurées, consultez [Trace Observability](docs/tracing.md).

## 🚧 Coming Soon

- **Communication collaborative des agents** 🛠️ : Les agents peuvent également partager des informations et transmettre des messages, réalisant ainsi une communication complexe des informations et une collaboration sur les tâches.
- **Agent Evaluation** 📊: Built-in Agent evaluation tools for assessing and optimizing the agents you build, aligning with business scenarios, and continuously improving intelligence.  

## 🌟 Why Choose LightAgent?

- **Open Source and Free** 💖: Completely open source, community-driven, continuously updated, contributions welcomed!  
- **Easy to Get Started** 🎯: Detailed documentation, abundant examples, quick to start, and easy to integrate into your projects.  
- **Community Support** 👥: An active developer community ready to assist and answer your questions.  
- **High Performance** ⚡: Optimized design for efficient operation, meeting high concurrency scenario demands.  

---

## 🛠️ Quick Start

### Install the Latest Version of LightAgent

```bash
pip install lightagent
```

(Optional installation) Install the Mem0 package via pip:

```bash
pip install mem0ai
```

Alternatively, you can use Mem0 on a hosting platform with one-click [click here](https://www.mem0.ai/).

### Hello World Sample Code

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


### Set Agent Self-Recognition Through System Prompts

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

### Tool Usage Sample Code

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
Supports custom tools in unlimited quantities.

Multiple tool examples: tools = [search_news,get_weather,get_stock_realtime_data,get_stock_kline_data]

---

## Detailed Function Descriptions

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
L’évaluation des agents mesurera le comportement face à des scénarios métier.

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

## Supported Mainstream Agent Models

LightAgent fonctionne avec les endpoints chat completion compatibles OpenAI : OpenAI, OpenRouter, Zhipu ChatGLM, DeepSeek, Qwen, StepFun, Moonshot/Kimi, MiniMax, vLLM, llama.cpp, Ollama et passerelles auto-hébergées.

For provider-specific parameters, base URLs, local model setup, and troubleshooting, see [Model Provider Configuration](docs/model_providers.md).

## Use Cases

- **Intelligent Customer Service**: Provide efficient customer support through multi-turn conversations and tool integration.
- **Data Analysis**: Use Tree of Thought and multi-agent collaboration to process complex data analysis tasks.
- **Automated Tools**: Quickly build customized tools through automated tool generation.
- **Educational Assistance**: Provide personalized learning experiences through memory modules and streaming APIs.

---
 
## 🛠️ Contribution Guidelines

We welcome contributions of any form! Whether it's code, documentation, testing, or feedback, every bit helps the project immensely. If you have good ideas or find bugs, please submit an issue or pull request. Here are the contribution steps:

1. **Fork This Project**: Click the `Fork` button in the upper right corner to copy the project to your GitHub repository.
2. **Create a Branch**: Create your development branch locally:  
   ```bash
   git checkout -b feature/YourFeature
   ```
3. **Submit Changes**: After completing the development, submit your changes:  
   ```bash
   git commit -m 'Add some feature'
   ```
4. **Push Branch**: Push the branch to your remote repository:  
   ```bash
   git push origin feature/YourFeature
   ```
5. **Submit Pull Request**: Submit a pull request on GitHub and describe your changes.

We will review your contributions as soon as possible. Thank you for your support! ❤️

---

## 🙏 Acknowledgments

The development and implementation of LightAgent would not have been possible without the inspiration and support from the following open-source projects, especially the excellent teams behind them:

- **mem0**: Thanks to [mem0](https://github.com/mem0ai/mem0) for providing the memory module, which offers strong support for contextual management in LightAgent.  
- **Swarm**: Thanks to [Swarm](https://github.com/openai/swarm) for the multi-agent collaborative design ideas that underpin the multi-agent functionality of LightAgent.  
- **ChatGLM3**: Thanks to [ChatGLM3](https://github.com/THUDM/ChatGLM3) for high-performance Chinese large model support and design inspiration.  
- **Qwen**: Thanks to [Qwen](https://github.com/QwenLM/Qwen) for high-performance Chinese large model support.  
- **DeepSeek-V3**: Thanks to [DeepSeek-V3](https://github.com/deepseek-ai/DeepSeek-V3) for high-performance Chinese large model support.  
- **StepFun**: Thanks to [step](https://www.stepfun.com/) for high-performance Chinese large model support.  

---

## 📄 License

LightAgent is licensed under the [Apache 2.0 License](LICENSE). You are free to use, modify, and distribute this project, but please comply with the terms of the license.

---

## 📬 Contact Us

For any questions or suggestions, feel free to contact us:

- **Email**: service@wanxingai.com  
- **GitHub Issues**: [https://github.com/wanxingai/LightAgent/issues](https://github.com/wanxingai/LightAgent/issues)  

We look forward to your feedback to make LightAgent stronger! 🚀


---

<p align="center">
  <strong>LightAgent - Make intelligence lighter and the future simpler.</strong> 🌈
</p>

 
**LightAgent** —— A lightweight, flexible, and powerful proactive Agent framework to help you quickly build intelligent applications!