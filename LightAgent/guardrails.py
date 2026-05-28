#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Lightweight guardrail primitives for input, tool-call, and output checks.
"""

from __future__ import annotations

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
