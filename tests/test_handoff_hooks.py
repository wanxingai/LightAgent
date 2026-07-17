from LightAgent import HookDecision, LightAgent, LightSwarm, PolicyHook


class FakeTargetAgent:
    name = "worker"
    instructions = "Handle delegated tasks."

    def __init__(self):
        self.calls = []

    def run(self, query, **kwargs):
        self.calls.append((query, kwargs))
        if kwargs.get("stream"):
            return iter(["chunk-1", "chunk-2"])
        return "delegated result"


def make_source_agent(hooks=None):
    agent = LightAgent(
        name="coordinator",
        model="gpt-4o-mini",
        api_key="test-key",
        base_url="http://127.0.0.1:9/v1",
        auto_discover_skills=False,
        hooks=hooks,
    )
    agent._detect_intent = lambda query, swarm: {"transfer_to": "worker"}
    return agent


def make_swarm(target):
    swarm = LightSwarm()
    swarm.agents[target.name] = target
    return swarm


def test_on_handoff_receives_context_and_closes_source_run():
    payloads = []

    def capture_handoff(ctx):
        if ctx.phase == "on_handoff":
            payloads.append(dict(ctx.payload))

    source = make_source_agent([capture_handoff])
    target = FakeTargetAgent()

    result = source.run("delegate this", light_swarm=make_swarm(target), trace=True)

    assert result == "delegated result"
    assert payloads == [{
        "source_agent": "coordinator",
        "target_agent": "worker",
        "query": "delegate this",
        "stream": False,
    }]
    assert target.calls[0][1]["parent_trace_id"] == source.traceid
    assert target.calls[0][1]["run_group_id"]
    assert any(event["type"] == "handoff" and event["data"]["status"] == "allowed" for event in source.export_trace())
    assert source.export_trace()[-1]["type"] == "run_end"
    assert source.export_trace()[-1]["data"]["stage"] == "handoff"


def test_on_handoff_can_block_delegation_and_close_error_lifecycle():
    lifecycle = []

    def enforce_policy(ctx):
        if ctx.phase == "on_handoff":
            return HookDecision.block("delegation limit reached")
        if ctx.phase in {"on_error", "after_run"}:
            lifecycle.append(ctx.phase)

    source = make_source_agent([enforce_policy])
    target = FakeTargetAgent()

    result = source.run("delegate this", light_swarm=make_swarm(target), trace=True)

    assert result.startswith("[LA-HOOK]")
    assert "delegation limit reached" in result
    assert target.calls == []
    assert lifecycle == ["on_error", "after_run"]
    assert any(event["type"] == "handoff" and event["data"]["status"] == "blocked" for event in source.export_trace())
    assert source.export_trace()[-1]["data"]["success"] is False


def test_on_handoff_policy_failure_fails_closed():
    def broken_policy(ctx):
        raise RuntimeError("delegation policy unavailable")

    source = make_source_agent([
        PolicyHook(broken_policy, phases={"on_handoff"}),
    ])
    target = FakeTargetAgent()

    result = source.run("delegate this", light_swarm=make_swarm(target), trace=True)

    assert result.startswith("[LA-HOOK]")
    assert "failed closed" in result
    assert target.calls == []
    assert any(
        event["type"] == "hook_decision"
        and event["data"]["hook"] == "broken_policy"
        and event["data"]["action"] == "error"
        for event in source.export_trace()
    )


def test_stream_handoff_finishes_source_run_after_consumption():
    source = make_source_agent()
    target = FakeTargetAgent()

    chunks = list(source.run("delegate this", light_swarm=make_swarm(target), stream=True, trace=True))

    assert chunks == ["chunk-1", "chunk-2"]
    assert target.calls[0][1]["stream"] is True
    assert source.export_trace()[-1]["type"] == "run_end"
    assert source.export_trace()[-1]["data"]["success"] is True


def test_lightswarm_run_forwards_runtime_options_to_entry_agent():
    entry = FakeTargetAgent()
    swarm = make_swarm(entry)
    metadata = {"tenant": "acme", "request_id": "run-123"}

    result = swarm.run(
        entry,
        "delegate this",
        user_id="alice",
        metadata=metadata,
        trace=True,
        result_format="object",
        max_retry=3,
        max_tool_iterations=2,
    )

    assert result == "delegated result"
    query, kwargs = entry.calls[0]
    assert query == "delegate this"
    assert kwargs["light_swarm"] is swarm
    assert kwargs["stream"] is False
    assert kwargs["user_id"] == "alice"
    assert kwargs["metadata"] == metadata
    assert kwargs["trace"] is True
    assert kwargs["result_format"] == "object"
    assert kwargs["max_retry"] == 3
    assert kwargs["max_tool_iterations"] == 2


def test_handoff_preserves_runtime_context_for_target_agent():
    source = make_source_agent()
    target = FakeTargetAgent()
    metadata = {"tenant": "acme", "request_id": "handoff-123"}

    result = source.run(
        "delegate this",
        light_swarm=make_swarm(target),
        user_id="alice",
        metadata=metadata,
        trace=True,
        result_format="object",
        max_retry=3,
        max_tool_iterations=2,
    )

    assert result == "delegated result"
    query, kwargs = target.calls[0]
    assert query == "delegate this"
    assert kwargs["light_swarm"] is not None
    assert kwargs["stream"] is False
    assert kwargs["user_id"] == "alice"
    assert kwargs["metadata"] == metadata
    assert kwargs["trace"] is True
    assert kwargs["result_format"] == "object"
    assert kwargs["max_retry"] == 3
    assert kwargs["max_tool_iterations"] == 2
    assert kwargs["parent_trace_id"] == source.traceid
    assert kwargs["run_group_id"]
