"""Offline execution, isolation and backwards-compatibility regression tests."""
import asyncio
import json
import os
from pathlib import Path
import shlex
import sys
import threading
import time
from types import SimpleNamespace

import pytest

from LightAgent import (
    BackendError, BackendRequest, BackendResult, CancellationToken, CapabilityGate,
    CodexBackend, LightAgent, LocalWorkspaceProvider, PermissionSet, PolicyDecision,
    PolicyEngine, RunResult, SecurityContext,
    BackendSessionStore,
)
from LightAgent.backends.process import run_process
from LightAgent.workspace import workspace_guidance


pytestmark = pytest.mark.skipif(os.name != "posix", reason="managed subprocess implementation is POSIX")


@pytest.fixture(autouse=True)
def backend_state(tmp_path, monkeypatch):
    # Control metadata is deliberately outside model-writable workspaces.
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path.parent / (tmp_path.name + "-state")))


def security(path, **kwargs):
    return SecurityContext(resources=frozenset({str(path.resolve())}), network_allowed=True, **kwargs)


@pytest.fixture
def workspace(tmp_path):
    session = LocalWorkspaceProvider(allow_host_execution=True).open(
        str(tmp_path), context=security(tmp_path), gate=CapabilityGate(),
        cancellation_token=CancellationToken(),
    )
    try:
        yield session
    finally:
        session.close()


def test_local_execution_requires_opt_in_and_cannot_claim_isolation(tmp_path):
    with pytest.raises(PermissionError):
        LocalWorkspaceProvider()
    provider = LocalWorkspaceProvider(allow_host_execution=True)
    for context in (security(tmp_path, sandbox_required=True), SecurityContext()):
        with pytest.raises(PermissionError):
            provider.open(str(tmp_path), context=context, gate=CapabilityGate(),
                          cancellation_token=CancellationToken())


def test_shell_search_read_and_state_survive_calls(workspace, tmp_path):
    (tmp_path / "README.md").write_text("DR007 data lives in data/\n")
    result = workspace.shell("grep -n DR007 README.md")
    assert result["exit_code"] == 0
    assert "data/" in result["output"]
    assert "LA_END_" not in result["output"]
    assert workspace.shell("export RESEARCH_MARKER=42")["exit_code"] == 0
    assert workspace.shell('printf "$RESEARCH_MARKER"')["output"] == "42"
    assert workspace.shell("false")["exit_code"] == 1


def test_shell_timeout_closes_session_and_cannot_reuse_it(workspace):
    started = time.monotonic()
    result = workspace.shell("sleep 20", timeout=0.1)
    assert result["status"] == "timed_out"
    assert not result["session_alive"]
    assert time.monotonic() - started < 3
    with pytest.raises(BackendError, match="closed"):
        workspace.shell("echo reused")


def test_shell_cancellation_and_output_limit(tmp_path):
    token = CancellationToken()
    session = LocalWorkspaceProvider(allow_host_execution=True, output_limit=128).open(
        str(tmp_path), context=security(tmp_path), gate=CapabilityGate(), cancellation_token=token)
    try:
        small = session.shell("printf '%100s' x")
        assert small["output"] == " " * 99 + "x"
        assert not small["truncated"]
        result = session.shell("printf '%10000s' x")
        assert result["truncated"]
        assert len(result["output"]) <= 128
        timer = threading.Timer(0.1, token.cancel)
        timer.start()
        try:
            assert session.shell("sleep 20")["status"] == "cancelled"
        finally:
            timer.cancel()
    finally:
        session.close()


def test_file_edits_preserve_content_and_detect_conflicts(workspace, tmp_path):
    created = workspace.edit_file("notes.txt", "alpha\nbeta\n")
    result = workspace.edit_file("notes.txt", "gamma", "beta", created["sha256"])
    assert (tmp_path / "notes.txt").read_text() == "alpha\ngamma\n"
    with pytest.raises(ValueError, match="stale"):
        workspace.edit_file("notes.txt", "delta", "gamma", created["sha256"])
    with pytest.raises(FileExistsError):
        workspace.edit_file("notes.txt", "overwrite")
    assert result["sha256"] != created["sha256"]
    workspace.edit_file("repeat.txt", "same same")
    with pytest.raises(ValueError, match="exactly once"):
        workspace.edit_file("repeat.txt", "other", "same")


def test_file_edits_reject_escapes_and_symlinks(workspace, tmp_path):
    (tmp_path / "linked").symlink_to(tmp_path.parent, target_is_directory=True)
    for path in ("../escape.txt", str(tmp_path / "absolute.txt")):
        with pytest.raises(ValueError):
            workspace.edit_file(path, "no")
    with pytest.raises(OSError):
        workspace.edit_file("linked/escape.txt", "no")


def test_workspace_policy_denial_and_rewrite(tmp_path):
    gate = CapabilityGate(policy_engine=PolicyEngine([
        lambda request: PolicyDecision.allow({**request.arguments, "command": "printf rewritten"})
    ]))
    provider = LocalWorkspaceProvider(allow_host_execution=True)
    session = provider.open(str(tmp_path), context=security(tmp_path), gate=gate,
                            cancellation_token=CancellationToken())
    try:
        assert session.shell("printf original")["output"] == "rewritten"
    finally:
        session.close()
    session = provider.open(str(tmp_path), gate=CapabilityGate(), cancellation_token=CancellationToken(),
                            context=security(tmp_path, permissions=PermissionSet(denied=frozenset({"workspace.shell"}))))
    try:
        with pytest.raises(PermissionError):
            session.shell("touch should-not-exist")
        assert not (tmp_path / "should-not-exist").exists()
    finally:
        session.close()


def test_guidance_is_bounded_and_does_not_read_link(tmp_path):
    (tmp_path / "AGENTS.md").write_text("base guidance")
    (tmp_path / "AGENTS.override.md").write_text("override" * 10)
    assert workspace_guidance(str(tmp_path), limit=8).startswith("override\n[")
    (tmp_path / "AGENTS.override.md").unlink()
    (tmp_path / "AGENTS.override.md").symlink_to(tmp_path / "AGENTS.md")
    assert workspace_guidance(str(tmp_path)) == "base guidance"


def fake_codex(tmp_path, monkeypatch, body):
    binary = tmp_path / "codex"
    binary.write_text(f"#!{sys.executable}\nimport sys, json, time\n" + """
if '--version' in sys.argv:
    print('codex-cli 0.160.0')
    sys.exit(0)
if '--help' in sys.argv:
    print('--json --ignore-user-config --strict-config --config --skip-git-repo-check --sandbox')
    sys.exit(0)
""" + body)
    binary.chmod(0o700)
    monkeypatch.setenv("PATH", str(tmp_path) + os.pathsep + os.environ.get("PATH", ""))


SUCCESS = """
prompt = sys.stdin.read()
print(json.dumps({'type': 'thread.started', 'thread_id': 'session-123'}))
print(json.dumps({'type': 'item.completed', 'item': {'type':'agent_message', 'text': 'result ' + prompt}}))
print(json.dumps({'type': 'turn.completed', 'usage': {'input_tokens': 10, 'output_tokens': 5}}))
"""


def test_codex_jsonl_and_literal_stdin(tmp_path, monkeypatch):
    fake_codex(tmp_path, monkeypatch, SUCCESS)
    events = []
    prompt = "$(touch pwned) `echo nope`\n中文"
    result = asyncio.run(CodexBackend().execute(BackendRequest(
        prompt, str(tmp_path), security(tmp_path), on_event=events.append)))
    assert result.status == "completed"
    assert result.content == "result " + prompt
    assert result.session_id == "session-123"
    assert result.usage["input_tokens"] == 10
    assert events[-1].type == "backend.finished"
    assert not (tmp_path / "pwned").exists()


@pytest.mark.parametrize("body", [
    "print('not json')", "print('{}')",
    "print(json.dumps({'type':'turn.completed'}))",
    SUCCESS + "sys.exit(1)",
    SUCCESS + "print(json.dumps({'type':'turn.failed', 'error':{'message':'failed'}}))",
])
def test_codex_does_not_accept_exit_or_text_as_success(tmp_path, monkeypatch, body):
    fake_codex(tmp_path, monkeypatch, body)
    try:
        result = asyncio.run(CodexBackend().execute(BackendRequest("test", str(tmp_path), security(tmp_path))))
    except BackendError:
        return
    assert result.status == "failed"
    assert result.error


def test_codex_resume_uses_exact_id(tmp_path, monkeypatch):
    fake_codex(tmp_path, monkeypatch, SUCCESS)
    asyncio.run(CodexBackend().execute(BackendRequest("first", str(tmp_path), security(tmp_path))))
    body = "assert 'resume' in sys.argv and 'session-123' in sys.argv\nassert '--last' not in sys.argv\n" + SUCCESS
    fake_codex(tmp_path, monkeypatch, body)
    result = asyncio.run(CodexBackend().execute(BackendRequest(
        "test", str(tmp_path), security(tmp_path), session_id="session-123")))
    assert result.status == "completed"


def test_codex_timeout_and_missing_binary(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", str(tmp_path))
    with pytest.raises(BackendError, match="PATH"):
        asyncio.run(CodexBackend().execute(BackendRequest("test", str(tmp_path), security(tmp_path))))
    fake_codex(tmp_path, monkeypatch, "time.sleep(20)")
    result = asyncio.run(CodexBackend().execute(BackendRequest("test", str(tmp_path), security(tmp_path), timeout=0.1)))
    assert result.status == "timed_out"


def test_async_cancel_waits_for_process_exit(tmp_path, monkeypatch):
    fake_codex(tmp_path, monkeypatch, "print(json.dumps({'type':'thread.started','thread_id':'session-123'}), flush=True)\ntime.sleep(20)")

    async def scenario():
        task = asyncio.create_task(CodexBackend().execute(BackendRequest("test", str(tmp_path), security(tmp_path))))
        await asyncio.sleep(0.1)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    started = time.monotonic()
    asyncio.run(scenario())
    assert time.monotonic() - started < 3


class NativeCompletions:
    def __init__(self):
        self.calls = []

    def create(self, **params):
        self.calls.append(params)
        if len(self.calls) == 1:
            call = SimpleNamespace(id="shell-1", function=SimpleNamespace(
                name="shell", arguments=json.dumps({"command": "cat README.md"})))
            message = SimpleNamespace(content=None, tool_calls=[call])
        else:
            message = SimpleNamespace(content="found DR007", tool_calls=None)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def test_native_workspace_uses_two_tools_and_leaves_legacy_agent_alone(tmp_path):
    (tmp_path / "README.md").write_text("DR007 data")
    agent = LightAgent(model="test", api_key="test", auto_discover_skills=False,
                       execution_provider=LocalWorkspaceProvider(allow_host_execution=True))
    completions = NativeCompletions()
    agent.client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    original_tools = agent.tool_registry.get_tools()
    result = agent.run("find data", workspace=str(tmp_path), result_format="object")
    assert result.content == "found DR007", result.error
    assert not result.error
    assert {t["function"]["name"] for t in completions.calls[0]["tools"]} == {"shell", "edit_file"}
    assert any("DR007 data" in str(m) for m in completions.calls[1]["messages"])
    assert agent.tool_registry.get_tools() == original_tools
    assert agent.run("ordinary chat") == "found DR007"
    assert completions.calls[-1]["tools"] == original_tools


def test_native_missing_provider_does_not_grant_host_access(tmp_path):
    agent = LightAgent(model="test", api_key="test", auto_discover_skills=False)
    with pytest.raises(BackendError, match="Provider"):
        agent.run("execute", workspace=str(tmp_path))


def test_external_backend_needs_no_api_key_and_preserves_result_shape(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    fake_codex(tmp_path, monkeypatch, SUCCESS)
    agent = LightAgent(backend="codex", auto_discover_skills=False)
    assert agent.client is None
    result = agent.run("hello", workspace=str(tmp_path), result_format="object")
    assert isinstance(result, RunResult)
    assert result.content.endswith("User request:\nhello"), result.error
    assert not result.error
    assert agent.get_session() is not None


def test_external_input_guardrail_prevents_execution(tmp_path):
    class Backend:
        async def execute(self, request):
            pytest.fail("guardrail was bypassed")
    agent = LightAgent(backend=Backend(), auto_discover_skills=False,
                       input_guardrails=[lambda *_: False])
    result = agent.run("denied", workspace=str(tmp_path), result_format="object")
    assert result.error


def test_process_large_stdin_and_total_output_budget(tmp_path):
    result = run_process([sys.executable, "-c", "import sys; print(len(sys.stdin.read()))"],
                         cwd=str(tmp_path), token=CancellationToken(), timeout=3, stdin=b"x" * 200000)
    assert result.stdout.strip() == "200000"
    with pytest.raises(BackendError, match="output budget"):
        run_process([sys.executable, "-c", "print('x'*10000)"], cwd=str(tmp_path),
                    token=CancellationToken(), timeout=3, stream_limit=1000)


def test_local_and_backend_session_ids_are_distinct(tmp_path, monkeypatch):
    fake_codex(tmp_path, monkeypatch, "assert 'resume' not in sys.argv\n" + SUCCESS)
    agent = LightAgent(backend="codex", instructions="Keep evidence", auto_discover_skills=False)
    first = agent.run("hello", workspace=str(tmp_path), session_id="local-session", result_format="object")
    assert not first.error
    assert "Keep evidence" in first.content
    assert agent.get_session().session_id == "local-session"
    assert agent.last_backend_result.session_id == "session-123"
    fake_codex(tmp_path, monkeypatch, "assert 'resume' in sys.argv\nassert 'session-123' in sys.argv\n" + SUCCESS)
    second = agent.run("continue", workspace=str(tmp_path), session_id="local-session",
                       backend_session_id=agent.last_backend_result.session_id, result_format="object")
    assert not second.error
    events = [e for e in agent.get_session().events if e.type == "backend.result"]
    assert len(events) == 2
    assert all(e.data["backend_session_id"] == "session-123" for e in events)


def test_backend_policy_rewrite_and_resource_mismatch_fail_before_launch(tmp_path, monkeypatch):
    fake_codex(tmp_path, monkeypatch, "open('launched', 'w').write('bad')\n" + SUCCESS)
    policy = PolicyEngine([lambda r: PolicyDecision.allow({**r.arguments, "prompt": "rewritten"})])
    with pytest.raises(BackendError, match="rewrites"):
        asyncio.run(CodexBackend(gate=CapabilityGate(policy_engine=policy)).execute(
            BackendRequest("test", str(tmp_path), security(tmp_path))))
    with pytest.raises(PermissionError, match="resource"):
        asyncio.run(CodexBackend().execute(BackendRequest("test", str(tmp_path), security(tmp_path.parent))))
    assert not (tmp_path / "launched").exists()


def test_deadline_clips_request_timeout(tmp_path):
    from datetime import datetime, timedelta, timezone
    deadline = (datetime.now(timezone.utc) + timedelta(seconds=1)).isoformat()
    request = BackendRequest("test", str(tmp_path), security(tmp_path, deadline=deadline), timeout=100)
    assert 0 < request.timeout <= 1
    with pytest.raises(PermissionError, match="expired"):
        BackendRequest("test", str(tmp_path), security(tmp_path, deadline="2000-01-01T00:00:00Z"))


def test_unsupported_external_policy_hooks_are_rejected():
    from LightAgent import PolicyHook, BudgetLimits
    for options in (
        {"hooks": [PolicyHook(lambda _: False, phases={"before_tool_call"})]},
        {"budget_limits": BudgetLimits(tool_calls=1)},
    ):
        with pytest.raises(ValueError):
            LightAgent(backend="codex", **options)


def test_shell_large_command_cannot_block_cancellation(workspace):
    # A command larger than the pipe capacity must be fed while reading output.
    result = workspace.shell("printf '%s' " + shlex.quote("x" * 60000), timeout=3)
    assert result["status"] == "completed"
    assert len(result["output"]) == 60000


def test_native_context_permissions_reach_tool_policy(tmp_path):
    (tmp_path / "README.md").write_text("private contents")
    agent = LightAgent(model="test", api_key="test", auto_discover_skills=False,
                       execution_provider=LocalWorkspaceProvider(allow_host_execution=True))
    completions = NativeCompletions()
    agent.client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    context = security(tmp_path, user_id="alice",
                       permissions=PermissionSet(denied=frozenset({"tool.shell"})))
    agent.run("read data", workspace=str(tmp_path), security_context=context)
    assert "private contents" not in str(completions.calls[-1]["messages"])
    session = agent.get_session()
    denials = [e for e in session.events if e.type == "policy.decision" and not e.data.get("allowed", True)]
    assert any(e.data["capability"] == "tool.shell" for e in denials)


@pytest.mark.parametrize("content,accepted", [
    ('{"kind":"candidate","content":"root"}', True),
    ('{"kind":"candidate","content":"wrong"}', False),
    ('{"kind":"candidate"}', False),
    ('plain text success', False),
])
def test_backend_dag_adapter_cannot_publish_without_verification(tmp_path, content, accepted):
    from LightAgent import BackendWorkerAdapter
    from LightAgent.dag import CallableVerifier, DAGConfig, LightDAG, LocalArtifactStore, SqliteTaskGraphStore, TaskSpec

    class Backend:
        async def execute(self, request):
            assert request.attempt_id
            assert request.security_context.user_id == "alice"
            return BackendResult(content)

    dag = LightDAG(
        store=SqliteTaskGraphStore(tmp_path / "dag.sqlite3"),
        artifact_store=LocalArtifactStore(tmp_path / "artifacts"),
        verifiers={"verify": CallableVerifier("verify", lambda req: req.candidate_content == b"root")},
        config=DAGConfig(max_attempts_per_task=1),
    )
    dag.register_worker("backend", BackendWorkerAdapter(Backend(), tmp_path))
    dag.create_run([TaskSpec(task_id="root", goal="produce root", acceptance_contract={"equals": "root"},
                             worker_key="backend", verifier_key="verify")],
                   run_id="run", context=security(tmp_path, user_id="alice", tenant_id="tenant", project_id="project"))
    result = dag.run("run")
    assert result.success == accepted
    assert bool(result.root_artifacts.get("root")) == accepted


def test_process_timeout_terminates_its_child_group(tmp_path):
    pids = []
    script = (
        "import subprocess, sys, time; "
        "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)']); "
        "print(child.pid, flush=True); time.sleep(30)"
    )
    result = run_process([sys.executable, "-c", script], cwd=str(tmp_path),
                         token=CancellationToken(), timeout=0.5,
                         on_stdout_line=lambda line: pids.append(int(line)))
    assert result.status == "timed_out"
    assert len(pids) == 1
    # A reaped process or a zombie awaiting OS reaping cannot keep running.
    for _ in range(100):
        try:
            os.kill(pids[0], 0)
        except ProcessLookupError:
            return
        status = Path(f"/proc/{pids[0]}/stat")
        if status.exists():
            try:
                if status.read_text().rsplit(") ", 1)[-1].startswith("Z"):
                    return
            except FileNotFoundError:
                return
        time.sleep(0.02)
    pytest.fail("child process survived managed process-group cleanup")


def test_codex_rejects_thread_switch_and_invalid_usage(tmp_path, monkeypatch):
    for suffix in (
        "print(json.dumps({'type':'thread.started','thread_id':'different'}))",
        "print(json.dumps({'type':'turn.completed','usage':{'input_tokens':-1}}))",
    ):
        fake_codex(tmp_path, monkeypatch, SUCCESS + suffix)
        with pytest.raises(BackendError):
            asyncio.run(CodexBackend().execute(BackendRequest("test", str(tmp_path), security(tmp_path))))


def test_guidance_skips_fifo_instead_of_waiting(tmp_path):
    os.mkfifo(tmp_path / "AGENTS.override.md")
    (tmp_path / "AGENTS.md").write_text("regular instructions")
    assert workspace_guidance(str(tmp_path)) == "regular instructions"


def test_repeated_async_cancel_still_waits_for_worker_cleanup():
    from LightAgent.backends.base import cancellable_thread
    token = CancellationToken()
    started = threading.Event()
    finished = threading.Event()

    def work():
        started.set()
        token.wait(2)
        time.sleep(0.15)  # simulate non-instant process-group cleanup
        finished.set()

    async def scenario():
        task = asyncio.create_task(cancellable_thread(work, token))
        while not started.is_set():
            await asyncio.sleep(0.005)
        task.cancel()
        await asyncio.sleep(0.01)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert finished.is_set()

    asyncio.run(scenario())


def test_codex_probe_reports_installed_capabilities_and_rejects_old_cli(tmp_path, monkeypatch):
    fake_codex(tmp_path, monkeypatch, "raise RuntimeError('must not run model during probe')")
    probe = CodexBackend().probe()
    assert probe.version == "0.160.0"
    assert probe.capabilities.resume and not probe.capabilities.steer
    binary = tmp_path / "codex"
    binary.write_text(binary.read_text().replace("0.160.0", "0.90.0"))
    with pytest.raises(BackendError, match="unsupported.*version"):
        CodexBackend().probe()


@pytest.mark.parametrize("changes", [
    {"user_id": "bob"}, {"tenant_id": "other"}, {"project_id": "other"},
    {"policy_version": "2"}, {"sandbox_required": True},
])
def test_codex_resume_is_bound_to_identity_and_authority(tmp_path, monkeypatch, changes):
    fake_codex(tmp_path, monkeypatch, SUCCESS)
    base = dict(user_id="alice", tenant_id="tenant", project_id="project")
    first = asyncio.run(CodexBackend().execute(BackendRequest("first", str(tmp_path), security(tmp_path, **base))))
    with pytest.raises(BackendError, match="binding mismatch"):
        asyncio.run(CodexBackend().execute(BackendRequest(
            "resume", str(tmp_path), security(tmp_path, **{**base, **changes}), session_id=first.session_id)))


def test_codex_rejects_unknown_session_and_changed_workspace(tmp_path, monkeypatch):
    fake_codex(tmp_path, monkeypatch, SUCCESS)
    with pytest.raises(BackendError, match="unknown backend session"):
        asyncio.run(CodexBackend().execute(BackendRequest(
            "resume", str(tmp_path), security(tmp_path), session_id="foreign-session")))
    asyncio.run(CodexBackend().execute(BackendRequest("first", str(tmp_path), security(tmp_path))))
    other = tmp_path / "other"
    other.mkdir()
    with pytest.raises(BackendError, match="binding mismatch"):
        asyncio.run(CodexBackend().execute(BackendRequest(
            "resume", str(other), security(other), session_id="session-123")))
    with pytest.raises(BackendError, match="binding mismatch"):
        asyncio.run(CodexBackend(sandbox="read-only").execute(BackendRequest(
            "resume", str(tmp_path), security(tmp_path), session_id="session-123")))


def test_codex_rejects_unmappable_permissions_and_project_config(tmp_path, monkeypatch):
    fake_codex(tmp_path, monkeypatch, "open('launched', 'w').write('bad')\n" + SUCCESS)
    for permissions in (PermissionSet(denied=frozenset({"tool.shell"})),
                        PermissionSet(allowed=frozenset({"backend.codex", "tool.read"})),):
        with pytest.raises(BackendError, match="cannot enforce"):
            asyncio.run(CodexBackend().execute(BackendRequest(
                "test", str(tmp_path), security(tmp_path, permissions=permissions))))
    (tmp_path / ".codex").mkdir()
    (tmp_path / ".codex" / "config.toml").write_text('[mcp_servers.bad]\ncommand="bad"')
    with pytest.raises(BackendError, match="project .codex"):
        asyncio.run(CodexBackend().execute(BackendRequest("test", str(tmp_path), security(tmp_path))))
    assert not (tmp_path / "launched").exists()


def test_session_lock_is_cross_process_and_released_after_crash(tmp_path):
    store = BackendSessionStore()
    script = '''
import sys, time
from LightAgent import BackendSessionStore
with BackendSessionStore(sys.argv[1]).lock("workspace", sys.argv[2]):
    print("locked", flush=True)
    time.sleep(30)
'''
    import subprocess
    process = subprocess.Popen([sys.executable, "-c", script, str(store.directory), str(tmp_path)],
                               stdout=subprocess.PIPE, text=True)
    try:
        assert process.stdout.readline().strip() == "locked"
        with pytest.raises(BackendError, match="busy"):
            with BackendSessionStore().lock("workspace", str(tmp_path)):
                pytest.fail("overlapping lock")
    finally:
        process.kill()
        process.wait(timeout=5)
        process.stdout.close()
    with BackendSessionStore().lock("workspace", str(tmp_path)):
        pass


def test_two_backend_instances_cannot_share_workspace(tmp_path, monkeypatch):
    fake_codex(tmp_path, monkeypatch, "print(json.dumps({'type':'thread.started','thread_id':'session-123'}), flush=True)\ntime.sleep(30)")
    async def scenario():
        started = threading.Event()
        first = asyncio.create_task(CodexBackend().execute(BackendRequest(
            "first", str(tmp_path), security(tmp_path),
            on_event=lambda e: started.set() if e.type == "backend.event" else None)))
        try:
            for _ in range(500):
                if started.is_set():
                    break
                await asyncio.sleep(0.01)
            assert started.is_set()
            with pytest.raises(BackendError, match="busy"):
                await CodexBackend().execute(BackendRequest("second", str(tmp_path), security(tmp_path)))
        finally:
            first.cancel()
            with pytest.raises(asyncio.CancelledError):
                await first
    asyncio.run(scenario())
    fake_codex(tmp_path, monkeypatch, SUCCESS)
    resumed = asyncio.run(CodexBackend().execute(BackendRequest(
        "continue after cancellation", str(tmp_path), security(tmp_path), session_id="session-123")))
    assert resumed.status == "completed"


def test_local_session_scope_checked_before_history_is_read(tmp_path, monkeypatch):
    fake_codex(tmp_path, monkeypatch, SUCCESS)
    agent = LightAgent(backend="codex", auto_discover_skills=False)
    result = agent.run("private", workspace=str(tmp_path), session_id="local", user_id="alice", result_format="object")
    assert not result.error
    before = len(agent.get_session().events)
    with pytest.raises(BackendError, match="binding mismatch"):
        agent.run("read", workspace=str(tmp_path), session_id="local", user_id="bob")
    assert len(agent.get_session().events) == before


def test_native_history_resume_requires_original_store(tmp_path):
    from LightAgent import NativeBackend, BackendSessionStore
    def factory():
        agent = LightAgent(model="test", api_key="test", auto_discover_skills=False)
        agent.client = SimpleNamespace(chat=SimpleNamespace(completions=NativeCompletions()))
        return agent
    provider = LocalWorkspaceProvider(allow_host_execution=True)
    (tmp_path / "README.md").write_text("DR007")
    first = asyncio.run(NativeBackend(factory, provider).execute(BackendRequest(
        "read", str(tmp_path), security(tmp_path))))
    with pytest.raises(BackendError, match="history is unavailable"):
        asyncio.run(NativeBackend(factory, provider).execute(BackendRequest(
            "continue", str(tmp_path), security(tmp_path), session_id=first.session_id)))


def test_external_native_configuration_cannot_be_silently_ignored(tmp_path):
    for options in ({"api_key": "unused"}, {"base_url": "http://invalid"},
                    {"provider": "litellm"}, {"skills_directories": ["skills"]}):
        with pytest.raises(ValueError, match="does not support"):
            LightAgent(backend="codex", **options)
    agent = LightAgent(backend="codex", auto_discover_skills=False)
    with pytest.raises(ValueError, match="cannot enforce"):
        agent.run("test", workspace=str(tmp_path), max_tool_iterations=1)


def test_native_resume_restores_history_across_instances_and_rejects_scope_changes(tmp_path):
    from LightAgent import SqliteSessionStore
    (tmp_path / "README.md").write_text("DR007")
    history = SqliteSessionStore(str(tmp_path.parent / (tmp_path.name + "-history.sqlite3")))
    def agent():
        value = LightAgent(name="persistent-native", model="test", api_key="test", auto_discover_skills=False,
                           session_store=history,
                           execution_provider=LocalWorkspaceProvider(allow_host_execution=True))
        value.client = SimpleNamespace(chat=SimpleNamespace(completions=NativeCompletions()))
        return value
    first = agent()
    assert not first.run("first private request", workspace=str(tmp_path),
                         session_id="native-history", user_id="alice", result_format="object").error
    second = agent()
    assert not second.run("continue", workspace=str(tmp_path), session_id="native-history",
                          user_id="alice", result_format="object").error
    messages = second.client.chat.completions.calls[0]["messages"]
    assert "first private request" in str(messages)
    with pytest.raises(BackendError, match="binding mismatch"):
        agent().run("continue", workspace=str(tmp_path), session_id="native-history", user_id="bob")


def test_codex_permission_mapping_is_explicit(tmp_path, monkeypatch):
    fake_codex(tmp_path, monkeypatch, """
for flag in ('--strict-config', '--ignore-user-config', '--skip-git-repo-check'):
    assert flag in sys.argv
for setting in ('approval_policy="never"', 'sandbox_workspace_write.network_access=false',
                'sandbox_workspace_write.exclude_slash_tmp=true',
                'sandbox_workspace_write.exclude_tmpdir_env_var=true', 'features.apps=false',
                'features.hooks=false', 'web_search="disabled"', 'allow_login_shell=false'):
    assert setting in sys.argv
assert '--dangerously-bypass-approvals-and-sandbox' not in sys.argv
""" + SUCCESS)
    result = asyncio.run(CodexBackend().execute(BackendRequest("test", str(tmp_path), security(tmp_path))))
    assert result.status == "completed", result.error


def test_codex_rejects_missing_probe_options_and_keeps_errors_secret_free(tmp_path, monkeypatch):
    fake_codex(tmp_path, monkeypatch, SUCCESS)
    binary = tmp_path / "codex"
    binary.write_text(binary.read_text().replace("--strict-config", "--unsupported"))
    with pytest.raises(BackendError, match="missing required options"):
        CodexBackend().probe()
    fake_codex(tmp_path, monkeypatch, "sys.stderr.write('authentication failed: SECRET_PAYLOAD'); sys.exit(1)")
    result = asyncio.run(CodexBackend().execute(BackendRequest("test", str(tmp_path), security(tmp_path))))
    assert "authentication" in result.error
    assert "SECRET_PAYLOAD" not in result.error


def test_control_state_cannot_be_worker_writable(tmp_path, monkeypatch):
    fake_codex(tmp_path, monkeypatch, SUCCESS)
    with pytest.raises(BackendError, match="outside"):
        asyncio.run(CodexBackend(session_store=BackendSessionStore(tmp_path / "state")).execute(
            BackendRequest("test", str(tmp_path), security(tmp_path))))


def test_backend_events_cannot_mutate_result_after_completion(tmp_path, monkeypatch):
    fake_codex(tmp_path, monkeypatch, SUCCESS + "print(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':'replaced'}}))")
    with pytest.raises(BackendError, match="terminal"):
        asyncio.run(CodexBackend().execute(BackendRequest("test", str(tmp_path), security(tmp_path))))


def test_expired_request_does_not_leave_backend_busy(tmp_path, monkeypatch):
    from datetime import datetime, timedelta, timezone
    fake_codex(tmp_path, monkeypatch, SUCCESS)
    backend = CodexBackend()
    deadline = (datetime.now(timezone.utc) + timedelta(seconds=0.05)).isoformat()
    request = BackendRequest("expired", str(tmp_path), security(tmp_path, deadline=deadline))
    time.sleep(0.1)
    with pytest.raises(PermissionError, match="expired"):
        asyncio.run(backend.execute(request))
    result = asyncio.run(backend.execute(BackendRequest("new", str(tmp_path), security(tmp_path))))
    assert result.status == "completed"


def test_native_factory_cannot_return_busy_instance(tmp_path):
    from LightAgent import NativeBackend
    agent = LightAgent(model="test", api_key="test", auto_discover_skills=False)
    agent._workspace_lock.acquire()
    try:
        backend = NativeBackend(lambda: agent, LocalWorkspaceProvider(allow_host_execution=True))
        with pytest.raises(BackendError, match="busy"):
            asyncio.run(backend.execute(BackendRequest("new", str(tmp_path), security(tmp_path))))
    finally:
        agent._workspace_lock.release()


@pytest.mark.parametrize("session_id", ["--last", "-x", "../foreign"])
def test_codex_session_id_cannot_be_a_cli_option(tmp_path, monkeypatch, session_id):
    fake_codex(tmp_path, monkeypatch, SUCCESS)
    with pytest.raises(ValueError, match="invalid Codex session"):
        asyncio.run(CodexBackend().execute(BackendRequest(
            "continue", str(tmp_path), security(tmp_path), session_id=session_id)))


def test_codex_network_is_explicit_and_session_bound(tmp_path, monkeypatch):
    fake_codex(tmp_path, monkeypatch, "assert 'sandbox_workspace_write.network_access=true' in sys.argv\n" + SUCCESS)
    store=BackendSessionStore(tmp_path.parent/(tmp_path.name+'-network-state'))
    result=asyncio.run(CodexBackend(network_access=True,session_store=store).execute(
        BackendRequest('test',str(tmp_path),security(tmp_path))))
    assert result.status=='completed'
    with pytest.raises(BackendError,match='binding'):
        asyncio.run(CodexBackend(session_store=store).execute(BackendRequest(
            'resume',str(tmp_path),security(tmp_path),session_id=result.session_id)))
    with pytest.raises(PermissionError):
        asyncio.run(CodexBackend(network_access=True,session_store=store).execute(BackendRequest(
            'test',str(tmp_path),SecurityContext(resources=frozenset({str(tmp_path.resolve())})))))
    with pytest.raises(ValueError):CodexBackend(network_access=True,sandbox='read-only')
