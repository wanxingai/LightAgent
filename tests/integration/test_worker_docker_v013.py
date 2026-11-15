"""Real Worker source + real Docker; scripted model responses, no API keys."""
import asyncio
from contextlib import contextmanager
from dataclasses import replace
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import threading
import time
from types import SimpleNamespace

import pytest

from LightAgent import (AgentRuntime, ApprovalToken, BackendRequest, BackendSessionStore,
    CancellationToken, CapabilityGate, ExecutionLimits, ExecutionRequirements, ExecutionService,
    LightAgent, LocalWorkspaceProvider, NativeBackend, SecurityContext, SqliteSessionStore)
from LightAgent.backends import BackendError

pytestmark = pytest.mark.skipif(os.getenv("LIGHTAGENT_WORKER_DOCKER_INTEGRATION") != "1",
                               reason="opt in to real Worker/Docker integration")


@pytest.fixture
def provider_type():
    if os.getenv("LIGHTWORKER_SOURCE"):
        source = Path(os.environ["LIGHTWORKER_SOURCE"]).resolve(strict=True)
        sys.path.insert(0, str(source / "src"))
    from lightworker.lightagent_execution import DockerWorkspaceProvider
    if os.getenv("LIGHTAGENT_EXPECT_INSTALLED") == "1":
        import LightAgent
        import lightworker
        assert "installed" in LightAgent.__file__ and "installed" in lightworker.__file__
    # Opt-in failures are failures, not skips masquerading as acceptance.
    DockerWorkspaceProvider(image=os.environ["LIGHTAGENT_WORKER_IMAGE"]).probe()
    return DockerWorkspaceProvider


def context(work):
    return SecurityContext(user_id="alice", tenant_id="acme", project_id="integration",
        resources=frozenset({str(work.resolve())}), sandbox_required=True, network_allowed=True)


def opened(provider_type, work, *, approval=False, token=None):
    provider = provider_type(image=os.environ["LIGHTAGENT_WORKER_IMAGE"], require_approval=approval,
        protected_patterns=["protected.txt"], sensitive_read_patterns=[".env"])
    return provider.open(str(work), context=context(work), gate=CapabilityGate(), cancellation_token=token or CancellationToken())


def test_real_worker_isolation_edit_and_no_host_mount(provider_type, tmp_path):
    work = tmp_path / "work"
    work.mkdir()
    (work / "protected.txt").write_text("keep")
    session = opened(provider_type, work)
    try:
        security = session.sandbox.call("security_probe", {})
        assert security == dict(ok=True, uid=10001, root_write_allowed=False,
                                docker_socket_exists=False, network_available=False)
        inspected = json.loads(subprocess.run(["docker", "inspect", session.sandbox.container_name],
            capture_output=True, text=True, check=True).stdout)[0]
        assert inspected["HostConfig"]["ReadonlyRootfs"] is True
        assert inspected["HostConfig"]["CapDrop"] == ["ALL"]
        mounts = [m for m in inspected["Mounts"] if m["Type"] == "bind"]
        assert len(mounts) == 1 and mounts[0]["Source"] == str(work.resolve())
        assert inspected["HostConfig"]["Memory"] > 0 and inspected["HostConfig"]["PidsLimit"] > 0
        created = session.edit_file("result.txt", "old\n")
        session.edit_file("result.txt", "new", "old", created["sha256"])
        assert (work / "result.txt").read_text() == "new\n"
        for path in ("../escape", "protected.txt", ".env"):
            with pytest.raises(BackendError):
                session.edit_file(path, "blocked")
        with pytest.raises(BackendError):
            session.edit_file("result.txt", "stale", "new", created["sha256"])
        session.edit_file("check.py", "print(6 * 7)\n")
        assert session.shell('python check.py', 20)["output"].strip() == "42"
        with pytest.raises(BackendError):
            session.shell("bash -c true", 20)
    finally:
        name = session.sandbox.container_name
        session.close()
    assert subprocess.run(["docker", "container", "inspect", name], capture_output=True).returncode != 0


def test_real_worker_exact_approval_and_replay_rejection(provider_type, tmp_path):
    session = opened(provider_type, tmp_path, approval=True)
    (tmp_path / "check.py").write_text("print(7)\n")
    command = 'python check.py'
    args = {"command": command, "timeout": 20}
    try:
        with pytest.raises(PermissionError):
            session.shell(command, 20)
        wrong = ApprovalToken.issue("workspace.shell", args, session.context, resource=str(tmp_path.resolve()))
        with pytest.raises(PermissionError):
            session.shell(command, 21, approval_token=wrong)
        token = ApprovalToken.issue("workspace.shell", args, session.context, resource=str(tmp_path.resolve()))
        assert session.shell(command, 20, approval_token=token)["output"].strip() == "7"
        with pytest.raises(PermissionError):
            session.shell(command, 20, approval_token=token)
    finally:
        session.close()


class ModelFixture:
    def __init__(self, command):
        self.command, self.calls = command, []
    def create(self, **params):
        self.calls.append(params)
        if len(self.calls) == 1:
            call = SimpleNamespace(id="docker-command", function=SimpleNamespace(name="shell",
                arguments=json.dumps(dict(command=self.command, timeout=60))))
            message = SimpleNamespace(content=None, tool_calls=[call])
        else:
            message = SimpleNamespace(content="fixture completed", tool_calls=None)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def factory(provider_type, root, command, clients):
    def agent():
        value = LightAgent(name="docker-child", model="fixture", api_key="fixture-not-real",
                           auto_discover_skills=False, session_store=SqliteSessionStore(root / "native.sqlite3"))
        client = ModelFixture(command)
        clients.append(client)
        value.client = SimpleNamespace(chat=SimpleNamespace(completions=client))
        return value
    return NativeBackend(agent, provider_type(image=os.environ["LIGHTAGENT_WORKER_IMAGE"], require_approval=False),
                         session_store=BackendSessionStore(root / "bindings"))


def test_real_docker_child_session_cold_resume_and_identity_binding(provider_type, tmp_path):
    work = tmp_path / "work"
    work.mkdir()
    clients = []
    (work / "check.py").write_text("print(41 + 1)\n")
    command = 'python check.py'
    class Child:
        name = "docker-child"
        async def arun(self, query):
            backend = factory(provider_type, tmp_path, command, clients)
            return (await backend.execute(BackendRequest(query, str(work), context(work),
                session_id="continuous-child", timeout=60))).content
    runtime = AgentRuntime(session_store=SqliteSessionStore(tmp_path / "parent.sqlite3"))
    runtime.open_session("parent")
    child = runtime.subagents.register(Child(), persistent=True)
    assert asyncio.run(runtime.subagents.run(child.agent_id, "first private question", lease_seconds=120)) == "fixture completed"
    resumed = subprocess.run([sys.executable, str(Path(__file__).parents[1] / "fixtures" / "worker_docker_cold_resume.py"),
        str(tmp_path), child.agent_id], env=os.environ.copy(), capture_output=True, text=True, timeout=90)
    assert resumed.returncode == 0, resumed.stderr
    summary = json.loads(resumed.stdout.strip().splitlines()[-1])
    assert summary["pid"] != os.getpid() and summary["restored_history"]
    assert summary["result"] == "fixture completed" and summary["jobs"] == 2
    backend = factory(provider_type, tmp_path, command, clients)
    with pytest.raises(BackendError, match="binding mismatch"):
        asyncio.run(backend.execute(BackendRequest("foreign", str(work), replace(context(work), user_id="bob"),
            session_id="continuous-child", timeout=60)))


def test_real_docker_parent_cancel_stops_child_container(provider_type, tmp_path):
    work = tmp_path / "work"
    work.mkdir()
    clients = []
    (work / "wait.py").write_text("from pathlib import Path\nimport time\nPath('started').write_text('yes')\ntime.sleep(60)\n")
    command = "python wait.py"
    backend = lambda: factory(provider_type, tmp_path, command, clients)
    service = ExecutionService(tmp_path / "control", backend_factories={"docker": backend})
    kwargs = dict(backend="docker", security_context=context(work), requirements=ExecutionRequirements(isolation="docker"),
                  limits=ExecutionLimits(timeout=120, lease_seconds=30))
    parent = service.submit("parent", work, **kwargs)
    parent.pause()
    child = service.submit("child", work, parent_id=parent.id, **kwargs)
    errors = []
    def serve():
        try:
            service.serve_forever(poll_interval=.05)
        except BaseException as error:
            errors.append(error)
    thread = threading.Thread(target=serve)
    thread.start()
    try:
        deadline = time.monotonic() + 45
        while not (work / "started").exists():
            assert time.monotonic() < deadline, (child.status(), errors)
            time.sleep(.1)
        names = subprocess.run(["docker", "ps", "--filter", "name=lightworker-la", "--format", "{{.Names}}"],
                               capture_output=True, text=True, check=True).stdout.splitlines()
        assert names
        parent.cancel()
        while child.status()["status"] != "cancelled":
            assert time.monotonic() < deadline, (child.status(), errors)
            time.sleep(.1)
        assert child.budget()["used"]["backend_calls"] == 1
        assert all(subprocess.run(["docker", "inspect", name], capture_output=True).returncode != 0 for name in names)
    finally:
        service.stop()
        thread.join(45)
    assert not thread.is_alive() and not errors


def test_docker_only_never_falls_back_and_provider_changes_pin_native_profile(provider_type, tmp_path):
    work = tmp_path / "work"
    work.mkdir()
    local = lambda: NativeBackend(lambda: None, LocalWorkspaceProvider(allow_host_execution=True))
    service = ExecutionService(tmp_path / "control", backend_factories={"host": local})
    with pytest.raises(PermissionError, match="Docker-only"):
        service.submit("must not run", work, backend="host", security_context=context(work),
                       requirements=ExecutionRequirements(isolation="docker"))
    with pytest.raises(BackendError, match="image"):
        provider_type(image="lightagent-missing-image:never-pull").probe()
    first = NativeBackend(lambda: None, provider_type(image=os.environ["LIGHTAGENT_WORKER_IMAGE"], require_approval=False))
    second = NativeBackend(lambda: None, provider_type(image=os.environ["LIGHTAGENT_WORKER_IMAGE"], require_approval=True))
    assert first.probe().version != second.probe().version
