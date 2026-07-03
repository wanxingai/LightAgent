import json
from types import SimpleNamespace

from LightAgent import HookDecision, LightAgent, RunResult, TraceEvent, TraceRecorder


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
    def create(self, **params):
        exc = Exception("provider failure")
        exc.status_code = 503
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


def event_types(trace):
    return [event["type"] for event in trace]


def test_trace_events_are_opt_in_on_structured_result():
    agent = make_agent()
    attach_client(agent, StaticCompletions("hello"))

    result = agent.run("hello", result_format="object", trace=True)

    assert isinstance(result, RunResult)
    assert result.content == "hello"
    assert event_types(result.trace) == ["run_start", "model_request", "model_response", "run_end"]
    assert result.trace == agent.export_trace()
    assert {event["trace_id"] for event in result.trace} == {result.trace_id}
    assert result.trace[1]["data"]["message_count"] == 2
    assert "messages" not in result.trace[1]["data"]


def test_trace_false_keeps_result_trace_empty():
    agent = make_agent()
    attach_client(agent, StaticCompletions("hello"))

    result = agent.run("hello", result_format="object")

    assert result.trace == []
    assert agent.export_trace() == []


def test_tool_call_and_result_are_recorded_in_trace():
    agent = make_agent()
    attach_client(agent, ToolCallCompletions())

    result = agent.run("add", tools=[runtime_add], result_format="object", trace=True)

    types = event_types(result.trace)
    assert result.content == "ok 42"
    assert types.count("model_request") == 2
    assert "tool_call" in types
    assert "tool_result" in types
    tool_call = next(event for event in result.trace if event["type"] == "tool_call")
    tool_result = next(event for event in result.trace if event["type"] == "tool_result")
    assert tool_call["data"]["name"] == "runtime_add"
    assert tool_result["data"]["output"] == '{"result": 42}'


def test_model_error_is_recorded_in_trace():
    agent = make_agent()
    attach_client(agent, ErrorCompletions())

    result = agent.run("hello", result_format="object", trace=True)

    types = event_types(result.trace)
    assert result.error.startswith("[LA-503]")
    assert types == ["run_start", "model_request", "error", "run_end"]
    assert result.trace[-1]["data"]["success"] is False


def test_trace_primitives_export_dicts():
    recorder = TraceRecorder(enabled=True, trace_id="trace-1", parent_trace_id="parent-1", run_group_id="group-1")
    recorder.record("run_start", {"query": "hello"})

    exported = recorder.to_list()

    assert isinstance(exported[0], dict)
    assert exported[0]["trace_id"] == "trace-1"
    assert exported[0]["parent_trace_id"] == "parent-1"
    assert exported[0]["run_group_id"] == "group-1"
    assert TraceEvent(type="custom", data={"ok": True}).to_dict()["type"] == "custom"


def test_agent_trace_can_carry_parent_trace_and_run_group():
    agent = make_agent()
    attach_client(agent, StaticCompletions("hello"))

    result = agent.run(
        "hello",
        result_format="object",
        trace=True,
        parent_trace_id="parent-run",
        run_group_id="workflow-1",
    )

    assert result.trace_id
    assert {event["parent_trace_id"] for event in result.trace} == {"parent-run"}
    assert {event["run_group_id"] for event in result.trace} == {"workflow-1"}


def test_before_model_request_hook_can_replace_payload():
    def inject_context(ctx):
        if ctx.phase != "before_model_request":
            return None
        params = dict(ctx.payload["params"])
        messages = list(params["messages"])
        messages[-1] = {**messages[-1], "content": "rewritten"}
        params["messages"] = messages
        return HookDecision.replace({"params": params})

    agent = LightAgent(
        model="gpt-4o-mini",
        api_key="test-key",
        base_url="http://127.0.0.1:9/v1",
        auto_discover_skills=False,
        hooks=[inject_context],
    )
    completions = attach_client(agent, StaticCompletions("hello"))

    result = agent.run("hello", result_format="object", trace=True)

    assert result.content == "hello"
    assert completions.calls[0]["messages"][-1]["content"] == "rewritten"
    assert any(event["type"] == "hook_decision" for event in result.trace)


def test_hook_can_block_run_before_model_request():
    def block_model(ctx):
        if ctx.phase == "before_model_request":
            return HookDecision.block("budget exceeded")
        return None

    agent = LightAgent(
        model="gpt-4o-mini",
        api_key="test-key",
        base_url="http://127.0.0.1:9/v1",
        auto_discover_skills=False,
        hooks=[block_model],
    )
    completions = attach_client(agent, StaticCompletions("should not run"))

    result = agent.run("hello", result_format="object", trace=True)

    assert result.error.startswith("[LA-HOOK]")
    assert "budget exceeded" in result.error
    assert completions.calls == []
    assert any(event["type"] == "hook_block" for event in result.trace)


def test_tool_hooks_can_replace_arguments_and_outputs():
    def adjust_tool(ctx):
        if ctx.phase == "before_tool_call":
            return HookDecision.replace({
                "tool_name": ctx.payload["tool_name"],
                "arguments": {"a": 40, "b": 2},
            })
        if ctx.phase == "after_tool_result":
            return HookDecision.replace({
                "tool_name": ctx.payload["tool_name"],
                "output": "hooked output",
            })
        return None

    agent = LightAgent(
        model="gpt-4o-mini",
        api_key="test-key",
        base_url="http://127.0.0.1:9/v1",
        auto_discover_skills=False,
        hooks=[adjust_tool],
    )
    completions = attach_client(agent, ToolCallCompletions())

    result = agent.run("add", tools=[runtime_add], result_format="object", trace=True)

    assert result.content == "ok 42"
    assert completions.calls[1]["messages"][-1]["content"] == "hooked output"
    tool_result = next(event for event in result.trace if event["type"] == "tool_result")
    assert tool_result["data"]["output"] == "hooked output"


def test_after_run_hook_closes_successful_run():
    phases = []

    def audit_run(ctx):
        phases.append((ctx.phase, ctx.payload.get("success"), ctx.payload.get("content")))
        return None

    agent = LightAgent(
        model="gpt-4o-mini",
        api_key="test-key",
        base_url="http://127.0.0.1:9/v1",
        auto_discover_skills=False,
        hooks=[audit_run],
    )
    attach_client(agent, StaticCompletions("hello"))

    result = agent.run("hello", result_format="object", trace=True)

    assert result.content == "hello"
    assert ("after_run", True, "hello") in phases


def test_on_error_hook_runs_for_hook_block():
    errors = []

    def block_and_collect(ctx):
        if ctx.phase == "before_model_request":
            return HookDecision.block("budget exceeded")
        if ctx.phase == "on_error":
            errors.append(ctx.payload)
        return None

    agent = LightAgent(
        model="gpt-4o-mini",
        api_key="test-key",
        base_url="http://127.0.0.1:9/v1",
        auto_discover_skills=False,
        hooks=[block_and_collect],
    )
    attach_client(agent, StaticCompletions("should not run"))

    result = agent.run("hello", result_format="object", trace=True)

    assert result.error.startswith("[LA-HOOK]")
    assert errors[0]["stage"] == "before_model_request"
    assert errors[0]["success"] is False
    assert "budget exceeded" in errors[0]["error"]
