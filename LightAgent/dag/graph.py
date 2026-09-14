"""Dependency graph algorithms that avoid Python recursion limits."""

from __future__ import annotations

from collections import deque
from typing import Iterable

from .store import DAGError


def topological_order(task_ids: Iterable[str], edges: Iterable[tuple[str, str]]) -> list[str]:
    nodes = set(task_ids)
    edge_set = set(edges)
    unknown = sorted({item for edge in edge_set for item in edge if item not in nodes})
    if unknown:
        raise DAGError("UNKNOWN-DEPENDENCY", f"unknown task IDs: {unknown}")
    if any(task_id == dependency_id for task_id, dependency_id in edge_set):
        raise DAGError("CYCLE", "self dependencies are not allowed")
    indegree = {task_id: 0 for task_id in nodes}
    reverse: dict[str, list[str]] = {task_id: [] for task_id in nodes}
    for task_id, dependency_id in edge_set:
        indegree[task_id] += 1
        reverse[dependency_id].append(task_id)
    ready = deque(sorted(task_id for task_id, degree in indegree.items() if degree == 0))
    ordered = []
    while ready:
        current = ready.popleft()
        ordered.append(current)
        for dependent in sorted(reverse[current]):
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                ready.append(dependent)
    if len(ordered) != len(nodes):
        raise DAGError("CYCLE", "task dependencies contain a cycle")
    return ordered


def dependency_closure(task_id: str, edges: Iterable[tuple[str, str]]) -> set[str]:
    dependencies: dict[str, list[str]] = {}
    for task, dependency in edges:
        dependencies.setdefault(task, []).append(dependency)
    seen: set[str] = set()
    pending = list(dependencies.get(task_id, ()))
    while pending:
        current = pending.pop()
        if current in seen:
            continue
        seen.add(current)
        pending.extend(dependencies.get(current, ()))
    return seen


__all__ = ["topological_order", "dependency_closure"]
