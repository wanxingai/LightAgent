
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
    <a href="https://arxiv.org/abs/2509.09292"><img src="https://img.shields.io/badge/arXiv-Paper-B31B1B?logo=arxiv&logoColor=white" alt="Code Style"></a>
  </p>
</div>
<div align="center">
  <p>
    English | 
    <a href="README.zh-CN.md">简体中文</a> | 
    <a href="README.zh-TW.md">繁體中文</a> | 
    <a href="README.es.md">Español</a> | 
    <a href="README.fr.md">Français</a> | 
    <a href="README.de.md">Deutsch</a> | 
    <a href="README.ja.md">日本語</a> | 
    <a href="README.ko.md">한국어</a> | 
    <a href="README.pt.md">Português</a> | 
    <a href="README.ru.md">Русский</a> 
  </p>
</div>
<div align="center">
  <h1>LightAgent🚀 – small footprint, big potential. 🌟(Open-source Agentic framework)</h1>
</div>

LightAgent is an ultra‑lightweight, open‑source framework that now natively supports Skills — letting you compose reusable capabilities with persistent memory, tool use, and tree‑of‑thought reasoning. It streamlines multi‑agent collaboration (build self‑learning agents in one step), connects to MCP over stdio and SSE, runs on any modern LLM (OpenAI, DeepSeek, Qwen, and more), and outputs OpenAI‑compatible streaming APIs for instant drop‑in with any chat interface. Small, modular, and skill‑ready — spin it up in five minutes.

---
## News
- <img src="https://img.alicdn.com/imgextra/i3/O1CN01SFL0Gu26nrQBFKXFR_!!6000000007707-2-tps-500-500.png" alt="new" width="30" height="30"/>**[2026-06-24]** LightAgent v0.9.0 Development: Adds checkpointed LightFlow workflows with resume/rerun support, approval nodes, richer step status and trace metadata, reusable Guardrails templates, stronger MemoryPolicy controls, and the first SharedMemoryPool prototype.
- <img src="https://img.alicdn.com/imgextra/i3/O1CN01SFL0Gu26nrQBFKXFR_!!6000000007707-2-tps-500-500.png" alt="new" width="30" height="30"/>**[2026-06-14]** LightAgent v0.8.1 Development: Adds MemoryScope metadata conventions, stricter MemoryPolicy provenance filters, and guidance for separating trace, user memory, self-reflection memory, and LightSwarm delegation state.
- **[2026-06-02]** LightAgent v0.8.0 Development: Adds initial LightFlow workflow orchestration for deterministic multi-step agent execution with DAG dependencies, step output passing, retries, and flow trace events.
- **[2026-05-29]** LightAgent v0.7.0 Development: Adds opt-in trace observability with structured run/model/tool/error events, `agent.export_trace()`, and prompt-safe model request summaries for production debugging.
- **[2026-05-28]** LightAgent v0.6.5 Released: Adds opt-in structured run results, structured streaming events, catchable LightAgent errors, and tool argument validation while keeping legacy `agent.run()` and `stream=True` behavior compatible.
- **[2026-05-27]** LightAgent v0.6.4 Released: Improves runtime tool dispatch reliability, adds structured error codes and troubleshooting guidance, expands OpenAI-compatible provider documentation for OpenRouter and local models, and updates browser-use integration examples.

Older release notes are available on [GitHub Releases](https://github.com/wanxingai/LightAgent/releases).

---

![lightswarm_demo_en.png](docs%2Fimages%2Flightswarm_demo_en.png)

## ✨ Features

- **Lightweight and Efficient** 🚀: Minimalist design, quick deployment, suitable for various application scenarios. (No LangChain, No LlamaIndex) The core framework stays small, modular, and fully open source while using focused dependencies for provider, MCP, memory, and tracing integrations. 
- **Memory Support** 🧠: Supports custom long-term memory for each user, natively supporting the `mem0` memory module, automatically managing user personalized memory during conversations, making agents smarter.
- **Autonomous Learning** 📚️: Each agent possesses autonomous learning capabilities, and admins with permissions can manage each agent.
- **Tool Integration** 🛠️: Support for custom tools (`Tools`) and MCP tool integration, flexible expansion to meet diverse needs.  
- **Complex Goals** 🌳: Built-in Tree of Thought (`ToT`) module with reflection, supporting complex task decomposition and multi-step reasoning, enhancing task processing capabilities.  
- **Multi-Agent Collaboration** 🤖: Simpler to implement multi-agent collaboration than Swarm, with built-in LightSwarm for intent recognition and task delegation, enabling smarter handling of user input and delegating tasks to other agents as needed. 
- **Workflow Orchestration** 🔁: LightFlow chains agents into deterministic multi-step workflows with explicit dependencies, step output passing, retries, checkpointed run records, resume/rerun support, approval nodes, fallback agents, and traceable execution.
- **Shared Memory Prototype** 🧠: SharedMemoryPool provides append-first in-memory shared memory with provenance metadata, scoped retrieval, and MemoryPolicy-compatible results for multi-agent experiments.
- **Independent Execution** 🤖: Tasks and tool calls are completed autonomously without human intervention.  
- **Multi-Model Support** 🔄: Compatible with OpenAI-style providers such as OpenAI, OpenRouter, Zhipu ChatGLM, Baichuan, StepFun, DeepSeek, Qwen, vLLM, llama.cpp, and other OpenAI-compatible endpoints.  
- **Streaming API** 🌊: Supports OpenAI streaming format API service output, seamlessly integrates with mainstream chat frameworks, enhancing user experience.  
- **Trace Observability** 🔎: Opt-in `trace=True` run traces record structured run lifecycle, model request summaries, tool calls, tool results, and errors without changing the default string return value.  
- **Runtime Hooks** 🧩: Ordered `hooks=[...]` middleware can observe, replace, or block run, model, tool, memory, and LightFlow step phases while recording hook decisions in trace events.
- **Guardrails Templates** 🛡️: Reusable input/tool/output guardrail templates help block private data, require confirmation for sensitive tools, validate high-risk parameters, and redact sensitive output.
- **Tool Generator** 🚀: Just provide your API documentation to the [Tool Generator], which will automatically create exclusive tools for you, allowing you to quickly build hundreds of personalized custom tools in just 1 hour to improve efficiency and unleash your creative potential.
- **Agent Self-Learning** 🧠️: Each agent has its own scene memory capabilities and the ability to self-learn from user conversations.
- **Adaptive Tool Mechanism** 🛠️: Supports adding an unlimited number of tools, allowing the large model to first select a candidate tool set from thousands of tools, filtering irrelevant tools before submitting context to the large model, significantly reducing token consumption.

## 🧭 Architecture At A Glance

| Layer | Main API | Use it when you need |
| --- | --- | --- |
| Single agent runtime | `LightAgent` | One agent with model calls, tools, memory, streaming, trace, and guardrails. |
| Multi-agent routing | `LightSwarm` | Role-based delegation across specialized agents. |
| Deterministic workflow | `LightFlow` | Ordered DAG workflows, retries, checkpoints, approvals, resume, and rerun. |
| Tools and integrations | `tools`, `ToolRegistry`, MCP | Python tools, generated tools, runtime tool loading, or MCP tool servers. |
| Memory boundary | `MemoryPolicy`, `MemoryScope` | Tenant isolation, provenance, trust, expiration, and write admission controls. |
| Shared memory prototype | `SharedMemoryPool` | In-memory shared memory experiments across agents. |
| Safety controls | `input_guardrails`, `tool_guardrails`, `output_guardrails` | Privacy blocking, sensitive tool confirmation, high-risk parameter checks, and output redaction. |
| Runtime hooks | `hooks`, `HookContext`, `HookDecision` | Policy, audit, redaction, routing, and payload mutation at lifecycle boundaries. |
| Observability | `trace=True`, `agent.export_trace()` | Structured run, model, tool, error, and workflow trace events. |

## Core Usage Patterns

LightAgent keeps the default call path simple while allowing production controls to be added incrementally.

| Pattern | Minimal call | Notes |
| --- | --- | --- |
| Basic response | `agent.run(query)` | Returns a string by default. |
| Streaming | `agent.run(query, stream=True)` | Returns OpenAI-compatible streaming chunks. |
| Structured result | `agent.run(query, result_format="object")` | Returns content plus structured metadata. |
| Trace | `agent.run(query, trace=True)` | Records events without changing the default string return. |
| User memory | `agent.run(query, user_id="alice")` | Uses the configured memory backend and memory policy. |
| Tools | `LightAgent(..., tools=[fn])` | Functions should expose `tool_info` metadata. |
| Guardrails | `LightAgent(..., input_guardrails=[...])` | Add input, tool, and output policies per agent. |
| Runtime hooks | `LightAgent(..., hooks=[fn])` | Observe, replace, or block lifecycle payloads. |
| Workflow | `LightFlow().step(...).run(query)` | Use for deterministic multi-step execution. |

## 🧩 Multi-agent troubleshooting (failure map)

If you are using LightSwarm or other multi-agent patterns and start seeing role drift, cross-agent memory issues or confusing logs, you can check the
[Multi-agent failure map](docs/multi_agent_failure_map.md) for a small symptom → mode → debug checklist.  
This page is docs-only and does not change any framework code.

## 📋 FAQ

For common installation, model provider, tool, memory, MCP, Skills, streaming, and LightSwarm questions, see [FAQ](docs/FAQ.md).

For deterministic multi-step workflows, checkpointed run records, resume/rerun, approval nodes, fallback agents, and step status tracking, see [LightFlow](docs/lightflow.md).

For custom tool creation, runtime tools, ToolRegistry, ToolLoader, AsyncToolDispatcher, and MCP tool integration, see [Tools Guide](docs/tools.md).

For shared long-term memory or graph memory deployments, review the [Memory Security Guidance](docs/memory_security.md).

For lightweight shared memory experiments, see [SharedMemoryPool](docs/shared_memory_pool.md).

For memory write admission, expiration-aware retrieval, and low-quality memory write blocking, see [Memory Admission And Mutation Controls](docs/memory_admission.md).

For separating trace, user memory, self-reflection memory, and LightSwarm delegation state, see [Memory, Trace, And Swarm Boundaries](docs/memory_trace_swarm_boundaries.md).

For input, tool, and output safety policies, see [Guardrails](docs/guardrails.md).

For runtime middleware that can observe, replace, or block lifecycle payloads, see [Runtime Hooks](docs/runtime_hooks.md).

For OpenRouter, local LLM, and OpenAI-compatible provider setup, see [Model Provider Configuration](docs/model_providers.md).

For structured error codes and troubleshooting hints, see [Error Handling](docs/error_handling.md).

For v0.7.0 trace observability, see [Trace Observability](docs/tracing.md).

For browser-use integration with recent `browser-use` versions, see [browser-use Integration](docs/browser_use.md).

---

## 🚧 Coming Soon

- **Agent Collaborative Communication** 🛠️: Agents can also share information and transmit messages, achieving complex information communication and task collaboration.
- **Agent Assessment** 📊: Built-in agent assessment tool for conveniently evaluating and optimizing the agents you build, aligning with business scenarios, and continuously improving intelligence levels.  


---
## 🌟 Why Choose LightAgent?

- **Open Source and Free** 💖: Fully open source, community-driven, continuously updated, contributions are welcome!  
- **Easy to Get Started** 🎯: Detailed documentation, rich examples, quick to get started, easy integration into your project.  
- **Community Support** 👥: An active developer community ready to assist and provide answers at any time.  
- **High Performance** ⚡: Optimized design, efficient operation, meeting high concurrency requirements.  

---

## 🛠️ Quick Start

### Install the latest version of LightAgent

```bash
pip install lightagent
```

(Optional installation) Install the Mem0 package via pip:

```bash
pip install mem0ai
```

Alternatively, you can use Mem0 on a hosted platform by clicking [here](https://www.mem0.ai/).

### Hello World Example Code

```python
from LightAgent import LightAgent

# Initialize Agent
agent = LightAgent(model="gpt-4.1", api_key="your_api_key", base_url="your_base_url")

# Run Agent
response = agent.run("Hello, who are you?")
print(response)
```

### Inspect a Run Trace (v0.7.0)

Tracing is opt-in and keeps the default `agent.run()` behavior backward compatible.

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

### Checkpoint a LightFlow Run (v0.9.0)

`LightFlow` can persist workflow checkpoints and resume failed runs without
starting from the first step again.

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

### Use SharedMemoryPool (v0.9.0)

`SharedMemoryPool` is a lightweight in-memory prototype for multi-agent shared
memory experiments.

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

### Set Model Self-Perception via System Prompt

```python
from LightAgent import LightAgent

# Initialize Agent
agent = LightAgent(
     role="Please remember that you are LightAgent, a useful assistant that helps users use multiple tools.",  # system role description
     model="gpt-4.1",  # Supported models: openai, chatglm, deepseek, qwen, etc.
     api_key="your_api_key",  # Replace with your large model provider API Key
     base_url="your_base_url",  # Replace with your large model provider api url
 )
# Run Agent
response = agent.run("Who are you?")
print(response)
```

### Tool Example Code

```python
from LightAgent import LightAgent

# Define Tool
def get_weather(city_name: str) -> str:
    """
    Get the current weather for `city_name`
    """
    return f"Query result: {city_name} is sunny."
# Define tool information inside the function
get_weather.tool_info = {
    "tool_name": "get_weather",
    "tool_description": "Get current weather information for the specified city.",
    "tool_params": [
        {"name": "city_name", "description": "The name of the city to query", "type": "string", "required": True},
    ]
}

tools = [get_weather]

# Initialize Agent
agent = LightAgent(model="gpt-4.1", api_key="your_api_key", base_url="your_base_url", tools=tools)

# Run Agent
response = agent.run("Please check the weather in Shanghai.")
print(response)
```
Supports an unlimited number of customizable tools.

Multiple tool examples: tools = [search_news, get_weather, get_stock_realtime_data, get_stock_kline_data]

---

## Function Details

README keeps the core usage model in one place. Longer examples, adapter-specific setup, and production guidance live in the dedicated docs pages.

### 1. Detachable Memory Module (`mem0`)
LightAgent accepts any memory backend that provides `store(data, user_id)` and `retrieve(query, user_id)`. This keeps memory detachable: you can start with a simple custom class, use `mem0`, or plug in a vector/graph memory adapter without changing agent code.

Use `user_id` to isolate conversations, and use `MemoryPolicy` when memory is shared across users, tenants, agents, or traces.

```python
from LightAgent import LightAgent, MemoryPolicy

agent = LightAgent(
    model="gpt-4.1",
    api_key="your_api_key",
    base_url="your_base_url",
    memory=your_memory_backend,
    memory_policy=MemoryPolicy(
        namespace="tenant-a",
        allowed_sources=("user", "reflection"),
        allowed_scopes=("user", "agent"),
        reject_duplicate_writes=True,
        min_write_length=8,
    ),
)

response = agent.run("Remember that I prefer concise reports.", user_id="alice")
```

See [Memory Security Guidance](docs/memory_security.md), [Memory Admission And Mutation Controls](docs/memory_admission.md), and [Memory, Trace, And Swarm Boundaries](docs/memory_trace_swarm_boundaries.md).

### 2. Tool Integration
Use Python functions with `tool_info` metadata to expose controlled capabilities to an agent. LightAgent can also work with runtime tools, `ToolRegistry`, `ToolLoader`, `AsyncToolDispatcher`, generated tools, and MCP tools.

```python
from LightAgent import LightAgent

def get_order_status(order_id: str) -> str:
    return f"Order {order_id} is being processed."

get_order_status.tool_info = {
    "tool_name": "get_order_status",
    "tool_description": "Get the status of an order.",
    "tool_params": [
        {"name": "order_id", "description": "Order ID", "type": "string", "required": True},
    ],
}

agent = LightAgent(
    model="gpt-4.1",
    api_key="your_api_key",
    base_url="your_base_url",
    tools=[get_order_status],
)
```

For advanced tool loading, generated tools, async dispatch, and MCP integration, see [Tools Guide](docs/tools.md).

### 3. Tool Generator
`agent.create_tool()` can generate tool code from API documentation or natural-language descriptions. It is useful when converting an internal API document into callable Python tools.

Keep generated tools in a reviewed tools directory, test them before production use, and avoid committing generated or experimental local tools unless they are part of the public package.

```python
agent.create_tool(
    "Create a tool that calls the internal order status API.",
    tools_directory="tools",
)
```

### 4. Tree of Thought (ToT)
Enable `tree_of_thought=True` when a task needs explicit planning and reflection before tool use or final response generation. ToT is best for complex multi-step reasoning, tool selection, and tasks where the agent should inspect its plan before acting.

```python
agent = LightAgent(
    model="gpt-4.1",
    api_key="your_api_key",
    base_url="your_base_url",
    tree_of_thought=True,
    tot_model="gpt-4.1",
    tot_api_key="your_api_key",
    tot_base_url="your_base_url",
)
```

### 5. Multi-Agent Collaboration
`LightSwarm` routes work across specialized agents for role-based delegation and multi-agent task handling. Use it when one front-facing agent should delegate to domain agents such as support, HR, finance, research, or data analysis.

Keep each agent's role narrow, give each agent clear boundaries, and avoid letting delegated agents write unrelated long-term memory unless the memory policy allows it.

```python
from LightAgent import LightAgent, LightSwarm

frontdesk = LightAgent(name="frontdesk", role="Route requests to the right specialist.")
finance = LightAgent(name="finance", role="Answer finance approval questions.")

swarm = LightSwarm()
swarm.register_agent(frontdesk, finance)
result = swarm.run(agent=frontdesk, query="How do I approve a vendor payment?")
```

For debugging role drift or cross-agent memory issues, see [Multi-agent failure map](docs/multi_agent_failure_map.md).

### 6. Streaming API
`agent.run(query, stream=True)` returns OpenAI-compatible streaming chunks and remains backward compatible with existing integrations. Use it for chat UIs, long responses, and agent services that should start sending output before the full answer is complete.

```python
for chunk in agent.run("Write a short report about AI agents.", stream=True):
    print(chunk)
```

### 7. Agent Self-Learning
Self-learning can be combined with a memory backend so an agent can retain scenario-specific knowledge across users or sessions. In production, pair self-learning with `MemoryPolicy` so low-quality, private, expired, or unrelated content does not enter long-term memory.

Recommended production controls:

- Use `namespace` to separate tenants or environments.
- Use `allowed_sources`, `allowed_scopes`, and `allowed_agent_names` to limit retrieved memory.
- Use `memory_write_admission`, `reject_write_patterns`, `min_write_length`, and `reject_duplicate_writes` to control writes.
- Use `enforce_expires_at=True` when memory records carry expiration metadata.

### 8. Langfuse Log Tracking
LightAgent can send trace data to Langfuse through `tracetools` configuration. For most local debugging, start with built-in trace events:

```python
result = agent.run("Debug this workflow.", result_format="object", trace=True)
print(result.trace_id)
print(agent.export_trace())
```

See [Trace Observability](docs/tracing.md) for event shapes and production debugging guidance.

### 9. Agent Assessment
Agent assessment is planned for future versions and will focus on evaluating agent behavior against business scenarios.

### 10. LightFlow Workflows
`LightFlow` is the deterministic workflow layer. Use it when a task should run through known steps instead of relying on free-form agent planning.

Key v0.9.0 workflow controls:

- Step states: `pending`, `running`, `success`, `failed`, `skipped`, `waiting_approval`.
- DAG validation: `flow.validate(strict=True)` checks unknown dependencies, cycles, and isolated steps.
- Step controls: `timeout`, `max_retry`, `cancel_if`, `fallback_agent`, `requires_approval`, and `approval_handler`.
- Persistence: `JsonLightFlowStore` stores run records and checkpoints.
- Recovery: `flow.resume(run_id)` continues incomplete runs; `flow.rerun_step(run_id, step_name)` reruns one step and downstream steps.
- Inspection: `flow.get_run(run_id)` and `flow.list_runs()` expose workflow state for UIs.

```python
from LightAgent import JsonLightFlowStore, LightAgent, LightFlow

store = JsonLightFlowStore(".lightflow_runs")
draft_agent = LightAgent(model="gpt-4.1", api_key="your_api_key", base_url="your_base_url")
review_agent = LightAgent(model="gpt-4.1", api_key="your_api_key", base_url="your_base_url")
backup_agent = LightAgent(model="gpt-4.1", api_key="your_api_key", base_url="your_base_url")

def approve(step, context):
    return {"approved": True, "reason": "Approved by policy."}

flow = (
    LightFlow(store=store)
    .step("draft", agent=draft_agent, timeout=30, max_retry=2)
    .step(
        "review",
        agent=review_agent,
        depends_on=["draft"],
        requires_approval=True,
        approval_handler=approve,
        fallback_agent=backup_agent,
    )
)

validation = flow.validate(strict=True)
if validation["errors"]:
    raise ValueError(validation["errors"])

result = flow.run("Prepare a customer support summary.", run_id="case-001", trace=True)
record = flow.get_run("case-001")
```

See [LightFlow](docs/lightflow.md) for complete workflow examples.

### 11. Guardrails
Guardrails are lightweight policy hooks around agent execution:

- Input guardrails inspect the user query before model execution.
- Tool guardrails inspect tool calls before execution.
- Output guardrails inspect or redact final non-streaming output.

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
        high_risk_parameter_guardrail({
            "amount": lambda value: value is not None and float(value) <= 1000,
        }),
    ],
    output_guardrails=[output_redaction_guardrail()],
)
```

Use default guardrail templates for privacy-sensitive input, sensitive tool confirmation, high-risk parameter validation, and output redaction. See [Guardrails](docs/guardrails.md).

### 12. Runtime Hooks
Runtime hooks are ordered middleware for production policies that need to observe, replace, or block lifecycle payloads without changing the default `agent.run()` behavior.

```python
from LightAgent import HookDecision, LightAgent


def redact_before_model(ctx):
    if ctx.phase != "before_model_request":
        return None

    params = dict(ctx.payload["params"])
    messages = list(params["messages"])
    messages[-1] = {
        **messages[-1],
        "content": messages[-1]["content"].replace("secret-token", "[REDACTED]"),
    }
    params["messages"] = messages
    return HookDecision.replace({"params": params})


def block_dangerous_tool(ctx):
    if ctx.phase == "before_tool_call" and ctx.payload["tool_name"] == "delete_file":
        return HookDecision.block("delete_file requires manual approval")
    return None


agent = LightAgent(
    model="gpt-4.1",
    api_key="your_api_key",
    base_url="your_base_url",
    hooks=[redact_before_model, block_dangerous_tool],
)

result = agent.run("Summarize this secret-token safely.", result_format="object", trace=True)
print(result.content)
print(result.trace)
```

Hooks can target `before_run`, `before_model_request`, `after_model_response`, `before_tool_call`, `after_tool_result`, `before_memory_write`, and `after_memory_write`. `LightFlow(hooks=[...])` also supports step lifecycle hooks such as `before_flow_step`, `after_flow_step`, `on_approval_required`, `on_resume`, and `on_rerun`. See [Runtime Hooks](docs/runtime_hooks.md).

### 13. SharedMemoryPool
`SharedMemoryPool` is an in-memory shared memory prototype for multi-agent experiments. It is append-first and keeps provenance metadata, making it useful for testing how multiple agents share information before adopting a durable vector or graph memory backend.

Use it with `MemoryPolicy` so each agent retrieves only memory that matches the expected namespace, source, scope, trust, confidence, or agent name.

## Mainstream Agent Model Support

LightAgent works with OpenAI-compatible chat completion endpoints, including OpenAI, OpenRouter, Zhipu ChatGLM, DeepSeek, Qwen, StepFun, Moonshot/Kimi, MiniMax, vLLM, llama.cpp, Ollama-compatible endpoints, and self-hosted gateways.

For provider-specific parameters, base URLs, local model setup, and troubleshooting, see [Model Provider Configuration](docs/model_providers.md).

---

## Use Cases

- **Intelligent Customer Service**: Provide efficient customer support through multi-turn dialogue and tool integration.
- **Data Analysis**: Use Tree of Thought and multi-agent collaboration to handle complex data analysis tasks.
- **Automated Tools**: Quickly build customized tools through automated tool generation.
- **Educational Assistance**: Provide personalized learning experiences using memory modules and streaming API.

---
 
## 🛠️ Contribution Guidelines

We welcome any form of contribution! Whether it's code, documentation, tests, or feedback, it's a tremendous help to the project. If you have great ideas or find bugs, please submit an Issue or Pull Request. Here are the contribution steps:

1. **Fork this project**: Click the `Fork` button at the top right corner to copy the project to your GitHub repository.
2. **Create a branch**: Create your development branch locally:  
   ```bash
   git checkout -b feature/YourFeature
   ```
3. **Submit changes**: After finishing development, submit your changes:  
   ```bash
   git commit -m 'Add some feature'
   ```
4. **Push the branch**: Push the branch to your remote repository:  
   ```bash
   git push origin feature/YourFeature
   ```
5. **Submit Pull Request**: Submit a Pull Request on GitHub and describe your changes.

We will review your contributions promptly. Thank you for your support! ❤️

---

## 🙏 Acknowledgments

Shanghai Wanxing AI and Professor Zhang Liwen's research group from the School of Statistics and Data Science at Shanghai University of Finance and Economics have jointly open-sourced a new generation intelligent agent framework called LightAgent.The development and implementation of LightAgent owe much to the inspiration and support from the following open-source projects, especially the outstanding projects and teams:

- **MCP**: Thanks to [mcp](https://modelcontextprotocol.io/introduction) for providing the **Model Context Protocol (MCP)**, which offers a standardized infrastructure for the **dynamic tool integration** of LightAgent.
- **mem0**: Thanks to [mem0](https://github.com/mem0ai/mem0) for providing the memory module, which offers strong support for LightAgent's context management.  
- **Swarm**: Thanks to [Swarm](https://github.com/openai/swarm) for designing ideas for multi-agent collaboration, laying the groundwork for LightAgent's multi-agent features.  
- **ChatGLM3**: Thanks to [ChatGLM3](https://github.com/THUDM/ChatGLM3) for providing high-performance Chinese large model support and design inspiration.  
- **Qwen**: Thanks to [Qwen](https://github.com/QwenLM/Qwen) for providing high-performance Chinese large model support.  
- **DeepSeek-V3**: Thanks to [DeepSeek-V3](https://github.com/deepseek-ai/DeepSeek-V3) for providing high-performance Chinese large model support.  
- **StepFun**: Thanks to [step](https://www.stepfun.com/) for providing high-performance Chinese large model support.  

---

## 📄 License

LightAgent is licensed under the [Apache 2.0 License](LICENSE). You can freely use, modify, and distribute this project, but please adhere to the terms of the license.

---

## 📬 Contact Us

If you have any questions or suggestions, please feel free to contact Wanxing AI or Professor Zhang Liwen from the School of Statistics and Data Science at Shanghai University of Finance and Economics:

- **Wanxing AI Email**: service@wanxingai.com 
- **Professor Zhang Liwen Email**: zhang.liwen@shufe.edu.cn
- **GitHub Issues**: [https://github.com/wanxingai/LightAgent/issues](https://github.com/wanxingai/LightAgent/issues)  

We look forward to your feedback and work together to make LightAgent even stronger! 🚀

---

<p align="center">
  <strong>LightAgent - Making intelligence lighter, making the future simpler.</strong> 🌈
</p>

**LightAgent** —— A lightweight, flexible, and powerful active Agent framework that assists you in quickly building intelligent applications!

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=wanxingai/LightAgent&type=Date)](https://star-history.com/#wanxingai/LightAgent&Date)

## Paper

```bibtex
@misc{2509.09292,
Author = {Weige Cai and Tong Zhu and Jinyi Niu and Ruiqi Hu and Lingyao Li and Tenglong Wang and Xiaowu Dai and Weining Shen and Liwen Zhang},
Title = {LightAgent: Production-level Open-source Agentic AI Framework},
Year = {2025},
Eprint = {arXiv:2509.09292},
Eprinttype = {arXiv},
Eprintclass = {cs.AI},
Url = {https://arxiv.org/abs/2509.09292},
Doi = {10.48550/arXiv.2509.09292},
Note = {Submitted on 11 Sep 2025}
}
```

## Security
[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/wanxingai-lightagent-badge.png)](https://mseep.ai/app/wanxingai-lightagent)
