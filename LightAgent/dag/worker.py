"""Worker protocols, factories, and strict LightAgent result adaptation."""

from __future__ import annotations

import asyncio
import inspect
import json
from typing import Any, Awaitable, Callable, Mapping, Protocol

from ..cancellation import accepts_keyword
from .models import DecompositionProposal, TaskContext, TaskOutcome, TaskOutcomeKind, TaskSpec


class DAGWorkerProtocolError(RuntimeError):
    pass


class DAGWorker(Protocol):
    async def execute(self, context: TaskContext) -> TaskOutcome:
        ...


class WorkerFactory(Protocol):
    async def create(self, worker_key: str, context: TaskContext) -> DAGWorker:
        ...

    async def release(self, worker: DAGWorker, context: TaskContext) -> None:
        ...


class CallableWorker:
    def __init__(self, function: Callable[[TaskContext], Any | Awaitable[Any]]):
        self.function = function

    async def execute(self, context: TaskContext) -> TaskOutcome:
        if inspect.iscoroutinefunction(self.function):
            raw = await self.function(context)
        else:
            raw = await asyncio.to_thread(self.function, context)
        return normalize_task_outcome(raw, context)


class RegistryWorkerFactory:
    """Create isolated workers from stable application-owned registrations."""

    def __init__(self, registrations: Mapping[str, Any] | None = None):
        self.registrations = dict(registrations or {})
        self.factories: set[str] = set()

    def register(self, key: str, factory: Any) -> None:
        if not key.strip():
            raise ValueError("worker key must not be empty")
        self.registrations[key] = factory

    def register_factory(self, key: str, factory: Any) -> None:
        self.register(key, factory)
        self.factories.add(key)

    async def create(self, worker_key: str, context: TaskContext) -> DAGWorker:
        if worker_key not in self.registrations:
            raise LookupError(f"worker `{worker_key}` is not registered")
        registration = self.registrations[worker_key]
        if worker_key in self.factories:
            value = registration(context) if accepts_keyword(registration, "context") else registration()
            if inspect.isawaitable(value):
                value = await value
        else:
            value = registration
        if hasattr(value, "execute"):
            return value
        if callable(value):
            return CallableWorker(value)
        raise TypeError(f"worker registration `{worker_key}` does not produce a DAGWorker")

    async def release(self, worker: DAGWorker, context: TaskContext) -> None:
        close = getattr(worker, "close", None)
        if callable(close):
            value = close()
            if inspect.isawaitable(value):
                await value


class LightAgentWorkerAdapter:
    """Require explicit structured TaskOutcome output from a LightAgent-like object."""

    def __init__(self, agent: Any, *, prompt_builder: Callable[[TaskContext], str] | None = None):
        self.agent = agent
        self.prompt_builder = prompt_builder or self._default_prompt

    async def execute(self, context: TaskContext) -> TaskOutcome:
        query = self.prompt_builder(context)
        kwargs = {
            "user_id": context.security_context.user_id or "dag-worker",
            "cancellation_token": context.cancellation_token,
            "idempotency_key": f"{context.run.run_id}:{context.task.spec.task_id}:{context.attempt.attempt_no}",
        }
        arun = getattr(self.agent, "arun", None)
        if callable(arun):
            accepted = {key: value for key, value in kwargs.items() if accepts_keyword(arun, key)}
            raw = await arun(query, **accepted)
        else:
            run = getattr(self.agent, "run", None)
            if not callable(run):
                raise TypeError("LightAgentWorkerAdapter requires an object with run() or arun()")
            accepted = {key: value for key, value in kwargs.items() if accepts_keyword(run, key)}
            raw = await asyncio.to_thread(run, query, **accepted)
        if hasattr(raw, "error") and raw.error:
            raise DAGWorkerProtocolError("agent returned a failed RunResult")
        content = getattr(raw, "content", raw)
        if isinstance(content, str):
            try:
                content = json.loads(content)
            except (json.JSONDecodeError, TypeError) as exc:
                raise DAGWorkerProtocolError("agent output must be an explicit JSON TaskOutcome") from exc
        return normalize_task_outcome(content, context)

    @staticmethod
    def _default_prompt(context: TaskContext) -> str:
        dependencies = {
            task_id: [artifact.to_dict() for artifact in artifacts]
            for task_id, artifacts in context.dependency_artifacts.items()
        }
        return json.dumps({
            "instruction": "Return a JSON TaskOutcome with kind candidate, decomposition, or blocked.",
            "goal": context.task.spec.goal,
            "acceptance_contract": context.task.spec.acceptance_contract,
            "phase": context.attempt.phase,
            "dependencies": dependencies,
            "last_diagnostic": context.last_diagnostic,
        }, ensure_ascii=False, sort_keys=True)


def normalize_task_outcome(raw: Any, context: TaskContext | None = None) -> TaskOutcome:
    if isinstance(raw, TaskOutcome):
        return raw
    if not isinstance(raw, Mapping):
        raise DAGWorkerProtocolError("worker must return TaskOutcome or an explicit mapping")
    kind = TaskOutcomeKind(str(raw.get("kind", "")))
    metadata = dict(raw.get("metadata") or {})
    if kind == TaskOutcomeKind.CANDIDATE:
        if "content" not in raw:
            raise DAGWorkerProtocolError("candidate outcome requires content")
        return TaskOutcome.candidate(
            raw["content"],
            media_type=str(raw.get("media_type", "text/plain")),
            **metadata,
        )
    if kind == TaskOutcomeKind.BLOCKED:
        return TaskOutcome.blocked(str(raw.get("blocker") or ""), **metadata)
    proposal_value = raw.get("decomposition")
    if isinstance(proposal_value, DecompositionProposal):
        proposal = proposal_value
    elif isinstance(proposal_value, Mapping):
        if context is None:
            raise DAGWorkerProtocolError("decomposition mapping requires TaskContext")
        proposal_kwargs = {
            "parent_task_id": str(proposal_value.get("parent_task_id") or context.task.spec.task_id),
            "new_tasks": tuple(TaskSpec.from_dict(item) for item in proposal_value.get("new_tasks", [])),
            "reuse_task_ids": tuple(proposal_value.get("reuse_task_ids") or ()),
            "rationale": str(proposal_value.get("rationale") or ""),
            "composition_contract": proposal_value.get("composition_contract"),
            "expected_graph_revision": int(
                proposal_value.get("expected_graph_revision", context.run.graph_revision)
            ),
        }
        if proposal_value.get("proposal_id"):
            proposal_kwargs["proposal_id"] = str(proposal_value["proposal_id"])
        proposal = DecompositionProposal(**proposal_kwargs)
    else:
        raise DAGWorkerProtocolError("decomposition outcome requires a proposal")
    return TaskOutcome.decompose(proposal, **metadata)


__all__ = [
    "DAGWorkerProtocolError",
    "DAGWorker",
    "WorkerFactory",
    "CallableWorker",
    "RegistryWorkerFactory",
    "LightAgentWorkerAdapter",
    "normalize_task_outcome",
]
