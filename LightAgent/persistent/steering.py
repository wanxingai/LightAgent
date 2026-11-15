"""Compatibility names for the explicitly registered research extension."""
from ..extensions import legacy_export

__all__ = ["dispatch"]  # noqa: F822 - provided by __getattr__


def __getattr__(name):
    if name in ("dispatch", "_deliver", "_deliver_bound"):
        return legacy_export("steering." + name)
    raise AttributeError(name)
