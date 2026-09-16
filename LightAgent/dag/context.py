"""Bounded local context construction for one DAG task attempt."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable, Iterable

from .models import ArtifactManifest, DAGTask, TaskAttempt
from .store import DAGError


@dataclass(frozen=True)
class DAGContextBudget:
    max_chars: int = 32_000
    max_dependency_artifacts: int = 32
    max_retrieval_results: int = 8

    def __post_init__(self) -> None:
        if min(self.max_chars, self.max_dependency_artifacts, self.max_retrieval_results) <= 0:
            raise ValueError("DAG context limits must be positive")


class ContextBuilder:
    """Keep mandatory contracts intact and trim only optional retrieval data."""

    def __init__(
            self,
            *,
            budget: DAGContextBudget | None = None,
            retrieve: Callable[[str, int], Iterable[Any]] | None = None,
    ):
        self.budget = budget or DAGContextBudget()
        self.retrieve = retrieve

    def build(
            self,
            task: DAGTask,
            attempt: TaskAttempt,
            dependency_artifacts: dict[str, tuple[ArtifactManifest, ...]],
    ) -> dict[str, Any]:
        flattened = [
            artifact
            for task_id in sorted(dependency_artifacts)
            for artifact in dependency_artifacts[task_id]
        ]
        if len(flattened) > self.budget.max_dependency_artifacts:
            raise DAGError("CONTEXT-OVERFLOW", "required dependency artifacts exceed the context budget")
        mandatory = {
            "task_id": task.spec.task_id,
            "goal": task.spec.goal,
            "acceptance_contract": task.spec.acceptance_contract,
            "contract_hash": task.spec.contract_hash,
            "phase": attempt.phase,
            "input_snapshot_hash": attempt.input_snapshot_hash,
            "dependencies": {
                task_id: [artifact.to_dict() for artifact in artifacts]
                for task_id, artifacts in dependency_artifacts.items()
            },
            "last_diagnostic": task.state.last_diagnostic,
        }
        mandatory_size = len(json.dumps(mandatory, ensure_ascii=False, default=repr))
        if mandatory_size > self.budget.max_chars:
            raise DAGError("CONTEXT-OVERFLOW", "mandatory task contract does not fit the context budget")
        retrieval = []
        if self.retrieve:
            for item in self.retrieve(task.spec.goal, self.budget.max_retrieval_results):
                candidate = [*retrieval, item]
                payload = {**mandatory, "retrieval": candidate}
                if len(json.dumps(payload, ensure_ascii=False, default=repr)) > self.budget.max_chars:
                    break
                retrieval = candidate
        return {**mandatory, "retrieval": retrieval}


__all__ = ["DAGContextBudget", "ContextBuilder"]
