"""Ordinary durable tasks on the shared single-host supervisor and control store."""
from __future__ import annotations

import asyncio
from dataclasses import asdict, replace
from pathlib import Path
import math
import threading
import time

from ..backends.base import BackendRequest, BackendResult
from ..cancellation import CancellationToken
from ..capabilities import CapabilitySpec, CapabilityRisk
from ..security import CapabilityGate, SecurityContext, canonical_digest
from .execution_contracts import (EXECUTION_SCHEMA_VERSION, ExecutionLimits, ExecutionRequirements,
                                  execution_profile, require_attempt)
from .ledger import BudgetLedger, LedgerLimitExceeded, _amounts
from .redaction import contains_secret
from .store import ControlStore, StateConflict, dumps, uid
from .supervisor import ServiceSupervisor

TERMINAL = frozenset({"completed", "failed", "cancelled"})


class ExecutionService(ServiceSupervisor):
    """Host factories are explicit; no model, Codex, Shell, or research default."""

    def __init__(self, root=None, *, backend_factories=None, backend_profiles=None, max_concurrent_jobs=8):
        super().__init__(root, backend_factories=backend_factories, max_concurrent_jobs=max_concurrent_jobs)
        self.backend_profiles = dict(backend_profiles or {})
        self.ledger = BudgetLedger(self.store)

    def _profile(self, backend):
        if backend not in self.backend_factories:
            raise ValueError("backend must be registered by the host; no implicit execution fallback")
        factory = self.backend_factories[backend]
        worker = factory()
        if not callable(getattr(worker, "probe", None)):
            raise TypeError("backend must implement capability probing")
        probe = worker.probe()
        return worker, probe, execution_profile(factory, probe, self.backend_profiles.get(backend, {}))

    def submit(self, query, workspace, *, backend, security_context, limits=None,
               requirements=None, budget=None, reservation=None, parent_id=None, session_id=None, idempotency_key=None):
        if not isinstance(query, str) or not query.strip() or len(query.encode()) > 65536:
            raise ValueError("query must contain 1..65536 bytes")
        if not isinstance(security_context, SecurityContext) or security_context.expired:
            raise PermissionError("an unexpired host SecurityContext is required")
        if session_id is not None and (not isinstance(session_id, str) or not 1 <= len(session_id) <= 256):
            raise ValueError("invalid backend session ID")
        limits, requirements = limits or ExecutionLimits(), requirements or ExecutionRequirements()
        workspace = Path(workspace).expanduser().resolve(strict=True)
        if not workspace.is_dir() or workspace.is_relative_to(self.root) or self.root.is_relative_to(workspace):
            raise ValueError("workspace and authority state must be disjoint directories")
        if security_context.resources and str(workspace) not in security_context.resources:
            raise PermissionError("workspace is not authorized")
        _, probe, profile = self._profile(backend)
        requirements.verify(probe, security_context)
        budget = _amounts(budget or {}, limits=True)
        reservation = _amounts(reservation or {})
        for dimension in ("model_calls", "tool_calls", "tokens", "cost"):
            if budget.get(dimension) is not None and (dimension not in probe.capabilities.budget_dimensions
                    or dimension not in reservation):
                raise PermissionError("backend cannot enforce/reserve the requested hard budget: " + dimension)
        if session_id and not probe.capabilities.resume:
            raise PermissionError("backend does not support session continuation")
        key = idempotency_key or uid()
        if not isinstance(key, str) or not 1 <= len(key) <= 256:
            raise ValueError("invalid submission idempotency key")
        spec = dict(query=query, workspace=str(workspace), backend=backend, security=security_context.to_dict(),
                    limits=asdict(limits), requirements=asdict(requirements), budget=budget, reservation=reservation,
                    parent_id=parent_id, session_id=session_id, profile=profile)
        if contains_secret(dumps(spec)):
            raise ValueError("durable task configuration contains a known credential")
        fingerprint = canonical_digest(spec)
        submission = canonical_digest(dict(key=key, user=security_context.user_id,
            tenant=security_context.tenant_id, project=security_context.project_id))
        with self.store.transaction() as db:
            if any(record.get('domain') != 'execution' for record in self.store.scan('agent', db=db)):
                raise StateConflict('research state requires its extension; choose a separate ordinary execution root')
            previous = self.store.get("execution_submission", submission, db)
            if previous:
                if previous["fingerprint"] != fingerprint:
                    raise StateConflict("submission key reused for different task configuration")
                return ExecutionHandle(previous["agent"], self.root)
            if parent_id:
                parent = self.store.get("agent", parent_id, db)
                if not parent or parent["desired"] == "cancelled":
                    raise StateConflict("parent is unavailable or cancelled")
                for account in self.ledger._chain(parent_id, db):
                    for dimension in ("model_calls", "tool_calls", "tokens", "cost"):
                        if account["limits"].get(dimension) is not None and (dimension not in probe.capabilities.budget_dimensions
                                or dimension not in reservation):
                            raise PermissionError("child backend cannot enforce inherited hard budget: " + dimension)
                parent_context = SecurityContext.from_dict(parent["security"])
                narrowed = parent_context.narrow(allowed_capabilities=security_context.permissions.allowed,
                    denied_capabilities=security_context.permissions.denied,
                    max_risk=security_context.permissions.max_risk, resources=security_context.resources,
                    network_allowed=security_context.network_allowed, sandbox_required=security_context.sandbox_required,
                    deadline=security_context.deadline)
                for attribute in ("user_id", "tenant_id", "project_id"):
                    if getattr(parent_context, attribute) != getattr(security_context, attribute):
                        raise PermissionError("child task cannot change security identity")
                if narrowed.permissions != security_context.permissions:
                    raise PermissionError("child task permissions are not a valid narrowing")
                if parent_context.resources and not security_context.resources:
                    raise PermissionError("child task cannot remove resource restrictions")
                if parent_context.deadline and not security_context.deadline:
                    raise PermissionError("child task cannot remove its parent deadline")
                if parent.get("requirements", {}).get("isolation") == "sandbox" and requirements.isolation == "none":
                    raise PermissionError("child task cannot remove its parent isolation requirement")
                if parent.get("requirements", {}).get("isolation") == "docker" and requirements.isolation != "docker":
                    raise PermissionError("child task cannot remove Docker-only execution")
            identity = uid()
            self.ledger.open(identity, limits=budget, parent=parent_id, db=db)
            record = dict(id=identity, domain="execution", schema_version=EXECUTION_SCHEMA_VERSION,
                **spec, epoch=0, status="queued", desired="running", attempt_id=None,
                created_at=time.time(), result=None, output_cursor=0)
            self.store.put("agent", record, db)
            self.store.put("execution_submission", dict(id=submission, agent=identity, fingerprint=fingerprint), db)
            self.store.event(identity, "execution.submitted", {"parent_id": parent_id, "profile": canonical_digest(profile)}, db)
        return ExecutionHandle(identity, self.root)

    def claim(self, task_id):
        with self.store.transaction() as db:
            task = self.store.get("agent", task_id, db)
            if not task or task.get("domain") != "execution" or task["status"] != "queued" or task["desired"] != "running":
                return None
            if task.get('schema_version') != EXECUTION_SCHEMA_VERSION:
                raise StateConflict('unsupported execution schema')
            attempt_id, now = uid(), time.time()
            self.ledger.reserve(task_id, attempt_id,
                {**task["reservation"], "backend_calls": 1, "seconds": task["limits"]["timeout"]}, db=db)
            task.update(status="running", epoch=task["epoch"] + 1, attempt_id=attempt_id)
            attempt = dict(id=attempt_id, agent=task_id, epoch=task["epoch"], owner=self._instance,
                status="running", created_at=now, deadline=now + task["limits"]["timeout"],
                lease_until=now + min(task["limits"]["lease_seconds"], task["limits"]["timeout"]), messages=[], dispatched=False)
            for message in self.store.scan("message", task_id, db, filters={"status": ("persisted",), "kind": ("message",)}):
                if len(attempt["messages"]) >= 100:
                    break
                message.update(status="claimed", claim_id=attempt_id, claim_epoch=task["epoch"])
                self.store.put("message", message, db)
                attempt["messages"].append(message["id"])
            self.store.put("agent", task, db)
            self.store.put("execution_attempt", attempt, db)
            self.store.event(task_id, "execution.claimed", {"attempt_id": attempt_id, "epoch": task["epoch"]}, db)
            return attempt

    def renew(self, attempt):
        now = time.time()
        with self.store.transaction() as db:
            task, current = require_attempt(self.store, attempt["agent"], attempt["id"], attempt["epoch"], db, now=now)
            if current["owner"] != self._instance:
                raise StateConflict("attempt is owned by another supervisor")
            current["lease_until"] = min(now + task["limits"]["lease_seconds"], current["deadline"])
            return self.store.put("execution_attempt", current, db)

    def _progress(self, attempt, event):
        if event.attempt_id != attempt["id"]:
            raise StateConflict("backend event belongs to another attempt")
        with self.store.transaction() as db:
            task, _ = require_attempt(self.store, attempt["agent"], attempt["id"], attempt["epoch"], db, now=time.time())
            task["output_cursor"] += 1
            self.store.put("agent", task, db)
            # Raw provider output is untrusted and may contain credentials.
            self.store.event(task["id"], "execution.progress", dict(attempt_id=attempt["id"],
                epoch=attempt["epoch"], cursor=task["output_cursor"], type=event.type), db)

    def _execute(self, attempt, token):
        task = self.store.get("agent", attempt["agent"])
        started = time.monotonic()
        result = None
        try:
            worker, probe, profile = self._profile(task["backend"])
            if profile != task["profile"]:
                raise StateConflict("backend/extension profile changed; explicit host reauthorization is required")
            context = SecurityContext.from_dict(task["security"])
            ExecutionRequirements(**task["requirements"]).verify(probe, context)
            CapabilityGate().authorize_sync(CapabilitySpec("backend.execute", execute=True,
                risk=CapabilityRisk.SENSITIVE), task["backend"],
                {"query": task["query"], "workspace": task["workspace"]}, context, resource=task["workspace"])
            updates = [self.store.get("message", key)["content"] for key in attempt["messages"]]
            prompt = task["query"] + ("\nHost follow-up messages:\n" + "\n".join(updates) if updates else "")
            request = BackendRequest(prompt, task["workspace"], context.narrow(task_id=task["id"], attempt_id=attempt["id"]),
                attempt_id=attempt["id"], session_id=task["session_id"], timeout=task["limits"]["timeout"],
                cancellation_token=token, on_event=lambda event: self._progress(attempt, event))
            request = replace(request, budget_reservation={**task["reservation"], "backend_calls": 1,
                                                         "seconds": task["limits"]["timeout"]})
            async def execute():
                try:
                    return await asyncio.wait_for(worker.execute(request), request.timeout)
                except asyncio.TimeoutError:
                    token.cancel("execution deadline")
                    raise
            with self.store.transaction() as db:
                _, current = require_attempt(self.store, task["id"], attempt["id"], attempt["epoch"], db, now=time.time())
                current["dispatched"] = True
                self.store.put("execution_attempt", current, db)
            result = asyncio.run(execute())
            if not isinstance(result, BackendResult):
                raise TypeError("backend must return BackendResult")
            if (not isinstance(result.content, str) or len(result.content.encode()) > 1024 * 1024
                    or contains_secret(dumps(asdict(result)))):
                raise ValueError("backend result exceeds its budget or contains a known credential")
            if result.status != "completed" or result.error:
                raise RuntimeError("backend did not confirm completion")
            self._finish(attempt, result, started)
        except Exception as exc:
            self._finish(attempt, result, started, error=type(exc).__name__)

    def _finish(self, attempt, result, started, *, error=None):
        with self.store.transaction() as db:
            task = self.store.get("agent", attempt["agent"], db)
            current = self.store.get("execution_attempt", attempt["id"], db)
            if not task or current["status"] != "running" or task["epoch"] != attempt["epoch"]:
                return
            expired = current["lease_until"] <= time.time()
            if expired:
                error = "ExpiredAttempt"
            dispatched = current.get("dispatched", False)
            usage = {"backend_calls": int(dispatched), "seconds": max(0, time.monotonic() - started)}
            reported = result.usage if result is not None and isinstance(result.usage, dict) else {}
            valid_amount = lambda value: type(value) in (int, float) and math.isfinite(value) and value >= 0
            if valid_amount(reported.get("total_tokens")):
                usage["tokens"] = reported["total_tokens"]
            for dimension in ("model_calls", "tool_calls", "cost"):
                if valid_amount(reported.get(dimension)):
                    usage[dimension] = reported[dimension]
            self.ledger.settle(task["id"], attempt["id"], usage,
                unknown=({"tokens", "model_calls", "tool_calls", "cost"} - usage.keys()) if dispatched else (), db=db)
            # A failed/abandoned call may have performed effects. Never replay automatically.
            status = ("reconciling" if dispatched else "failed") if error else "completed"
            if task["desired"] == "cancelled":
                status = "cancelled"
            current.update(status=status, error=error, finished_at=time.time())
            task.update(status=status, result=asdict(result) if status == "completed" else None)
            self.store.put("execution_attempt", current, db)
            self.store.put("agent", task, db)
            for key in attempt["messages"]:
                message = self.store.get("message", key, db)
                if message.get("claim_id") != attempt["id"] or message.get("claim_epoch") != attempt["epoch"]:
                    raise StateConflict("stale inbox acknowledgement")
                message.update(status="applied" if status == "completed" else "uncertain")
                self.store.put("message", message, db)
            self.store.event(task["id"], "execution." + status, {"attempt_id": attempt["id"], "error": error}, db)

    def recover(self):
        if getattr(self, '_supervisor_thread', None) != threading.get_ident():
            with self._supervisor_guard():
                return self._recover_locked()
        return self._recover_locked()

    def _recover_locked(self):
        for task in self.store.scan("agent"):
            if task.get("domain") != "execution":
                raise StateConflict("this control root contains research history; use its explicit extension, not a generic runner")
            if task.get('schema_version') != EXECUTION_SCHEMA_VERSION:
                raise StateConflict('unsupported execution schema; preserve state before migration')
            if task["status"] != "running":
                continue
            with self.store.transaction() as db:
                current = self.store.get("agent", task["id"], db)
                if current["status"] != "running":
                    continue
                attempt = self.store.get("execution_attempt", current["attempt_id"], db)
                attempt.update(status="reconciling", error="SupervisorInterrupted")
                current.update(status="reconciling", epoch=current["epoch"] + 1)
                self.store.put("execution_attempt", attempt, db)
                self.store.put("agent", current, db)
                dispatched = attempt.get('dispatched', False)
                self.ledger.settle(current["id"], attempt["id"], {"backend_calls": int(dispatched)},
                    unknown={"model_calls", "tool_calls", "tokens", "seconds", "cost"} if dispatched else (), db=db)
                for key in attempt["messages"]:
                    message = self.store.get("message", key, db)
                    message["status"] = "uncertain"
                    self.store.put("message", message, db)
                self.store.event(current["id"], "execution.reconciling", {"attempt_id": attempt["id"]}, db)

    def tick(self, pool):
        from .jobs import poll_jobs
        poll_jobs(self)
        for identity, (future, token) in list(self._active.items()):
            task = self.store.get("agent", identity)
            if task["desired"] == "cancelled":
                token.cancel("parent/task cancelled")
            if future.done():
                future.result()
                del self._active[identity]
            elif task["status"] == "running":
                try:
                    self.renew(self.store.get("execution_attempt", task["attempt_id"]))
                except StateConflict:
                    token.cancel("execution lease expired")
        from .wakeups import WakeupScheduler
        WakeupScheduler(self.store).deliver_due()
        for task in self.store.scan("agent", filters={"status": ("queued",)}):
            if len(self._active) >= 4:
                break
            if task["id"] not in self._active:
                try:
                    attempt = self.claim(task["id"])
                except LedgerLimitExceeded:
                    with self.store.transaction() as db:
                        current = self.store.get("agent", task["id"], db)
                        current["status"] = "blocked"
                        self.store.put("agent", current, db)
                        self.store.event(task["id"], "budget.blocked", {}, db)
                    continue
                if attempt:
                    token = CancellationToken()
                    self._active[task["id"]] = pool.submit(self._execute, attempt, token), token


class ExecutionHandle:
    def __init__(self, task_id, root=None):
        self.id, self.store = task_id, ControlStore(root)
        if self.status().get("domain") != "execution":
            raise StateConflict("not an ordinary execution task")

    @classmethod
    def connect(cls, task_id, *, root=None):
        return cls(task_id, root)

    def status(self):
        record = self.store.get("agent", self.id)
        if record is None:
            raise KeyError(self.id)
        if record.get('domain') != 'execution' or record.get('schema_version') != EXECUTION_SCHEMA_VERSION:
            raise StateConflict('unsupported execution record schema; preserve state before migration')
        return record

    def events(self, after=0, limit=100):
        return self.store.events(self.id, after, limit)

    def send(self, content, *, idempotency_key=None):
        if self.status()["status"] in TERMINAL:
            raise StateConflict("terminal task cannot accept new work; submit a new task or child session")
        return self.store.enqueue(self.id, content, idempotency_key)

    def receipt(self, message_id):
        record = self.store.get("message", message_id)
        if not record or record["agent"] != self.id:
            raise KeyError(message_id)
        return record

    def budget(self):
        return BudgetLedger(self.store).snapshot(self.id)

    def records(self, kind, *, cursor=None, limit=50):
        if kind not in ('execution_attempt', 'message', 'job', 'interaction', 'wakeup', 'budget_reservation'):
            raise ValueError('unsupported execution record kind')
        return self.store.page(kind, self.id, cursor=cursor, limit=limit)

    def submit_job(self, argv, **kwargs):
        from .jobs import submit_job
        return submit_job(self, argv, **kwargs)

    def job_status(self, job_id):
        from .jobs import job_status
        return job_status(self, job_id)

    def reconcile_job(self, job_id, *, status, note):
        from .jobs import reconcile_job
        return reconcile_job(self, job_id, status=status, note=note)

    def cancel_job(self, job_id):
        with self.store.transaction() as db:
            job = self.store.get('job', job_id, db)
            if not job or job['agent'] != self.id:
                raise KeyError(job_id)
            job['cancel'] = True
            return self.store.put('job', job, db)

    def read_job_output(self, job_id, *, after=0, limit=65536):
        import os
        import stat
        if type(after) is not int or after < 0 or type(limit) is not int or not 1 <= limit <= 65536:
            raise ValueError('invalid Job output cursor')
        job = self.store.get('job', job_id)
        if not job or job['agent'] != self.id:
            raise KeyError(job_id)
        if Path(job_id).name != job_id or job_id in ('', '.', '..'):
            raise ValueError('invalid Job identity')
        directory = self.store.root / 'job-output'
        if directory.is_symlink():
            raise PermissionError('Job output directory is not trusted')
        path = directory / job_id
        if not path.exists():
            return dict(content=b'', next_cursor=after, status=job['status'])
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(descriptor, 'rb') as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise PermissionError('Job output is not a regular file')
            stream.seek(after)
            content = stream.read(limit)
        return dict(content=content, next_cursor=after+len(content), status=job['status'])

    def _control(self, desired):
        with self.store.transaction() as db:
            task = self.store.get("agent", self.id, db)
            if task["status"] in TERMINAL and not (desired == "cancelled" and task["status"] == "completed"):
                if desired == "cancelled" and task["status"] == "cancelled":
                    return task
                raise StateConflict("terminal tasks cannot resume")
            if desired == "running" and task["status"] == "reconciling":
                raise StateConflict("reconcile uncertain effects before resuming")
            task["desired"] = desired
            if task["status"] in ("queued", "paused", "blocked"):
                task["status"] = "queued" if desired == "running" else desired
            self.store.put("agent", task, db)
            self.store.event(self.id, "execution.control", {"desired": desired}, db)
            if desired == "cancelled":
                descendants = {self.id}
                children = list(self.store.scan("agent", db=db))
                for _ in range(len(children)):
                    added = {child["id"] for child in children if child.get("parent_id") in descendants} - descendants
                    if not added:
                        break
                    descendants.update(added)
                for identity in descendants - {self.id}:
                    child = self.store.get("agent", identity, db)
                    child["desired"] = "cancelled"
                    if child["status"] in ("queued", "paused"):
                        child["status"] = "cancelled"
                    self.store.put("agent", child, db)
                    self.store.event(identity, "execution.parent_cancelled", {"parent_id": self.id}, db)
                for job in self.store.scan("job", db=db):
                    if job["agent"] in descendants:
                        job["cancel"] = True
                        self.store.put("job", job, db)
        return task

    def pause(self):
        return self._control("paused")

    def resume(self):
        return self._control("running")

    def cancel(self):
        return self._control("cancelled")

    def reconcile(self, *, action, note):
        if action not in ("retry", "discard") or not isinstance(note, str) or not note.strip() or len(note) > 4096:
            raise ValueError("reconciliation requires retry/discard and a bounded host note")
        with self.store.transaction() as db:
            task = self.store.get("agent", self.id, db)
            if task["status"] != "reconciling" or (task["desired"] == "cancelled" and action == "retry"):
                raise StateConflict("task is not awaiting reconciliation")
            previous = self.store.get("execution_attempt", task["attempt_id"], db)
            previous.update(status="reconciled", resolution=action, note=note)
            self.store.put("execution_attempt", previous, db)
            task.update(status="queued" if action == "retry" else "cancelled",
                        desired="running" if action == "retry" else "cancelled", epoch=task["epoch"] + 1)
            self.store.put("agent", task, db)
            for identity in previous["messages"]:
                message = self.store.get("message", identity, db)
                message["status"] = "persisted" if action == "retry" else "discarded"
                self.store.put("message", message, db)
            self.store.event(self.id, "execution.reconciled", {"attempt_id": previous["id"], "action": action}, db)
            return task
