from LightResearch import enable_legacy_api
enable_legacy_api()
"""Large workspace copying must not starve the service control database."""
import sqlite3
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from LightAgent import AgentService, AgentHandle, ResearchContract
from LightAgent.persistent.store import ResearchStore
from LightAgent.persistent.storage import StorageBudget, StorageBudgetExceeded
import LightResearch.contracts as contract_module
import LightResearch.service as service_module


def test_read_only_store_reconnect_does_not_reserve_writer(tmp_path):
    store = ResearchStore(tmp_path/'state')
    with store.transaction() as db:
        store.put('agent', {'id':'researcher', 'contract':{}, 'value':'committed'}, db)
        store.event('researcher','created',{},db)
    started = time.monotonic()
    with store.transaction() as writer:
        record = store.get('agent','researcher',writer)
        record['value'] = 'uncommitted'
        store.put('agent',record,writer)
        # The constructor used by every panel request must also be read-only
        # when the schema is initialized, not just get/list themselves.
        reader = ResearchStore(store.root)
        assert reader.get('agent','researcher')['value'] == 'committed'
        assert reader.list('agent')[0]['value'] == 'committed'
        assert list(reader.scan('agent'))[0]['value'] == 'committed'
        assert reader.events('researcher')[0]['type'] == 'created'
        with reader.read_transaction() as db:
            with pytest.raises(sqlite3.OperationalError, match='readonly'):
                db.execute('DELETE FROM records')
    assert time.monotonic()-started < 2
    assert store.get('agent','researcher')['value'] == 'uncommitted'


def test_large_repeated_snapshot_keeps_heartbeat_reads_and_inbox_responsive(tmp_path, monkeypatch):
    work = tmp_path/'workspace'
    work.mkdir()
    contents = b'x'*(80*1024)
    for i in range(555):
        directory = work/str(i//37)
        directory.mkdir(exist_ok=True)
        (directory/(str(i)+'.txt')).write_bytes(contents)
    contract = ResearchContract(max_storage_bytes=512*1024*1024)
    service = AgentService(tmp_path/'state')
    handle = service.submit('large local snapshot fixture',work,backend='codex',contract=contract)
    handle.pause()  # This test performs no model or CLI calls.
    original_read = contract_module.read_bounded
    started = threading.Event()
    scans = []
    original_used = StorageBudget.used

    def slow_read(path, limit):
        if threading.current_thread().name == 'bulk-snapshot':
            started.set()
            time.sleep(.001)
        return original_read(path,limit)

    def count_used(budget):
        if threading.current_thread().name == 'bulk-snapshot':
            scans.append(time.monotonic())
        return original_used(budget)

    monkeypatch.setattr(contract_module,'read_bounded',slow_read)
    monkeypatch.setattr(StorageBudget,'used',count_used)
    errors = []
    manifests = []

    def supervise():
        try:
            service.serve_forever(poll_interval=.01)
        except BaseException as exc:
            errors.append(exc)

    def snapshot():
        try:
            source = work
            for name in ('inputs','work','attempt-inputs'):
                target = service.root/name/'large-fixture'
                manifests.append(service._snapshot(source,target,contract))
                source = target
        except BaseException as exc:
            errors.append(exc)

    supervisor = threading.Thread(target=supervise,daemon=True)
    copier = threading.Thread(target=snapshot,name='bulk-snapshot',daemon=True)
    supervisor.start()
    copier.start()
    latencies, heartbeats = [], []
    receipt = None
    try:
        assert started.wait(5)
        deadline = time.monotonic()+30
        while copier.is_alive() and time.monotonic()<deadline:
            begin = time.monotonic()
            connected = AgentHandle.connect(handle.id,root=service.root)
            connected.status()
            connected.events()
            connected.records('cycle')
            heartbeat = service.store.get('service','main')
            if heartbeat:
                heartbeats.append(heartbeat['heartbeat_at'])
            if receipt is None:
                receipt = connected.send('Keep this direction while copying local data.')
            latencies.append(time.monotonic()-begin)
            time.sleep(.01)
        copier.join(5)
        assert not copier.is_alive(), 'bounded snapshot did not complete'
        assert not errors, errors
        assert len(manifests) == 3
        assert all(len(m['files']) == 555 and m['bytes'] > 40*1024*1024 for m in manifests)
        assert len(set(heartbeats)) >= 5, 'heartbeat did not advance during snapshot copying'
        assert max(latencies) < 2, 'control-plane reads or inbox writes were starved'
        assert len(scans) <= 8, 'snapshot rescanned all stored files for individual writes'
        assert handle.receipt(receipt['id'])['status'] == 'persisted'
        assert handle.status()['backend_calls'] == 0
    finally:
        service.stop()
        copier.join(5)
        supervisor.join(10)
    assert not supervisor.is_alive()
    assert not errors, errors
    assert service.store.get('service','main')['status'] == 'stopped'


def test_snapshot_batches_keep_cross_process_budget_admission(tmp_path):
    store = ResearchStore(tmp_path/'state')
    script = '''import sys,time,shutil
from pathlib import Path
from LightAgent.persistent.store import ResearchStore
from LightAgent.persistent.storage import StorageBudget,StorageBudgetExceeded
store=ResearchStore(sys.argv[1]);budget=StorageBudget(store,450*1024)
destination=store.root/sys.argv[2]
try:
 with budget.batch():
  for i in range(4):
   budget.write_bytes(destination/str(i),b'x'*(64*1024))
   time.sleep(.03)
 print('written')
except StorageBudgetExceeded:
 shutil.rmtree(destination,ignore_errors=True)
 print('blocked')
'''
    children = [subprocess.Popen([sys.executable,'-c',script,str(store.root),'copy-'+str(i)],
                stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) for i in range(2)]
    results = []
    try:
        for child in children:
            output,error = child.communicate(timeout=25)
            assert child.returncode == 0, error
            results.append(output.strip())
    finally:
        for child in children:
            if child.poll() is None:
                child.kill();child.wait(timeout=5)
    assert sorted(results) == ['blocked','written']
    assert StorageBudget(store,450*1024).used() < 450*1024
    assert len(list(store.root.glob('copy-*'))) == 1


def test_snapshot_final_recheck_cleans_only_its_own_copy(tmp_path, monkeypatch):
    source = tmp_path/'source';source.mkdir()
    (source/'evidence').write_text('input')
    service = AgentService(tmp_path/'state')
    contract = ResearchContract()
    target = service.root/'inputs'/'copy'
    first = service._snapshot(source,target,contract)
    with pytest.raises(FileExistsError):
        service._snapshot(source,target,contract)
    assert (target/'evidence').read_text() == 'input'
    assert first['bytes'] == 5
    original_check = StorageBudget.check
    def fail_final(budget, allocation=0):
        if getattr(budget._local,'remaining',None) is not None:
            raise StorageBudgetExceeded('unmanaged concurrent growth')
        return original_check(budget,allocation)
    monkeypatch.setattr(StorageBudget,'check',fail_final)
    second = service.root/'inputs'/'other'
    with pytest.raises(StorageBudgetExceeded):
        service._snapshot(source,second,contract)
    assert not second.exists()
    assert (target/'evidence').read_text() == 'input'


def test_snapshot_does_not_delete_destination_created_by_another_writer(tmp_path, monkeypatch):
    source = tmp_path/'source';source.mkdir()
    service = AgentService(tmp_path/'state')
    target = service.root/'inputs'/'concurrent'
    assert not target.exists()
    def competing_copy(*args, **kwargs):
        # Deterministic interleaving: the destination did not exist at method
        # entry, but another writer published it before the copier could claim
        # it. A stale preflight exists() must not authorize its deletion.
        target.mkdir(parents=True)
        (target/'sentinel').write_text('another successful snapshot')
        raise FileExistsError(str(target))
    monkeypatch.setattr(service_module,'snapshot_workspace',competing_copy)
    with pytest.raises(FileExistsError):
        service._snapshot(source,target,ResearchContract())
    assert (target/'sentinel').read_text() == 'another successful snapshot'


def test_supervisor_retries_busy_heartbeat_without_stopping(tmp_path, monkeypatch):
    service = AgentService(tmp_path/'state')
    heartbeat = service._heartbeat
    attempts = []
    def temporary_busy(status='running'):
        attempts.append(status)
        if len(attempts) <= 2:
            exc = sqlite3.OperationalError('database is locked')
            exc.sqlite_errorcode = getattr(sqlite3,'SQLITE_BUSY',5)
            raise exc
        return heartbeat(status)
    monkeypatch.setattr(service,'_heartbeat',temporary_busy)
    service.serve_forever(poll_interval=.001,max_ticks=2)
    assert attempts.count('running') == 4
    assert service.store.get('service','main')['status'] == 'stopped'
    def actual_fault(status='running'):
        raise sqlite3.OperationalError('disk I/O error')
    monkeypatch.setattr(service,'_heartbeat',actual_fault)
    with pytest.raises(sqlite3.OperationalError,match='disk I/O'):
        service._heartbeat_if_available()
