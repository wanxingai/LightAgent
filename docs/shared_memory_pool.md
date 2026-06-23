# SharedMemoryPool

`SharedMemoryPool` is a lightweight in-memory prototype for multi-agent shared
memory. It satisfies the existing `MemoryProtocol`, so it can be passed directly
to `LightAgent(memory=...)`:

```python
from LightAgent import LightAgent, MemoryPolicy, SharedMemoryPool

shared_memory = SharedMemoryPool(agent_name="writer")

agent = LightAgent(
    name="writer",
    model="gpt-4o-mini",
    api_key="...",
    memory=shared_memory,
    memory_policy=MemoryPolicy(
        namespace="tenant-a",
        allow_unattributed_results=False,
        allowed_sources=("user",),
        allowed_scopes=("user",),
    ),
)
```

The first implementation is intentionally not durable storage. It is designed
for local experiments, tests, LightFlow prototypes, and LightSwarm design work
before adding heavier backends.

## Design Rules

- **Append first**: `store()` creates a new record instead of overwriting an
  existing memory.
- **Scoped by user id**: `retrieve(query, user_id)` searches only records with
  the same scoped `user_id`.
- **Provenance aware**: records include `metadata.source`,
  `metadata.scope`, `metadata.agent_name`, and `metadata.user_id`.
- **Policy compatible**: retrieval results include the fields required by
  `MemoryPolicy` so callers can fail closed for unattributed or cross-scope
  memory.
- **Low dependency**: no SQLite, vector database, or network dependency is added
  to the core package.

## Direct Use

```python
from LightAgent import SharedMemoryPool

pool = SharedMemoryPool(agent_name="researcher")

pool.store("Alice prefers concise reports", user_id="tenant-a:alice")
pool.store("Bob prefers detailed reports", user_id="tenant-a:bob")

results = pool.retrieve("concise report", user_id="tenant-a:alice")
print(results["results"])
```

The returned shape follows the memory retrieval convention:

```python
{
    "results": [
        {
            "memory": "Alice prefers concise reports",
            "user_id": "tenant-a:alice",
            "metadata": {
                "source": "user",
                "scope": "user",
                "agent_name": "researcher",
                "user_id": "tenant-a:alice",
            },
            "memory_id": "...",
            "created_at": "...",
        }
    ]
}
```

## Self-Learning Boundary

When `LightAgent` writes to a memory backend that supports `metadata`, it now
passes MemoryScope-compatible provenance metadata. With `SharedMemoryPool`, user
conversation memory and self-learning reflection memory are written into
separate scoped user ids:

```text
tenant-a:alice   -> source=user, scope=user
tenant-a:writer  -> source=reflection, scope=agent
```

This keeps reflection useful for inspection while preventing it from collapsing
into ordinary user memory.

## Inspection

Use `list_records()` for tests, debugging, and audit views:

```python
user_records = pool.list_records(user_id="tenant-a:alice")
agent_private = pool.list_records(
    user_id="tenant-a:writer",
    source="reflection",
    scope="agent",
)
```

Use `clear()` only in tests or local experiments:

```python
pool.clear(user_id="tenant-a:alice")
pool.clear()
```

## Production Guidance

`SharedMemoryPool` is not a replacement for a durable database. Production
shared memory should keep the same record shape while adding:

- persistence;
- access control;
- explicit conflict handling;
- stronger retrieval ranking;
- backup and deletion workflows;
- domain-specific admission checks through `MemoryPolicy`.
