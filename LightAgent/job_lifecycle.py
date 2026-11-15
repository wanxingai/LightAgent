"""Shared Job transitions; storage and runners remain host-owned adapters."""

from copy import deepcopy
from datetime import datetime, timezone
import math
import time


class JobConflict(RuntimeError):
    pass


ALIASES = {"pending": "queued", "success": "completed"}
ACTIVE = frozenset({"queued", "launching", "running"})
TRANSITIONS = {
    "queued": {"launching", "running", "cancelled", "interrupted"},
    "launching": {"running", "failed", "cancelled", "uncertain", "interrupted"},
    "running": {"completed", "failed", "cancelled", "timed_out", "uncertain", "interrupted"},
    "interrupted": {"queued"},
    "uncertain": {"completed", "failed", "cancelled"},
}


def status_of(record):
    value = record["status"]
    value = getattr(value, "value", value)
    return ALIASES.get(value, value)


def positive_seconds(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        raise ValueError("lease_seconds must be finite and positive")
    return value


def identity(record):
    """Read old nonce/lease fields without rewriting historical records."""
    return (record.get("attempt_id") or record.get("nonce"),
            record.get("epoch", record.get("lease_epoch", 0)))


def expired(record, *, now=None):
    deadline = record.get("lease_until", record.get("lease_expires_at"))
    if deadline is None:
        return False
    if isinstance(deadline, str):
        parsed = datetime.fromisoformat(deadline.replace("Z", "+00:00"))
        deadline = parsed.replace(tzinfo=parsed.tzinfo or timezone.utc).timestamp()
    return (time.time() if now is None else now) >= deadline


def require_attempt(record, expected, *, live=False):
    if identity(record) != expected:
        raise JobConflict("job attempt/epoch is stale")
    if live and (status_of(record) not in ACTIVE or expired(record)):
        raise JobConflict("job attempt is no longer active or its lease expired")


def transition(record, target, *, expected=None, reconcile=False, resume=False, **updates):
    """Return a fenced replacement of the *existing* authoritative record."""
    source = status_of(record)
    canonical = ALIASES.get(target, target)
    if expected is not None:
        require_attempt(record, expected)
    if canonical not in TRANSITIONS.get(source, ()):
        raise JobConflict(f"invalid Job transition: {source} -> {canonical}")
    if source == "uncertain" and not reconcile:
        raise JobConflict("uncertain jobs require explicit host reconciliation")
    if source == "interrupted" and not resume:
        raise JobConflict("interrupted jobs require explicit host resume")
    value = deepcopy(record)
    value.update(updates)
    value["status"] = target
    return value


def view(record):
    attempt, epoch = identity(record)
    return dict(status=status_of(record), attempt_id=attempt, epoch=epoch,
                owner_id=record.get("owner_id", record.get("owner_agent_id", record.get("agent"))),
                parent_id=record.get("parent_job_id"),
                output_cursor=record.get("output_cursor", len(record["output"]) if "output" in record else None),
                runner_stopped=record.get("runner_stopped"),
                reconciliation_required=status_of(record) in {"uncertain", "interrupted"}
                    or (status_of(record) == "cancelled" and record.get("runner_stopped") is not True))
