"""Coroutine adapter for the shared Job lifecycle and Session authority."""

import asyncio
from contextlib import contextmanager, nullcontext
from contextvars import ContextVar
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
import inspect
from typing import Any
from uuid import uuid4

from .cancellation import CancellationToken, accepts_keyword
from .job_lifecycle import ACTIVE, JobConflict, expired, identity, positive_seconds, require_attempt, status_of, transition
from .session import _utc_now

_active_attempt = ContextVar("lightagent_job_attempt", default=None)


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    INTERRUPTED = "interrupted"


@dataclass
class JobRecord:
    name: str
    job_id: str = field(default_factory=lambda: uuid4().hex)
    status: JobStatus = JobStatus.PENDING
    owner_agent_id: str | None = None
    created_at: str = field(default_factory=_utc_now)
    started_at: str | None = None
    completed_at: str | None = None
    result: Any = None
    error: str | None = None
    idempotency_key: str | None = None
    cancellation_token_id: str | None = None
    lease_owner: str | None = None
    lease_epoch: int = 0
    lease_expires_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    output: list[Any] = field(default_factory=list)
    attempt_id: str | None = None
    parent_job_id: str | None = None
    output_cursor: int = 0
    runner_stopped: bool | None = None
    reconciliation_note: str | None = None
    notification_sent: bool | None = None

    def to_dict(self):
        value = asdict(self)
        value["status"] = self.status.value
        return value


class JobManager:
    """Live tasks are local; persisted Job events decide all state changes.

    SQLite adapters serialize read/check/append across processes. Other Session
    stores and standalone managers provide in-process coordination only.
    """

    def __init__(self, event_sink=None, inbox=None, *, state_scope=None, session_reader=None):
        self._records = {}
        self._tasks = {}
        self._cancellations = {}
        self._errors = {}
        self.manager_id = uuid4().hex
        self._event_sink = event_sink
        self._inbox = inbox
        self._state_scope = state_scope
        self._session_reader = session_reader

    @contextmanager
    def _state(self):
        with self._state_scope() if self._state_scope else nullcontext():
            if self._session_reader:
                self.restore(self._session_reader(), clear_live=False)
            yield

    def _put(self, event, record):
        if self._event_sink:
            self._event_sink(event, {"job": record.to_dict()})
        self._records[record.job_id] = record
        return deepcopy(record)

    def _transition(self, record, target, event, **kwargs):
        payload = transition(record.to_dict(), target, **kwargs)
        payload["status"] = JobStatus(payload["status"])
        return self._put(event, JobRecord(**payload))

    def start(self, name, operation, *, owner_agent_id=None, metadata=None, idempotency_key=None,
              cancellation_token=None, lease_seconds=None, parent_job_id=None, max_active=None):
        loop = asyncio.get_running_loop()
        if lease_seconds is not None:
            positive_seconds(lease_seconds)
        if idempotency_key is not None and (not isinstance(idempotency_key, str) or not idempotency_key.strip()):
            raise ValueError("idempotency_key must not be empty")
        with self._state():
            if self._session_reader:
                controls = [e.type for e in self._session_reader().events
                            if e.type in {"session.cancelled", "session.resumed"}]
                if controls and controls[-1] == "session.cancelled":
                    raise JobConflict("cancelled Session cannot start Jobs; host must explicitly resume")
            for previous in self._records.values():
                if idempotency_key is not None and previous.idempotency_key == idempotency_key:
                    # Names remain display labels (v0.10 compatibility), not operation identity.
                    if (previous.owner_agent_id != owner_agent_id or previous.metadata != (metadata or {})
                            or previous.parent_job_id != parent_job_id):
                        raise JobConflict("job idempotency key reused for different parameters")
                    if inspect.iscoroutine(operation):
                        operation.close()
                    return deepcopy(previous)
            if max_active is not None and sum(
                    r.metadata.get("kind") == "subagent" and (status_of(r.to_dict()) in ACTIVE or r.runner_stopped is not True)
                    for r in self._records.values()) >= max_active:
                raise RuntimeError("subagent concurrency limit reached")
            if parent_job_id is not None:
                parent = self._records[parent_job_id]
                if status_of(parent.to_dict()) not in ACTIVE or expired(parent.to_dict()):
                    raise JobConflict("parent Job is not active")
                if cancellation_token is None:
                    cancellation_token = self._cancellations.get(parent_job_id)
            token = cancellation_token.child() if cancellation_token else CancellationToken()
            record = JobRecord(name=name, owner_agent_id=owner_agent_id, metadata=deepcopy(metadata or {}),
                idempotency_key=idempotency_key, cancellation_token_id=token.token_id,
                lease_owner=self.manager_id, lease_epoch=1, attempt_id=uuid4().hex,
                lease_expires_at=self._deadline(lease_seconds), parent_job_id=parent_job_id,
                runner_stopped=True, notification_sent=False)
            self._put("job.created", record)
            self._cancellations[record.job_id] = token
            self._tasks[record.job_id] = loop.create_task(self._execute(record, operation, token))
            return deepcopy(record)

    async def _execute(self, claimed, operation, token):
        job_id, attempt = claimed.job_id, identity(claimed.to_dict())
        published = False
        context_token = _active_attempt.set((job_id, attempt))
        worker = asyncio.current_task()

        async def watch():
            while True:
                await asyncio.sleep(.05)
                try:
                    current = self.get(job_id)
                except Exception:
                    token.cancel("job authority monitor unavailable")
                    worker.cancel()
                    return
                if (identity(current.to_dict()) != attempt or status_of(current.to_dict()) not in ACTIVE
                        or expired(current.to_dict())):
                    token.cancel("job authority lost, cancelled or lease expired")
                    worker.cancel()
                    return

        monitor = asyncio.create_task(watch())
        threaded = claimed.metadata.get("runner_kind") == "thread" or (callable(operation) and not inspect.iscoroutinefunction(operation))
        dispatched = False
        try:
            with self._state():
                record = self._records[job_id]
                require_attempt(record.to_dict(), attempt, live=True)
                self._transition(record, "running", "job.started", expected=attempt, started_at=_utc_now(), runner_stopped=False)
            if token.cancelled:
                raise asyncio.CancelledError
            if callable(operation):
                kwargs = {"cancellation_token": token} if accepts_keyword(operation, "cancellation_token") else {}
                # A sync operation must not stall cancellation, leases or sibling jobs.
                dispatched = True
                value = operation(**kwargs) if inspect.iscoroutinefunction(operation) else await asyncio.to_thread(operation, **kwargs)
            else:
                dispatched = True
                value = operation
            if inspect.isawaitable(value):
                value = await value
            if token.cancelled:
                raise asyncio.CancelledError
            with self._state():
                record = self._records[job_id]
                require_attempt(record.to_dict(), attempt, live=True)
                self._transition(record, "success", "job.completed", expected=attempt, result=value, completed_at=_utc_now(), runner_stopped=True)
                published = True
        except BaseException as error:
            if not isinstance(error, (Exception, asyncio.CancelledError)):
                raise
            with self._state():
                record = self._records[job_id]
                if identity(record.to_dict()) == attempt and status_of(record.to_dict()) in ACTIVE:
                    if isinstance(error, JobConflict) or expired(record.to_dict()):
                        target, message = "interrupted", "job lease expired or authority lost; inspect effects before resume"
                    elif isinstance(error, asyncio.CancelledError):
                        target, message = "cancelled", token.reason or "cancelled"
                    else:
                        target, message = "failed", f"{type(error).__name__}: {error}"
                        self._errors[(job_id, attempt)] = error
                    self._transition(record, target, "job." + target, expected=attempt, error=message, completed_at=_utc_now(),
                        runner_stopped=not (dispatched and threaded and isinstance(error, asyncio.CancelledError)))
                    published = True
        finally:
            monitor.cancel()
            await asyncio.gather(monitor, return_exceptions=True)
            _active_attempt.reset(context_token)
            with self._state():
                current = self._records[job_id]
                if (identity(current.to_dict()) == attempt and current.runner_stopped is not True
                        and not (threaded and token.cancelled)):
                    current.runner_stopped = True
                    self._put("job.runner_stopped", current)
            if inspect.iscoroutine(operation) and inspect.getcoroutinestate(operation) == inspect.CORO_CREATED:
                operation.close()
            if published:
                self._notify(job_id, attempt)

    def _notify(self, job_id, attempt):
        with self._state():
            record = self._records[job_id]
            if identity(record.to_dict()) != attempt or not self._inbox or record.notification_sent is not False:
                return
            if self._session_reader:
                self._inbox.restore(self._session_reader())
            self._inbox.enqueue("context", {"job": record.to_dict()},
                message_id="job-" + job_id + "-" + str(attempt[0] or attempt[1]),
                correlation_id=job_id, metadata={"kind": "job_completion"})
            record.notification_sent = True
            self._put("job.notified", record)

    async def wait(self, job_id):
        self.get(job_id)
        task = self._tasks.get(job_id)
        if task is not None:
            try:
                await asyncio.shield(task)
            except asyncio.CancelledError:
                if not task.cancelled():
                    raise
        while True:
            record = self.get(job_id)
            if status_of(record.to_dict()) not in ACTIVE:
                return record
            if expired(record.to_dict()):
                self.mark_interrupted()
            else:
                await asyncio.sleep(.05)

    def cancel(self, job_id, reason=None):
        with self._state():
            if job_id not in self._records:
                raise KeyError(job_id)
            descendants = {job_id}
            while True:
                children = {r.job_id for r in self._records.values() if r.parent_job_id in descendants}
                if children <= descendants:
                    break
                descendants |= children
            changed = False
            for record in list(self._records.values()):
                if record.job_id not in descendants or status_of(record.to_dict()) not in ACTIVE:
                    continue
                self._transition(record, "cancelled", "job.cancelled", error=reason or "job cancellation requested", completed_at=_utc_now())
                token = self._cancellations.get(record.job_id)
                if token:
                    token.cancel(reason or "job cancellation requested")
                task = self._tasks.get(record.job_id)
                if task:
                    task.cancel()
                self._notify(record.job_id, identity(record.to_dict()))
                changed = True
            return changed

    def cancellation_token(self, job_id):
        self.get(job_id)
        token = self._cancellations.get(job_id)
        if token is None:
            raise RuntimeError(f"job `{job_id}` is not active in this process")
        return token

    def renew_lease(self, job_id, lease_seconds, *, owner=None, expected_epoch=None):
        positive_seconds(lease_seconds)
        with self._state():
            record = self._records[job_id]
            if record.lease_owner != (owner or self.manager_id):
                raise PermissionError("job lease belongs to another owner")
            if expected_epoch is not None and record.lease_epoch != expected_epoch:
                raise JobConflict("job lease epoch is stale")
            require_attempt(record.to_dict(), identity(record.to_dict()), live=True)
            record.lease_expires_at = self._deadline(lease_seconds)
            return self._put("job.lease_renewed", record)

    def resume(self, job_id, operation, *, lease_seconds=60.0, note=None):
        loop = asyncio.get_running_loop()
        positive_seconds(lease_seconds)
        with self._state():
            record = self._records[job_id]
            if record.runner_stopped is not True and (not isinstance(note, str) or not note.strip() or len(note.encode()) > 4096):
                raise JobConflict("unknown runner effects require a host reconciliation note before resume")
            token = CancellationToken()
            record = self._transition(record, "pending", "job.resumed", resume=True,
                lease_owner=self.manager_id, lease_epoch=record.lease_epoch + 1, attempt_id=uuid4().hex,
                lease_expires_at=self._deadline(lease_seconds), cancellation_token_id=token.token_id,
                started_at=None, completed_at=None, error=None, result=None, runner_stopped=True,
                reconciliation_note=note, notification_sent=False)
            self._cancellations[job_id] = token
            self._tasks[job_id] = loop.create_task(self._execute(record, operation, token))
            return record

    def reconcile(self, job_id, *, note):
        if not isinstance(note, str) or not note.strip() or len(note.encode()) > 4096:
            raise ValueError("reconciliation requires a host note of at most 4096 bytes")
        with self._state():
            record = self._records[job_id]
            if record.status not in {JobStatus.CANCELLED, JobStatus.INTERRUPTED}:
                raise JobConflict("only cancelled/interrupted runners can be reconciled")
            record.runner_stopped, record.reconciliation_note = True, note
            return self._put("job.reconciled", record)

    def emit_output(self, job_id, value, *, expected_attempt=None, expected_epoch=None):
        with self._state():
            record = self._records[job_id]
            if record.lease_owner != self.manager_id:
                raise JobConflict("output requires the owning Job manager")
            expected = (expected_attempt if expected_attempt is not None else record.attempt_id,
                        expected_epoch if expected_epoch is not None else record.lease_epoch)
            active = _active_attempt.get()
            if active and active[0] == job_id:
                expected = active[1]
            require_attempt(record.to_dict(), expected, live=True)
            record.output.append(deepcopy(value))
            record.output_cursor += 1
            return self._put("job.output", record)

    def get(self, job_id):
        with self._state():
            return deepcopy(self._records[job_id])

    def list(self):
        with self._state():
            return deepcopy(list(self._records.values()))

    def status(self, job_id):
        from .job_lifecycle import view
        record = self.get(job_id)
        return dict(job_id=record.job_id, name=record.name, **view(record.to_dict()))

    def mark_interrupted(self):
        with self._state():
            for record in list(self._records.values()):
                if status_of(record.to_dict()) in ACTIVE and (record.lease_expires_at is None or expired(record.to_dict())):
                    self._transition(record, "interrupted", "job.interrupted", completed_at=_utc_now(),
                        error="owner unavailable or lease expired; inspect effects before resume")

    def recover_notifications(self):
        for record in self.list():
            if record.notification_sent is False and status_of(record.to_dict()) not in ACTIVE:
                self._notify(record.job_id, identity(record.to_dict()))

    @staticmethod
    def _deadline(seconds):
        return (datetime.now(timezone.utc) + timedelta(seconds=seconds)).isoformat() if seconds is not None else None

    def restore(self, session, *, clear_live=True):
        records = {}
        for event in session.events:
            value = event.data.get("job") if event.type.startswith("job.") else None
            if isinstance(value, dict):
                payload = dict(value)
                payload["status"] = JobStatus(payload.get("status", "pending"))
                payload.setdefault("output_cursor", len(payload.get("output", [])))
                records[payload["job_id"]] = JobRecord(**payload)
        self._records = records
        if clear_live:
            self._tasks = {}
            self._cancellations = {}

    def result_error(self, record):
        return self._errors.get((record.job_id, identity(record.to_dict())))
