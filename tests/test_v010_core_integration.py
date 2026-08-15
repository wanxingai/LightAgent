import asyncio
import json
from types import SimpleNamespace

from LightAgent import BudgetLimits, InMemorySessionStore, LightAgent


class StaticCompletions:
    def __init__(self, replies):
        self.replies = iter(replies)
        self.requests = []

    def create(self, **kwargs):
        self.requests.append(kwargs)
        message = SimpleNamespace(content=next(self.replies), tool_calls=None)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=message)],
            usage=SimpleNamespace(prompt_tokens=2, completion_tokens=1, total_tokens=3),
        )


class ToolCallCompletions:
    def __init__(self):
        self.requests = []

    def create(self, **kwargs):
        self.requests.append(kwargs)
        if len(self.requests) == 1:
            tool_call = SimpleNamespace(
                id="call-add",
                function=SimpleNamespace(name="add", arguments=json.dumps({"a": 2, "b": 3})),
            )
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content=None, tool_calls=[tool_call]))]
            )
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="five", tool_calls=None))]
        )


def add(a, b):
    return a + b


add.tool_info = {
    "tool_name": "add",
    "tool_description": "Add two numbers.",
    "tool_params": [
        {"name": "a", "type": "number", "description": "First", "required": True},
        {"name": "b", "type": "number", "description": "Second", "required": True},
    ],
}


def make_agent(replies, **kwargs):
    agent = LightAgent(
        model="test-model",
        api_key="test-key",
        auto_discover_skills=False,
        **kwargs,
    )
    completions = StaticCompletions(replies)
    agent.client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    return agent, completions


def test_run_persists_balanced_turn_and_exact_model_request():
    store = InMemorySessionStore()
    agent, _ = make_agent(["hello"], session_store=store)

    assert agent.run("hi", session_id="session-1") == "hello"

    session = store.get("session-1")
    event_types = [event.type for event in session.events]
    assert event_types.count("turn.started") == 1
    assert event_types.count("turn.completed") == 1
    assert event_types.count("model.requested") == 1
    assert event_types.count("model.completed") == 1
    request = next(event for event in session.events if event.type == "model.requested")
    assert request.data["messages"][-1] == {"role": "user", "content": "hi"}
    assert session.replay().incomplete_turns == []


def test_explicit_session_continues_previous_conversation():
    store = InMemorySessionStore()
    agent, completions = make_agent(["first answer", "second answer"], session_store=store)

    agent.run("first", session_id="conversation")
    agent.run("second", session_id="conversation")

    second_messages = completions.requests[1]["messages"]
    assert {"role": "assistant", "content": "first answer"} in second_messages
    assert second_messages[-1] == {"role": "user", "content": "second"}


def test_arun_preserves_legacy_string_result():
    agent, _ = make_agent(["async answer"])

    result = asyncio.run(agent.arun("hello"))

    assert result == "async answer"


def test_astream_returns_async_iterator():
    agent, _ = make_agent(["unused"])

    def fake_run(query, **kwargs):
        return iter(["a", "b"])

    agent.run = fake_run

    async def collect():
        stream = await agent.arun("hello", stream=True)
        return [chunk async for chunk in stream]

    assert asyncio.run(collect()) == ["a", "b"]


def test_model_call_budget_blocks_before_second_request():
    agent, _ = make_agent(["first", "second"], budget_limits=BudgetLimits(model_calls=1))

    assert agent.run("first", session_id="budgeted") == "first"
    second = agent.run("second", session_id="budgeted")

    assert second.startswith("[LA-BUDGET]")
    assert agent.replay_session()["failed_turns"]


def test_tool_call_persists_balanced_request_and_result_events():
    store = InMemorySessionStore()
    agent = LightAgent(
        model="test-model",
        api_key="test-key",
        auto_discover_skills=False,
        session_store=store,
    )
    completions = ToolCallCompletions()
    agent.client = SimpleNamespace(chat=SimpleNamespace(completions=completions))

    assert agent.run("add", tools=[add], session_id="tools") == "five"

    session = store.get("tools")
    requested = [event for event in session.events if event.type == "tool.requested"]
    completed = [event for event in session.events if event.type == "tool.completed"]
    assert len(requested) == len(completed) == 1
    assert requested[0].data["name"] == completed[0].data["name"] == "add"
    assert requested[0].turn_id == completed[0].turn_id
    assert requested[0].run_id == completed[0].run_id
    assert session.replay().incomplete_turns == []


def test_model_exception_persists_failed_model_run_and_turn():
    class FailingCompletions:
        def create(self, **kwargs):
            raise RuntimeError("provider unavailable")

    store = InMemorySessionStore()
    agent, _ = make_agent(["unused"], session_store=store)
    agent.client = SimpleNamespace(chat=SimpleNamespace(completions=FailingCompletions()))

    result = agent.run("hello", session_id="failed", result_format="object")

    session = store.get("failed")
    types = [event.type for event in session.events]
    assert result.error
    assert types.count("model.requested") == 1
    assert types.count("model.failed") == 1
    assert types.count("run.failed") == 1
    assert types.count("turn.failed") == 1
    assert session.replay().failed_turns
    assert session.replay().incomplete_turns == []


def test_astream_closes_sync_iterator_when_consumer_stops_early():
    closed = []

    def stream_values():
        try:
            yield "first"
            yield "second"
        finally:
            closed.append(True)

    agent, _ = make_agent(["unused"])
    agent.run = lambda query, **kwargs: stream_values()

    async def consume_one():
        stream = await agent.arun("hello", stream=True)
        assert await anext(stream) == "first"
        await stream.aclose()

    asyncio.run(consume_one())

    assert closed == [True]


def test_public_session_control_apis_persist_events_and_fork():
    store = InMemorySessionStore()
    agent, _ = make_agent(["answer"], session_store=store)
    agent.run("hello", session_id="control")

    checkpoint = agent.checkpoint_session("before review")
    agent.pause_session("review")
    agent.resume_session("approved")
    agent.cancel_session("finished")
    forked = agent.fork_session(through_sequence=checkpoint["sequence"])

    session = store.get("control")
    assert [event.type for event in session.events[-4:]] == [
        "session.checkpointed", "session.paused", "session.resumed", "session.cancelled"
    ]
    assert forked.metadata["forked_from"] == "control"
    assert store.get(forked.session_id) is not None


def test_public_compact_session_reduces_projected_history_and_persists_event():
    store = InMemorySessionStore()
    agent, _ = make_agent(["one", "two", "three"], session_store=store)
    agent.run("first", session_id="compact")
    agent.run("second", session_id="compact")
    agent.run("third", session_id="compact")

    result = agent.compact_session(max_messages=2)

    assert result["removed_count"] > 0
    assert len(result["messages"]) <= 2
    persisted = store.get("compact")
    event = persisted.events[-1]
    assert event.type == "context.compacted"
    assert event.data["removed_count"] == result["removed_count"]
