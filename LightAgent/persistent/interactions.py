"""Durable interaction correlation; presentation and approval policy belong to the host."""
from __future__ import annotations

import math
import time
from ..security import ApprovalToken, SecurityContext, canonical_digest
from .execution_contracts import require_attempt
from .redaction import contains_secret
from .store import StateConflict, dumps

INTERACTION_SCHEMA_VERSION = 1


class InteractionRequests:
    def __init__(self, store):
        self.store = store

    def request(self, task_id, *, attempt_id, epoch, kind, payload, ttl_seconds=300, idempotency_key):
        if kind not in ("question", "plan_review", "approval"):
            raise ValueError("unsupported interaction kind")
        if not isinstance(payload, dict) or len(dumps(payload).encode()) > 65536 or contains_secret(dumps(payload)):
            raise ValueError("interaction payload is invalid, too large, or contains a known credential")
        if type(ttl_seconds) not in (int, float) or not math.isfinite(ttl_seconds) or not 0 < ttl_seconds <= 86400:
            raise ValueError("invalid interaction expiry")
        if not isinstance(idempotency_key, str) or not 1 <= len(idempotency_key) <= 256:
            raise ValueError("invalid interaction idempotency key")
        if kind == "approval" and (set(payload) != {"operation", "arguments", "resource"}
                or not isinstance(payload["operation"], str) or not payload["operation"]
                or not isinstance(payload["arguments"], dict)):
            raise ValueError("approval must bind an exact operation, arguments, and resource")
        identity = canonical_digest(dict(task=task_id, key=idempotency_key))
        fingerprint = canonical_digest(dict(attempt_id=attempt_id, epoch=epoch, kind=kind,
                                            payload=payload, ttl_seconds=ttl_seconds))
        with self.store.transaction() as db:
            previous = self.store.get("interaction", identity, db)
            if previous:
                if previous["fingerprint"] != fingerprint:
                    raise StateConflict("interaction key reused for a different request")
                return previous
            task, _ = require_attempt(self.store, task_id, attempt_id, epoch, db, now=time.time())
            context = SecurityContext.from_dict(task["security"]).narrow(task_id=task_id, attempt_id=attempt_id)
            value = self.store.put("interaction", dict(id=identity, agent=task_id,
                schema_version=INTERACTION_SCHEMA_VERSION, attempt_id=attempt_id, epoch=epoch,
                kind=kind, payload=payload, context=context.to_dict(), fingerprint=fingerprint,
                status="pending", expires_at=time.time() + ttl_seconds), db)
            self.store.event(task_id, "interaction.requested", {"request_id": identity, "kind": kind}, db)
            return value

    def respond(self, request_id, answer, *, context, approval_token=None):
        if not isinstance(context, SecurityContext):
            raise PermissionError("host response SecurityContext is required")
        if len(dumps(answer).encode()) > 65536 or contains_secret(dumps(answer)):
            raise ValueError("response exceeds its budget or contains a known credential")
        failure = None
        with self.store.transaction() as db:
            request = self.store.get("interaction", request_id, db)
            if request is None:
                raise KeyError(request_id)
            expected = SecurityContext.from_dict(request["context"])
            fields = ("user_id", "tenant_id", "project_id", "task_id", "attempt_id", "policy_version")
            if any(getattr(context, key) != getattr(expected, key) for key in fields) or context.expired:
                raise PermissionError("response identity/policy does not match the interaction")
            if request["status"] == "responded":
                if request["answer"] != answer:
                    raise StateConflict("interaction already has another response")
                return request
            if request["status"] != "pending":
                raise StateConflict("interaction is no longer pending")
            task = self.store.get("agent", request["agent"], db)
            if time.time() >= request["expires_at"]:
                request["status"], failure = "expired", "interaction has expired"
            elif (not task or task["epoch"] != request["epoch"] or task["attempt_id"] != request["attempt_id"]
                    or task["desired"] == "cancelled" or task["status"] != "running"):
                request["status"], failure = "cancelled", "interaction belongs to a stale attempt"
            else:
                if request["kind"] == "approval":
                    if type(answer) is not bool:
                        raise ValueError("approval response must be a boolean")
                    if answer:
                        if not isinstance(approval_token, ApprovalToken):
                            raise PermissionError("positive approval requires an exact host ApprovalToken")
                        payload = request["payload"]
                        approval_token.verify(payload["operation"], payload["arguments"], expected,
                                              resource=payload["resource"], consume=False)
                        if not approval_token.reusable:
                            self.store.put("consumed_approval", dict(id=approval_token.token_id,
                                agent=request["agent"], request_id=request_id), db)
                        request["approval_token_id"] = approval_token.token_id
                request.update(status="responded", answer=answer, responded_at=time.time())
            value = self.store.put("interaction", request, db)
            self.store.event(request["agent"], "interaction." + request["status"], {"request_id": request_id}, db)
        if failure:
            raise StateConflict(failure)
        return value

    def get(self, request_id):
        value = self.store.get("interaction", request_id)
        if value is None:
            raise KeyError(request_id)
        return value
