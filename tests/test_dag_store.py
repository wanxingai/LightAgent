import time

import pytest

from LightAgent.dag import (
    DAGConfig,
    DAGError,
    DAGRun,
    DAGTaskStatus,
    SqliteTaskGraphStore,
    TaskSpec,
    topological_order,
)


def task(name, *, depends_on=()):
    return TaskSpec(
        task_id=name,
        goal=name,
        acceptance_contract={"equals": name},
        worker_key="worker",
        verifier_key="verifier",
        depends_on=tuple(depends_on),
    )


def run_record(run_id="run-a"):
    return DAGRun(
        run_id=run_id,
        tenant_id="tenant-a",
        project_id="project-a",
        root_task_ids=["root"],
    )


def test_iterative_graph_validation_handles_deep_graph_and_cycles():
    nodes = {f"n-{index}" for index in range(10_000)}
    edges = {(f"n-{index}", f"n-{index - 1}") for index in range(1, 10_000)}

    ordered = topological_order(nodes, edges)

    assert ordered[0] == "n-0"
    assert ordered[-1] == "n-9999"
    with pytest.raises(DAGError, match="LA-DAG-CYCLE"):
        topological_order(nodes, {*edges, ("n-0", "n-9999")})


def test_store_creates_diamond_graph_and_claims_each_task_once(tmp_path):
    path = tmp_path / "dag.sqlite3"
    first = SqliteTaskGraphStore(path)
    second = SqliteTaskGraphStore(path)
    tasks = [task("shared"), task("left", depends_on=("shared",)), task("right", depends_on=("shared",)), task("root", depends_on=("left", "right"))]
    first.create_run(run_record(), tasks, DAGConfig())

    claim = first.claim_ready_task("run-a", "worker-a", 10)
    duplicate = second.claim_ready_task("run-a", "worker-b", 10)

    assert claim is not None
    assert claim[0].spec.task_id == "shared"
    assert duplicate is None
    assert first.dependencies("run-a", "root") == ["left", "right"]


def test_store_rejects_unknown_dependency_and_cycle(tmp_path):
    store = SqliteTaskGraphStore(tmp_path / "dag.sqlite3")
    with pytest.raises(DAGError, match="UNKNOWN-DEPENDENCY"):
        store.create_run(run_record(), [task("root", depends_on=("missing",))], DAGConfig())
    with pytest.raises(DAGError, match="CYCLE"):
        store.create_run(
            run_record("cycle"),
            [task("root", depends_on=("other",)), task("other", depends_on=("root",))],
            DAGConfig(),
        )

    with pytest.raises(ValueError, match="contract_hash"):
        TaskSpec.from_dict({**task("root").to_dict(), "contract_hash": "forged"})


def test_expired_attempt_is_requeued_and_old_epoch_is_rejected(tmp_path):
    store = SqliteTaskGraphStore(tmp_path / "dag.sqlite3")
    store.create_run(run_record(), [task("root")], DAGConfig())
    _, attempt = store.claim_ready_task("run-a", "worker-a", 0.01)
    time.sleep(0.02)

    assert store.expire_attempts("run-a") == 1
    assert store.get_task("run-a", "root").state.status == DAGTaskStatus.READY
    with pytest.raises(DAGError, match="STALE-ATTEMPT"):
        store.mark_attempt_running(attempt.attempt_id, attempt.lease_epoch)
    replacement = store.claim_ready_task("run-a", "worker-b", 1)
    assert replacement is not None
    assert replacement[1].attempt_no == 2


def test_active_scheduler_lease_cannot_be_stolen(tmp_path):
    store = SqliteTaskGraphStore(tmp_path / "dag.sqlite3")
    store.create_run(run_record(), [task("root")], DAGConfig())
    epoch = store.acquire_scheduler_lease("run-a", "scheduler-a", 10)

    assert epoch == 1
    with pytest.raises(DAGError, match="LEASE-REJECTED"):
        store.acquire_scheduler_lease("run-a", "scheduler-b", 10)


def test_create_run_is_idempotent_for_same_logical_request(tmp_path):
    store = SqliteTaskGraphStore(tmp_path / "dag.sqlite3")

    first = store.create_run(run_record(), [task("root")], DAGConfig())
    replay = store.create_run(run_record(), [task("root")], DAGConfig())

    assert replay.run_id == first.run_id
    assert replay.graph_revision == first.graph_revision == 1
    assert len(store.events("run-a")) == 1

    changed = task("root")
    changed = TaskSpec.from_dict({**changed.to_dict(), "goal": "different goal"})
    with pytest.raises(DAGError, match="IDEMPOTENCY-CONFLICT"):
        store.create_run(run_record(), [changed], DAGConfig())


def test_supersede_rewires_unverified_dependents_and_fences_old_attempt(tmp_path):
    store = SqliteTaskGraphStore(tmp_path / "dag.sqlite3")
    store.create_run(
        DAGRun(
            run_id="replace",
            tenant_id="tenant-a",
            project_id="project-a",
            root_task_ids=["root"],
        ),
        [task("source"), task("root", depends_on=("source",))],
        DAGConfig(),
    )
    _, attempt = store.claim_ready_task("replace", "worker-a", 10)

    replacement = TaskSpec.from_dict({
        **task("source-v2").to_dict(),
        "supersedes_task_id": "source",
    })
    created = store.supersede_task(
        "replace",
        "source",
        replacement,
        expected_graph_revision=1,
        config=DAGConfig(),
    )

    assert created.spec.task_id == "source-v2"
    assert store.get_task("replace", "source").state.status == DAGTaskStatus.SUPERSEDED
    assert store.dependencies("replace", "root") == ["source-v2"]
    assert store.get_task("replace", "root").state.dependency_revision == 1
    assert store.get_attempt(attempt.attempt_id).status.value == "cancelled"
    with pytest.raises(DAGError, match="STALE-ATTEMPT"):
        store.mark_attempt_running(attempt.attempt_id, attempt.lease_epoch)
