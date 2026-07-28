#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Trace event primitives for LightAgent observability.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Protocol


@dataclass
class TraceEvent:
    """A machine-readable event emitted during an agent run."""

    type: str
    data: dict[str, Any] = field(default_factory=dict)
    trace_id: str | None = None
    parent_trace_id: str | None = None
    run_group_id: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        event = {
            "type": self.type,
            "data": self.data,
            "trace_id": self.trace_id,
            "timestamp": self.timestamp,
        }
        if self.parent_trace_id is not None:
            event["parent_trace_id"] = self.parent_trace_id
        if self.run_group_id is not None:
            event["run_group_id"] = self.run_group_id
        return event


@dataclass
class TraceSummary:
    """Aggregated production metrics derived from structured trace events."""

    event_count: int = 0
    duration_ms: float | None = None
    model_request_count: int = 0
    model_latency_ms: float = 0.0
    tool_call_count: int = 0
    tool_success_count: int = 0
    tool_latency_ms: float = 0.0
    retry_count: int = 0
    error_count: int = 0
    error_categories: dict[str, int] = field(default_factory=dict)
    review_counts: dict[str, int] = field(default_factory=dict)
    usage: dict[str, int] = field(default_factory=dict)
    estimated_cost_usd: float | None = None

    @property
    def tool_success_rate(self) -> float | None:
        if self.tool_call_count == 0:
            return None
        return self.tool_success_count / self.tool_call_count

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_count": self.event_count,
            "duration_ms": self.duration_ms,
            "model_request_count": self.model_request_count,
            "model_latency_ms": self.model_latency_ms,
            "tool_call_count": self.tool_call_count,
            "tool_success_count": self.tool_success_count,
            "tool_success_rate": self.tool_success_rate,
            "tool_latency_ms": self.tool_latency_ms,
            "retry_count": self.retry_count,
            "error_count": self.error_count,
            "error_categories": dict(self.error_categories),
            "review_counts": dict(self.review_counts),
            "usage": dict(self.usage),
            "estimated_cost_usd": self.estimated_cost_usd,
        }


class TraceExporter(Protocol):
    """Minimal exporter contract for external observability integrations."""

    def export(
            self,
            events: list[dict[str, Any]],
            summary: TraceSummary,
            metadata: dict[str, Any] | None = None,
    ) -> Any:
        ...


class JsonlTraceExporter:
    """Append complete trace envelopes to a local JSONL audit file."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def export(
            self,
            events: list[dict[str, Any]],
            summary: TraceSummary,
            metadata: dict[str, Any] | None = None,
    ) -> Path:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        envelope = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {},
            "summary": summary.to_dict(),
            "events": events,
        }
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(envelope, ensure_ascii=False, default=str))
            stream.write("\n")
        return self.path


def normalize_usage(usage: Any) -> dict[str, int]:
    """Normalize OpenAI-compatible usage objects and dictionaries."""
    if usage is None:
        return {}
    if hasattr(usage, "model_dump"):
        usage = usage.model_dump()
    elif not isinstance(usage, dict):
        usage = {
            name: getattr(usage, name)
            for name in (
                "prompt_tokens",
                "completion_tokens",
                "total_tokens",
                "input_tokens",
                "output_tokens",
            )
            if getattr(usage, name, None) is not None
        }
    prompt = usage.get("prompt_tokens", usage.get("input_tokens", 0)) or 0
    completion = usage.get("completion_tokens", usage.get("output_tokens", 0)) or 0
    total = usage.get("total_tokens")
    if total is None:
        total = prompt + completion
    return {
        "prompt_tokens": int(prompt or 0),
        "completion_tokens": int(completion or 0),
        "total_tokens": int(total or 0),
    }


def summarize_trace(
        events: list[dict[str, Any]],
        *,
        usage: Any = None,
        pricing: dict[str, float] | None = None,
) -> TraceSummary:
    """Create stable aggregate metrics without requiring an external backend."""
    summary = TraceSummary(event_count=len(events))
    event_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    for event in events:
        event_type = str(event.get("type", ""))
        data = event.get("data") or {}
        if event_type == "model_request":
            summary.model_request_count += 1
            summary.model_latency_ms += float(data.get("latency_ms") or 0)
            current_usage = normalize_usage(data.get("usage"))
            for key in event_usage:
                event_usage[key] += current_usage.get(key, 0)
        elif event_type == "tool_call":
            summary.tool_call_count += 1
        elif event_type == "tool_result":
            if not data.get("error"):
                summary.tool_success_count += 1
            summary.tool_latency_ms += float(data.get("latency_ms") or 0)
        elif event_type == "error":
            summary.error_count += 1
            category = str(data.get("category") or data.get("stage") or "unknown")
            summary.error_categories[category] = summary.error_categories.get(category, 0) + 1
            if "retry" in category:
                summary.retry_count += 1
        elif event_type.startswith("approval_") or event_type == "human_feedback":
            summary.review_counts[event_type] = summary.review_counts.get(event_type, 0) + 1
        elif event_type == "run_end":
            if data.get("duration_ms") is not None:
                summary.duration_ms = float(data["duration_ms"])
            summary.retry_count = max(summary.retry_count, int(data.get("retry_count") or 0))

    summary.model_latency_ms = round(summary.model_latency_ms, 3)
    summary.tool_latency_ms = round(summary.tool_latency_ms, 3)
    summary.tool_success_count = min(
        summary.tool_success_count,
        summary.tool_call_count,
    )
    summary.usage = normalize_usage(usage) or event_usage

    if pricing:
        input_rate = float(pricing.get("input_per_million", 0))
        output_rate = float(pricing.get("output_per_million", 0))
        summary.estimated_cost_usd = round(
            (
                summary.usage.get("prompt_tokens", 0) * input_rate
                + summary.usage.get("completion_tokens", 0) * output_rate
            ) / 1_000_000,
            8,
        )
    return summary


def export_trace(
        events: list[dict[str, Any]],
        exporter: TraceExporter | Callable[..., Any],
        *,
        usage: Any = None,
        pricing: dict[str, float] | None = None,
        metadata: dict[str, Any] | None = None,
) -> Any:
    """Export trace data through a callable or the small TraceExporter contract."""
    summary = summarize_trace(events, usage=usage, pricing=pricing)
    method = getattr(exporter, "export", None)
    if callable(method):
        return method(events, summary, metadata)
    if callable(exporter):
        return exporter(events, summary, metadata)
    raise TypeError("exporter must be callable or provide export()")


class TraceRecorder:
    """Collect trace events when tracing is explicitly enabled."""

    def __init__(
            self,
            enabled: bool = False,
            trace_id: str | None = None,
            parent_trace_id: str | None = None,
            run_group_id: str | None = None,
    ):
        self.enabled = enabled
        self.trace_id = trace_id
        self.parent_trace_id = parent_trace_id
        self.run_group_id = run_group_id
        self.events: list[TraceEvent] = []

    def record(self, event_type: str, data: dict[str, Any] | None = None) -> TraceEvent | None:
        if not self.enabled:
            return None
        event = TraceEvent(
            type=event_type,
            data=data or {},
            trace_id=self.trace_id,
            parent_trace_id=self.parent_trace_id,
            run_group_id=self.run_group_id,
        )
        self.events.append(event)
        return event

    def to_list(self) -> list[dict[str, Any]]:
        return [event.to_dict() for event in self.events]

    def record_feedback(self, feedback: Any) -> TraceEvent | None:
        """Attach a serializable human annotation to this trace."""
        if hasattr(feedback, "to_dict"):
            data = feedback.to_dict()
        elif isinstance(feedback, dict):
            data = dict(feedback)
        else:
            raise TypeError("feedback must be a dictionary or provide to_dict()")
        return self.record("human_feedback", data)

    def summarize(
            self,
            *,
            usage: Any = None,
            pricing: dict[str, float] | None = None,
    ) -> TraceSummary:
        return summarize_trace(self.to_list(), usage=usage, pricing=pricing)

    def export(
            self,
            exporter: TraceExporter | Callable[..., Any],
            *,
            usage: Any = None,
            pricing: dict[str, float] | None = None,
            metadata: dict[str, Any] | None = None,
    ) -> Any:
        return export_trace(
            self.to_list(),
            exporter,
            usage=usage,
            pricing=pricing,
            metadata=metadata,
        )
