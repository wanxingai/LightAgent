#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Lightweight shared memory primitives for multi-agent experiments.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock
from typing import Any
from uuid import uuid4

from .protocol import MemoryScope


@dataclass(frozen=True)
class SharedMemoryRecord:
    """Append-only record stored in SharedMemoryPool."""

    memory: str
    user_id: str
    metadata: dict[str, Any] = field(default_factory=dict)
    memory_id: str = field(default_factory=lambda: uuid4().hex)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_result(self) -> dict[str, Any]:
        """Return the MemoryProtocol retrieval shape."""
        return {
            "memory": self.memory,
            "user_id": self.user_id,
            "metadata": dict(self.metadata),
            "memory_id": self.memory_id,
            "created_at": self.created_at,
        }


class SharedMemoryPool:
    """In-memory append-first shared memory backend.

    The pool intentionally satisfies the existing MemoryProtocol:
    `store(data, user_id)` and `retrieve(query, user_id)`. It is designed as a
    lightweight prototype for LightSwarm/LightFlow experiments, not as durable
    storage. External backends can mirror this record shape while preserving
    namespace, source, scope, and agent provenance metadata.
    """

    def __init__(
            self,
            *,
            agent_name: str | None = None,
            default_source: str = "user",
            default_scope: str = "user",
            max_results: int = 5,
    ):
        if max_results <= 0:
            raise ValueError("max_results must be greater than 0")
        self.agent_name = agent_name
        self.default_source = default_source
        self.default_scope = default_scope
        self.max_results = max_results
        self._records: list[SharedMemoryRecord] = []
        self._lock = RLock()

    def store(
            self,
            data: str,
            user_id: str,
            *,
            metadata: dict[str, Any] | None = None,
            scope: MemoryScope | None = None,
    ) -> dict[str, Any]:
        """Append a memory record and return storage metadata."""
        record_metadata = self._build_metadata(user_id=user_id, metadata=metadata, scope=scope)
        record = SharedMemoryRecord(
            memory=str(data),
            user_id=str(user_id),
            metadata=record_metadata,
        )
        with self._lock:
            self._records.append(record)
        return {"stored": True, "memory_id": record.memory_id, "user_id": record.user_id}

    def retrieve(
            self,
            query: str,
            user_id: str,
            *,
            agent_name: str | None = None,
            source: str | None = None,
            scope: str | None = None,
            limit: int | None = None,
    ) -> dict[str, list[dict[str, Any]]]:
        """Retrieve scoped memories using simple token overlap ranking."""
        max_results = self.max_results if limit is None else limit
        if max_results <= 0:
            return {"results": []}

        query_tokens = self._tokenize(query)
        with self._lock:
            candidates = [
                record for record in self._records
                if self._record_matches(record, user_id=user_id, agent_name=agent_name, source=source, scope=scope)
            ]

        scored = [
            (self._score(query_tokens, record), index, record)
            for index, record in enumerate(candidates)
        ]
        scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
        return {"results": [record.to_result() for score, _, record in scored[:max_results] if score > 0 or not query_tokens]}

    def list_records(
            self,
            *,
            user_id: str | None = None,
            agent_name: str | None = None,
            source: str | None = None,
            scope: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return records for inspection, optionally filtered by provenance."""
        with self._lock:
            records = [
                record for record in self._records
                if self._record_matches(record, user_id=user_id, agent_name=agent_name, source=source, scope=scope)
            ]
        return [record.to_result() for record in records]

    def clear(self, *, user_id: str | None = None) -> int:
        """Clear all records, or records for a single scoped user id."""
        with self._lock:
            if user_id is None:
                count = len(self._records)
                self._records = []
                return count
            original_count = len(self._records)
            self._records = [record for record in self._records if record.user_id != str(user_id)]
            return original_count - len(self._records)

    def __len__(self) -> int:
        with self._lock:
            return len(self._records)

    def _build_metadata(
            self,
            *,
            user_id: str,
            metadata: dict[str, Any] | None,
            scope: MemoryScope | None,
    ) -> dict[str, Any]:
        if scope is not None:
            record_metadata = scope.to_metadata()
        else:
            record_metadata = MemoryScope(
                source=self.default_source,
                scope=self.default_scope,
                agent_name=self.agent_name,
                metadata={"user_id": str(user_id)},
            ).to_metadata()
        if metadata:
            record_metadata.update(metadata)
        record_metadata.setdefault("user_id", str(user_id))
        return record_metadata

    @staticmethod
    def _record_matches(
            record: SharedMemoryRecord,
            *,
            user_id: str | None,
            agent_name: str | None,
            source: str | None,
            scope: str | None,
    ) -> bool:
        metadata = record.metadata
        if user_id is not None and record.user_id != str(user_id):
            return False
        if agent_name is not None and metadata.get("agent_name") != agent_name:
            return False
        if source is not None and metadata.get("source") != source:
            return False
        if scope is not None and metadata.get("scope") != scope:
            return False
        return True

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        return {token for token in str(text).lower().split() if token}

    @classmethod
    def _score(cls, query_tokens: set[str], record: SharedMemoryRecord) -> int:
        if not query_tokens:
            return 1
        record_tokens = cls._tokenize(record.memory)
        return len(query_tokens & record_tokens)
