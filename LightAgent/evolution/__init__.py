"""Explicit legacy extension proxy; no research implementation in the core."""
from ..extensions import legacy_export


def __getattr__(name):
    if name == "AgentVersion":
        return legacy_export(name)
    raise AttributeError(name)
