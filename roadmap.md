# LightAgent Roadmap

Last updated: 2026-08-15

LightAgent should continue to evolve as a lightweight, low-dependency agent
framework rather than a broad replacement for LangChain, LangGraph, CrewAI, or
LlamaIndex.

The product direction remains:

**Lightweight core + event-sourced Sessions + composable capability Providers +
reliable tool execution + unified Policy + safe memory + deterministic
workflows + OpenAI-compatible model ecosystem.**

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
- **v0.9.6**: Added production trace summaries and exporters, deterministic
  evaluation, tool/handoff human review, durable LightFlow approvals, review
  batches, human feedback, and shared Graph Memory fail-closed write admission
  and audit controls.
- **v0.9.7**: Added the dependency-free Connector manifest and offline
  validation contract, two credential-free examples, expanded Python executor
  adversarial checks, an opt-in real Mem0 Graph security matrix, and the first
  public API compatibility inventory for the v1.0 stabilization line.

### In Development

- **v0.10.0**: Deliver the unified event-sourced Agent Runtime, combining
  durable Sessions, native async execution, Capability Registry and Policy,
  Inbox/Goals/Budgets, compaction and recovery, multi-Agent Jobs/Workflow, and
  standardized Memory/Skills/MCP/RAG Providers while preserving v0.9.x APIs.

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

- Live pull-request state changes faster than this roadmap and should be read
  from GitHub. Documentation-only pull requests do not change the runtime
  version plan or release gates recorded here.

### Active Issues

Immediate security-governance work:

- **#39 Shared graph memory security disclosure**: evaluate a private GitHub
  Security Advisory and possible CVE scope without declaring affected versions
  or a fully patched release before backend-level reproduction is complete.
  v0.9.5 provides framework-level mitigation primitives, not proof that shared
  graph mutation is fully contained.

P1 engineering work:

- **#39 Shared graph memory security disclosure**: v0.9.6 adds a fake-backend
  adversarial cross-user regression, explicit fail-closed write admission, and
  retrieval-filter audit counts. The remaining acceptance criterion is an
  opt-in test against the exact Mem0 Graph version and storage configuration
  used in production.
- **#1 Enhanced memory management for multi-agent systems**: keep shared-memory
  adapter hardening active until durable graph/vector backends have explicit
  tenant, provenance, conflict, and trust-boundary tests.

P2 issues:

- **#26 External API tool bundle**: accept only focused, provider-owned tool
  examples with no secrets, live CI calls, or required core dependencies.
- **#50 Nautilus A2A registry/discovery proposal**: keep vendor registration,
  wallets, and token economics in an external optional connector.

Resolved or ready to close:

- **#5 Custom plugin/integration development**: v0.9.7 delivered the optional,
  dependency-free Connector manifest, offline validator, examples, and
  contributor documentation without adding a marketplace runtime.
- **#33 Optional ClawMem memory backend**: #74 delivered the optional
  dependency-free adapter example, documentation, and fake-client tests.

Not planned for the core repository:

- Broad marketplace, hosted review UI, hosted observability dashboard, or
  external API bundle in the default package.

## Near-Term Version Plan

This section records the planned direction for the next several LightAgent
versions after `v0.9.7`. Exact scope can still change as issues, pull requests,
and user feedback evolve, but the intended product direction is:

**event-sourced runtime + composable capability providers + unified policy +
long-task control + recoverable context + stable APIs.**

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

Status: the framework-level memory-promotion boundary was implemented in
v0.9.5. Backend-level validation for #39 remains open.

Security scope: v0.9.5 is the first mitigation release for the #39 shared graph
memory risk and completes the #82 explicit memory promotion workflow. It is not
yet evidence that every shared Graph Memory backend is fully remediated.

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
- Treat #39 as an ongoing backend-level security validation item. v0.9.5
  includes deterministic framework tests for cross-user filtering and
  unreviewed internal-memory promotion paths, but does not yet prove containment
  against a realistic shared Graph Memory mutation pipeline.
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

Status: completed in v0.9.6 and released on 2026-07-30.

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

### v0.9.7: Security Validation, Connector Contract, And Release Hardening

Status: released on 2026-08-15.

Goal: close the remaining security and extensibility gaps before the v1.0 API
freeze. v0.9.7 should be a bridge release: small enough to ship quickly, but
strong enough to reduce release risk around Python execution, shared memory,
and third-party integrations.

Primary themes:

- **Security validation first**: finish the #39 backend-level validation track
  before declaring shared Graph Memory risks fully handled.
- **Safer execution tools**: build on merged #85 and extend Python executor
  tests beyond direct imports into attribute access, `getattr`, subscripted
  lookups, dynamic dispatch, import aliases, and builtins escape patterns.
- **Lightweight connector contract**: address #5 with a small Python-native
  contract for packaging Tools, Skills, MCP server settings, Hooks, memory
  adapters, optional dependencies, and documentation.
- **v1.0 readiness**: tighten public API inventory, compatibility promises,
  examples, packaging, and release notes before the stable line.

Implemented work:

- Add a `docs/security_shared_graph_memory_validation.md` guide that separates
  framework-level mitigations from backend-specific Mem0 Graph validation.
- Add an opt-in Graph Memory regression matrix for the exact Mem0 Graph version
  and storage settings used by maintainers or downstream deployments.
- Add adversarial memory tests for cross-user poisoning, low-trust relation
  mutation, trusted-fact overwrite, entity-neighborhood merge, and retrieval
  audit counts.
- Extended merged #85 with a table-driven `_safe_import_check` regression suite
  for direct calls, attribute-style calls, dynamic dispatch helpers, import
  aliases, `__dict__`/subscript access, and safe false-positive cases.
- Document Python executor limitations clearly: AST filtering is defense in
  depth, not a complete sandbox; high-risk deployments should wrap
  `execute_python_code` with `PolicyHook`, Human Review, container isolation,
  timeout limits, network restrictions, and dependency-install controls.
- Introduce a minimal connector manifest shape, such as a dataclass or plain
  dictionary, with fields for `name`, `version`, `tools`, `skills`,
  `mcp_servers`, `hooks`, `memory_adapters`, `extras`, and `docs`.
- Add connector validation utilities that inspect tool schemas, optional
  dependency declarations, unsafe import hints, duplicate tool names, and
  missing documentation without loading network services.
- Provide two dependency-free connector examples:
  - a local research connector that bundles a search-style tool and a Skill;
  - an enterprise API connector skeleton that shows auth/config placeholders
    without shipping secrets or provider SDKs.
- Add a contributor guide for "build a connector in 10 minutes" using existing
  Tools, Skills, MCP, Hooks, and `MemoryProtocol` primitives.
- Prepare v1.0 compatibility docs: public API inventory, deprecation policy,
  supported Python versions, dependency extras, and example coverage matrix.

Release gates:

- #39 has either a private-security follow-up path or a documented public
  validation status that avoids overstating remediation.
- #85 or equivalent Python executor hardening tests pass locally and in CI.
- Connector contract remains optional and dependency-free in the core package.
- Existing `LightAgent`, `LightSwarm`, `LightFlow`, tracing, evaluation,
  review, memory, and streaming compatibility tests remain green.
- Docs clearly distinguish built-in primitives from optional integration
  examples.

Release validation: 193 passed, 1 opt-in Mem0 Graph test skipped, package
compilation and wheel build passed, `git diff --check` passed, and GitHub CI
passed on Python 3.10, 3.11, 3.12, and 3.13.

Expected outcome:

LightAgent enters the v0.10 runtime-evolution phase with fewer loose security
threads, a practical answer to custom integrations, and clearer boundaries
around what the lightweight core will and will not own.

### Post-v0.9.7 Runtime Design Guardrails

The next development line should strengthen the runtime without turning the
core package into a hosted platform or a mandatory collection of heavyweight
integrations.

- Preserve `agent.run("hello")`, `stream=True`, structured results, existing
  Tools, Hooks, Memory backends, LightSwarm, and the LightFlow chain API.
- Make every model-visible message, tool result, memory item, approval result,
  steering message, and compaction summary reconstructable from durable Session
  events.
- Separate capability execution from policy decisions: a Provider implements
  an operation, while Policy, Sandbox, Guardrails, and Approval decide whether
  that operation may run.
- Require child Agents, Skills, and Workflow steps to inherit or reduce parent
  permissions; task code must never expand its own capability set.
- Make the runtime async-first while retaining synchronous compatibility
  wrappers.
- Keep Browser, Docker, LSP, vector databases, WebUI frameworks, and hosted
  services as optional Providers or upper-layer product capabilities.
- Distinguish model errors, tool failures, policy denials, approval waits,
  budget exhaustion, cancellation, and context overflow with explicit states
  and error codes.

### v0.10.0: Unified Event-Sourced Agent Runtime

Status: implementation candidate completed on `codex/develop-v0.10.0`;
release validation is in progress.

Goal: deliver one coherent runtime release that combines the previously
planned v0.10.0-v0.15.0 capabilities without breaking v0.9.x applications.
The work remains ordered as six internal milestones, but there are no separate
public v0.11.0-v0.15.0 releases in this plan.

Implementation delivered in the v0.10.0 development PR:

- Versioned Session events, in-memory/JSONL/SQLite stores, replay, pagination,
  checkpoints, fork lineage, migration hooks, context/trace projection, and
  explicit incomplete-Turn detection.
- Compatible `arun()`/`astream()` entry points and durable model/tool/runtime
  lifecycle recording without changing default `run()` return behavior.
- Scoped Capability Registry, Provider lifecycle, deterministic conflict
  diagnostics, narrowing-only permissions, unified Policy decisions, audit
  configuration digests, and adapters for Tools, Memory, Skills, MCP, and
  LightFlow.
- Durable Inbox, Goals, Budgets, progress detection, Jobs, bounded subagents,
  context budgets, deterministic/summary compaction, oversized-tool spill
  references, Session control events, and restart restoration.
- Deterministic Skill precedence, conflict reporting, nested `AGENTS.md`
  discovery, MCP Streamable HTTP/reconnect/refresh/namespaces/credential
  headers, SQLite FTS5 RAG, and citation-based cross-Session search.
- Focused v0.10 protocol, persistence, corruption, policy, runtime, async,
  compatibility, and retrieval tests plus complete legacy regression testing.

External validation still required before release:

- Python 3.10-3.13 GitHub Actions, package build/install, and real provider
  smoke tests.
- Fault injection against real MCP Streamable HTTP, process interruption,
  concurrent persistent writes, and context-overflow provider responses.
- Contract tests for optional Browser, Terminal, Shell, LSP, vector, sandbox,
  and hosted-service Providers supplied outside the lightweight core.

#### Milestone 1: Event-Sourced Sessions And Native Async

- Add versioned `Session`, `SessionEvent`, and `SessionStore` contracts.
- Define Session, Turn, Step, Message, Model, Tool, Approval, Error, and
  lifecycle events with schema validation and migration hooks.
- Provide dependency-free in-memory and JSONL stores plus an optional SQLite
  store based on the Python standard library.
- Add Session export, pagination, replay, recovery, and incomplete-Turn
  detection.
- Derive model context and the current `TraceRecorder` view from the same event
  history instead of maintaining unrelated sources of truth.
- Add native `agent.arun()` and retain `run()` as a compatibility wrapper.
- Record balanced model request/response and tool request/result pairs with
  explicit interrupted and failed terminal states.

#### Milestone 2: Capability Registry And Unified Policy

- Add `CapabilityProvider` and `CapabilityRegistry` protocols with mount,
  start, health, reload, stop, and unmount lifecycle methods.
- Support Runtime, Session, and Agent scopes with deterministic resolution and
  conflict diagnostics.
- Define protocols for Model, Tool, FileSystem, Shell, Terminal, Browser, Web,
  LSP, Memory, RAG, Subagent, Workflow, Interaction, Sandbox, Credential,
  Policy, and Telemetry Providers.
- Adapt existing Tools, MCP, Memory, Connector, LightFlow, Hooks, Guardrails,
  and approval APIs instead of introducing a parallel plugin runtime.
- Add capability metadata for read/write/network/execute behavior, risk,
  timeout, output limits, cancellation, persistence, and optional dependencies.
- Route sensitive operations through one Policy decision path and record the
  Provider name, version, and configuration digest in audit events.

#### Milestone 3: Agent Inbox, Goals, And Budgets

- Add a durable Agent Inbox for `followup`, `steering`, `context`, and
  `approval` messages.
- Queue and consume messages in order, injecting steering only at safe Step
  boundaries.
- Add durable Goals with acceptance criteria, subgoals, completion evidence,
  blockers, and status transitions.
- Add model-call, tool-call, token, time, and estimated-cost budgets.
- Support pause, resume, cancel, and continue through Session events.
- Add no-progress detection, repeated-tool detection, bounded retry, and
  message idempotency keys.

#### Milestone 4: Context Compaction, Checkpoints, And Fork

- Add model-aware token accounting and configurable context budgets.
- Implement two-stage compaction: deterministic trimming first, optional LLM
  summarization second.
- Spill oversized tool results outside the prompt while retaining event-backed
  references and integrity metadata.
- Persist compaction summaries and covered event ranges as versioned Session
  events.
- Add Session checkpoints, restore validation, and Fork from a selected event
  boundary.
- Support bounded recovery from context-overflow errors and an optional
  dedicated summarization model.

#### Milestone 5: Multi-Agent, Jobs, And Workflow Unification

- Unify LightSwarm, handoff, and subagent lifecycle events while preserving
  existing LightSwarm behavior.
- Support one-shot, persistent, and Session-Fork subagents with depth, count,
  concurrency, and budget limits.
- Add Agent-tree inspection, messaging, interruption, resume, and result
  collection.
- Freeze auditable child-permission snapshots and prohibit capability
  escalation.
- Add background Jobs with status, incremental output, cancellation, and Inbox
  completion notifications.
- Evolve LightFlow into the common Workflow Provider for fixed DAGs, dynamic
  model-planned workflows, checkpoints, approvals, reruns, and parallel steps.
- Add optional persistent Terminal and LSP Providers without making them core
  dependencies.

#### Milestone 6: Memory, Skills, MCP, And Knowledge Standardization

- Standardize Working, Session, Workspace, User, and Shared Memory scopes with
  owner, tenant, provenance, TTL, trust, sensitivity, and admission metadata.
- Keep automatic Memory writes and promotion behind `MemoryPolicy`, Policy,
  and optional approval.
- Support user, workspace, nested-directory, managed, and built-in Markdown
  Skills with deterministic precedence and conflict diagnostics.
- Add compatible project instruction discovery such as `AGENTS.md` without
  runtime self-modification.
- Add MCP Streamable HTTP, reconnect, tool-list refresh, namespace isolation,
  and external Credential Provider integration while retaining stdio/SSE
  configuration compatibility.
- Define a Retrieval/RAG Provider and ship an optional SQLite FTS5 minimum
  implementation; keep embeddings, vector databases, reranking, and hybrid
  retrieval optional.
- Add cross-Session text search with citations while keeping Session Search
  separate from knowledge-base retrieval.

#### v0.10.0 Compatibility Commitments

- Preserve `agent.run("hello")`, `stream=True`, structured results, existing
  Tools, Hooks, Guardrails, Memory backends, LightSwarm, and LightFlow APIs.
- Existing users can adopt Session, Registry, Inbox, Goal, compaction,
  subagent, and knowledge features incrementally; none becomes mandatory for a
  basic Agent.
- Existing Trace, Tool, Memory, Hook, MCP, LightSwarm, and LightFlow data is
  exposed through compatibility adapters instead of forced migration.
- Browser, Docker, LSP, vector databases, hosted services, and WebUI frameworks
  remain optional.

#### v0.10.0 Release Gates

- Every model request can be reconstructed deterministically from persisted
  Session events, and model/tool/approval records remain balanced.
- Process interruption, EventLog failure, context overflow, Provider failure,
  and incomplete Turns have explicit recoverable or terminal states.
- Provider contract and cleanup tests prove that replacement and unload do not
  leak tools, listeners, processes, credentials, or stale registrations.
- Write, network, execution, credential, and persistence operations cannot
  bypass Policy, approval, scope inheritance, or audit handling.
- Restart preserves Inbox order, Goal state, pending approvals, budgets,
  checkpoints, and idempotency markers.
- Compaction preserves unresolved Goals, approvals, decisions, file changes,
  tool lineage, and replay integrity.
- Child Agent and Job failures cannot erase parent state; concurrent writes are
  denied or serialized unless explicitly allowed.
- Workflow and Agentic Loop execution use the same Session, capability,
  Policy, approval, budget, and recovery contracts.
- Memory, Skill, MCP, RAG, and Session Search retain source, owner, scope, and
  provenance metadata; MCP reconnect cannot duplicate tools.
- The Runtime remains usable without vector, Browser, Docker, hosted service,
  or model-gateway dependencies.
- The complete v0.9.7 compatibility suite passes on Python 3.10-3.13, together
  with replay, migration, corruption, fault-injection, long-task, concurrency,
  security, package-build, and import tests.

### v1.0.0: Stable Runtime And Ecosystem

Goal: freeze the runtime contracts only after they have survived multiple
pre-1.0 releases and fault-oriented validation.

Planned work:

- Freeze the public API, Provider protocols, Session event schemas, Policy
  decisions, and compatibility adapters.
- Publish a versioned deprecation and migration policy with tooling for v0.9.x
  Session, Trace, Tool, Memory, Hook, LightSwarm, and LightFlow users.
- Provide a Headless Runner, Python SDK, and optional JSON-RPC service surface.
- Publish official Provider templates and contract-test kits.
- Complete multilingual production documentation and the supported example
  matrix.
- Add OpenTelemetry, Langfuse, and JSONL exporters through optional adapters.
- Establish performance, recovery, tool-call, multi-agent, and workflow
  reliability benchmarks.
- Automate signed package build, PyPI publishing, release notes, and rollback
  checks.

Release gates:

- Public contracts have passed the complete v0.10.0 milestone suite and at
  least one release-candidate or stabilization-patch compatibility cycle.
- Event schemas support forward migration and deterministic replay.
- Long-task interruption recovery passes in deterministic test environments.
- Multi-Agent, approval, compaction, MCP, and Provider lifecycle paths pass
  fault-injection tests.
- Core installation does not require Browser, Docker, vector databases, model
  gateway SDKs, or Web frameworks.
- The v0.9.x-to-v1.0 migration guide and compatibility suite are complete.

### v1.1.0: Enterprise Integration

Goal: make LightAgent easier to embed into internal systems after the runtime
contracts are stable.

Planned work:

- Add multi-tenant policy templates and reference deployment profiles.
- Provide tool-level permission, credential, and audit patterns.
- Add optional Docker and service-wrapper deployment templates.
- Improve model routing guidance for compatible endpoints, LiteLLM, local
  inference, and private gateways.
- Add enterprise examples without placing business workflows or hosted user
  interfaces in the core package.

### Unified v0.10.0 Quality Gates

Every internal v0.10.0 milestone must extend, not replace, the following
validation layers. Passing an early milestone does not authorize releasing a
partial v0.10.0 as the final version:

1. Protocol and state-machine unit tests.
2. Provider contract and resource-cleanup tests.
3. Session replay, migration, projection, and corruption tests.
4. Compatibility tests for all v0.9.7 public APIs.
5. Security tests for Policy, Sandbox, Approval, Credential, and scope
   inheritance.
6. Fault injection for model streams, tools, stores, MCP, Providers, Jobs, and
   subagents.
7. Long-task tests covering budgets, compaction, checkpoint, resume, and
   idempotency.
8. Python 3.10, 3.11, 3.12, and 3.13 CI plus package build and import checks.

Suggested release cadence:

| Version | Theme | Suggested cycle |
| --- | --- | --- |
| v0.10.0 | Unified event-sourced Agent Runtime | 24-36 weeks, milestone-driven |
| v1.0.0 | API freeze and production hardening | After v0.10 stabilization gates |
| v1.1.0 | Optional enterprise integration | Post-v1.0 feedback-driven |

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
framework-level #39 mitigation and the #82 promotion boundary shipped in v0.9.5
through explicit memory promotion.

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
- Make those tests the v0.9.5 framework-level release gate for #82 memory
  promotion safety and the first mitigation checkpoint for #39. Keep realistic
  shared Graph Memory backend tests as follow-up acceptance criteria.
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

Status: completed in v0.9.6 and released on 2026-07-30.

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

### v0.9.7 Workstream: Security Validation And Connector Contract

Status: released on 2026-08-15.

Goal: harden the remaining high-risk surfaces and define a minimal custom
integration path before the v1.0 API freeze.

### Implemented Work

- Treat #39 shared Graph Memory validation as the top security workstream:
  keep public wording conservative, move reproduction/version scoping into an
  appropriate private advisory workflow, and add backend-specific opt-in tests.
- Build on merged #85 with broader Python executor AST blocklist hardening.
- Expand Python executor security regression tests for:
  - `builtins.eval`, `builtins.exec`, and `builtins.compile`;
  - `getattr(obj, "eval")`, `getattr(obj, "system")`, and similar helpers;
  - `obj.__dict__["eval"](...)` and other subscripted call patterns;
  - aliased imports and nested dangerous module access;
  - benign math/list/string code that should remain allowed.
- Add docs that position `execute_python_code` as a controlled utility, not a
  complete sandbox. Recommend tool allowlists, `PolicyHook`, Human Review,
  container-level isolation, timeout limits, and dependency-install controls.
- Define a dependency-free connector manifest and validation helper for #5.
- Show how a connector can bundle:
  - one or more Python tools;
  - Skills and `SKILL.md` instructions;
  - MCP server settings;
  - lifecycle hooks;
  - optional memory adapters;
  - optional dependency extras;
  - usage docs and examples.
- Add at least two connector examples that run without live credentials.
- Update docs so contributors understand the difference between core
  primitives, optional connectors, and unsupported marketplace/runtime hosting.
- Start v1.0 compatibility inventory for public imports, dataclasses, hook
  phases, trace event names, review-store methods, LightFlow store methods,
  and memory protocol behavior.

### Expected Outcome

LightAgent should have a safer Python execution story, a clearer response to
the shared Graph Memory disclosure, and a small but useful extension path for
domain integrations, while keeping v1.0 focused on stability instead of new
surface area.

### Post-v0.9.7 Runtime Workstreams

The earlier plan split runtime evolution across v0.10.0-v0.15.0. These scopes
are now consolidated into one public **v0.10.0 Unified Event-Sourced Agent
Runtime** release with six ordered internal milestones:

1. Session events, stores, replay, projection, and native async execution.
2. Capability Registry, Provider lifecycle, scopes, and unified Policy.
3. Durable Inbox, Goals, budgets, steering, and cancellation.
4. Context compaction, checkpoints, restore, and Session Fork.
5. Subagents, background Jobs, and Workflow/Agent Loop unification.
6. Standardized Memory, Skills, MCP, Retrieval, and RAG Providers.

The detailed scope and release gates are maintained in the Near-Term Version
Plan. v1.0 is deferred until the complete v0.10.0 runtime has passed its
compatibility, replay, recovery, security, and stabilization gates.

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

- Respond to the #39 advisory/CVE request, move reproduction and version-scoping
  details into a private security workflow, and avoid naming affected or fully
  patched versions until the shared Graph Memory test matrix is complete.
- Run the opt-in matrix against every maintained Mem0 Graph and storage
  configuration before changing public remediation claims.

### Next P1

- Start **v0.10.0 Unified Event-Sourced Agent Runtime** with the smallest
  stable Session event model and compatibility adapters, then advance through
  all six internal milestones under the same public version.
- Implement native `arun()` without changing `run()` or streaming behavior.
- Add in-memory, JSONL, and optional SQLite Session stores with replay and
  incomplete-Turn recovery tests.
- Convert Trace into a projection of Session history while preserving current
  Trace APIs and exporters.
- Continue #39 backend validation as an independent security release gate.

### P2

- Prepare the v0.10.0 Capability Registry milestone and Provider contract-test
  fixtures in parallel, but do not route production execution through them
  before Session invariants are stable.
- Add fault-injection fixtures for interrupted model streams, tool timeout,
  EventLog write failure, and concurrent Session recovery.
- Keep external Provider examples focused, optional, credential-free in CI,
  and outside the required core dependency set.

### P3

- Inbox, Goal, Budget, compaction, subagents, background Jobs, Workflow, MCP,
  and RAG remain required v0.10.0 milestones and must land after their Session
  and Provider prerequisites instead of accumulating in one unreviewable
  change.
- Visual trace UI and distributed worker coordination remain upper-layer or
  post-protocol work.

## Next Development Recommendation

The next development target is **v0.10.0 Unified Event-Sourced Agent Runtime**.
It includes the complete former v0.10.0-v0.15.0 scope. Implementation remains
milestone-ordered, but the public version is released only after all six
milestones and their combined quality gates pass.

Reasoning:

- Trace, Hooks, review, Memory, LightFlow, and streaming currently record
  related lifecycle data through different surfaces; one durable EventLog is
  required before reliable resume and context reconstruction can be promised.
- Long-running Agent execution needs native async cancellation and recovery
  semantics rather than additional wrappers around the current synchronous
  loop.
- Capability Registry and Policy unification depend on stable Session identity,
  event ordering, and audit records, so milestone 1 must precede milestone 2
  even though both ship in v0.10.0.
- The six-milestone v0.10.0 plan reduces the risk of freezing immature
  contracts in v1.0 while keeping development increments independently
  reviewable and testable.
- Optional stores and Providers preserve the lightweight core and let
  LightWorker or other products supply Browser, Docker, WebUI, and business
  workflow implementations.

First v0.10.0 implementation slice:

1. Publish versioned Session event dataclasses and an in-memory store.
2. Record one non-streaming Agent run as balanced Session, Turn, Model, Tool,
   and terminal events.
3. Rebuild current Trace events and model context from that Session history.
4. Add JSONL persistence, replay, incomplete-Turn detection, and corruption
   tests.
5. Add native `arun()` and prove `run()` plus `stream=True` compatibility.
6. Add optional SQLite storage only after the store contract passes the same
   replay and migration suite.
