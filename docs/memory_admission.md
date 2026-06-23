## Memory Admission And Mutation Controls

LightAgent v0.8.2 adds optional write-time controls for memory-backed agents.
These controls are configured through `MemoryPolicy` and run before
`memory.store(data, user_id)` is called.

Default behavior is unchanged. If you do not configure memory admission options,
LightAgent stores memory the same way as earlier versions.

### Write Admission Hook

Use `memory_write_admission` when an application needs to block, approve, or
rewrite memory writes.

```python
from LightAgent import LightAgent, MemoryAdmissionDecision, MemoryPolicy

def admit_memory(data, context):
    if context["source"] == "reflection":
        return "Reflection memory requires review before persistence."
    return MemoryAdmissionDecision(allowed=True, value=data.strip())

agent = LightAgent(
    model="gpt-4.1",
    api_key="your_api_key",
    base_url="your_base_url",
    memory=memory_backend,
    memory_policy=MemoryPolicy(memory_write_admission=admit_memory),
)
```

The hook receives:

| Field | Meaning |
| --- | --- |
| `data` | Candidate memory text |
| `context["source"]` | `user` or `reflection` for built-in writes |
| `context["scope"]` | `user` or `agent` for built-in writes |
| `context["user_id"]` | Original user or agent identifier |
| `context["memory_user_id"]` | Scoped user id sent to the backend |
| `context["agent_name"]` | Current agent name |
| `context["trace_id"]` | Current run trace id |

The hook can return:

- `True` or `None` to allow the write;
- `False` or a string to block the write;
- `MemoryAdmissionDecision`;
- a dictionary with `allowed`, `reason`, and optional `value`;
- any other value to allow and rewrite the stored memory text.

### Write Limits

Use `max_writes_per_run` to cap memory mutations from a single run.

```python
policy = MemoryPolicy(max_writes_per_run=1)
```

This is useful when `self_learning=True` or when reflection logic may otherwise
write multiple derivative memories from one user turn.

### Duplicate Write Blocking

Use `reject_duplicate_writes=True` to block duplicate candidate writes within a
single run.

```python
policy = MemoryPolicy(reject_duplicate_writes=True)
```

The duplicate fingerprint is lightweight and scope-aware. It includes the scoped
memory user id, source, scope, agent name, and normalized text. This means a
user memory and a reflection memory with the same text are not treated as the
same write.

### Low-Quality Write Blocking

Use `min_write_length` and `reject_write_patterns` for simple default memory
quality gates before a backend persists data:

```python
policy = MemoryPolicy(
    min_write_length=12,
    reject_write_patterns=(
        r"ignore previous instructions",
        r"system prompt",
    ),
)
```

These checks run before `memory_write_admission`, so application-specific
classifiers can still perform deeper review after basic filtering.

### Expiration-Aware Retrieval

Memory records can include `expires_at` metadata. When
`enforce_expires_at=True`, LightAgent only injects retrieved memories that have
a valid future expiration value:

```python
policy = MemoryPolicy(
    allow_unattributed_results=False,
    enforce_expires_at=True,
)
```

Adapters can store `expires_at` as an ISO-8601 timestamp or a Unix timestamp.
Expired, malformed, or missing expiration metadata is filtered out when
expiration enforcement is enabled.

### Trace Events

When tracing is enabled, memory write controls emit:

| Event | Meaning |
| --- | --- |
| `memory_write` | A memory write was allowed and persisted. |
| `memory_write_block` | A memory write was blocked by policy. |

These events do not include raw memory text.

### Recommended Use

- Keep default behavior for simple single-agent demos.
- Configure `memory_write_admission` for shared or graph-backed memory.
- Use `max_writes_per_run` for self-learning agents to reduce write
  amplification.
- Use `reject_duplicate_writes=True` for reflection-heavy workflows.
- Combine write-time controls with retrieval-time filters from
  [Memory, Trace, And Swarm Boundaries](memory_trace_swarm_boundaries.md).
