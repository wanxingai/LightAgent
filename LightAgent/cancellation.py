"""Cooperative cancellation primitives shared by runtime executions."""

from __future__ import annotations

import inspect
from threading import Event, Lock
from typing import Any, Callable
from uuid import uuid4


class CancellationToken:
    """Thread-safe cooperative cancellation token with parent propagation."""

    def __init__(
            self,
            *,
            token_id: str | None = None,
            parent: "CancellationToken | None" = None,
            run_id: str | None = None,
    ):
        self.token_id = token_id or uuid4().hex
        self.parent = parent
        self.run_id = run_id
        self._event = Event()
        self._reason: str | None = None
        self._lock = Lock()

    @property
    def cancelled(self) -> bool:
        return self._event.is_set() or bool(self.parent and self.parent.cancelled)

    @property
    def reason(self) -> str | None:
        if self._event.is_set():
            return self._reason
        if self.parent and self.parent.cancelled:
            return self.parent.reason
        return None

    def cancel(self, reason: str | None = None) -> bool:
        """Cancel once and return whether this call changed the token."""
        with self._lock:
            if self._event.is_set():
                return False
            self._reason = reason or "cancelled"
            self._event.set()
            return True

    def child(self, *, run_id: str | None = None) -> "CancellationToken":
        return CancellationToken(parent=self, run_id=run_id or self.run_id)

    def wait(self, timeout: float | None = None) -> bool:
        if self.cancelled:
            return True
        if self.parent is None:
            return self._event.wait(timeout)
        # Parent-aware waiting is cooperative; callers that need prompt wakeup
        # should poll at their natural safe boundaries.
        return self._event.wait(timeout) or self.parent.cancelled


def accepts_keyword(function: Callable[..., Any], keyword: str) -> bool:
    """Return whether a callable explicitly or generically accepts a keyword."""
    try:
        parameters = inspect.signature(function).parameters
    except (TypeError, ValueError):
        return False
    parameter = parameters.get(keyword)
    return (parameter is not None and parameter.kind in (
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
        inspect.Parameter.KEYWORD_ONLY,
    )) or any(
        parameter.kind == inspect.Parameter.VAR_KEYWORD
        for parameter in parameters.values()
    )


__all__ = ["CancellationToken", "accepts_keyword"]
