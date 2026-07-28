# LightAgent Roadmap

Last updated: 2026-07-21

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
- **v0.9.1**: Added the first runtime hook layer through `HookContext`,
  `HookDecision`, `HookManager`, `LightAgent(..., hooks=[...])`, and
  `LightFlow(hooks=[...])`.
- **v0.9.2**: Completed core agent lifecycle hooks with `after_run`,
  `on_error`, memory-retrieval hooks, and async-compatible hook execution.
- **v0.9.3**: Hardened streaming tool-loop safety with `max_tool_iterations`
  and consistent `on_error`, `after_run`, and `run_end` closure.
- **v0.9.4**: Released tool schema diagnostics, `PolicyHook` fail-closed
  policy behavior, `on_handoff`, LightSwarm runtime-context propagation, and
  complete Python 3.10/3.11/3.12 CI coverage.
- **v0.9.5**: Added explicit memory promotion boundaries for internal
  reflection, delegation, self-learning, tool, trace, swarm, and shared-memory
  evidence; added non-injectable `MemoryCandidate` records, approve/reject/
  rewrite/keep `MemoryPromotionDecision` handling, `before_memory_promote` and
  `after_memory_promote` hooks, promotion trace events, fail-closed promotion
  policy behavior, and optional OSS/NOS `boto3` dependencies.

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

- **#81 fix for broken build pipeline**: external PR proposing Poetry/build
  pipeline changes in `pyproject.toml`, `poetry.lock`, `.github/workflows`,
  `.gitignore`, and a new `Makefile`. Review separately as release hygiene;
  do not mix it with the v0.9.5 memory-safety feature line.

### Active Issues

P1 issues that should shape the next releases:

- **#82 Explicit memory promotion workflow**: v0.9.5 implements the first
  explicit, auditable promotion path; keep follow-up work focused on external
  review queues and UI integration.
- **#39 Shared graph memory security disclosure**: v0.9.5 blocks unreviewed
  internal/shared evidence from prompt injection by default; continue
  adapter-level hardening for durable graph/vector backends.
- **#1 Enhanced memory management for multi-agent systems**: design a lightweight
  shared memory model with per-agent boundaries, provenance, and conflict rules.
- **#33 Optional ClawMem memory backend**: keep as an optional adapter that
  satisfies `MemoryProtocol`.
- **#5 Custom plugin/integration development**: define a small connector contract
  without turning the core into a heavy plugin platform.

P2 issues:

- **#76 CCS fail-closed protocol proposal**: evaluate as an optional policy
  integration or documentation pattern; keep the core dependency-free because
  `PolicyHook` already provides first-party fail-closed behavior.
- **#50 Nautilus A2A registry/discovery proposal**: evaluate as optional
  connector or docs-only integration.
- **#26 External API tool integrations**: accept one API/tool family per PR, no
  secrets, no required core dependencies.

## Near-Term Version Plan

This section records the planned direction for the next several LightAgent
versions after `v0.9.5`. Exact scope can still change as issues, pull requests,
and user feedback evolve, but the intended product direction is:

**explicit memory promotion + safer shared memory + reliable hooks + better
observability + stable APIs + enterprise-friendly integration.**

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

### v0.9.1: Runtime Hooks And Middleware

Status: first implementation slice completed.

Goal: add a small, ordered hook layer that unifies today's specialized
extension points without turning LightAgent into a heavy plugin framework.

Why now:

- v0.9.0 already has guardrails, trace events, memory write admission, LightFlow
  approval handlers, checkpoint/resume, and shared-memory prototypes.
- New production needs such as cost control, model routing, prompt enrichment,
  tool auditing, PII redaction, evaluation, and approval policies should not
  require new one-off constructor parameters each time.
- Hook support gives LightAgent a stable extension spine while preserving the
  existing lightweight, inspectable core.

Implemented in the first slice:

- Added `HookContext`, `HookDecision`, and `HookManager`.
- Added ordered sync hooks with isolated hook failures.
- Added `LightAgent(..., hooks=[...])` for `before_run`,
  `before_model_request`, `after_model_response`, `before_tool_call`,
  `after_tool_result`, `before_memory_write`, and `after_memory_write`.
- Added `LightFlow(hooks=[...])` for `before_flow_step`, `after_flow_step`,
  `on_approval_required`, `on_resume`, and `on_rerun`.
- Added trace events for hook replacement, blocking, metadata, and hook
  failures through `hook_decision` and `hook_block`.
- Added `parent_trace_id` and `run_group_id` support to agent traces, flow
  traces, LightFlow step calls, and memory write metadata.
- Added `after_run`, `on_error`, `before_memory_retrieve`, and
  `after_memory_retrieve` to close the core agent and memory-read lifecycle.
- Added async-compatible hook execution and production recipes for redaction,
  budgets, routing, tool policy, memory filtering, export, and evaluation
  sampling.
- Kept existing `agent.run("hello")` and
  `agent.run(query, stream=True, user_id=user_id)` behavior compatible.

Remaining work after v0.9.3:

- Add explicit fail-closed behavior for security policy hooks without changing
  the default failure isolation of observability hooks.
- Add handoff hook support around the stabilized LightSwarm delegation path.
- Continue hardening guardrail and memory policy adapter traces while preserving
  the current public APIs.
- Expand production recipes as new integration targets appear.
- Add pre-registration tool schema diagnostics so malformed tools can be found
  without changing runtime registration behavior.

### v0.9.3: Runtime Hook Hardening And Stream Safety

Status: completed in v0.9.3.

Goal: stabilize the runtime hook lifecycle and stream safety behavior before
adding larger workflow or observability features.

Completed work:

- Close streaming tool-loop limit failures through `_finish_run(...)` so
  `on_error`, `after_run`, and `run_end` stay consistent.
- Add `max_tool_iterations` as an explicit stream tool-call loop limit while
  keeping the default behavior compatible with `max_retry`.
- Add focused regression tests for stream tool-loop limits, hook lifecycle
  closure, and trace behavior on failure.
- Keep async hook support as completed v0.9.2 behavior and continue expanding
  sync/async hook coverage through tests.
- Document how production applications can monitor stream tool-loop errors with
  `on_error` hooks.

Draft usage model:

```python
from LightAgent import LightAgent, HookDecision


def redact_before_model(ctx):
    if ctx.phase == "before_model_request":
        messages = ctx.payload["messages"]
        redacted_messages = redact_private_data(messages)
        return HookDecision.replace(payload={"messages": redacted_messages})

    return HookDecision.continue_()


agent = LightAgent(
    name="assistant",
    role="Answer safely.",
    hooks=[redact_before_model],
)
```

Tool policy example:

```python
def block_sensitive_tool(ctx):
    if ctx.phase == "before_tool_call":
        tool_name = ctx.payload["tool_name"]
        if tool_name in {"transfer_money", "delete_file"}:
            return HookDecision.block(reason="Sensitive tool requires approval")

    return HookDecision.continue_()
```

Supported hook points:

| Area | Hook point | Typical usage |
| --- | --- | --- |
| Run lifecycle | `before_run` | Input cleanup, permission checks, tenant context injection |
| Run lifecycle | `after_run` | Audit logging, evaluation sampling, result persistence |
| Model call | `before_model_request` | Prompt rewriting, PII redaction, model routing, budget checks |
| Model call | `after_model_response` | Output inspection, schema repair, quality scoring |
| Tool call | `before_tool_call` | Tool permission checks, argument validation, approval gating |
| Tool call | `after_tool_result` | Result filtering, error classification, audit logging |
| Memory read | `before_memory_retrieve` | Scope, tenant, user, agent, or trust-level constraints |
| Memory read | `after_memory_retrieve` | Expiration filtering, confidence filtering, re-ranking |
| Memory write | `before_memory_write` | Poisoning checks, deduplication, write-quality scoring |
| Memory write | `after_memory_write` | Audit recording, synchronization to external memory stores |
| Error handling | `on_error` | Fallback, retry classification, alerting |
| Multi-agent | `on_handoff` | Handoff audit, target-agent policy, delegation limits |
| LightFlow | `before_flow_step` | Step input validation, budget checks, cancellation policy |
| LightFlow | `after_flow_step` | Step output validation, trace enrichment, checkpoint metadata |
| LightFlow | `on_approval_required` | Integration with human approval systems |
| LightFlow | `on_resume` | State verification and external context restoration |
| LightFlow | `on_rerun` | Cleanup, historical result reuse, rerun policy checks |

Hook decisions:

| Decision | Semantics |
| --- | --- |
| `continue` | Continue without changing the current operation |
| `replace` | Replace the current payload, such as messages, tool arguments, or memory content |
| `block` | Stop the current operation with a structured reason |
| `retry` | Request a retry for the current model, tool, or flow step |
| `fallback` | Route to a fallback model, agent, tool, or flow branch |
| `metadata` | Attach trace, audit, evaluation, or policy metadata |

Expected outcome:

Developers should be able to extend LightAgent execution in production without
forking the runtime or adding new framework-level parameters for every policy,
observability, evaluation, routing, or enterprise integration requirement.

### v0.9.4: Tool Contracts And Policy Safety

Status: completed in v0.9.4 and released on 2026-07-17.

Goal: make tool schemas inspectable before runtime and let security-sensitive
hooks fail closed explicitly, while keeping existing hooks and tool
registration behavior compatible.

Completed work:

- Added `ToolRegistry.validate_tool_info(tool_info)` and registry-level
  `validate_tools()` diagnostics for names, descriptions, parameter lists,
  duplicate parameters, canonical types, and `required` flags.
- Added `LightAgent.validate_tools()` as a convenience API.
- Kept schema validation opt-in and read-only; invalid legacy schemas are not
  rejected by default.
- Added `PolicyHook` with phase scoping, explicit failure mode, and optional
  sync/async timeout handling.
- Kept plain hook failures isolated while allowing explicitly wrapped policy
  hooks to block on exceptions or timeouts.
- Added `on_handoff` before LightSwarm delegation with block and metadata
  support, structured handoff trace events, parent trace propagation, and
  consistent source `run_end` closure.
- Added focused tests with no model, network, MCP server, or external policy
  dependency.
- Expanded GitHub CI to run the complete tracked test suite on Python 3.10,
  3.11, and 3.12.
- Preserved LightSwarm `user_id`, `metadata`, tracing options, result format,
  retry limits, and tool-iteration limits across entry runs and delegated
  handoffs.

Compatibility requirements:

- Existing callable hooks continue after exceptions by default.
- Existing `register_tool()` overwrite behavior remains unchanged.
- Existing `agent.run()` and streaming return types remain unchanged.
- No CCS or other policy engine is added to the core dependency set.

Expected outcome:

Applications can detect bad tool contracts before model execution and can mark
specific authorization hooks as fail closed without making audit, metrics, or
other observability hooks a new source of downtime.

### v0.9.5: Memory Promotion And Shared Memory Safety

Status: implemented in v0.9.5.

Fix target: v0.9.5 is the first release line for closing the #39 shared graph
memory security risk and the #82 explicit memory promotion workflow.

Goal: make reflection, self-learning, delegation summaries, and shared-memory
evidence safe by default before they can affect future user-facing prompts, and
add the first human-review slice around memory promotion only.

Completed work:

- Add an explicit memory promotion workflow for internal reflection and
  delegation summaries.
- Treat reflection and delegation outputs as non-injectable memory candidates by
  default.
- Add a promotion decision model that can approve, reject, rewrite, or keep a
  candidate non-injectable.
- Add lifecycle hooks such as `before_memory_promote` and
  `after_memory_promote`, or an equivalent promotion callback API, for policy
  and human review.
- Add a lightweight memory-candidate shape that carries `run_id`, `trace_id`,
  candidate ID, memory scope, source agent, trust level, confidence, reviewer
  metadata, and rejection or rewrite reason.
- Support optional policy review for memory promotion with approve, reject,
  rewrite, and keep-non-injectable outcomes.
- Keep memory-review hooks compatible with sync and async hook execution,
  including fail-closed handling for security-sensitive promotion policies.
- Preserve provenance through `source`, `scope`, `trust_level`, `confidence`,
  `agent_name`, `trace_id`, `parent_trace_id`, `run_id`, and derived-memory
  lineage.
- Record promotion candidates, decisions, rewrites, and blocks in trace or
  audit output without exposing raw sensitive memory text by default.
- Record memory-review events such as `memory_promotion_required`,
  `memory_promotion_approved`, `memory_promotion_rejected`,
  `memory_promotion_rewritten`, and `memory_promotion_blocked` as the first
  Human-in-the-loop and Human-on-the-loop audit vocabulary.
- Add fail-closed defaults for unattributed, unreviewed, cross-user, or
  cross-scope internal memory before prompt injection.
- Add tests proving reflection, delegation, and shared-memory candidates cannot
  become prompt-injectable without explicit promotion.
- Treat #39 and #82 as release gates: v0.9.5 includes deterministic tests for
  memory poisoning, cross-user contamination, and unreviewed internal-memory
  promotion paths.
- Document safe patterns for `SharedMemoryPool`, mem0-style graph memory,
  vector memory adapters, and optional external memory backends such as ClawMem.
- Document how external approval queues or review UIs can integrate with memory
  promotion through hooks without becoming core dependencies.

Delivered in v0.9.6:

- Broader human-review surfaces for high-risk tools, handoffs, and LightFlow
  steps.

Still deferred:

- Durable external review queues and admin UI examples.

Expected outcome:

LightAgent should give applications a clear and auditable path from internal
agent evidence to durable prompt context, reducing memory poisoning and
cross-user contamination risks while keeping existing memory backends
compatible. v0.9.5 introduces human review as a narrow memory-promotion
control, not as a general tool or workflow approval system.

### v0.9.6: Observability, Evaluation, And Human Review

Status: implemented in v0.9.6; pending review and release.

Goal: improve production debugging, measurement, and human control over
high-risk actions after the memory-promotion boundary and memory-scoped review
path are explicit.

Completed work:

- Added `TraceSummary`, normalized usage and cost estimates, model/tool latency,
  retry and error categories, review counters, generic exporters, and a JSONL
  audit exporter.
- Added `LightEvaluator` and `EvaluationCase` for output, tool, policy-event,
  recovery, latency, usage, cost, and custom domain checks.
- Added `HumanApprovalHook`, `ApprovalRequest`, `ApprovalDecision`,
  `InMemoryReviewStore`, and `JsonReviewStore` without adding a queue, UI, or
  database dependency.
- Added fail-closed approval, rejection, argument editing, reviewer timeout,
  exact-context approval reuse, multi-action store batches, and trace feedback.
- Added durable LightFlow request IDs and decisions with
  `flow.approve(...); flow.resume(...)`, including approve, reject, edit, and
  respond behavior.
- Extended structured traces with approval and feedback events while preserving
  existing `agent.run()` defaults and result formats.
- Documented evaluation, external trace export, tool/handoff review, durable
  LightFlow approval, batches, and feedback integration.

Human-control expansion checklist completed in v0.9.6:

- Formalize LightFlow `requires_approval`, `approval_handler`, and
  `waiting_approval` as the first Human-in-the-loop checkpoint model for
  deterministic workflows.
- Use `on_approval_required` to notify external approval systems when a
  LightFlow step cannot continue without review.
- Add a small approval request/result shape that can carry `run_id`,
  `trace_id`, action name, tool name, argument summary, source agent, target
  agent, allowed decisions, reviewer metadata, and rejection reason.
- Support approve, reject, edit, and respond decision types for reviewed
  actions, while preserving simpler approve/reject behavior for existing
  LightFlow approvals.
- Use `PolicyHook` on `before_tool_call` for fail-closed checks before
  sensitive tools such as file deletion, payments, database writes, shell
  execution, external API mutation, or customer-impacting actions.
- Use `PolicyHook` on `on_handoff` to review or block delegation to another
  agent before LightSwarm transfers control.
- Use tool schema diagnostics so reviewers and policies can inspect stable tool
  names, descriptions, required arguments, and duplicate or malformed
  parameters before approval.
- Record `hook_decision`, `hook_block`, `handoff`, `guardrail_block`,
  approval, rejection, edit, feedback, and `run_end` events as the audit
  substrate for Human-on-the-loop monitoring.
- Keep first-class human feedback queues, annotation workflows, online/offline
  evaluation dashboards, and web approval UIs optional rather than core
  dependencies.

Expected outcome:

LightAgent should support production environments where teams need to measure
agent quality, inspect failures, review memory-promotion decisions, and keep
humans in control of high-impact external side effects.

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

- **LangGraph / LangChain**: durable execution, checkpointing,
  human-in-the-loop workflows, long-running stateful tasks, and middleware hooks
  around agent/model/tool execution.
- **CrewAI**: combining autonomous agent collaboration with deterministic
  workflow orchestration through Crews and Flows.
- **OpenAI Agents SDK**: handoffs, guardrails, tracing, lifecycle hooks, and
  production-oriented agent execution primitives.
- **Microsoft AutoGen**: multi-agent conversations, collaboration protocols, and
  agent-to-agent coordination.
- **Microsoft Semantic Kernel**: filter pipelines around prompt rendering,
  function invocation, auto function invocation, and policy interception.
- **Pydantic AI**: typed tools, structured output, schema validation, and
  type-safe agent interfaces.
- **LlamaIndex**: data-oriented agents, workflows, RAG, document pipelines, and
  knowledge retrieval.

### Human Control Patterns From External Frameworks

External HITL/HOTL designs suggest a clear split between the lightweight
runtime foundation that belongs in LightAgent core and the heavier product
surfaces that should remain optional. These patterns informed the v0.9.5
memory-review slice and the v0.9.6 human-review implementation:

- **Pause and resume**: OpenAI Agents SDK and LangGraph both model HITL as an
  interruption/pause point that returns pending actions and resumes from saved
  state after review. LightAgent keeps durable LightFlow approval checkpoints
  as the lightweight core version of this pattern.
- **Decision vocabulary**: LangGraph exposes approve, reject, edit, and respond
  decision types. LightAgent v0.9.5 applies approve, reject, and rewrite
  to memory promotion first; v0.9.6 extends approve, reject, edit, and respond
  behavior to tools and workflow checkpoints.
- **Tool-level approval**: OpenAI Agents SDK applies approvals to sensitive
  tool calls, nested agent tools, shell/apply-patch tools, and MCP tools.
  LightAgent maps this to `before_tool_call`, `HumanApprovalHook`, `PolicyHook`,
  Guardrails,
  and tool schema diagnostics rather than adding a separate heavy approval
  runtime.
- **Handoff review**: OpenAI approval surfaces work across handoffs and nested
  agent-as-tool calls. LightAgent keeps `on_handoff` as the core
  LightSwarm review point.
- **Fail-closed policy**: Semantic Kernel filters and OpenAI guardrail/tool
  approval patterns emphasize policy checks before execution. LightAgent
  keep plain hooks failure-isolated, but use `PolicyHook` for fail-closed
  security decisions.
- **Human-on-the-loop monitoring**: LangSmith and Microsoft Responsible AI
  guidance emphasize trace review, feedback capture, annotation queues,
  telemetry, audit logs, and escalation paths. LightAgent v0.9.5 begins
  with memory-promotion review events; v0.9.6 adds broader monitoring
  on the same trace/audit substrate while keeping review queues, dashboards,
  and evaluators optional integrations.

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

This was the first partial response to issues #57, #39, and #1. The first
#39 and #82 release-gate slice shipped in v0.9.5 through explicit memory
promotion.

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

### v0.9.1 Workstream: Runtime Hooks And Middleware

Status: first implementation slice completed in v0.9.1. Run-end, error, and
memory-read lifecycle hooks completed in v0.9.2. Remaining items should move
into the next hook hardening release unless user feedback reprioritizes
observability or persistence work.

Goal: introduce a minimal lifecycle hook system that lets applications observe,
modify, block, retry, or route execution at well-defined points.

### Completed First Slice

- Add a `HookContext` data object that carries stable run metadata and the
  phase-specific payload.
- Add a `HookDecision` return object with explicit control decisions rather
  than relying on exceptions or ad hoc booleans.
- Implement a `HookManager` that runs hooks in deterministic order and isolates
  hook failures.
- Cover run start, model request/response, tool call/result, memory write, and
  LightFlow step, approval, resume, and rerun phases.
- Record hook activity through trace events so blocked operations and payload
  changes are auditable.
- Add trace hierarchy fields through `parent_trace_id` and `run_group_id`.
- Add run-end, error, memory-read, and async-compatible hook execution in the
  v0.9.2 line.

### Completed Follow-up

- Harden stream failure paths so hook lifecycles stay consistent when tool-call
  loops hit safety limits.
- Add `PolicyHook` so security-sensitive hooks can fail closed while ordinary
  observability hooks remain failure-isolated.
- Add `on_handoff` after the LightSwarm handoff contract stabilized.
- Add production recipes for redaction, budgets, routing, tool policy, memory
  filtering, export, and evaluation sampling.
- Add compatibility tests so `agent.run()`, streaming, structured results,
  guardrails, memory policy, LightSwarm, and LightFlow behavior remain
  compatible when no hooks are configured.

### Remaining Work

- Convert or adapt existing guardrails and memory write admission into the new
  lifecycle model where it simplifies implementation, without breaking current
  public APIs.
- Reuse the hook layer for v0.9.5 memory promotion, especially policy review,
  human review, and trace/audit export.
- Document common hook recipes:
  - PII redaction before model calls;
  - budget enforcement before model/tool execution;
  - tool allow/deny policy before execution;
  - OpenTelemetry or Langfuse export;
  - model routing and A/B experiments;
  - prompt enrichment from application context;
  - evaluation sampling after runs;
  - memory promotion approval and rejection.

### Draft API Contract

- `hooks=[callable_or_hook_object]` should be accepted by `LightAgent` and
  optionally by `LightFlow`.
- A simple hook callable should receive one `HookContext` argument and return a
  `HookDecision`, `HookResult`, `None`, or a compatible dictionary.
- `None` should mean continue, so simple observability hooks can avoid boilerplate
  return values.
- Hook objects may expose named methods such as `before_model_request(ctx)` or
  `after_tool_result(ctx)` when that is clearer than branching on `ctx.phase`.
- Hook ordering should be deterministic and documented. Later versions can add
  explicit priority, but the first version should preserve list order.
- Hook failures should be recorded as trace events. The default behavior should
  fail closed only for policy hooks that explicitly request blocking semantics;
  observability hooks should not crash the agent by default.
- Guardrails and `MemoryPolicy.memory_write_admission` should continue to work
  with their current public APIs while the implementation starts routing them
  through the same lifecycle concepts.

### Expected Outcome

LightAgent should gain an extension mechanism that is powerful enough for
production policy and observability work, but small enough to keep the framework
direct, Python-native, and easy to inspect.

### v0.9.5 Workstream: Memory Promotion And Shared Memory Safety

Status: completed as the v0.9.5 release line.

Goal: close the gap between internal agent evidence and future prompt context.
Reflection, self-learning, delegation summaries, and shared-memory evidence
should not become prompt-injectable memory unless an explicit policy or
memory-scoped human review promotes them.

### Completed Work

- Add a memory-candidate representation for reflection and delegation outputs.
- Mark internal candidates as non-injectable by default.
- Add an explicit promotion API or lifecycle hook that can approve, reject,
  rewrite, or keep candidates non-injectable.
- Add a memory-candidate and promotion-decision shape for optional policy or
  human approval of memory promotion.
- Support sync and async memory-review hooks with fail-closed behavior for
  security-sensitive promotion decisions.
- Preserve full provenance and lineage across promotion decisions.
- Add trace/audit events for promotion candidates, approvals, rejections,
  rewrites, blocks, and final decisions.
- Add fail-closed tests for unattributed, unreviewed, cross-user, cross-agent,
  and cross-scope memory candidates.
- Make those tests the v0.9.5 release gate for #39 shared graph memory
  security and #82 memory promotion safety.
- Update memory security docs for SharedMemoryPool, mem0-style graph memory,
  vector memory adapters, and optional ClawMem-style adapters.
- Document memory-review integration patterns for external approval queues,
  ticketing systems, or lightweight admin UIs without adding those systems as
  core dependencies.

### Expected Outcome

LightAgent should reduce shared-memory poisoning risk and provide a clear,
auditable path from internal reflection or delegation evidence to durable user
memory. This release should also provide the first narrow Human-in-the-loop
surface, limited to memory promotion decisions.

### v0.9.6 Workstream: Observability, Evaluation, And Human Review

Status: implemented in v0.9.6; pending review and release.

Goal: support production teams that need measurement, review, and control over
agent behavior after the memory-promotion boundary and memory-review slice are
explicit.

### Completed Work

- Rich trace summaries, latency/usage/retry/error metadata, generic export, and
  local JSONL audit envelopes.
- Dependency-free deterministic evaluation with custom checks and aggregate
  reports.
- Fail-closed tool and handoff review through `HumanApprovalHook`.
- Durable LightFlow approval checkpoints with approve, reject, edit, respond,
  and resume behavior.
- Multi-action review-store batches and human feedback records.
- Approval and feedback trace events for Human-on-the-loop monitoring.

### Expected Outcome

LightAgent should support workflows where a model can plan and prepare actions,
but humans retain control over important external side effects and memory
promotion decisions.

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

### Hook-Based Extensions

- Keep hooks as a runtime extension contract, not a general plugin marketplace.
- Prefer small Python callables and dataclass-style context objects over heavy
  dependency injection.
- Let hooks power optional integrations for observability, evaluation,
  enterprise policy, model routing, rate limiting, and audit export.
- Keep hook payloads explicit and redaction-friendly so trace output does not
  accidentally expose private prompts, memory values, or tool parameters.
- Provide compatibility adapters so current guardrail and memory policy users
  can migrate gradually.

## Recommended Priority

### Immediate P0

- No active P0 item as of 2026-07-21.

### Next P1

- v1.0.0 public API stabilization, compatibility contracts, deprecation policy,
  and production documentation.
- Durable memory-review queue examples that build on v0.9.5 promotion
  candidates without becoming required core dependencies.
- Shared-memory adapter hardening for #1 and follow-up #39 work, especially
  durable graph/vector backends, tenant boundaries, provenance checks, and
  conflict handling.
- External trace/audit adapters and production review-queue examples built on
  the v0.9.6 exporter and approval contracts.

### P2

- Review #81 build-pipeline PR separately as packaging/release hygiene.
- Database-backed workflow and shared-memory adapters.
- Stronger idempotency and distributed execution controls for persistent
  workflows.
- Optional ClawMem adapter shape for #33.
- Lightweight plugin/connector contract for #5.
- CCS optional policy-integration documentation for #76.
- Nautilus/A2A optional connector evaluation for #50.
- External API examples for #26.

### P3

- Visual trace UI.
- Distributed execution and durable worker coordination.

## Next Development Recommendation

After v0.9.6, the next development target should be **v1.0.0 Stable API And
Production Documentation**. The main runtime, workflow, memory-safety,
observability, evaluation, and human-review primitives now exist; the next
priority is making their contracts stable and consistently documented.

Reasoning:

- v0.9.0 covers checkpointed LightFlow runs, resume/rerun, approval nodes,
  memory-safety controls, guardrail templates, and the shared-memory prototype.
- v0.9.3 completes stream tool-loop safety and consistent runtime hook closure.
- v0.9.4 completes tool schema diagnostics, `PolicyHook`, `on_handoff`,
  LightSwarm runtime-context propagation, and full tracked-test CI.
- v0.9.5 adds explicit promotion candidates, promotion decisions,
  `before_memory_promote` / `after_memory_promote`, promotion trace events, and
  fail-closed tests for internal/shared memory safety.
- v0.9.6 adds trace summaries/exporters, deterministic evaluation, tool and
  handoff review, durable LightFlow approvals, and human feedback.
- #1 and follow-up #39 work keep durable shared-memory poisoning, provenance,
  and multi-agent memory boundaries as active P1 concerns.
- Database-backed durability should stay optional so the core package remains
  lightweight.

Suggested first implementation slice:

1. Publish a supported public API inventory and compatibility matrix.
2. Add a deprecation policy and warnings for any API that must change.
3. Tighten type hints and protocol contracts for run results, memory, tracing,
   evaluation, review stores, and workflow stores.
4. Build a production documentation and example matrix for single-agent,
   streaming, tools, memory, LightSwarm, LightFlow, evaluation, and review.
5. Validate packaging, installation, and examples across Python 3.10-3.13.
6. Continue #39 backend-level security validation as a focused parallel track.
