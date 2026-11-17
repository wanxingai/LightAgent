"""Regression tests for non-stream assistant message normalization.

Provider responses are objects (OpenAI SDK models, Pydantic v2 models, custom
namespaces). They must never be appended to ``chat_params["messages"]`` raw:
``ContextBudget.estimate`` calls ``json.dumps`` on the list, and session events
serialize it, so an opaque object either crashes the next request or degrades
the event log to a ``repr`` string.
"""
import json
from types import SimpleNamespace

import pytest
from openai.types.chat import ChatCompletionMessage
from pydantic import BaseModel

from LightAgent import InMemorySessionStore, LightAgent
from LightAgent.session import ContextBudget


def echo_tool(text: str = "x") -> str:
    """Echo text back."""
    return f"echo:{text}"


echo_tool.tool_info = {
    "tool_name": "echo_tool",
    "tool_description": "Echo text back.",
    "tool_params": [
        {"name": "text", "description": "Text to echo.", "type": "string", "required": False},
    ],
}


class PydanticFunction(BaseModel):
    name: str
    arguments: str


class PydanticToolCall(BaseModel):
    id: str
    type: str = "function"
    function: PydanticFunction


class PydanticMessage(BaseModel):
    role: str = "assistant"
    content: str | None = None
    reasoning_content: str | None = None
    tool_calls: list[PydanticToolCall] | None = None


class TwoStepCompletions:
    """First create() returns a tool call, second returns a plain reply."""

    def __init__(self, tool_name="echo_tool", tool_args=None, message_factory=None):
        self.tool_name = tool_name
        self.tool_args = tool_args or {}
        self.message_factory = message_factory
        self.calls = []

    def create(self, **params):
        self.calls.append(params)
        if len(self.calls) == 1:
            if self.message_factory is not None:
                return SimpleNamespace(choices=[SimpleNamespace(
                    message=self.message_factory(self.tool_name, self.tool_args))])
            tool_call = SimpleNamespace(
                id="call_1",
                function=SimpleNamespace(
                    name=self.tool_name,
                    arguments=json.dumps(self.tool_args),
                ),
            )
            return SimpleNamespace(choices=[SimpleNamespace(
                message=SimpleNamespace(content=None, tool_calls=[tool_call]))])
        return SimpleNamespace(choices=[SimpleNamespace(
            message=SimpleNamespace(content="final-reply", tool_calls=None))])


def make_agent(completions, **kwargs):
    agent = LightAgent(
        model="test-model",
        api_key="test-key",
        base_url="http://127.0.0.1:9/v1",
        auto_discover_skills=False,
        **kwargs,
    )
    agent.client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    return agent


def assistant_messages(agent):
    return [m for m in agent.chat_params["messages"] if m.get("role") == "assistant"]


def test_nonstream_tool_turn_stores_assistant_message_as_dict():
    completions = TwoStepCompletions()
    agent = make_agent(completions)

    assert agent.run("use echo_tool", tools=[echo_tool]) == "final-reply"

    assistants = assistant_messages(agent)
    assert len(assistants) == 1
    assert isinstance(assistants[0], dict)
    assert assistants[0]["content"] == ""
    assert assistants[0]["reasoning_content"] == ""
    assert assistants[0]["tool_calls"] == [{
        "id": "call_1",
        "type": "function",
        "function": {"name": "echo_tool", "arguments": json.dumps({})},
    }]
    assert set(assistants[0]) == {"role", "content", "reasoning_content", "tool_calls"}


def test_multimodal_content_is_json_native():
    from LightAgent.core import _coerce_assistant_message

    message = SimpleNamespace(
        role="assistant",
        content=[SimpleNamespace(type="text", text="checking")],
        reasoning_content=None,
        tool_calls=[SimpleNamespace(
            id="call_1",
            function=SimpleNamespace(name="echo_tool", arguments="{}"),
        )],
    )

    assistant = _coerce_assistant_message(message)

    assert assistant["content"] == [{"type": "text", "text": "checking"}]
    json.dumps(assistant)


def test_nonstream_tool_turn_with_context_budget_issues_second_request():
    completions = TwoStepCompletions()
    agent = make_agent(
        completions,
        context_budget=ContextBudget(max_tokens=100_000, reserved_output_tokens=1024),
    )

    assert agent.run("use echo_tool", tools=[echo_tool]) == "final-reply"
    assert len(completions.calls) == 2
    assert completions.calls[1]["messages"][2]["role"] == "assistant"


def test_pydantic_v2_message_is_normalized():
    def factory(tool_name, tool_args):
        return PydanticMessage(
            content=None,
            reasoning_content="need the tool",
            tool_calls=[PydanticToolCall(
                id="call_pydantic",
                function=PydanticFunction(name=tool_name, arguments=json.dumps(tool_args)),
            )],
        )

    completions = TwoStepCompletions(message_factory=factory)
    agent = make_agent(
        completions,
        context_budget=ContextBudget(max_tokens=100_000, reserved_output_tokens=1024),
    )

    assert agent.run("use echo_tool", tools=[echo_tool]) == "final-reply"

    assistant = assistant_messages(agent)[0]
    assert isinstance(assistant, dict)
    assert assistant["reasoning_content"] == "need the tool"
    assert assistant["tool_calls"][0]["id"] == "call_pydantic"
    assert len(completions.calls) == 2


def test_openai_sdk_message_is_normalized():
    def factory(tool_name, tool_args):
        return ChatCompletionMessage(
            role="assistant",
            content=None,
            tool_calls=[{
                "id": "call_sdk",
                "type": "function",
                "function": {"name": tool_name, "arguments": json.dumps(tool_args)},
            }],
        )

    completions = TwoStepCompletions(message_factory=factory)
    agent = make_agent(completions)

    agent.run("use echo_tool", tools=[echo_tool])

    assistant = assistant_messages(agent)[0]
    assert isinstance(assistant, dict)
    assert assistant["content"] == ""
    assert assistant["tool_calls"][0]["id"] == "call_sdk"
    assert assistant["tool_calls"][0]["function"]["name"] == "echo_tool"


def test_reasoning_content_is_preserved_for_attribute_objects():
    def factory(tool_name, tool_args):
        return SimpleNamespace(
            role="assistant",
            content=None,
            reasoning_content="deepseek reasoning",
            tool_calls=[SimpleNamespace(
                id="call_reasoning",
                function=SimpleNamespace(name=tool_name, arguments=json.dumps(tool_args)),
            )],
        )

    completions = TwoStepCompletions(message_factory=factory)
    agent = make_agent(completions)

    agent.run("use echo_tool", tools=[echo_tool])

    assistant = assistant_messages(agent)[0]
    assert assistant["reasoning_content"] == "deepseek reasoning"


def test_non_string_arguments_are_serialized():
    from LightAgent.core import _coerce_assistant_message

    message = SimpleNamespace(
        role="assistant",
        content=None,
        tool_calls=[SimpleNamespace(
            id="call_dict_args",
            function=SimpleNamespace(name="echo_tool", arguments={"text": "hi"}),
        )],
    )

    assistant = _coerce_assistant_message(message)

    arguments = assistant["tool_calls"][0]["function"]["arguments"]
    assert json.loads(arguments) == {"text": "hi"}


def test_model_requested_event_messages_are_json_native():
    store = InMemorySessionStore()
    completions = TwoStepCompletions()
    agent = make_agent(completions, session_store=store)

    agent.run("use echo_tool", tools=[echo_tool], session_id="session-1")

    session = store.get("session-1")
    requests = [event for event in session.events if event.type == "model.requested"]
    assert len(requests) == 2
    for request in requests:
        assert all(isinstance(message, dict) for message in request.data["messages"])
    json.dumps(requests[-1].data["messages"])


def test_history_provider_message_is_normalized_with_context_budget():
    class OneShotCompletions:
        def __init__(self):
            self.calls = []

        def create(self, **params):
            self.calls.append(params)
            return SimpleNamespace(choices=[SimpleNamespace(
                message=SimpleNamespace(content="final-reply", tool_calls=None))])

    store = InMemorySessionStore()
    completions = OneShotCompletions()
    agent = make_agent(
        completions,
        session_store=store,
        context_budget=ContextBudget(max_tokens=100_000, reserved_output_tokens=1024),
    )

    result = agent.run(
        "continue",
        history=[SimpleNamespace(role="assistant", content="hi")],
        session_id="session-history",
    )

    assert result == "final-reply"
    assert completions.calls[0]["messages"][1] == {"role": "assistant", "content": "hi"}

    session = store.get("session-history")
    requests = [event for event in session.events if event.type == "model.requested"]
    assert len(requests) == 1
    assert all(isinstance(message, dict) for message in requests[0].data["messages"])
    json.dumps(agent.get_history())


def test_dict_assistant_message_is_not_mutated():
    from LightAgent.core import _coerce_assistant_message

    message = {
        "role": "assistant",
        "content": None,
        "tool_calls": [{
            "id": "call_mapping",
            "type": "function",
            "function": {"name": "echo_tool", "arguments": "{}"},
        }],
    }

    assistant = _coerce_assistant_message(message)

    assert assistant is not message
    assert message["content"] is None
    assert message["tool_calls"][0]["function"]["name"] == "echo_tool"
    assert assistant["content"] == ""
    assert assistant["tool_calls"][0]["id"] == "call_mapping"


@pytest.mark.parametrize("budget", [None, ContextBudget(max_tokens=100_000, reserved_output_tokens=1024)])
def test_stream_assistant_message_stays_json_native(budget):
    class StreamCompletions:
        def __init__(self):
            self.calls = []

        def create(self, **params):
            self.calls.append(params)
            if len(self.calls) == 1:
                tool_call = SimpleNamespace(
                    index=0,
                    id="call_stream",
                    function=SimpleNamespace(name="echo_tool", arguments=json.dumps({})),
                )
                delta = SimpleNamespace(reasoning_content=None, content=None, tool_calls=[tool_call])
                return iter([
                    SimpleNamespace(choices=[SimpleNamespace(delta=delta, finish_reason=None)]),
                    SimpleNamespace(choices=[SimpleNamespace(
                        delta=SimpleNamespace(reasoning_content=None, content=None, tool_calls=None),
                        finish_reason="tool_calls",
                    )]),
                ])
            return iter([
                SimpleNamespace(choices=[SimpleNamespace(
                    delta=SimpleNamespace(reasoning_content=None, content="final-reply", tool_calls=None),
                    finish_reason=None,
                )]),
                SimpleNamespace(choices=[SimpleNamespace(
                    delta=SimpleNamespace(reasoning_content=None, content=None, tool_calls=None),
                    finish_reason="stop",
                )]),
            ])

    completions = StreamCompletions()
    agent = make_agent(completions, context_budget=budget)

    list(agent.run("use echo_tool", tools=[echo_tool], stream=True))

    assistant = assistant_messages(agent)[0]
    assert isinstance(assistant, dict)
    assert assistant["tool_calls"][0]["id"] == "call_stream"
