#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Runtime hook primitives for LightAgent lifecycle extensions.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import inspect
from dataclasses import dataclass, field
from collections.abc import Awaitable
from typing import Any, Callable


HOOK_CONTINUE = "continue"
HOOK_REPLACE = "replace"
HOOK_BLOCK = "block"
HOOK_RETRY = "retry"
HOOK_FALLBACK = "fallback"
HOOK_METADATA = "metadata"


@dataclass
class HookContext:
    """Context passed to runtime hooks."""

    phase: str
    payload: dict[str, Any] = field(default_factory=dict)
    trace_id: str | None = None
    parent_trace_id: str | None = None
    run_id: str | None = None
    run_group_id: str | None = None
    user_id: str | None = None
    agent_name: str | None = None
    flow_id: str | None = None
    step_name: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class HookDecision:
    """Decision returned by a runtime hook."""

    action: str = HOOK_CONTINUE
    payload: dict[str, Any] | None = None
    reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def continue_(cls, *, metadata: dict[str, Any] | None = None) -> "HookDecision":
        return cls(action=HOOK_CONTINUE, metadata=metadata or {})

    @classmethod
    def replace(cls, payload: dict[str, Any], *, metadata: dict[str, Any] | None = None) -> "HookDecision":
        return cls(action=HOOK_REPLACE, payload=payload, metadata=metadata or {})

    @classmethod
    def block(cls, reason: str | None = None, *, metadata: dict[str, Any] | None = None) -> "HookDecision":
        return cls(action=HOOK_BLOCK, reason=reason, metadata=metadata or {})

    @classmethod
    def retry(cls, reason: str | None = None, *, metadata: dict[str, Any] | None = None) -> "HookDecision":
        return cls(action=HOOK_RETRY, reason=reason, metadata=metadata or {})

    @classmethod
    def fallback(cls, reason: str | None = None, *, metadata: dict[str, Any] | None = None) -> "HookDecision":
        return cls(action=HOOK_FALLBACK, reason=reason, metadata=metadata or {})


class HookManager:
    """Run hooks in list order while isolating observability hook failures."""

    def __init__(self, hooks: list[Callable[..., Any] | Any] | None = None):
        self.hooks = list(hooks or [])

    def run(self, context: HookContext) -> HookDecision:
        payload = dict(context.payload or {})
        hook_events: list[dict[str, Any]] = []
        metadata: dict[str, Any] = {}

        for hook in self.hooks:
            hook_name = getattr(hook, "__name__", hook.__class__.__name__)
            try:
                raw = self._call_hook(hook, context)
                if inspect.isawaitable(raw):
                    raw = self._run_awaitable(raw)
                decision = self._normalize(raw)
            except Exception as exc:
                hook_events.append({
                    "phase": context.phase,
                    "hook": hook_name,
                    "action": "error",
                    "error": str(exc),
                })
                continue

            if decision.metadata:
                metadata.update(decision.metadata)

            if decision.action == HOOK_REPLACE:
                payload = dict(decision.payload or {})
                context.payload = payload
                hook_events.append({
                    "phase": context.phase,
                    "hook": hook_name,
                    "action": HOOK_REPLACE,
                })
                continue

            if decision.action == HOOK_METADATA:
                hook_events.append({
                    "phase": context.phase,
                    "hook": hook_name,
                    "action": HOOK_METADATA,
                })
                continue

            if decision.action != HOOK_CONTINUE:
                decision.payload = payload
                decision.metadata = {**metadata, **decision.metadata, "hook_events": hook_events}
                hook_events.append({
                    "phase": context.phase,
                    "hook": hook_name,
                    "action": decision.action,
                    "reason": decision.reason,
                })
                decision.metadata["hook_events"] = hook_events
                return decision

        return HookDecision(
            action=HOOK_CONTINUE,
            payload=payload,
            metadata={**metadata, "hook_events": hook_events} if hook_events else metadata,
        )

    @staticmethod
    def _call_hook(hook: Callable[..., Any] | Any, context: HookContext) -> Any:
        method = getattr(hook, context.phase, None)
        if callable(method):
            return method(context)
        if callable(hook):
            return hook(context)
        return None

    @staticmethod
    def _run_awaitable(awaitable: Awaitable[Any]) -> Any:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(awaitable)

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(asyncio.run, awaitable)
            return future.result()

    @staticmethod
    def _normalize(raw: Any) -> HookDecision:
        if raw is None:
            return HookDecision.continue_()
        if isinstance(raw, HookDecision):
            return raw
        if isinstance(raw, bool):
            return HookDecision.continue_() if raw else HookDecision.block("hook returned False")
        if isinstance(raw, str):
            return HookDecision.block(raw)
        if isinstance(raw, dict):
            if raw.get("allowed") is False:
                return HookDecision.block(raw.get("reason"), metadata=raw.get("metadata"))
            action = raw.get("action")
            if action:
                return HookDecision(
                    action=str(action),
                    payload=raw.get("payload"),
                    reason=raw.get("reason"),
                    metadata=raw.get("metadata") or {},
                )
            if "payload" in raw:
                return HookDecision.replace(raw["payload"], metadata=raw.get("metadata"))
            return HookDecision.continue_(metadata=raw.get("metadata"))
        return HookDecision.continue_()
