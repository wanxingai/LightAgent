## Runtime Hooks

LightAgent v0.9.1 introduced a small ordered hook layer for policy, audit,
redaction, routing, and payload mutation without changing the default
`agent.run()` behavior. LightAgent v0.9.2 completes the core agent lifecycle
with run-end, error, and memory-read hooks.

Hooks can be plain callables or objects with methods named after a lifecycle
phase. A hook receives a `HookContext` and may return:

| Return value | Meaning |
| --- | --- |
| `None` | Continue with the current payload. |
| `HookDecision.continue_()` | Continue explicitly, optionally with metadata. |
| `HookDecision.replace(payload)` | Replace the phase payload. |
| `HookDecision.block(reason)` | Stop the phase with an `LA-HOOK` error. |
| `dict` | Compatible shorthand for `payload`, `action`, `reason`, and `metadata`. |

### Agent Hooks

```python
from LightAgent import HookDecision, LightAgent


def redact_before_model(ctx):
    if ctx.phase != "before_model_request":
        return None

    params = dict(ctx.payload["params"])
    messages = list(params["messages"])
    messages[-1] = {
        **messages[-1],
        "content": messages[-1]["content"].replace("secret", "[REDACTED]"),
    }
    params["messages"] = messages
    return HookDecision.replace({"params": params})


agent = LightAgent(
    model="gpt-4.1",
    api_key="your_api_key",
    base_url="your_base_url",
    hooks=[redact_before_model],
)
```

Supported first-slice phases:

| Phase | Payload |
| --- | --- |
| `before_run` | Query, runtime tools, stream mode, result format, and metadata. |
| `after_run` | Final success flag, content, error, stage, and run metadata. |
| `on_error` | Error stage, error text, success flag, and phase-specific context. |
| `before_model_request` | OpenAI-compatible request params. |
| `after_model_response` | Final non-streaming model content before output guardrails. |
| `before_tool_call` | Tool name and parsed arguments. |
| `after_tool_result` | Tool name and tool output. |
| `before_memory_retrieve` | Query, target memory user id, original user id, source, and scope. |
| `after_memory_retrieve` | Retrieved memory payload before final `MemoryPolicy` filtering. |
| `before_memory_write` | Memory data, source, scope, and target user id. |
| `after_memory_write` | Stored data, metadata, source, scope, and target user id. |

### LightFlow Hooks

`LightFlow(hooks=[...])` supports:

| Phase | Usage |
| --- | --- |
| `before_flow_step` | Validate, replace, or block a step query before execution. |
| `after_flow_step` | Audit or export a completed step result. |
| `on_approval_required` | Notify an external approval system. |
| `on_resume` | Inspect a checkpoint before resume. |
| `on_rerun` | Inspect a checkpoint before rerunning one step and downstream steps. |

### Streaming Tool Loop Errors

Streaming tool-call loops are bounded by `max_tool_iterations`. When the limit
is reached, LightAgent closes the run through the normal lifecycle, so
`on_error`, `after_run`, and `run_end` trace events stay consistent.

```python
def alert_tool_loop(ctx):
    if ctx.phase != "on_error":
        return None
    if ctx.payload.get("stage") == "max_tool_iterations":
        alert({
            "trace_id": ctx.trace_id,
            "run_id": ctx.run_id,
            "error": ctx.payload.get("error"),
            "message": ctx.payload.get("message"),
        })
    return None


agent = LightAgent(
    model="gpt-4.1",
    api_key="your_api_key",
    base_url="your_base_url",
    hooks=[alert_tool_loop],
)

stream = agent.run(
    "run a tool-heavy task",
    tools=[some_tool],
    stream=True,
    max_retry=3,
    max_tool_iterations=2,
)
```

### Trace Integration

When tracing is enabled, hook replacements, blocks, metadata events, and hook
failures are recorded as `hook_decision` or `hook_block` events. Hook failures
are isolated by default so observability hooks do not crash an agent run.

Use `parent_trace_id` and `run_group_id` to connect sibling runs:

```python
result = agent.run(
    "child task",
    result_format="object",
    trace=True,
    parent_trace_id="parent-trace",
    run_group_id="workflow-42",
)
```

`LightFlow` automatically passes the flow trace as the parent trace for each
step agent run.

For practical production patterns, see [Runtime Hook Recipes](runtime_hook_recipes.md).
