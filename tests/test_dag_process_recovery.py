import os
import subprocess
import sys
import time
from pathlib import Path

from LightAgent.dag import DAGAttemptStatus, DAGConfig, DAGRun, SqliteTaskGraphStore, TaskSpec


def test_attempt_claimed_by_terminated_process_is_recovered(tmp_path):
    database = tmp_path / "dag.sqlite3"
    script = f"""
from LightAgent.dag import DAGConfig, DAGRun, SqliteTaskGraphStore, TaskSpec
store = SqliteTaskGraphStore({str(database)!r})
task = TaskSpec(task_id='root', goal='root', acceptance_contract={{'equals': 'root'}}, worker_key='worker', verifier_key='verify')
run = DAGRun(run_id='process-recovery', tenant_id='tenant-a', project_id='project-a', root_task_ids=['root'])
store.create_run(run, [task], DAGConfig())
store.claim_ready_task('process-recovery', 'terminated-worker', 0.02)
"""
    environment = dict(os.environ)
    project_root = str(Path(__file__).resolve().parents[1])
    environment["PYTHONPATH"] = os.pathsep.join(filter(None, [project_root, environment.get("PYTHONPATH")]))

    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=project_root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert completed.returncode == 0, completed.stderr

    time.sleep(0.03)
    recovered = SqliteTaskGraphStore(database)
    assert recovered.expire_attempts("process-recovery") == 1
    next_claim = recovered.claim_ready_task("process-recovery", "replacement-worker", 1)

    assert next_claim is not None
    assert next_claim[1].attempt_no == 2
    attempts = [
        event for event in recovered.events("process-recovery")
        if event.type == "dag.attempt.expired"
    ]
    assert len(attempts) == 1
    expired_id = attempts[0].attempt_id
    assert recovered.get_attempt(expired_id).status == DAGAttemptStatus.EXPIRED
