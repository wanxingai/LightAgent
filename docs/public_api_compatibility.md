## Public API And Compatibility Inventory

This v0.9.7 inventory prepares the v1.0 API freeze. It documents current intent
but does not retroactively make every private method stable. Names beginning
with `_`, raw provider payloads, and undocumented internal trace metadata may
change before v1.0.

### Supported Runtime

- Python 3.10, 3.11, 3.12, and 3.13 are exercised by GitHub CI.
- `agent.run("hello")`, structured `RunResult`, and `stream=True` remain
  compatibility paths.
- Core installation remains provider-focused; `litellm`, `oss`, and `nos` are
  optional extras. Connector `extras` are descriptive and never installed by
  validation.

### Top-Level Public Imports

| Area | Public types and functions |
| --- | --- |
| Runtime | `LightAgent`, `LightSwarm`, `RunResult`, `StreamEvent` |
| Workflow | `LightFlow`, `LightFlowStep`, `LightFlowStepResult`, `LightFlowResult`, `JsonLightFlowStore` |
| Dynamic workflow | `LightDAG`, `TaskSpec`, `TaskOutcome`, `DecompositionProposal`, DAG stores, verifiers, and result/status types |
| Unified security | `SecurityContext`, `CapabilityGate`, `ApprovalToken`, `ProviderManifest` |
| Tools | `ToolRegistry`, `ToolLoader`, `AsyncToolDispatcher`, Python executor functions |
| Skills and MCP | `Skill`, `SkillManager`, `create_skill_tools`, `MCPClientManager` |
| Memory | `MemoryProtocol`, `MemoryScope`, `MemoryPolicy`, `MemoryAdmissionDecision`, `MemoryCandidate`, `MemoryPromotionDecision`, `SharedMemoryPool` |
| Hooks and safety | `HookContext`, `HookDecision`, `HookManager`, `PolicyHook`, Guardrail APIs |
| Review | `ApprovalRequest`, `ApprovalDecision`, `HumanApprovalHook`, review stores, `HumanFeedback` |
| Trace and evaluation | trace recorder/exporters/summaries and `LightEvaluator` report types |
| Connectors | `ConnectorManifest`, `ConnectorValidator`, diagnostics/report types, `validate_connector` |

### Compatibility Contracts For v1.0 Review

- Dataclass field additions should use defaults; removals or semantic changes
  require deprecation first.
- Existing hook phases and decision actions should remain stable. New phases
  may be added without forcing applications to implement them.
- Existing trace event names remain machine-readable contracts; new optional
  metadata may be added, while sensitive raw values should not become required.
- `MemoryProtocol` keeps the minimal `store(data, user_id)` and
  `retrieve(query, user_id)` surface. Metadata support remains capability
  detected for compatibility with older adapters.
- Review stores retain request lookup/save, decision resolution, batch, and
  feedback behavior. LightFlow stores retain checkpoint save/load behavior.
- `ConnectorManifest` composes existing APIs. It does not own activation,
  dependency installation, network sessions, or a marketplace lifecycle.

### Deprecation Policy Proposal

After v1.0, documented public APIs should receive at least one minor release of
deprecation notice before removal. Security fixes may block unsafe behavior
immediately when preserving it would expose users; such changes must include a
clear release note and migration path. Private methods and undocumented
provider-specific payload details are excluded from this promise.

### Example Coverage Matrix

| Capability | Example or guide |
| --- | --- |
| Basic agent and tools | `example/01.single_agent.py`, `example/02.tools_agent.py` |
| Memory and self-learning | `example/03.memory_mem0.py`, `example/05.self_learning.py` |
| Multi-agent and history | `example/04.multi_agent.py`, `example/06.chat_with_history.py` |
| MCP and browser use | `example/07.use_mcp.py`, `example/08.browser_use.py` |
| Tool creation and LightFlow | `example/09.create_tools.py`, `example/10.lightflow.py` |
| Memory adapters | `example/11.vector_memory_adapter.py`, `example/clawmem_memory_adapter.py` |
| Optional provider | `example/12.atlas_cloud.py`, model provider guide |
| Connectors | `example/connectors/local_research`, `example/connectors/enterprise_api` |
| Human review and evaluation | human review and evaluation guides plus tracked tests |
| Dynamic DAG and verified artifacts | `example/14.dynamic_dag.py`, `docs/lightdag.md` |

The v1.0 release should review this inventory against `LightAgent.__all__`, the
generated package wheel, examples, and CI before declaring the stable surface.

## v0.12.0 research baseline (historical API)

The following describes the frozen v0.12.0 source baseline. In the v1.0.0
development branch, research APIs and the panel have moved to the optional
LightResearch package. See the migration section below; these are no longer
default core exports.

Ordinary `run`, `arun`, streaming, tools, Hooks, Memory, LightFlow, LightSwarm,
and existing LightDAG APIs keep their default behavior. `mode="once"` is the
explicit spelling of the default. `mode="persistent"` requires a workspace and
returns `AgentHandle`; turn-scoped streaming/history/session/timeout options are
rejected rather than silently carried into the daemon. Use `ResearchContract`
and `SecurityContext` for persistent configuration.

New opt-in exports: AgentService, AgentHandle, ChatHandle, ResearchContract,
ResearchEvaluator, PromotionPolicy, AgentVersion, CodexAppServerBackend and
MCPToolBridge. The historical reference panel has moved to LightResearch.panel.
The default Codex adapter is exec; experimental App Server and tool bridges are
explicit objects. Unknown transport/configuration/permission requirements fail
closed. No Codex executable or new frontend framework is required for import,
ordinary calls, or native research.

Persistent control records have a separate schema (version 1), leaving v0.11
Session and DAG databases unchanged. Keep the complete control directory when
backing up. Pre-release P0 backend bindings now include transport and network
configuration; use a new session instead of silently importing older unbound or
differently bound engine sessions. See the [research guide](persistent_research.zh-CN.md).

The persistent handle also exposes `reconcile_candidate`, `reconcile_job`,
`propose_contract`, `adopt_contract`, and `prune_workspaces` (dry-run by default).
Contract adoption requires a paused, idle researcher and opens a new comparison
series; it cannot expand runtime permissions or reset consumed budgets.
`ResearchContract` adds bounded safe-retry controls and per-agent Job concurrency;
`AgentService(max_concurrent_jobs=8)` controls the shared Job limit.
`LightAgent.persistent.BackendFailure` lets trusted adapters explicitly declare
safe retries. Unknown failures and side effects are never inferred safe from text.

New versions pin an execution profile and declared mutable-file state. Legacy
records without a profile retain their original content identity and unpinned
behavior, including descendants and contract revisions. Submit a new researcher
to bind the current host configuration; old records are not silently rewritten.

Historical records are available through `records_page(kind, cursor=None,
limit=50, query=None)` and `record(kind, id)`; the existing list-returning
`records()` and `experiments()` remain recent-window compatibility views.
Artifact authorization and `search_results()` use the full agent-owned ledger.
The panel exposes the same paginated experiment history and search.

`instruction_state()` returns a review fingerprint. While paused and idle, the
host may call `archive_instructions(replacement=..., rationale=...,
expected_fingerprint=..., idempotency_key=...)`; alternatively, `workspace_file`
freezes a reviewed project file. This creates an immutable revision and keeps
original receipts, pending messages, budgets and permissions. It never performs
automatic model summarization or resumes research implicitly.

The managed `lightagent_history` workspace namespace contains bounded verified
history and a provenance index. Optional report fields `reuse_query` and
`reuse_experiments` select same-agent, same-series evidence for the following
cycle. History is part of frozen evaluation inputs and execution-profile identity.
`clear_reuse_request()` is a paused-and-idle host recovery operation for the
latest publication's next-cycle selection. It preserves the original report and
does not apply to later publications. Existing instances remain bound to their
execution-profile implementation digest; source upgrades do not silently rebind
immutable versions.

## v1.0.0 development contracts

Current source version: `1.0.0`; not yet released and not a completed
cross-project migration.

- Core: `ExecutionService`, `ExecutionHandle`, `ExecutionLimits`,
  `ExecutionRequirements`, `ControlStore`, `BudgetLedger`, `InteractionRequests`,
  and `WakeupScheduler`. Execution, interaction, and wakeup records declare
  schema version 1. Session and DAG schema numbers are not silently bumped.
- SQLite Session saves append immutable events. Transactions are shared by
  instances in the same thread, CAS/idempotency collisions fail closed, and
  new sessions have verified SHA-256 event chains. Legacy histories remain
  explicitly unanchored; they are not silently rehashed or claimed verified.
- Runtime JobManager remains public but is a Session adapter using the same
  lifecycle/fencing rules as external Jobs. SubagentManager no longer owns a
  separate execution state machine. Restored registrations require host bind();
  unknown historical runners require an explicit reconciliation note to resume.
  Thread cancellation is not claimed as forced termination; unresolved runners
  retain Subagent capacity until host reconciliation.
  Synchronous Job callables now run in a worker thread; use an async callable
  for operations requiring the current event loop.
- HistoryBundle performs offline copy-only backup/restore into new directories.
  SqliteSessionStore.anchor_legacy requires an inspected digest and host note;
  it never rewrites old events or research authority. The frozen 0.12 wheel
  migration/rollback rehearsal is a local release gate, not a general trust importer.
- Backend probes declare isolation, network-control and budget-enforcement
  capabilities. Docker-only cannot fall back to a host Shell or CLI sandbox.
  Opaque backends do not certify hard token or monetary limits.
- Native probe/session bindings now pin the host provider's capability/configuration
  probe. Native control/session files are rejected inside the worker workspace.
  Old bindings are not silently rewritten to bypass these checks.
- Optional supply-chain API: ProviderAttestation (schema 1), ProviderTrustStore,
  AttestedProvider and artifact_digest. Signed releases require explicit host
  approval; signature validity never replaces CapabilityGate or operation approval.
  ProviderManifest adds a binding digest when a host adapter exposes attestation_state().
  Existing unsigned Providers keep their legacy behavior unless the host opts in.
- LightResearch `0.1.0.dev0` is an independently built optional wheel.
  `ResearchService`, `ResearchHandle`, `ResearchContract`, `ResearchEvaluator`,
  `PromotionPolicy`, `AgentVersion` and the debugging panel belong there.
- Legacy `AgentService`/`AgentHandle` and `run(mode="persistent")` require
  explicit `LightResearch.enable_legacy_api()`. This preserves their research
  semantics instead of silently turning them into ordinary tasks.
- Research cycle steering and experiment report search are implemented in
  LightResearch. After the same explicit registration, the old
  `LightAgent.persistent.steering` entry points and
  `ResearchStore.page(..., query=...)` forward to the extension. Ordinary
  `ControlStore.page` works without it. The database schema, stored receipts,
  and version-1 cursor encoding and query binding are unchanged.
- LightResearch projects record, event, storage and Job concurrency capacities
  into the `limits` mapping on new research owner records. Core readers use
  nonempty `limits` first, otherwise the saved legacy `contract`; the mappings
  are not merged, and historical rows are not rewritten. Core-only detached
  Jobs retain these limits and the original protections for immutable research
  records without requiring extension registration.
- Mem0 and Langfuse are optional SDKs. Install `lightagent[mem0]` or
  `lightagent[langfuse]` (or keep independently installed SDKs). The
  `from mem0 import Memory`, `memory=`, and
  `tracetools["TraceToolConfig"]` integration paths are unchanged. Plain
  runs, custom memory adapters and built-in tracing require neither SDK.
- MCP connections and MCP stdio serving require `lightagent[mcp]` or an
  independently installed compatible SDK. Existing `MCPClientManager` imports,
  `setup_mcp(mcp_setting=...)`, and `mcpServers` settings still work. The
  Codex App Server tool bridge validates arguments with `jsonschema` without
  importing MCP unless used as an MCP stdio server.
- The base install includes PyYAML for Skills metadata parsing. `Skill`,
  `SkillManager`, and `create_skill_tools` keep their import paths. Default
  discovery still scans `skills/` or configured `skills_directories`.
- Removed core modules: `persistent.panel`, `persistent.graph`,
  `persistent.contracts`, `persistent.reuse`, `persistent.instructions`, and the
  old research implementation modules. Research tests moved to `tests/research`;
  generic backends, cancellation, storage, flow, memory and guardrail regressions remain.

See [durable execution](durable_execution.zh-CN.md) and the
[v1.0.0 plan](lightagent_v100_development_plan.zh-CN.md) for outstanding release gates.
