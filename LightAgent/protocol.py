#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
作者: [weego/WXAI-Team]
最后更新: 2026-02-20
"""

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
import re
from typing import Any, Callable, Iterable, Protocol
from uuid import uuid4


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


MEMORY_PROMOTION_APPROVE = "approve"
MEMORY_PROMOTION_REJECT = "reject"
MEMORY_PROMOTION_REWRITE = "rewrite"
MEMORY_PROMOTION_KEEP = "keep"


@dataclass(frozen=True)
class MemoryCandidate:
    """Non-injectable memory evidence awaiting explicit promotion."""

    data: str
    memory_user_id: str
    original_user_id: str
    source: str
    scope: str
    agent_name: str | None = None
    trace_id: str | None = None
    parent_trace_id: str | None = None
    run_id: str | None = None
    run_group_id: str | None = None
    confidence: float | None = None
    trust_level: str | None = None
    candidate_id: str = field(default_factory=lambda: uuid4().hex)
    status: str = "candidate"
    injectable: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def with_updates(self, **updates: Any) -> "MemoryCandidate":
        """Return a copy with selected fields changed."""
        return replace(self, **updates)

    def to_metadata(self) -> dict[str, Any]:
        """Export metadata for adapters that persist a promoted candidate."""
        data = dict(self.metadata)
        data["user_id"] = str(self.memory_user_id)
        data["original_user_id"] = str(self.original_user_id)
        data["source"] = self.source
        data["scope"] = self.scope
        data["candidate_id"] = self.candidate_id
        data["promotion_status"] = self.status
        data["injectable"] = self.injectable
        if self.agent_name is not None:
            data["agent_name"] = self.agent_name
        if self.trace_id is not None:
            data["trace_id"] = self.trace_id
        if self.parent_trace_id is not None:
            data["parent_trace_id"] = self.parent_trace_id
        if self.run_id is not None:
            data["run_id"] = self.run_id
        if self.run_group_id is not None:
            data["run_group_id"] = self.run_group_id
        if self.confidence is not None:
            data["confidence"] = self.confidence
        if self.trust_level is not None:
            data["trust_level"] = self.trust_level
        return data

    def to_dict(self, *, include_data: bool = True) -> dict[str, Any]:
        """Return a serializable representation for APIs, hooks, and tests."""
        data = {
            "candidate_id": self.candidate_id,
            "memory_user_id": str(self.memory_user_id),
            "original_user_id": str(self.original_user_id),
            "source": self.source,
            "scope": self.scope,
            "agent_name": self.agent_name,
            "trace_id": self.trace_id,
            "parent_trace_id": self.parent_trace_id,
            "run_id": self.run_id,
            "run_group_id": self.run_group_id,
            "confidence": self.confidence,
            "trust_level": self.trust_level,
            "status": self.status,
            "injectable": self.injectable,
            "metadata": dict(self.metadata),
        }
        if include_data:
            data["data"] = self.data
        return {key: value for key, value in data.items() if value is not None}


@dataclass(frozen=True)
class MemoryPromotionDecision:
    """Decision returned before internal memory can become prompt-injectable."""

    action: str = MEMORY_PROMOTION_KEEP
    reason: str | None = None
    value: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        action = str(self.action).lower()
        if action not in {
            MEMORY_PROMOTION_APPROVE,
            MEMORY_PROMOTION_REJECT,
            MEMORY_PROMOTION_REWRITE,
            MEMORY_PROMOTION_KEEP,
        }:
            raise ValueError("MemoryPromotionDecision action must be approve, reject, rewrite, or keep")
        object.__setattr__(self, "action", action)

    @property
    def promotes(self) -> bool:
        return self.action in {MEMORY_PROMOTION_APPROVE, MEMORY_PROMOTION_REWRITE}

    @classmethod
    def approve(
            cls,
            value: str | None = None,
            *,
            reason: str | None = None,
            metadata: dict[str, Any] | None = None,
    ) -> "MemoryPromotionDecision":
        return cls(action=MEMORY_PROMOTION_APPROVE, value=value, reason=reason, metadata=metadata or {})

    @classmethod
    def reject(
            cls,
            reason: str | None = None,
            *,
            metadata: dict[str, Any] | None = None,
    ) -> "MemoryPromotionDecision":
        return cls(action=MEMORY_PROMOTION_REJECT, reason=reason, metadata=metadata or {})

    @classmethod
    def rewrite(
            cls,
            value: str,
            *,
            reason: str | None = None,
            metadata: dict[str, Any] | None = None,
    ) -> "MemoryPromotionDecision":
        return cls(action=MEMORY_PROMOTION_REWRITE, value=value, reason=reason, metadata=metadata or {})

    @classmethod
    def keep(
            cls,
            reason: str | None = None,
            *,
            metadata: dict[str, Any] | None = None,
    ) -> "MemoryPromotionDecision":
        return cls(action=MEMORY_PROMOTION_KEEP, reason=reason, metadata=metadata or {})


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
    enforce_expires_at: bool = False
    memory_write_admission: Callable[[str, dict[str, Any]], Any] | None = None
    max_writes_per_run: int | None = None
    reject_duplicate_writes: bool = False
    min_write_length: int | None = None
    reject_write_patterns: Iterable[str] | None = None
    memory_promotion_admission: Callable[[MemoryCandidate, dict[str, Any]], Any] | None = None
    require_promotion_for_internal_memory: bool = True

    def __post_init__(self):
        for field_name in ("allowed_sources", "allowed_scopes", "allowed_agent_names", "allowed_trust_levels"):
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, tuple):
                object.__setattr__(self, field_name, tuple(str(item) for item in value))
        if self.max_writes_per_run is not None and self.max_writes_per_run < 0:
            raise ValueError("max_writes_per_run must be greater than or equal to 0")
        if self.min_write_length is not None and self.min_write_length < 0:
            raise ValueError("min_write_length must be greater than or equal to 0")
        if self.reject_write_patterns is not None and not isinstance(self.reject_write_patterns, tuple):
            object.__setattr__(self, "reject_write_patterns", tuple(str(item) for item in self.reject_write_patterns))

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
        if self._blocks_prompt_injection(item, metadata):
            return False

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
            and self._allows_not_expired(item, metadata)
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

    def _allows_not_expired(self, item: dict[str, Any], metadata: dict[str, Any]) -> bool:
        expires_at = self._get_value(item, metadata, ("expires_at", "expiresAt"))
        if expires_at is None:
            return not self.enforce_expires_at
        try:
            if isinstance(expires_at, (int, float)):
                expires = datetime.fromtimestamp(float(expires_at), tz=timezone.utc)
            else:
                expires = datetime.fromisoformat(str(expires_at).replace("Z", "+00:00"))
                if expires.tzinfo is None:
                    expires = expires.replace(tzinfo=timezone.utc)
        except (TypeError, ValueError):
            return False
        return expires > datetime.now(timezone.utc)

    def _blocks_prompt_injection(self, item: dict[str, Any], metadata: dict[str, Any]) -> bool:
        injectable = self._get_value(item, metadata, ("injectable", "prompt_injectable", "is_injectable"))
        if injectable is not None and not self._truthy(injectable):
            return True

        status = self._get_value(item, metadata, ("promotion_status",))
        normalized_status = str(status).lower() if status is not None else None
        if normalized_status in {
            "candidate",
            "pending",
            "requires_review",
            "review_required",
            "kept",
            "non_injectable",
            "rejected",
            "blocked",
        }:
            return True

        if not self.require_promotion_for_internal_memory:
            return False

        source = self._get_value(item, metadata, ("source", "memory_source"))
        scope = self._get_value(item, metadata, ("scope", "memory_scope"))
        internal_source = source is not None and str(source).lower() in {
            "reflection",
            "delegation",
            "self_learning",
            "agent",
            "derived",
            "swarm",
            "trace",
            "tool",
        }
        internal_scope = scope is not None and str(scope).lower() in {
            "agent",
            "delegation",
            "shared",
            "internal",
            "swarm",
            "flow",
        }
        if not internal_source and not internal_scope:
            return False

        if normalized_status in {"promoted", "approved"}:
            return False
        return not self._truthy(injectable)

    @staticmethod
    def _truthy(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        return str(value).strip().lower() in {"1", "true", "yes", "y", "on", "promoted", "approved"}

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

        if self.min_write_length is not None and len(candidate.strip()) < self.min_write_length:
            return MemoryAdmissionDecision(
                allowed=False,
                reason=f"Memory write is shorter than min_write_length={self.min_write_length}",
            )

        for pattern in self.reject_write_patterns or ():
            if re.search(pattern, candidate, flags=re.IGNORECASE):
                return MemoryAdmissionDecision(allowed=False, reason=f"Memory write rejected by pattern: {pattern}")

        fingerprint = self.write_fingerprint(candidate, context)
        if self.reject_duplicate_writes and recent_fingerprints is not None and fingerprint in recent_fingerprints:
            return MemoryAdmissionDecision(allowed=False, reason="Duplicate memory write blocked.")

        if self.memory_write_admission is None:
            return MemoryAdmissionDecision(allowed=True, value=candidate)

        raw_decision = self.memory_write_admission(candidate, context)
        return self._coerce_write_decision(raw_decision, candidate)

    def allows_promotion(
            self,
            candidate: MemoryCandidate,
            context: dict[str, Any] | None = None,
    ) -> MemoryPromotionDecision:
        """Return whether a non-injectable candidate can be promoted."""
        if self.memory_promotion_admission is None:
            return MemoryPromotionDecision.keep("Memory promotion requires explicit approval.")
        try:
            raw_decision = self.memory_promotion_admission(candidate, context or {})
        except Exception as exc:
            return MemoryPromotionDecision.keep(
                f"Memory promotion admission failed: {type(exc).__name__}",
                metadata={"admission_error_type": type(exc).__name__},
            )
        return self._coerce_promotion_decision(raw_decision, candidate.data)

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

    @staticmethod
    def _coerce_promotion_decision(raw_decision: Any, current_value: str) -> MemoryPromotionDecision:
        if isinstance(raw_decision, MemoryPromotionDecision):
            return raw_decision
        if raw_decision is None:
            return MemoryPromotionDecision.keep("Memory promotion callback did not approve this candidate.")
        if raw_decision is True:
            return MemoryPromotionDecision.approve(current_value)
        if raw_decision is False:
            return MemoryPromotionDecision.reject("Memory promotion callback rejected this candidate.")
        if isinstance(raw_decision, str):
            return MemoryPromotionDecision.reject(raw_decision)
        if isinstance(raw_decision, dict):
            action = raw_decision.get("action")
            if action:
                return MemoryPromotionDecision(
                    action=str(action),
                    reason=raw_decision.get("reason"),
                    value=raw_decision.get("value"),
                    metadata=raw_decision.get("metadata") or {},
                )
            allowed = raw_decision.get("allowed", raw_decision.get("promote"))
            if allowed is True:
                value = raw_decision.get("value", current_value)
                if value != current_value:
                    return MemoryPromotionDecision.rewrite(
                        str(value),
                        reason=raw_decision.get("reason"),
                        metadata=raw_decision.get("metadata"),
                    )
                return MemoryPromotionDecision.approve(
                    str(value),
                    reason=raw_decision.get("reason"),
                    metadata=raw_decision.get("metadata"),
                )
            if allowed is False:
                return MemoryPromotionDecision.reject(
                    raw_decision.get("reason"),
                    metadata=raw_decision.get("metadata"),
                )
            if "value" in raw_decision:
                return MemoryPromotionDecision.rewrite(
                    str(raw_decision["value"]),
                    reason=raw_decision.get("reason"),
                    metadata=raw_decision.get("metadata"),
                )
            return MemoryPromotionDecision.keep(
                raw_decision.get("reason"),
                metadata=raw_decision.get("metadata"),
            )
        return MemoryPromotionDecision.keep("Memory promotion callback returned an unsupported decision.")
