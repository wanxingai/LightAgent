"""Opt-in workspace tools. A cwd is never treated as a security sandbox."""

from __future__ import annotations

import hashlib
import errno
import math
import os
from pathlib import Path
import re
import selectors
import shlex
import shutil
import stat
import subprocess
import threading
import time
from typing import Protocol
from uuid import uuid4

from .backends.base import BackendError
from .backends.process import terminate_group
from .cancellation import CancellationToken
from .capabilities import CapabilityRisk, CapabilitySpec
from .security import CapabilityGate, SecurityContext


class WorkspaceSession(Protocol):
    def shell(self, command: str, timeout: float = 60) -> dict: ...
    def edit_file(self, path: str, new_text: str, old_text: str | None = None,
                  expected_sha256: str | None = None) -> dict: ...
    def close(self) -> None: ...


class WorkspaceExecutionProvider(Protocol):
    def open(self, workspace: str, *, context: SecurityContext,
             gate: CapabilityGate, cancellation_token: CancellationToken) -> WorkspaceSession: ...


class LocalWorkspaceProvider:
    """Explicit trusted-host execution, NOT isolation or a sandbox.

    The application must acknowledge host execution. Restricted deployments
    should implement WorkspaceExecutionProvider with real isolation instead.
    No subprocess is launched until the first authorized shell invocation.
    """

    def __init__(self, *, allow_host_execution: bool = False,
                 max_timeout: float = 300, output_limit: int = 65536,
                 max_file_bytes: int = 1024 * 1024):
        if not allow_host_execution:
            raise PermissionError("LocalWorkspaceProvider requires explicit allow_host_execution=True")
        if not math.isfinite(max_timeout) or max_timeout <= 0 or min(output_limit, max_file_bytes) < 1:
            raise ValueError("workspace limits must be positive and finite")
        self.max_timeout = max_timeout
        self.output_limit = output_limit
        self.max_file_bytes = max_file_bytes

    def open(self, workspace, *, context, gate, cancellation_token):
        if context.sandbox_required:
            raise PermissionError("LocalWorkspaceProvider cannot enforce a sandbox")
        if not context.network_allowed:
            raise PermissionError("LocalWorkspaceProvider cannot deny host network access")
        if os.name != "posix":
            raise BackendError("local managed shell currently requires POSIX")
        return _LocalSession(workspace, context, gate, cancellation_token, self)


class _LocalSession:
    def __init__(self, workspace, context, gate, token, config):
        self.root = Path(workspace).resolve(strict=True)
        if not self.root.is_dir():
            raise ValueError("workspace must be a directory")
        self.context, self.gate, self.token, self.config = context, gate, token, config
        self._process = None
        self._closed = False
        self._lock = threading.Lock()

    def _authorize(self, capability, arguments):
        if self._closed:
            raise BackendError("workspace session is closed")
        if self.token.cancelled:
            raise BackendError("workspace execution was cancelled")
        decision = self.gate.authorize_sync(
            CapabilitySpec(capability, execute=capability == "workspace.shell", write=True,
                           risk=CapabilityRisk.SENSITIVE),
            "local-workspace", arguments, self.context, resource=str(self.root),
        )
        # A transformed command must never silently execute the original.
        return decision.arguments if decision.arguments is not None else arguments

    def shell(self, command: str, timeout: float = 60) -> dict:
        with self._lock:
            args = self._authorize("workspace.shell", {"command": command, "timeout": timeout})
            command, timeout = args["command"], args["timeout"]
            if not isinstance(command, str) or not command.strip() or len(command.encode()) > 65536:
                raise ValueError("command must contain 1..65536 bytes")
            if not math.isfinite(timeout) or timeout <= 0 or timeout > self.config.max_timeout:
                raise ValueError("timeout exceeds workspace execution limits")
            if self._process is None:
                binary = shutil.which("bash")
                if not binary:
                    raise BackendError("bash is not available on PATH")
                self._process = subprocess.Popen(
                    [binary, "--noprofile", "--norc"], cwd=self.root,
                    env={k: v for k, v in os.environ.items() if k not in {"BASH_ENV", "ENV"}},
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
                os.set_blocking(self._process.stdout.fileno(), False)
                os.set_blocking(self._process.stdin.fileno(), False)
            process = self._process
            marker = ("LA_END_" + uuid4().hex).encode()
            script = f"eval {shlex.quote(command)} </dev/null\nbuiltin printf '\\n{marker.decode()}:%s\\n' \"$?\"\n"
            output = bytearray()
            tail = bytearray()
            total = 0
            status = "completed"
            code = None
            selector = selectors.DefaultSelector()
            deadline = time.monotonic() + timeout
            pending = script.encode()
            written = 0
            try:
                selector.register(process.stdout, selectors.EVENT_READ)
                selector.register(process.stdin, selectors.EVENT_WRITE)
                while True:
                    if self.token.cancelled or time.monotonic() >= deadline or self.context.expired:
                        status = "cancelled" if self.token.cancelled else "timed_out"
                        self.close()
                        break
                    readable = False
                    for key, _ in selector.select(0.05):
                        if key.fileobj is process.stdin:
                            written += os.write(process.stdin.fileno(), pending[written:written + 4096])
                            if written >= len(pending):
                                selector.unregister(process.stdin)
                        else:
                            readable = True
                    if readable:
                        chunk = os.read(process.stdout.fileno(), 16384)
                        if not chunk:
                            status = "failed"
                            self.close()
                            break
                        total += len(chunk)
                        output.extend(chunk[:max(0, self.config.output_limit - len(output))])
                        tail.extend(chunk)
                        match = re.search(rb"\n" + marker + rb":([0-9]+)\n", tail)
                        if match:
                            code = int(match.group(1))
                            # Exclude framing even when the capture limit cuts
                            # through the marker, and only flag user truncation.
                            total = total - len(tail) + match.start()
                            output = output[:total]
                            break
                        tail = tail[-128:]
                    if process.poll() is not None:
                        status = "failed"
                        self.close()
                        break
            except BaseException:
                self.close()
                raise
            finally:
                selector.close()
            return {"status": status, "exit_code": code,
                    "output": output.decode("utf-8", "replace"),
                    "truncated": total > self.config.output_limit,
                    "session_alive": not self._closed}

    def edit_file(self, path: str, new_text: str, old_text: str | None = None,
                  expected_sha256: str | None = None) -> dict:
        with self._lock:
            args = self._authorize("workspace.edit_file", {
                "path": path, "new_text": new_text, "old_text": old_text,
                "expected_sha256": expected_sha256,
            })
            path, new_text, old_text, expected_sha256 = (
                args["path"], args["new_text"], args["old_text"], args["expected_sha256"]
            )
            relative = Path(path)
            if relative.is_absolute() or not relative.parts or any(p == ".." for p in relative.parts):
                raise ValueError("edit path must be workspace-relative without '..'")
            if not isinstance(new_text, str) or len(new_text.encode()) > self.config.max_file_bytes:
                raise ValueError("new text exceeds the file budget")
            if old_text is None and expected_sha256 is not None:
                raise ValueError("expected_sha256 requires a replacement, not file creation")
            # Open each ancestor without following links, then keep the parent
            # fd pinned so directory renames cannot redirect the final write.
            parent = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            temporary = None
            try:
                for part in relative.parts[:-1]:
                    child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
                    os.close(parent)
                    parent = child
                leaf = relative.name
                if old_text is None:
                    fd = os.open(leaf, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                                 0o600, dir_fd=parent)
                    with os.fdopen(fd, "wb") as handle:
                        handle.write(new_text.encode())
                        handle.flush()
                        os.fsync(handle.fileno())
                    content = new_text
                else:
                    if not isinstance(old_text, str) or not old_text:
                        raise ValueError("old_text must be non-empty for replacement")
                    fd = os.open(leaf, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
                    with os.fdopen(fd, "rb") as handle:
                        before = os.fstat(handle.fileno())
                        if not stat.S_ISREG(before.st_mode):
                            raise ValueError("edit target must be a regular file")
                        data = handle.read(self.config.max_file_bytes + 1)
                    if len(data) > self.config.max_file_bytes:
                        raise ValueError("file exceeds the editing budget")
                    digest = hashlib.sha256(data).hexdigest()
                    if expected_sha256 is not None and digest != expected_sha256:
                        raise ValueError("stale file version")
                    text = data.decode("utf-8")
                    if text.count(old_text) != 1:
                        raise ValueError("old_text must match exactly once")
                    content = text.replace(old_text, new_text, 1)
                    if len(content.encode()) > self.config.max_file_bytes:
                        raise ValueError("edited file exceeds the budget")
                    temporary = ".lightagent-edit-" + uuid4().hex
                    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                                 before.st_mode & 0o777, dir_fd=parent)
                    with os.fdopen(fd, "wb") as handle:
                        handle.write(content.encode())
                        handle.flush()
                        os.fsync(handle.fileno())
                    after = os.stat(leaf, dir_fd=parent, follow_symlinks=False)
                    if (before.st_ino, before.st_mtime_ns, before.st_size) != (
                            after.st_ino, after.st_mtime_ns, after.st_size):
                        raise ValueError("file changed during editing")
                    os.replace(temporary, leaf, src_dir_fd=parent, dst_dir_fd=parent)
                    temporary = None
                os.fsync(parent)
                return {"path": str(relative), "sha256": hashlib.sha256(content.encode()).hexdigest()}
            finally:
                if temporary is not None:
                    os.unlink(temporary, dir_fd=parent)
                os.close(parent)

    def close(self):
        self._closed = True
        if self._process:
            terminate_group(self._process)
            for pipe in (self._process.stdin, self._process.stdout):
                if not pipe.closed:
                    pipe.close()


def workspace_tools(session: WorkspaceSession) -> list:
    """Create per-execution closures; never add tools to the caller's registry."""
    def shell(command: str, timeout: float = 60):
        return session.shell(command, timeout)

    def edit_file(path: str, new_text: str, old_text: str | None = None,
                  expected_sha256: str | None = None):
        return session.edit_file(path, new_text, old_text, expected_sha256)

    shell.tool_info = {
        "tool_name": "shell", "tool_description": "Run bounded shell commands; state lasts only for this run. Search/read with available commands. Avoid excessive output.",
        "tool_params": [{"name": "command", "type": "string", "required": True},
                        {"name": "timeout", "type": "number", "required": False}],
    }
    edit_file.tool_info = {
        "tool_name": "edit_file", "tool_description": "Create a new relative file, or replace one exact old_text occurrence. Omit old_text only to create. Parent directories must exist.",
        "tool_params": [{"name": "path", "type": "string", "required": True},
                        {"name": "new_text", "type": "string", "required": True},
                        {"name": "old_text", "type": "string", "required": False},
                        {"name": "expected_sha256", "type": "string", "required": False}],
    }
    return [shell, edit_file]


def workspace_guidance(workspace: str, limit: int = 32768) -> str:
    """Read root project guidance only, bounded and without following links."""
    root = Path(workspace).resolve(strict=True)
    if limit < 1:
        raise ValueError("guidance limit must be positive")
    parent = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for filename in ("AGENTS.override.md", "AGENTS.md"):
            try:
                fd = os.open(filename, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
            except OSError as exc:
                if exc.errno in (errno.ENOENT, errno.ELOOP):
                    continue
                raise
            with os.fdopen(fd, "rb") as handle:
                if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
                    continue
                data = handle.read(limit + 1)
            if data.strip():
                return data[:limit].decode("utf-8", "replace") + (
                    "\n[Project guidance truncated; read relevant sections with tools.]" if len(data) > limit else "")
    finally:
        os.close(parent)
    return "Read the workspace README and relevant project instructions before acting. Discover information on demand."
