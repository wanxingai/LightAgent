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

The v1.0 release should review this inventory against `LightAgent.__all__`, the
generated package wheel, examples, and CI before declaring the stable surface.
