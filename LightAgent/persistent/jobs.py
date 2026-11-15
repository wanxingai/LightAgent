"""Durable external jobs, explicitly authorized by the host application.

Job runners outlive the supervisor and report using an execution nonce. A lost
runner is uncertain, never retried or killed using a persisted PID alone.
"""
import argparse
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import sqlite3
import stat
import subprocess
import sys
import threading
import time
from .store import ControlStore, StateConflict, RecordBudgetExceeded, uid
from .legacy_storage import read_control_limits
from ..backends import BackendSessionStore, BackendError
from ..backends.process import run_process
from ..cancellation import CancellationToken
from .storage import StorageBudget, StorageBudgetExceeded
from .ledger import BudgetLedger, LedgerLimitExceeded
from ..security import canonical_digest
from ..job_lifecycle import JobConflict, identity as job_identity, transition as job_transition


def job_status(handle, job_id):
    from ..job_lifecycle import view
    record = handle.store.get('job', job_id)
    if not record or record['agent'] != handle.id:
        raise KeyError(job_id)
    return dict(job_id=job_id, **view(record))


@dataclass(frozen=True)
class _JobControlPolicy:
    """Bound both the unmonitored interval and the final database write wait."""
    poll_interval: float = .2
    lock_timeout: float = .2
    unavailable_timeout: float = 10
    finalize_timeout: float = 10
    retry_base: float = .05
    retry_max: float = .5

    def __post_init__(self):
        if any(type(value) not in (int, float) or not math.isfinite(value) or value <= 0
               for value in vars(self).values()) or self.retry_base > self.retry_max:
            raise ValueError('job control timing must be finite, positive and bounded')


def _database_busy(exc):
    if not isinstance(exc, sqlite3.OperationalError):
        return False
    code = getattr(exc, 'sqlite_errorcode', None)
    if code is not None:
        return (code & 255) in (getattr(sqlite3, 'SQLITE_BUSY', 5), getattr(sqlite3, 'SQLITE_LOCKED', 6))
    # Python versions without SQLite error codes expose these exact messages.
    return str(exc) in ('database is locked', 'database table is locked', 'database schema is locked')


@contextmanager
def _job_transaction(store, timeout):
    # Job cancellation must not inherit the control store's ten-second lock
    # wait on every heartbeat. Keep this private to runners; schema is unchanged.
    db = sqlite3.connect(store.path, timeout=max(0, timeout))
    db.row_factory = sqlite3.Row
    try:
        db.execute('BEGIN IMMEDIATE')
        yield db
        db.commit()
    except BaseException:
        db.rollback()
        raise
    finally:
        db.close()


def _receipt_path(store, job_id):
    name = hashlib.sha256(job_id.encode()).hexdigest()+'.json'
    return store.root/'job-recovery'/name


def _write_receipt(store, job, outcome):
    """Small control-plane evidence survives a database that cannot be written."""
    path = _receipt_path(store, job['id'])
    path.parent.mkdir(exist_ok=True, mode=0o700)
    if path.parent.is_symlink() or path.parent.stat().st_mode & 0o077:
        raise PermissionError('job recovery directory must be private and not a symlink')
    payload = json.dumps({'id': job['id'], 'agent': job['agent'], 'nonce': job['nonce'],
                          'outcome': outcome}, allow_nan=False).encode()
    if len(payload) > 4096:
        raise ValueError('job recovery receipt exceeds control budget')
    temporary = path.with_name(path.name+'.'+uid()+'.tmp')
    try:
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _read_receipt(store, job):
    path = _receipt_path(store, job['id'])
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0))
        with os.fdopen(fd, 'rb') as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size > 4096 or info.st_mode & 0o077:
                return None
            receipt = json.loads(stream.read(4097))
        if not isinstance(receipt, dict) or any(receipt.get(key) != job[key] for key in ('id', 'agent', 'nonce')):
            return None
        outcome = receipt.get('outcome')
        if (not isinstance(outcome, dict) or outcome.get('status') not in
                ('completed', 'failed', 'cancelled', 'timed_out', 'uncertain')
                or not set(outcome) <= {'status', 'finished_at', 'returncode', 'result_file', 'error', 'diagnostic', 'output_cursor'}):
            return None
        finished = outcome.get('finished_at')
        if type(finished) not in (int, float) or not math.isfinite(finished) or finished < 0:
            return None
        if 'returncode' in outcome and type(outcome['returncode']) is not int:
            return None
        if 'output_cursor' in outcome and (type(outcome['output_cursor']) is not int or not 0 <= outcome['output_cursor'] <= 131073):
            return None
        if 'result_file' in outcome and outcome['result_file'] != str(store.root/'job-output'/job['id']):
            return None
        if any(key in outcome and (not isinstance(outcome[key], str) or len(outcome[key]) > 512)
               for key in ('error', 'diagnostic')):
            return None
        return outcome
    except (OSError, ValueError, TypeError, OverflowError):
        return None


def _apply_outcome(store, job, outcome, db):
    current = store.get('job', job['id'], db)
    if not current or current['nonce'] != job['nonce'] or current['agent'] != job['agent']:
        raise StateConflict('stale job runner')
    if current['status'] not in ('running', 'launching'):
        raise StateConflict('job already resolved; preserve its host decision')
    try:
        current = job_transition(current, outcome['status'], expected=job_identity(job),
                                 runner_stopped=outcome['status'] != 'uncertain',
                                 **{k: v for k, v in outcome.items() if k != 'status'})
    except JobConflict as exc:
        raise StateConflict(str(exc)) from exc
    ledger = BudgetLedger(store)
    reservation = store.get('budget_reservation', ledger._key(job['agent'], 'job-'+job['id']), db)
    if reservation and reservation['status'] == 'reserved':
        ledger.settle(job['agent'], 'job-'+job['id'], {'tool_calls': 1}, unknown=('seconds',), db=db)
    store.put('job', current, db)


def _finish_job(store, job, outcome, policy):
    # Recovery evidence is not raw process output. Its small bounded allocation
    # uses control-plane headroom even when the managed output budget is full.
    receipt_written = False
    try:
        _write_receipt(store, job, outcome)
        receipt_written = True
    except OSError:
        pass  # Still try the database when the filesystem cannot save evidence.
    deadline = time.monotonic()+policy.finalize_timeout
    delay = policy.retry_base
    while True:
        remaining = deadline-time.monotonic()
        try:
            with _job_transaction(store, min(policy.lock_timeout, max(0, remaining))) as db:
                _apply_outcome(store, job, outcome, db)
            _receipt_path(store, job['id']).unlink(missing_ok=True)
            return True
        except Exception as exc:
            remaining = deadline-time.monotonic()
            if not _database_busy(exc) or remaining <= 0:
                if not receipt_written:
                    raise  # Both channels failed; supervisor must reconcile.
                return False  # Release the Job lock; poll_jobs imports evidence.
            time.sleep(min(delay, remaining))
            delay = min(policy.retry_max, delay*2)


def submit_job(handle, argv, *, workspace=None, timeout=300, allow_host_execution=False, idempotency_key=None):
    if allow_host_execution is not True:
        raise PermissionError('external jobs require explicit trusted host execution authorization')
    if not isinstance(argv, (list, tuple)) or not argv or not all(isinstance(x,str) and '\0' not in x for x in argv):
        raise ValueError('job argv must be a nonempty list of strings')
    if len(str(argv)) > 32768 or not math.isfinite(timeout) or not 0 < timeout <= 86400:
        raise ValueError('job command or deadline exceeds budget')
    from .redaction import contains_secret
    if contains_secret(str(argv)):
        raise ValueError('job arguments cannot contain known credentials')
    a = handle.status()
    if a.get('requirements', {}).get('isolation') in ('sandbox', 'docker'):
        raise PermissionError('host jobs cannot bypass the required execution isolation')
    # Explicit host API; cannot enlarge a sandboxed agent's authority.
    security = a['security']
    if security['sandbox_required'] or not security['network_allowed'] or security['permissions']['allowed'] or security['permissions']['denied'] or security['permissions']['max_risk'] != 'L3':
        raise PermissionError('host jobs cannot enforce this agent security policy')
    workspace = Path(workspace or a['workspace']).resolve(strict=True)
    if str(workspace) != a['workspace']:
        raise PermissionError('job workspace must match the authorized project')
    record = dict(id=uid(), agent=handle.id, nonce=uid(), argv=list(argv), workspace=str(workspace),
                  timeout=timeout, status='queued', cancel=False, created_at=time.time(), notified=False)
    record.update(owner_id=handle.id, attempt_id=record['nonce'], epoch=1, output_cursor=0, runner_stopped=True)
    if idempotency_key is not None and (not isinstance(idempotency_key, str) or not 1 <= len(idempotency_key) <= 256):
        raise ValueError('invalid Job idempotency key')
    identity = canonical_digest({'agent': handle.id, 'key': idempotency_key})
    fingerprint = canonical_digest({'argv': list(argv), 'workspace': str(workspace), 'timeout': timeout})
    with handle.store.transaction() as db:
        owner = handle.store.get('agent', handle.id, db)
        if owner['desired'] == 'cancelled':
            raise StateConflict('cancelled parent cannot submit Jobs')
        if idempotency_key is not None:
            previous = handle.store.get('job_submission', identity, db)
            if previous:
                if previous['fingerprint'] != fingerprint:
                    raise StateConflict('Job idempotency key reused for different parameters')
                return handle.store.get('job', previous['job_id'], db)
        count = db.execute('SELECT count(*) FROM records WHERE agent=?', (handle.id,)).fetchone()[0]
        limits = read_control_limits(owner)
        if count >= limits.get('max_records', 10000):
            raise RecordBudgetExceeded('persistent record budget reached')
        outstanding = handle.store.scan('job', handle.id, db,
                                       filters={'status': ('queued', 'launching', 'running', 'uncertain')})
        if sum(1 for _ in outstanding) >= 100:
            raise ValueError('outstanding job budget reached')
        handle.store.put('job', record, db)
        if idempotency_key is not None:
            handle.store.put('job_submission', dict(id=identity, agent=handle.id,
                            fingerprint=fingerprint, job_id=record['id']), db)
        handle.store.event(handle.id, 'job.queued', {'job_id': record['id']}, db)
    return record


def _claim_queued_job(service, job_id):
    """Reserve a slot in the same transaction that claims the durable job.

    Count launching jobs too: the detached runner may not have started yet.
    Uncertain jobs retain their slot until the host explicitly reconciles them;
    losing a runner heartbeat does not prove all its effects have stopped.
    """
    global_limit = getattr(service, 'max_concurrent_jobs', 8)
    if type(global_limit) is not int or global_limit < 1:
        raise ValueError('max_concurrent_jobs must be a positive integer')
    with service.store.transaction() as db:
        current = service.store.get('job', job_id, db)
        if not current or current['status'] != 'queued':
            return None
        owner = service.store.get('agent', current['agent'], db)
        if current['cancel'] or not owner or owner['desired'] == 'cancelled':
            current = job_transition(current, 'cancelled', finished_at=time.time(), runner_stopped=True)
            service.store.put('job', current, db)
            return None
        per_agent = read_control_limits(owner).get('max_concurrent_jobs', 2)
        if type(per_agent) is not int or per_agent < 1:
            raise ValueError('agent max_concurrent_jobs must be a positive integer')
        active = list(service.store.scan('job', db=db,
                      filters={'status': ('launching', 'running', 'uncertain')}))
        if len(active) >= global_limit or sum(j['agent'] == current['agent'] for j in active) >= per_agent:
            return None
        ledger = BudgetLedger(service.store)
        if service.store.get('budget_account', current['agent'], db) is None:
            ledger.open(current['agent'], limits=owner.get('budget') or {}, parent=owner.get('parent_id'), db=db)
        try:
            ledger.reserve(current['agent'], 'job-'+current['id'], {'tool_calls': 1, 'seconds': current['timeout']}, db=db)
        except LedgerLimitExceeded:
            service.store.event(current['agent'], 'job.budget_blocked', {'job_id': current['id']}, db)
            return None
        current = job_transition(current, 'launching', launched_at=time.time(), owner_id=current['agent'], runner_stopped=False)
        service.store.put('job', current, db)
        service.store.event(current['agent'], 'job.launching', {'job_id': current['id']}, db)
        return current


def reconcile_job(handle, job_id, *, status, note):
    """Host acknowledgement of an uncertain runner, without replaying it.

    The host must independently check effects/processes before freeing the slot.
    A new execution is a separate explicit submit_job call with a new nonce.
    """
    if status not in ('completed', 'failed', 'cancelled'):
        raise ValueError('reconciled job status must be completed, failed, or cancelled')
    if not isinstance(note, str) or not note.strip() or len(note.encode()) > 4096:
        raise ValueError('reconciliation requires a host note of at most 4096 bytes')
    from .redaction import contains_secret
    if contains_secret(note):
        raise ValueError('reconciliation note contains a known credential')
    with handle.store.transaction() as db:
        job = handle.store.get('job', job_id, db)
        if not job or job['agent'] != handle.id:
            raise KeyError('job not found')
        if job['status'] != 'uncertain':
            raise StateConflict('only uncertain jobs may be reconciled')
        job = job_transition(job, status, reconcile=True, reconciliation_note=note,
                             reconciled_at=time.time(), finished_at=time.time(), runner_stopped=True)
        ledger = BudgetLedger(handle.store)
        reservation = handle.store.get('budget_reservation', ledger._key(handle.id, 'job-'+job_id), db)
        if reservation and reservation['status'] == 'reserved':
            ledger.settle(handle.id, 'job-'+job_id, {'tool_calls': 1}, unknown=('seconds',), db=db)
        handle.store.put('job', job, db)
        handle.store.event(handle.id, 'job.reconciled', {'job_id': job_id, 'status': status}, db)
        return job


def poll_jobs(service):
    for job in service.store.scan('job'):
        if job['status'] == 'queued':
            # Claim before launch. A crash between claim/spawn remains uncertain.
            job = _claim_queued_job(service, job['id'])
            if job is None:
                continue
            env = dict(os.environ)
            env['PYTHONPATH'] = str(Path(__file__).resolve().parents[2])+os.pathsep+env.get('PYTHONPATH','')
            try:
                subprocess.Popen([sys.executable,'-m','LightAgent.persistent.jobs','--root',str(service.root),'--job',job['id']],
                             stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                             start_new_session=True,env=env,cwd=service.root)
            except OSError:
                with service.store.transaction() as db:
                    current=service.store.get('job',job['id'],db)
                    _apply_outcome(service.store, job,
                                   dict(status='failed',error='runner_launch_failed',finished_at=time.time()), db)
        elif job['status'] in ('running','launching') and (time.time()-job.get('heartbeat_at',job.get('launched_at',0)) > 10
                                                        or _receipt_path(service.store, job['id']).exists()):
            try:
                with service.bindings.lock('job', job['id']):
                    recovered = False
                    with service.store.transaction() as db:
                        current = service.store.get('job',job['id'],db)
                        if current['status'] in ('running','launching'):
                            outcome = _read_receipt(service.store, current)
                            if outcome is not None:
                                _apply_outcome(service.store, current, outcome, db)
                                recovered = True
                                service.store.event(job['agent'], 'job.recovered',
                                                    {'job_id': job['id'], 'status': outcome['status']}, db)
                            else:
                                current = job_transition(current, 'uncertain', error='runner_result_unavailable',
                                    diagnostic='Runner exited without a verifiable outcome; inspect effects before reconciliation.')
                                service.store.put('job',current,db)
                                service.store.event(job['agent'],'job.uncertain',{'job_id':job['id']},db)
                    if recovered:
                        _receipt_path(service.store, job['id']).unlink(missing_ok=True)
            except BackendError:
                pass
        elif job['status'] in ('completed','failed','cancelled','timed_out','uncertain') and not job['notified']:
            if job.get('notification_retry_at', 0) > time.time():
                continue
            # Durable outbox: enqueue is idempotent if supervisor exits before ack.
            owner = service.store.get('agent', job['agent'])
            if owner and owner.get('domain') == 'execution' and owner['status'] in ('completed','failed','cancelled'):
                with service.store.transaction() as db:
                    current = service.store.get('job', job['id'], db)
                    current['notified'] = True
                    service.store.put('job', current, db)
                    service.store.event(job['agent'], 'job.notification', {'job_id': job['id'], 'status': job['status']}, db)
                continue
            try:
                service.store.enqueue(job['agent'], 'External job '+job['id']+' ended as '+job['status']+
                                      '. Inspect its result through the host job API before relying on it.', key='job-'+job['id'])
            except (RecordBudgetExceeded, StorageBudgetExceeded) as exc:
                # Keep the outbox pending. Capacity exhaustion in one researcher
                # must not take down the supervisor or other researchers.
                with service.store.transaction() as db:
                    current = service.store.get('job', job['id'], db)
                    attempts = current.get('notification_attempts', 0)+1
                    current.update(notification_attempts=attempts,
                                   notification_error='inbox_record_budget' if isinstance(exc,RecordBudgetExceeded) else 'storage_budget',
                                   notification_retry_at=time.time()+min(300, 2**min(attempts, 8)))
                    service.store.put('job', current, db)
                continue
            with service.store.transaction() as db:
                current=service.store.get('job',job['id'],db)
                current['notified']=True
                current.pop('notification_error', None)
                current.pop('notification_retry_at', None)
                service.store.put('job',current,db)


def run_job(root, job_id, *, control_policy=None):
    policy = control_policy or _JobControlPolicy()
    store=ControlStore(root)
    bindings=BackendSessionStore(store.root/'bindings')
    with bindings.lock('job',job_id):
        with store.transaction() as db:
            job=store.get('job',job_id,db)
            if not job or job['status'] != 'launching':
                return
            job = job_transition(job, 'running', expected=job_identity(job), heartbeat_at=time.time())
            store.put('job',job,db)
        token=CancellationToken()
        if job['cancel']:
            token.cancel('job cancelled before start')
        done=threading.Event()
        monitor_failure = {}

        def stop_unmonitored(error, diagnostic):
            monitor_failure.update(error=error, diagnostic=diagnostic)
            token.cancel(diagnostic)

        def watch():
            unavailable_since = None
            delay = policy.poll_interval
            retry_delay = policy.retry_base
            while not done.wait(delay):
                started = time.monotonic()
                remaining = (policy.unavailable_timeout if unavailable_since is None else
                             policy.unavailable_timeout-(started-unavailable_since))
                if remaining <= 0:
                    stop_unmonitored('job_monitor_unavailable',
                                     'Job control database stayed busy beyond its monitoring deadline; process cancelled.')
                    return
                try:
                    with _job_transaction(store, min(policy.lock_timeout, remaining)) as db:
                        current=store.get('job',job_id,db)
                        if not current or job_identity(current) != job_identity(job) or current['nonce'] != job['nonce'] or current['status'] != 'running':
                            raise StateConflict('job runner no longer owns this execution')
                        owner = store.get('agent', current['agent'], db)
                        if current['cancel'] or not owner or owner['desired'] == 'cancelled':
                            token.cancel('job cancelled')
                        current['heartbeat_at']=time.time()
                        store.put('job',current,db)
                    unavailable_since = None
                    delay = policy.poll_interval
                    retry_delay = policy.retry_base
                except Exception as exc:
                    if not _database_busy(exc):
                        # Never classify I/O/corruption/authority failures as a
                        # retryable lock conflict, or put raw errors in prompts.
                        stop_unmonitored('job_monitor_error',
                                         'Job control monitor failed with '+type(exc).__name__+'; process cancelled.')
                        return
                    unavailable_since = started if unavailable_since is None else unavailable_since
                    remaining = policy.unavailable_timeout-(time.monotonic()-unavailable_since)
                    if remaining <= 0:
                        stop_unmonitored('job_monitor_unavailable',
                                         'Job control database stayed busy beyond its monitoring deadline; process cancelled.')
                        return
                    delay = min(retry_delay, remaining)
                    retry_delay = min(policy.retry_max, retry_delay*2)

        thread=threading.Thread(target=watch,daemon=True,name='lightagent-job-monitor')
        thread.start()
        result = None
        try:
            owner=store.get('agent',job['agent'])
            if owner is None:
                raise StateConflict('Job owner is missing')
            budget=StorageBudget(store,read_control_limits(owner).get('max_storage_bytes', 512*1024*1024))
            with budget.watch(token):
                result=run_process(job['argv'],cwd=job['workspace'],token=token,timeout=job['timeout'],output_limit=65536)
            status=result.status if result.status!='completed' or result.returncode==0 else 'failed'
            outcome = dict(status=status,returncode=result.returncode,finished_at=time.time())
            # Raw stdout/stderr stays in an owner-only local result file, never
            # automatically admitted into prompts, memory, or panel events.
            output=store.root/'job-output'
            output.mkdir(exist_ok=True,mode=0o700)
            file=output/job_id
            budget.write_bytes(file,(result.stdout+'\n'+result.stderr).encode())
            outcome['result_file'] = str(file)
            outcome['output_cursor'] = file.stat().st_size
        except StorageBudgetExceeded:
            outcome = dict(status='failed',error='storage_budget',finished_at=time.time())
        except Exception as exc:
            # run_process cleans its group in finally. A cleanup failure itself
            # cannot be claimed as confirmed termination: retain uncertainty.
            outcome = dict(status='uncertain',error='job_execution_error',finished_at=time.time(),
                           diagnostic='Job execution ended with '+type(exc).__name__+'; inspect effects before reconciliation.')
        finally:
            done.set()
            # The monitor only executes short SQLite transactions and Event
            # waits, so joining cannot retain the former ten-second DB wait.
            thread.join()
        if monitor_failure:
            if result is not None:
                outcome['status'] = 'failed'
            outcome.update(monitor_failure)
        _finish_job(store, job, outcome, policy)


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',required=True)
    parser.add_argument('--job',required=True)
    args=parser.parse_args()
    run_job(args.root,args.job)
