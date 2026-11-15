"""Cross-version migration/rollback release gate; no model or network required."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from unittest.mock import patch
import zipfile

from LightAgent import AgentRuntime, HistoryBundle, JobStatus, SqliteSessionStore, __version__
from LightAgent.persistent import StateConflict
from LightAgent.persistent.jobs import poll_jobs
from LightResearch import ResearchHandle, ResearchService, enable_legacy_api


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-wheel", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    wheel = args.baseline_wheel.resolve(strict=True)
    old_code = args.output / "old-code"
    with zipfile.ZipFile(wheel) as archive:
        archive.extractall(old_code)
    producer = Path(__file__).with_name("fixtures") / "v012_history_producer.py"
    env = {**os.environ, "PYTHONPATH": str(old_code.resolve())}
    original = args.output / "original"
    def old(operation, root):
        result = subprocess.run([sys.executable, str(producer), operation, str(root.resolve())],
            cwd=args.output, env=env, capture_output=True, text=True, timeout=60, check=True)
        return json.loads(result.stdout.strip().splitlines()[-1]) if operation == "inspect" else None
    old("create", original)
    before = old("inspect", original)
    bundle = args.output / "backup"
    HistoryBundle.capture(original, bundle, quiescent=True)
    candidate = HistoryBundle.restore(bundle, args.output / "candidate")
    # Inspect once with the *old* reader before applying any v0.13 changes.
    assert old("inspect", candidate) == before
    store = SqliteSessionStore(candidate / "sessions.sqlite3")
    original_session = store.get("historical").to_dict()
    assert store.integrity("historical")["status"] == "legacy_unanchored"
    store.anchor_legacy("historical", expected_digest=store.history_digest("historical"),
                        note="Host-reviewed frozen v0.12 migration rehearsal")
    assert store.get("historical").to_dict() == original_session
    runtime = AgentRuntime(session_store=store)
    runtime.open_session("historical")
    index = json.loads((candidate / "fixture.json").read_text())
    assert runtime.jobs.get(index["completed_runtime_job"]).result == "historical result"
    assert runtime.jobs.get(index["completed_runtime_job"]).output_cursor == 1
    assert runtime.jobs.get(index["failed_runtime_job"]).status == JobStatus.FAILED
    assert runtime.jobs.get(index["running_runtime_job"]).status == JobStatus.INTERRUPTED
    assert runtime.subagents.tree()[0]["bound"] is False
    assert runtime.subagents.tree()[0]["status"] == "success"
    assert runtime.budget.usage.model_calls == 1
    assert runtime.budget.usage.tool_calls == 1
    assert len(runtime.goals.list()) == 1
    assert any(message.content == "pending steering" for message in runtime.inbox.pending())
    enable_legacy_api()
    # No backend factory: migration must not dispatch or silently bless old profiles.
    service = ResearchService(candidate / "research")
    handle = ResearchHandle.connect(index["research_id"], root=service.root)
    versions = handle.versions()
    experiments = handle.experiments()
    assert handle.records_page("experiment", query="FROZEN BASELINE")["items"] == experiments
    artifacts = {a["blob"]: hashlib.sha256(handle.read_artifact(a["blob"])).hexdigest() for a in handle.artifacts()}
    assert artifacts == before["artifacts"]
    assert hashlib.sha256((candidate / "research" / "job-output" / index["external_job_id"]).read_bytes()).hexdigest() == before["job_output"]
    assert handle.receipt(index["applied_message_id"])["status"] == "applied"
    assert handle.receipt(index["pending_message_id"])["status"] == "persisted"
    chat = handle.chat(index["chat_id"])
    chat_receipt = handle.receipt(index["chat_applied_id"])
    assert chat_receipt["status"] == "applied" and chat_receipt["response"] == "historical chat reply"
    assert chat.send("historical question", idempotency_key="historical-chat-applied") == chat_receipt
    assert handle.receipt(index["chat_delivered_id"])["status"] == "delivered"
    counts = {a["id"]: a["backend_calls"] for a in service.store.scan("agent")}
    # Old authority/profile identities remain pinned, not rewritten to new modules.
    from LightAgent.persistent.store import dumps
    pinned = dumps(versions)
    try:
        service._check_execution(handle.status(), versions[0])
    except (StateConflict, ValueError):
        pass
    else:
        raise AssertionError("old execution profile must not silently accept the new host")
    with service.bindings.lock("supervisor", "main"):
        service.recover()
    with patch("LightAgent.persistent.jobs.time.time", return_value=time.time() + 11):
        poll_jobs(service)
    assert service.store.get("agent", index["interrupted_research_id"])["status"] == "reconciling"
    assert service.store.get("job", index["external_job_id"])["status"] == "completed"
    assert service.store.get("job", index["uncertain_job_id"])["status"] == "uncertain"
    assert handle.experiments() == experiments
    assert handle.receipt(index["chat_applied_id"]) == chat_receipt
    assert handle.receipt(index["chat_delivered_id"])["status"] == "uncertain"
    assert dumps(handle.versions()) == pinned
    assert {a["id"]: a["backend_calls"] for a in service.store.scan("agent")} == counts
    rollback = HistoryBundle.restore(bundle, args.output / "rollback")
    assert old("inspect", rollback) == before
    assert old("inspect", original) == before
    report = dict(baseline="0.12.0", target=__version__,
        baseline_wheel_sha256=hashlib.sha256(wheel.read_bytes()).hexdigest(), baseline_history=before,
        result="passed", checks=["old-wheel history production and cold process exit", "SQLite-consistent offline backup",
        "legacy Session read and explicit anchoring without event rewrites", "Runtime Job/Subagent/message/budget restoration",
        "research experiment/artifact/receipt/version preservation", "unknown Job/cycle effects require reconciliation",
        "pinned execution profile fails closed", "historical chat receipt and idempotency preserved",
        "interrupted chat remains uncertain", "zero backend replay", "old-wheel rollback read equals original"])
    (args.output / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
