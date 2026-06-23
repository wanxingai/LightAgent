import time

from LightAgent import JsonLightFlowStore, LightFlow, LightFlowResult, RunResult


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
    assert result.steps[0].status == "success"
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
    assert result.steps[0].status == "failed"
    assert result.steps[1].status == "skipped"
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


def test_lightflow_validate_reports_isolated_steps_without_blocking_run():
    flow = (
        LightFlow()
        .step("a", agent=FakeAgent("a", ["a"]))
        .step("b", agent=FakeAgent("b", ["b"]))
    )

    validation = flow.validate()
    result = flow.run("hello")

    assert validation["warnings"] == ["step `a` is isolated", "step `b` is isolated"]
    assert result.success is True


def test_lightflow_result_format_dict_and_str():
    agent = FakeAgent("writer", ["done", "done"])
    flow = LightFlow().step("write", agent=agent)

    as_dict = flow.run("draft this", result_format="dict")
    as_str = flow.run("draft this", result_format="str")

    assert as_dict["content"] == "done"
    assert as_dict["success"] is True
    assert as_dict["steps"][0]["name"] == "write"
    assert as_dict["steps"][0]["status"] == "success"
    assert as_str == "done"


def test_lightflow_timeout_and_fallback_agent():
    class SlowAgent(FakeAgent):
        def run(self, query, **kwargs):
            self.calls.append({"query": query, "kwargs": kwargs})
            time.sleep(0.05)
            return RunResult(content="late")

    slow = SlowAgent("slow", [])
    fallback = FakeAgent("fallback", ["fallback done"])
    flow = LightFlow().step("work", agent=slow, timeout=0.01, fallback_agent=fallback)

    result = flow.run("hello")

    assert result.success is True
    assert result.content == "fallback done"
    assert result.steps[0].used_fallback is True
    assert result.steps[0].status == "success"


def test_lightflow_approval_node_can_pause_before_execution():
    agent = FakeAgent("writer", ["done"])
    flow = LightFlow().step("approve", agent=agent, requires_approval=True)

    result = flow.run("needs review")

    assert result.status == "waiting_approval"
    assert result.success is False
    assert result.steps[0].status == "waiting_approval"
    assert agent.calls == []


def test_lightflow_checkpoint_records_pending_steps(tmp_path):
    store = JsonLightFlowStore(tmp_path)
    approve = FakeAgent("approve", ["approved"])
    write = FakeAgent("write", ["done"])
    flow = (
        LightFlow(store=store)
        .step("approve", agent=approve, requires_approval=True)
        .step("write", agent=write, depends_on=["approve"])
    )

    flow.run("needs approval", run_id="approval-run")
    record = flow.get_run("approval-run")

    statuses = {step["name"]: step["status"] for step in record["steps"]}
    assert statuses == {"approve": "waiting_approval", "write": "pending"}


def test_lightflow_checkpoint_resume_and_rerun(tmp_path):
    store = JsonLightFlowStore(tmp_path)
    first = FakeAgent("first", ["facts"])
    flaky = FakeAgent("flaky", [
        RunResult(content="[LA-500] failed", error="[LA-500] failed"),
        "fixed",
        "rerun fixed",
    ])
    flow = (
        LightFlow(store=store)
        .step("first", agent=first)
        .step("second", agent=flaky, depends_on=["first"])
    )

    failed = flow.run("do work", run_id="run-1")
    resumed = flow.resume("run-1")
    rerun = flow.rerun_step("run-1", "second")
    record = flow.get_run("run-1")

    assert failed.success is False
    assert resumed.success is True
    assert resumed.content == "fixed"
    assert rerun.content == "rerun fixed"
    assert record["run_id"] == "run-1"
    assert record["steps"][-1]["status"] == "success"
