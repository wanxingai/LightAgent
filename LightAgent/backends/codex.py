"""Optional Codex CLI execution; importing this module needs no CLI or key."""

from __future__ import annotations

import json
import re
import shutil
import threading
import os
import time
from contextlib import ExitStack
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from ..capabilities import CapabilityRisk, CapabilitySpec
from ..cancellation import CancellationToken
from ..security import CapabilityGate
from .base import (
    BackendCapabilities, BackendError, BackendProbe, BackendRequest, BackendResult, cancellable_thread,
)
from .process import run_process
from .sessions import BackendSessionStore, session_binding


class CodexBackend:
    """Run one bounded CLI turn. Final messages remain unverified candidates.

    User configuration is excluded to avoid silently enabling unrelated MCP
    servers/hooks. CLI authentication is reused; model may be set explicitly.
    """

    capabilities = BackendCapabilities(resume=True, isolation="sandbox", network_control=True)

    def __init__(self, *, model: str | None = None, sandbox: str = "workspace-write",
                 gate: CapabilityGate | None = None, output_limit: int = 65536,
                 network_access: bool = False,
                 session_store: BackendSessionStore | None = None):
        if sandbox not in ("read-only", "workspace-write"):
            raise ValueError("Codex sandbox must be read-only or workspace-write")
        if output_limit < 1:
            raise ValueError("output_limit must be positive")
        if type(network_access) is not bool or (network_access and sandbox != "workspace-write"):
            raise ValueError("network_access requires workspace-write and a boolean value")
        self.network_access = network_access
        self.model = model
        self.sandbox = sandbox
        self.gate = gate or CapabilityGate()
        self.output_limit = output_limit
        self._lock = threading.Lock()
        self.session_store = session_store or BackendSessionStore()

    def probe(self, *, token=None, timeout=10) -> BackendProbe:
        """Inspect installed CLI without a model request or reading credentials."""
        return self._probe(token or CancellationToken(), time.monotonic() + timeout)[1]

    def _probe(self, token, deadline):
        binary = shutil.which("codex")
        if binary is None:
            raise BackendError("codex was not found on PATH; install Codex CLI or use the native backend")
        outputs = []
        for flags in (["--version"], ["exec", "--help"], ["exec", "resume", "--help"]):
            remaining = deadline - time.monotonic()
            if remaining <= 0 or token.cancelled:
                raise BackendError("Codex capability probe was cancelled or timed out")
            result = run_process([binary, *flags], cwd=os.getcwd(), token=token,
                                 timeout=min(remaining, 10), output_limit=65536)
            if result.status != "completed" or result.returncode or result.truncated:
                raise BackendError(f"Codex capability probe failed: {result.status}")
            outputs.append(result.stdout)
        match = re.search(r"codex-cli (\d+)\.(\d+)\.(\d+)(?:\s|$)", outputs[0])
        if not match or tuple(map(int, match.groups()[:2])) != (0, 160):
            raise BackendError("unsupported Codex CLI version; this adapter supports the tested 0.160.x protocol")
        required = {"--json", "--ignore-user-config", "--strict-config", "--config", "--skip-git-repo-check"}
        for help_text in outputs[1:]:
            missing = required - set(re.findall(r"--[a-z][a-z-]+", help_text))
            if missing:
                raise BackendError("Codex CLI missing required options: " + ", ".join(sorted(missing)))
        if "--sandbox" not in outputs[1]:
            raise BackendError("Codex CLI does not support sandbox selection")
        return binary, BackendProbe("codex", ".".join(match.groups()), self.capabilities, (
            "POSIX only; no live steering or per-tool LightAgent policy",
            "Model transport needs network; Apps and web search are disabled; shell network is explicit opt-in",
            "Resume requires unchanged host-owned session binding",
        ))

    def _validate_permissions(self, request):
        permissions = request.security_context.permissions
        # A backend-level grant cannot represent restrictions on opaque native
        # CLI tools. Never accept a tool allowlist/denylist then silently ignore it.
        entry_points = {"backend.execute", "backend.codex", "dag.task.execute"}
        if (permissions.allowed - entry_points or permissions.denied - entry_points
                or permissions.max_risk != CapabilityRisk.DESTRUCTIVE):
            raise BackendError("Codex cannot enforce per-tool permissions or max_risk; use a native backend or isolated provider")
        root = Path(request.workspace)
        state = self.session_store.directory.resolve()
        if state == root or root in state.parents:
            raise BackendError("Codex session state must be outside the writable workspace")
        # Project config can enable arbitrary hooks/MCP outside command sandbox.
        # P0 does not import those layers; reject rather than partially applying.
        for parent in (root, *root.parents):
            if (parent / ".codex").resolve() == Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).resolve():
                continue  # excluded explicitly by --ignore-user-config
            for filename in ("config.toml", "hooks.json"):
                if (parent / ".codex" / filename).exists():
                    raise BackendError("project .codex config/hooks are unsupported by the bounded Codex backend")

    async def execute(self, request: BackendRequest) -> BackendResult:
        if not self._lock.acquire(blocking=False):
            raise BackendError("backend is busy; use one backend instance per worker")
        try:
            token = (request.cancellation_token or CancellationToken()).child()
            request = replace(request, cancellation_token=token)
            self._validate_permissions(request)
            arguments = {"prompt": request.prompt, "workspace": request.workspace,
                         "session_id": request.session_id, "sandbox": self.sandbox}
            decision = await self.gate.authorize(
                CapabilitySpec("backend.codex", execute=True, network=True,
                               risk=CapabilityRisk.SENSITIVE),
                "codex", arguments,
                request.security_context, resource=request.workspace,
            )
            if decision.arguments is not None and decision.arguments != arguments:
                raise BackendError("Codex backend policy rewrites are unsupported; submit the revised request explicitly")
            return await cancellable_thread(lambda: self._execute(request), token)
        finally:
            self._lock.release()

    def _execute(self, request: BackendRequest) -> BackendResult:
        expires = time.monotonic() + request.timeout
        if request.security_context.deadline:
            deadline = datetime.fromisoformat(request.security_context.deadline.replace("Z", "+00:00"))
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=timezone.utc)
            expires = min(expires, time.monotonic() + (deadline - datetime.now(timezone.utc)).total_seconds())
        if request.cancellation_token.cancelled:
            return BackendResult("", "cancelled", error="cancelled")
        if request.session_id and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}", request.session_id):
            raise ValueError("invalid Codex session ID")
        with ExitStack() as stack:
            stack.enter_context(self.session_store.lock("workspace", request.workspace))
            binding = session_binding(request.workspace, request.security_context, {
                "backend": "codex", "model": self.model, "sandbox": self.sandbox,
                "protocol": "0.160", "config_revision": 2, "network_access": self.network_access,
                "codex_home": str(Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).resolve()),
                **self._extra_binding(),
            })
            if request.session_id:
                stack.enter_context(self.session_store.claim("codex", request.session_id, binding))
            try:
                binary, probe = self._probe(request.cancellation_token, expires)
            except BackendError:
                if request.cancellation_token.cancelled or time.monotonic() >= expires:
                    status = "cancelled" if request.cancellation_token.cancelled else "timed_out"
                    return BackendResult("", status, request.session_id, error=status)
                raise
            request.emit("backend.capabilities", backend=probe.backend, version=probe.version,
                         limitations=list(probe.limitations))
            return self._run_turn(request, binary, stack, binding, expires)

    def _extra_binding(self):
        return {"transport": "exec"}

    def _configuration_options(self):
        return [
            "-c", 'approval_policy="never"',
            "-c", "sandbox_workspace_write.network_access=" + str(self.network_access).lower(),
            "-c", "sandbox_workspace_write.writable_roots=[]",
            "-c", "sandbox_workspace_write.exclude_slash_tmp=true",
            "-c", "sandbox_workspace_write.exclude_tmpdir_env_var=true",
            "-c", "features.apps=false", "-c", "features.hooks=false",
            "-c", "features.multi_agent=false", "-c", "agents.enabled=false",
            "-c", "features.remote_plugin=false", "-c", 'web_search="disabled"',
            "-c", "allow_login_shell=false",
            "-c", 'shell_environment_policy.inherit="core"',
            "-c", "shell_environment_policy.ignore_default_excludes=false"]

    def _run_turn(self, request, binary, stack, binding, expires):
        # Global configuration flags must precede the resume subcommand. Only
        # documented resume flags are placed after it; never use --last.
        argv = [binary, "exec", "--ignore-user-config", "--strict-config", "--sandbox", self.sandbox,
                *self._configuration_options()]
        if self.model:
            argv.extend(["--model", self.model])
        if request.session_id:
            argv.extend(["resume", request.session_id])
        argv.extend(["--skip-git-repo-check", "--json", "-"])
        content = ""
        session_id = request.session_id
        completed = False
        failure = None
        usage = None
        event_count = 0
        terminal = False

        def event(line: bytes):
            nonlocal content, session_id, completed, failure, usage, event_count, terminal
            if not line.strip():
                return
            try:
                item = json.loads(line)
            except (ValueError, UnicodeDecodeError) as exc:
                raise BackendError("Codex emitted invalid JSONL") from exc
            if not isinstance(item, dict) or not isinstance(item.get("type"), str):
                raise BackendError("Codex emitted an invalid event envelope")
            event_count += 1
            if event_count > 10000:
                raise BackendError("Codex exceeded the event count budget")
            kind = item["type"]
            if terminal:
                raise BackendError("Codex emitted events after the terminal result")
            if kind == "thread.started":
                received = item.get("thread_id")
                if not isinstance(received, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}", received):
                    raise BackendError("Codex did not provide a session ID")
                if session_id and received != session_id:
                    raise BackendError("Codex resumed a different session")
                if session_id is None:
                    stack.enter_context(self.session_store.claim("codex", received, binding, create=True))
                session_id = received
            elif kind == "item.completed":
                value = item.get("item", {})
                if isinstance(value, dict) and value.get("type") == "agent_message":
                    text = value.get("text")
                    if not isinstance(text, str) or len(text.encode("utf-8")) > self.output_limit:
                        raise BackendError("Codex final message is invalid or exceeds the output budget")
                    content = text
            elif kind == "turn.completed":
                terminal = True
                completed = True
                usage = item.get("usage")
                if usage is not None:
                    if not isinstance(usage, dict):
                        raise BackendError("Codex emitted invalid usage")
                    for key in ("input_tokens", "output_tokens", "cached_input_tokens", "reasoning_output_tokens"):
                        value = usage.get(key, 0)
                        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                            raise BackendError("Codex emitted invalid token usage")
            elif kind in ("turn.failed", "error"):
                failure = json.dumps(item.get("error", item.get("message", kind)), ensure_ascii=False)
                terminal = kind == "turn.failed"
            request.emit("backend.event", backend="codex", event=item)

        request.emit("backend.started", backend="codex", workspace=request.workspace)
        result = run_process(
            argv, cwd=request.workspace, token=request.cancellation_token,
            timeout=max(0.001, expires - time.monotonic()), stdin=request.prompt.encode("utf-8"),
            output_limit=self.output_limit, on_stdout_line=event,
        )
        if result.status != "completed":
            status = result.status
            failure = status
        elif failure or result.returncode != 0 or not completed or not session_id or not content:
            status = "failed"
            failure = failure or self._diagnostic(result.stderr, result.returncode)
        else:
            status = "completed"
        request.emit("backend.finished", backend="codex", status=status, session_id=session_id)
        return BackendResult(content, status, session_id, usage, failure)

    @staticmethod
    def _diagnostic(stderr, returncode):
        """Return actionable categories without persisting raw CLI diagnostics."""
        value = stderr.lower()
        categories = (
            (("readonly database", "operation not permitted", "permission denied"),
             "Codex cannot access its runtime files or start its sandbox; check host permissions"),
            (("not logged in", "unauthorized", "authentication", "401"),
             "Codex authentication failed; check codex login status"),
            (("rate limit", "quota", "usage limit", "429"),
             "Codex account usage is limited; retry after the account limit resets"),
            (("unexpected argument", "unknown field", "invalid value", "unknown variant"),
             "Codex rejected the adapter configuration; run probe and check CLI compatibility"),
        )
        for terms, message in categories:
            if any(term in value for term in terms):
                return f"{message} (exit={returncode})"
        return f"Codex exit={returncode}; missing successful final result"
