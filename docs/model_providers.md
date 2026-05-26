## Model Provider Configuration

LightAgent uses OpenAI-compatible chat completion APIs. Most cloud gateways and
local runtimes work by setting three values:

- `model`: the provider-specific model name
- `api_key`: the provider key, or any non-empty value for local servers that do
  not require authentication
- `base_url`: the OpenAI-compatible API root, usually ending in `/v1`

### OpenRouter

```python
from LightAgent import LightAgent

agent = LightAgent(
    model="openai/gpt-4.1",
    api_key="your_openrouter_api_key",
    base_url="https://openrouter.ai/api/v1",
)

print(agent.run("Who are you?"))
```

OpenRouter model names are provider-routed strings such as
`openai/gpt-4.1`, `anthropic/claude-sonnet-4`, or another model listed in your
OpenRouter account.

### vLLM

Start vLLM with its OpenAI-compatible server, then use its `/v1` endpoint:

```bash
vllm serve Qwen/Qwen2.5-7B-Instruct --host 0.0.0.0 --port 8000
```

```python
from LightAgent import LightAgent

agent = LightAgent(
    model="Qwen/Qwen2.5-7B-Instruct",
    api_key="local",
    base_url="http://localhost:8000/v1",
)
```

### llama.cpp

Run llama.cpp in server mode with an OpenAI-compatible endpoint:

```bash
llama-server -m ./models/model.gguf --host 0.0.0.0 --port 8080
```

```python
from LightAgent import LightAgent

agent = LightAgent(
    model="local-model",
    api_key="local",
    base_url="http://localhost:8080/v1",
)
```

### Ollama OpenAI-Compatible Endpoint

Recent Ollama versions expose an OpenAI-compatible `/v1` API:

```python
from LightAgent import LightAgent

agent = LightAgent(
    model="llama3.1",
    api_key="ollama",
    base_url="http://localhost:11434/v1",
)
```

### Troubleshooting

- If you see `[LA-401]`, check the API key or provider account.
- If you see `[LA-404]`, check `base_url` and the exact `model` name.
- If you see `[LA-413]`, reduce history, prompt size, or tool output.
- If a local model is slow, test the same request directly against the local
  server first, then reduce context size or choose a smaller model.
