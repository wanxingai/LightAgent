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


@dataclass(frozen=True)
class PolicyHook:
    """Explicit hook policy for failures that must block protected operations."""

    handler: Callable[..., Any] | Any
    phases: set[str] | frozenset[str] | None = None
    failure_mode: str = "block"
    timeout: float | None = None
    name: str | None = None

    def __post_init__(self) -> None:
        if self.handler is None:
            raise ValueError("PolicyHook handler is required")
        if self.failure_mode not in {"block", "continue"}:
            raise ValueError("PolicyHook failure_mode must be 'block' or 'continue'")
        if self.timeout is not None:
            if isinstance(self.timeout, bool) or not isinstance(self.timeout, (int, float)) or self.timeout <= 0:
                raise ValueError("PolicyHook timeout must be a number greater than 0")
        if self.phases is not None:
            object.__setattr__(self, "phases", frozenset(str(phase) for phase in self.phases))


class HookManager:
    """Run hooks in list order while isolating observability hook failures."""

    def __init__(self, hooks: list[Callable[..., Any] | Any | PolicyHook] | None = None):
        self.hooks = list(hooks or [])

    def run(self, context: HookContext) -> HookDecision:
        payload = dict(context.payload or {})
        hook_events: list[dict[str, Any]] = []
        metadata: dict[str, Any] = {}

        for hook in self.hooks:
            policy = hook if isinstance(hook, PolicyHook) else None
            handler = policy.handler if policy else hook
            if policy and policy.phases is not None and context.phase not in policy.phases:
                continue
            hook_name = (policy.name if policy else None) or getattr(
                handler,
                "__name__",
                handler.__class__.__name__,
            )
            try:
                raw = self._invoke_hook(handler, context, policy.timeout if policy else None)
                decision = self._normalize(raw)
            except Exception as exc:
                failure_mode = policy.failure_mode if policy else "continue"
                error_event = {
                    "phase": context.phase,
                    "hook": hook_name,
                    "action": "error",
                    "error": str(exc),
                    "error_type": "timeout" if isinstance(exc, TimeoutError) else "exception",
                    "failure_mode": failure_mode,
                }
                hook_events.append(error_event)
                if failure_mode == "block":
                    return HookDecision.block(
                        f"Policy hook `{hook_name}` failed closed: {exc}",
                        metadata={
                            **metadata,
                            "policy_hook": hook_name,
                            "failure_mode": failure_mode,
                            "hook_events": hook_events,
                        },
                    )
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

    @classmethod
    def _invoke_hook(
            cls,
            hook: Callable[..., Any] | Any,
            context: HookContext,
            timeout: float | None,
    ) -> Any:
        if timeout is None:
            return cls._call_and_resolve(hook, context)

        isolated_context = HookContext(
            phase=context.phase,
            payload=dict(context.payload),
            trace_id=context.trace_id,
            parent_trace_id=context.parent_trace_id,
            run_id=context.run_id,
            run_group_id=context.run_group_id,
            user_id=context.user_id,
            agent_name=context.agent_name,
            flow_id=context.flow_id,
            step_name=context.step_name,
            metadata=dict(context.metadata),
        )
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        future = executor.submit(cls._call_and_resolve, hook, isolated_context)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError as exc:
            future.cancel()
            raise TimeoutError(f"hook timed out after {timeout:g}s") from exc
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

    @classmethod
    def _call_and_resolve(cls, hook: Callable[..., Any] | Any, context: HookContext) -> Any:
        raw = cls._call_hook(hook, context)
        if inspect.isawaitable(raw):
            return cls._run_awaitable(raw)
        return raw

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
