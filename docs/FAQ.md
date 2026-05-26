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

LightAgent can use OpenAI-compatible chat completion endpoints. The README examples cover OpenAI, DeepSeek, Qwen, Zhipu ChatGLM, Baichuan, StepFun, and other compatible providers. For OpenRouter or a self-hosted gateway, set `base_url` to the provider's OpenAI-compatible endpoint.

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

Yes, when the local runtime exposes an OpenAI-compatible endpoint. For example, with a local gateway, Ollama-compatible proxy, or vLLM server, pass the endpoint through `base_url` and use the matching model name.

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

The public API accepts `run(..., tools=[...])`, but runtime tool dispatch needs to be validated against the installed LightAgent version. If a runtime tool is advertised to the model but not registered with the dispatcher, the model may call a tool that cannot be executed. Prefer constructor-level `tools=[...]` until your version includes the runtime dispatch fix.

### What is the memory system?

LightAgent accepts a custom memory object through the `memory` parameter. The object should provide `store(data, user_id)` and `retrieve(query, user_id)` methods. The README includes a Mem0-based example, and other memory backends can be integrated by implementing the same small interface.

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
