#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Lightweight guardrail primitives for input, tool-call, and output checks.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class GuardrailDecision:
    """Decision returned by an input, tool, or output guardrail."""

    allowed: bool
    reason: str | None = None
    value: Any = None


class GuardrailManager:
    """Runs configured guardrails while keeping the default runtime unchanged."""

    def __init__(
            self,
            *,
            input_guardrails: list[Callable[..., Any]] | None = None,
            tool_guardrails: list[Callable[..., Any]] | None = None,
            output_guardrails: list[Callable[..., Any]] | None = None,
    ):
        self.input_guardrails = input_guardrails or []
        self.tool_guardrails = tool_guardrails or []
        self.output_guardrails = output_guardrails or []

    def check_input(self, query: str, context: dict[str, Any] | None = None) -> GuardrailDecision:
        return self._run_guardrails(self.input_guardrails, query, context or {})

    def check_tool(
            self,
            tool_name: str,
            arguments: dict[str, Any],
            context: dict[str, Any] | None = None,
    ) -> GuardrailDecision:
        payload = {"tool_name": tool_name, "arguments": arguments}
        return self._run_guardrails(self.tool_guardrails, payload, context or {})

    def check_output(self, output: str, context: dict[str, Any] | None = None) -> GuardrailDecision:
        return self._run_guardrails(self.output_guardrails, output, context or {})

    def _run_guardrails(
            self,
            guardrails: list[Callable[..., Any]],
            value: Any,
            context: dict[str, Any],
    ) -> GuardrailDecision:
        current_value = value
        for guardrail in guardrails:
            raw_decision = guardrail(current_value, context)
            decision = self._coerce_decision(raw_decision, current_value)
            if not decision.allowed:
                return decision
            if decision.value is not None:
                current_value = decision.value
        return GuardrailDecision(allowed=True, value=current_value)

    @staticmethod
    def _coerce_decision(raw_decision: Any, current_value: Any) -> GuardrailDecision:
        if isinstance(raw_decision, GuardrailDecision):
            return raw_decision
        if raw_decision is None or raw_decision is True:
            return GuardrailDecision(allowed=True, value=current_value)
        if raw_decision is False:
            return GuardrailDecision(allowed=False, reason="Guardrail blocked this operation.")
        if isinstance(raw_decision, str):
            return GuardrailDecision(allowed=False, reason=raw_decision)
        if isinstance(raw_decision, dict):
            return GuardrailDecision(
                allowed=bool(raw_decision.get("allowed", True)),
                reason=raw_decision.get("reason"),
                value=raw_decision.get("value", current_value),
            )
        return GuardrailDecision(allowed=True, value=raw_decision)


DEFAULT_PRIVACY_PATTERNS = (
    r"\b\d{3}-\d{2}-\d{4}\b",
    r"\b(?:\d[ -]*?){13,19}\b",
    r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
    r"\b(?:api[_-]?key|secret|password|token)\s*[:=]\s*\S+",
)


def privacy_input_guardrail(
        patterns: list[str] | tuple[str, ...] | None = None,
        *,
        reason: str = "privacy-sensitive input detected",
) -> Callable[[str, dict[str, Any]], GuardrailDecision]:
    """Return an input guardrail that blocks common private data patterns."""
    compiled = [re.compile(pattern, flags=re.IGNORECASE) for pattern in (patterns or DEFAULT_PRIVACY_PATTERNS)]

    def guardrail(query: str, context: dict[str, Any]) -> GuardrailDecision:
        text = "" if query is None else str(query)
        if any(pattern.search(text) for pattern in compiled):
            return GuardrailDecision(False, reason=reason)
        return GuardrailDecision(True, value=query)

    return guardrail


def sensitive_tool_confirmation_guardrail(
        tool_names: list[str] | tuple[str, ...],
        *,
        approved: bool = False,
        reason: str = "tool call requires approval",
) -> Callable[[dict[str, Any], dict[str, Any]], GuardrailDecision]:
    """Return a tool guardrail that blocks selected tools until approved."""
    sensitive = {str(name) for name in tool_names}

    def guardrail(tool_call: dict[str, Any], context: dict[str, Any]) -> GuardrailDecision:
        if tool_call.get("tool_name") in sensitive and not approved:
            return GuardrailDecision(False, reason=reason)
        return GuardrailDecision(True, value=tool_call)

    return guardrail


def high_risk_parameter_guardrail(
        rules: dict[str, Callable[[Any], bool] | list[str] | tuple[str, ...]],
        *,
        reason: str = "high-risk tool parameter blocked",
) -> Callable[[dict[str, Any], dict[str, Any]], GuardrailDecision]:
    """Return a tool guardrail for validating sensitive argument values."""

    def guardrail(tool_call: dict[str, Any], context: dict[str, Any]) -> GuardrailDecision:
        arguments = tool_call.get("arguments") or {}
        for name, rule in rules.items():
            value = arguments.get(name)
            if callable(rule) and not rule(value):
                return GuardrailDecision(False, reason=f"{reason}: {name}")
            if isinstance(rule, (list, tuple)) and value not in rule:
                return GuardrailDecision(False, reason=f"{reason}: {name}")
        return GuardrailDecision(True, value=tool_call)

    return guardrail


def output_redaction_guardrail(
        patterns: list[str] | tuple[str, ...] | None = None,
        *,
        replacement: str = "[redacted]",
) -> Callable[[str, dict[str, Any]], GuardrailDecision]:
    """Return an output guardrail that redacts common sensitive patterns."""
    compiled = [re.compile(pattern, flags=re.IGNORECASE) for pattern in (patterns or DEFAULT_PRIVACY_PATTERNS)]

    def guardrail(output: str, context: dict[str, Any]) -> GuardrailDecision:
        text = "" if output is None else str(output)
        for pattern in compiled:
            text = pattern.sub(replacement, text)
        return GuardrailDecision(True, value=text)

    return guardrail
