"""Explicit host registration. Persisted records never select Python imports."""
from dataclasses import dataclass
from threading import RLock
from types import MappingProxyType
from typing import Callable, Mapping


class ExtensionRequired(RuntimeError):
    pass


@dataclass(frozen=True)
class Extension:
    name: str
    version: str
    exports: Mapping[str, object]
    persistent_run: Callable


_extensions = {}
_lock = RLock()


def register_extension(name, *, version, exports, persistent_run):
    if not isinstance(name, str) or not name.isidentifier() or not version or not callable(persistent_run):
        raise ValueError("invalid extension registration")
    extension = Extension(name, str(version), MappingProxyType(dict(exports)), persistent_run)
    with _lock:
        previous = _extensions.get(name)
        if previous is not None and previous != extension:
            raise ValueError("extension already registered; restart with the reviewed configuration")
        _extensions[name] = extension
    return extension


def require_extension(name):
    with _lock:
        extension = _extensions.get(name)
    if extension is None:
        raise ExtensionRequired(
            "Research moved out of the core in v1.0.0. Use LightResearch.ResearchService, "
            "or explicitly call LightResearch.enable_legacy_api() before mode='persistent'. "
            "This mode retains its research semantics; use ExecutionService for ordinary tasks."
        )
    return extension


def legacy_export(name):
    return require_extension("research").exports[name]
