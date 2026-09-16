import asyncio

import pytest

from LightAgent.capabilities import CapabilityRegistry, CapabilityRisk, PermissionSet
from LightAgent.dag import (
    CallableVerifier,
    ContextBuilder,
    DAGConfig,
    DAGContextBudget,
    DAGError,
    DAGRunStatus,
    DAGTask,
    DAGTaskStatus,
    DecompositionProposal,
    LightDAG,
    LightDAGProvider,
    LocalArtifactStore,
    SqliteTaskGraphStore,
    TaskOutcome,
    TaskAttempt,
    TaskSpec,
    TaskState,
    VerificationVerdict,
)
from LightAgent.security import SecurityContext


def security(run_id=None, *, tenant="tenant-a", project="project-a"):
    return SecurityContext(
        user_id="alice",
        tenant_id=tenant,
        project_id=project,
        run_id=run_id,
        permissions=PermissionSet(
            allowed=frozenset({"dag.task.execute"}),
            max_risk=CapabilityRisk.SENSITIVE,
        ),
    )


def make_dag(tmp_path, verifier, *, config=None):
    return LightDAG(
        store=SqliteTaskGraphStore(tmp_path / "dag.sqlite3"),
        artifact_store=LocalArtifactStore(tmp_path / "artifacts"),
        verifiers={"verify": verifier},
        config=config,
    )


def spec(task_id="root", *, worker="worker", verifier="verify", decomposer=None, depends_on=()):
    return TaskSpec(
        task_id=task_id,
        goal=f"produce {task_id}",
        acceptance_contract={"equals": task_id},
        worker_key=worker,
        verifier_key=verifier,
        decomposer_key=decomposer,
        depends_on=tuple(depends_on),
    )


def test_lightdag_requires_explicit_verifier_and_structured_worker_output(tmp_path):
    dag = make_dag(tmp_path, CallableVerifier("verify", lambda request: True), config=DAGConfig(max_attempts_per_task=1))
    dag.register_worker("worker", lambda context: "plain text is not a TaskOutcome")
    dag.create_run([spec()], run_id="strict", context=security())

    result = dag.run("strict")

    assert result.status == DAGRunStatus.FAILED
    assert result.failed_tasks == ["root"]
    assert "plain text" not in repr(dag.events("strict"))

    missing = LightDAG(
        store=SqliteTaskGraphStore(tmp_path / "missing.sqlite3"),
        artifact_store=LocalArtifactStore(tmp_path / "missing-artifacts"),
    )
    missing.register_worker("worker", lambda context: TaskOutcome.candidate("root"))
    with pytest.raises(DAGError, match="VERIFIER-UNAVAILABLE"):
        missing.create_run([spec()], context=security())


def test_lightdag_publishes_only_verified_artifacts_and_enforces_scope(tmp_path):
    verifier = CallableVerifier("verify", lambda request: request.candidate_content == b"root")
    dag = make_dag(tmp_path, verifier)
    dag.register_worker("worker", lambda context: TaskOutcome.candidate("root"))
    dag.create_run([spec()], run_id="simple", context=security())

    result = dag.run("simple")
    manifest = result.root_artifacts["root"][0]

    assert result.success is True
    assert manifest.state == "published"
    assert dag.artifact_store.read(manifest, security("simple")) == b"root"
    with pytest.raises(PermissionError, match="tenant/project"):
        dag.artifact_store.read(manifest, security("simple", tenant="tenant-b"))


def test_dynamic_decomposition_runs_children_concurrently_repairs_and_integrates(tmp_path):
    started = set()
    both_started = asyncio.Event()
    active = 0
    max_active = 0

    async def worker(context):
        nonlocal active, max_active
        task_id = context.task.spec.task_id
        if task_id == "root" and context.attempt.phase == "solve":
            proposal = DecompositionProposal(
                parent_task_id="root",
                new_tasks=(spec("a"), spec("b")),
                rationale="independent parts",
                composition_contract={"join": ["a", "b"]},
                expected_graph_revision=context.run.graph_revision,
            )
            return TaskOutcome.decompose(proposal)
        if task_id in {"a", "b"}:
            active += 1
            max_active = max(max_active, active)
            started.add(task_id)
            if len(started) == 2:
                both_started.set()
            await asyncio.wait_for(both_started.wait(), timeout=1)
            active -= 1
            if task_id == "b" and context.attempt.attempt_no == 1:
                return TaskOutcome.candidate("bad-b")
            return TaskOutcome.candidate(task_id)
        assert context.attempt.phase == "integrate"
        assert set(context.dependency_artifacts) == {"a", "b"}
        return TaskOutcome.candidate("root")

    def verify(request):
        if request.kind == "decomposition":
            return True
        expected = request.task.spec.task_id.encode()
        if request.candidate_content == expected:
            return True
        return {"verdict": "fail", "diagnostics": ["candidate did not match the task contract"]}

    dag = make_dag(tmp_path, CallableVerifier("verify", verify))
    dag.register_worker("worker", worker)
    dag.create_run([spec(decomposer="verify")], run_id="dynamic", context=security())

    result = asyncio.run(dag.arun("dynamic"))
    tasks = {task.spec.task_id: task for task in dag.list_tasks("dynamic")}

    assert result.status == DAGRunStatus.SUCCEEDED
    assert max_active == 2
    assert tasks["a"].state.status == DAGTaskStatus.VERIFIED
    assert tasks["a"].spec.created_by_task_id == "root"
    assert tasks["b"].state.attempt_count == 2
    assert tasks["root"].state.attempt_count == 2
    assert any(event.type == "dag.decomposition.accepted" for event in dag.events("dynamic"))


def test_restart_expires_stale_attempt_and_resumes_from_sqlite(tmp_path):
    path = tmp_path / "dag.sqlite3"
    artifacts = tmp_path / "artifacts"
    config = DAGConfig(task_lease_seconds=1)
    verifier = CallableVerifier("verify", lambda request: request.candidate_content == b"root")
    first = LightDAG(
        store=SqliteTaskGraphStore(path),
        artifact_store=LocalArtifactStore(artifacts),
        verifiers={"verify": verifier},
        config=config,
    )
    first.register_worker("worker", lambda context: TaskOutcome.candidate("root"))
    first.create_run([spec()], run_id="recover", context=security())
    _, stale = first.store.claim_ready_task("recover", "crashed-worker", 0.01)

    import time
    time.sleep(0.02)
    recovered = LightDAG(
        store=SqliteTaskGraphStore(path),
        artifact_store=LocalArtifactStore(artifacts),
        verifiers={"verify": verifier},
        config=config,
    )
    recovered.register_worker("worker", lambda context: TaskOutcome.candidate("root"))

    result = recovered.run("recover")

    assert result.status == DAGRunStatus.SUCCEEDED
    assert recovered.store.get_attempt(stale.attempt_id).status.value == "expired"
    assert any(event.type == "dag.attempt.expired" for event in recovered.events("recover"))


def test_recovery_rejects_changed_scheduler_configuration(tmp_path):
    path = tmp_path / "dag.sqlite3"
    artifacts = tmp_path / "artifacts"
    verifier = CallableVerifier("verify", lambda request: True)
    original = LightDAG(
        store=SqliteTaskGraphStore(path),
        artifact_store=LocalArtifactStore(artifacts),
        verifiers={"verify": verifier},
        config=DAGConfig(max_concurrency=2),
    )
    original.register_worker("worker", lambda context: TaskOutcome.candidate("root"))
    original.create_run([spec()], run_id="config", context=security())

    changed = LightDAG(
        store=SqliteTaskGraphStore(path),
        artifact_store=LocalArtifactStore(artifacts),
        verifiers={"verify": verifier},
        config=DAGConfig(max_concurrency=3),
    )
    changed.register_worker("worker", lambda context: TaskOutcome.candidate("root"))

    with pytest.raises(DAGError, match="RECOVERY-CONFIG-MISMATCH"):
        changed.run("config")


def test_verification_failure_never_publishes_staged_artifact(tmp_path):
    verifier = CallableVerifier(
        "verify",
        lambda request: {"verdict": VerificationVerdict.FAIL.value, "diagnostics": ["no"]},
    )
    dag = make_dag(tmp_path, verifier, config=DAGConfig(max_attempts_per_task=1))
    dag.register_worker("worker", lambda context: TaskOutcome.candidate("wrong"))
    dag.create_run([spec()], run_id="rejected", context=security())

    result = dag.run("rejected")

    assert result.status == DAGRunStatus.FAILED
    assert dag.store.list_artifacts("rejected", state="published") == []
    staged = dag.store.list_artifacts("rejected", state="staged")
    assert len(staged) == 1
    with pytest.raises(PermissionError, match="staged"):
        dag.artifact_store.read(staged[0], security("rejected"))


def test_blocked_run_requires_explicit_resolution_before_execution(tmp_path):
    calls = []
    dag = make_dag(tmp_path, CallableVerifier("verify", lambda request: True))
    dag.register_worker("worker", lambda context: TaskOutcome.blocked("approval required"))
    dag.create_run([spec()], run_id="blocked", context=security())

    first = dag.run("blocked")
    dag.register_worker("worker", lambda context: calls.append(context.attempt.attempt_no) or TaskOutcome.candidate("root"))
    unchanged = dag.run("blocked")

    assert first.status == DAGRunStatus.BLOCKED
    assert unchanged.status == DAGRunStatus.BLOCKED
    assert calls == []

    dag.resolve_blocker("blocked", "root", "approved")
    resumed = dag.run("blocked")
    assert resumed.status == DAGRunStatus.SUCCEEDED
    assert calls == [2]


def test_artifact_tampering_is_detected_after_publication(tmp_path):
    dag = make_dag(tmp_path, CallableVerifier("verify", lambda request: True))
    dag.register_worker("worker", lambda context: TaskOutcome.candidate("root"))
    dag.create_run([spec()], run_id="tamper", context=security())
    manifest = dag.run("tamper").root_artifacts["root"][0]
    blob = dag.artifact_store.root / manifest.relative_blob_path
    blob.write_bytes(b"tampered")

    assert dag.artifact_store.check_integrity(manifest) is False
    with pytest.raises(DAGError, match="ARTIFACT-INTEGRITY"):
        dag.artifact_store.read(manifest, security("tamper"))
    with pytest.raises(DAGError, match="ARTIFACT-INTEGRITY"):
        dag.run("tamper")


def test_task_execution_is_denied_without_required_capability(tmp_path):
    denied = SecurityContext(
        user_id="alice",
        tenant_id="tenant-a",
        project_id="project-a",
        permissions=PermissionSet(allowed=frozenset({"tool.read"})),
    )
    dag = make_dag(
        tmp_path,
        CallableVerifier("verify", lambda request: True),
        config=DAGConfig(max_attempts_per_task=1),
    )
    dag.register_worker("worker", lambda context: TaskOutcome.candidate("root"))
    dag.create_run([spec()], run_id="denied", context=denied)

    result = dag.run("denied")

    assert result.status == DAGRunStatus.FAILED
    assert dag.store.list_artifacts("denied", state=None) == []


def test_context_builder_never_truncates_mandatory_contract():
    task = spec()
    dag_task = DAGTask(task, TaskState(task_id="root"))
    attempt = TaskAttempt(
        run_id="run",
        task_id="root",
        attempt_no=1,
        worker_id="worker",
        input_snapshot_hash="snapshot",
    )
    builder = ContextBuilder(
        budget=DAGContextBudget(max_chars=32, max_dependency_artifacts=1, max_retrieval_results=1)
    )

    with pytest.raises(DAGError, match="CONTEXT-OVERFLOW"):
        builder.build(dag_task, attempt, {})


def test_lightdag_provider_exposes_read_only_inspection(tmp_path):
    dag = make_dag(tmp_path, CallableVerifier("verify", lambda request: True))
    dag.register_worker("worker", lambda context: TaskOutcome.candidate("root"))
    dag.create_run([spec()], run_id="provider", context=security())
    registry = CapabilityRegistry()
    registry.register(LightDAGProvider(dag))
    read_context = SecurityContext(
        user_id="alice",
        tenant_id="tenant-a",
        project_id="project-a",
        run_id="provider",
        permissions=PermissionSet(allowed=frozenset({"workflow.dag.get_run"})),
    )

    result = asyncio.run(registry.invoke(
        "workflow.dag.get_run",
        {"run_id": "provider"},
        context=read_context,
    ))

    assert result["run_id"] == "provider"


def test_continue_independent_finishes_other_root_after_failure(tmp_path):
    calls = []

    def verify(request):
        return request.task.spec.task_id != "a-fail"

    dag = make_dag(
        tmp_path,
        CallableVerifier("verify", verify),
        config=DAGConfig(max_concurrency=1, max_attempts_per_task=1),
    )
    dag.register_worker(
        "worker",
        lambda context: calls.append(context.task.spec.task_id) or TaskOutcome.candidate("value"),
    )
    dag.create_run(
        [spec("a-fail"), spec("b-pass")],
        run_id="continue",
        context=security(),
    )

    result = dag.run("continue")

    assert result.status == DAGRunStatus.FAILED
    assert calls == ["a-fail", "b-pass"]
    assert dag.get_task("continue", "b-pass").state.status == DAGTaskStatus.VERIFIED


def test_fail_fast_stops_before_claiming_another_root(tmp_path):
    calls = []

    def verify(request):
        return request.task.spec.task_id != "a-fail"

    dag = make_dag(
        tmp_path,
        CallableVerifier("verify", verify),
        config=DAGConfig(
            max_concurrency=1,
            max_attempts_per_task=1,
            failure_policy="fail_fast",
        ),
    )
    dag.register_worker(
        "worker",
        lambda context: calls.append(context.task.spec.task_id) or TaskOutcome.candidate("value"),
    )
    dag.create_run(
        [spec("a-fail"), spec("b-pass")],
        run_id="fail-fast",
        context=security(),
    )

    result = dag.run("fail-fast")

    assert result.status == DAGRunStatus.FAILED
    assert calls == ["a-fail"]
    assert dag.get_task("fail-fast", "b-pass").state.status == DAGTaskStatus.READY
