from LightResearch import enable_legacy_api
enable_legacy_api()
"""Resource limits, explicit retries and retention that preserve recovery evidence."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import threading
import time
from types import SimpleNamespace

import pytest

from LightAgent.backends import BackendSessionStore
from LightAgent.persistent.jobs import _claim_queued_job, poll_jobs, reconcile_job
from LightResearch.maintenance import prune_workspaces
from LightAgent.persistent.retries import BackendFailure, RetryPolicy, next_retry
from LightAgent.persistent.store import ResearchStore, StateConflict


@pytest.fixture
def store(tmp_path):
    store = ResearchStore(tmp_path/'state')
    with store.transaction() as db:
        for name in ('a', 'b', 'c'):
            store.put('agent', {'id':name, 'desired':'running', 'status':'waiting', 'next_wakeup_at':0,
                      'contract': {'max_concurrent_jobs':2, 'max_records':1000, 'max_storage_bytes':1024*1024}}, db)
    return store


def job(store, key, agent='a', **fields):
    value = {'id':key, 'agent':agent, 'status':'queued', 'cancel':False, 'notified':False,
             'nonce':'nonce-'+key, 'timeout':300, 'created_at':time.time(), **fields}
    with store.transaction() as db:
        store.put('job', value, db)
    return value


def service(store, global_limit=3):
    return SimpleNamespace(store=store, root=store.root, max_concurrent_jobs=global_limit,
                           bindings=BackendSessionStore(store.root/'bindings'))


def test_job_claim_enforces_global_and_owner_limits_under_concurrency(store):
    s = service(store)
    ids = []
    for aid in ('a', 'b', 'c'):
        for index in range(4):
            jid = aid+str(index)
            job(store, jid, agent=aid)
            ids.append(jid)
    with ThreadPoolExecutor(max_workers=12) as pool:
        claimed = [value for value in pool.map(lambda jid: _claim_queued_job(s, jid), ids) if value]
    assert len(claimed) == 3
    assert max(sum(j['agent'] == aid for j in claimed) for aid in ('a','b','c')) <= 2
    # A launching slot counts before any child heartbeat has been written.
    assert _claim_queued_job(s, 'c3') is None


def test_job_fifo_admission_and_cancel_before_launch(store, monkeypatch):
    s = service(store)
    job(store, 'first'); job(store, 'second'); job(store, 'third')
    job(store, 'cancelled', agent='b', cancel=True)
    job(store, 'other-owner', agent='b')
    spawned = []
    monkeypatch.setattr('LightAgent.persistent.jobs.subprocess.Popen', lambda argv, **kw: spawned.append(argv[-1]))
    poll_jobs(s)
    assert spawned == ['first', 'second', 'other-owner']
    assert store.get('job', 'third')['status'] == 'queued'
    assert store.get('job', 'cancelled')['status'] == 'cancelled'
    assert len(list(store.scan('job', filters={'status':('launching',)}))) == 3


def test_unknown_job_holds_slot_until_explicit_host_reconciliation(store):
    s = service(store, 1)
    job(store, 'unknown', status='uncertain')
    job(store, 'waiting')
    assert _claim_queued_job(s, 'waiting') is None
    handle = SimpleNamespace(store=store, id='a')
    with pytest.raises(KeyError):
        reconcile_job(SimpleNamespace(store=store, id='b'), 'unknown', status='failed', note='checked')
    with pytest.raises(ValueError):
        reconcile_job(handle, 'unknown', status='failed', note='')
    reconcile_job(handle, 'unknown', status='failed', note='Host confirmed child and descendants stopped.')
    assert _claim_queued_job(s, 'waiting')['status'] == 'launching'
    with pytest.raises(StateConflict):
        reconcile_job(handle, 'unknown', status='completed', note='duplicate')


def test_safe_retry_requires_structured_signal_and_bounds():
    p = RetryPolicy(max_retries=4, base_delay=2, max_delay=10, jitter=.2)
    transient = BackendFailure('connection rejected before dispatch', category='unavailable',
                                retryable=True, safe_to_retry=True)
    assert p.delay(transient, 1, random_value=0) == 1.6
    assert p.delay(transient, 1, random_value=1) == 2.4
    assert p.delay(transient, 4, random_value=1) == 10
    assert p.delay(transient, 5) is None
    assert next_retry(transient, 1, p, now=100, random_value=.5) == 102
    for exc in (RuntimeError('429 retryable safe before dispatch'), TimeoutError('before dispatch'),
                BackendFailure('maybe wrote data', retryable=True),
                BackendFailure('authentication', category='authentication', retryable=True, safe_to_retry=True),
                BackendFailure('unknown effects', category='unknown', retryable=True, safe_to_retry=True)):
        assert p.delay(exc, 1) is None
    rate_limited = BackendFailure('no dispatch', category='rate_limit', retryable=True,
                                   safe_to_retry=True, retry_after=7)
    assert p.delay(rate_limited, 1, random_value=0) == 7
    assert p.delay(BackendFailure('wait', retryable=True, safe_to_retry=True, retry_after=20), 1) is None


@pytest.mark.parametrize('fields', [{'max_retries':-1}, {'max_retries':True}, {'base_delay':0},
                                   {'max_delay':float('inf')}, {'jitter':1.1}])
def test_retry_configuration_rejects_unbounded_values(fields):
    with pytest.raises(ValueError):
        RetryPolicy(**fields)


def archived_cycle(store, key, **fields):
    work = store.root/'work'/key
    work.mkdir(parents=True)
    (work/'evidence.txt').write_bytes(b'verified observation')
    digest = hashlib.sha256(b'verified observation').hexdigest()
    blobs = store.root/'blobs'; blobs.mkdir(exist_ok=True)
    (blobs/digest).write_bytes(b'verified observation')
    for collection in ('inputs','attempt-inputs','graphs'):
        path = store.root/collection/key
        path.mkdir(parents=True)
        (path/'preserve.txt').write_text('frozen input or durable graph')
    with store.transaction() as db:
        store.put('cycle', {'id':key, 'agent':'a', 'status':'completed', 'finished_at':0,
                  'workspace':str(work), **fields}, db)
        store.put('experiment', {'id':key, 'agent':'a', 'published':True,
                  'artifacts':[{'blob':digest, 'sha256':digest, 'path':'evidence.txt'}]}, db)
    return work


def test_retention_dry_run_prunes_only_archived_duplicate_outputs(store):
    work = archived_cycle(store, 'finished')
    failed = archived_cycle(store, 'failed', status='failed')
    unknown = archived_cycle(store, 'uncertain', status='reconciling')
    preview = prune_workspaces(store, agent='a', older_than_seconds=0)
    assert preview['dry_run'] and preview['removed_bytes'] == 0 and work.exists()
    assert [x['record_id'] for x in preview['workspaces']] == ['finished']
    report = prune_workspaces(store, agent='a', dry_run=False, older_than_seconds=0)
    assert not work.exists() and failed.exists() and unknown.exists()
    assert report['removed_bytes'] == len(b'verified observation')
    for collection in ('inputs','attempt-inputs','graphs'):
        assert (store.root/collection/'finished'/'preserve.txt').exists()
    assert list((store.root/'blobs').iterdir())
    assert store.get('experiment', 'finished')['published']
    assert len(list(store.scan('workspace_archive'))) == 1


@pytest.mark.parametrize('retry_status', ['queued', 'running', 'uncertain'])
def test_retention_preserves_uncertain_candidate_and_pending_reevaluation(store, retry_status):
    for name in ('unknown-baseline','retry-baseline','active-attempt'):
        archived_cycle(store, name)
    with store.transaction() as db:
        store.put('candidate', {'id':'unknown-candidate', 'agent':'a', 'status':'uncertain', 'baseline_id':'unknown-baseline'}, db)
        store.put('candidate_retry', {'id':'re-evaluate', 'agent':'a', 'status':retry_status, 'baseline_id':'retry-baseline', 'source_candidate_id':'failed-candidate'}, db)
        store.put('attempt', {'id':'attempt', 'agent':'a', 'cycle_id':'active-attempt', 'status':'running'}, db)
    assert prune_workspaces(store, older_than_seconds=0)['workspaces'] == []


def test_retention_refuses_corrupt_archive_and_external_symlink(store, tmp_path):
    work = archived_cycle(store, 'finished')
    blob = next((store.root/'blobs').iterdir())
    blob.write_bytes(b'corrupted')
    assert prune_workspaces(store, older_than_seconds=0)['workspaces'] == []
    blob.write_bytes(b'verified observation')
    outside = tmp_path/'outside'; outside.mkdir()
    (outside/'important.txt').write_text('keep')
    (work/'external').symlink_to(outside, target_is_directory=True)
    prune_workspaces(store, dry_run=False, older_than_seconds=0)
    assert (outside/'important.txt').read_text() == 'keep'


def test_runtime_log_rotation_captures_real_descriptors_in_detached_process(tmp_path):
    root = tmp_path/'logs'; root.mkdir(mode=0o700)
    script = '''
import os, sys
from LightAgent.persistent.maintenance import runtime_logging
with runtime_logging(sys.argv[1], max_bytes=64, backups=2):
    os.write(1, b'A'*64)
    os.write(2, b'B'*64)
    os.write(1, b'C'*64)
    os.write(2, b'END')
'''
    result = subprocess.run([sys.executable, '-c', script, str(root)], capture_output=True, timeout=20)
    assert result.returncode == 0, result.stderr.decode()
    assert result.stdout == b'' and result.stderr == b''
    assert (root/'runner.log').read_bytes() == b'END'
    assert (root/'runner.log.1').read_bytes() == b'C'*64
    assert (root/'runner.log.2').read_bytes() == b'B'*64
    assert sum(p.stat().st_size for p in root.glob('runner.log*')) <= 3*64
    assert all(p.stat().st_mode & 0o077 == 0 for p in root.glob('runner.log*'))


def retry_service(tmp_path, failures, **contract_options):
    from LightAgent import AgentService, BackendResult, ResearchContract
    class Adapter:
        calls = []
        async def execute(self, request):
            self.calls.append(request)
            if len(self.calls) <= len(failures):
                raise failures[len(self.calls)-1]
            (Path(request.workspace)/'evidence.txt').write_text('a verified observation')
            return BackendResult(json.dumps({'summary':'retry worked', 'hypothesis':'one observation',
                'evidence':['evidence.txt'], 'next_action':'wait'}))
    work = tmp_path/'project'; work.mkdir()
    (work/'README.md').write_text('small local retry scenario')
    service = AgentService(tmp_path/'research-state', backend_factories={'fixture':Adapter})
    options = dict(max_safe_retries=2, retry_base_seconds=.02, retry_max_seconds=.1, task_timeout=5)
    options.update(contract_options)
    handle = service.submit('exercise retry', work, backend='fixture', contract=ResearchContract(**options))
    return service, handle, Adapter


def wait_for(predicate, timeout=10):
    until = time.monotonic()+timeout
    while time.monotonic() < until:
        value = predicate()
        if value:
            return value
        time.sleep(.01)
    raise AssertionError('expected condition did not become true')


def test_service_safe_transient_retries_are_charged_and_recorded(tmp_path):
    from LightAgent.cancellation import CancellationToken
    failures = [BackendFailure('not sent', category='unavailable', retryable=True, safe_to_retry=True),
                BackendFailure('rate limited before execution', category='rate_limit',
                               retryable=True, safe_to_retry=True, retry_after=.03)]
    s, h, adapter = retry_service(tmp_path, failures)
    cycle = s._claim(h.id, None)
    s._cycle(cycle, CancellationToken())
    saved = s.store.get('cycle', cycle['id'])
    assert saved['status'] == 'completed', saved
    assert saved['calls'] == h.status()['backend_calls'] == len(adapter.calls) == 3
    assert [r['retry_number'] for r in saved['retries']] == [1, 2]
    assert all(r['safe_to_retry'] and r['next_retry_at'] <= time.time() for r in saved['retries'])
    assert len({request.attempt_id for request in adapter.calls}) == 3
    assert len(list(s.store.scan('attempt', h.id))) == 3
    assert h.experiments()[0]['published']
    assert sum(e['type'] == 'backend.retry_scheduled' for e in h.events()) == 2


def test_completed_job_history_does_not_exhaust_pending_queue_budget(tmp_path):
    s, h, _ = retry_service(tmp_path, [])
    for index in range(100):
        job(s.store, 'historical-'+str(index), agent=h.id, status='completed', notified=True)
    accepted = h.submit_job([sys.executable, '-c', 'pass'], allow_host_execution=True)
    assert accepted['status'] == 'queued'
    assert len(list(s.store.scan('job', h.id))) == 101
    for index in range(99):
        job(s.store, 'pending-'+str(index), agent=h.id)
    with pytest.raises(ValueError, match='outstanding job budget'):
        h.submit_job([sys.executable, '-c', 'pass'], allow_host_execution=True)


@pytest.mark.parametrize('legacy', [True, False])
def test_job_submission_enforces_total_contract_record_capacity(tmp_path, legacy):
    from LightAgent.persistent.store import RecordBudgetExceeded
    # A research submission starts with version, owner, ledger, revision,
    # activation and submission records; fill to the configured cap explicitly.
    maximum = 16
    s, h, _ = retry_service(tmp_path, [], max_records=maximum)
    with s.store.transaction() as db:
        owner = s.store.get('agent', h.id, db)
        count = db.execute('SELECT count(*) FROM records WHERE agent=?', (h.id,)).fetchone()[0]
        assert count < maximum
        assert owner['limits']['max_records'] == owner['contract']['max_records'] == maximum
        if legacy:
            del owner['limits']
            s.store.put('agent', owner, db)
        for index in range(maximum - count):
            s.store.put('fixture', dict(id='capacity-' + str(index), agent=h.id), db)
    with pytest.raises(RecordBudgetExceeded):
        h.submit_job([sys.executable, '-c', 'pass'], allow_host_execution=True)


@pytest.mark.parametrize('failure', [
    BackendFailure('effect could have happened', retryable=True, safe_to_retry=False),
    BackendFailure('credential invalid', category='authentication', retryable=True, safe_to_retry=True),
    TimeoutError('result unknown'),
])
def test_service_does_not_retry_unknown_effects_or_auth(tmp_path, failure):
    from LightAgent.cancellation import CancellationToken
    s, h, adapter = retry_service(tmp_path, [failure])
    cycle = s._claim(h.id, None)
    s._cycle(cycle, CancellationToken())
    saved = s.store.get('cycle', cycle['id'])
    assert saved['status'] == 'failed'
    assert saved['calls'] == h.status()['backend_calls'] == len(adapter.calls) == 1
    assert not saved.get('retries')
    assert h.status()['status'] == 'blocked'
    assert h.experiments() == []


def test_service_safe_retries_obey_call_budget(tmp_path):
    from LightAgent.cancellation import CancellationToken
    s, h, adapter = retry_service(tmp_path, [BackendFailure('not sent', retryable=True, safe_to_retry=True)],
                                   max_backend_calls_per_cycle=1)
    cycle = s._claim(h.id, None)
    s._cycle(cycle, CancellationToken())
    saved = s.store.get('cycle', cycle['id'])
    assert saved['status'] == 'failed' and saved['calls'] == 1
    assert len(adapter.calls) == 1 and not saved.get('retries')


def test_interrupt_during_persistent_backoff_prevents_second_dispatch(tmp_path):
    from LightAgent.cancellation import CancellationToken
    s, h, adapter = retry_service(tmp_path, [BackendFailure('not sent', retryable=True, safe_to_retry=True)],
                                   retry_base_seconds=.8, retry_max_seconds=1)
    cycle = s._claim(h.id, None)
    token = CancellationToken()
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(s._cycle, cycle, token)
        wait_for(lambda: s.store.get('cycle',cycle['id']).get('retries'))
        h.interrupt()
        future.result(timeout=5)
    assert token.cancelled
    assert len(adapter.calls) == 1
    assert s.store.get('cycle',cycle['id'])['status'] == 'cancelled'


def test_supervisor_shutdown_drains_retry_without_cancelling_running_intent(tmp_path):
    s, h, adapter = retry_service(tmp_path, [BackendFailure('not sent', retryable=True, safe_to_retry=True)],
                                   retry_base_seconds=.3, retry_max_seconds=.5)
    errors = []
    def serve():
        try:
            s.serve_forever(poll_interval=.01)
        except BaseException as exc:
            errors.append(exc)
    thread = threading.Thread(target=serve)
    thread.start()
    try:
        wait_for(lambda: any(e['type']=='backend.retry_scheduled' for e in h.events()))
        s.stop()
        thread.join(timeout=10)
        assert not thread.is_alive() and not errors
        assert len(adapter.calls) == 2
        assert h.status()['desired'] == 'running' and h.experiments()[0]['published']
        assert s.store.get('service','main')['status'] == 'stopped'
    finally:
        s.stop(); thread.join(timeout=10)


def test_chat_failure_diagnostics_redact_known_credentials(tmp_path, monkeypatch):
    from LightAgent.cancellation import CancellationToken
    secret = 'test-sensitive-key-do-not-store-12345'
    monkeypatch.setenv('LIGHTAGENT_TEST_API_KEY', secret)
    error = RuntimeError('provider rejected credential '+secret+'; request was refused')
    s, h, adapter = retry_service(tmp_path, [error])
    message = h.open_chat().send('What is the current research status?')
    s._chat(message, CancellationToken())
    receipt = h.receipt(message['id'])
    expected = 'provider rejected credential [REDACTED]; request was refused'
    assert len(adapter.calls) == 1
    assert receipt['status'] == 'failed' and receipt['error'] == 'RuntimeError'
    assert receipt['diagnostic'] == expected
    assert 'response' not in receipt and 'applied_at' not in receipt
    events = h.events()
    failures = [event for event in events if event['type'] == 'chat.failed']
    assert len(failures) == 1
    assert failures[0]['data'] == {'message_id':message['id'], 'chat_id':message['chat_id'],
                                   'error_type':'RuntimeError', 'diagnostic':expected}
    assert not any(event['type'] == 'chat.completed' for event in events)
    assert secret not in json.dumps({'message':receipt, 'events':events})
