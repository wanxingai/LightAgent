"""Bounded, credential-free persistent-runtime soak with real process death."""
import argparse
import asyncio
from contextlib import closing
import gc
import json
import os
from pathlib import Path
import resource
import sqlite3
import statistics
import subprocess
import sys
import threading
import time

import LightAgent

from LightAgent import (AgentRuntime, ApprovalToken, BackendCapabilities, BackendProbe, BackendResult,
    ExecutionHandle, ExecutionLimits, ExecutionService, InteractionRequests, SecurityContext, SqliteSessionStore)
from LightAgent.persistent.store import StateConflict


def effect(workspace, task_id):
    with closing(sqlite3.connect(Path(workspace) / "effects.sqlite3", timeout=10)) as db, db:
        db.execute("CREATE TABLE IF NOT EXISTS effects (task_id TEXT PRIMARY KEY)")
        db.execute("INSERT INTO effects VALUES (?)", (task_id,))


class FixtureBackend:
    def probe(self):
        return BackendProbe("soak-fixture", "1", BackendCapabilities(network_control=True))

    async def execute(self, request):
        effect(request.workspace, request.security_context.task_id)
        if request.prompt.startswith("cold-crash"):
            os._exit(23)  # A committed external effect with no result publication.
        request.emit("fixture.progress", safe_metadata=True)
        await asyncio.sleep(.005)
        return BackendResult("completed", usage={"model_calls": 0, "tool_calls": 0, "total_tokens": 0, "cost": 0})


def service(root):
    return ExecutionService(root, backend_factories={"fixture": FixtureBackend})


def count_effects(workspace):
    with closing(sqlite3.connect(Path(workspace) / "effects.sqlite3")) as db:
        return db.execute("SELECT count(*) FROM effects").fetchone()[0]


class Supervisor:
    def __init__(self, instance):
        self.instance, self.errors = instance, []
        self.thread = threading.Thread(target=self._run)

    def _run(self):
        try:
            self.instance.serve_forever(poll_interval=.02)
        except BaseException as error:
            self.errors.append(error)

    def start(self):
        self.thread.start()

    def close(self):
        self.instance.stop()
        self.thread.join(30)
        if self.thread.is_alive() or self.errors:
            raise RuntimeError("supervisor did not close cleanly: " + repr(self.errors))


def metrics():
    values = dict(threads=threading.active_count(), max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    if Path("/proc/self/status").exists():
        status = dict(line.split(":", 1) for line in Path("/proc/self/status").read_text().splitlines() if ":" in line)
        values["rss_kib"] = int(status["VmRSS"].split()[0])
        values["fds"] = len(list(Path("/proc/self/fd").iterdir()))
    else:
        values["rss_kib"] = values["max_rss_kib"] // (1024 if sys.platform == "darwin" else 1)
        values["fds"] = None
    for name in ("memory.current", "memory.peak", "memory.max", "memory.events", "pids.current"):
        path = Path("/sys/fs/cgroup") / name
        if path.exists():
            values["cgroup_" + name] = path.read_text().strip()
    return values


async def runtime_round(path, index):
    runtime = AgentRuntime(session_store=SqliteSessionStore(path))
    runtime.open_session("round-" + str(index))
    message = runtime.inbox.enqueue("context", "bounded message", message_id="once")
    runtime.inbox.claim_next(safe_boundary=True)
    runtime.inbox.complete(message.message_id)
    class Child:
        async def arun(self, query):
            await asyncio.sleep(.001)
            return query.upper()
    child = runtime.subagents.register(Child(), persistent=True)
    assert await runtime.subagents.run(child.agent_id, "bounded", idempotency_key="once", lease_seconds=10) == "BOUNDED"
    assert await runtime.subagents.run(child.agent_id, "bounded", idempotency_key="once", lease_seconds=10) == "BOUNDED"
    assert len(runtime.jobs.list()) == 1
    restored = AgentRuntime(session_store=SqliteSessionStore(path))
    restored.open_session("round-" + str(index))
    assert restored.subagents.tree()[0]["status"] == "success"
    assert not restored.subagents.tree()[0]["bound"]
    assert restored.inbox.get("once").status.value == "completed"
    assert restored.session_store.integrity(restored.session.session_id)["status"] == "verified"


def interaction_round(root, workspace):
    instance = service(root)
    context = SecurityContext(user_id="soak", tenant_id="test", project_id="offline")
    task = instance.submit("approval-boundary", workspace, backend="fixture", security_context=context)
    attempt = instance.claim(task.id)
    protocol = InteractionRequests(instance.store)
    payload = dict(operation="fixture.write", arguments={"value": 1}, resource="fixture")
    request = protocol.request(task.id, attempt_id=attempt["id"], epoch=attempt["epoch"], kind="approval",
                               payload=payload, idempotency_key="approval")
    identity = context.narrow(task_id=task.id, attempt_id=attempt["id"])
    wrong = ApprovalToken.issue(payload["operation"], {"value": 2}, identity, resource="fixture")
    try:
        protocol.respond(request["id"], True, context=identity, approval_token=wrong)
    except PermissionError:
        pass
    else:
        raise AssertionError("approval accepted different parameters")
    token = ApprovalToken.issue(payload["operation"], payload["arguments"], identity, resource="fixture")
    protocol.respond(request["id"], True, context=identity, approval_token=token)
    other = protocol.request(task.id, attempt_id=attempt["id"], epoch=attempt["epoch"], kind="approval",
                             payload=payload, idempotency_key="other")
    try:
        protocol.respond(other["id"], True, context=identity, approval_token=ApprovalToken.from_dict(token.to_dict()))
    except StateConflict:
        pass
    else:
        raise AssertionError("approval was replayed")
    task.cancel()
    instance.recover()
    task.reconcile(action="discard", note="Host confirmed the approval fixture was never dispatched")
    assert task.budget()["used"]["backend_calls"] == 0


def crash_child(root, workspace):
    instance = service(root)
    task = instance.submit("cold-crash", workspace, backend="fixture",
                           security_context=SecurityContext(user_id="soak"))
    (root.parent / "task.json").write_text(json.dumps({"id": task.id}))
    instance.serve_forever(max_ticks=1)
    raise AssertionError("crash fixture unexpectedly returned")


def crash_round(root, workspace):
    root.parent.mkdir(parents=True, exist_ok=True)
    environment = {key: value for key, value in os.environ.items() if key in
                   {"PATH", "PYTHONPATH", "VIRTUAL_ENV", "HOME", "TMPDIR", "PYTHONNOUSERSITE"}}
    environment["LANGFUSE_TRACING_ENABLED"] = "false"
    environment["PYTHONPATH"] = str(Path(LightAgent.__file__).resolve().parent.parent)
    process = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--crash-child", str(root),
                              "--workspace", str(workspace)], env=environment,
                              capture_output=True, text=True, timeout=30)
    if process.returncode != 23:
        raise RuntimeError("crash fixture failed: " + process.stderr[-2000:])
    task_id = json.loads((root.parent / "task.json").read_text())["id"]
    before = count_effects(workspace)
    restarted = service(root)
    restarted.recover()
    task = ExecutionHandle.connect(task_id, root=root)
    assert task.status()["status"] == "reconciling"
    restarted.serve_forever(max_ticks=1)
    assert count_effects(workspace) == before
    assert task.budget()["used"]["backend_calls"] == 1
    task.reconcile(action="discard", note="Host verified committed fixture effect; do not replay")
    assert task.status()["status"] == "cancelled" and task.status()["result"] is None


def run_soak(output, *, seconds=900, concurrency=4, interval=2, fault_interval=60, min_rounds=100):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    workspace = output / "workspace"
    workspace.mkdir()
    effect(workspace, "initial-sentinel")
    instance = service(output / "control")
    context = SecurityContext(user_id="soak", tenant_id="test", project_id="offline")
    parent = instance.submit("budget-parent", workspace, backend="fixture", security_context=context,
                             budget={"backend_calls": 100000})
    parent.pause()
    supervisor = Supervisor(instance)
    supervisor.start()
    started, rounds, completed, crashes, restarts = time.monotonic(), 0, 0, 0, 0
    next_fault, next_sample = 0, 0
    latencies, samples = [], []
    report = dict(schema_version=1, status="running", duration_requested=seconds, concurrency=concurrency,
                  interval_seconds=interval, python=sys.version, model="deterministic local fixture; no API calls",
                  rss_growth_ceiling_mib=128, min_rounds=min_rounds, fault_interval_seconds=fault_interval)
    try:
        while time.monotonic() - started < seconds:
            cycle = time.monotonic()
            handles = []
            for index in range(concurrency):
                key = f"round-{rounds}-task-{index}"
                kwargs = dict(backend="fixture", security_context=context, parent_id=parent.id,
                              idempotency_key=key, limits=ExecutionLimits(timeout=20, lease_seconds=10))
                handle = instance.submit("bounded-task", workspace, **kwargs)
                assert instance.submit("bounded-task", workspace, **kwargs).id == handle.id
                handles.append(handle)
            deadline = time.monotonic() + 30
            while any(h.status()["status"] != "completed" for h in handles):
                if time.monotonic() >= deadline or supervisor.errors:
                    raise RuntimeError("batch failed to settle: " + repr([h.status()["status"] for h in handles]))
                time.sleep(.01)
            completed += len(handles)
            latencies.append(time.monotonic() - cycle)
            assert parent.budget()["used"]["backend_calls"] == completed
            assert count_effects(workspace) == completed + crashes + 1
            asyncio.run(runtime_round(output / "sessions.sqlite3", rounds))
            rounds += 1
            now = time.monotonic() - started
            if now >= next_fault:
                crash_round(output / "faults" / str(crashes) / "control", workspace)
                interaction_round(output / "approvals" / str(crashes), workspace)
                crashes += 1
                supervisor.close()
                instance = service(output / "control")
                parent = ExecutionHandle.connect(parent.id, root=instance.root)
                supervisor = Supervisor(instance)
                supervisor.start()
                restarts += 1
                next_fault = now + fault_interval
            if now >= next_sample:
                sample = dict(elapsed_seconds=round(now, 3), completed=completed, rounds=rounds, **metrics())
                samples.append(sample)
                with (output / "samples.jsonl").open("a") as stream:
                    stream.write(json.dumps(sample, sort_keys=True) + "\n")
                print(json.dumps(sample, sort_keys=True), flush=True)
                next_sample = now + min(30, max(1, seconds / 3))
            time.sleep(max(0, interval - (time.monotonic() - cycle)))
        supervisor.close()
        gc.collect()
        final = metrics()
        report.update(rounds=rounds, completed=completed, crashes_reconciled=crashes, supervisor_restarts=restarts,
            duration_seconds=round(time.monotonic() - started, 3), final_metrics=final,
            batch_latency_seconds=dict(p50=statistics.median(latencies), p95=sorted(latencies)[int((len(latencies)-1)*.95)], max=max(latencies)),
            samples=samples)
        assert rounds >= min_rounds, "insufficient sustained work"
        assert count_effects(workspace) == completed + crashes + 1
        assert parent.budget()["used"]["backend_calls"] == completed
        warm = [s for s in samples if s["elapsed_seconds"] >= min(60, seconds / 3)]
        if warm:
            report["rss_growth_mib"] = round((max(s["rss_kib"] for s in warm) - warm[0]["rss_kib"]) / 1024, 3)
            assert report["rss_growth_mib"] <= 128, "RSS growth exceeded the 128 MiB acceptance ceiling"
            if warm[0]["fds"] is not None:
                assert final["fds"] <= warm[0]["fds"] + 8, "file descriptors did not settle"
            assert final["threads"] <= warm[0]["threads"] + 2, "threads did not settle"
        assert "oom_kill 0" in final.get("cgroup_memory.events", "oom_kill 0"), "container OOM occurred"
        report["release_gate"] = seconds >= 900 and rounds >= 100 and len(warm) >= 3
        report["status"] = "passed"
    except BaseException as error:
        report.update(status="failed", error=repr(error), rounds=rounds, completed=completed,
                      crashes_reconciled=crashes, supervisor_restarts=restarts,
                      duration_seconds=round(time.monotonic() - started, 3), samples=samples)
        raise
    finally:
        cleanup_error = None
        try:
            supervisor.close()
        except Exception as error:
            cleanup_error = error
            report.update(status="failed", cleanup_error=repr(error))
        (output / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(json.dumps({k: v for k, v in report.items() if k != "samples"}, sort_keys=True), flush=True)
        if cleanup_error and sys.exc_info()[0] is None:
            raise RuntimeError("soak cleanup failed") from cleanup_error
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--seconds", type=float, default=900)
    parser.add_argument("--concurrency", type=int, choices=range(1, 9), default=4)
    parser.add_argument("--interval", type=float, default=2)
    parser.add_argument("--fault-interval", type=float, default=60)
    parser.add_argument("--min-rounds", type=int, default=100)
    parser.add_argument("--crash-child", type=Path)
    parser.add_argument("--workspace", type=Path)
    args = parser.parse_args()
    if args.crash_child:
        crash_child(args.crash_child, args.workspace)
    else:
        if not args.output or args.seconds <= 0 or args.interval < 0 or args.fault_interval <= 0 or args.min_rounds < 1:
            parser.error("positive bounded duration, output and round count are required")
        run_soak(args.output, seconds=args.seconds, concurrency=args.concurrency, interval=args.interval,
                 fault_interval=args.fault_interval, min_rounds=args.min_rounds)
