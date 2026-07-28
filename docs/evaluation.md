## Evaluation Harness

LightAgent v0.9.6 includes a dependency-free evaluation harness for fixed agent
and LightFlow regression cases. It uses structured results and traces, so it can
measure behavior without a hosted evaluation service.

### Basic Evaluation

```python
from LightAgent import EvaluationCase, LightEvaluator

cases = [
    EvaluationCase(
        name="weather tool",
        query="What is the weather in Shanghai?",
        expected_output_contains=("Shanghai",),
        expected_tools=("get_weather",),
        expected_trace_events=("tool_result", "run_end"),
        max_latency_ms=5000,
    ),
]

report = LightEvaluator().run(agent, cases)

print(report.pass_rate)
print(report.to_dict())
```

The evaluator enables `result_format="object"` and `trace=True` by default.
Use `run_kwargs` when a case needs a user, runtime tools, or another run option:

```python
EvaluationCase(
    name="tenant memory policy",
    query="Recall my account note",
    expected_trace_events=("memory_retrieve",),
    run_kwargs={
        "user_id": "alice",
        "metadata": {"tenant": "acme"},
    },
)
```

### Supported Assertions

| Field | Check |
| --- | --- |
| `expected_output_contains` | Every substring must occur in the final content. |
| `expected_tools` | Every named tool must appear in a `tool_call` event. |
| `forbidden_tools` | Named tools must not be called. |
| `expected_trace_events` | Required lifecycle, policy, memory, or review events. |
| `expect_success` | Whether the structured result should have no error. |
| `max_latency_ms` | End-to-end case latency budget. |
| `require_recovery` | The run must succeed after at least one traced retry. |
| `checks` | Application-defined callables for domain assertions. |

Custom checks receive `(result, trace)`. Return `True` or `None` to pass,
`False` to fail with a generic message, or a string to provide the failure
reason.

```python
def no_private_output(result, trace):
    if "customer-secret" in result.content:
        return "private marker leaked into output"
    return True
```

### Usage And Cost

Pass per-million-token rates when a provider returns usage:

```python
evaluator = LightEvaluator(pricing={
    "input_per_million": 0.50,
    "output_per_million": 1.50,
})
```

Each case includes a `TraceSummary` with model and tool counts, latency, retry
and error categories, review-event counts, normalized usage, and estimated
cost. Cost is an estimate supplied by the application, not a billing record.

### CI Usage

Keep CI cases deterministic. Use fake model clients and fake tools for normal
pull-request checks, then run real-provider or real-memory integration cases in
an opt-in or scheduled workflow. This keeps the default suite fast and avoids
committed credentials or network-dependent failures.
