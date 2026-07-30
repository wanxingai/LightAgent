import json
from types import SimpleNamespace

from LightAgent import (
    HumanFeedback,
    JsonlTraceExporter,
    LightAgent,
    TraceRecorder,
    normalize_usage,
    summarize_trace,
)


def test_trace_summary_aggregates_runtime_metrics():
    summary = summarize_trace(
        [
            {
                "type": "model_request",
                "data": {
                    "latency_ms": 10,
                    "usage": {
                        "prompt_tokens": 100,
                        "completion_tokens": 20,
                        "total_tokens": 120,
                    },
                },
            },
            {"type": "tool_call", "data": {"name": "search"}},
            {"type": "tool_result", "data": {"name": "search", "latency_ms": 5}},
            {"type": "error", "data": {"stage": "stream_retry"}},
            {"type": "approval_approve", "data": {"request_id": "a-1"}},
            {"type": "run_end", "data": {"duration_ms": 20, "retry_count": 1}},
        ],
        pricing={"input_per_million": 1, "output_per_million": 2},
    )

    assert summary.duration_ms == 20
    assert summary.model_request_count == 1
    assert summary.tool_success_rate == 1.0
    assert summary.retry_count == 1
    assert summary.error_categories == {"stream_retry": 1}
    assert summary.review_counts == {"approval_approve": 1}
    assert summary.estimated_cost_usd == 0.00014


def test_streaming_tool_chunks_do_not_overcount_tool_success():
    summary = summarize_trace([
        {"type": "tool_call", "data": {"name": "stream_tool"}},
        {"type": "tool_result", "data": {"name": "stream_tool", "output": "a"}},
        {"type": "tool_result", "data": {"name": "stream_tool", "output": "b"}},
    ])

    assert summary.tool_call_count == 1
    assert summary.tool_success_count == 1
    assert summary.tool_success_rate == 1.0


def test_usage_normalization_handles_nullable_provider_fields():
    assert normalize_usage({
        "prompt_tokens": None,
        "completion_tokens": None,
        "total_tokens": 4,
    }) == {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 4,
    }


def test_jsonl_exporter_and_feedback_event(tmp_path):
    recorder = TraceRecorder(enabled=True, trace_id="trace-1")
    recorder.record("run_start", {"query": "hello"})
    recorder.record_feedback(HumanFeedback(
        trace_id="trace-1",
        rating=1.0,
        label="correct",
    ))
    path = tmp_path / "traces.jsonl"

    recorder.export(JsonlTraceExporter(path), metadata={"environment": "test"})
    envelope = json.loads(path.read_text(encoding="utf-8").splitlines()[0])

    assert envelope["metadata"] == {"environment": "test"}
    assert envelope["summary"]["review_counts"] == {"human_feedback": 1}
    assert envelope["events"][1]["type"] == "human_feedback"


def test_agent_trace_contains_model_latency_usage_and_run_totals():
    agent = LightAgent(
        model="gpt-4o-mini",
        api_key="test-key",
        base_url="http://127.0.0.1:9/v1",
        auto_discover_skills=False,
    )

    def create(**params):
        message = SimpleNamespace(content="hello", tool_calls=None)
        usage = SimpleNamespace(
            prompt_tokens=20,
            completion_tokens=5,
            total_tokens=25,
        )
        return SimpleNamespace(
            choices=[SimpleNamespace(message=message)],
            usage=usage,
        )

    agent.client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=create),
        ),
    )

    result = agent.run("hello", result_format="object", trace=True)
    request = next(event for event in result.trace if event["type"] == "model_request")
    run_end = result.trace[-1]

    assert request["data"]["request_index"] == 1
    assert request["data"]["latency_ms"] >= 0
    assert request["data"]["usage"]["total_tokens"] == 25
    assert run_end["data"]["duration_ms"] >= 0
    assert run_end["data"]["model_request_count"] == 1
    assert run_end["data"]["retry_count"] == 0
    assert run_end["data"]["usage"]["total_tokens"] == 25
    assert agent.summarize_trace().usage["total_tokens"] == 25
