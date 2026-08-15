import asyncio

import pytest

from LightAgent import (
    AgentRuntime,
    BudgetExceeded,
    BudgetLimits,
    GoalStatus,
    InboxMessageStatus,
    InMemorySessionStore,
    JobStatus,
    PermissionSet,
    ProgressTracker,
)


def test_inbox_goal_and_budget_restore_from_session():
    store = InMemorySessionStore()
    runtime = AgentRuntime(session_store=store, budget_limits=BudgetLimits(model_calls=3))
    runtime.open_session("durable")
    message = runtime.inbox.enqueue("steering", "focus", message_id="stable-id")
    runtime.inbox.claim_next(safe_boundary=True)
    runtime.inbox.complete(message.message_id)
    goal = runtime.goals.create("ship", acceptance_criteria=["tests pass"])
    runtime.goals.activate(goal.goal_id)
    runtime.budget.consume(model_calls=2)

    restored = AgentRuntime(session_store=store, budget_limits=BudgetLimits(model_calls=3))
    restored.open_session("durable")

    assert restored.inbox.get("stable-id").status == InboxMessageStatus.COMPLETED
    assert restored.goals.get(goal.goal_id).status == GoalStatus.ACTIVE
    assert restored.budget.remaining()["model_calls"] == 1
    assert restored.inbox.enqueue("steering", "duplicate", message_id="stable-id").content == "focus"


def test_budget_is_fail_closed():
    runtime = AgentRuntime(budget_limits=BudgetLimits(tool_calls=1))
    runtime.open_session()
    runtime.budget.consume(tool_calls=1)

    with pytest.raises(BudgetExceeded):
        runtime.budget.consume(tool_calls=1)
    assert any(event.type == "budget.exhausted" for event in runtime.session.events)


def test_progress_tracker_detects_repeated_tools():
    tracker = ProgressTracker(max_repeated_tool_calls=2)
    for _ in range(3):
        tracker.record(tool="search", arguments={"q": "same"})

    assert tracker.stalled


def test_background_job_reports_output_and_completion_to_inbox():
    async def scenario():
        runtime = AgentRuntime()
        runtime.open_session()

        async def work():
            await asyncio.sleep(0)
            return "done"

        record = runtime.jobs.start("work", work)
        runtime.jobs.emit_output(record.job_id, "halfway")
        completed = await runtime.jobs.wait(record.job_id)
        return runtime, completed

    runtime, completed = asyncio.run(scenario())

    assert completed.status == JobStatus.SUCCESS
    assert completed.output == ["halfway"]
    assert runtime.inbox.pending()[0].correlation_id == completed.job_id


class StubAgent:
    name = "child"

    async def arun(self, query, **kwargs):
        return query.upper()


def test_subagent_permissions_are_frozen_and_tree_is_inspectable():
    runtime = AgentRuntime()
    runtime.open_session()
    parent = PermissionSet(allowed=frozenset({"text.echo"}))
    record = runtime.subagents.register(
        StubAgent(), parent_permissions=parent, allowed_capabilities={"text.echo"}
    )

    result = asyncio.run(runtime.subagents.run(record.agent_id, "hello"))

    assert result == "HELLO"
    assert runtime.subagents.tree()[0]["status"] == "success"


def test_steering_waits_for_safe_boundary_and_rejection_is_restored():
    store = InMemorySessionStore()
    runtime = AgentRuntime(session_store=store)
    runtime.open_session("inbox")
    message = runtime.inbox.enqueue("steering", "change direction")

    assert runtime.inbox.claim_next(safe_boundary=False) is None
    claimed = runtime.inbox.claim_next(safe_boundary=True)
    assert claimed.message_id == message.message_id
    runtime.inbox.reject(message.message_id, "unsafe request")

    restored = AgentRuntime(session_store=store)
    restored.open_session("inbox")
    assert restored.inbox.get(message.message_id).status == InboxMessageStatus.REJECTED


def test_goal_terminal_state_and_evidence_are_restored():
    store = InMemorySessionStore()
    runtime = AgentRuntime(session_store=store)
    runtime.open_session("goals")
    goal = runtime.goals.create("release", acceptance_criteria=["tests pass"])
    runtime.goals.activate(goal.goal_id)
    runtime.goals.complete(goal.goal_id, evidence=[{"suite": "passed"}])

    with pytest.raises(ValueError, match="terminal goal"):
        runtime.goals.block(goal.goal_id, "too late")

    restored = AgentRuntime(session_store=store)
    restored.open_session("goals")
    completed = restored.goals.get(goal.goal_id)
    assert completed.status == GoalStatus.COMPLETED
    assert completed.evidence == [{"suite": "passed"}]


@pytest.mark.parametrize("dimension,value", [
    ("model_calls", 2),
    ("tool_calls", 2),
    ("tokens", 11),
    ("seconds", 1.5),
    ("cost", 0.6),
])
def test_each_budget_dimension_fails_without_committing_usage(dimension, value):
    runtime = AgentRuntime(budget_limits=BudgetLimits(**{dimension: value / 2}))
    runtime.open_session()

    with pytest.raises(BudgetExceeded) as exc_info:
        runtime.budget.consume(**{dimension: value})

    assert exc_info.value.dimension == dimension
    assert getattr(runtime.budget.usage, dimension) == 0
    assert runtime.session.events[-1].type == "budget.exhausted"


def test_background_job_failure_is_persisted_and_reported_to_inbox():
    async def scenario():
        runtime = AgentRuntime()
        runtime.open_session()

        async def fail():
            raise RuntimeError("job failed")

        record = runtime.jobs.start("failure", fail)
        return runtime, await runtime.jobs.wait(record.job_id)

    runtime, failed = asyncio.run(scenario())

    assert failed.status == JobStatus.FAILED
    assert failed.error == "RuntimeError: job failed"
    assert runtime.inbox.pending()[0].metadata["kind"] == "job_completion"
    assert any(event.type == "job.failed" for event in runtime.session.events)


def test_background_job_cancellation_and_interrupted_restore():
    store = InMemorySessionStore()

    async def scenario():
        runtime = AgentRuntime(session_store=store)
        runtime.open_session("jobs")
        started = asyncio.Event()

        async def wait_forever():
            started.set()
            await asyncio.Event().wait()

        record = runtime.jobs.start("cancelled", wait_forever)
        await started.wait()
        assert runtime.jobs.cancel(record.job_id)
        return runtime, await runtime.jobs.wait(record.job_id)

    runtime, cancelled = asyncio.run(scenario())
    assert cancelled.status == JobStatus.CANCELLED

    pending_event = runtime.session.append("job.created", {
        "job": {**cancelled.to_dict(), "job_id": "interrupted", "status": "running"}
    })
    assert pending_event.type == "job.created"
    store.save(runtime.session)
    restored = AgentRuntime(session_store=store)
    restored.open_session("jobs")
    assert restored.jobs.get("interrupted").status == JobStatus.INTERRUPTED


def test_runtime_pause_resume_cancel_checkpoint_and_fork_are_durable():
    store = InMemorySessionStore()
    runtime = AgentRuntime(session_store=store)
    runtime.open_session("control")
    runtime.pause("manual review")
    checkpoint = runtime.checkpoint("reviewed")
    runtime.resume("approved")
    runtime.cancel("operator stop")
    forked = runtime.fork(through_sequence=checkpoint.sequence)

    persisted_types = [event.type for event in store.get("control").events]
    assert persisted_types[-4:] == [
        "session.paused", "session.checkpointed", "session.resumed", "session.cancelled"
    ]
    assert forked.metadata["forked_from"] == "control"
    assert forked.metadata["forked_at_sequence"] == checkpoint.sequence
