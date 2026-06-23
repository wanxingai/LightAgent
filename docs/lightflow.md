## LightFlow

LightAgent v0.8.0 introduces `LightFlow`, a lightweight deterministic workflow
runner for chaining multiple `LightAgent` instances into explicit steps.

`LightFlow` is intentionally small: it provides DAG-style dependencies, step
input/output passing, step retries, step status tracking, checkpointable run
records, and flow-level trace events without adding a heavy orchestration
dependency.

See `example/10.lightflow.py` for a complete runnable example.

### Basic Usage

```python
from LightAgent import LightAgent, LightFlow

research_agent = LightAgent(
    name="ResearchAgent",
    model="gpt-4.1",
    api_key="your_api_key",
    base_url="your_base_url",
)

writer_agent = LightAgent(
    name="WriterAgent",
    model="gpt-4.1",
    api_key="your_api_key",
    base_url="your_base_url",
)

flow = (
    LightFlow()
    .step("research", agent=research_agent)
    .step("write", agent=writer_agent, depends_on=["research"])
)

result = flow.run("Analyze this company", trace=True)

print(result.content)
print(result.success)
print(result.trace)
```

When a step depends on previous steps and does not define a custom query,
LightFlow appends the dependency outputs to the original input.

### Custom Step Input

Use a callable `query` when a step needs precise control over its prompt.

```python
flow = (
    LightFlow()
    .step("research", agent=research_agent)
    .step(
        "write",
        agent=writer_agent,
        depends_on=["research"],
        query=lambda context: f"Write a concise report from: {context['outputs']['research']}",
    )
)
```

The callable receives a context dictionary:

| Key | Meaning |
| --- | --- |
| `input` | The original flow input. |
| `outputs` | Mapping of completed step name to string output. |
| `steps` | Mapping of completed step name to `LightFlowStepResult`. |

### Step Retries

Each step can retry when the underlying agent returns a structured error.

```python
flow.step("research", agent=research_agent, max_retry=2)
```

Retries are step-local. If a step still fails after its retries, the flow stops
and returns a `LightFlowResult` with `success == False`.

### Step Status And Controls

Each `LightFlowStepResult` includes a `status` value:

| Status | Meaning |
| --- | --- |
| `pending` | Step has not started yet. |
| `running` | Step is currently executing. |
| `success` | Step completed successfully. |
| `failed` | Step failed after retries and fallback handling. |
| `skipped` | Step did not run because the flow was cancelled or a dependency failed. |
| `waiting_approval` | Step requires human approval before execution. |

Steps support timeout, cancellation, fallback agents, and approval handlers:

```python
flow.step(
    "review",
    agent=review_agent,
    depends_on=["draft"],
    timeout=30,
    fallback_agent=fallback_review_agent,
    requires_approval=True,
    approval_handler=lambda step, context: True,
)
```

Use `flow.validate()` to inspect workflow structure before execution. Unknown
dependencies and cycles are reported as errors. Isolated steps are reported as
warnings so they can be reviewed without blocking simple workflows.

### Result Formats

The default result is a `LightFlowResult` object:

```python
result = flow.run("Analyze this company")
print(result.content)
print(result.steps[0].content)
print(result.error)
```

You can also request a string or dictionary:

```python
text = flow.run("Analyze this company", result_format="str")
data = flow.run("Analyze this company", result_format="dict")
```

### Trace Events

Pass `trace=True` to collect flow-level events:

| Event | Meaning |
| --- | --- |
| `flow_start` | The flow started. |
| `step_start` | A step started. |
| `step_end` | A step completed or failed. |
| `flow_end` | The flow completed or stopped on failure. |

Each step also preserves the underlying agent trace when the agent returns a
structured `RunResult`.

`step_end` events include status, attempts, retry count, error reason, duration,
input summary, output summary, and whether a fallback agent was used.

### Persistent Runs

Use `JsonLightFlowStore` to persist checkpoints and inspect workflow run
records:

```python
from LightAgent import JsonLightFlowStore, LightFlow

store = JsonLightFlowStore(".lightflow_runs")

flow = (
    LightFlow(store=store)
    .step("research", agent=research_agent)
    .step("write", agent=writer_agent, depends_on=["research"])
)

result = flow.run("Analyze this company", run_id="report-001")

if not result.success:
    result = flow.resume("report-001")
```

For a selected step and its downstream dependencies:

```python
result = flow.rerun_step("report-001", "write")
```

Use `get_run(run_id)` and `list_runs()` to build front-end execution views.

### Current Scope

The v0.9.0 implementation provides lightweight JSON checkpoints and run
records. Production deployments that need database-backed locking,
distributed workers, or strong idempotency should provide a stronger run-store
adapter around the same record shape.
