"""Versioned host execution requirements, independent of any task domain."""
from dataclasses import asdict, dataclass
import inspect
import json
import math

from ..backends.base import BackendProbe
from ..security import canonical_digest
from .redaction import contains_secret
from .store import dumps, StateConflict

EXECUTION_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class ExecutionLimits:
    timeout: float = 300
    lease_seconds: float = 30
    max_events: int = 10000
    max_records: int = 10000
    max_storage_bytes: int = 512 * 1024 * 1024
    max_concurrent_jobs: int = 2

    def __post_init__(self):
        for key in ("timeout", "lease_seconds"):
            value = getattr(self, key)
            if type(value) not in (int, float) or not math.isfinite(value) or not 0 < value <= 86400:
                raise ValueError("execution deadlines must be finite and within one day")
        for key in ("max_events", "max_records", "max_storage_bytes", "max_concurrent_jobs"):
            if type(getattr(self, key)) is not int or getattr(self, key) < 1:
                raise ValueError("execution capacities must be positive integers")


@dataclass(frozen=True)
class ExecutionRequirements:
    isolation: str = "none"
    resume: bool = False
    cancel: bool = True

    def __post_init__(self):
        if self.isolation not in ("none", "sandbox", "docker"):
            raise ValueError("unsupported execution isolation requirement")
        if type(self.resume) is not bool or type(self.cancel) is not bool:
            raise ValueError("capability requirements must be boolean")

    def verify(self, probe, context):
        if not isinstance(probe, BackendProbe):
            raise TypeError("backend must return a BackendProbe")
        capabilities = probe.capabilities
        if self.isolation == "docker" and capabilities.isolation != "docker":
            raise PermissionError("Docker-only execution cannot fall back to a host or CLI sandbox")
        if (self.isolation == "sandbox" or context.sandbox_required) and capabilities.isolation == "none":
            raise PermissionError("backend cannot enforce the required sandbox")
        if not context.network_allowed and not capabilities.network_control:
            raise PermissionError("backend cannot enforce the requested network restriction")
        if any(getattr(self, key) and not getattr(capabilities, key) for key in ("resume", "cancel")):
            raise PermissionError("backend lacks a required lifecycle capability")


def execution_profile(factory, probe, configuration):
    try:
        source = inspect.getsource(factory)
    except (OSError, TypeError):
        source = None
    value = dict(schema_version=EXECUTION_SCHEMA_VERSION, probe=asdict(probe),
                 factory=getattr(factory, "__module__", "") + "." + getattr(factory, "__qualname__", type(factory).__qualname__),
                 factory_digest=canonical_digest(source), configuration=configuration)
    if len(dumps(value).encode()) > 262144 or contains_secret(dumps(value)):
        raise ValueError("execution profile exceeds its budget or contains a credential")
    return json.loads(dumps(value))


def require_attempt(store, task_id, attempt_id, epoch, db, *, now):
    task = store.require_epoch(task_id, epoch, db)
    attempt = store.get("execution_attempt", attempt_id, db)
    if (not attempt or attempt["agent"] != task_id or attempt["epoch"] != epoch
            or attempt["status"] != "running" or task.get("attempt_id") != attempt_id
            or attempt["lease_until"] <= now or task["status"] != "running" or task["desired"] == "cancelled"):
        raise StateConflict("stale, expired, or terminal execution attempt")
    return task, attempt
