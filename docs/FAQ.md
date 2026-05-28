## FAQ

### What is LightAgent?

LightAgent is a lightweight Python agent framework for building tool-using agents, memory-enabled agents, Tree-of-Thought workflows, MCP integrations, and LightSwarm multi-agent collaboration. It uses OpenAI-compatible chat completion APIs, so it can work with OpenAI and compatible providers by configuring `model`, `api_key`, and `base_url`.

### How is LightAgent different from LangChain or CrewAI?

LightAgent focuses on a small core, direct Python tool registration, OpenAI-compatible streaming output, MCP tool integration, and a simple LightSwarm abstraction for multi-agent routing. It avoids requiring LangChain or LlamaIndex as core dependencies.

### How do I install LightAgent?

```bash
pip install lightagent
```

Memory examples that use Mem0 also require:

```bash
pip install mem0ai
```

### How do I create a basic agent?

```python
from LightAgent import LightAgent

agent = LightAgent(
    model="gpt-4.1",
    api_key="your_api_key",
    base_url="your_base_url",
)

response = agent.run("Hello, who are you?")
print(response)
```

### Which model providers are supported?

LightAgent can use OpenAI-compatible chat completion endpoints. The README examples cover OpenAI, DeepSeek, Qwen, Zhipu ChatGLM, Baichuan, StepFun, and other compatible providers. For OpenRouter or a self-hosted gateway, set `base_url` to the provider's OpenAI-compatible endpoint. See [Model Provider Configuration](model_providers.md) for OpenRouter, vLLM, llama.cpp, and Ollama examples.

Example OpenRouter configuration:

```python
from LightAgent import LightAgent

agent = LightAgent(
    model="openai/gpt-4.1",
    api_key="your_openrouter_api_key",
    base_url="https://openrouter.ai/api/v1",
)
```

### Does LightAgent support local models?

Yes, when the local runtime exposes an OpenAI-compatible endpoint. For example, with vLLM use `base_url="http://localhost:8000/v1"`, with llama.cpp server mode use `base_url="http://localhost:8080/v1"`, and with Ollama's OpenAI-compatible API use `base_url="http://localhost:11434/v1"`. The `api_key` can be any non-empty value when the local server does not require authentication.

### How do I add a custom tool?

Define a Python function and attach `tool_info`, then pass the function through the `tools` argument.

```python
from LightAgent import LightAgent

def get_weather(city_name: str) -> str:
    return f"Query result: {city_name} is sunny."

get_weather.tool_info = {
    "tool_name": "get_weather",
    "tool_description": "Get current weather information for the specified city.",
    "tool_params": [
        {
            "name": "city_name",
            "description": "The city name to query",
            "type": "string",
            "required": True,
        },
    ],
}

agent = LightAgent(
    model="gpt-4.1",
    api_key="your_api_key",
    base_url="your_base_url",
    tools=[get_weather],
)

print(agent.run("Please check the weather in Shanghai."))
```

### Can tools be passed at runtime?

Yes. `run(..., tools=[...])` registers runtime tools into the active tool registry and dispatcher before the model request, so tools advertised for that run can also be executed when the model calls them.

### How do I troubleshoot model or tool errors?

LightAgent returns stable error codes such as `LA-401` for authentication errors, `LA-413` for oversized requests, `LA-429` for rate limits, `LA-JSON` for malformed tool arguments, and `LA-TOOL` for tool execution failures. See [Error Handling](error_handling.md) for the full taxonomy and troubleshooting guidance.

### Does `agent.run()` still return a string?

Yes. `agent.run("hello")` still returns a string by default, and `agent.run(query, stream=True, user_id=user_id)` still returns the legacy stream generator. Structured results are opt-in:

```python
result = agent.run("hello", result_format="object")
print(result.content)
print(result.tool_calls)
print(result.trace_id)
print(result.error)
```

For structured streaming events, use `result_format="event"` with `stream=True`.

### How do I inspect an agent run trace?

LightAgent v0.7.0 adds opt-in structured traces. Pass `trace=True` to collect
prompt-safe events for the latest run, including run start/end, model request
summaries, tool calls, tool results, and errors.

```python
result = agent.run("hello", result_format="object", trace=True)
print(result.trace)

for event in agent.export_trace():
    print(event["type"], event["data"])
```

Tracing is disabled by default, and model request trace events summarize counts
and tool names instead of storing full prompts or message history.

### How do I use browser-use with LightAgent?

Use `example/08.browser_use.py` as the reference implementation. For `browser-use` 0.11 and newer, LightAgent's example adds a compatibility `provider` attribute to `langchain_openai.ChatOpenAI` when needed. See [browser-use Integration](browser_use.md).

### What is the memory system?

LightAgent accepts a custom memory object through the `memory` parameter. The object should provide `store(data, user_id)` and `retrieve(query, user_id)` methods. The README includes a Mem0-based example, and other memory backends can be integrated by implementing the same small interface.

For shared or graph-backed memory deployments, review the [Memory Security Guidance](memory_security.md) before enabling cross-user persistence.

### What is Tree of Thought?

Tree of Thought is an optional planning and reflection mode enabled with `tree_of_thought=True`. It uses a reasoning model to create a tool-use plan and can filter tools before the final model call.

```python
agent = LightAgent(
    model="gpt-4.1",
    api_key="your_api_key",
    base_url="your_base_url",
    tree_of_thought=True,
    tot_model="deepseek-r1",
)
```

### What is LightSwarm?

LightSwarm is LightAgent's multi-agent collaboration helper. You register multiple `LightAgent` instances and run a selected agent through the swarm so tasks can be routed to specialized agents.

```python
from LightAgent import LightAgent, LightSwarm

swarm = LightSwarm()
support_agent = LightAgent(
    name="SupportAgent",
    role="Handle support questions.",
    model="gpt-4.1",
    api_key="your_api_key",
    base_url="your_base_url",
)

swarm.register_agent(support_agent)
response = swarm.run(support_agent, "Help me troubleshoot this issue.")
print(response)
```

### How do I use MCP tools?

Configure MCP server settings and call `setup_mcp()` before running the agent. LightAgent supports stdio and SSE MCP transports; see `mcp_release.md` and the examples under `mcp/` for complete configuration examples.

### How do I use Skills?

Skills are discovered from skill directories containing `SKILL.md` files. By default, LightAgent looks under `skills/` and can expose skill activation tools when skills are discovered. Keep skill instructions focused and pair them with normal Python tools when external actions are required.

### How do I enable streaming?

Pass `stream=True` to `run()`. The method returns a generator that yields model chunks and tool events.

```python
response = agent.run("Tell me a short story.", stream=True)
for chunk in response:
    print(chunk)
```

### Where should I start troubleshooting?

- For tool issues, confirm the tool has `tool_info`, is passed through `tools=[...]`, and the selected model supports tool calls.
- For memory issues, confirm your memory object implements both `store()` and `retrieve()` and that you pass a stable `user_id`.
- For multi-agent issues, see the [Multi-agent failure map](multi_agent_failure_map.md).
- For MCP issues, verify that the MCP server command or SSE endpoint starts independently before connecting it to LightAgent.

### Where can I get help?

- Documentation: https://sufe-aiflm-lab.github.io/LightAgent/
- Issues: https://github.com/wanxingai/LightAgent/issues
- PyPI: https://pypi.org/project/lightagent/
- Paper: https://arxiv.org/abs/2509.09292
