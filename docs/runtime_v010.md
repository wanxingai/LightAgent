# LightAgent v0.10 Runtime

LightAgent v0.10 adds an opt-in, event-sourced runtime beneath the compatible
`agent.run()` API. Basic agents still require no database or runtime setup.

## Durable Sessions

```python
from LightAgent import LightAgent, SqliteSessionStore

store = SqliteSessionStore(".lightagent/sessions.sqlite3")
agent = LightAgent(
    model="deepseek-v4-flash",
    api_key="your_api_key",
    base_url="your_base_url",
    session_store=store,
)

agent.run("Remember this project decision", session_id="project-42")
agent.run("What did we decide?", session_id="project-42")

print(agent.replay_session("project-42"))
checkpoint = agent.checkpoint_session("before-implementation")
fork = agent.fork_session(through_sequence=checkpoint["sequence"])
```

`InMemorySessionStore`, `JsonlSessionStore`, and `SqliteSessionStore` implement
the same contract. Events are append-only, sequence-validated, versioned, and
credential fields are redacted before persistence. `ContextProjector` rebuilds
conversation context, exact model requests, and compatible trace views from
the event log.

## Async Usage

```python
result = await agent.arun("Analyze the incident")

stream = await agent.arun("Analyze the incident", stream=True)
async for chunk in stream:
    print(chunk)
```

The async entry point keeps synchronous v0.9 model and tool clients compatible
by isolating them in a worker thread. Native async Providers and background
Jobs execute on the caller's event loop.

## Capabilities And Policy

```python
from LightAgent import (
    BaseCapabilityProvider,
    CapabilityRegistry,
    CapabilitySpec,
    PolicyDecision,
    PolicyEngine,
)

def workspace_policy(request):
    if request.capability.write and request.context.metadata.get("read_only"):
        return PolicyDecision.block("workspace is read-only")
    return PolicyDecision.allow(request.arguments)

registry = CapabilityRegistry(policy_engine=PolicyEngine([workspace_policy]))
```

Providers declare lifecycle methods and capability metadata for read, write,
network, execution, persistence, risk, timeout, output limits, cancellation,
and approval. Runtime, Session, and Agent scopes resolve deterministically;
equal-scope conflicts are available through `registry.conflicts()`.

`ToolProviderAdapter`, `MemoryProviderAdapter`, `SkillProviderAdapter`,
`MCPProviderAdapter`, and `WorkflowProviderAdapter` bridge existing LightAgent
APIs into the registry. Sensitive tool calls made by `LightAgent` pass through
the registry's `PolicyEngine` before existing Guardrails and Hooks.

## Long-Task State

Every `LightAgent` exposes `agent.runtime`:

```python
goal = agent.runtime.goals.create(
    "Prepare the release",
    acceptance_criteria=["tests pass", "artifacts build"],
)
agent.runtime.goals.activate(goal.goal_id)
agent.runtime.inbox.enqueue("steering", "Do not publish yet", message_id="release-hold")
agent.runtime.pause("waiting for CI")
```

The runtime includes ordered and idempotent Inbox messages, durable Goals,
model/tool/token/time/cost budgets, progress-loop detection, cancellable Jobs,
and bounded subagent registration with narrowing-only permission snapshots.
Restoring a Session rebuilds Inbox, Goal, Budget, and interrupted Job state.

## Context And Knowledge

`ContextBudget` and `ContextCompactor` provide deterministic trimming,
optional summarization, and SHA-256 references for oversized tool output.
Compaction decisions are Session events. Checkpoints and forks retain source
event lineage.

`SqliteFTSRetrievalProvider` is a dependency-free minimum RAG implementation:

```python
from LightAgent import RetrievalDocument, SqliteFTSRetrievalProvider

rag = SqliteFTSRetrievalProvider(".lightagent/knowledge.sqlite3")
rag.ingest(RetrievalDocument(
    content="The production deployment uses blue-green releases.",
    title="Deployment guide",
    source="docs/deployment.md",
    tenant_id="acme",
))

for result in rag.search("deployment", tenant_id="acme"):
    print(result.citation_id, result.content)
```

`SessionSearchProvider` is intentionally separate from knowledge-base RAG and
returns citations in `session:<session_id>:<sequence>` form.

## Skills And MCP

Skill directories are processed in declared order; later directories shadow
earlier entries and conflicts are reported by `SkillManager.list_conflicts()`.
`discover_project_instructions()` loads nested `AGENTS.md` files from root to
the working directory without modifying them.

MCP retains stdio and SSE configuration compatibility and adds opt-in
Streamable HTTP (`transport: streamable-http`), reconnect attempts, tool-list
refresh, namespace isolation, and external credential-header resolution.

## Compatibility Boundary

- `agent.run("hello")`, `stream=True`, structured results, Hooks, Guardrails,
  Memory, LightSwarm, and LightFlow remain compatible.
- Browser, Terminal, Shell, LSP, vector database, hosted service, and WebUI
  implementations remain optional Providers rather than core dependencies.
- Session and Capability APIs are pre-1.0 contracts and may receive additive
  changes before the v1.0 API freeze.
