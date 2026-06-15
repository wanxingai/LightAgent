#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
作者: [weego/WXAI-Team]
最后更新: 2026-02-20
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Protocol


class MemoryProtocol(Protocol):
    """记忆存储与检索协议"""
    def store(self, data: str, user_id: str) -> Any:
        ...

    def retrieve(self, query: str, user_id: str) -> Any:
        ...


@dataclass(frozen=True)
class MemoryScope:
    """Recommended metadata shape for memory provenance and retrieval policy."""

    source: str = "user"
    scope: str = "user"
    agent_name: str | None = None
    trace_id: str | None = None
    parent_trace_id: str | None = None
    confidence: float | None = None
    trust_level: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_metadata(self) -> dict[str, Any]:
        """Export scope fields as a memory adapter metadata dictionary."""
        data = dict(self.metadata)
        data["source"] = self.source
        data["scope"] = self.scope
        if self.agent_name is not None:
            data["agent_name"] = self.agent_name
        if self.trace_id is not None:
            data["trace_id"] = self.trace_id
        if self.parent_trace_id is not None:
            data["parent_trace_id"] = self.parent_trace_id
        if self.confidence is not None:
            data["confidence"] = self.confidence
        if self.trust_level is not None:
            data["trust_level"] = self.trust_level
        return data

    @classmethod
    def user(cls, *, agent_name: str | None = None, trace_id: str | None = None, **metadata: Any) -> "MemoryScope":
        return cls(source="user", scope="user", agent_name=agent_name, trace_id=trace_id, metadata=metadata)

    @classmethod
    def reflection(
            cls,
            *,
            agent_name: str | None = None,
            trace_id: str | None = None,
            parent_trace_id: str | None = None,
            **metadata: Any,
    ) -> "MemoryScope":
        return cls(
            source="reflection",
            scope="agent",
            agent_name=agent_name,
            trace_id=trace_id,
            parent_trace_id=parent_trace_id,
            metadata=metadata,
        )


@dataclass(frozen=True)
class MemoryAdmissionDecision:
    """Decision returned before a memory write is persisted."""

    allowed: bool
    reason: str | None = None
    value: str | None = None


@dataclass(frozen=True)
class MemoryPolicy:
    """Optional safety policy for shared memory backends."""

    namespace: str | None = None
    allow_unattributed_results: bool = True
    allowed_sources: Iterable[str] | None = None
    allowed_scopes: Iterable[str] | None = None
    allowed_agent_names: Iterable[str] | None = None
    allowed_trust_levels: Iterable[str] | None = None
    min_confidence: float | None = None
    memory_write_admission: Callable[[str, dict[str, Any]], Any] | None = None
    max_writes_per_run: int | None = None
    reject_duplicate_writes: bool = False

    def __post_init__(self):
        for field_name in ("allowed_sources", "allowed_scopes", "allowed_agent_names", "allowed_trust_levels"):
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, tuple):
                object.__setattr__(self, field_name, tuple(str(item) for item in value))
        if self.max_writes_per_run is not None and self.max_writes_per_run < 0:
            raise ValueError("max_writes_per_run must be greater than or equal to 0")

    def scoped_user_id(self, user_id: str) -> str:
        user = str(user_id)
        if not self.namespace:
            return user
        return f"{self.namespace}:{user}"

    def allows_result(self, item: Any, scoped_user_id: str, original_user_id: str) -> bool:
        """Return whether a retrieved memory item can be injected into context."""
        if not isinstance(item, dict):
            return self.allow_unattributed_results

        metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        item_user_id = (
            item.get("user_id")
            or item.get("userId")
            or metadata.get("user_id")
            or metadata.get("userId")
        )
        if item_user_id is None:
            return self.allow_unattributed_results

        allowed = {str(original_user_id), str(scoped_user_id)}
        if str(item_user_id) not in allowed:
            return False

        return (
            self._allows_value(item, metadata, ("source", "memory_source"), self.allowed_sources)
            and self._allows_value(item, metadata, ("scope", "memory_scope"), self.allowed_scopes)
            and self._allows_value(item, metadata, ("agent_name", "agent"), self.allowed_agent_names)
            and self._allows_value(item, metadata, ("trust_level", "trust"), self.allowed_trust_levels)
            and self._allows_confidence(item, metadata)
        )

    @staticmethod
    def _get_value(item: dict[str, Any], metadata: dict[str, Any], names: tuple[str, ...]) -> Any:
        for name in names:
            if name in item:
                return item.get(name)
            if name in metadata:
                return metadata.get(name)
        return None

    @classmethod
    def _allows_value(
            cls,
            item: dict[str, Any],
            metadata: dict[str, Any],
            names: tuple[str, ...],
            allowed_values: Iterable[str] | None,
    ) -> bool:
        if allowed_values is None:
            return True
        value = cls._get_value(item, metadata, names)
        if value is None:
            return False
        allowed = {str(item) for item in allowed_values}
        return str(value) in allowed

    def _allows_confidence(self, item: dict[str, Any], metadata: dict[str, Any]) -> bool:
        if self.min_confidence is None:
            return True
        value = self._get_value(item, metadata, ("confidence", "score", "trust_score"))
        if value is None:
            return False
        try:
            return float(value) >= float(self.min_confidence)
        except (TypeError, ValueError):
            return False

    def allows_write(
            self,
            data: str,
            context: dict[str, Any] | None = None,
            *,
            write_count: int = 0,
            recent_fingerprints: set[str] | None = None,
    ) -> MemoryAdmissionDecision:
        """Return whether a candidate memory write should be persisted."""
        context = context or {}
        candidate = str(data)

        if self.max_writes_per_run is not None and write_count >= self.max_writes_per_run:
            return MemoryAdmissionDecision(
                allowed=False,
                reason=f"Memory write limit exceeded: max_writes_per_run={self.max_writes_per_run}",
            )

        fingerprint = self.write_fingerprint(candidate, context)
        if self.reject_duplicate_writes and recent_fingerprints is not None and fingerprint in recent_fingerprints:
            return MemoryAdmissionDecision(allowed=False, reason="Duplicate memory write blocked.")

        if self.memory_write_admission is None:
            return MemoryAdmissionDecision(allowed=True, value=candidate)

        raw_decision = self.memory_write_admission(candidate, context)
        return self._coerce_write_decision(raw_decision, candidate)

    @staticmethod
    def write_fingerprint(data: str, context: dict[str, Any] | None = None) -> str:
        """Build a lightweight duplicate key for a candidate memory write."""
        context = context or {}
        normalized = " ".join(str(data).lower().split())
        scope_key = "|".join(
            str(context.get(key, ""))
            for key in ("memory_user_id", "source", "scope", "agent_name")
        )
        return f"{scope_key}|{normalized}"

    @staticmethod
    def _coerce_write_decision(raw_decision: Any, current_value: str) -> MemoryAdmissionDecision:
        if isinstance(raw_decision, MemoryAdmissionDecision):
            return raw_decision
        if raw_decision is None or raw_decision is True:
            return MemoryAdmissionDecision(allowed=True, value=current_value)
        if raw_decision is False:
            return MemoryAdmissionDecision(allowed=False, reason="Memory write admission blocked this write.")
        if isinstance(raw_decision, str):
            return MemoryAdmissionDecision(allowed=False, reason=raw_decision)
        if isinstance(raw_decision, dict):
            return MemoryAdmissionDecision(
                allowed=bool(raw_decision.get("allowed", True)),
                reason=raw_decision.get("reason"),
                value=raw_decision.get("value", current_value),
            )
        return MemoryAdmissionDecision(allowed=True, value=str(raw_decision))
