import asyncio
import json
import time
from types import SimpleNamespace

import pytest

from LightAgent import HookContext, HookManager, LightAgent, PolicyHook


def test_observability_hook_failure_remains_isolated():
    def broken_hook(ctx):
        raise RuntimeError("audit sink unavailable")

    decision = HookManager([broken_hook]).run(HookContext(phase="before_tool_call"))

    assert decision.action == "continue"
    assert decision.metadata["hook_events"][0]["failure_mode"] == "continue"


def test_policy_hook_exception_fails_closed():
    def broken_policy(ctx):
        raise RuntimeError("policy service unavailable")

    decision = HookManager([
        PolicyHook(broken_policy, phases={"before_tool_call"}),
    ]).run(HookContext(phase="before_tool_call"))

    assert decision.action == "block"
    assert "failed closed" in decision.reason
    assert decision.metadata["policy_hook"] == "broken_policy"
    assert decision.metadata["hook_events"][0]["error_type"] == "exception"


def test_policy_hook_only_runs_for_selected_phases():
    calls = []

    def policy(ctx):
        calls.append(ctx.phase)

    manager = HookManager([PolicyHook(policy, phases={"before_tool_call"})])

    assert manager.run(HookContext(phase="before_model_request")).action == "continue"
    assert manager.run(HookContext(phase="before_tool_call")).action == "continue"
    assert calls == ["before_tool_call"]


def test_policy_hook_sync_timeout_fails_closed():
    def slow_policy(ctx):
        time.sleep(0.05)

    decision = HookManager([
        PolicyHook(slow_policy, timeout=0.005),
    ]).run(HookContext(phase="before_tool_call"))

    assert decision.action == "block"
    assert "timed out" in decision.reason
    assert decision.metadata["hook_events"][0]["error_type"] == "timeout"


def test_policy_hook_async_timeout_fails_closed():
    async def slow_policy(ctx):
        await asyncio.sleep(0.05)

    decision = HookManager([
        PolicyHook(slow_policy, timeout=0.005),
    ]).run(HookContext(phase="before_tool_call"))

    assert decision.action == "block"
    assert decision.metadata["hook_events"][0]["error_type"] == "timeout"


def test_policy_hook_rejects_invalid_configuration():
    with pytest.raises(ValueError, match="failure_mode"):
        PolicyHook(lambda ctx: None, failure_mode="raise")
    with pytest.raises(ValueError, match="greater than 0"):
        PolicyHook(lambda ctx: None, timeout=0)
    with pytest.raises(ValueError, match="greater than 0"):
        PolicyHook(lambda ctx: None, timeout="slow")


def test_policy_hook_failure_closes_agent_lifecycle():
    phases = []

    def broken_policy(ctx):
        raise RuntimeError("policy backend down")

    def collect_lifecycle(ctx):
        if ctx.phase in {"on_error", "after_run"}:
            phases.append(ctx.phase)

    agent = LightAgent(
        model="gpt-4o-mini",
        api_key="test-key",
        base_url="http://127.0.0.1:9/v1",
        auto_discover_skills=False,
        hooks=[
            PolicyHook(broken_policy, phases={"before_model_request"}),
            collect_lifecycle,
        ],
    )
    completions = SimpleNamespace(calls=[])

    def create(**params):
        completions.calls.append(params)
        return SimpleNamespace()

    completions.create = create
    agent.client = SimpleNamespace(chat=SimpleNamespace(completions=completions))

    result = agent.run("hello", result_format="object", trace=True)

    assert result.error.startswith("[LA-HOOK]")
    assert "failed closed" in result.error
    assert completions.calls == []
    assert phases == ["on_error", "after_run"]
    assert any(event["type"] == "hook_block" for event in result.trace)
    assert result.trace[-1]["type"] == "run_end"


def test_failed_tool_policy_prevents_tool_execution():
    executions = []
    errors = []

    def dangerous_tool():
        executions.append("executed")
        return "done"

    dangerous_tool.tool_info = {
        "tool_name": "dangerous_tool",
        "tool_description": "Perform a sensitive operation.",
        "tool_params": [],
    }

    def broken_policy(ctx):
        raise RuntimeError("authorization service unavailable")

    def capture_error(ctx):
        if ctx.phase == "on_error":
            errors.append(dict(ctx.payload))

    class ToolCallCompletions:
        def __init__(self):
            self.calls = []

        def create(self, **params):
            self.calls.append(params)
            if len(self.calls) == 1:
                call = SimpleNamespace(
                    id="call-dangerous",
                    function=SimpleNamespace(name="dangerous_tool", arguments=json.dumps({})),
                )
                message = SimpleNamespace(content=None, tool_calls=[call])
            else:
                message = SimpleNamespace(content="operation blocked", tool_calls=None)
            return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    agent = LightAgent(
        model="gpt-4o-mini",
        api_key="test-key",
        base_url="http://127.0.0.1:9/v1",
        auto_discover_skills=False,
        hooks=[
            PolicyHook(broken_policy, phases={"before_tool_call"}),
            capture_error,
        ],
    )
    completions = ToolCallCompletions()
    agent.client = SimpleNamespace(chat=SimpleNamespace(completions=completions))

    result = agent.run("perform operation", tools=[dangerous_tool], result_format="object", trace=True)

    assert result.content == "operation blocked"
    assert executions == []
    assert len(completions.calls) == 2
    assert errors[0]["stage"] == "tool_guardrail"
    assert "failed closed" in errors[0]["error"]
