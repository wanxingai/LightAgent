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
| `approval_required` | A protected action is waiting for human review. |
| `approval_approve` / `approval_reject` / `approval_edit` | A human-review decision was applied. |
| `human_feedback` | A post-run rating or annotation was attached to the trace. |
| `hook_decision` | A runtime hook replaced a payload, blocked a phase, attached metadata, or failed in isolation. |
| `hook_block` | A runtime hook explicitly blocked a phase. |
| `error` | A model, JSON, tool, retry, or max-retry error occurred. |
| `run_end` | The run finished or failed. |

v0.9.6 adds latency, usage, retry, and review metadata. Model request events
include request indexes and provider-call latency. Tool result events include
execution latency. `run_end` includes total duration, request/tool counts,
retry count, and normalized usage when the provider returns it.

### Summaries And Exporters

Use the built-in aggregation API without changing the raw event format:

```python
summary = agent.summarize_trace(pricing={
    "input_per_million": 0.50,
    "output_per_million": 1.50,
})
print(summary.to_dict())
```

Export through a generic callable or the local JSONL exporter:

```python
from LightAgent import JsonlTraceExporter

agent.export_trace_to(
    JsonlTraceExporter(".lightagent/traces.jsonl"),
    metadata={"environment": "staging"},
)
```

Custom Langfuse, OpenTelemetry, data-warehouse, or audit-store adapters only
need an `export(events, summary, metadata)` method. This keeps external SDKs and
credentials outside the core tracing layer.

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

Each `agent.run(..., trace=True)` call creates its own `trace_id`. Pass
`parent_trace_id` and `run_group_id` when your application wants explicit trace
hierarchy:

```python
child = agent.run(
    "Summarize the approved step",
    result_format="object",
    trace=True,
    parent_trace_id=parent_result.trace_id,
    run_group_id="workflow-42",
)
```

Trace events include those fields when provided. `LightFlow` automatically
passes its flow trace as the parent trace for step agent runs.

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
