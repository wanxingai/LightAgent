"""Real process/SQLite contention at the external Job control boundary."""
import json
import os
from pathlib import Path
import signal
import sqlite3
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest

from LightAgent.backends import BackendSessionStore
from LightAgent.persistent import jobs
from LightAgent.persistent.store import ResearchStore


pytestmark = pytest.mark.skipif(os.name != 'posix', reason='managed Job process groups require POSIX')


CHILD = r'''
import json, os, signal, subprocess, sys, time
from pathlib import Path
root = Path(sys.argv[1])
child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])
def stop(*args):
    raise SystemExit(0)
signal.signal(signal.SIGTERM, stop)
with (root/'launches').open('a') as stream:
    stream.write('once\n')
(root/'pids').write_text(json.dumps([os.getpid(), child.pid]))
try:
    while not (root/'finish').exists():
        time.sleep(.01)
finally:
    child.terminate()
    child.wait(timeout=1)
'''

RUNNER = r'''
import json, sqlite3, sys, threading
from contextlib import contextmanager
from pathlib import Path
from LightAgent.persistent import jobs
root, work, policy, fault = sys.argv[1:]
work = Path(work)
real = jobs._job_transaction
@contextmanager
def injected(store, timeout):
    target = 'lightagent-job-monitor' if fault == 'monitor_io' else 'MainThread'
    if fault and threading.current_thread().name == target and (work/'pids').exists():
        with (work/'faults').open('a') as stream:
            stream.write('once\n')
        raise sqlite3.OperationalError('disk I/O error: sensitive backend detail')
    with real(store, timeout) as db:
        yield db
jobs._job_transaction = injected
jobs.run_job(root, 'job', control_policy=jobs._JobControlPolicy(**json.loads(policy)))
'''


def eventually(predicate, timeout=5):
    deadline = time.monotonic()+timeout
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(.01)
    pytest.fail('timed out waiting for isolated Job test condition')


def alive(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    stat = Path('/proc')/str(pid)/'stat'
    if stat.exists():
        try:
            return not stat.read_text().rsplit(') ', 1)[-1].startswith('Z')
        except FileNotFoundError:
            return False
    return True


@pytest.fixture
def isolated_job(tmp_path):
    store = ResearchStore(tmp_path/'state')
    work = tmp_path/'work'
    work.mkdir()
    with store.transaction() as db:
        store.put('agent', {'id':'agent', 'desired':'running', 'status':'waiting', 'next_wakeup_at':0,
                           'contract': {'max_concurrent_jobs':2, 'max_records':1000,
                                        'max_storage_bytes':8*1024*1024}}, db)
        store.put('job', {'id':'job', 'agent':'agent', 'nonce':'execution-one', 'status':'launching',
                         'argv':[sys.executable, '-c', CHILD, str(work)], 'workspace':str(work),
                         'timeout':20, 'cancel':False, 'notified':False, 'created_at':time.time(),
                         'launched_at':time.time()}, db)
    processes = []

    def start(*, fault='', **overrides):
        policy = dict(poll_interval=.03, lock_timeout=.02, unavailable_timeout=1.5,
                      finalize_timeout=1.5, retry_base=.02, retry_max=.06)
        policy.update(overrides)
        env = dict(os.environ)
        env['PYTHONPATH'] = str(Path(__file__).resolve().parents[1])+os.pathsep+env.get('PYTHONPATH', '')
        process = subprocess.Popen([sys.executable, '-c', RUNNER, str(store.root), str(work),
                                    json.dumps(policy), fault], stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True, env=env, start_new_session=True)
        processes.append(process)
        eventually(lambda: (work/'pids').exists())
        return process

    yield SimpleNamespace(store=store, work=work, start=start,
                          service=SimpleNamespace(store=store, root=store.root, max_concurrent_jobs=8,
                                                  bindings=BackendSessionStore(store.root/'bindings')))
    # Only PIDs created by this isolated fixture; never inspect or signal a live
    # application Job. Cleanup also runs when an assertion fails mid-lock test.
    if (work/'pids').exists():
        for pid in json.loads((work/'pids').read_text()):
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
    for process in processes:
        if process.poll() is None:
            process.kill()
        process.communicate(timeout=5)


def assert_stopped(case, process):
    stdout, stderr = process.communicate(timeout=5)
    assert process.returncode == 0, stdout+stderr
    assert 'Exception in thread' not in stderr
    pids = json.loads((case.work/'pids').read_text())
    eventually(lambda: all(not alive(pid) for pid in pids))
    assert (case.work/'launches').read_text() == 'once\n'


def test_job_monitor_survives_busy_then_observes_cancel(isolated_job):
    case = isolated_job
    process = case.start()
    with case.store.transaction() as db:
        time.sleep(.25)  # Several actual SQLITE_BUSY retries, within the bound.
        assert process.poll() is None
        current = case.store.get('job', 'job', db)
        current['cancel'] = True
        case.store.put('job', current, db)
    assert_stopped(case, process)
    result = case.store.get('job', 'job')
    assert result['status'] == 'cancelled'
    assert 'error' not in result
    assert not jobs._receipt_path(case.store, 'job').exists()


def test_persistent_busy_cancels_group_and_recovers_outcome_without_replay(isolated_job):
    case = isolated_job
    process = case.start(unavailable_timeout=.2, finalize_timeout=.2)
    with case.store.transaction():
        # Keep the writer lock past BOTH bounded waits. The managed process
        # group must already be gone before its database outcome can be stored.
        assert_stopped(case, process)
        receipt = json.loads(jobs._receipt_path(case.store, 'job').read_text())
        assert receipt['nonce'] == 'execution-one'
        assert receipt['outcome']['status'] == 'failed'
        assert receipt['outcome']['error'] == 'job_monitor_unavailable'
        assert case.store.get('job', 'job')['status'] == 'running'
    jobs.poll_jobs(case.service)
    result = case.store.get('job', 'job')
    assert result['status'] == 'failed'
    assert result['error'] == 'job_monitor_unavailable'
    assert 'process cancelled' in result['diagnostic']
    assert not jobs._receipt_path(case.store, 'job').exists()
    jobs.poll_jobs(case.service)
    assert (case.work/'launches').read_text() == 'once\n'


def test_terminal_write_retries_busy_after_process_has_exited(isolated_job):
    case = isolated_job
    process = case.start()
    with case.store.transaction():
        (case.work/'finish').touch()
        eventually(lambda: jobs._receipt_path(case.store, 'job').exists())
        time.sleep(.2)
        assert process.poll() is None
        assert all(not alive(pid) for pid in json.loads((case.work/'pids').read_text()))
    assert_stopped(case, process)
    assert case.store.get('job', 'job')['status'] == 'completed'
    assert not jobs._receipt_path(case.store, 'job').exists()


def test_monitor_non_busy_error_cancels_without_retry_or_raw_error_leak(isolated_job):
    case = isolated_job
    process = case.start(fault='monitor_io')
    assert_stopped(case, process)
    result = case.store.get('job', 'job')
    assert result['status'] == 'failed'
    assert result['error'] == 'job_monitor_error'
    assert 'OperationalError' in result['diagnostic']
    assert 'sensitive backend detail' not in json.dumps(result)
    assert (case.work/'faults').read_text() == 'once\n'


def test_terminal_non_busy_error_keeps_receipt_for_supervisor(isolated_job):
    case = isolated_job
    process = case.start(fault='finalize_io')
    (case.work/'finish').touch()
    assert_stopped(case, process)
    assert case.store.get('job', 'job')['status'] == 'running'
    assert (case.work/'faults').read_text() == 'once\n'
    jobs.poll_jobs(case.service)
    assert case.store.get('job', 'job')['status'] == 'completed'
    assert not jobs._receipt_path(case.store, 'job').exists()


def test_recovery_receipt_cannot_publish_across_execution_nonce(isolated_job):
    case = isolated_job
    job = case.store.get('job', 'job')
    jobs._write_receipt(case.store, job, {'status':'completed', 'finished_at':time.time(), 'returncode':0})
    with case.store.transaction() as db:
        job['nonce'] = 'different-execution'
        case.store.put('job', job, db)
    jobs.poll_jobs(case.service)
    result = case.store.get('job', 'job')
    assert result['status'] == 'uncertain'
    assert result['error'] == 'runner_result_unavailable'
    assert jobs._receipt_path(case.store, 'job').exists()  # Preserve rejected evidence.


@pytest.mark.parametrize('invalid', [{'finished_at':float('nan')}, {'finished_at':10**350}, {'returncode':'success'},
                                  {'result_file':'/tmp/unrelated-output'}, {'diagnostic':['invalid']}])
def test_corrupt_recovery_receipt_requires_reconciliation(isolated_job, invalid):
    case = isolated_job
    job = case.store.get('job', 'job')
    jobs._write_receipt(case.store, job, {'status':'completed', 'finished_at':time.time(), 'returncode':0})
    path = jobs._receipt_path(case.store, 'job')
    value = json.loads(path.read_text())
    value['outcome'].update(invalid)
    path.write_text(json.dumps(value))
    jobs.poll_jobs(case.service)
    assert case.store.get('job', 'job')['status'] == 'uncertain'
    assert path.exists()


@pytest.mark.parametrize('code,expected', [(getattr(sqlite3, 'SQLITE_BUSY', 5), True), (getattr(sqlite3, 'SQLITE_LOCKED', 6), True),
                                        (getattr(sqlite3, 'SQLITE_BUSY', 5) | (2 << 8), True), (getattr(sqlite3, 'SQLITE_IOERR', 10), False)])
def test_only_sqlite_busy_and_locked_codes_are_retryable(code, expected):
    error = sqlite3.OperationalError('database is locked')
    error.sqlite_errorcode = code
    assert jobs._database_busy(error) is expected
    assert not jobs._database_busy(RuntimeError('database is locked'))
