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
