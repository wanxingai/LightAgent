"""Execution contracts shared by native and external agent workers."""

from __future__ import annotations

import asyncio
import math
from datetime import datetime, timezone
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Protocol
from uuid import uuid4

from ..cancellation import CancellationToken
from ..security import SecurityContext


class BackendError(RuntimeError):
    """A backend failed before it could produce a trustworthy result."""


@dataclass(frozen=True)
class BackendCapabilities:
    resume: bool = False
    steer: bool = False
    cancel: bool = True
    events: bool = True
    isolation: str = "none"
    network_control: bool = False
    budget_dimensions: tuple[str, ...] = ()

    def __post_init__(self):
        if self.isolation not in ("none", "sandbox", "docker"):
            raise ValueError("unknown execution isolation boundary")
        if any(type(getattr(self, key)) is not bool for key in
               ("resume", "steer", "cancel", "events", "network_control")):
            raise ValueError("backend capability flags must be boolean")
        if set(self.budget_dimensions) - {"model_calls", "tool_calls", "tokens", "cost"}:
            raise ValueError("unsupported backend budget enforcement dimension")


@dataclass(frozen=True)
class BackendProbe:
    backend: str
    version: str
    capabilities: BackendCapabilities
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True)
class BackendEvent:
    type: str
    attempt_id: str
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BackendRequest:
    prompt: str
    workspace: str
    security_context: SecurityContext
    attempt_id: str = field(default_factory=lambda: uuid4().hex)
    session_id: str | None = None
    timeout: float = 1800
    cancellation_token: CancellationToken | None = None
    on_event: Callable[[BackendEvent], None] | None = field(default=None, repr=False, compare=False)
    budget_reservation: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.prompt.strip():
            raise ValueError("prompt must not be empty")
        if len(self.prompt.encode("utf-8")) > 2 * 1024 * 1024:
            raise ValueError("prompt exceeds the 2 MiB execution budget")
        if not math.isfinite(self.timeout) or self.timeout <= 0:
            raise ValueError("timeout must be finite and positive")
        if (set(self.budget_reservation) - {"backend_calls", "model_calls", "tool_calls", "tokens", "seconds", "cost"}
                or any(type(v) not in (int, float) or not math.isfinite(v) or v < 0 for v in self.budget_reservation.values())):
            raise ValueError("invalid execution budget reservation")
        path = Path(self.workspace).resolve(strict=True)
        if not path.is_dir():
            raise ValueError("workspace must be a directory")
        object.__setattr__(self, "workspace", str(path))
        if self.security_context.resources and str(path) not in self.security_context.resources:
            raise PermissionError("workspace resource is outside the security context")
        if self.security_context.deadline:
            deadline = datetime.fromisoformat(self.security_context.deadline.replace("Z", "+00:00"))
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=timezone.utc)
            remaining = (deadline - datetime.now(timezone.utc)).total_seconds()
            if remaining <= 0:
                raise PermissionError("backend deadline has expired")
            object.__setattr__(self, "timeout", min(self.timeout, remaining))

    def emit(self, event_type: str, **data: Any) -> None:
        if self.on_event:
            self.on_event(BackendEvent(event_type, self.attempt_id, data))


@dataclass(frozen=True)
class BackendResult:
    content: str
    status: str = "completed"
    session_id: str | None = None
    usage: dict[str, Any] | None = None
    error: str | None = None


class AgentBackend(Protocol):
    capabilities: BackendCapabilities

    def probe(self) -> BackendProbe:
        ...

    async def execute(self, request: BackendRequest) -> BackendResult:
        ...


async def cancellable_thread(function, token: CancellationToken):
    """Propagate asyncio cancellation and wait for owned processes to exit."""
    task = asyncio.create_task(asyncio.to_thread(function))
    try:
        return await asyncio.shield(task)
    except asyncio.CancelledError:
        token.cancel("async task cancelled")
        # Repeated cancellation must not detach the still-running thread and
        # let its subprocess outlive the awaiter's cleanup contract.
        while not task.done():
            try:
                await asyncio.shield(task)
            except asyncio.CancelledError:
                continue
            except Exception:
                break
        if task.done() and not task.cancelled():
            task.exception()  # retrieve any worker failure; cancellation wins
        raise
