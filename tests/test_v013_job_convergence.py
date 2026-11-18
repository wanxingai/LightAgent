import asyncio
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import threading

import pytest

from LightAgent import AgentRuntime, JobStatus, PermissionSet, SqliteSessionStore
from LightAgent.job_lifecycle import JobConflict, transition, view
from LightAgent.persistent import jobs
from LightAgent.persistent.store import ControlStore, StateConflict


def test_subagent_runs_are_jobs_and_restore_requires_explicit_binding(tmp_path):
    class Child:
        name = "child"
        async def arun(self, query):
            return query.upper()

    store = SqliteSessionStore(tmp_path / "sessions.db")
    runtime = AgentRuntime(session_store=store)
    runtime.open_session("shared")
    child = runtime.subagents.register(Child(), persistent=True)
    assert asyncio.run(runtime.subagents.run(child.agent_id, "hello", idempotency_key="one")) == "HELLO"
    assert len(runtime.jobs.list()) == 1
    record = runtime.jobs.list()[0]
    assert record.owner_agent_id == child.agent_id
    assert runtime.subagents.tree()[0]["job_id"] == record.job_id
    restored = AgentRuntime(session_store=SqliteSessionStore(store.path))
    restored.open_session("shared")
    assert restored.subagents.tree()[0]["status"] == "success"
    assert restored.subagents.tree()[0]["bound"] is False
    with pytest.raises(RuntimeError, match="bind"):
        asyncio.run(restored.subagents.run(child.agent_id, "hello"))
    restored.subagents.bind(child.agent_id, Child())
    assert asyncio.run(restored.subagents.run(child.agent_id, "hello", idempotency_key="one")) == "HELLO"
    assert len(restored.jobs.list()) == 1
    with pytest.raises(JobConflict, match="idempotency"):
        asyncio.run(restored.subagents.run(child.agent_id, "different", idempotency_key="one"))


@pytest.mark.parametrize("separate_runtime", [False, True])
def test_cancelling_reused_subagent_wait_keeps_job_running(tmp_path, separate_runtime):
    async def scenario():
        path = tmp_path / "sessions.db"
        runtime = AgentRuntime(session_store=SqliteSessionStore(path))
        runtime.open_session("shared")
        started, release, joined = asyncio.Event(), asyncio.Event(), asyncio.Event()
        calls = []

        class Child:
            async def arun(self, query: str) -> str:
                calls.append(query)
                started.set()
                await release.wait()
                return query.upper()

        agent = Child()
        child = runtime.subagents.register(agent, persistent=True)
        waiter_runtime = runtime
        if separate_runtime:
            waiter_runtime = AgentRuntime(session_store=SqliteSessionStore(path))
            waiter_runtime.open_session("shared")
            waiter_runtime.subagents.bind(child.agent_id, agent)

        async def join_job() -> str:
            joined.set()
            return await waiter_runtime.subagents.run(child.agent_id, "hello", idempotency_key="one")

        original = asyncio.create_task(runtime.subagents.run(
            child.agent_id, "hello", idempotency_key="one", lease_seconds=10,
        ))
        duplicate = None
        try:
            await asyncio.wait_for(started.wait(), 5)
            duplicate = asyncio.create_task(join_job())
            await asyncio.wait_for(joined.wait(), 5)

            duplicate.cancel()
            with pytest.raises(asyncio.CancelledError):
                await duplicate

            assert [job.status for job in runtime.jobs.list()] == [JobStatus.RUNNING]
            release.set()
            assert await asyncio.wait_for(original, 5) == "HELLO"
        finally:
            release.set()
            if duplicate is not None:
                duplicate.cancel()
                await asyncio.gather(duplicate, return_exceptions=True)
            await asyncio.gather(original, return_exceptions=True)

        assert calls == ["hello"]
        assert [job.status for job in runtime.jobs.list()] == [JobStatus.SUCCESS]

    asyncio.run(scenario())


def test_cancelling_subagent_job_creator_cancels_job():
    async def scenario():
        runtime = AgentRuntime()
        runtime.open_session()
        started = asyncio.Event()
        release = asyncio.Event()

        class Child:
            async def arun(self, query: str) -> str:
                started.set()
                await release.wait()
                return query.upper()

        child = runtime.subagents.register(Child())
        original = asyncio.create_task(runtime.subagents.run(child.agent_id, "hello", idempotency_key="one"))
        try:
            await asyncio.wait_for(started.wait(), 5)
            original.cancel()
            with pytest.raises(asyncio.CancelledError):
                await original

            assert [job.status for job in runtime.jobs.list()] == [JobStatus.CANCELLED]
        finally:
            release.set()
            await asyncio.gather(original, return_exceptions=True)

    asyncio.run(scenario())


def test_live_lease_survives_second_runtime_open_and_remote_cancel(tmp_path):
    async def scenario():
        path = tmp_path / "sessions.db"
        first = AgentRuntime(session_store=SqliteSessionStore(path))
        first.open_session("s")
        started = asyncio.Event()
        cancelled = asyncio.Event()
        async def work(*, cancellation_token):
            started.set()
            try:
                await asyncio.sleep(20)
            finally:
                cancelled.set()
        job = first.jobs.start("work", work, lease_seconds=10)
        await started.wait()
        second = AgentRuntime(session_store=SqliteSessionStore(path))
        second.open_session("s")
        assert second.jobs.get(job.job_id).status == JobStatus.RUNNING
        with pytest.raises(PermissionError):
            second.jobs.renew_lease(job.job_id, 1)
        assert second.jobs.cancel(job.job_id)
        await asyncio.wait_for(cancelled.wait(), 2)
        result = await first.jobs.wait(job.job_id)
        assert result.status == JobStatus.CANCELLED
        assert result.result is None
        messages = [e for e in second.session_store.get("s").events if e.type == "inbox.enqueued"]
        assert len(messages) == 1
    asyncio.run(scenario())


def test_cancel_before_dispatch_never_executes_and_notifies_once():
    async def scenario():
        runtime = AgentRuntime()
        runtime.open_session()
        calls = []
        job = runtime.jobs.start("immediate", lambda: calls.append(1))
        assert runtime.jobs.cancel(job.job_id)
        result = await runtime.jobs.wait(job.job_id)
        assert result.status == JobStatus.CANCELLED
        assert calls == []
        assert len(runtime.inbox.pending()) == 1
    asyncio.run(scenario())


def test_late_attempt_cannot_publish_result_or_output_after_resume(tmp_path):
    async def scenario():
        path = tmp_path / "sessions.db"
        first = AgentRuntime(session_store=SqliteSessionStore(path))
        first.open_session("s")
        entered, release = asyncio.Event(), asyncio.Event()
        async def old():
            entered.set()
            try:
                await release.wait()
            except asyncio.CancelledError:
                await release.wait()
            with pytest.raises(JobConflict):
                first.jobs.emit_output(job.job_id, "stale")
            return "stale"
        job = first.jobs.start("old", old, lease_seconds=10)
        try:
            await asyncio.wait_for(entered.wait(), 5)
            # Expire only after dispatch; slow SQLite setup must not prevent entry.
            first.jobs.renew_lease(job.job_id, .001)
            await asyncio.sleep(.02)
            second = AgentRuntime(session_store=SqliteSessionStore(path))
            second.open_session("s")
            resumed = second.jobs.resume(job.job_id, lambda: "new", lease_seconds=5,
                                         note="Host approved a replacement and fenced the stale worker")
            assert resumed.attempt_id != job.attempt_id
            assert resumed.lease_epoch == 2
            release.set()
            assert (await asyncio.wait_for(second.jobs.wait(job.job_id), 5)).result == "new"
            await asyncio.wait_for(first.jobs.wait(job.job_id), 5)
            assert first.jobs.get(job.job_id).result == "new"
            assert first.jobs.get(job.job_id).output == []
        finally:
            release.set()
    asyncio.run(scenario())


def test_subagent_concurrency_and_descendant_cancel_use_jobs():
    async def scenario():
        runtime = AgentRuntime()
        runtime.open_session()
        runtime.subagents.max_concurrency = 2
        entered = asyncio.Event()
        class Child:
            async def arun(self, query):
                entered.set()
                await asyncio.sleep(30)
        parent = runtime.subagents.register(Child())
        child = runtime.subagents.register(Child(), parent_agent_id=parent.agent_id)
        tasks = [asyncio.create_task(runtime.subagents.run(r.agent_id, "go")) for r in (parent, child)]
        await entered.wait()
        with pytest.raises(RuntimeError, match="concurrency"):
            await runtime.subagents.run(child.agent_id, "third")
        assert runtime.subagents.cancel(parent.agent_id) == 2
        assert all(isinstance(r, asyncio.CancelledError) for r in await asyncio.gather(*tasks, return_exceptions=True))
        assert {r["status"] for r in runtime.subagents.tree()} == {"cancelled"}
    asyncio.run(scenario())


def test_session_cancel_reaches_job_children_and_cannot_reopen_active_session():
    async def scenario():
        runtime = AgentRuntime()
        runtime.open_session()
        async def wait():
            await asyncio.sleep(30)
        parent = runtime.jobs.start("parent", wait)
        child = runtime.jobs.start("child", wait, parent_job_id=parent.job_id)
        with pytest.raises(RuntimeError, match="active"):
            runtime.open_session("other")
        runtime.cancel("host stopped")
        assert (await runtime.jobs.wait(parent.job_id)).status == JobStatus.CANCELLED
        assert (await runtime.jobs.wait(child.job_id)).status == JobStatus.CANCELLED
    asyncio.run(scenario())


def test_expired_lease_cannot_be_renewed_or_output_extended():
    async def scenario():
        runtime = AgentRuntime()
        runtime.open_session()
        async def wait():
            await asyncio.sleep(.03)
        job = runtime.jobs.start("lease", wait, lease_seconds=.001)
        await asyncio.sleep(.01)
        with pytest.raises(JobConflict, match="expired"):
            runtime.jobs.renew_lease(job.job_id, 100)
        with pytest.raises(JobConflict):
            runtime.jobs.emit_output(job.job_id, "late")
        assert (await runtime.jobs.wait(job.job_id)).status == JobStatus.INTERRUPTED
    asyncio.run(scenario())


@pytest.mark.parametrize("seconds", [float("nan"), float("inf"), True, 0, -1])
def test_invalid_leases_fail_before_dispatch(seconds):
    async def scenario():
        runtime = AgentRuntime()
        runtime.open_session()
        with pytest.raises(ValueError):
            runtime.jobs.start("bad", lambda: None, lease_seconds=seconds)
        assert runtime.jobs.list() == []
    asyncio.run(scenario())


def test_subagent_unknown_parent_and_permission_widening_rejected():
    runtime = AgentRuntime()
    runtime.open_session()
    with pytest.raises(KeyError):
        runtime.subagents.register(object(), parent_agent_id="missing")
    parent = runtime.subagents.register(object(), parent_permissions=PermissionSet(allowed=frozenset({"read"})))
    with pytest.raises(ValueError):
        runtime.subagents.register(object(), parent_agent_id=parent.agent_id,
                                   parent_permissions=PermissionSet(allowed=frozenset({"write"})))


def test_shared_transition_preserves_legacy_fields_and_rejects_stale_or_uncertain():
    legacy = dict(status="running", nonce="old", agent="a", lease_epoch=0)
    original = deepcopy(legacy)
    completed = transition(legacy, "completed", expected=("old", 0))
    assert legacy == original
    assert view(completed)["attempt_id"] == "old"
    with pytest.raises(JobConflict):
        transition(legacy, "completed", expected=("other", 1))
    uncertain = transition(legacy, "uncertain")
    with pytest.raises(JobConflict, match="reconciliation"):
        transition(uncertain, "completed")
    assert transition(uncertain, "completed", reconcile=True)["status"] == "completed"


def test_external_outcome_uses_same_attempt_epoch_fence(tmp_path):
    store = ControlStore(tmp_path / "control")
    record = dict(id="j", agent="a", status="running", nonce="same", attempt_id="new", epoch=2)
    with store.transaction() as db:
        store.put("job", record, db)
        with pytest.raises(StateConflict, match="stale"):
            jobs._apply_outcome(store, {**record, "attempt_id": "old", "epoch": 1}, {"status": "completed"}, db)
    assert store.get("job", "j")["status"] == "running"


def test_two_sqlite_managers_atomically_deduplicate_submission(tmp_path):
    path = tmp_path / "sessions.db"
    runtimes = [AgentRuntime(session_store=SqliteSessionStore(path)) for _ in range(2)]
    for runtime in runtimes:
        runtime.open_session("s")
    ready = threading.Barrier(2)
    calls = []
    def submit(runtime):
        async def scenario():
            async def operation():
                calls.append(1)
                await asyncio.sleep(.02)
                return "once"
            ready.wait(timeout=5)
            record = runtime.jobs.start("same", operation, idempotency_key="shared", lease_seconds=5)
            await runtime.jobs.wait(record.job_id)
            return record.job_id
        return asyncio.run(scenario())
    with ThreadPoolExecutor(2) as pool:
        ids = list(pool.map(submit, runtimes))
    assert ids[0] == ids[1]
    assert calls == [1]
    assert len(runtimes[0].jobs.list()) == 1


def test_thread_cancel_retains_slot_until_host_reconciles():
    async def scenario():
        runtime = AgentRuntime()
        runtime.open_session()
        runtime.subagents.max_concurrency = 1
        entered, release, finished = threading.Event(), threading.Event(), threading.Event()
        class ThreadChild:
            def run(self, query):
                entered.set()
                release.wait(5)
                finished.set()
                return "side effect finished"
        child = runtime.subagents.register(ThreadChild())
        task = asyncio.create_task(runtime.subagents.run(child.agent_id, "work"))
        try:
            assert await asyncio.to_thread(entered.wait, 2)
            assert runtime.subagents.cancel(child.agent_id) == 1
            with pytest.raises(asyncio.CancelledError):
                await task
            job = runtime.jobs.list()[0]
            assert runtime.jobs.status(job.job_id)["runner_stopped"] is False
            with pytest.raises(RuntimeError, match="concurrency"):
                await runtime.subagents.run(child.agent_id, "must not overlap")
            release.set()
            assert await asyncio.to_thread(finished.wait, 2)
            runtime.jobs.reconcile(job.job_id, note="Host independently joined the thread and checked its effects")
            assert runtime.jobs.status(job.job_id)["runner_stopped"] is True
        finally:
            release.set()
    asyncio.run(scenario())


def test_cancelled_session_requires_host_resume_before_new_jobs():
    async def scenario():
        runtime = AgentRuntime()
        runtime.open_session()
        runtime.cancel()
        with pytest.raises(JobConflict, match="cancelled Session"):
            runtime.jobs.start("blocked", lambda: 1)
        runtime.resume("host approval")
        job = runtime.jobs.start("allowed", lambda: 1)
        assert (await runtime.jobs.wait(job.job_id)).result == 1
    asyncio.run(scenario())


def test_cold_legacy_job_requires_reconciliation_note_before_resume():
    async def scenario():
        runtime = AgentRuntime()
        runtime.open_session()
        runtime._append("job.created", {"job": dict(name="old", job_id="old", status="running")})
        runtime.jobs.mark_interrupted()
        with pytest.raises(JobConflict, match="reconciliation note"):
            runtime.jobs.resume("old", lambda: "replayed")
        job = runtime.jobs.resume("old", lambda: "host approved", note="Host verified old process is gone")
        assert (await runtime.jobs.wait(job.job_id)).result == "host approved"
    asyncio.run(scenario())


def test_legacy_running_subagent_requires_host_acknowledgement_to_bind():
    runtime = AgentRuntime()
    runtime.open_session()
    runtime._append("subagent.started", {"agent": dict(agent_id="old", name="old child", parent_agent_id=None,
        depth=1, permissions=dict(allowed=[], denied=[], max_risk="L3"), persistent=True, status="running", metadata={})})
    runtime.subagents.restore(runtime.session)
    assert runtime.subagents.tree()[0]["status"] == "interrupted"
    with pytest.raises(RuntimeError, match="reconciliation note"):
        runtime.subagents.bind("old", object())
    runtime.subagents.bind("old", object(), note="Host confirmed the old child is no longer running")
    assert runtime.subagents.tree()[0]["status"] == "ready"
    assert runtime.subagents.tree()[0]["bound"] is True


def test_cold_restart_recovers_completion_outbox_once_and_skips_legacy_unknown(tmp_path):
    path = tmp_path / "sessions.db"
    runtime = AgentRuntime(session_store=SqliteSessionStore(path))
    runtime.open_session("s")
    runtime._append("job.completed", {"job": dict(name="crash gap", job_id="new", status="success",
        result="persisted", attempt_id="attempt", lease_epoch=1, notification_sent=False, runner_stopped=True)})
    runtime._append("job.completed", {"job": dict(name="old notified elsewhere", job_id="legacy", status="success")})
    for _ in range(2):
        restored = AgentRuntime(session_store=SqliteSessionStore(path))
        restored.open_session("s")
        assert restored.jobs.get("new").notification_sent is True
        assert len(restored.inbox.pending()) == 1
        assert restored.inbox.pending()[0].correlation_id == "new"


def test_sqlite_notification_and_ack_are_rolled_back_together(tmp_path, monkeypatch):
    path = tmp_path / "sessions.db"
    runtime = AgentRuntime(session_store=SqliteSessionStore(path))
    runtime.open_session("s")
    runtime._append("job.completed", {"job": dict(name="ready", job_id="j", status="success",
        result="done", attempt_id="attempt", lease_epoch=1, notification_sent=False, runner_stopped=True)})
    enqueue = runtime.inbox.enqueue
    def fail(*args, **kwargs):
        enqueue(*args, **kwargs)
        raise OSError("injected crash before acknowledgement")
    monkeypatch.setattr(runtime.inbox, "enqueue", fail)
    with pytest.raises(OSError):
        runtime.jobs.recover_notifications()
    assert runtime.inbox.pending() == []
    assert runtime.jobs.get("j").notification_sent is False
    restarted = AgentRuntime(session_store=SqliteSessionStore(path))
    restarted.open_session("s")
    assert len(restarted.inbox.pending()) == 1
    assert restarted.jobs.get("j").notification_sent is True
