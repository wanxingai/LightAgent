#!/usr/bin/env python
"""Credential-free LightDAG decomposition, repair, and integration demo."""

import tempfile
from pathlib import Path

from LightAgent import (
    CallableVerifier,
    CapabilityRisk,
    DAGConfig,
    DecompositionProposal,
    LightDAG,
    LocalArtifactStore,
    PermissionSet,
    SecurityContext,
    SqliteTaskGraphStore,
    TaskOutcome,
    TaskSpec,
)


def task(task_id: str, *, decomposer: str | None = None) -> TaskSpec:
    return TaskSpec(
        task_id=task_id,
        goal=f"Produce the exact text: {task_id}",
        acceptance_contract={"equals": task_id},
        worker_key="local-worker",
        verifier_key="exact",
        decomposer_key=decomposer,
    )


def worker(context):
    task_id = context.task.spec.task_id
    if task_id == "root" and context.attempt.phase == "solve":
        return TaskOutcome.decompose(DecompositionProposal(
            parent_task_id="root",
            new_tasks=(task("analysis"), task("summary")),
            rationale="The two inputs can be prepared independently.",
            composition_contract={"requires": ["analysis", "summary"]},
            expected_graph_revision=context.run.graph_revision,
        ))
    if task_id == "summary" and context.attempt.attempt_no == 1:
        return TaskOutcome.candidate("needs repair")
    return TaskOutcome.candidate(task_id)


def verify(request):
    if request.kind == "decomposition":
        return True
    expected = request.task.spec.task_id.encode("utf-8")
    if request.candidate_content == expected:
        return True
    return {"verdict": "fail", "diagnostics": ["candidate did not match the contract"]}


with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    dag = LightDAG(
        store=SqliteTaskGraphStore(root / "dag.sqlite3"),
        artifact_store=LocalArtifactStore(root / "artifacts"),
        verifiers={"exact": CallableVerifier("exact", verify)},
        config=DAGConfig(max_concurrency=2),
    )
    dag.register_worker("local-worker", worker)
    dag.create_run(
        [task("root", decomposer="exact")],
        run_id="offline-demo",
        context=SecurityContext(
            user_id="demo",
            tenant_id="local",
            project_id="lightdag-demo",
            permissions=PermissionSet(
                allowed=frozenset({"dag.task.execute"}),
                max_risk=CapabilityRisk.SENSITIVE,
            ),
        ),
    )

    result = dag.run("offline-demo")
    states = {item.spec.task_id: item.state.status.value for item in dag.list_tasks(result.run_id)}
    print(result.status.value, states)
    assert result.success
    assert states == {"root": "verified", "analysis": "verified", "summary": "verified"}
