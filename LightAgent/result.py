#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Structured result objects for optional LightAgent responses.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RunResult:
    """Optional structured return value for non-streaming agent runs."""

    content: str
    reasoning_content: str | None = None
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    usage: dict[str, Any] | None = None
    trace_id: str | None = None
    trace: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None

    def __str__(self) -> str:
        return self.content


@dataclass
class StreamEvent:
    """Optional structured event for streaming agent runs."""

    type: str
    data: Any = None
    trace_id: str | None = None

    def __str__(self) -> str:
        return str(self.data)
