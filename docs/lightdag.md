# LightDAG: Persistent Dynamic Multi-Agent Workflows

LightDAG is the opt-in v0.11 runtime for workflows whose task graph is not
known in advance. A Worker can submit a typed decomposition or candidate
artifact, but only an application-owned Verifier can accept the decomposition
or publish the artifact. `LightFlow` remains the simpler choice for fixed DAGs.

## Minimal Offline Example

```python
from LightAgent import (
    CallableVerifier,
    LightDAG,
    PermissionSet,
    SecurityContext,
    TaskOutcome,
    TaskSpec,
)

context = SecurityContext(
    user_id="alice",
    tenant_id="acme",
    project_id="reporting",
    permissions=PermissionSet(allowed=frozenset({"dag.task.execute"})),
)
dag = LightDAG(verifiers={"exact": CallableVerifier(
    "exact",
    lambda request: request.candidate_content == request.task.spec.task_id.encode(),
)})
dag.register_worker(
    "local",
    lambda task_context: TaskOutcome.candidate(task_context.task.spec.task_id),
)
dag.create_run([
    TaskSpec(
        task_id="report",
        goal="Produce the report",
        acceptance_contract={"equals": "report"},
        worker_key="local",
        verifier_key="exact",
    )
], run_id="report-run", context=context)

result = dag.run("report-run")
assert result.success
```

The default store is local SQLite and the default artifact store is
`.lightagent/artifacts`. Production applications should pass explicit
`SqliteTaskGraphStore` and `LocalArtifactStore` paths.

Run the complete credential-free repository example with:

```bash
PYTHONPATH=. python example/14.dynamic_dag.py
```

## Worker Contract

A registered Worker must return one of these explicit outcomes:

- `TaskOutcome.candidate(content)`: stage a candidate for completion checks.
- `TaskOutcome.decompose(proposal)`: propose new or reused dependencies.
- `TaskOutcome.blocked(reason)`: stop the task until an operator resolves it.

Plain strings are rejected. A successful model response is not task
completion. `LightAgentWorkerAdapter` accepts only JSON matching the same
outcome contract.

`DecompositionProposal` carries an `expected_graph_revision`. Acceptance is a
single SQLite transaction that validates task and edge limits, unknown
dependencies, cycles, the active attempt lease, and the current graph version.
The parent runs again with phase `integrate` only after all dependencies have
published verified artifacts.

## Verification And Artifacts

`CallableVerifier` adapts deterministic sync or async checks. Every report is
bound to the attempt input snapshot, verifier version/configuration, artifact
hashes, assurance level, diagnostics, and evidence references. Only a `pass`
report can move a staged artifact to `published` and mark a task `verified`.

`LocalArtifactStore` writes immutable, content-addressed blobs. Reads enforce
tenant/project scope, published state, byte length, SHA-256 integrity, and path
containment. Failed verification keeps the candidate staged and unavailable as
a trusted downstream result.

## Persistence And Recovery

Each run stores its graph, tasks, attempts, events, reports, artifacts,
idempotency records, and scheduler lease in SQLite. On resume, expired attempts
are fenced and requeued. An old attempt cannot publish after its lease expires
or after its task is superseded. Reopening a run with a different `DAGConfig`
fails closed with `LA-DAG-RECOVERY-CONFIG-MISMATCH`.

```python
result = dag.run(run_id)              # terminal/paused/blocked runs are unchanged
dag.resolve_blocker(run_id, task_id)  # explicit operator action
result = dag.run(run_id)

dag.pause(run_id)
result = await dag.resume(run_id)
dag.cancel(run_id)
```

Use `supersede_task()` to replace an unfinished task. Verified tasks and
verified downstream consumers are immutable; changing those contracts requires
a new run.

## Security Boundary

Every run requires a `SecurityContext` with tenant and project identity.
Worker attempts receive a narrowing-only child context containing the run,
task, attempt, agent, resources, permissions, network policy, sandbox
requirement, deadline, and policy version. `CapabilityGate` checks the
`dag.task.execute` capability before Worker creation, including tasks that do
not declare a resource.

`ApprovalToken` is operation-, argument-, identity-, resource-, and
policy-version-bound, expires, and is single-use by default. It can be used for
sensitive `CapabilityRegistry` calls. It is not a bearer token for arbitrary
operations and must never contain credentials.

## Scope And Limits

v0.11 is single-host with one active scheduler per run and multiple async
Workers. SQLite must be on a local filesystem. Execution is at-least-once;
fencing protects LightDAG state but cannot undo an external side effect. Use an
idempotent external operation or a dedicated Sandbox/Provider for such work.

Distributed queues, a Web UI, automatic Git merging/deployment, built-in code
sandboxing, and generic formal proof tooling are outside this release. The full
design and acceptance boundaries are documented in the
[v0.11 development plan](lightdag_v011_development_plan.zh-CN.md).
