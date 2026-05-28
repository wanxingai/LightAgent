import asyncio
import json
from types import SimpleNamespace

from LightAgent import (
    AsyncToolDispatcher,
    LightAgent,
    LightAgentError,
    RunResult,
    StreamEvent,
    classify_exception,
)


def make_agent():
    return LightAgent(
        model="gpt-4o-mini",
        api_key="test-key",
        base_url="http://127.0.0.1:9/v1",
        auto_discover_skills=False,
    )


class StaticCompletions:
    def __init__(self, content="hello"):
        self.calls = []
        self.content = content

    def create(self, **params):
        self.calls.append(params)
        message = SimpleNamespace(content=self.content, tool_calls=None)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class ToolCallCompletions:
    def __init__(self):
        self.calls = []

    def create(self, **params):
        self.calls.append(params)
        if len(self.calls) == 1:
            tool_call = SimpleNamespace(
                id="call_runtime_add",
                function=SimpleNamespace(name="runtime_add", arguments=json.dumps({"a": 20, "b": 22})),
            )
            message = SimpleNamespace(content=None, tool_calls=[tool_call])
            return SimpleNamespace(choices=[SimpleNamespace(message=message)])
        message = SimpleNamespace(content="ok 42", tool_calls=None)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class ErrorCompletions:
    def __init__(self, status_code):
        self.status_code = status_code

    def create(self, **params):
        exc = Exception("provider failure")
        exc.status_code = self.status_code
        raise exc


def attach_client(agent, completions):
    agent.client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    return completions


def runtime_add(a, b):
    return {"result": a + b}


runtime_add.tool_info = {
    "tool_name": "runtime_add",
    "tool_description": "Add two numbers.",
    "tool_params": [
        {"name": "a", "type": "number", "description": "left operand", "required": True},
        {"name": "b", "type": "number", "description": "right operand", "required": True},
    ],
}


def test_default_run_result_remains_string():
    agent = make_agent()
    attach_client(agent, StaticCompletions("hello"))

    result = agent.run("hello")

    assert result == "hello"
    assert isinstance(result, str)


def test_object_run_result_is_opt_in():
    agent = make_agent()
    attach_client(agent, StaticCompletions("hello"))

    result = agent.run("hello", result_format="object")

    assert isinstance(result, RunResult)
    assert result.content == "hello"
    assert result.trace_id
    assert result.error is None


def test_runtime_tools_are_recorded_in_run_result():
    agent = make_agent()
    completions = attach_client(agent, ToolCallCompletions())

    result = agent.run("add", tools=[runtime_add], result_format="object")

    assert result.content == "ok 42"
    assert result.tool_calls[0]["name"] == "runtime_add"
    assert completions.calls[1]["messages"][-1]["content"] == '{"result": 42}'


def test_model_errors_can_return_structured_result():
    agent = make_agent()
    attach_client(agent, ErrorCompletions(401))

    result = agent.run("hello", result_format="object")

    assert isinstance(result, RunResult)
    assert result.error.startswith("[LA-401]")
    assert result.content == result.error


def test_stream_default_remains_generator_and_event_is_opt_in():
    agent = make_agent()
    attach_client(agent, ErrorCompletions(429))

    legacy_stream = agent.run("hello", stream=True)
    assert next(legacy_stream).startswith("[LA-429]")

    event_stream = agent.run("hello", stream=True, result_format="event")
    event = next(event_stream)
    assert isinstance(event, StreamEvent)
    assert event.type == "error"
    assert str(event.data).startswith("[LA-429]")


def test_tool_parameter_validation_missing_required_and_wrong_type():
    dispatcher = AsyncToolDispatcher(
        {"runtime_add": runtime_add},
        {"runtime_add": runtime_add.tool_info},
    )

    missing = asyncio.run(dispatcher.dispatch("runtime_add", {"a": 1}))
    wrong_type = asyncio.run(dispatcher.dispatch("runtime_add", {"a": "1", "b": 2}))

    assert missing.startswith("[LA-TOOL]")
    assert "missing required parameter `b`" in missing
    assert wrong_type.startswith("[LA-TOOL]")
    assert "parameter `a` expected `number`" in wrong_type


def test_lightagent_error_is_catchable_and_classification_still_works():
    error = LightAgentError("LA-413", details="too large")
    assert error.code == "LA-413"
    assert "[LA-413]" in str(error)

    exc = Exception("quota exceeded")
    exc.status_code = 429
    assert classify_exception(exc).code == "LA-429"
