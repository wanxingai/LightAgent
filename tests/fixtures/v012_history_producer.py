"""Run ONLY against a frozen 0.12.0 wheel, outside the current checkout."""
import asyncio
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import threading
import time


class HistoricalBackend:
    async def execute(self, request):
        from LightAgent import BackendResult
        if request.prompt.startswith("Independent research chat"):
            return BackendResult("historical chat reply")
        (Path(request.workspace) / "evidence.txt").write_text("historical verified evidence", encoding="utf-8")
        return BackendResult(json.dumps(dict(summary="frozen baseline experiment", hypothesis="local fixture",
            evidence=["evidence.txt"], next_action="wait")))


def inspect_history(root):
    from LightAgent import AgentHandle, SqliteSessionStore
    session = SqliteSessionStore(root / "sessions.sqlite3").get("historical")
    index = json.loads((root / "fixture.json").read_text())
    handle = AgentHandle.connect(index["research_id"], root=root / "research")
    artifacts = {a["blob"]: hashlib.sha256(handle.read_artifact(a["blob"])).hexdigest() for a in handle.artifacts()}
    job_output = hashlib.sha256((root / "research" / "job-output" / index["external_job_id"]).read_bytes()).hexdigest()
    with sqlite3.connect(root / "research" / "control.sqlite3") as connection:
        records = [list(row) for row in connection.execute("SELECT kind,id,agent,revision,body FROM records ORDER BY kind,id")]
        events = [list(row) for row in connection.execute("SELECT * FROM events ORDER BY sequence")]
    value = dict(session=session.to_dict(), records=records, events=events, artifacts=artifacts, job_output=job_output)
    digest = hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return dict(digest=digest, session_events=len(session.events), records=len(records),
                control_events=len(events), artifacts=artifacts, job_output=job_output, experiments=len(handle.experiments()))


def produce(root):
    from LightAgent import AgentRuntime, AgentService, ResearchContract, SecurityContext, SqliteSessionStore, __version__
    from LightAgent.persistent.jobs import _claim_queued_job, run_job, poll_jobs
    assert __version__ == "0.12.0", "fixture must be produced by the frozen v0.12.0 wheel"
    root.mkdir()
    project = root / "project"
    project.mkdir()
    (project / "data.txt").write_text("frozen local input", encoding="utf-8")
    service = AgentService(root / "research", backend_factories={"fixture": HistoricalBackend})
    contract = ResearchContract(max_cycles_per_day=1, interval_seconds=1)
    handle = service.submit("baseline research", project, backend="fixture", contract=contract,
                            security_context=SecurityContext(network_allowed=True))
    applied = handle.send("Keep the evidence local", idempotency_key="applied")
    errors = []
    def serve():
        try:
            service.serve_forever(poll_interval=.01)
        except BaseException as error:
            errors.append(str(error))
    thread = threading.Thread(target=serve)
    thread.start()
    deadline = time.monotonic() + 15
    try:
        while not handle.experiments():
            assert time.monotonic() < deadline, errors
            time.sleep(.01)
        handle.pause()
    finally:
        service.stop()
        thread.join(10)
    assert not thread.is_alive() and not errors, errors
    pending = handle.send("Unconsumed historical message", idempotency_key="pending")
    from LightAgent.cancellation import CancellationToken
    chat = handle.open_chat()
    chat_applied = chat.send("historical question", idempotency_key="historical-chat-applied")
    service._chat(chat_applied, CancellationToken())
    assert handle.receipt(chat_applied["id"])["status"] == "applied"
    chat_delivered = chat.send("interrupted question", idempotency_key="historical-chat-delivered")
    with service.store.transaction() as db:
        chat_delivered["status"] = "delivered"
        service.store.put("message", chat_delivered, db)
    external = handle.submit_job([sys.executable, "-c", "print('historical job output')"], allow_host_execution=True)
    _claim_queued_job(service, external["id"])
    run_job(service.root, external["id"])
    poll_jobs(service)
    assert service.store.get("job", external["id"])["status"] == "completed"
    uncertain = handle.submit_job([sys.executable, "-c", "pass"], allow_host_execution=True)
    _claim_queued_job(service, uncertain["id"])
    interrupted = service.submit("interrupted research", project, backend="fixture", contract=contract)
    interrupted.send("preserve claimed input", idempotency_key="claimed")
    cycle = service._claim(interrupted.id, "historical-watch")
    index = dict(research_id=handle.id, interrupted_research_id=interrupted.id, cycle_id=cycle["id"],
                 applied_message_id=applied["id"], pending_message_id=pending["id"],
                 external_job_id=external["id"], uncertain_job_id=uncertain["id"],
                 chat_id=chat.id, chat_applied_id=chat_applied["id"], chat_delivered_id=chat_delivered["id"])

    async def runtime_history():
        runtime = AgentRuntime(session_store=SqliteSessionStore(root / "sessions.sqlite3"))
        runtime.open_session("historical", metadata={"baseline": "0.12.0"})
        message = runtime.inbox.enqueue("context", "completed inbox message")
        runtime.inbox.claim_next(safe_boundary=True)
        runtime.inbox.complete(message.message_id)
        runtime.inbox.enqueue("steering", "pending steering")
        runtime.goals.create("retain historical goal")
        runtime.budget.consume(model_calls=1, tool_calls=1)
        completed = runtime.jobs.start("success", lambda: "historical result", idempotency_key="once")
        runtime.jobs.emit_output(completed.job_id, "historical output chunk")
        await runtime.jobs.wait(completed.job_id)
        async def fail():
            raise ValueError("historical failure")
        failed = runtime.jobs.start("failure", fail)
        await runtime.jobs.wait(failed.job_id)
        class Child:
            name = "historical child"
            async def arun(self, query):
                return "historical child result"
        child = runtime.subagents.register(Child(), persistent=True)
        await runtime.subagents.run(child.agent_id, "hello")
        entered = asyncio.Event()
        async def crash_boundary():
            entered.set()
            await asyncio.sleep(3600)
        running = runtime.jobs.start("crashed owner", crash_boundary)
        await entered.wait()
        index.update(completed_runtime_job=completed.job_id, failed_runtime_job=failed.job_id,
                     running_runtime_job=running.job_id, subagent_id=child.agent_id)
        (root / "fixture.json").write_text(json.dumps(index, sort_keys=True), encoding="utf-8")
        # Real cold-exit boundary: do not let asyncio cancel/finalize the Job.
        os._exit(0)
    asyncio.run(runtime_history())


if __name__ == "__main__":
    operation, location = sys.argv[1:]
    root = Path(location).resolve()
    if operation == "create":
        produce(root)
    elif operation == "inspect":
        print(json.dumps(inspect_history(root), sort_keys=True))
    else:
        raise ValueError("unknown operation")
