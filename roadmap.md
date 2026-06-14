# LightAgent Roadmap

Last updated: 2026-06-14

LightAgent should continue to evolve as a lightweight, low-dependency agent
framework rather than a broad replacement for LangChain, LangGraph, CrewAI, or
LlamaIndex.

The product direction remains:

**Lightweight core + composable Skills + reliable tool execution + observable
traces + safe memory + deterministic workflows + OpenAI-compatible model
ecosystem.**

## Current Status

### Completed

- **v0.6.5**: Added structured run results, structured streaming events,
  catchable LightAgent errors, and tool argument validation while keeping
  legacy `agent.run()` and `stream=True` behavior compatible.
- **v0.7.0**: Added opt-in trace observability with structured run, model,
  tool, and error events.
- **v0.7.5**: Added initial memory safety and guardrail capabilities through
  `MemoryPolicy` and input/tool/output guardrails.
- **v0.8.0**: Added `LightFlow` for deterministic multi-step workflows with
  DAG dependencies, step output passing, retries, structured results, and flow
  trace events.
- **Post-v0.8.0 main**: Merged PR #56 to persist `self.tracetools` and document
  the optional LiteLLM provider.
- **v0.8.1**: Added `MemoryScope` metadata conventions, stricter
  `MemoryPolicy` source/scope/agent/trust/confidence filtering, and docs for
  separating trace events, user memory, self-reflection memory, and LightSwarm
  delegation state.

### Completed Milestone Details

These items came from the earlier roadmap and are now treated as shipped
capabilities or established direction:

- **Stability and developer experience**: preserve string-return compatibility
  while making structured `RunResult` available for callers that need trace IDs,
  errors, and structured run metadata.
- **Trace and observability**: keep human-readable debug logs separate from
  machine-readable trace events so production debugging can rely on structured
  data.
- **Guardrails and safe tool execution**: constrain input, tool calls, and final
  output through explicit policy while keeping default behavior lightweight.
- **LightFlow workflow orchestration**: support deterministic workflow steps
  without turning LightAgent into a heavy orchestration framework.

The shipped LightFlow API should remain simple:

```python
flow = LightFlow()

flow.step("research", agent=research_agent)
flow.step("analyze", agent=analysis_agent, depends_on=["research"])
flow.step("write", agent=writer_agent, depends_on=["analyze"])

result = flow.run("Analyze this company")
```

### Open Pull Requests

- No open PRs as of 2026-06-05.

### Active Issues

P1 issues that should shape the next releases:

- **#57 Trace observability vs mem0 auto-memory vs LightSwarm reflection**:
  clarify and harden the boundary between trace events, persistent memory, and
  multi-agent reflection/self-learning.
- **#39 Shared graph memory security disclosure**: continue adapter-level memory
  safeguards beyond the initial `MemoryPolicy` and guardrails.
- **#1 Enhanced memory management for multi-agent systems**: design a lightweight
  shared memory model with per-agent boundaries, provenance, and conflict rules.
- **#33 Optional ClawMem memory backend**: keep as an optional adapter that
  satisfies `MemoryProtocol`.
- **#5 Custom plugin/integration development**: define a small connector contract
  without turning the core into a heavy plugin platform.

P2 issues:

- **#50 Nautilus A2A registry/discovery proposal**: evaluate as optional
  connector or docs-only integration.
- **#26 External API tool integrations**: accept one API/tool family per PR, no
  secrets, no required core dependencies.
- **#4 Existing vector database integration**: add focused docs/examples or
  optional adapters instead of core dependencies.

## Reference Directions From Other Agent Frameworks

Current agent frameworks are converging around several production-oriented
capabilities:

- **LangGraph**: durable execution, checkpointing, human-in-the-loop workflows,
  long-running stateful tasks.
- **CrewAI**: combining autonomous agent collaboration with deterministic
  workflow orchestration through Crews and Flows.
- **OpenAI Agents SDK**: handoffs, guardrails, tracing, and production-oriented
  agent execution primitives.
- **Microsoft AutoGen**: multi-agent conversations, collaboration protocols, and
  agent-to-agent coordination.
- **Pydantic AI**: typed tools, structured output, schema validation, and
  type-safe agent interfaces.
- **LlamaIndex**: data-oriented agents, workflows, RAG, document pipelines, and
  knowledge retrieval.

LightAgent should borrow the strongest production ideas from these frameworks
while preserving its own identity: small, direct, Python-native, Skills-first,
and OpenAI-compatible.

## Positioning

LightAgent should not become a second LangGraph, CrewAI, or LlamaIndex. Its
strongest path is to remain:

- lightweight;
- explicit;
- low-dependency;
- Python-native;
- OpenAI-compatible;
- Skills-first;
- easy to inspect;
- easy to extend.

The highest-value work is improving reliability, observability, safety, tests,
workflow composition, and memory boundaries while keeping the core simple.

## v0.8.1: Memory, Trace, And Swarm Boundary Safety

Goal: prevent trace observability, persistent memory, and LightSwarm
self-reflection from collapsing into one uncontrolled feedback loop.

This should directly address issues #57, #39, and #1.

### Completed Work

- Document the recommended separation between:
  - per-run trace events;
  - user conversation memory;
  - agent self-reflection memory;
  - LightSwarm delegation state.
- Add `MemoryScope` as a metadata convention for memory writes:
  - `source`: `user`, `agent`, `tool`, `trace`, `reflection`, or `swarm`;
  - `scope`: `user`, `agent`, `session`, `flow`, `swarm`, or `project`;
  - `agent_name`;
  - `trace_id`;
  - optional `parent_trace_id`;
  - optional `confidence` / `trust_level`.
- Extend `MemoryPolicy` and tests so retrieved memories can be filtered
  by source, scope, user, and agent provenance.
- Add docs that explain the current trace model:
  - each `agent.run()` has its own `trace_id`;
  - nested reflection or delegated runs should be treated as sibling traces
    unless the caller wires `parent_trace_id`;
  - LightSwarm traces are not automatically folded into parent traces yet.
- Add regression tests for memory provenance filtering and reflection-memory
  isolation.

### Expected Outcome

Users should understand how to prevent self-reflection, trace summaries, and
delegated agent outputs from being stored as ordinary user memory. LightAgent
should provide a clear convention that future memory adapters can follow.

## v0.8.2: Memory Admission And Mutation Controls

Goal: make memory writes safer before adding deeper shared-memory features.

### Planned Work

- Add optional memory write admission hooks.
- Support simple rate limits for memory mutations per user/session/agent.
- Add semantic duplicate and recent-write checks as optional extension points.
- Add provenance/trust requirements for high-impact or shared memory backends.
- Keep default behavior unchanged for simple single-agent usage.

### Expected Outcome

LightAgent should have a minimal but practical first layer against memory
poisoning, write amplification, and reflection cascades.

## v0.9.0: SharedMemoryPool Prototype

Goal: provide a lightweight shared memory design for multi-agent systems without
adding heavy storage dependencies.

### Planned Work

- Add a `SharedMemoryPool` interface or design doc.
- Start with an in-memory or SQLite prototype.
- Keep per-agent private memory separate from shared pool memory.
- Use append-first conflict handling instead of overwrite-by-default behavior.
- Support namespace and provenance policies from `MemoryPolicy`.
- Add tests for multi-agent read/write isolation.

### Expected Outcome

LightAgent users should be able to experiment with shared memory in LightSwarm
or LightFlow while preserving explicit boundaries and inspectable behavior.

## v0.9.5: Human-In-The-Loop

Goal: support high-risk tasks that need explicit human review before continuing.

### Planned Work

- Add a `HumanApprovalTool`.
- Support approval requirements for selected tools or flow steps.
- Allow humans to approve, reject, or edit tool arguments.
- Add timeout and rejection handling.
- Allow an agent or flow to continue after approval.

### Expected Outcome

LightAgent should support workflows where a model can plan and prepare actions,
but humans retain control over important external side effects.

## v1.0.0: Stable API And Ecosystem

Goal: stabilize the public API and make LightAgent reliable for production users
and contributors.

### Planned Work

- Stabilize public APIs:
  - `LightAgent`
  - `LightSwarm`
  - `LightFlow`
  - `Skill`
  - `ToolRegistry`
  - `MemoryProtocol`
  - `MemoryPolicy`
  - `RunResult`
- Build a complete documentation site.
- Add a full example matrix:
  - basic agent;
  - constructor tools;
  - runtime tools;
  - memory;
  - Skills;
  - MCP;
  - browser-use;
  - OpenRouter;
  - LiteLLM;
  - local LLM;
  - LightFlow;
  - human approval.
- Add CI coverage for core runtime behavior.
- Automate PyPI release publishing.
- Add benchmarks for tool-call success rate, multi-turn completion, token cost,
  latency, and recovery behavior.

### Expected Outcome

LightAgent 1.0 should provide a stable, documented, tested foundation for
building lightweight production agents.

## Longer-Term Directions

### Durable Execution And Resume

- Add a `RunStore` interface.
- Provide SQLite, Redis, and Postgres adapters as optional packages.
- Persist model requests, responses, tool calls, tool results, memory reads, and
  memory writes.
- Add `agent.resume(run_id)` or `flow.resume(run_id)`.
- Add idempotency markers for tools.
- Prevent already-completed tool calls from being repeated during resume.

### Structured Output

- Add `output_schema=MyPydanticModel`.
- Validate and parse model output into typed Python objects.
- Retry or repair invalid JSON where possible.
- Support schema-first tool and response design.

### Data-Oriented Agents

- Add stronger document, SQL, RAG, and vector-store examples.
- Provide lightweight adapters for common retrieval workflows.
- Keep retrieval optional and modular instead of adding heavy core dependencies.

### Multi-Agent Protocol Compatibility

- Continue improving MCP support.
- Explore agent-to-agent handoff schemas.
- Evaluate A2A or registry/discovery proposals only as optional connectors.

### Visual Debugging

- Build a simple trace viewer.
- Show model calls, tool calls, memory operations, handoffs, flow steps, and
  failures in chronological order.
- Make traces shareable for issue reports and debugging.

## Recommended Priority

### Immediate P0

- No active P0 item as of 2026-06-05.

### Next P1

- v0.8.2 memory admission and mutation controls for #57, #39, and #1.
- Memory write admission hooks and mutation rate-limit examples.
- Duplicate/recent-write checks to reduce reflection cascades.

### P2

- Optional ClawMem adapter shape for #33.
- Lightweight plugin/connector contract for #5.
- Vector database and external API examples for #4 and #26.

### P3

- Nautilus/A2A optional connector evaluation for #50.
- Visual trace UI.
- Durable execution and resume.

## Next Development Recommendation

The next development target should be **v0.8.2: Memory Admission And Mutation
Controls**.

Reasoning:

- v0.8.1 created the metadata and retrieval-filter foundation.
- #57 and #39 still need write-time controls to reduce memory poisoning, write
  amplification, and reflection cascades.
- Admission hooks can stay optional and lightweight while giving production
  deployments a stronger safety boundary.

Suggested first implementation slice:

1. Add optional memory write admission hooks.
2. Add simple per-user/session/agent memory mutation rate-limit examples.
3. Add duplicate/recent-write extension points.
4. Keep default single-agent memory behavior unchanged.
