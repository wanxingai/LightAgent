## Memory Security Guidance

LightAgent accepts external memory backends through a small `store()` and
`retrieve()` interface. This keeps the framework flexible, but it also means
deployments must treat long-term memory as a trust boundary.

### Threat Model

Shared memory backends can persist user supplied content and later return it as
agent context. If untrusted content is written into the same memory namespace as
trusted content, a later request can retrieve poisoned facts and pass them to the
model as apparently reliable context.

This is especially important for high-impact domains such as healthcare,
finance, legal, enterprise automation, and policy support.

### Recommended Defaults

- Use separate memory namespaces per user, tenant, agent, and environment.
- Set `memory_namespace` or a custom `MemoryPolicy` when a single backend is
  shared by multiple tenants or environments.
- Do not share graph memory across users unless there is an explicit product
  requirement and a reviewable access policy.
- Treat retrieved memories as untrusted context unless the memory backend can
  provide provenance and trust metadata.
- Treat reflection, delegation summaries, and self-learning output as
  non-injectable evidence until a promotion policy or reviewer explicitly
  approves or rewrites it.
- Disable memory writes for high-impact workflows until source trust,
  consistency checks, and rollback behavior are defined.
- Log memory writes at the metadata level: user id, agent id, source, timestamp,
  and trust level. Avoid logging sensitive raw content unless required by your
  compliance process.

### Admission Checks Before Writing Memory

Memory adapters should validate candidate memories before persistence:

- Record provenance: source user, agent, tool, channel, and timestamp.
- Keep trust levels separate, for example system, admin, verified source,
  authenticated user, and unauthenticated user.
- Reject or quarantine memories that contradict higher-trust facts.
- Avoid merging entities only by similar names; include entity type, context,
  tenant, and relation neighborhood in entity resolution.
- Preserve conflicting facts with provenance instead of silently deleting older
  trusted facts.

### Promotion Boundary For Internal Memory

LightAgent keeps built-in user memory compatible, but internal memory is safer
by default. When `self_learning=True` or another internal path writes
`source=reflection`, `source=delegation`, or `scope=agent`, LightAgent creates a
`MemoryCandidate` instead of immediately calling `memory.store()`. The candidate
can be promoted only through `MemoryPolicy(memory_promotion_admission=...)`,
`before_memory_promote` hooks, or the explicit
`agent.promote_memory_candidate(candidate_id)` API.

Promoted internal memory is persisted with metadata such as
`candidate_id`, `promotion_status="promoted"`, and `injectable=True`. Retrieved
memory with `injectable=False`, a candidate/rejected/blocked promotion status,
or unpromoted internal `source`/`scope` metadata is filtered before prompt
injection.

### Retrieval Checks Before Using Memory

Before injecting retrieved memory into the model context:

- Filter by tenant, user, agent, and allowed source trust level.
- Prefer verified or same-user memories over cross-user memories.
- Include provenance in internal context where possible.
- For high-impact answers, require a trusted external source or tool result
  before producing recommendations.

### Mem0 Graph Memory Notes

When using Mem0 graph memory or another shared graph backend, configure it so
one user's conversational claims cannot overwrite or remove trusted facts for
another user. If the backend cannot enforce that policy, use isolated memory
instances or per-user namespaces.

### LightAgent Adapter Guidance

Custom memory implementations passed to `LightAgent(memory=...)` should enforce
the security policy inside their `store()` and `retrieve()` methods. LightAgent
will call those methods, but the backend adapter remains responsible for
persistence, isolation, provenance, and conflict handling.

LightAgent also provides a lightweight core policy hook for shared deployments:

```python
from LightAgent import LightAgent, MemoryPolicy

agent = LightAgent(
    model="gpt-4.1",
    api_key="your_api_key",
    base_url="your_base_url",
    memory=memory_backend,
    memory_policy=MemoryPolicy(
        namespace="prod-tenant-a",
        allow_unattributed_results=False,
        allowed_sources=("user",),
        allowed_scopes=("user",),
    ),
)
```

`namespace` prefixes the `user_id` sent to the memory backend. If retrieved
memory items include `user_id` or `metadata.user_id`, LightAgent filters out
items that do not match the current scoped user. Set
`allow_unattributed_results=False` when the backend can provide provenance for
all memory records.

For long-lived agents, self-learning agents, or LightSwarm deployments, also
tag memory records by source and scope. See
[Memory, Trace, And Swarm Boundaries](memory_trace_swarm_boundaries.md) for the
recommended `MemoryScope` metadata convention and trace hierarchy guidance.

For write-time controls such as admission hooks, per-run write limits, and
duplicate write blocking, see
[Memory Admission And Mutation Controls](memory_admission.md).

For a lightweight shared-memory prototype that follows these provenance rules,
see [SharedMemoryPool](shared_memory_pool.md).

For a minimal vector-database adapter pattern, see
[Vector Memory Adapter Example](vector_memory_adapter.md).
