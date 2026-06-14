## Trace Observability

LightAgent v0.7.0 adds opt-in structured traces for debugging agent runs without
changing the default `agent.run()` return type.

### Enable Tracing

```python
from LightAgent import LightAgent

agent = LightAgent(
    model="gpt-4.1",
    api_key="your_api_key",
    base_url="your_base_url",
)

result = agent.run("Check the weather in Shanghai", result_format="object", trace=True)

print(result.content)
print(result.trace_id)
print(result.trace)
```

The same trace is available from the agent after the run:

```python
for event in agent.export_trace():
    print(event["type"], event["data"])
```

### Event Types

| Event | Meaning |
| --- | --- |
| `run_start` | A new run began. |
| `model_request` | A model request was made. The event stores a prompt-safe summary. |
| `model_response` | The model produced a final response. |
| `tool_call` | The model requested a tool call. |
| `tool_result` | A tool returned output. |
| `error` | A model, JSON, tool, retry, or max-retry error occurred. |
| `run_end` | The run finished or failed. |

### Compatibility

Tracing is disabled by default. Existing calls such as `agent.run("hello")` and
`agent.run(query, stream=True, user_id=user_id)` keep their legacy behavior.

For non-streaming diagnostics, use `result_format="object"`:

```python
result = agent.run("hello", result_format="object", trace=True)
assert result.trace
```

For legacy string results, use `agent.export_trace()` after the call:

```python
response = agent.run("hello", trace=True)
trace_events = agent.export_trace()
```

### Nested Runs And Delegation

Each `agent.run(..., trace=True)` call creates its own root `trace_id`. A
reflection run, LightSwarm delegated run, or LightFlow step should be treated as
a sibling trace unless your application records a `parent_trace_id` externally
or in memory metadata.

LightAgent does not currently fold delegated LightSwarm traces into the parent
trace automatically. See
[Memory, Trace, And Swarm Boundaries](memory_trace_swarm_boundaries.md) for the
recommended metadata convention.

### Privacy Notes

Trace model request events intentionally store only request summaries, including
model name, stream mode, message count, and tool names. They do not include the
full system prompt or full message history. Tool arguments and outputs are
captured because they are often needed to debug tool behavior, so avoid enabling
tracing for sensitive workloads unless your application can handle that data.
