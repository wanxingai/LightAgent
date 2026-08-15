import asyncio
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
