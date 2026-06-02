from LightAgent import LightFlow, LightFlowResult, RunResult


class FakeAgent:
    def __init__(self, name, responses):
        self.name = name
        self.responses = list(responses)
        self.calls = []

    def run(self, query, **kwargs):
        self.calls.append({"query": query, "kwargs": kwargs})
        response = self.responses.pop(0)
        if isinstance(response, RunResult):
            return response
        return RunResult(content=str(response), trace=[{"type": "agent_event", "data": {"agent": self.name}}])


def test_lightflow_runs_single_step_and_returns_object_result():
    agent = FakeAgent("writer", ["done"])
    flow = LightFlow().step("write", agent=agent)

    result = flow.run("draft this", trace=True)

    assert isinstance(result, LightFlowResult)
    assert result.success is True
    assert result.content == "done"
    assert result.steps[0].name == "write"
    assert agent.calls[0]["query"] == "draft this"
    assert [event["type"] for event in result.trace] == ["flow_start", "step_start", "step_end", "flow_end"]


def test_lightflow_passes_dependency_outputs_to_later_steps():
    research = FakeAgent("research", ["facts"])
    writer = FakeAgent("writer", ["report"])
    flow = (
        LightFlow()
        .step("research", agent=research)
        .step("write", agent=writer, depends_on=["research"])
    )

    result = flow.run("analyze company")

    assert result.content == "report"
    assert "Previous step outputs:" in writer.calls[0]["query"]
    assert "research: facts" in writer.calls[0]["query"]


def test_lightflow_supports_callable_step_query():
    research = FakeAgent("research", ["facts"])
    writer = FakeAgent("writer", ["report"])
    flow = (
        LightFlow()
        .step("research", agent=research)
        .step(
            "write",
            agent=writer,
            depends_on=["research"],
            query=lambda context: f"Write using {context['outputs']['research']}",
        )
    )

    flow.run("ignored")

    assert writer.calls[0]["query"] == "Write using facts"


def test_lightflow_retries_failed_step_and_records_attempts():
    flaky = FakeAgent("flaky", [
        RunResult(content="[LA-500] failed", error="[LA-500] failed"),
        "recovered",
    ])
    flow = LightFlow().step("flaky", agent=flaky, max_retry=2)

    result = flow.run("try it")

    assert result.success is True
    assert result.content == "recovered"
    assert result.steps[0].attempts == 2
    assert len(flaky.calls) == 2


def test_lightflow_stops_on_step_error_after_retries():
    failing = FakeAgent("failing", [
        RunResult(content="[LA-500] failed", error="[LA-500] failed"),
        RunResult(content="[LA-500] failed again", error="[LA-500] failed again"),
    ])
    skipped = FakeAgent("skipped", ["should not run"])
    flow = (
        LightFlow()
        .step("failing", agent=failing, max_retry=2)
        .step("skipped", agent=skipped, depends_on=["failing"])
    )

    result = flow.run("try it", trace=True)

    assert result.success is False
    assert result.error == "[LA-500] failed again"
    assert result.steps[0].attempts == 2
    assert skipped.calls == []
    assert result.trace[-1]["data"]["success"] is False


def test_lightflow_detects_unknown_dependency_and_cycles():
    flow = LightFlow().step("write", agent=FakeAgent("writer", ["done"]), depends_on=["missing"])
    try:
        flow.run("hello")
    except ValueError as exc:
        assert "unknown step" in str(exc)
    else:
        raise AssertionError("expected unknown dependency error")

    cyclic = (
        LightFlow()
        .step("a", agent=FakeAgent("a", ["a"]), depends_on=["b"])
        .step("b", agent=FakeAgent("b", ["b"]), depends_on=["a"])
    )
    try:
        cyclic.run("hello")
    except ValueError as exc:
        assert "cycle detected" in str(exc)
    else:
        raise AssertionError("expected cycle error")


def test_lightflow_result_format_dict_and_str():
    agent = FakeAgent("writer", ["done", "done"])
    flow = LightFlow().step("write", agent=agent)

    as_dict = flow.run("draft this", result_format="dict")
    as_str = flow.run("draft this", result_format="str")

    assert as_dict["content"] == "done"
    assert as_dict["success"] is True
    assert as_dict["steps"][0]["name"] == "write"
    assert as_str == "done"
