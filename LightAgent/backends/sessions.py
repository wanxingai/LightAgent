"""Host-owned session bindings and POSIX locks shared across backend instances.

This registry is not a task queue or a replacement for SessionStore. It binds
opaque engine IDs before history can be loaded. Keep it outside worker roots.
"""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import stat

from .base import BackendError


def session_binding(workspace, context, configuration):
    """Exclude per-turn identity/deadlines but bind authority and history scope."""
    return {
        "workspace": str(Path(workspace).resolve(strict=True)),
        "identity": {key: getattr(context, key) for key in
                     ("user_id", "tenant_id", "project_id", "agent_id", "session_id")},
        "permissions": context.to_dict()["permissions"],
        "resources": sorted(context.resources),
        "network_allowed": context.network_allowed,
        "sandbox_required": context.sandbox_required,
        "policy_version": context.policy_version,
        "configuration": configuration,
    }


class BackendSessionStore:
    """Single-host metadata, protected by nonblocking OS locks, not PID leases.

    All callers coordinating the same engine must use the same state directory.
    Locks survive threads/instances and are released by the OS on process exit.
    Binding records survive restarts; unknown Codex IDs are never auto-imported.
    """

    def __init__(self, directory=None):
        self.directory = Path(directory) if directory is not None else (
            Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
            / "lightagent" / "backends"
        )
        self.directory = self.directory.absolute()

    def _prepare(self):
        if os.name != "posix":
            raise BackendError("backend session locks currently require POSIX")
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        info = self.directory.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise BackendError("backend state directory must be owner-only (0700) and not a symlink")

    @contextmanager
    def lock(self, namespace, key):
        self._prepare()
        import fcntl
        digest = hashlib.sha256(f"{namespace}\0{key}".encode()).hexdigest()
        fd = os.open(self.directory / (digest + ".lock"),
                     os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        try:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise BackendError(f"{namespace} is busy; concurrent execution is not allowed") from exc
            yield
        finally:
            os.close(fd)

    def _connect(self):
        self._prepare()
        path = self.directory / "sessions.sqlite3"
        fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        os.close(fd)
        connection = sqlite3.connect(path, timeout=5)
        version = connection.execute("PRAGMA user_version").fetchone()[0]
        if version not in (0, 1):
            connection.close()
            raise BackendError("unsupported backend session registry schema")
        connection.execute("CREATE TABLE IF NOT EXISTS bindings "
                           "(namespace TEXT, session_id TEXT, binding TEXT NOT NULL, "
                           "PRIMARY KEY(namespace, session_id))")
        connection.execute("PRAGMA user_version=1")
        return connection

    @contextmanager
    def claim(self, namespace, session_id, binding, *, create=False):
        if not isinstance(session_id, str) or not session_id or len(session_id) > 256:
            raise ValueError("invalid backend session ID")
        with self.lock(namespace, session_id):
            serialized = json.dumps(binding, sort_keys=True, separators=(",", ":"))
            connection = self._connect()
            try:
                with connection:
                    row = connection.execute(
                        "SELECT binding FROM bindings WHERE namespace=? AND session_id=?",
                        (namespace, session_id),
                    ).fetchone()
                    if row is None:
                        if not create:
                            raise BackendError("unknown backend session; only sessions created by this registry can resume")
                        connection.execute("INSERT INTO bindings VALUES (?, ?, ?)",
                                           (namespace, session_id, serialized))
                    elif row[0] != serialized:
                        raise BackendError("session binding mismatch: workspace, identity, permissions or configuration changed")
            finally:
                connection.close()
            yield row is None
