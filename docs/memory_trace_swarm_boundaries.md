## Memory, Trace, And Swarm Boundaries

LightAgent v0.8.1 documents a clear boundary between three layers that often
interact in long-lived agents:

| Layer | Lifetime | Recommended Storage |
| --- | --- | --- |
| Trace | One run | Trace recorder or external observability backend |
| User memory | Cross-session | Memory backend scoped by user or tenant |
| Agent reflection memory | Cross-run or cross-session | Separate agent/reflection scope |
| LightSwarm delegation state | One task or workflow | Caller-managed task state or trace metadata |

Do not store trace summaries, tool logs, or self-reflection outputs as ordinary
user memories unless your application intentionally promotes them.

### MemoryScope Metadata

`MemoryScope` is a small metadata convention that memory adapters can use when
they support provenance fields.

```python
from LightAgent import MemoryScope

metadata = MemoryScope.user(
    agent_name="support-agent",
    trace_id="trace-123",
    project_id="customer-helpdesk",
).to_metadata()
```

For self-reflection or agent-private memories:

```python
metadata = MemoryScope.reflection(
    agent_name="planner-agent",
    trace_id="reflection-trace",
    parent_trace_id="user-run-trace",
).to_metadata()
```

Recommended fields:

| Field | Meaning |
| --- | --- |
| `source` | `user`, `agent`, `tool`, `trace`, `reflection`, or `swarm` |
| `scope` | `user`, `agent`, `session`, `flow`, `swarm`, or `project` |
| `agent_name` | Agent that wrote or owns the memory |
| `trace_id` | Run that produced the memory |
| `parent_trace_id` | Parent user-facing run when this came from reflection/delegation |
| `confidence` | Optional numeric confidence |
| `trust_level` | Optional trust tier such as `verified`, `user`, or `system` |

The core `MemoryProtocol` remains `store(data, user_id)` and
`retrieve(query, user_id)` for compatibility. Adapters that support metadata can
store this shape internally.

### Filtering Retrieved Memories

Use `MemoryPolicy` to keep reflection, trace, or cross-agent memories out of the
user-facing context.

```python
from LightAgent import LightAgent, MemoryPolicy

agent = LightAgent(
    model="gpt-4.1",
    api_key="your_api_key",
    base_url="your_base_url",
    memory=memory_backend,
    memory_policy=MemoryPolicy(
        namespace="tenant-a",
        allow_unattributed_results=False,
        allowed_sources=("user",),
        allowed_scopes=("user",),
        allowed_agent_names=("support-agent",),
        allowed_trust_levels=("verified", "user"),
        min_confidence=0.7,
    ),
)
```

When filters such as `allowed_sources` are configured, memories missing that
metadata are rejected. This is intentional: strict shared-memory deployments
should not inject unknown-origin records into the prompt.

### Trace Hierarchy

Each `agent.run(..., trace=True)` call creates its own `trace_id`. If your
application launches a reflection run or a delegated sub-agent run, treat it as
a sibling trace by default.

If you need hierarchy, pass and store `parent_trace_id` in memory metadata or in
your external trace backend. LightAgent does not currently fold delegated
LightSwarm traces into the parent agent trace automatically.

### LightSwarm And Self-Learning Guidance

For LightSwarm or self-learning deployments:

- Keep user conversation memory and reflection memory in different scopes.
- Treat delegated agent outputs as task state until intentionally promoted.
- Use `agent_name`, `source`, and `scope` filters before injecting memories into
  a future prompt.
- Prefer append-only memory writes with provenance over overwriting shared
  records.
- Do not let trace-derived summaries write directly into user memory without an
  admission check.

Use [Memory Admission And Mutation Controls](memory_admission.md) to add
write-time admission hooks, per-run write limits, and duplicate write blocking.
