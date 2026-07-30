from LightAgent import EvaluationCase, LightEvaluator, RunResult


class FakeTarget:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def run(self, query, **kwargs):
        self.calls.append((query, kwargs))
        return self.result


def test_evaluator_scores_output_tools_trace_and_cost():
    target = FakeTarget(RunResult(
        content="Weather is sunny.",
        tool_calls=[{"name": "get_weather"}],
        usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        trace=[
            {"type": "model_request", "data": {"latency_ms": 8}},
            {"type": "tool_call", "data": {"name": "get_weather"}},
            {"type": "tool_result", "data": {"name": "get_weather", "latency_ms": 3}},
            {"type": "run_end", "data": {"success": True, "duration_ms": 12}},
        ],
    ))
    evaluator = LightEvaluator(pricing={
        "input_per_million": 1.0,
        "output_per_million": 2.0,
    })

    report = evaluator.run(target, [EvaluationCase(
        name="weather",
        query="weather",
        expected_output_contains=("sunny",),
        expected_tools=("get_weather",),
        expected_trace_events=("tool_result", "run_end"),
    )])

    assert report.total == 1
    assert report.passed == 1
    assert report.pass_rate == 1.0
    assert report.results[0].summary.tool_success_rate == 1.0
    assert report.results[0].summary.estimated_cost_usd == 0.0002
    assert target.calls[0][1]["result_format"] == "object"
    assert target.calls[0][1]["trace"] is True


def test_evaluator_reports_all_failed_expectations():
    target = FakeTarget(RunResult(
        content="denied",
        error="[LA-HOOK] denied",
        trace=[
            {"type": "tool_call", "data": {"name": "dangerous_tool"}},
            {"type": "run_end", "data": {"success": False}},
        ],
    ))

    report = LightEvaluator().run(target, [EvaluationCase(
        name="policy",
        query="run",
        expected_output_contains=("approved",),
        forbidden_tools=("dangerous_tool",),
        expected_trace_events=("approval_rejected",),
    )])

    result = report.results[0]
    assert result.passed is False
    assert report.failed == 1
    assert len(result.failures) == 4
    assert any("expected success=True" in failure for failure in result.failures)
    assert any("forbidden tool" in failure for failure in result.failures)


def test_evaluator_supports_recovery_and_custom_checks():
    target = FakeTarget(RunResult(
        content="recovered",
        trace=[
            {"type": "error", "data": {"stage": "stream_retry"}},
            {"type": "run_end", "data": {"success": True, "retry_count": 1}},
        ],
    ))

    report = LightEvaluator().run(target, [EvaluationCase(
        name="recovery",
        query="retry",
        require_recovery=True,
        checks=(lambda result, trace: result.content == "recovered",),
    )])

    assert report.results[0].passed is True
    assert report.results[0].summary.retry_count == 1
