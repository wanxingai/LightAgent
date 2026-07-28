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
from .hooks import HOOK_BLOCK, HookContext, HookDecision, HookManager
from .review import (
    APPROVAL_EDIT,
    APPROVAL_PENDING,
    APPROVAL_REJECT,
    APPROVAL_RESPOND,
    ApprovalDecision,
    ApprovalRequest,
)
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
    approval_request_id: str | None = None
    approval_decision: str | None = None

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

    def __init__(self, *, store: JsonLightFlowStore | None = None, hooks: list[Callable[..., Any] | Any] | None = None):
        self._steps: list[LightFlowStep] = []
        self.store = store
        self.hooks = HookManager(hooks)
        self._records: dict[str, dict[str, Any]] = {}
        self._approval_decisions: dict[tuple[str, str], ApprovalDecision] = {}
        self._approval_request_ids: dict[tuple[str, str], str] = {}
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
            parent_trace_id: str | None = None,
            run_group_id: str | None = None,
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
            parent_trace_id=parent_trace_id,
            run_group_id=run_group_id,
        )

    def resume(
            self,
            run_id: str,
            *,
            user_id: str = "default_user",
            trace: bool = False,
            result_format: str = "object",
            parent_trace_id: str | None = None,
            run_group_id: str | None = None,
    ) -> LightFlowResult | str | dict[str, Any]:
        """Resume a failed or incomplete run from the last checkpoint."""
        record = self.get_run(run_id)
        if not record:
            raise ValueError(f"run `{run_id}` not found")
        self._restore_approval_decisions(run_id, record)
        self._run_flow_hook("on_resume", {"run_id": run_id, "record": record})
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
            parent_trace_id=parent_trace_id,
            run_group_id=run_group_id,
        )

    def rerun_step(
            self,
            run_id: str,
            step_name: str,
            *,
            user_id: str = "default_user",
            trace: bool = False,
            result_format: str = "object",
            parent_trace_id: str | None = None,
            run_group_id: str | None = None,
    ) -> LightFlowResult | str | dict[str, Any]:
        """Rerun one step and all downstream steps from a checkpoint."""
        record = self.get_run(run_id)
        if not record:
            raise ValueError(f"run `{run_id}` not found")
        self._restore_approval_decisions(run_id, record)
        steps_by_name = {step.name: step for step in self._ordered_steps()}
        if step_name not in steps_by_name:
            raise ValueError(f"step `{step_name}` not found")

        self._run_flow_hook("on_rerun", {"run_id": run_id, "step_name": step_name, "record": record})
        downstream = self._downstream_steps(step_name)
        for approval_step in downstream:
            self._approval_decisions.pop((run_id, approval_step), None)
            self._approval_request_ids.pop((run_id, approval_step), None)
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
            parent_trace_id=parent_trace_id,
            run_group_id=run_group_id,
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

    def approve(
            self,
            run_id: str,
            step_name: str,
            decision: ApprovalDecision | bool | str | dict[str, Any] = True,
    ) -> ApprovalDecision:
        """Persist a human decision so a waiting flow can resume safely."""
        record = self.get_run(run_id)
        if not record:
            raise ValueError(f"run `{run_id}` not found")
        step_record = next(
            (step for step in record.get("steps", []) if step.get("name") == step_name),
            None,
        )
        if step_record is None:
            raise ValueError(f"step `{step_name}` not found in run `{run_id}`")
        if step_record.get("status") != FLOW_WAITING_APPROVAL:
            raise ValueError(f"step `{step_name}` is not waiting for approval")
        request_id = step_record.get("approval_request_id")
        if not request_id:
            raise ValueError(f"step `{step_name}` is not waiting for approval")
        normalized = self._coerce_approval_decision(decision, request_id=request_id)
        self._approval_request_ids[(run_id, step_name)] = request_id
        self._approval_decisions[(run_id, step_name)] = normalized
        approvals = dict(record.get("approvals") or {})
        approvals[step_name] = normalized.to_dict()
        record["approvals"] = approvals
        step_record["approval_decision"] = normalized.action
        record["updated_at"] = time.time()
        self._records[run_id] = record
        if self.store:
            self.store.save_run(run_id, record)
        return normalized

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
            parent_trace_id: str | None = None,
            run_group_id: str | None = None,
    ) -> LightFlowResult | str | dict[str, Any]:
        trace_id = uuid4().hex
        run_group = run_group_id or run_id
        recorder = TraceRecorder(enabled=trace, trace_id=trace_id, parent_trace_id=parent_trace_id, run_group_id=run_group)
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
            step_hook = self._run_flow_hook(
                "before_flow_step",
                {"query": step_query, "context": context, "run_id": run_id},
                trace_id=trace_id,
                parent_trace_id=parent_trace_id,
                run_group_id=run_group,
                user_id=user_id,
                flow_id=run_id,
                step_name=step.name,
                recorder=recorder,
            )
            if step_hook.action == HOOK_BLOCK:
                result = self._skipped_result(step, step_hook.reason or "blocked by before_flow_step hook")
                step_results.append(result)
                self._checkpoint(run_id, query, status=FLOW_SKIPPED, steps=step_results, error=result.error, all_steps=all_steps)
                continue
            if step_hook.payload and "query" in step_hook.payload:
                step_query = str(step_hook.payload["query"])

            approval_request = ApprovalRequest(
                action="flow_step",
                request_id=self._approval_request_ids.get(
                    (run_id, step.name),
                    uuid4().hex,
                ),
                run_id=run_id,
                trace_id=trace_id,
                action_name=step.name,
                arguments={"query": step_query},
                source_agent=getattr(step.agent, "name", None),
                reviewer_metadata={"user_id": user_id},
                metadata={"step": step.name, "depends_on": list(step.depends_on)},
                allowed_decisions=("approve", "reject", "edit", "respond"),
            )
            approval_decision = self._check_approval(
                step,
                context,
                approval_request,
                run_id=run_id,
            )
            if step.requires_approval:
                recorder.record(f"approval_{approval_decision.action}", {
                    "request_id": approval_request.request_id,
                    "run_id": run_id,
                    "step": step.name,
                    "reason": approval_decision.reason,
                    "reviewer_id": approval_decision.reviewer_id,
                })
            if approval_decision.action == APPROVAL_PENDING:
                self._approval_request_ids[(run_id, step.name)] = approval_request.request_id
                self._run_flow_hook(
                    "on_approval_required",
                    {
                        "run_id": run_id,
                        "step": step.name,
                        "reason": approval_decision.reason,
                        "request": approval_request.to_dict(),
                    },
                    trace_id=trace_id,
                    parent_trace_id=parent_trace_id,
                    run_group_id=run_group,
                    user_id=user_id,
                    flow_id=run_id,
                    step_name=step.name,
                    recorder=recorder,
                )
                result = self._skipped_result(
                    step,
                    approval_decision.reason or "approval required",
                    status=FLOW_WAITING_APPROVAL,
                )
                result.approval_request_id = approval_request.request_id
                result.approval_decision = approval_decision.action
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
            if approval_decision.action == APPROVAL_REJECT:
                result = self._skipped_result(
                    step,
                    approval_decision.reason or "approval rejected",
                )
                result.approval_request_id = approval_request.request_id
                result.approval_decision = approval_decision.action
                step_results.append(result)
                status = FLOW_FAILED
                error = result.error
                self._checkpoint(
                    run_id,
                    query,
                    status=status,
                    steps=step_results,
                    error=error,
                    all_steps=all_steps,
                )
                break
            if approval_decision.action == APPROVAL_EDIT:
                step_query = str(
                    (approval_decision.arguments or {}).get("query", step_query)
                )
            if approval_decision.action == APPROVAL_RESPOND:
                content = approval_decision.response or ""
                now = time.perf_counter()
                result = LightFlowStepResult(
                    name=step.name,
                    content=content,
                    status=FLOW_SUCCESS,
                    started_at=now,
                    ended_at=now,
                    duration_ms=0.0,
                    input_summary=self._summarize(step_query),
                    output_summary=self._summarize(content),
                    approval_request_id=approval_request.request_id,
                    approval_decision=approval_decision.action,
                )
                step_results.append(result)
                context["steps"][step.name] = result
                context["outputs"][step.name] = result.content
                final_content = result.content
                recorder.record("step_end", {
                    "step": step.name,
                    "status": FLOW_SUCCESS,
                    "success": True,
                    "duration_ms": 0.0,
                    "human_response": True,
                })
                self._checkpoint(
                    run_id,
                    query,
                    status=FLOW_SUCCESS,
                    steps=step_results,
                    error=None,
                    all_steps=all_steps,
                )
                continue

            recorder.record("step_start", {
                "step": step.name,
                "agent": getattr(step.agent, "name", None),
                "depends_on": step.depends_on,
                "status": FLOW_RUNNING,
                "input_summary": self._summarize(step_query),
            })

            step_result = self._run_step(
                step,
                step_query,
                user_id=user_id,
                trace=trace,
                parent_trace_id=trace_id,
                run_group_id=run_group,
            )
            if step.requires_approval:
                step_result.approval_request_id = approval_request.request_id
                step_result.approval_decision = approval_decision.action
            step_results.append(step_result)
            self._run_flow_hook(
                "after_flow_step",
                {"run_id": run_id, "step_result": self._step_result_to_dict(step_result)},
                trace_id=trace_id,
                parent_trace_id=parent_trace_id,
                run_group_id=run_group,
                user_id=user_id,
                flow_id=run_id,
                step_name=step.name,
                recorder=recorder,
            )
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

    def _run_step(
            self,
            step: LightFlowStep,
            query: str,
            *,
            user_id: str,
            trace: bool,
            parent_trace_id: str | None,
            run_group_id: str | None,
    ) -> LightFlowStepResult:
        started = time.perf_counter()
        last_result: LightFlowStepResult | None = None
        for attempt in range(1, step.max_retry + 1):
            raw_result, timed_out = self._call_agent(
                step.agent,
                step,
                query,
                user_id=user_id,
                trace=trace,
                parent_trace_id=parent_trace_id,
                run_group_id=run_group_id,
            )
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
            fallback_result, timed_out = self._call_agent(
                step.fallback_agent,
                step,
                query,
                user_id=user_id,
                trace=trace,
                parent_trace_id=parent_trace_id,
                run_group_id=run_group_id,
            )
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
            parent_trace_id: str | None,
            run_group_id: str | None,
    ) -> tuple[Any, bool]:
        kwargs = {
            "tools": step.tools,
            "stream": False,
            "user_id": user_id,
            "metadata": step.metadata,
            "result_format": "object",
            "trace": trace,
            "parent_trace_id": parent_trace_id,
            "run_group_id": run_group_id,
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

    def _run_flow_hook(
            self,
            phase: str,
            payload: dict[str, Any],
            *,
            trace_id: str | None = None,
            parent_trace_id: str | None = None,
            run_group_id: str | None = None,
            user_id: str | None = None,
            flow_id: str | None = None,
            step_name: str | None = None,
            recorder: TraceRecorder | None = None,
    ) -> HookDecision:
        context = HookContext(
            phase=phase,
            payload=payload,
            trace_id=trace_id,
            parent_trace_id=parent_trace_id,
            run_group_id=run_group_id,
            user_id=user_id,
            flow_id=flow_id,
            step_name=step_name,
        )
        decision = self.hooks.run(context)
        if recorder:
            for event in decision.metadata.get("hook_events", []) if decision.metadata else []:
                recorder.record("hook_decision", event)
            for event in decision.metadata.get("review_events", []) if decision.metadata else []:
                event_data = dict(event)
                event_type = str(event_data.pop("type", "approval_decision"))
                recorder.record(event_type, event_data)
            if decision.action == HOOK_BLOCK:
                recorder.record("hook_block", {"phase": phase, "reason": decision.reason, "step": step_name})
        return decision

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
            "approvals": {
                step_name: decision.to_dict()
                for (decision_run_id, step_name), decision in self._approval_decisions.items()
                if decision_run_id == run_id
            },
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

    def _check_approval(
            self,
            step: LightFlowStep,
            context: dict[str, Any],
            request: ApprovalRequest,
            *,
            run_id: str,
    ) -> ApprovalDecision:
        if not step.requires_approval:
            return ApprovalDecision.approve(request_id=request.request_id)
        persisted = self._approval_decisions.get((run_id, step.name))
        if persisted is not None:
            persisted.request_id = request.request_id
            return persisted
        if step.approval_handler is None:
            return ApprovalDecision.pending("approval required", request_id=request.request_id)
        approval_context = {**context, "approval_request": request}
        try:
            raw = step.approval_handler(step, approval_context)
        except Exception as exc:
            return ApprovalDecision.reject(
                f"approval handler failed: {exc}",
                request_id=request.request_id,
            )
        if raw is False:
            return ApprovalDecision.pending(
                "approval rejected",
                request_id=request.request_id,
            )
        if isinstance(raw, str):
            return ApprovalDecision.pending(raw, request_id=request.request_id)
        if isinstance(raw, dict) and "action" not in raw:
            approved = raw.get("approved", raw.get("allowed", False))
            if not approved:
                return ApprovalDecision.pending(
                    raw.get("reason") or "approval required",
                    request_id=request.request_id,
                )
        return self._coerce_approval_decision(raw, request_id=request.request_id)

    @staticmethod
    def _coerce_approval_decision(
            raw: ApprovalDecision | bool | str | dict[str, Any] | None,
            *,
            request_id: str,
    ) -> ApprovalDecision:
        if isinstance(raw, ApprovalDecision):
            raw.request_id = request_id
            return raw
        if raw is True or raw is None:
            return ApprovalDecision.approve(request_id=request_id)
        if raw is False:
            return ApprovalDecision.reject("approval rejected", request_id=request_id)
        if isinstance(raw, str):
            return ApprovalDecision.reject(raw, request_id=request_id)
        if isinstance(raw, dict):
            action = raw.get("action")
            if action is None:
                action = "approve" if raw.get("approved", raw.get("allowed", False)) else "reject"
            return ApprovalDecision(
                action=str(action),
                request_id=request_id,
                reason=raw.get("reason"),
                arguments=raw.get("arguments"),
                response=raw.get("response"),
                reviewer_id=raw.get("reviewer_id"),
                metadata=raw.get("metadata") or {},
            )
        if raw:
            return ApprovalDecision.approve(request_id=request_id)
        return ApprovalDecision.reject("approval rejected", request_id=request_id)

    def _restore_approval_decisions(
            self,
            run_id: str,
            record: dict[str, Any],
    ) -> None:
        for step_name, data in (record.get("approvals") or {}).items():
            self._approval_decisions[(run_id, step_name)] = ApprovalDecision(**data)
        for step in record.get("steps", []):
            request_id = step.get("approval_request_id")
            if request_id:
                self._approval_request_ids[(run_id, step["name"])] = request_id

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
