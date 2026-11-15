"""Credential-free execution, fencing, inheritance, and extension boundaries."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import os
import subprocess
import sys
import time

import pytest
from LightAgent import (BackendCapabilities, BackendProbe, BackendResult, ExecutionService,
    ExecutionHandle, ExecutionLimits, ExecutionRequirements, SecurityContext, LedgerLimitExceeded)
from LightAgent.persistent.store import StateConflict


class FixtureBackend:
    capabilities = BackendCapabilities(resume=True, isolation="docker", network_control=True)
    version = "1"
    calls = []

    def probe(self):
        return BackendProbe("fixture", self.version, self.capabilities)

    async def execute(self, request):
        self.calls.append(request)
        request.emit("output", content="untrusted output stays outside the event log")
        return BackendResult("completed: " + request.prompt, session_id=request.session_id or "fixture-session",
                             usage={"total_tokens": 2, "model_calls": 1, "tool_calls": 0, "cost": 0})


@pytest.fixture
def setup(tmp_path):
    FixtureBackend.calls = []
    work = tmp_path / "workspace"
    work.mkdir()
    service = ExecutionService(tmp_path / "state", backend_factories={"fixture": FixtureBackend})
    context = SecurityContext(user_id="alice", tenant_id="acme", project_id="demo",
                              resources=frozenset({str(work.resolve())}), sandbox_required=True)
    return service, work, context


def submit(setup, **kwargs):
    service, work, context = setup
    return service.submit("ordinary task", work, backend="fixture", security_context=context, **kwargs)


def test_ordinary_task_runs_without_research_contract_and_reconnects(setup):
    service, _, _ = setup
    handle = submit(setup, idempotency_key="once")
    assert submit(setup, idempotency_key="once").id == handle.id
    message = handle.send("keep evidence", idempotency_key="followup")
    service.serve_forever(poll_interval=.01, max_ticks=2)
    restored = ExecutionHandle.connect(handle.id, root=service.root)
    assert restored.status()["status"] == "completed"
    assert restored.status()["result"]["content"] == "completed: ordinary task\nHost follow-up messages:\nkeep evidence"
    assert restored.receipt(message["id"])["status"] == "applied"
    assert restored.budget()["used"]["backend_calls"] == 1
    assert any(event["type"] == "execution.progress" for event in handle.events())
    assert "untrusted output" not in str(handle.events())
    assert "contract" not in restored.status() and "active_version_id" not in restored.status()


def test_submission_key_collision_is_rejected(setup):
    service, work, context = setup
    submit(setup, idempotency_key="once")
    with pytest.raises(StateConflict):
        service.submit("different", work, backend="fixture", security_context=context, idempotency_key="once")


def test_ordinary_submission_cannot_corrupt_an_existing_research_root(setup):
    service, _, _ = setup
    with service.store.transaction() as db:
        service.store.put('agent', dict(id='legacy-research', contract={}, epoch=0), db)
    with pytest.raises(StateConflict, match='research'):
        submit(setup)
    assert len(list(service.store.scan('agent'))) == 1


def test_claim_is_atomic_across_service_instances(setup):
    service, _, _ = setup
    handle = submit(setup)
    other = ExecutionService(service.root, backend_factories={"fixture": FixtureBackend})
    with ThreadPoolExecutor(2) as pool:
        claims = list(pool.map(lambda instance: instance.claim(handle.id), [service, other]))
    assert sum(claim is not None for claim in claims) == 1
    assert handle.budget()["reserved"]["backend_calls"] == 1


def test_recovery_cannot_fence_another_live_supervisor(setup):
    from LightAgent import BackendError
    service, _, _ = setup
    handle = submit(setup)
    service.claim(handle.id)
    other = ExecutionService(service.root, backend_factories={'fixture': FixtureBackend})
    with service._supervisor_guard():
        with pytest.raises(BackendError):
            other.recover()
    assert handle.status()['status'] == 'running'


def test_cold_recovery_fences_attempt_and_never_replays_unknown_effects(setup):
    service, _, _ = setup
    handle = submit(setup)
    message = handle.send("review before running")
    attempt = service.claim(handle.id)
    restarted = ExecutionService(service.root, backend_factories={"fixture": FixtureBackend})
    restarted.serve_forever(poll_interval=.01, max_ticks=1)
    assert handle.status()["status"] == "reconciling"
    assert not FixtureBackend.calls
    assert handle.receipt(message["id"])["status"] == "uncertain"
    with pytest.raises(StateConflict):
        service.renew(attempt)
    with pytest.raises(StateConflict):
        handle.resume()
    handle.reconcile(action="retry", note="Host inspected the disposable workspace; retry is safe.")
    restarted.serve_forever(poll_interval=.01, max_ticks=1)
    assert handle.status()["status"] == "completed"
    assert handle.receipt(message["id"])["status"] == "applied"
    assert len(FixtureBackend.calls) == 1


def test_pause_prevents_claim_and_resume_is_explicit(setup):
    service, _, _ = setup
    handle = submit(setup)
    handle.pause()
    assert service.claim(handle.id) is None
    handle.resume()
    assert service.claim(handle.id)


def test_cancelled_uncertain_task_can_be_discarded_but_never_retried(setup):
    service, _, _ = setup
    handle = submit(setup)
    service.claim(handle.id)
    handle.cancel()
    service.recover()
    with pytest.raises(StateConflict):
        handle.reconcile(action='retry', note='Do not resurrect a cancelled task.')
    handle.reconcile(action='discard', note='Host inspected effects; keep the cancellation terminal.')
    assert handle.status()['status'] == 'cancelled'


def test_expired_attempt_cannot_publish_or_renew(setup):
    service, _, _ = setup
    handle = submit(setup)
    attempt = service.claim(handle.id)
    with service.store.transaction() as db:
        current = service.store.get("execution_attempt", attempt["id"], db)
        current["lease_until"] = time.time() - 1
        service.store.put("execution_attempt", current, db)
    with pytest.raises(StateConflict):
        service.renew(attempt)
    service._execute(attempt, __import__("LightAgent").CancellationToken())
    assert handle.status()["status"] == "failed"
    assert not FixtureBackend.calls


def test_changed_backend_profile_requires_host_reauthorization(setup, monkeypatch):
    service, _, _ = setup
    handle = submit(setup)
    monkeypatch.setattr(FixtureBackend, "version", "2")
    service.serve_forever(poll_interval=.01, max_ticks=1)
    assert handle.status()["status"] == "failed"
    assert not FixtureBackend.calls


def test_children_share_parent_budget_and_cancel_atomically(setup):
    service, _, _ = setup
    parent = submit(setup, budget={"backend_calls": 1})
    child = submit(setup, parent_id=parent.id)
    sibling = submit(setup, parent_id=parent.id)
    assert service.claim(child.id)
    with pytest.raises(LedgerLimitExceeded):
        service.claim(sibling.id)
    parent.cancel()
    assert child.status()["desired"] == sibling.status()["desired"] == "cancelled"
    with pytest.raises(StateConflict):
        submit(setup, parent_id=parent.id)


@pytest.mark.parametrize("field,value", [("network_allowed", True), ("sandbox_required", False),
                                        ("resources", frozenset()), ("user_id", "mallory")])
def test_child_cannot_widen_parent_security(setup, field, value):
    service, work, context = setup
    parent = submit(setup)
    with pytest.raises((ValueError, PermissionError)):
        service.submit("child", work, backend="fixture", security_context=replace(context, **{field: value}), parent_id=parent.id)


@pytest.mark.parametrize("isolation", ["none", "sandbox"])
def test_docker_only_rejects_host_or_cli_probe_without_executing(setup, isolation, monkeypatch):
    service, work, context = setup
    monkeypatch.setattr(FixtureBackend, "capabilities", BackendCapabilities(isolation=isolation, network_control=True))
    with pytest.raises(PermissionError):
        service.submit("task", work, backend="fixture", security_context=context,
                       requirements=ExecutionRequirements(isolation="docker"))
    assert not FixtureBackend.calls
    assert list(service.store.scan("agent")) == []


def test_unreported_cost_is_unknown_not_free_and_strict_cost_budget_fails_closed(setup):
    service, work, context = setup
    with pytest.raises(PermissionError, match="hard budget"):
        service.submit("cost limited", work, backend="fixture", security_context=context, budget={"cost": 1})


@pytest.mark.requires_lightresearch
def test_research_cannot_ignore_docker_only_requirements(setup, monkeypatch):
    from LightResearch import ResearchService
    service, work, context = setup
    monkeypatch.setattr(FixtureBackend, "capabilities", BackendCapabilities(network_control=True))
    researcher = ResearchService(service.root, backend_factories={"fixture": FixtureBackend})
    with pytest.raises(PermissionError):
        researcher.submit("research", work, backend="fixture", security_context=context,
                          requirements=ExecutionRequirements(isolation="docker"))
    assert not FixtureBackend.calls


def test_forward_execution_schema_is_not_silently_executed(setup):
    service, _, _ = setup
    handle = submit(setup)
    with service.store.transaction() as db:
        task = service.store.get('agent', handle.id, db)
        task['schema_version'] = 99
        service.store.put('agent', task, db)
    with pytest.raises(StateConflict, match='schema'):
        service.claim(handle.id)
    assert not FixtureBackend.calls


def test_backend_call_timeout_requires_reconciliation(setup, monkeypatch):
    service, work, context = setup
    class Slow(FixtureBackend):
        async def execute(self, request):
            self.calls.append(request)
            await asyncio.sleep(60)
    wait_for = asyncio.wait_for
    async def bounded_call(coroutine, timeout):
        assert timeout == 5
        # Time only the dispatched call, not database preparation on a busy runner.
        return await wait_for(coroutine, .03)
    monkeypatch.setattr(asyncio, "wait_for", bounded_call)
    service.backend_factories["slow"] = Slow
    handle = service.submit("bounded", work, backend="slow", security_context=context,
                            limits=ExecutionLimits(timeout=5))
    service.serve_forever(poll_interval=.005, max_ticks=2)
    assert len(FixtureBackend.calls) == 1
    assert handle.status()["status"] == "reconciling"
    attempt = service.store.get("execution_attempt", handle.status()["attempt_id"])
    assert attempt["dispatched"] and attempt["error"] == "TimeoutError"


def test_core_import_and_legacy_error_do_not_import_research_or_start_cli():
    script = '''
import sys
from LightAgent import LightAgent, ExecutionService
from LightAgent.extensions import ExtensionRequired
assert not any(name.startswith('LightResearch') for name in sys.modules)
try:
    LightAgent(backend='codex').run('x', mode='persistent', workspace='.')
except ExtensionRequired:
    pass
else:
    raise AssertionError('legacy research semantics silently changed')
assert not any(name.startswith('LightResearch') for name in sys.modules)
'''
    result = subprocess.run([sys.executable, "-c", script], env={**os.environ, "PATH": ""},
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
