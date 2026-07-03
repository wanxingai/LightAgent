## Runtime Hook Recipes

These recipes show common production uses for `LightAgent(..., hooks=[...])`.
Each hook can return `None`, `HookDecision.continue_()`,
`HookDecision.replace(payload)`, or `HookDecision.block(reason)`.

### PII Redaction Before Model Calls

```python
import re

from LightAgent import HookDecision


def redact_pii(ctx):
    if ctx.phase != "before_model_request":
        return None

    params = dict(ctx.payload["params"])
    messages = list(params["messages"])
    redacted = []
    for message in messages:
        content = message.get("content", "")
        content = re.sub(r"[\w.+-]+@[\w.-]+", "[redacted-email]", str(content))
        redacted.append({**message, "content": content})
    params["messages"] = redacted
    return HookDecision.replace({"params": params})
```

### Cost Budget Enforcement

```python
from LightAgent import HookDecision


def token_budget(max_messages=12):
    def hook(ctx):
        if ctx.phase != "before_model_request":
            return None
        message_count = len(ctx.payload["params"].get("messages", []))
        if message_count > max_messages:
            return HookDecision.block("message budget exceeded")
        return None

    return hook
```

### Model Routing

```python
from LightAgent import HookDecision


def route_small_tasks(ctx):
    if ctx.phase != "before_model_request":
        return None

    params = dict(ctx.payload["params"])
    user_text = params["messages"][-1]["content"]
    if len(user_text) < 120:
        params["model"] = "gpt-4o-mini"
    return HookDecision.replace({"params": params})
```

### Tool Allow/Deny Audit

```python
from LightAgent import HookDecision


def tool_policy(allowed_tools):
    allowed = set(allowed_tools)

    def hook(ctx):
        if ctx.phase != "before_tool_call":
            return None
        tool_name = ctx.payload["tool_name"]
        if tool_name not in allowed:
            return HookDecision.block(f"tool `{tool_name}` is not allowed")
        return HookDecision.continue_(metadata={"audited_tool": tool_name})

    return hook
```

### Memory Retrieve Filtering

```python
from LightAgent import HookDecision


def filter_low_confidence_memory(ctx):
    if ctx.phase != "after_memory_retrieve":
        return None

    memories = dict(ctx.payload["memories"])
    memories["results"] = [
        item for item in memories.get("results", [])
        if item.get("metadata", {}).get("confidence", 1.0) >= 0.7
    ]
    return HookDecision.replace({**ctx.payload, "memories": memories})
```

### Langfuse Or OpenTelemetry Export

```python
def export_hook(exporter):
    def hook(ctx):
        if ctx.phase in {"after_run", "on_error", "after_tool_result"}:
            exporter.record({
                "phase": ctx.phase,
                "trace_id": ctx.trace_id,
                "run_id": ctx.run_id,
                "agent_name": ctx.agent_name,
                "payload": ctx.payload,
            })
        return None

    return hook
```

### Evaluation Sampling After Run

```python
import random


def sample_for_eval(queue, rate=0.05):
    def hook(ctx):
        if ctx.phase != "after_run" or not ctx.payload.get("success"):
            return None
        if random.random() <= rate:
            queue.append({
                "trace_id": ctx.trace_id,
                "content": ctx.payload.get("content"),
                "metadata": ctx.metadata,
            })
        return None

    return hook
```

### Async Hook

```python
from LightAgent import HookDecision


async def async_policy(ctx):
    if ctx.phase != "before_model_request":
        return None

    allowed = await check_external_policy(ctx.user_id, ctx.payload["params"])
    if not allowed:
        return HookDecision.block("external policy rejected request")
    return None
```

`HookManager` runs async hooks automatically, including when the caller is
already inside an event loop.
