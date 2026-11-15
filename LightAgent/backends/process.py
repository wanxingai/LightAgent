"""Bounded POSIX process execution without shell interpolation."""

from __future__ import annotations

import os
import selectors
import signal
import subprocess
import time
from dataclasses import dataclass
from typing import Callable

from ..cancellation import CancellationToken
from .base import BackendError


@dataclass(frozen=True)
class ProcessResult:
    returncode: int
    stdout: str
    stderr: str
    truncated: bool
    status: str


def terminate_group(process: subprocess.Popen) -> None:
    """Clean descendants too, including inherited pipes after leader exit."""
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    except PermissionError:
        # macOS can deny signalling a group whose leader has just exited.
        # Do not hide a denial for an actually running owned process.
        try:
            process.wait(timeout=0.2)
        except subprocess.TimeoutExpired as exc:
            raise BackendError("permission denied while terminating managed process group") from exc
    try:
        process.wait(timeout=0.2)
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    except PermissionError:
        try:
            process.wait(timeout=0.2)
        except subprocess.TimeoutExpired as exc:
            raise BackendError("permission denied while killing managed process group") from exc
    process.wait(timeout=2)


def run_process(
        argv: list[str], *, cwd: str, token: CancellationToken,
        timeout: float, stdin: bytes = b"", env: dict[str, str] | None = None,
        output_limit: int = 65536, stream_limit: int = 64 * 1024 * 1024,
        on_stdout_line: Callable[[bytes], None] | None = None,
        line_limit: int = 1024 * 1024,
) -> ProcessResult:
    if os.name != "posix":
        raise BackendError("managed process groups currently require POSIX")
    if token.cancelled:
        return ProcessResult(-1, "", "", False, "cancelled")
    process = subprocess.Popen(
        argv, cwd=cwd, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, start_new_session=True,
    )
    selector = selectors.DefaultSelector()
    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    pending = bytearray()
    total = 0
    truncated = False
    status = "completed"
    written = 0
    deadline = time.monotonic() + timeout
    try:
        for pipe, name in ((process.stdout, "stdout"), (process.stderr, "stderr")):
            os.set_blocking(pipe.fileno(), False)
            selector.register(pipe, selectors.EVENT_READ, name)
        if stdin:
            os.set_blocking(process.stdin.fileno(), False)
            selector.register(process.stdin, selectors.EVENT_WRITE, "stdin")
        else:
            process.stdin.close()
        while selector.get_map():
            if token.cancelled:
                status = "cancelled"
                break
            if time.monotonic() >= deadline:
                status = "timed_out"
                break
            for key, _ in selector.select(timeout=0.05):
                pipe, name = key.fileobj, key.data
                if name == "stdin":
                    try:
                        written += os.write(pipe.fileno(), stdin[written:written + 16384])
                    except BrokenPipeError:
                        written = len(stdin)
                    if written >= len(stdin):
                        selector.unregister(pipe)
                        pipe.close()
                    continue
                chunk = os.read(pipe.fileno(), 16384)
                if not chunk:
                    selector.unregister(pipe)
                    pipe.close()
                    continue
                total += len(chunk)
                if total > stream_limit:
                    raise BackendError("process exceeded total output budget")
                available = max(0, output_limit - len(buffers[name]))
                buffers[name].extend(chunk[:available])
                truncated |= len(chunk) > available
                if name == "stdout" and on_stdout_line:
                    pending.extend(chunk)
                    while b"\n" in pending:
                        line, _, rest = pending.partition(b"\n")
                        pending = bytearray(rest)
                        if len(line) > line_limit:
                            raise BackendError("process event exceeds line budget")
                        on_stdout_line(bytes(line))
                    if len(pending) > line_limit:
                        raise BackendError("process event exceeds line budget")
            # A leader that exited while descendants keep pipes open must not
            # keep this call alive or leave detached processes behind.
            if process.poll() is not None:
                terminate_group(process)
        if status == "completed":
            while process.poll() is None:
                if token.cancelled or time.monotonic() >= deadline:
                    status = "cancelled" if token.cancelled else "timed_out"
                    break
                token.wait(0.02)
            if pending and on_stdout_line:
                on_stdout_line(bytes(pending))
    finally:
        terminate_group(process)
        selector.close()
        for pipe in (process.stdin, process.stdout, process.stderr):
            if not pipe.closed:
                pipe.close()
    return ProcessResult(
        process.returncode, buffers["stdout"].decode("utf-8", "replace"),
        buffers["stderr"].decode("utf-8", "replace"), truncated, status,
    )
