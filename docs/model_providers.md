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

### LiteLLM (multi-provider routing)

LiteLLM provides a unified interface to 100+ LLM providers through a single SDK.
LightAgent supports LiteLLM as an optional provider backend via the `provider`
parameter. When you pass `provider="litellm"`, all chat completion calls are
routed through the LiteLLM SDK instead of the default OpenAI client.

**Installation**

```bash
pip install "LightAgent[litellm]"
```

**Usage**

```python
from LightAgent import LightAgent

agent = LightAgent(
    model="gpt-4.1",
    provider="litellm",
    api_key="your_api_key",
)
```

When `provider` is set to `"litellm"`, LightAgent creates a `LiteLLMClient`
wrapper that exposes the same `client.chat.completions.create(**params)`
interface. You can use any model name that LiteLLM supports, including models
from Anthropic, Google, Azure, AWS Bedrock, Together AI, and more, without
changing your code.

**Model routing**

- `model` can be any LiteLLM-supported model string (e.g. `"claude-sonnet-4-20250514"`,
  `"gemini/gemini-2.5-flash"`, `"together_ai/meta-llama/Llama-4-70B"`).
- `api_key` and `base_url` are forwarded to the LiteLLM completion call as
  `api_key` and `api_base` respectively. If `base_url` is the default
  `https://api.openai.com/v1`, it is omitted so LiteLLM can use its built-in
  provider routing.
- The `drop_params` flag is enabled to allow provider-specific parameters to be
  safely ignored when they do not apply to the target provider.

For a full list of supported models and providers, see the
[LiteLLM documentation](https://docs.litellm.ai/docs/providers).

### Troubleshooting

- If you see `[LA-401]`, check the API key or provider account.
- If you see `[LA-404]`, check `base_url` and the exact `model` name.
- If you see `[LA-413]`, reduce history, prompt size, or tool output.
- If a local model is slow, test the same request directly against the local
  server first, then reduce context size or choose a smaller model.
