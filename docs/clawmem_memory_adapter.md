## ClawMem Memory Adapter Example

LightAgent can use ClawMem as an optional long-term memory backend through the
same small `MemoryProtocol` used by other memory integrations:

```python
memory.store(data: str, user_id: str)
memory.retrieve(query: str, user_id: str)
```

The example in `example/clawmem_memory_adapter.py` keeps ClawMem outside the
core dependency set. It accepts an injected client, so applications can wrap a
ClawMem HTTP client, SDK client, MCP client, or local service while tests use a
fake client with no live network calls.

### Adapter Shape

`ClawMemMemoryAdapter` expects the injected client to expose two methods:

```python
client.create_memory(payload)
client.search_memories(
    query,
    user_id=user_id,
    limit=top_k,
    metadata_filter={...},
)
```

The adapter maps a LightAgent memory write to a ClawMem-style knowledge item:

| LightAgent field | ClawMem payload field |
| --- | --- |
| `data` | `content` |
| first line of `data` | `title` |
| short text summary | `description` |
| `user_id` | `user_id` |
| `MemoryScope` metadata | `metadata` and searchable tags |

Returned search results are normalized back to LightAgent's retrieval shape:

```python
{
    "results": [
        {
            "memory": "Alice prefers quiet beach towns",
            "score": 0.91,
            "user_id": "tenant-a:alice",
            "metadata": {
                "source": "user",
                "scope": "user",
                "agent_name": "travel-agent",
                "user_id": "tenant-a:alice",
            },
        }
    ]
}
```

### Minimal Usage

```python
from LightAgent import LightAgent, MemoryPolicy
from example.clawmem_memory_adapter import ClawMemMemoryAdapter


class MyClawMemClient:
    def create_memory(self, payload):
        # Call your ClawMem SDK, HTTP API, MCP tool, or local service here.
        return {"id": "memory-id"}

    def search_memories(self, query, *, user_id, limit, metadata_filter=None):
        # Return ClawMem items with content/text, score, user_id, and metadata.
        return []


memory = ClawMemMemoryAdapter(MyClawMemClient(), agent_name="travel-agent")

agent = LightAgent(
    name="travel-agent",
    model="gpt-4.1",
    api_key="your_api_key",
    base_url="your_base_url",
    memory=memory,
    memory_policy=MemoryPolicy(
        namespace="tenant-a",
        allow_unattributed_results=False,
        allowed_sources=("user",),
        allowed_scopes=("user",),
        allowed_agent_names=("travel-agent",),
    ),
)
```

### Recommended Policy

When ClawMem is shared across tenants, users, agents, or environments, keep
retrieval fail-closed:

```python
MemoryPolicy(
    namespace="prod-tenant-a",
    allow_unattributed_results=False,
    allowed_sources=("user",),
    allowed_scopes=("user",),
    allowed_agent_names=("travel-agent",),
)
```

This ensures ClawMem records missing provenance, records from another user, and
agent-private reflection memories are not injected into user-facing prompts.

### Production Notes

- Keep ClawMem dependencies optional and application-owned.
- Do not commit ClawMem API keys or service URLs into examples.
- Preserve `user_id`, `source`, `scope`, and `agent_name` metadata on both write
  and read paths.
- Use `memory_write_admission`, `reject_duplicate_writes`, and
  `max_writes_per_run` for high-risk or high-volume deployments.
- Use fake clients in tests so CI stays deterministic and offline.
