"""Compatibility entry for the old research-only AgentService name."""
from ..extensions import legacy_export


class AgentService:
    def __new__(cls, *args, **kwargs):
        return legacy_export("AgentService")(*args, **kwargs)


class ServiceStartupError(RuntimeError):
    """A durable submission exists even if detached startup is unconfirmed."""
