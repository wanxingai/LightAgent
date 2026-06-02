#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Lightweight workflow orchestration for LightAgent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable
from uuid import uuid4

from .result import RunResult
from .tracing import TraceRecorder


@dataclass
class LightFlowStep:
    """A single agent-backed workflow step."""

    name: str
    agent: Any
    depends_on: list[str] = field(default_factory=list)
    query: str | Callable[..., str] | None = None
    tools: list[Any] | None = None
    max_retry: int = 1
    metadata: dict[str, Any] | None = None


@dataclass
class LightFlowStepResult:
    """Result captured for one LightFlow step."""

    name: str
    content: str
    error: str | None = None
    attempts: int = 1
    trace: list[dict[str, Any]] = field(default_factory=list)

    def __str__(self) -> str:
        return self.content


@dataclass
class LightFlowResult:
    """Structured LightFlow run result."""

    content: str
    steps: list[LightFlowStepResult] = field(default_factory=list)
    trace_id: str | None = None
    trace: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None

    @property
    def success(self) -> bool:
        return self.error is None

    def __str__(self) -> str:
        return self.content


class LightFlow:
    """Minimal deterministic workflow runner for LightAgent instances."""

    def __init__(self):
        self._steps: list[LightFlowStep] = []

    def step(
            self,
            name: str,
            *,
            agent: Any,
            depends_on: list[str] | None = None,
            query: str | Callable[..., str] | None = None,
            tools: list[Any] | None = None,
            max_retry: int = 1,
            metadata: dict[str, Any] | None = None,
    ) -> "LightFlow":
        """Register a workflow step and return the flow for chaining."""
        if not name:
            raise ValueError("step name must not be empty")
        if any(existing.name == name for existing in self._steps):
            raise ValueError(f"step `{name}` is already registered")
        if not hasattr(agent, "run"):
            raise ValueError(f"step `{name}` agent must provide a run() method")
        if max_retry < 1:
            raise ValueError("max_retry must be at least 1")

        self._steps.append(
            LightFlowStep(
                name=name,
                agent=agent,
                depends_on=depends_on or [],
                query=query,
                tools=tools,
                max_retry=max_retry,
                metadata=metadata,
            )
        )
        return self

    def run(
            self,
            query: str,
            *,
            user_id: str = "default_user",
            trace: bool = False,
            result_format: str = "object",
    ) -> LightFlowResult | str | dict[str, Any]:
        """Run all registered steps once their dependencies are satisfied."""
        if result_format not in ("object", "str", "dict"):
            raise ValueError("result_format must be one of: object, str, dict")
        ordered_steps = self._ordered_steps()
        trace_id = uuid4().hex
        recorder = TraceRecorder(enabled=trace, trace_id=trace_id)
        recorder.record("flow_start", {"query": query, "steps": [step.name for step in ordered_steps]})

        context: dict[str, Any] = {
            "input": query,
            "steps": {},
            "outputs": {},
        }
        step_results: list[LightFlowStepResult] = []
        final_content = ""

        for step in ordered_steps:
            step_query = self._build_step_query(step, query, context)
            recorder.record("step_start", {
                "step": step.name,
                "agent": getattr(step.agent, "name", None),
                "depends_on": step.depends_on,
            })

            step_result = self._run_step(step, step_query, user_id=user_id, trace=trace)
            step_results.append(step_result)
            context["steps"][step.name] = step_result
            context["outputs"][step.name] = step_result.content
            final_content = step_result.content

            recorder.record("step_end", {
                "step": step.name,
                "success": step_result.error is None,
                "error": step_result.error,
                "attempts": step_result.attempts,
            })

            if step_result.error:
                recorder.record("flow_end", {"success": False, "error": step_result.error})
                return self._format_result(
                    LightFlowResult(
                        content=step_result.content,
                        steps=step_results,
                        trace_id=trace_id,
                        trace=recorder.to_list(),
                        error=step_result.error,
                    ),
                    result_format,
                )

        recorder.record("flow_end", {"success": True})
        return self._format_result(
            LightFlowResult(
                content=final_content,
                steps=step_results,
                trace_id=trace_id,
                trace=recorder.to_list(),
            ),
            result_format,
        )

    def _run_step(self, step: LightFlowStep, query: str, *, user_id: str, trace: bool) -> LightFlowStepResult:
        last_result: LightFlowStepResult | None = None
        for attempt in range(1, step.max_retry + 1):
            raw_result = step.agent.run(
                query,
                tools=step.tools,
                stream=False,
                user_id=user_id,
                metadata=step.metadata,
                result_format="object",
                trace=trace,
            )
            content, error, step_trace = self._normalize_agent_result(raw_result)
            last_result = LightFlowStepResult(
                name=step.name,
                content=content,
                error=error,
                attempts=attempt,
                trace=step_trace,
            )
            if error is None:
                return last_result
        return last_result or LightFlowStepResult(name=step.name, content="", error="step did not run")

    def _ordered_steps(self) -> list[LightFlowStep]:
        steps_by_name = {step.name: step for step in self._steps}
        if len(steps_by_name) != len(self._steps):
            raise ValueError("step names must be unique")

        ordered: list[LightFlowStep] = []
        temporary: set[str] = set()
        permanent: set[str] = set()

        def visit(step: LightFlowStep):
            if step.name in permanent:
                return
            if step.name in temporary:
                raise ValueError(f"cycle detected at step `{step.name}`")
            temporary.add(step.name)
            for dependency in step.depends_on:
                if dependency not in steps_by_name:
                    raise ValueError(f"step `{step.name}` depends on unknown step `{dependency}`")
                visit(steps_by_name[dependency])
            temporary.remove(step.name)
            permanent.add(step.name)
            ordered.append(step)

        for step in self._steps:
            visit(step)
        return ordered

    @staticmethod
    def _build_step_query(step: LightFlowStep, original_query: str, context: dict[str, Any]) -> str:
        if callable(step.query):
            try:
                return str(step.query(context))
            except TypeError:
                return str(step.query(original_query, context))
        if step.query is not None:
            return str(step.query)
        if not step.depends_on:
            return original_query

        dependency_outputs = "\n".join(
            f"{name}: {context['outputs'][name]}" for name in step.depends_on
        )
        return f"{original_query}\n\nPrevious step outputs:\n{dependency_outputs}"

    @staticmethod
    def _normalize_agent_result(result: Any) -> tuple[str, str | None, list[dict[str, Any]]]:
        if isinstance(result, RunResult):
            return result.content, result.error, result.trace
        text = "" if result is None else str(result)
        error = text if text.startswith("[LA-") else None
        return text, error, []

    @staticmethod
    def _format_result(result: LightFlowResult, result_format: str) -> LightFlowResult | str | dict[str, Any]:
        if result_format == "str":
            return result.content
        if result_format == "dict":
            return {
                "content": result.content,
                "steps": [
                    {
                        "name": step.name,
                        "content": step.content,
                        "error": step.error,
                        "attempts": step.attempts,
                        "trace": step.trace,
                    }
                    for step in result.steps
                ],
                "trace_id": result.trace_id,
                "trace": result.trace,
                "error": result.error,
                "success": result.success,
            }
        return result
