#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Lightweight workflow orchestration for LightAgent.
"""

from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from .result import RunResult
from .tracing import TraceRecorder


FLOW_PENDING = "pending"
FLOW_RUNNING = "running"
FLOW_SUCCESS = "success"
FLOW_FAILED = "failed"
FLOW_SKIPPED = "skipped"
FLOW_WAITING_APPROVAL = "waiting_approval"


@dataclass
class LightFlowStep:
    """A single agent-backed workflow step."""

    name: str
    agent: Any
    depends_on: list[str] = field(default_factory=list)
    query: str | Callable[..., str] | None = None
    tools: list[Any] | None = None
    max_retry: int = 1
    timeout: float | None = None
    fallback_agent: Any | None = None
    cancel_if: Callable[[dict[str, Any]], bool] | None = None
    requires_approval: bool = False
    approval_handler: Callable[..., Any] | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class LightFlowStepResult:
    """Result captured for one LightFlow step."""

    name: str
    content: str
    error: str | None = None
    attempts: int = 1
    trace: list[dict[str, Any]] = field(default_factory=list)
    status: str = FLOW_SUCCESS
    started_at: float | None = None
    ended_at: float | None = None
    duration_ms: float | None = None
    input_summary: str | None = None
    output_summary: str | None = None
    retry_count: int = 0
    used_fallback: bool = False

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
    run_id: str | None = None
    status: str = FLOW_SUCCESS

    @property
    def success(self) -> bool:
        return self.error is None and self.status == FLOW_SUCCESS

    def __str__(self) -> str:
        return self.content


class JsonLightFlowStore:
    """Small JSON-file run store for LightFlow checkpoints."""

    def __init__(self, directory: str | Path):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def save_run(self, run_id: str, record: dict[str, Any]) -> None:
        path = self._path(run_id)
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    def load_run(self, run_id: str) -> dict[str, Any] | None:
        path = self._path(run_id)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def list_runs(self) -> list[dict[str, Any]]:
        records = []
        for path in sorted(self.directory.glob("*.json")):
            records.append(json.loads(path.read_text(encoding="utf-8")))
        return records

    def _path(self, run_id: str) -> Path:
        safe_run_id = "".join(char for char in str(run_id) if char.isalnum() or char in ("-", "_"))
        if not safe_run_id:
            raise ValueError("run_id must contain at least one safe character")
        return self.directory / f"{safe_run_id}.json"


class LightFlow:
    """Deterministic workflow runner for LightAgent instances."""

    def __init__(self, *, store: JsonLightFlowStore | None = None):
        self._steps: list[LightFlowStep] = []
        self.store = store
        self._records: dict[str, dict[str, Any]] = {}
        self._cancelled = False

    def step(
            self,
            name: str,
            *,
            agent: Any,
            depends_on: list[str] | None = None,
            query: str | Callable[..., str] | None = None,
            tools: list[Any] | None = None,
            max_retry: int = 1,
            timeout: float | None = None,
            fallback_agent: Any | None = None,
            cancel_if: Callable[[dict[str, Any]], bool] | None = None,
            requires_approval: bool = False,
            approval_handler: Callable[..., Any] | None = None,
            metadata: dict[str, Any] | None = None,
    ) -> "LightFlow":
        """Register a workflow step and return the flow for chaining."""
        if not name:
            raise ValueError("step name must not be empty")
        if any(existing.name == name for existing in self._steps):
            raise ValueError(f"step `{name}` is already registered")
        if not hasattr(agent, "run"):
            raise ValueError(f"step `{name}` agent must provide a run() method")
        if fallback_agent is not None and not hasattr(fallback_agent, "run"):
            raise ValueError(f"step `{name}` fallback_agent must provide a run() method")
        if max_retry < 1:
            raise ValueError("max_retry must be at least 1")
        if timeout is not None and timeout <= 0:
            raise ValueError("timeout must be greater than 0")

        self._steps.append(
            LightFlowStep(
                name=name,
                agent=agent,
                depends_on=depends_on or [],
                query=query,
                tools=tools,
                max_retry=max_retry,
                timeout=timeout,
                fallback_agent=fallback_agent,
                cancel_if=cancel_if,
                requires_approval=requires_approval,
                approval_handler=approval_handler,
                metadata=metadata,
            )
        )
        return self

    def validate(self, *, strict: bool = False) -> dict[str, list[str]]:
        """Validate DAG errors and optionally warn on isolated steps."""
        errors: list[str] = []
        warnings: list[str] = []
        steps_by_name = {step.name: step for step in self._steps}

        if len(steps_by_name) != len(self._steps):
            errors.append("step names must be unique")

        referenced = {dependency for step in self._steps for dependency in step.depends_on}
        for step in self._steps:
            for dependency in step.depends_on:
                if dependency not in steps_by_name:
                    errors.append(f"step `{step.name}` depends on unknown step `{dependency}`")
            if not step.depends_on and step.name not in referenced and len(self._steps) > 1:
                warnings.append(f"step `{step.name}` is isolated")

        temporary: set[str] = set()
        permanent: set[str] = set()

        def visit(step: LightFlowStep):
            if step.name in permanent:
                return
            if step.name in temporary:
                errors.append(f"cycle detected at step `{step.name}`")
                return
            temporary.add(step.name)
            for dependency in step.depends_on:
                if dependency in steps_by_name:
                    visit(steps_by_name[dependency])
            temporary.remove(step.name)
            permanent.add(step.name)

        for step in self._steps:
            visit(step)

        if strict and warnings:
            errors.extend(warnings)
        return {"errors": errors, "warnings": warnings}

    def cancel(self) -> None:
        """Request cancellation before the next step starts."""
        self._cancelled = True

    def run(
            self,
            query: str,
            *,
            user_id: str = "default_user",
            trace: bool = False,
            result_format: str = "object",
            run_id: str | None = None,
    ) -> LightFlowResult | str | dict[str, Any]:
        """Run all registered steps once their dependencies are satisfied."""
        if result_format not in ("object", "str", "dict"):
            raise ValueError("result_format must be one of: object, str, dict")
        ordered_steps = self._ordered_steps()
        return self._execute(
            query=query,
            ordered_steps=ordered_steps,
            user_id=user_id,
            trace=trace,
            result_format=result_format,
            run_id=run_id or uuid4().hex,
        )

    def resume(
            self,
            run_id: str,
            *,
            user_id: str = "default_user",
            trace: bool = False,
            result_format: str = "object",
    ) -> LightFlowResult | str | dict[str, Any]:
        """Resume a failed or incomplete run from the last checkpoint."""
        record = self.get_run(run_id)
        if not record:
            raise ValueError(f"run `{run_id}` not found")
        completed = {
            step["name"]: self._step_result_from_dict(step)
            for step in record.get("steps", [])
            if step.get("status") == FLOW_SUCCESS
        }
        ordered_steps = [step for step in self._ordered_steps() if step.name not in completed]
        return self._execute(
            query=record.get("query", ""),
            ordered_steps=ordered_steps,
            user_id=user_id,
            trace=trace,
            result_format=result_format,
            run_id=run_id,
            initial_completed=completed,
        )

    def rerun_step(
            self,
            run_id: str,
            step_name: str,
            *,
            user_id: str = "default_user",
            trace: bool = False,
            result_format: str = "object",
    ) -> LightFlowResult | str | dict[str, Any]:
        """Rerun one step and all downstream steps from a checkpoint."""
        record = self.get_run(run_id)
        if not record:
            raise ValueError(f"run `{run_id}` not found")
        steps_by_name = {step.name: step for step in self._ordered_steps()}
        if step_name not in steps_by_name:
            raise ValueError(f"step `{step_name}` not found")

        downstream = self._downstream_steps(step_name)
        completed = {
            step["name"]: self._step_result_from_dict(step)
            for step in record.get("steps", [])
            if step.get("status") == FLOW_SUCCESS and step["name"] not in downstream
        }
        ordered_steps = [step for step in self._ordered_steps() if step.name in downstream]
        return self._execute(
            query=record.get("query", ""),
            ordered_steps=ordered_steps,
            user_id=user_id,
            trace=trace,
            result_format=result_format,
            run_id=run_id,
            initial_completed=completed,
        )

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        """Return a run record from memory or the configured store."""
        if run_id in self._records:
            return self._records[run_id]
        if self.store:
            return self.store.load_run(run_id)
        return None

    def list_runs(self) -> list[dict[str, Any]]:
        """Return known run records for inspection or UI display."""
        if self.store:
            return self.store.list_runs()
        return list(self._records.values())

    def _execute(
            self,
            *,
            query: str,
            ordered_steps: list[LightFlowStep],
            user_id: str,
            trace: bool,
            result_format: str,
            run_id: str,
            initial_completed: dict[str, LightFlowStepResult] | None = None,
    ) -> LightFlowResult | str | dict[str, Any]:
        trace_id = uuid4().hex
        recorder = TraceRecorder(enabled=trace, trace_id=trace_id)
        all_steps = self._ordered_steps()
        recorder.record("flow_start", {"query": query, "steps": [step.name for step in all_steps], "run_id": run_id})

        context: dict[str, Any] = {
            "input": query,
            "steps": {},
            "outputs": {},
        }
        step_results: list[LightFlowStepResult] = []
        for completed in (initial_completed or {}).values():
            context["steps"][completed.name] = completed
            context["outputs"][completed.name] = completed.content
            step_results.append(completed)
        self._checkpoint(run_id, query, status=FLOW_RUNNING, steps=step_results, error=None, all_steps=all_steps)

        final_content = step_results[-1].content if step_results else ""
        status = FLOW_SUCCESS
        error = None

        for step in ordered_steps:
            if self._cancelled or (step.cancel_if and step.cancel_if(context)):
                result = self._skipped_result(step, "cancelled before execution")
                step_results.append(result)
                self._checkpoint(run_id, query, status=FLOW_SKIPPED, steps=step_results, error=result.error, all_steps=all_steps)
                continue

            step_query = self._build_step_query(step, query, context)
            approved, approval_reason = self._check_approval(step, context)
            if not approved:
                result = self._skipped_result(step, approval_reason or "approval rejected", status=FLOW_WAITING_APPROVAL)
                step_results.append(result)
                self._checkpoint(
                    run_id,
                    query,
                    status=FLOW_WAITING_APPROVAL,
                    steps=step_results,
                    error=result.error,
                    all_steps=all_steps,
                )
                status = FLOW_WAITING_APPROVAL
                error = result.error
                break

            recorder.record("step_start", {
                "step": step.name,
                "agent": getattr(step.agent, "name", None),
                "depends_on": step.depends_on,
                "status": FLOW_RUNNING,
                "input_summary": self._summarize(step_query),
            })

            step_result = self._run_step(step, step_query, user_id=user_id, trace=trace)
            step_results.append(step_result)
            context["steps"][step.name] = step_result
            context["outputs"][step.name] = step_result.content
            final_content = step_result.content

            recorder.record("step_end", {
                "step": step.name,
                "status": step_result.status,
                "success": step_result.error is None,
                "error": step_result.error,
                "attempts": step_result.attempts,
                "retry_count": step_result.retry_count,
                "duration_ms": step_result.duration_ms,
                "input_summary": step_result.input_summary,
                "output_summary": step_result.output_summary,
                "used_fallback": step_result.used_fallback,
            })

            self._checkpoint(
                run_id,
                query,
                status=step_result.status,
                steps=step_results,
                error=step_result.error,
                all_steps=all_steps,
            )
            if step_result.error:
                status = FLOW_FAILED
                error = step_result.error
                step_results.extend(self._remaining_skipped_results(step, all_steps, step_results))
                self._checkpoint(run_id, query, status=status, steps=step_results, error=error, all_steps=all_steps)
                recorder.record("flow_end", {"success": False, "error": error, "status": status, "run_id": run_id})
                return self._format_result(
                    LightFlowResult(
                        content=step_result.content,
                        steps=step_results,
                        trace_id=trace_id,
                        trace=recorder.to_list(),
                        error=error,
                        run_id=run_id,
                        status=status,
                    ),
                    result_format,
                )

        recorder.record("flow_end", {"success": error is None, "status": status, "run_id": run_id})
        return self._format_result(
            LightFlowResult(
                content=final_content,
                steps=step_results,
                trace_id=trace_id,
                trace=recorder.to_list(),
                error=error,
                run_id=run_id,
                status=status,
            ),
            result_format,
        )

    def _run_step(self, step: LightFlowStep, query: str, *, user_id: str, trace: bool) -> LightFlowStepResult:
        started = time.perf_counter()
        last_result: LightFlowStepResult | None = None
        for attempt in range(1, step.max_retry + 1):
            raw_result, timed_out = self._call_agent(step.agent, step, query, user_id=user_id, trace=trace)
            content, error, step_trace = self._normalize_agent_result(raw_result)
            if timed_out:
                error = f"step `{step.name}` timed out after {step.timeout} seconds"
                content = f"[LA-FLOW-TIMEOUT] {error}"
            ended = time.perf_counter()
            last_result = LightFlowStepResult(
                name=step.name,
                content=content,
                error=error,
                attempts=attempt,
                trace=step_trace,
                status=FLOW_FAILED if error else FLOW_SUCCESS,
                started_at=started,
                ended_at=ended,
                duration_ms=round((ended - started) * 1000, 3),
                input_summary=self._summarize(query),
                output_summary=self._summarize(content),
                retry_count=attempt - 1,
            )
            if error is None:
                return last_result

        if last_result and last_result.error and step.fallback_agent is not None:
            fallback_result, timed_out = self._call_agent(step.fallback_agent, step, query, user_id=user_id, trace=trace)
            content, error, step_trace = self._normalize_agent_result(fallback_result)
            if timed_out:
                error = f"fallback for step `{step.name}` timed out after {step.timeout} seconds"
                content = f"[LA-FLOW-TIMEOUT] {error}"
            ended = time.perf_counter()
            return LightFlowStepResult(
                name=step.name,
                content=content,
                error=error,
                attempts=last_result.attempts + 1,
                trace=step_trace,
                status=FLOW_FAILED if error else FLOW_SUCCESS,
                started_at=started,
                ended_at=ended,
                duration_ms=round((ended - started) * 1000, 3),
                input_summary=self._summarize(query),
                output_summary=self._summarize(content),
                retry_count=last_result.attempts - 1,
                used_fallback=True,
            )
        return last_result or LightFlowStepResult(name=step.name, content="", error="step did not run", status=FLOW_FAILED)

    def _call_agent(
            self,
            agent: Any,
            step: LightFlowStep,
            query: str,
            *,
            user_id: str,
            trace: bool,
    ) -> tuple[Any, bool]:
        kwargs = {
            "tools": step.tools,
            "stream": False,
            "user_id": user_id,
            "metadata": step.metadata,
            "result_format": "object",
            "trace": trace,
        }
        if step.timeout is None:
            return agent.run(query, **kwargs), False
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(agent.run, query, **kwargs)
            try:
                return future.result(timeout=step.timeout), False
            except TimeoutError:
                future.cancel()
                return None, True

    def _ordered_steps(self) -> list[LightFlowStep]:
        validation = self.validate()
        if validation["errors"]:
            raise ValueError(validation["errors"][0])
        steps_by_name = {step.name: step for step in self._steps}
        ordered: list[LightFlowStep] = []
        permanent: set[str] = set()

        def visit(step: LightFlowStep):
            if step.name in permanent:
                return
            for dependency in step.depends_on:
                visit(steps_by_name[dependency])
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
                "steps": [LightFlow._step_result_to_dict(step) for step in result.steps],
                "trace_id": result.trace_id,
                "trace": result.trace,
                "error": result.error,
                "success": result.success,
                "run_id": result.run_id,
                "status": result.status,
            }
        return result

    def _checkpoint(
            self,
            run_id: str,
            query: str,
            *,
            status: str,
            steps: list[LightFlowStepResult],
            error: str | None,
            all_steps: list[LightFlowStep] | None = None,
    ) -> None:
        record_steps = list(steps)
        if all_steps:
            seen = {step.name for step in record_steps}
            record_steps.extend(
                LightFlowStepResult(name=step.name, content="", attempts=0, status=FLOW_PENDING)
                for step in all_steps
                if step.name not in seen
            )
        record = {
            "run_id": run_id,
            "query": query,
            "status": status,
            "error": error,
            "steps": [self._step_result_to_dict(step) for step in record_steps],
            "updated_at": time.time(),
        }
        self._records[run_id] = record
        if self.store:
            self.store.save_run(run_id, record)

    def _remaining_skipped_results(
            self,
            failed_step: LightFlowStep,
            all_steps: list[LightFlowStep],
            step_results: list[LightFlowStepResult],
    ) -> list[LightFlowStepResult]:
        seen = {result.name for result in step_results}
        skipped = []
        for step in all_steps:
            if step.name in seen:
                continue
            if failed_step.name in step.depends_on or any(dep in seen for dep in step.depends_on):
                skipped.append(self._skipped_result(step, f"skipped after `{failed_step.name}` failed"))
        return skipped

    @staticmethod
    def _skipped_result(step: LightFlowStep, reason: str, *, status: str = FLOW_SKIPPED) -> LightFlowStepResult:
        return LightFlowStepResult(
            name=step.name,
            content="",
            error=reason,
            attempts=0,
            status=status,
            retry_count=0,
        )

    @staticmethod
    def _check_approval(step: LightFlowStep, context: dict[str, Any]) -> tuple[bool, str | None]:
        if not step.requires_approval:
            return True, None
        if step.approval_handler is None:
            return False, "approval required"
        raw = step.approval_handler(step, context)
        if raw is True or raw is None:
            return True, None
        if raw is False:
            return False, "approval rejected"
        if isinstance(raw, str):
            return False, raw
        if isinstance(raw, dict):
            return bool(raw.get("approved", raw.get("allowed", False))), raw.get("reason")
        return bool(raw), None

    def _downstream_steps(self, step_name: str) -> set[str]:
        downstream = {step_name}
        changed = True
        while changed:
            changed = False
            for step in self._steps:
                if step.name not in downstream and any(dep in downstream for dep in step.depends_on):
                    downstream.add(step.name)
                    changed = True
        return downstream

    @staticmethod
    def _step_result_to_dict(step: LightFlowStepResult) -> dict[str, Any]:
        return asdict(step)

    @staticmethod
    def _step_result_from_dict(data: dict[str, Any]) -> LightFlowStepResult:
        fields = LightFlowStepResult.__dataclass_fields__
        return LightFlowStepResult(**{key: value for key, value in data.items() if key in fields})

    @staticmethod
    def _summarize(value: Any, *, limit: int = 240) -> str:
        text = "" if value is None else str(value)
        return text if len(text) <= limit else f"{text[:limit]}..."
