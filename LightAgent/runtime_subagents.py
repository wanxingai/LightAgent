"""Subagent registry; executions and cancellations are Jobs, not a scheduler."""

import asyncio
from contextlib import nullcontext
from copy import deepcopy
from dataclasses import asdict, dataclass, field
import hashlib
import json
from typing import Any
from uuid import uuid4

from .capabilities import CapabilityRisk, PermissionSet
from .cancellation import accepts_keyword
from .runtime_jobs import JobManager, JobStatus
from .job_lifecycle import ACTIVE, status_of


@dataclass
class SubagentRecord:
    agent_id: str
    name: str
    parent_agent_id: str | None
    depth: int
    permissions: PermissionSet
    persistent: bool = False
    status: str = "ready"
    metadata: dict[str, Any] = field(default_factory=dict)
    job_id: str | None = None


class SubagentManager:
    def __init__(self, *, max_depth=2, max_agents=8, max_concurrency=4, event_sink=None,
                 jobs=None, state_scope=None, session_reader=None):
        for value in (max_depth, max_agents, max_concurrency):
            if type(value) is not int or value < 1:
                raise ValueError("subagent limits must be positive integers")
        self.max_depth, self.max_agents, self.max_concurrency = max_depth, max_agents, max_concurrency
        self._event_sink = event_sink
        self.jobs = jobs or JobManager(event_sink)
        self._records = {}
        self._bindings = {}
        self._state_scope, self._session_reader = state_scope, session_reader

    def _refresh(self):
        if self._session_reader:
            with self._state_scope() if self._state_scope else nullcontext():
                self.restore(self._session_reader(), clear_bindings=False)

    def register(self, agent, *, parent_agent_id=None, parent_permissions=None,
                 allowed_capabilities=None, max_risk=None, persistent=False, metadata=None):
        with self._state_scope() if self._state_scope else nullcontext():
            self._refresh()
            if len(self._records) >= self.max_agents:
                raise RuntimeError("subagent limit reached")
            parent = self._records[parent_agent_id] if parent_agent_id else None
            depth = parent.depth + 1 if parent else 1
            if depth > self.max_depth:
                raise RuntimeError("subagent depth limit reached")
            base = parent.permissions if parent else (parent_permissions or PermissionSet())
            if parent and parent_permissions:
                base = base.narrow(allowed=parent_permissions.allowed or None,
                    denied=parent_permissions.denied, max_risk=parent_permissions.max_risk)
            if allowed_capabilities is not None:
                allowed_capabilities = frozenset(allowed_capabilities)
                if base.allowed and not allowed_capabilities:
                    raise ValueError("empty capability allowlist would widen the parent's permissions")
            permissions = base.narrow(allowed=allowed_capabilities, max_risk=max_risk)
            record = SubagentRecord(agent_id=uuid4().hex, name=str(getattr(agent, "name", "subagent")),
                parent_agent_id=parent_agent_id, depth=depth, permissions=permissions,
                persistent=persistent, metadata=deepcopy(metadata or {}))
            self._emit("subagent.created", record)
            self._records[record.agent_id] = record
            self._bindings[record.agent_id] = agent
            return deepcopy(record)

    def bind(self, agent_id, agent, *, note=None):
        """Explicitly supply trusted code after restoring a registration."""
        with self._state_scope() if self._state_scope else nullcontext():
            self._refresh()
            record = self._records[agent_id]
            owned = [j for j in self.jobs.list() if j.owner_agent_id == agent_id and j.metadata.get("kind") == "subagent"]
            if record.status == "running" and not owned:
                if not isinstance(note, str) or not note.strip() or len(note.encode()) > 4096:
                    raise RuntimeError("legacy running subagent requires a host reconciliation note before bind")
                record.status = "ready"
                record.metadata["legacy_rebind_note"] = note
                self._emit("subagent.rebound", record)
            self._bindings[agent_id] = agent

    async def run(self, agent_id, query, *, cancellation_token=None, idempotency_key=None,
                  parent_job_id=None, lease_seconds=None, **kwargs):
        self._refresh()
        record = self._records[agent_id]
        agent = self._bindings.get(agent_id)
        if agent is None:
            raise RuntimeError("restored subagent requires explicit host bind() before execution")
        # Hash input identity; do not copy prompts or credentials into Job metadata.
        fingerprint = None
        if idempotency_key is not None:
            if not isinstance(idempotency_key, str) or not idempotency_key.strip():
                raise ValueError("idempotency_key must not be empty")
            fingerprint = hashlib.sha256(json.dumps([query, kwargs], sort_keys=True, allow_nan=False).encode()).hexdigest()

        async def operation(*, cancellation_token):
            arun = getattr(agent, "arun", None)
            method = arun if callable(arun) else agent.run
            options = dict(kwargs)
            if accepts_keyword(method, "cancellation_token"):
                options["cancellation_token"] = cancellation_token
            if idempotency_key is not None and accepts_keyword(method, "idempotency_key"):
                options["idempotency_key"] = idempotency_key
            return await method(query, **options) if callable(arun) else await asyncio.to_thread(method, query, **options)

        key = "subagent:" + agent_id + ":" + idempotency_key if idempotency_key is not None else None
        job = self.jobs.start(record.name, operation, owner_agent_id=agent_id,
            metadata={"kind": "subagent", "input_digest": fingerprint,
                      "runner_kind": "coroutine" if callable(getattr(agent, "arun", None)) else "thread"},
            idempotency_key=key, cancellation_token=cancellation_token,
            lease_seconds=lease_seconds, parent_job_id=parent_job_id, max_active=self.max_concurrency)
        try:
            completed = await self.jobs.wait(job.job_id)
        except asyncio.CancelledError:
            self.jobs.cancel(job.job_id, "subagent caller cancelled")
            raise
        if completed.status == JobStatus.CANCELLED:
            raise asyncio.CancelledError(completed.error)
        if completed.status != JobStatus.SUCCESS:
            raise self.jobs.result_error(completed) or RuntimeError(completed.error or completed.status.value)
        return completed.result

    def cancel(self, agent_id, reason=None):
        self._refresh()
        if agent_id not in self._records:
            raise KeyError(agent_id)
        descendants = {agent_id}
        while True:
            children = {r.agent_id for r in self._records.values() if r.parent_agent_id in descendants}
            if children <= descendants:
                break
            descendants |= children
        return sum(self.jobs.cancel(j.job_id, reason or "subagent cancellation requested")
                   for j in self.jobs.list() if j.owner_agent_id in descendants and status_of(j.to_dict()) in ACTIVE)

    def list(self):
        self._refresh()
        jobs = self.jobs.list()
        records = deepcopy(list(self._records.values()))
        for record in records:
            owned = [j for j in jobs if j.owner_agent_id == record.agent_id and j.metadata.get("kind") == "subagent"]
            if owned:
                active = [j for j in owned if status_of(j.to_dict()) in ACTIVE]
                latest = (active or owned)[-1]
                record.status, record.job_id = latest.status.value, latest.job_id
                if record.status == "pending":
                    record.status = "running"
            elif record.status == "running":
                record.status = "interrupted"
        return records

    def tree(self):
        return [dict(agent_id=r.agent_id, name=r.name, parent_agent_id=r.parent_agent_id,
                     depth=r.depth, status=r.status, persistent=r.persistent, job_id=r.job_id,
                     bound=r.agent_id in self._bindings) for r in self.list()]

    def send(self, agent_id, content, *, message_type="context"):
        self._refresh()
        if agent_id not in self._records:
            raise KeyError(agent_id)
        runtime = getattr(self._bindings.get(agent_id), "runtime", None)
        if runtime is None or runtime.session is None:
            raise RuntimeError("target subagent does not have an open runtime Session")
        return runtime.inbox.enqueue(message_type, content)

    def restore(self, session, *, clear_bindings=True):
        records = {}
        for event in session.events:
            payload = event.data.get("agent") if event.type.startswith("subagent.") else None
            if isinstance(payload, dict):
                value = deepcopy(payload)
                p = value["permissions"]
                value["permissions"] = PermissionSet(frozenset(p["allowed"]), frozenset(p["denied"]), CapabilityRisk(p["max_risk"]))
                # Legacy completed/failed registrations without Jobs remain readable.
                records[value["agent_id"]] = SubagentRecord(**value)
        self._records = records
        if clear_bindings:
            self._bindings = {}

    def _emit(self, event, record):
        if self._event_sink:
            value = asdict(record)
            value["permissions"] = dict(allowed=sorted(record.permissions.allowed), denied=sorted(record.permissions.denied),
                                        max_risk=record.permissions.max_risk.value)
            self._event_sink(event, {"agent": value})
