#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Trace event primitives for LightAgent observability.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class TraceEvent:
    """A machine-readable event emitted during an agent run."""

    type: str
    data: dict[str, Any] = field(default_factory=dict)
    trace_id: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "data": self.data,
            "trace_id": self.trace_id,
            "timestamp": self.timestamp,
        }


class TraceRecorder:
    """Collect trace events when tracing is explicitly enabled."""

    def __init__(self, enabled: bool = False, trace_id: str | None = None):
        self.enabled = enabled
        self.trace_id = trace_id
        self.events: list[TraceEvent] = []

    def record(self, event_type: str, data: dict[str, Any] | None = None) -> TraceEvent | None:
        if not self.enabled:
            return None
        event = TraceEvent(
            type=event_type,
            data=data or {},
            trace_id=self.trace_id,
        )
        self.events.append(event)
        return event

    def to_list(self) -> list[dict[str, Any]]:
        return [event.to_dict() for event in self.events]
