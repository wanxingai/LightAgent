## browser-use Integration

The `browser-use` package can be used as a LightAgent tool for browser-based
data collection. With `browser-use` 0.11 and newer, some versions expect the
LangChain chat model object to expose a `provider` attribute. Older
`langchain_openai.ChatOpenAI` objects may not provide that attribute.

LightAgent examples include a small compatibility helper:

```python
def ensure_browser_use_provider(llm, provider: str = "openai"):
    if hasattr(llm, "provider"):
        return llm
    try:
        setattr(llm, "provider", provider)
    except Exception:
        object.__setattr__(llm, "provider", provider)
    return llm
```

Use it when constructing the browser-use agent:

```python
import os
from browser_use import Agent
from langchain_openai import ChatOpenAI

llm = ensure_browser_use_provider(ChatOpenAI(
    model=os.getenv("BROWSER_USE_MODEL", "gpt-4.1-mini"),
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
))

browser_agent = Agent(
    task="Search for the current weather in Shanghai.",
    llm=llm,
    use_vision=False,
)
```

### Notes

- Prefer reading API keys from environment variables in new examples. Existing
  reusable tools may keep an `api_key` parameter for backward compatibility.
- Keep browser tasks narrow and explicit. Browser automation is slower and more
  failure-prone than direct API tools.
- If `browser-use` changes its LLM adapter requirements, update the helper in
  the example and any project-specific browser tools that construct `ChatOpenAI`.
