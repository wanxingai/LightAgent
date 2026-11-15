"""Trusted-host Jobs use the same owner, cancellation and budget authority."""
import sys
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import pytest
from LightAgent import (BackendCapabilities, BackendProbe, BackendResult, ControlStore, ExecutionService,
                        ExecutionRequirements, SecurityContext)
from LightAgent.persistent.jobs import _claim_queued_job, run_job
from LightAgent.persistent.store import RecordBudgetExceeded, StateConflict


class HostFixture:
    capabilities = BackendCapabilities(budget_dimensions=("tool_calls",))

    def probe(self):
        return BackendProbe("trusted-host-fixture", "1", self.capabilities)

    async def execute(self, request):
        return BackendResult("fixture")


def make(tmp_path, *, budget=None):
    work = tmp_path / "work"
    work.mkdir()
    service = ExecutionService(tmp_path / "state", backend_factories={"host": HostFixture})
    context = SecurityContext(user_id="alice", tenant_id="acme", project_id="demo", network_allowed=True)
    handle = service.submit("host-owned task", work, backend="host", security_context=context,
        budget=budget, reservation={"tool_calls": 0} if budget else None)
    return service, handle


def test_job_submission_idempotency_and_parent_budget_are_shared(tmp_path):
    service, handle = make(tmp_path, budget={"tool_calls": 1})
    argv = [sys.executable, "-c", "pass"]
    first = handle.submit_job(argv, allow_host_execution=True, idempotency_key="one")
    assert handle.submit_job(argv, allow_host_execution=True, idempotency_key="one")["id"] == first["id"]
    with pytest.raises(StateConflict):
        handle.submit_job([sys.executable, "-c", "print(1)"], allow_host_execution=True, idempotency_key="one")
    second = handle.submit_job(argv, allow_host_execution=True)
    assert _claim_queued_job(service, first["id"])
    assert _claim_queued_job(service, second["id"]) is None
    assert handle.budget()["reserved"]["tool_calls"] == 1
    assert first["owner_id"] == handle.id and first["attempt_id"] == first["nonce"]


def test_parent_cancel_stops_owned_job_and_keeps_byte_cursor_output(tmp_path):
    service, handle = make(tmp_path)
    job = handle.submit_job([sys.executable, "-u", "-c", "import time; print('started', flush=True); time.sleep(5)"],
                            allow_host_execution=True, timeout=10)
    _claim_queued_job(service, job["id"])
    with ThreadPoolExecutor(1) as pool:
        future = pool.submit(run_job, service.root, job["id"])
        deadline = time.monotonic() + 5
        while service.store.get("job", job["id"])["status"] != "running":
            assert time.monotonic() < deadline
            time.sleep(.01)
        time.sleep(.1)
        handle.cancel()
        future.result(timeout=5)
    assert service.store.get("job", job["id"])["status"] == "cancelled"
    first = handle.read_job_output(job["id"], limit=2)
    second = handle.read_job_output(job["id"], after=first["next_cursor"])
    assert first["next_cursor"] == len(first["content"])
    assert second["next_cursor"] == len(first["content"]) + len(second["content"])
    assert "started" not in str(handle.events())


def test_docker_only_task_never_uses_host_job_opt_in(tmp_path, monkeypatch):
    monkeypatch.setattr(HostFixture, "capabilities", BackendCapabilities(isolation="docker", network_control=True))
    work = tmp_path / "work"
    work.mkdir()
    service = ExecutionService(tmp_path / "state", backend_factories={"docker": HostFixture})
    handle = service.submit("isolated", work, backend="docker",
        security_context=SecurityContext(user_id="alice", network_allowed=True),
        requirements=ExecutionRequirements(isolation="docker"))
    with pytest.raises(PermissionError, match="isolation"):
        handle.submit_job([sys.executable, "-c", "pass"], allow_host_execution=True)


def test_uncertain_job_reconciliation_releases_reservation_without_free_usage(tmp_path):
    service, handle = make(tmp_path)
    job = handle.submit_job([sys.executable, '-c', 'pass'], allow_host_execution=True)
    _claim_queued_job(service, job['id'])
    with service.store.transaction() as db:
        record = service.store.get('job', job['id'], db)
        record['status'] = 'uncertain'
        service.store.put('job', record, db)
    handle.reconcile_job(job['id'], status='cancelled', note='Host checked that no process remains.')
    budget = handle.budget()
    assert budget['reserved']['tool_calls'] == 0
    assert budget['used']['tool_calls'] == 1
    assert budget['unknown']['seconds'] == 1


@pytest.mark.parametrize("limit_field", ["contract", "limits"])
def test_saved_capacities_control_inbox_events_and_detached_job(tmp_path, limit_field):
    store = ControlStore(tmp_path / "state")
    work = tmp_path / "work"
    work.mkdir()
    capacities = dict(max_records=4, max_events=2, max_concurrent_jobs=1, max_storage_bytes=256 * 1024)
    owner = dict(id="owner", desired="paused", status="paused", **{limit_field: capacities})
    if limit_field == "limits":
        # A valid nonempty limits mapping takes precedence over legacy values.
        owner["contract"] = {name: value * 10 for name, value in capacities.items()}
    with store.transaction() as db:
        owner = store.put("agent", owner, db)
        for job_id in ("first", "second"):
            store.put("job", dict(id=job_id, agent="owner", nonce=job_id, status="queued",
                         cancel=False, timeout=5, workspace=str(work),
                         argv=[sys.executable, "-c", "from pathlib import Path; Path('ran').touch()"]), db)
    store.enqueue("owner", "only allowed message", "once")
    with pytest.raises(RecordBudgetExceeded):
        store.enqueue("owner", "would exceed saved limit", "extra")
    service = SimpleNamespace(store=store, max_concurrent_jobs=8)
    assert _claim_queued_job(service, "first")
    assert _claim_queued_job(service, "second") is None
    (store.root / "preexisting.bin").write_bytes(b"x" * capacities["max_storage_bytes"])
    runner = """
import importlib.abc, sys
class NoResearch(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith('LightResearch'):
            raise AssertionError('detached Job attempted to load the research extension')
sys.meta_path.insert(0, NoResearch())
from LightAgent.persistent.jobs import run_job
run_job(sys.argv[1], 'first')
assert 'LightResearch' not in sys.modules
"""
    environment = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1]), "PYTHONDONTWRITEBYTECODE": "1"}
    child = subprocess.run([sys.executable, "-c", runner, str(store.root)], cwd=work, env=environment,
                           timeout=30, capture_output=True, text=True)
    assert child.returncode == 0, child.stderr
    first = store.get("job", "first")
    assert first["status"] == "failed" and first["error"] == "storage_budget"
    assert not (work / "ran").exists()
    with store.transaction() as db:
        for _ in range(3):
            store.event("owner", "fixture", {}, db)
    assert len(store.events("owner")) == capacities["max_events"]
    assert store.get("agent", "owner") == owner
