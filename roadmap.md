# LightAgent Roadmap

Last updated: 2026-06-24

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
- **v0.8.2**: Added optional memory write admission hooks, per-run write
  limits, duplicate write blocking, and trace events for allowed or blocked
  memory writes.
- **v0.9.0**: Added enhanced LightFlow execution controls, JSON checkpointed
  workflow runs, resume/rerun support, approval nodes, reusable guardrail
  templates, stronger memory admission controls, and the first lightweight
  `SharedMemoryPool` prototype.

### Completed Milestone Details

These items came from the earlier `roadmap 2.md` draft and are now treated as
shipped capabilities or established direction:

- **Stability and developer experience**: preserve string-return compatibility
  while making structured `RunResult` available for callers that need trace IDs,
  errors, and structured run metadata. The legacy roadmap also called out
  `content`, `reasoning_content`, `tool_calls`, `usage`, `trace_id`, and
  `error` as the key result fields, plus catchable `LightAgentError` behavior,
  tool argument validation, example cleanup, stale import fixes, and focused
  unit tests for tool registry, runtime tools, stream/non-stream execution,
  error handling, and memory adapter behavior.
- **Trace and observability**: keep human-readable debug logs separate from
  machine-readable trace events so production debugging can rely on structured
  data. The legacy roadmap also listed `run_start`, `model_request`,
  `model_response`, `tool_call`, `tool_result`, `handoff`, `memory_read`,
  `memory_write`, and `run_end` as the desired event vocabulary, with JSON
  export and Langfuse integration built on top of trace events.
- **Guardrails and safe tool execution**: constrain input, tool calls, and final
  output through explicit policy while keeping default behavior lightweight.
  The legacy roadmap specifically called for prompt-injection checks,
  permission checks, high-risk tool-call policies, approval requirements for
  file/network/database/payment/external-action tools, output schema/PII
  checks, and memory guardrails for namespace, provenance, trust, and retrieval
  filtering.
- **LightFlow workflow orchestration**: support deterministic workflow steps
  without turning LightAgent into a heavy orchestration framework. The merged
  legacy plan included explicit step input/output passing, per-step tools,
  model, memory, retry behavior, flow trace export, and later manual approval
  nodes.
- **Human-in-the-loop and recoverability**: keep human approval, durable
  execution, run stores, idempotency markers, and resume semantics as planned
  follow-on work rather than core requirements for early 0.8.x releases.

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

## Near-Term Version Plan

This section records the planned direction for the next several LightAgent
versions after `v0.8.2`. Exact scope can still change as issues, pull requests,
and user feedback evolve, but the intended product direction is:

**safer memory + stronger LightFlow + better observability + stable APIs +
enterprise-friendly integration.**

### v0.8.3 Goals: LightFlow Execution Controls

Goal: make LightFlow easier to operate and debug in real multi-step workflows.
These goals are completed as part of the v0.9.0 development line.

Completed in v0.9.0:

- Clear step status tracking: `pending`, `running`, `success`, `failed`,
  `skipped`, and `waiting_approval`.
- DAG validation for unknown dependencies, circular dependencies, and isolated
  step warnings.
- Step-level timeout, cancellation, fallback-agent, and approval controls.
- Flow trace output with step input summaries, output summaries, retry counts,
  error reasons, timing metadata, and fallback usage.
- Focused tests for enhanced workflow controls.

Expected outcome:

Developers should be able to build and troubleshoot predictable LightFlow
pipelines without relying on prompt-only control or external workflow engines.

### v0.8.4 Goals: Memory And Guardrail Hardening

Goal: strengthen memory admission, memory retrieval safety, and guardrail
templates for production usage. These goals are completed as part of the v0.9.0
development line.

Completed in v0.9.0:

- Extend `MemoryPolicy` with expiration-aware retrieval through
  `enforce_expires_at`.
- Improve memory write admission with `min_write_length` and
  `reject_write_patterns`.
- Keep source, scope, agent, trust-level, and confidence filtering from the
  earlier memory-safety line.
- Add reusable guardrail templates for privacy filtering, high-risk tool
  confirmation, sensitive parameter validation, and output redaction.
- Clarify recommended boundaries between trace events, user memory,
  self-reflection memory, and LightSwarm delegation state.
- Add more tests around memory provenance filtering, expiration filtering,
  blocked memory writes, and guardrail templates.

Expected outcome:

LightAgent should become safer for shared memory, customer service, internal
knowledge assistant, financial analysis, and other high-impact agent use cases.

### v0.9.0: Persistent LightFlow, Safety, And Shared Memory

Goal: extend LightFlow from an in-memory workflow runner into a lightweight
checkpointed workflow system, while also shipping the memory and safety
hardening required for long-running multi-agent workflows.

Completed work:

- Add LightFlow step status tracking with `pending`, `running`, `success`,
  `failed`, `skipped`, and `waiting_approval`.
- Add workflow validation for unknown dependencies, circular dependencies, and
  isolated step warnings.
- Add step-level timeout, cancellation, fallback-agent, and approval controls.
- Add JSON checkpoint storage through `JsonLightFlowStore`.
- Add `resume(run_id)`, `rerun_step(run_id, step_name)`, `get_run(run_id)`,
  and `list_runs()` workflow record APIs.
- Persist intermediate step results and status for front-end execution views.
- Add an in-memory `SharedMemoryPool` that satisfies `MemoryProtocol`.
- Use append-first records with `memory_id`, `created_at`, `user_id`, and
  provenance metadata.
- Keep user memory and agent reflection memory in separate scoped ids when used
  with `LightAgent`.
- Allow direct inspection through `list_records()` and test cleanup through
  `clear()`.
- Pass `MemoryScope`-compatible metadata to memory backends that support a
  `metadata` keyword while preserving compatibility with two-argument legacy
  backends.
- Add memory expiration filtering and basic low-quality write blocking through
  `MemoryPolicy`.
- Add reusable guardrail templates for privacy filtering, sensitive tool
  confirmation, high-risk parameter validation, and output redaction.
- Add tests for workflow controls, checkpoint/resume/rerun, scoped retrieval,
  append-first behavior, provenance filtering, guardrail templates, and
  LightAgent integration.

Deferred work:

- SQLite or other database-backed run stores.
- Distributed workers, locks, and stronger idempotency guarantees.
- Advanced conflict-resolution policies beyond append-first storage.

Expected outcome:

Users can experiment with safer shared memory in LightAgent, LightSwarm, or
LightFlow prototypes while preserving explicit provenance boundaries and a
lightweight core.

### v0.9.5: Observability, Evaluation, And Human Review

Goal: improve production debugging, measurement, and human control over
high-risk actions.

Planned work:

- Add richer trace metadata for model latency, tool latency, token usage,
  retry counts, error categories, and flow-step timing.
- Provide a lightweight evaluation harness for tool-call success rate,
  task-completion rate, latency, cost, and recovery behavior.
- Improve Langfuse and external observability integration on top of structured
  trace events.
- Add a `HumanApprovalTool` or equivalent approval primitive.
- Allow selected tools or LightFlow steps to require human approval before
  continuing.
- Support approval, rejection, argument editing, timeout, and rejection handling.

Expected outcome:

LightAgent should support production environments where teams need to measure
agent quality, inspect failures, and keep humans in control of high-impact
external side effects.

### v1.0.0: Stable API And Production Documentation

Goal: freeze the public API surface and make LightAgent dependable for
production users and contributors.

Planned work:

- Stabilize public APIs:
  - `LightAgent`
  - `LightSwarm`
  - `LightFlow`
  - `Skill`
  - `ToolRegistry`
  - `MemoryProtocol`
  - `MemoryPolicy`
  - `GuardrailDecision`
  - `RunResult`
  - `StreamEvent`
- Reduce breaking changes after the 1.0 line.
- Complete bilingual documentation for installation, tools, skills, memory,
  MCP, Guardrails, Trace, LightSwarm, LightFlow, and production deployment.
- Add a complete example matrix covering basic agents, constructor tools,
  runtime tools, memory, Skills, MCP, browser-use, OpenRouter, LiteLLM, local
  LLMs, LightFlow, human approval, and error handling.
- Add stronger CI coverage for core runtime behavior.
- Automate PyPI release publishing and release notes.

Expected outcome:

LightAgent 1.0 should provide a stable, documented, tested foundation for
building lightweight production agents.

### v1.1.0: Enterprise Integration

Goal: make LightAgent easier to embed into internal systems and private
deployments.

Planned work:

- Add stronger multi-tenant memory isolation examples and policy templates.
- Provide tool-level permission and audit patterns for production systems.
- Add deployment templates for Docker and service-style API wrappers.
- Improve model routing guidance for OpenAI-compatible endpoints, LiteLLM,
  local inference servers, and private model gateways.
- Provide audit log export examples for trace, tool calls, guardrail blocks,
  memory writes, and workflow steps.
- Add enterprise-oriented examples for customer service, data analysis,
  internal knowledge assistants, and automated office workflows.

Expected outcome:

LightAgent should be easier to adopt inside enterprise systems without turning
the core framework into a large platform.

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

### Completed Work

- Add optional memory write admission hooks through `MemoryPolicy`.
- Support simple per-run write limits for memory mutations.
- Add lightweight duplicate write blocking using scope-aware fingerprints.
- Emit `memory_write` and `memory_write_block` trace events without raw memory
  text.
- Document write-time controls for high-impact or shared memory backends.
- Keep default behavior unchanged for simple single-agent usage.

### Expected Outcome

LightAgent should have a minimal but practical first layer against memory
poisoning, write amplification, and reflection cascades.

## Detailed Backlog For Planned Releases

### v0.9.0 Workstream: Persistent LightFlow, Safety, And Shared Memory

Goal: provide checkpointed workflow execution, reusable safety controls, and a
lightweight shared-memory design without adding heavy storage dependencies.

### Completed Work

- Add explicit LightFlow step status, richer step traces, timeout,
  cancellation, fallback-agent, approval, checkpoint, resume, rerun, and run
  record APIs.
- Add JSON-file workflow persistence through `JsonLightFlowStore`.
- Persist intermediate step results so long-running workflows can resume after
  failure instead of restarting from the first step.
- Add an in-memory `SharedMemoryPool` implementation.
- Keep records append-first instead of overwrite-by-default.
- Store `memory_id`, `created_at`, `user_id`, `memory`, and provenance
  metadata on each record.
- Support scoped retrieval by `user_id`, `agent_name`, `source`, and `scope`.
- Preserve compatibility with `MemoryPolicy` by returning retrieval records with
  `user_id` and `metadata`.
- Update `LightAgent` to pass memory metadata to backends that support it while
  preserving the existing two-argument `MemoryProtocol`.
- Add memory expiration filtering, minimum write length checks, and reject
  patterns for low-quality memory writes.
- Add default guardrail templates for privacy filtering, sensitive tool
  confirmation, high-risk parameter validation, and output redaction.
- Add tests for multi-agent read/write isolation and reflection-memory
  separation, persistent workflow records, resume, rerun, approval, fallback,
  memory admission, and guardrail templates.

### Expected Outcome

LightAgent users should be able to experiment with shared memory in LightSwarm
or LightFlow while preserving explicit boundaries and inspectable behavior.

### v0.9.5 Workstream: Human-In-The-Loop

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

### v1.0.0 Workstream: Stable API And Ecosystem

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

- No active P0 item as of 2026-06-24.

### Next P1

- Database-backed workflow and shared-memory adapters.
- Stronger idempotency and distributed execution controls for persistent
  workflows.
- Evaluation harness and richer production observability.

### P2

- Optional ClawMem adapter shape for #33.
- Lightweight plugin/connector contract for #5.
- Vector database and external API examples for #4 and #26.

### P3

- Nautilus/A2A optional connector evaluation for #50.
- Visual trace UI.
- Durable execution and resume.

## Next Development Recommendation

After v0.9.0, the next development target should be **v0.9.5:
Observability And Evaluation** or a smaller **v0.9.1 database-backed run store**
if user feedback asks for stronger persistence first.

Reasoning:

- v0.9.0 now covers checkpointed LightFlow runs, resume/rerun, approval nodes,
  memory-safety controls, guardrail templates, and the shared-memory prototype.
- The next pressure points are production measurement and stronger persistence:
  evaluations, richer traces, database-backed run stores, and idempotency.
- Database-backed durability should stay optional so the core package remains
  lightweight.

Suggested first implementation slice:

1. Add an evaluation harness for task completion and tool-call success.
2. Add richer trace fields for latency, retry count, and error categories.
3. Add database-backed run-store adapters if persistence becomes the next user
   priority.
4. Add idempotency markers for external side-effect tools.
