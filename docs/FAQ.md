## 📋 FAQ

### What is LightAgent?

LightAgent is an ultra-lightweight, open-source Python AI Agent framework with native Skills support. It enables you to build self-learning agents with persistent memory, tool integration, and tree-of-thought reasoning. Key features include LightSwarm for multi-agent collaboration, MCP protocol support, and OpenAI-compatible streaming APIs. The core code is only ~1000 lines with no LangChain/LlamaIndex dependencies.

### How does LightAgent differ from LangChain or CrewAI?

| Framework | Philosophy | Key Differentiator |
|-----------|-----------|-------------------|
| **LightAgent** | Ultra-lightweight, Skills-native | 1000-line core, no external dependencies, LightSwarm multi-agent, Tree-of-Thought, adaptive tool filtering (80% token reduction) |
| **LangChain** | Chain-based orchestration | Heavy dependency chain, complex abstraction layers |
| **CrewAI** | Role-playing agents | Actor-based, Crew concept for team collaboration |

LightAgent focuses on **minimal footprint, big potential** — lightweight design without sacrificing capabilities.

### How do I install LightAgent?

```bash
pip install lightagent
```

Optional: Install Mem0 for memory support:

```bash
pip install mem0ai
```

### What LLM providers does LightAgent support?

LightAgent is compatible with:
- **OpenAI** (GPT-4, GPT-3.5)
- **DeepSeek** (deepseek-r1 for ToT)
- **Qwen** (Qwen series, Qwen3 thinking mode)
- **Zhipu ChatGLM**
- **Baichuan Large Model**
- **StepFun**
- And other OpenAI-compatible APIs

Configure via `model`, `api_key`, and `base_url` parameters:

```python
agent = LightAgent(
    model="gpt-4.1",
    api_key="your_api_key",
    base_url="your_base_url"
)
```

### What is the Memory system?

LightAgent natively supports `mem0` for persistent, user-specific memory:
- Automatically manages conversation history
- Stores personalized user preferences
- Enables cross-session context retention
- Can use Qdrant as vector database backend

Enable memory with `CustomMemory()` class implementing `store()` and `retrieve()` methods.

### How do I add custom Tools?

Define tools as Python functions with `tool_info` attribute:

```python
def get_weather(city_name: str) -> str:
    """Get current weather for city"""
    return f"Query result: {city_name} is sunny."

get_weather.tool_info = {
    "tool_name": "get_weather",
    "tool_description": "Get current weather information.",
    "tool_params": [
        {"name": "city_name", "description": "City name", "type": "string", "required": True}
    ]
}

agent = LightAgent(model="gpt-4.1", api_key="...", tools=[get_weather])
```

LightAgent supports **unlimited tools** with adaptive filtering (reduces token consumption by 80%).

### What is Tree-of-Thought (ToT)?

ToT enables complex task decomposition and multi-step reasoning:
- Reflects on intermediate results
- Decomposes complex goals into subtasks
- Supports multi-tool planning
- Especially effective with DeepSeek-r1 model

Enable with `tree_of_thought=True` parameter.

### What is LightSwarm?

LightSwarm simplifies multi-agent collaboration:
- Intent recognition for task delegation
- Automatic routing to specialized agents
- Easier than Swarm framework implementation
- Handles user input intelligently across agents

Use LightSwarm for multi-agent scenarios where different agents handle different domains.

### What is MCP support?

LightAgent fully supports MCP (Model Context Protocol):
- Connects to MCP servers via stdio and SSE
- Integrates MCP tools seamlessly
- Enables tool sharing across agents
- Supports browser_use integration

See `mcp_release.md` for MCP integration details.

### What are Skills?

Skills (v0.6.0+) are reusable, composable capabilities:
- Task-oriented agent modules
- Persistent memory integration
- Tool use encapsulation
- Tree-of-thought reasoning built-in

Skills enable modular agent design with better maintainability.

### How do I use the Tool Generator?

Provide your API documentation to the Tool Generator:
- Automatically creates exclusive tools
- Build hundreds of custom tools in ~1 hour
- Reduces manual tool development effort

### How do I troubleshoot multi-agent issues?

Check the [Multi-agent failure map](docs/multi_agent_failure_map.md) for:
- Role drift symptoms
- Cross-agent memory issues
- Debug checklist
- Common failure patterns

### Where can I get help?

- **Documentation**: https://sufe-aiflm-lab.github.io/LightAgent/
- **Issues**: https://github.com/wanxingai/LightAgent/issues
- **Paper**: https://arxiv.org/abs/2509.09292
- **Community**: Active developer community for Q&A

---

