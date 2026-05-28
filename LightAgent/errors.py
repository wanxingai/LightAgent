#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
LightAgent error taxonomy and user-facing formatting helpers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LightAgentErrorInfo:
    code: str
    message: str
    guidance: str


class LightAgentError(Exception):
    """Catchable structured LightAgent exception."""

    def __init__(
            self,
            code: str,
            message: str | None = None,
            guidance: str | None = None,
            details: Any = None,
    ):
        info = ERROR_TAXONOMY.get(code, ERROR_TAXONOMY["LA-UNKNOWN"])
        self.code = info.code
        self.message = message or info.message
        self.guidance = guidance or info.guidance
        self.details = details
        super().__init__(self.__str__())

    def __str__(self) -> str:
        text = f"[{self.code}] {self.message} Guidance: {self.guidance}"
        if self.details is not None:
            text = f"{text} Details: {self.details}"
        return text


ERROR_TAXONOMY = {
    "LA-400": LightAgentErrorInfo(
        "LA-400",
        "Invalid request sent to the model provider.",
        "Check the request parameters, tool schema, message format, and model name.",
    ),
    "LA-401": LightAgentErrorInfo(
        "LA-401",
        "Authentication failed.",
        "Check that api_key or OPENAI_API_KEY is set and valid for the configured provider.",
    ),
    "LA-403": LightAgentErrorInfo(
        "LA-403",
        "The provider rejected this request because of permissions or policy.",
        "Check account permissions, model access, and provider-side safety or quota settings.",
    ),
    "LA-404": LightAgentErrorInfo(
        "LA-404",
        "The requested endpoint or model was not found.",
        "Check base_url and model. For OpenAI-compatible local servers, base_url should end at /v1.",
    ),
    "LA-408": LightAgentErrorInfo(
        "LA-408",
        "The model request timed out.",
        "Retry the request, reduce input size, or increase provider/client timeout settings.",
    ),
    "LA-413": LightAgentErrorInfo(
        "LA-413",
        "The request or response exceeded the provider limit.",
        "Reduce the prompt, history, tool output, or requested completion size.",
    ),
    "LA-429": LightAgentErrorInfo(
        "LA-429",
        "Rate limit or quota was exceeded.",
        "Wait before retrying, reduce concurrency, or check provider quota and billing status.",
    ),
    "LA-500": LightAgentErrorInfo(
        "LA-500",
        "The model provider returned a server error.",
        "Retry later or switch to another compatible provider endpoint.",
    ),
    "LA-503": LightAgentErrorInfo(
        "LA-503",
        "The model provider is temporarily unavailable.",
        "Retry later, reduce traffic, or use a fallback model/provider.",
    ),
    "LA-JSON": LightAgentErrorInfo(
        "LA-JSON",
        "A tool call argument could not be parsed as JSON.",
        "Check that the model returned valid tool-call JSON matching the registered tool schema.",
    ),
    "LA-TOOL": LightAgentErrorInfo(
        "LA-TOOL",
        "Tool execution failed.",
        "Check the tool implementation, required arguments, dependencies, and external service credentials.",
    ),
    "LA-GUARDRAIL": LightAgentErrorInfo(
        "LA-GUARDRAIL",
        "A configured guardrail blocked this operation.",
        "Review the configured input, tool, or output guardrail policy and adjust the request if appropriate.",
    ),
    "LA-UNKNOWN": LightAgentErrorInfo(
        "LA-UNKNOWN",
        "An unexpected LightAgent error occurred.",
        "Enable debug logging and inspect the original exception details.",
    ),
}


def classify_exception(exc: BaseException, default_code: str = "LA-UNKNOWN") -> LightAgentErrorInfo:
    """Classify common provider and runtime exceptions into stable LightAgent codes."""
    status_code = getattr(exc, "status_code", None)
    if status_code is None and getattr(exc, "response", None) is not None:
        status_code = getattr(exc.response, "status_code", None)

    if status_code in (400,):
        return ERROR_TAXONOMY["LA-400"]
    if status_code in (401,):
        return ERROR_TAXONOMY["LA-401"]
    if status_code in (403,):
        return ERROR_TAXONOMY["LA-403"]
    if status_code in (404,):
        return ERROR_TAXONOMY["LA-404"]
    if status_code in (408,):
        return ERROR_TAXONOMY["LA-408"]
    if status_code in (413,):
        return ERROR_TAXONOMY["LA-413"]
    if status_code in (429,):
        return ERROR_TAXONOMY["LA-429"]
    if status_code in (500, 502):
        return ERROR_TAXONOMY["LA-500"]
    if status_code in (503, 504):
        return ERROR_TAXONOMY["LA-503"]

    name = exc.__class__.__name__.lower()
    text = str(exc).lower()
    if "authentication" in name or "unauthorized" in text or "api key" in text:
        return ERROR_TAXONOMY["LA-401"]
    if "permission" in name or "forbidden" in text:
        return ERROR_TAXONOMY["LA-403"]
    if "notfound" in name or "not found" in text:
        return ERROR_TAXONOMY["LA-404"]
    if "timeout" in name or "timed out" in text:
        return ERROR_TAXONOMY["LA-408"]
    if "ratelimit" in name or "rate limit" in text or "quota" in text:
        return ERROR_TAXONOMY["LA-429"]
    if "context length" in text or "maximum context" in text or "too large" in text:
        return ERROR_TAXONOMY["LA-413"]

    return ERROR_TAXONOMY.get(default_code, ERROR_TAXONOMY["LA-UNKNOWN"])


def format_lightagent_error(exc: BaseException, action: str | None = None, default_code: str = "LA-UNKNOWN") -> str:
    """Return a concise user-facing error with a stable code and troubleshooting hint."""
    info = classify_exception(exc, default_code=default_code)
    prefix = f"[{info.code}] {info.message}"
    if action:
        prefix = f"{prefix} Action: {action}."
    return f"{prefix} Guidance: {info.guidance} Details: {exc}"


def format_error_code(code: str, details: Any = None) -> str:
    """Format a known LightAgent error code with optional details."""
    info = ERROR_TAXONOMY.get(code, ERROR_TAXONOMY["LA-UNKNOWN"])
    message = f"[{info.code}] {info.message} Guidance: {info.guidance}"
    if details is not None:
        message = f"{message} Details: {details}"
    return message
