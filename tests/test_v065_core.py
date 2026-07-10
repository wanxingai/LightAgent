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


def make_agent(**kwargs):
    return LightAgent(
        model="gpt-4o-mini",
        api_key="test-key",
        base_url="http://127.0.0.1:9/v1",
        auto_discover_skills=False,
        **kwargs,
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


class LoopingStreamToolCallCompletions:
    def __init__(self, max_create_calls):
        self.calls = []
        self.max_create_calls = max_create_calls

    def create(self, **params):
        self.calls.append(params)
        if len(self.calls) > self.max_create_calls:
            raise AssertionError("stream loop exceeded max_retry")

        call_id = f"call_runtime_add_{len(self.calls)}"
        return iter([
            SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        delta=SimpleNamespace(
                            reasoning_content=None,
                            content=None,
                            tool_calls=[
                                SimpleNamespace(
                                    index=0,
                                    id=call_id,
                                    function=SimpleNamespace(
                                        name="runtime_add",
                                        arguments=json.dumps({"a": 20, "b": 22}),
                                    ),
                                )
                            ],
                        ),
                        finish_reason=None,
                    )
                ],
            ),
            SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        delta=SimpleNamespace(
                            reasoning_content=None,
                            content=None,
                            tool_calls=None,
                        ),
                        finish_reason="tool_calls",
                    )
                ],
            ),
        ])


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


def test_stream_tool_loop_stops_at_max_retry():
    agent = make_agent()
    completions = attach_client(agent, LoopingStreamToolCallCompletions(max_create_calls=2))

    chunks = list(agent.run("loop", tools=[runtime_add], stream=True, max_retry=2, trace=True))

    assert len(completions.calls) == 2
    assert any("Max tool iterations(2) reached." in str(chunk) for chunk in chunks)
    assert {
        "success": False,
        "error": "max_tool_iterations_reached",
        "stage": "max_tool_iterations",
        "max_tool_iterations": 2,
    }.items() <= agent.export_trace()[-1]["data"].items()


def test_stream_tool_loop_respects_max_tool_iterations():
    agent = make_agent()
    completions = attach_client(agent, LoopingStreamToolCallCompletions(max_create_calls=1))

    chunks = list(agent.run(
        "loop",
        tools=[runtime_add],
        stream=True,
        max_retry=5,
        max_tool_iterations=1,
        trace=True,
    ))

    assert len(completions.calls) == 1
    assert any("Max tool iterations(1) reached." in str(chunk) for chunk in chunks)
    assert agent.export_trace()[-1]["data"]["max_tool_iterations"] == 1


def test_stream_tool_loop_uses_finish_run_hooks():
    events = []

    def collect_lifecycle(ctx):
        if ctx.phase in {"on_error", "after_run"}:
            events.append((ctx.phase, dict(ctx.payload)))
        return None

    agent = make_agent(hooks=[collect_lifecycle])
    attach_client(agent, LoopingStreamToolCallCompletions(max_create_calls=2))

    list(agent.run("loop", tools=[runtime_add], stream=True, max_retry=2, trace=True))

    assert [phase for phase, _ in events] == ["on_error", "after_run"]
    assert events[0][1]["stage"] == "max_tool_iterations"
    assert events[0][1]["error"] == "max_tool_iterations_reached"
    run_end_events = [event for event in agent.export_trace() if event["type"] == "run_end"]
    assert len(run_end_events) == 1
    assert run_end_events[0]["data"]["stage"] == "max_tool_iterations"


def test_on_error_capture_in_stream_tool_loop():
    errors = []

    def capture_error(ctx):
        if ctx.phase == "on_error":
            errors.append(dict(ctx.payload))
        return None

    agent = make_agent(hooks=[capture_error])
    attach_client(agent, LoopingStreamToolCallCompletions(max_create_calls=1))

    chunks = list(agent.run(
        "loop",
        tools=[runtime_add],
        stream=True,
        max_retry=3,
        max_tool_iterations=1,
        trace=True,
    ))

    assert any("Max tool iterations(1) reached." in str(chunk) for chunk in chunks)
    assert errors == [{
        "success": False,
        "content": None,
        "error": "max_tool_iterations_reached",
        "stage": "max_tool_iterations",
        "message": "Max tool iterations(1) reached.",
        "max_tool_iterations": 1,
    }]


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
