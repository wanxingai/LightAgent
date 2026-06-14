#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
作者: [weego/WXAI-Team]
最后更新: 2026-02-20
"""

from dataclasses import dataclass, field
from typing import Any, Iterable, Protocol


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
class MemoryPolicy:
    """Optional safety policy for shared memory backends."""

    namespace: str | None = None
    allow_unattributed_results: bool = True
    allowed_sources: Iterable[str] | None = None
    allowed_scopes: Iterable[str] | None = None
    allowed_agent_names: Iterable[str] | None = None
    allowed_trust_levels: Iterable[str] | None = None
    min_confidence: float | None = None

    def __post_init__(self):
        for field_name in ("allowed_sources", "allowed_scopes", "allowed_agent_names", "allowed_trust_levels"):
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, tuple):
                object.__setattr__(self, field_name, tuple(str(item) for item in value))

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
