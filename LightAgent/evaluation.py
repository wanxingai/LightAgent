#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Dependency-free regression evaluation for LightAgent runs."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable

from .tracing import TraceSummary, summarize_trace


EvaluationCheck = Callable[[Any, list[dict[str, Any]]], Any]


@dataclass
class EvaluationCase:
    """One deterministic agent or LightFlow regression case."""

    name: str
    query: str
    expected_output_contains: tuple[str, ...] = ()
    expected_tools: tuple[str, ...] = ()
    forbidden_tools: tuple[str, ...] = ()
    expected_trace_events: tuple[str, ...] = ()
    expect_success: bool = True
    max_latency_ms: float | None = None
    require_recovery: bool = False
    checks: tuple[EvaluationCheck, ...] = ()
    run_kwargs: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationCaseResult:
    """Result and metrics for one evaluation case."""

    name: str
    passed: bool
    content: str
    error: str | None
    failures: list[str]
    duration_ms: float
    trace: list[dict[str, Any]]
    summary: TraceSummary
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "content": self.content,
            "error": self.error,
            "failures": list(self.failures),
            "duration_ms": self.duration_ms,
            "summary": self.summary.to_dict(),
            "metadata": dict(self.metadata),
        }


@dataclass
class EvaluationReport:
    """Aggregate report for a deterministic evaluation suite."""

    results: list[EvaluationCaseResult]

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def passed(self) -> int:
        return sum(result.passed for result in self.results)

    @property
    def failed(self) -> int:
        return self.total - self.passed

    @property
    def pass_rate(self) -> float:
        return self.passed / self.total if self.total else 0.0

    def to_dict(self) -> dict[str, Any]:
        durations = [result.duration_ms for result in self.results]
        costs = [
            result.summary.estimated_cost_usd
            for result in self.results
            if result.summary.estimated_cost_usd is not None
        ]
        return {
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "pass_rate": self.pass_rate,
            "average_latency_ms": sum(durations) / len(durations) if durations else 0.0,
            "estimated_cost_usd": sum(costs) if costs else None,
            "results": [result.to_dict() for result in self.results],
        }


class LightEvaluator:
    """Run fixed cases against any object exposing a compatible run() method."""

    def __init__(self, *, pricing: dict[str, float] | None = None):
        self.pricing = pricing

    def run(self, target: Any, cases: list[EvaluationCase]) -> EvaluationReport:
        if not hasattr(target, "run"):
            raise TypeError("evaluation target must provide run()")
        return EvaluationReport([self._run_case(target, case) for case in cases])

    def _run_case(self, target: Any, case: EvaluationCase) -> EvaluationCaseResult:
        kwargs = dict(case.run_kwargs)
        kwargs.setdefault("result_format", "object")
        kwargs.setdefault("trace", True)
        started = time.perf_counter()
        try:
            result = target.run(case.query, **kwargs)
            raised_error = None
        except Exception as exc:
            result = None
            raised_error = str(exc)
        duration_ms = round((time.perf_counter() - started) * 1000, 3)

        content = "" if result is None else str(getattr(result, "content", result))
        error = raised_error or getattr(result, "error", None)
        trace = list(getattr(result, "trace", []) or [])
        usage = getattr(result, "usage", None)
        summary = summarize_trace(trace, usage=usage, pricing=self.pricing)
        if summary.duration_ms is None:
            summary.duration_ms = duration_ms

        failures: list[str] = []
        success = error is None
        if success != case.expect_success:
            failures.append(f"expected success={case.expect_success}, got success={success}")

        for expected in case.expected_output_contains:
            if expected not in content:
                failures.append(f"output does not contain {expected!r}")

        event_types = [str(event.get("type")) for event in trace]
        called_tools = [
            str((event.get("data") or {}).get("name"))
            for event in trace
            if event.get("type") == "tool_call"
        ]
        for tool in case.expected_tools:
            if tool not in called_tools:
                failures.append(f"expected tool {tool!r} was not called")
        for tool in case.forbidden_tools:
            if tool in called_tools:
                failures.append(f"forbidden tool {tool!r} was called")
        for event_type in case.expected_trace_events:
            if event_type not in event_types:
                failures.append(f"expected trace event {event_type!r} was not recorded")

        if case.max_latency_ms is not None and duration_ms > case.max_latency_ms:
            failures.append(
                f"latency {duration_ms:.3f}ms exceeded {case.max_latency_ms:.3f}ms"
            )
        if case.require_recovery and not (success and summary.retry_count > 0):
            failures.append("expected a successful recovery after at least one retry")

        for check in case.checks:
            try:
                outcome = check(result, trace)
            except Exception as exc:
                failures.append(f"custom check raised: {exc}")
                continue
            if outcome is False:
                failures.append("custom check returned False")
            elif isinstance(outcome, str) and outcome:
                failures.append(outcome)
            elif isinstance(outcome, tuple) and outcome and not outcome[0]:
                failures.append(str(outcome[1] if len(outcome) > 1 else "custom check failed"))

        return EvaluationCaseResult(
            name=case.name,
            passed=not failures,
            content=content,
            error=error,
            failures=failures,
            duration_ms=duration_ms,
            trace=trace,
            summary=summary,
            metadata=dict(case.metadata),
        )
