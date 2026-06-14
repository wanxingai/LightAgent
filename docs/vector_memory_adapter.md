## Vector Memory Adapter Example

LightAgent accepts custom memory backends through the small `MemoryProtocol`
interface:

```python
memory.store(data: str, user_id: str)
memory.retrieve(query: str, user_id: str)
```

That means vector databases should normally live behind an adapter, not inside
LightAgent core. The example in `example/11.vector_memory_adapter.py` shows a
local, dependency-free adapter with the same shape a Qdrant, Chroma, Milvus, or
FAISS integration would use.

### Adapter Shape

The example keeps three responsibilities explicit:

- `store()` embeds the text, records the scoped `user_id`, and stores provenance
  metadata from `MemoryScope`.
- `retrieve()` embeds the query, searches only the current user's records, and
  returns `{"results": [...]}`.
- Returned records include `user_id` and `metadata`, so `MemoryPolicy` can filter
  unsafe or cross-scope memories before they are injected into the prompt.

For a production vector database, replace the local `_records` list with backend
calls while keeping the same boundary:

```python
class QdrantMemoryAdapter:
    def store(self, data: str, user_id: str):
        metadata = MemoryScope.user(agent_name="agent", user_id=user_id).to_metadata()
        vector = embed(data)
        qdrant.upsert(collection, vector=vector, payload={
            "memory": data,
            "user_id": user_id,
            "metadata": metadata,
        })

    def retrieve(self, query: str, user_id: str):
        vector = embed(query)
        hits = qdrant.search(
            collection,
            query_vector=vector,
            query_filter={"must": [{"key": "user_id", "match": {"value": user_id}}]},
        )
        return {"results": [hit.payload for hit in hits]}
```

### Recommended Policy

When sharing a vector database across users, tenants, agents, or environments,
use `MemoryPolicy` so retrieval fails closed for unattributed or cross-scope
records:

```python
MemoryPolicy(
    namespace="prod-tenant-a",
    allow_unattributed_results=False,
    allowed_sources=("user",),
    allowed_scopes=("user",),
)
```

This keeps vector search useful without letting agent reflection, tool output, or
another user's memories collapse into the same prompt context.
