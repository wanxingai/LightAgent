#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Human approval and feedback primitives for high-impact agent actions."""

from __future__ import annotations

import concurrent.futures
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from .hooks import HookContext, HookDecision


APPROVAL_PENDING = "pending"
APPROVAL_APPROVE = "approve"
APPROVAL_REJECT = "reject"
APPROVAL_EDIT = "edit"
APPROVAL_RESPOND = "respond"
APPROVAL_ACTIONS = {
    APPROVAL_PENDING,
    APPROVAL_APPROVE,
    APPROVAL_REJECT,
    APPROVAL_EDIT,
    APPROVAL_RESPOND,
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ApprovalRequest:
    """Serializable request sent to a human review system."""

    action: str
    request_id: str = field(default_factory=lambda: uuid4().hex)
    run_id: str | None = None
    trace_id: str | None = None
    action_name: str | None = None
    tool_name: str | None = None
    arguments: dict[str, Any] = field(default_factory=dict)
    source_agent: str | None = None
    target_agent: str | None = None
    allowed_decisions: tuple[str, ...] = (
        APPROVAL_APPROVE,
        APPROVAL_REJECT,
        APPROVAL_EDIT,
    )
    reviewer_metadata: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["allowed_decisions"] = list(self.allowed_decisions)
        return data


@dataclass
class ApprovalDecision:
    """Review decision for an ApprovalRequest."""

    action: str
    request_id: str | None = None
    reason: str | None = None
    arguments: dict[str, Any] | None = None
    response: str | None = None
    reviewer_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    decided_at: str = field(default_factory=_now)

    def __post_init__(self) -> None:
        if self.action not in APPROVAL_ACTIONS:
            raise ValueError(f"unsupported approval action: {self.action}")

    @property
    def approved(self) -> bool:
        return self.action in {APPROVAL_APPROVE, APPROVAL_EDIT, APPROVAL_RESPOND}

    @classmethod
    def approve(cls, **kwargs: Any) -> "ApprovalDecision":
        return cls(action=APPROVAL_APPROVE, **kwargs)

    @classmethod
    def reject(cls, reason: str | None = None, **kwargs: Any) -> "ApprovalDecision":
        return cls(action=APPROVAL_REJECT, reason=reason, **kwargs)

    @classmethod
    def edit(cls, arguments: dict[str, Any], **kwargs: Any) -> "ApprovalDecision":
        return cls(action=APPROVAL_EDIT, arguments=arguments, **kwargs)

    @classmethod
    def respond(cls, response: str, **kwargs: Any) -> "ApprovalDecision":
        return cls(action=APPROVAL_RESPOND, response=response, **kwargs)

    @classmethod
    def pending(cls, reason: str | None = None, **kwargs: Any) -> "ApprovalDecision":
        return cls(action=APPROVAL_PENDING, reason=reason, **kwargs)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class HumanFeedback:
    """Human-on-the-loop annotation attached to a trace."""

    trace_id: str
    rating: float | None = None
    label: str | None = None
    comment: str | None = None
    reviewer_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    feedback_id: str = field(default_factory=lambda: uuid4().hex)
    created_at: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class InMemoryReviewStore:
    """In-memory request, decision, batch, and feedback store."""

    def __init__(self):
        self.requests: dict[str, ApprovalRequest] = {}
        self.decisions: dict[str, ApprovalDecision] = {}
        self.feedback: list[HumanFeedback] = []

    def create_request(self, request: ApprovalRequest) -> ApprovalRequest:
        self.requests[request.request_id] = request
        return request

    def create_batch(self, requests: list[ApprovalRequest]) -> list[ApprovalRequest]:
        return [self.create_request(request) for request in requests]

    def get_request(self, request_id: str) -> ApprovalRequest | None:
        return self.requests.get(request_id)

    def resolve(self, request_id: str, decision: ApprovalDecision) -> ApprovalDecision:
        if request_id not in self.requests:
            raise KeyError(f"approval request {request_id!r} not found")
        decision.request_id = request_id
        self.decisions[request_id] = decision
        return decision

    def resolve_batch(
            self,
            decisions: dict[str, ApprovalDecision],
    ) -> dict[str, ApprovalDecision]:
        return {
            request_id: self.resolve(request_id, decision)
            for request_id, decision in decisions.items()
        }

    def get_decision(self, request_id: str) -> ApprovalDecision | None:
        return self.decisions.get(request_id)

    def list_pending(self) -> list[ApprovalRequest]:
        return [
            request
            for request_id, request in self.requests.items()
            if request_id not in self.decisions
        ]

    def add_feedback(self, feedback: HumanFeedback) -> HumanFeedback:
        self.feedback.append(feedback)
        return feedback

    def list_feedback(self, trace_id: str | None = None) -> list[HumanFeedback]:
        if trace_id is None:
            return list(self.feedback)
        return [item for item in self.feedback if item.trace_id == trace_id]


class JsonReviewStore(InMemoryReviewStore):
    """Small durable JSON store for delayed approvals and trace feedback."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        super().__init__()
        self._load()

    def create_request(self, request: ApprovalRequest) -> ApprovalRequest:
        value = super().create_request(request)
        self._save()
        return value

    def resolve(self, request_id: str, decision: ApprovalDecision) -> ApprovalDecision:
        value = super().resolve(request_id, decision)
        self._save()
        return value

    def add_feedback(self, feedback: HumanFeedback) -> HumanFeedback:
        value = super().add_feedback(feedback)
        self._save()
        return value

    def _load(self) -> None:
        if not self.path.exists():
            return
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        self.requests = {
            item["request_id"]: ApprovalRequest(
                **{**item, "allowed_decisions": tuple(item.get("allowed_decisions", ()))}
            )
            for item in payload.get("requests", [])
        }
        self.decisions = {
            item["request_id"]: ApprovalDecision(**item)
            for item in payload.get("decisions", [])
        }
        self.feedback = [HumanFeedback(**item) for item in payload.get("feedback", [])]

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "requests": [request.to_dict() for request in self.requests.values()],
            "decisions": [decision.to_dict() for decision in self.decisions.values()],
            "feedback": [feedback.to_dict() for feedback in self.feedback],
        }
        temporary = self.path.with_suffix(f"{self.path.suffix}.tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        temporary.replace(self.path)


class HumanApprovalHook:
    """Fail-closed hook for selected tools and handoffs.

    Without a synchronous reviewer, the hook stores a pending request and blocks
    the action. Resolve the request, then rerun with approval_id=request_id.
    """

    def __init__(
            self,
            *,
            store: InMemoryReviewStore | None = None,
            reviewer: Callable[[ApprovalRequest], Any] | None = None,
            tools: set[str] | None = None,
            phases: set[str] | None = None,
            timeout: float | None = None,
    ):
        if timeout is not None and timeout <= 0:
            raise ValueError("timeout must be greater than 0")
        self.store = store if store is not None else InMemoryReviewStore()
        self.reviewer = reviewer
        self.tools = set(tools) if tools is not None else None
        self.phases = (
            set(phases)
            if phases is not None
            else {"before_tool_call", "on_handoff"}
        )
        self.timeout = timeout

    def __call__(self, context: HookContext) -> HookDecision | None:
        if context.phase not in self.phases:
            return None
        if context.phase == "before_tool_call":
            tool_name = str(context.payload.get("tool_name") or "")
            if self.tools is not None and tool_name not in self.tools:
                return None

        approval_id = context.metadata.get("approval_id")
        if approval_id:
            previous_request = self.store.get_request(str(approval_id))
            existing = self.store.get_decision(str(approval_id))
            if previous_request is not None and existing is not None and self._matches(previous_request, context):
                return self._hook_decision(existing, context, reused=True)
            if previous_request is not None and existing is not None:
                return HookDecision.block(
                    "approval does not match the current action",
                    metadata={
                        "approval_request_id": str(approval_id),
                        "review_events": [{
                            "type": "approval_rejected",
                            "request_id": str(approval_id),
                            "phase": context.phase,
                            "reason": "approval context mismatch",
                            "reused": True,
                        }],
                    },
                )
            return HookDecision.block(
                "approval request not found or unresolved",
                metadata={
                    "approval_request_id": str(approval_id),
                    "review_events": [{
                        "type": "approval_required",
                        "request_id": str(approval_id),
                        "phase": context.phase,
                        "reason": "approval request not found or unresolved",
                        "reused": True,
                    }],
                },
            )

        request = self._build_request(context)
        self.store.create_request(request)
        if self.reviewer is None:
            decision = ApprovalDecision.pending(
                "human approval required",
                request_id=request.request_id,
            )
            return self._hook_decision(decision, context)

        try:
            raw = self._call_reviewer(request)
            decision = self._normalize_decision(raw, request.request_id)
        except Exception as exc:
            decision = ApprovalDecision.reject(
                f"approval reviewer failed: {exc}",
                request_id=request.request_id,
            )
        self.store.resolve(request.request_id, decision)
        return self._hook_decision(decision, context)

    def _call_reviewer(self, request: ApprovalRequest) -> Any:
        if self.timeout is None:
            return self.reviewer(request)
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        future = executor.submit(self.reviewer, request)
        try:
            return future.result(timeout=self.timeout)
        except concurrent.futures.TimeoutError as exc:
            future.cancel()
            raise TimeoutError(f"approval timed out after {self.timeout:g}s") from exc
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

    @staticmethod
    def _normalize_decision(raw: Any, request_id: str) -> ApprovalDecision:
        if isinstance(raw, ApprovalDecision):
            raw.request_id = request_id
            return raw
        if raw is True or raw is None:
            return ApprovalDecision.approve(request_id=request_id)
        if raw is False:
            return ApprovalDecision.reject("human reviewer rejected action", request_id=request_id)
        if isinstance(raw, str):
            return ApprovalDecision.reject(raw, request_id=request_id)
        if isinstance(raw, dict):
            action = raw.get("action")
            if action is None:
                action = APPROVAL_APPROVE if raw.get("approved", raw.get("allowed", False)) else APPROVAL_REJECT
            return ApprovalDecision(
                action=str(action),
                request_id=request_id,
                reason=raw.get("reason"),
                arguments=raw.get("arguments"),
                response=raw.get("response"),
                reviewer_id=raw.get("reviewer_id"),
                metadata=raw.get("metadata") or {},
            )
        return ApprovalDecision.reject("unsupported approval decision", request_id=request_id)

    def _build_request(self, context: HookContext) -> ApprovalRequest:
        payload = dict(context.payload)
        arguments = dict(payload.get("arguments") or {})
        if context.phase == "on_handoff" and payload.get("query") is not None:
            arguments["query"] = payload["query"]
        return ApprovalRequest(
            action=context.phase,
            run_id=context.run_id,
            trace_id=context.trace_id,
            action_name=str(payload.get("action_name") or context.phase),
            tool_name=payload.get("tool_name"),
            arguments=arguments,
            source_agent=payload.get("source_agent") or context.agent_name,
            target_agent=payload.get("target_agent"),
            reviewer_metadata={"user_id": context.user_id},
            metadata={
                "flow_id": context.flow_id,
                "step_name": context.step_name,
                "run_group_id": context.run_group_id,
            },
        )

    @staticmethod
    def _matches(request: ApprovalRequest, context: HookContext) -> bool:
        payload = dict(context.payload)
        arguments = dict(payload.get("arguments") or {})
        if context.phase == "on_handoff" and payload.get("query") is not None:
            arguments["query"] = payload["query"]
        return (
            request.action == context.phase
            and request.tool_name == payload.get("tool_name")
            and request.arguments == arguments
            and request.source_agent == (payload.get("source_agent") or context.agent_name)
            and request.target_agent == payload.get("target_agent")
            and request.reviewer_metadata.get("user_id") == context.user_id
        )

    @staticmethod
    def _hook_decision(
            decision: ApprovalDecision,
            context: HookContext,
            *,
            reused: bool = False,
    ) -> HookDecision:
        event_type = (
            "approval_required"
            if decision.action == APPROVAL_PENDING
            else f"approval_{decision.action}"
        )
        event = {
            "type": event_type,
            "request_id": decision.request_id,
            "phase": context.phase,
            "tool_name": context.payload.get("tool_name"),
            "source_agent": context.payload.get("source_agent") or context.agent_name,
            "target_agent": context.payload.get("target_agent"),
            "reason": decision.reason,
            "reviewer_id": decision.reviewer_id,
            "reused": reused,
        }
        metadata = {
            "approval_request_id": decision.request_id,
            "review_events": [event],
        }
        if decision.action == APPROVAL_APPROVE:
            return HookDecision.continue_(metadata=metadata)
        if decision.action == APPROVAL_EDIT:
            payload = dict(context.payload)
            if context.phase == "before_tool_call":
                payload["arguments"] = dict(decision.arguments or {})
            else:
                payload.update(decision.arguments or {})
            return HookDecision.replace(payload, metadata=metadata)
        if decision.action == APPROVAL_RESPOND:
            return HookDecision.block(decision.response or "action replaced by human response", metadata=metadata)
        return HookDecision.block(
            decision.reason or f"approval {decision.action}",
            metadata=metadata,
        )
