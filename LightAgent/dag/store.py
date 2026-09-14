"""SQLite-backed authoritative task graph, event log, and lease store."""

from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Protocol

from ..security import canonical_digest
from .models import (
    DAGAttemptStatus,
    DAGConfig,
    DAGEvent,
    DAGRun,
    DAGRunStatus,
    DAGTask,
    DAGTaskStatus,
    ArtifactManifest,
    DecompositionProposal,
    TaskAttempt,
    TaskSpec,
    TaskState,
    VerificationReport,
    utc_now,
)


class DAGError(RuntimeError):
    def __init__(self, code: str, message: str):
        self.code = code if code.startswith("LA-DAG-") else f"LA-DAG-{code}"
        self.message = message
        super().__init__(f"[{self.code}] {message}")


class TaskGraphStore(Protocol):
    def create_run(self, run: DAGRun, tasks: Iterable[TaskSpec], config: DAGConfig) -> DAGRun:
        ...

    def get_run(self, run_id: str) -> DAGRun | None:
        ...

    def list_tasks(self, run_id: str) -> list[DAGTask]:
        ...

    def get_task(self, run_id: str, task_id: str) -> DAGTask | None:
        ...

    def events(self, run_id: str, after: int = 0, limit: int = 100) -> list[DAGEvent]:
        ...


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), default=repr)


def _loads(value: str) -> Any:
    return json.loads(value)


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


class SqliteTaskGraphStore:
    """Single-host SQLite implementation with transactional CAS and fencing."""

    schema_version = 1

    def __init__(self, path: str | Path = ":memory:"):
        self.path = str(path)
        self._uri = self.path.startswith("file:")
        self._lock = threading.RLock()
        self._connection = sqlite3.connect(
            self.path,
            check_same_thread=False,
            isolation_level=None,
            uri=self._uri,
        )
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.execute("PRAGMA busy_timeout = 5000")
        if self.path != ":memory:":
            self._connection.execute("PRAGMA journal_mode = WAL")
        self._initialize()

    def close(self) -> None:
        self._connection.close()

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                yield self._connection
            except BaseException:
                self._connection.rollback()
                raise
            else:
                self._connection.commit()

    def _initialize(self) -> None:
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS dag_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS dag_runs (
                run_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                graph_revision INTEGER NOT NULL,
                scheduler_epoch INTEGER NOT NULL,
                payload TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS dag_tasks (
                run_id TEXT NOT NULL,
                task_id TEXT NOT NULL,
                status TEXT NOT NULL,
                priority INTEGER NOT NULL,
                spec TEXT NOT NULL,
                state TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY (run_id, task_id),
                FOREIGN KEY (run_id) REFERENCES dag_runs(run_id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS dag_tasks_ready
                ON dag_tasks(run_id, status, priority DESC, created_at, task_id);
            CREATE TABLE IF NOT EXISTS dag_dependencies (
                run_id TEXT NOT NULL,
                task_id TEXT NOT NULL,
                dependency_id TEXT NOT NULL,
                decomposition_id TEXT NOT NULL,
                PRIMARY KEY (run_id, task_id, dependency_id),
                FOREIGN KEY (run_id, task_id) REFERENCES dag_tasks(run_id, task_id) ON DELETE CASCADE,
                FOREIGN KEY (run_id, dependency_id) REFERENCES dag_tasks(run_id, task_id) ON DELETE RESTRICT
            );
            CREATE INDEX IF NOT EXISTS dag_dependencies_reverse
                ON dag_dependencies(run_id, dependency_id, task_id);
            CREATE TABLE IF NOT EXISTS dag_attempts (
                attempt_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                task_id TEXT NOT NULL,
                status TEXT NOT NULL,
                lease_epoch INTEGER NOT NULL,
                lease_expires_at TEXT,
                payload TEXT NOT NULL,
                FOREIGN KEY (run_id, task_id) REFERENCES dag_tasks(run_id, task_id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS dag_attempts_lease
                ON dag_attempts(run_id, status, lease_expires_at);
            CREATE TABLE IF NOT EXISTS dag_events (
                run_id TEXT NOT NULL,
                sequence INTEGER NOT NULL,
                payload TEXT NOT NULL,
                PRIMARY KEY (run_id, sequence),
                FOREIGN KEY (run_id) REFERENCES dag_runs(run_id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS dag_commands (
                run_id TEXT NOT NULL,
                command_key TEXT NOT NULL,
                request_digest TEXT NOT NULL,
                response TEXT NOT NULL,
                PRIMARY KEY (run_id, command_key),
                FOREIGN KEY (run_id) REFERENCES dag_runs(run_id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS dag_reports (
                report_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                task_id TEXT NOT NULL,
                attempt_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                FOREIGN KEY (attempt_id) REFERENCES dag_attempts(attempt_id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS dag_artifacts (
                artifact_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                task_id TEXT NOT NULL,
                attempt_id TEXT NOT NULL,
                state TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                payload TEXT NOT NULL,
                FOREIGN KEY (attempt_id) REFERENCES dag_attempts(attempt_id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS dag_artifacts_task
                ON dag_artifacts(run_id, task_id, state);
            CREATE TABLE IF NOT EXISTS dag_decompositions (
                proposal_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                parent_task_id TEXT NOT NULL,
                proposal_digest TEXT NOT NULL,
                payload TEXT NOT NULL,
                FOREIGN KEY (run_id, parent_task_id) REFERENCES dag_tasks(run_id, task_id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS dag_scheduler_leases (
                run_id TEXT PRIMARY KEY,
                owner_id TEXT NOT NULL,
                epoch INTEGER NOT NULL,
                expires_at TEXT NOT NULL,
                FOREIGN KEY (run_id) REFERENCES dag_runs(run_id) ON DELETE CASCADE
            );
            """
        )
        row = self._connection.execute("SELECT value FROM dag_meta WHERE key='schema_version'").fetchone()
        if row is None:
            self._connection.execute(
                "INSERT INTO dag_meta(key, value) VALUES('schema_version', ?)",
                (str(self.schema_version),),
            )
        elif int(row["value"]) != self.schema_version:
            raise DAGError("SCHEMA-MISMATCH", f"unsupported DAG schema version {row['value']}")

    def create_run(self, run: DAGRun, tasks: Iterable[TaskSpec], config: DAGConfig) -> DAGRun:
        task_list = list(tasks)
        if not run.tenant_id or not run.project_id:
            raise DAGError("IDENTITY-REQUIRED", "tenant_id and project_id are required")
        if not task_list:
            raise ValueError("at least one task is required")
        if len(task_list) > config.max_tasks:
            raise DAGError("BUDGET-EXHAUSTED", "task count exceeds max_tasks")
        by_id = {task.task_id: task for task in task_list}
        if len(by_id) != len(task_list):
            raise ValueError("task IDs must be unique")
        if not set(run.root_task_ids).issubset(by_id):
            raise DAGError("UNKNOWN-DEPENDENCY", "every root task must exist in the run")
        edges = {(task.task_id, dep) for task in task_list for dep in task.depends_on}
        if len(edges) > config.max_edges:
            raise DAGError("BUDGET-EXHAUSTED", "edge count exceeds max_edges")
        self._validate_graph(set(by_id), edges)
        resolved_config_digest = run.config_digest or canonical_digest(config.to_dict())
        run_identity = {
            "run_id": run.run_id,
            "tenant_id": run.tenant_id,
            "project_id": run.project_id,
            "root_task_ids": list(run.root_task_ids),
            "config_digest": resolved_config_digest,
            "policy_digest": run.policy_digest,
            "budget_limits": run.budget_limits,
            "security_context": run.security_context,
            "schema_version": run.schema_version,
        }
        payload_digest = canonical_digest({
            "run": run_identity,
            "tasks": [task.to_dict() for task in task_list],
            "config": config.to_dict(),
        })
        with self._transaction() as db:
            existing = db.execute("SELECT payload FROM dag_runs WHERE run_id=?", (run.run_id,)).fetchone()
            if existing is not None:
                stored = DAGRun.from_dict(_loads(existing["payload"]))
                command = self._command_locked(db, run.run_id, f"create:{run.run_id}", payload_digest)
                if command is None:
                    raise DAGError("IDEMPOTENCY-CONFLICT", "run ID already exists with different content")
                return stored
            run.graph_revision = 1
            run.config_digest = resolved_config_digest
            run.updated_at = utc_now()
            db.execute(
                "INSERT INTO dag_runs(run_id,status,graph_revision,scheduler_epoch,payload,updated_at) VALUES(?,?,?,?,?,?)",
                (run.run_id, run.status.value, run.graph_revision, run.scheduler_epoch, _json(run.to_dict()), run.updated_at),
            )
            for task in task_list:
                status = DAGTaskStatus.READY if not task.depends_on else DAGTaskStatus.WAITING_DEPENDENCIES
                state = TaskState(task_id=task.task_id, status=status)
                created = utc_now()
                db.execute(
                    "INSERT INTO dag_tasks(run_id,task_id,status,priority,spec,state,created_at) VALUES(?,?,?,?,?,?,?)",
                    (run.run_id, task.task_id, status.value, task.priority, _json(task.to_dict()), _json(state.to_dict()), created),
                )
            for task_id, dependency_id in sorted(edges):
                db.execute(
                    "INSERT INTO dag_dependencies(run_id,task_id,dependency_id,decomposition_id) VALUES(?,?,?,?)",
                    (run.run_id, task_id, dependency_id, "initial"),
                )
            self._append_event_locked(db, run.run_id, "dag.run.created", data={
                "root_task_ids": list(run.root_task_ids),
                "config_digest": run.config_digest,
            })
            self._save_command_locked(
                db,
                run.run_id,
                f"create:{run.run_id}",
                payload_digest,
                run.to_dict(),
            )
        return deepcopy(run)

    def get_run(self, run_id: str) -> DAGRun | None:
        row = self._connection.execute("SELECT payload FROM dag_runs WHERE run_id=?", (run_id,)).fetchone()
        return DAGRun.from_dict(_loads(row["payload"])) if row else None

    def list_tasks(self, run_id: str) -> list[DAGTask]:
        rows = self._connection.execute(
            "SELECT spec,state,created_at FROM dag_tasks WHERE run_id=? ORDER BY priority DESC,created_at,task_id",
            (run_id,),
        ).fetchall()
        return [self._task_from_row(row) for row in rows]

    def get_task(self, run_id: str, task_id: str) -> DAGTask | None:
        row = self._connection.execute(
            "SELECT spec,state,created_at FROM dag_tasks WHERE run_id=? AND task_id=?",
            (run_id, task_id),
        ).fetchone()
        return self._task_from_row(row) if row else None

    def dependencies(self, run_id: str, task_id: str) -> list[str]:
        rows = self._connection.execute(
            "SELECT dependency_id FROM dag_dependencies WHERE run_id=? AND task_id=? ORDER BY dependency_id",
            (run_id, task_id),
        ).fetchall()
        return [str(row["dependency_id"]) for row in rows]

    def events(self, run_id: str, after: int = 0, limit: int = 100) -> list[DAGEvent]:
        if limit < 1:
            raise ValueError("limit must be positive")
        rows = self._connection.execute(
            "SELECT payload FROM dag_events WHERE run_id=? AND sequence>? ORDER BY sequence LIMIT ?",
            (run_id, after, limit),
        ).fetchall()
        return [DAGEvent(**_loads(row["payload"])) for row in rows]

    def acquire_scheduler_lease(self, run_id: str, owner_id: str, lease_seconds: float) -> int:
        now = datetime.now(timezone.utc)
        expires = (now + timedelta(seconds=lease_seconds)).isoformat()
        with self._transaction() as db:
            self._require_run_locked(db, run_id)
            row = db.execute(
                "SELECT owner_id,epoch,expires_at FROM dag_scheduler_leases WHERE run_id=?",
                (run_id,),
            ).fetchone()
            if row and row["owner_id"] != owner_id and _parse_time(row["expires_at"]) > now:
                raise DAGError("LEASE-REJECTED", "another scheduler owns an active lease")
            epoch = int(row["epoch"]) + 1 if row and row["owner_id"] != owner_id else int(row["epoch"]) if row else 1
            db.execute(
                "INSERT INTO dag_scheduler_leases(run_id,owner_id,epoch,expires_at) VALUES(?,?,?,?) "
                "ON CONFLICT(run_id) DO UPDATE SET owner_id=excluded.owner_id,epoch=excluded.epoch,expires_at=excluded.expires_at",
                (run_id, owner_id, epoch, expires),
            )
            self._update_run_locked(db, run_id, scheduler_epoch=epoch)
            self._append_event_locked(db, run_id, "dag.scheduler.acquired", data={"owner_id": owner_id, "epoch": epoch})
            return epoch

    def renew_scheduler_lease(self, run_id: str, owner_id: str, epoch: int, lease_seconds: float) -> None:
        expires = (datetime.now(timezone.utc) + timedelta(seconds=lease_seconds)).isoformat()
        with self._transaction() as db:
            changed = db.execute(
                "UPDATE dag_scheduler_leases SET expires_at=? WHERE run_id=? AND owner_id=? AND epoch=?",
                (expires, run_id, owner_id, epoch),
            ).rowcount
            if not changed:
                raise DAGError("LEASE-REJECTED", "scheduler lease is stale")

    def release_scheduler_lease(self, run_id: str, owner_id: str, epoch: int) -> None:
        with self._transaction() as db:
            db.execute(
                "DELETE FROM dag_scheduler_leases WHERE run_id=? AND owner_id=? AND epoch=?",
                (run_id, owner_id, epoch),
            )

    def expire_attempts(self, run_id: str) -> int:
        now = datetime.now(timezone.utc)
        expired = 0
        with self._transaction() as db:
            rows = db.execute(
                "SELECT attempt_id,payload FROM dag_attempts WHERE run_id=? AND status IN (?,?,?) AND lease_expires_at IS NOT NULL",
                (
                    run_id,
                    DAGAttemptStatus.CLAIMED.value,
                    DAGAttemptStatus.RUNNING.value,
                    DAGAttemptStatus.SUBMITTED.value,
                ),
            ).fetchall()
            for row in rows:
                attempt = TaskAttempt.from_dict(_loads(row["payload"]))
                if attempt.lease_expires_at is None or _parse_time(attempt.lease_expires_at) > now:
                    continue
                attempt.status = DAGAttemptStatus.EXPIRED
                attempt.updated_at = utc_now()
                self._save_attempt_locked(db, attempt)
                task = self._require_task_locked(db, run_id, attempt.task_id)
                if task.state.active_attempt_id == attempt.attempt_id:
                    task.state.active_attempt_id = None
                    task.state.status = DAGTaskStatus.READY
                    task.state.state_version += 1
                    task.state.last_diagnostic = "previous attempt lease expired"
                    task.state.updated_at = utc_now()
                    self._save_task_locked(db, run_id, task)
                self._append_event_locked(
                    db,
                    run_id,
                    "dag.attempt.expired",
                    task_id=attempt.task_id,
                    attempt_id=attempt.attempt_id,
                    data={"lease_epoch": attempt.lease_epoch},
                )
                expired += 1
        return expired

    def claim_ready_task(
            self,
            run_id: str,
            worker_id: str,
            lease_seconds: float,
    ) -> tuple[DAGTask, TaskAttempt] | None:
        with self._transaction() as db:
            run = self._require_run_locked(db, run_id)
            if run.status != DAGRunStatus.RUNNING:
                return None
            rows = db.execute(
                "SELECT spec,state,created_at FROM dag_tasks WHERE run_id=? AND status=? "
                "ORDER BY priority DESC,created_at,task_id",
                (run_id, DAGTaskStatus.READY.value),
            ).fetchall()
            for row in rows:
                task = self._task_from_row(row)
                if not self._dependencies_verified_locked(db, run_id, task.spec.task_id):
                    continue
                task.state.attempt_count += 1
                phase = "integrate" if task.state.decomposition_count else "solve"
                dependency_manifest = self._dependency_manifest_locked(db, run_id, task.spec.task_id)
                attempt = TaskAttempt(
                    run_id=run_id,
                    task_id=task.spec.task_id,
                    attempt_no=task.state.attempt_count,
                    worker_id=worker_id,
                    phase=phase,
                    input_snapshot_hash=canonical_digest({
                        "contract_hash": task.spec.contract_hash,
                        "dependencies": dependency_manifest,
                        "state_version": task.state.state_version,
                    }),
                    lease_expires_at=(datetime.now(timezone.utc) + timedelta(seconds=lease_seconds)).isoformat(),
                )
                task.state.status = DAGTaskStatus.RUNNING
                task.state.active_attempt_id = attempt.attempt_id
                task.state.state_version += 1
                task.state.updated_at = utc_now()
                self._save_task_locked(db, run_id, task)
                db.execute(
                    "INSERT INTO dag_attempts(attempt_id,run_id,task_id,status,lease_epoch,lease_expires_at,payload) "
                    "VALUES(?,?,?,?,?,?,?)",
                    (
                        attempt.attempt_id,
                        run_id,
                        task.spec.task_id,
                        attempt.status.value,
                        attempt.lease_epoch,
                        attempt.lease_expires_at,
                        _json(attempt.to_dict()),
                    ),
                )
                self._append_event_locked(
                    db,
                    run_id,
                    "dag.task.claimed",
                    task_id=task.spec.task_id,
                    attempt_id=attempt.attempt_id,
                    data={"worker_id": worker_id, "phase": phase, "lease_epoch": attempt.lease_epoch},
                )
                return deepcopy(task), deepcopy(attempt)
        return None

    def mark_attempt_running(self, attempt_id: str, lease_epoch: int) -> TaskAttempt:
        with self._transaction() as db:
            attempt = self._require_attempt_locked(db, attempt_id)
            self._assert_attempt_current_locked(db, attempt, lease_epoch)
            attempt.status = DAGAttemptStatus.RUNNING
            attempt.updated_at = utc_now()
            self._save_attempt_locked(db, attempt)
            return deepcopy(attempt)

    def renew_attempt(self, attempt_id: str, lease_epoch: int, lease_seconds: float) -> TaskAttempt:
        with self._transaction() as db:
            attempt = self._require_attempt_locked(db, attempt_id)
            self._assert_attempt_current_locked(db, attempt, lease_epoch)
            attempt.lease_expires_at = (datetime.now(timezone.utc) + timedelta(seconds=lease_seconds)).isoformat()
            attempt.updated_at = utc_now()
            self._save_attempt_locked(db, attempt)
            return deepcopy(attempt)

    def get_attempt(self, attempt_id: str) -> TaskAttempt | None:
        row = self._connection.execute(
            "SELECT payload FROM dag_attempts WHERE attempt_id=?",
            (attempt_id,),
        ).fetchone()
        return TaskAttempt.from_dict(_loads(row["payload"])) if row else None

    def save_staged_artifact(self, manifest: ArtifactManifest, lease_epoch: int) -> ArtifactManifest:
        with self._transaction() as db:
            attempt = self._require_attempt_locked(db, manifest.attempt_id)
            self._assert_attempt_current_locked(db, attempt, lease_epoch)
            existing = db.execute(
                "SELECT payload FROM dag_artifacts WHERE artifact_id=?",
                (manifest.artifact_id,),
            ).fetchone()
            if existing:
                stored = ArtifactManifest.from_dict(_loads(existing["payload"]))
                if stored.content_hash != manifest.content_hash:
                    raise DAGError("IDEMPOTENCY-CONFLICT", "artifact ID was reused with different content")
                return stored
            db.execute(
                "INSERT INTO dag_artifacts(artifact_id,run_id,task_id,attempt_id,state,content_hash,payload) VALUES(?,?,?,?,?,?,?)",
                (
                    manifest.artifact_id,
                    manifest.run_id,
                    manifest.task_id,
                    manifest.attempt_id,
                    manifest.state,
                    manifest.content_hash,
                    _json(manifest.to_dict()),
                ),
            )
            attempt.status = DAGAttemptStatus.SUBMITTED
            attempt.updated_at = utc_now()
            self._save_attempt_locked(db, attempt)
            task = self._require_task_locked(db, manifest.run_id, manifest.task_id)
            task.state.status = DAGTaskStatus.VERIFYING
            task.state.state_version += 1
            task.state.updated_at = utc_now()
            self._save_task_locked(db, manifest.run_id, task)
            self._append_event_locked(
                db,
                manifest.run_id,
                "dag.artifact.staged",
                task_id=manifest.task_id,
                attempt_id=manifest.attempt_id,
                data={"artifact_id": manifest.artifact_id, "content_hash": manifest.content_hash},
            )
            return deepcopy(manifest)

    def publish_artifact(
            self,
            manifest: ArtifactManifest,
            report: VerificationReport,
            lease_epoch: int,
    ) -> ArtifactManifest:
        if report.verdict.value != "pass":
            raise DAGError("VERIFICATION-FAILED", "only passing reports can publish artifacts")
        with self._transaction() as db:
            attempt = self._require_attempt_locked(db, manifest.attempt_id)
            self._assert_attempt_current_locked(db, attempt, lease_epoch)
            task = self._require_task_locked(db, manifest.run_id, manifest.task_id)
            if report.input_snapshot_hash != attempt.input_snapshot_hash:
                raise DAGError("VERSION-CONFLICT", "verification report input snapshot is stale")
            existing = db.execute(
                "SELECT payload,state FROM dag_artifacts WHERE artifact_id=?",
                (manifest.artifact_id,),
            ).fetchone()
            if existing is None:
                raise KeyError(manifest.artifact_id)
            stored = ArtifactManifest.from_dict(_loads(existing["payload"]))
            if stored.state == "published":
                return stored
            manifest.state = "published"
            manifest.verification_report_id = report.report_id
            db.execute(
                "INSERT OR IGNORE INTO dag_reports(report_id,run_id,task_id,attempt_id,payload) VALUES(?,?,?,?,?)",
                (report.report_id, manifest.run_id, manifest.task_id, manifest.attempt_id, _json(report.to_dict())),
            )
            db.execute(
                "UPDATE dag_artifacts SET state=?,payload=? WHERE artifact_id=?",
                (manifest.state, _json(manifest.to_dict()), manifest.artifact_id),
            )
            attempt.status = DAGAttemptStatus.SUCCEEDED
            attempt.updated_at = utc_now()
            self._save_attempt_locked(db, attempt)
            task.state.status = DAGTaskStatus.VERIFIED
            task.state.active_attempt_id = None
            task.state.blocker = None
            task.state.verified_artifact_ids = list(dict.fromkeys([
                *task.state.verified_artifact_ids,
                manifest.artifact_id,
            ]))
            task.state.state_version += 1
            task.state.updated_at = utc_now()
            self._save_task_locked(db, manifest.run_id, task)
            self._append_event_locked(
                db,
                manifest.run_id,
                "dag.artifact.published",
                task_id=manifest.task_id,
                attempt_id=manifest.attempt_id,
                data={"artifact_id": manifest.artifact_id, "report_id": report.report_id},
            )
            self._append_event_locked(
                db,
                manifest.run_id,
                "dag.task.verified",
                task_id=manifest.task_id,
                attempt_id=manifest.attempt_id,
                data={"artifact_ids": list(task.state.verified_artifact_ids)},
            )
            self._refresh_dependents_locked(db, manifest.run_id, manifest.task_id)
            self._refresh_run_status_locked(db, manifest.run_id)
            return deepcopy(manifest)

    def reject_candidate(
            self,
            attempt_id: str,
            lease_epoch: int,
            report: VerificationReport,
            max_attempts: int,
    ) -> DAGTask:
        with self._transaction() as db:
            attempt = self._require_attempt_locked(db, attempt_id)
            self._assert_attempt_current_locked(db, attempt, lease_epoch)
            task = self._require_task_locked(db, attempt.run_id, attempt.task_id)
            db.execute(
                "INSERT OR IGNORE INTO dag_reports(report_id,run_id,task_id,attempt_id,payload) VALUES(?,?,?,?,?)",
                (report.report_id, attempt.run_id, attempt.task_id, attempt_id, _json(report.to_dict())),
            )
            attempt.status = DAGAttemptStatus.FAILED
            attempt.error = "; ".join(report.diagnostics) or report.verdict.value
            attempt.updated_at = utc_now()
            self._save_attempt_locked(db, attempt)
            task.state.verification_failure_count += 1
            task.state.active_attempt_id = None
            task.state.last_diagnostic = attempt.error
            task.state.status = (
                DAGTaskStatus.READY
                if task.state.attempt_count < max_attempts and report.verdict.value in {"fail", "error"}
                else DAGTaskStatus.BLOCKED
                if report.verdict.value == "inconclusive"
                else DAGTaskStatus.FAILED
            )
            task.state.blocker = attempt.error if task.state.status == DAGTaskStatus.BLOCKED else None
            task.state.state_version += 1
            task.state.updated_at = utc_now()
            self._save_task_locked(db, attempt.run_id, task)
            self._append_event_locked(
                db,
                attempt.run_id,
                "dag.verification.failed",
                task_id=attempt.task_id,
                attempt_id=attempt_id,
                data={"report_id": report.report_id, "verdict": report.verdict.value, "diagnostics": report.diagnostics},
            )
            self._refresh_run_status_locked(db, attempt.run_id)
            return deepcopy(task)

    def accept_decomposition(
            self,
            run_id: str,
            attempt_id: str,
            lease_epoch: int,
            proposal: DecompositionProposal,
            report: VerificationReport,
            config: DAGConfig,
    ) -> list[DAGTask]:
        if report.verdict.value != "pass":
            raise DAGError("VERIFICATION-FAILED", "decomposition requires a passing report")
        with self._transaction() as db:
            attempt = self._require_attempt_locked(db, attempt_id)
            self._assert_attempt_current_locked(db, attempt, lease_epoch)
            if attempt.task_id != proposal.parent_task_id or attempt.run_id != run_id:
                raise DAGError("STALE-ATTEMPT", "proposal is not bound to the active parent attempt")
            run = self._require_run_locked(db, run_id)
            if proposal.expected_graph_revision != run.graph_revision:
                raise DAGError("VERSION-CONFLICT", "decomposition graph revision is stale")
            parent = self._require_task_locked(db, run_id, proposal.parent_task_id)
            if parent.state.decomposition_count >= config.max_decompositions_per_task:
                raise DAGError("BUDGET-EXHAUSTED", "task decomposition limit reached")
            existing = db.execute(
                "SELECT proposal_digest FROM dag_decompositions WHERE proposal_id=?",
                (proposal.proposal_id,),
            ).fetchone()
            if existing:
                if existing["proposal_digest"] != proposal.digest:
                    raise DAGError("IDEMPOTENCY-CONFLICT", "proposal ID was reused with different content")
                return [self._require_task_locked(db, run_id, task.task_id) for task in proposal.new_tasks]
            existing_ids = {
                str(row["task_id"])
                for row in db.execute("SELECT task_id FROM dag_tasks WHERE run_id=?", (run_id,)).fetchall()
            }
            new_ids = {task.task_id for task in proposal.new_tasks}
            if len(new_ids) != len(proposal.new_tasks) or existing_ids & new_ids:
                raise DAGError("IDEMPOTENCY-CONFLICT", "decomposition task IDs must be new and unique")
            if not set(proposal.reuse_task_ids).issubset(existing_ids):
                raise DAGError("UNKNOWN-DEPENDENCY", "decomposition references an unknown reusable task")
            all_ids = existing_ids | new_ids
            edges = {
                (str(row["task_id"]), str(row["dependency_id"]))
                for row in db.execute(
                    "SELECT task_id,dependency_id FROM dag_dependencies WHERE run_id=?",
                    (run_id,),
                ).fetchall()
            }
            for task in proposal.new_tasks:
                edges.update((task.task_id, dep) for dep in task.depends_on)
            edges.update((proposal.parent_task_id, task_id) for task_id in sorted(new_ids | set(proposal.reuse_task_ids)))
            if len(all_ids) > config.max_tasks or len(edges) > config.max_edges:
                raise DAGError("BUDGET-EXHAUSTED", "decomposition exceeds graph limits")
            self._validate_graph(all_ids, edges)
            created_tasks = []
            for task in proposal.new_tasks:
                status = DAGTaskStatus.READY if not task.depends_on else DAGTaskStatus.WAITING_DEPENDENCIES
                state = TaskState(task_id=task.task_id, status=status)
                created = utc_now()
                db.execute(
                    "INSERT INTO dag_tasks(run_id,task_id,status,priority,spec,state,created_at) VALUES(?,?,?,?,?,?,?)",
                    (run_id, task.task_id, status.value, task.priority, _json(task.to_dict()), _json(state.to_dict()), created),
                )
                created_tasks.append(DAGTask(task, state, created))
            db.execute(
                "DELETE FROM dag_dependencies WHERE run_id=? AND task_id=?",
                (run_id, proposal.parent_task_id),
            )
            for task_id, dependency_id in sorted(edges):
                if task_id not in new_ids and task_id != proposal.parent_task_id:
                    continue
                db.execute(
                    "INSERT OR IGNORE INTO dag_dependencies(run_id,task_id,dependency_id,decomposition_id) VALUES(?,?,?,?)",
                    (run_id, task_id, dependency_id, proposal.proposal_id),
                )
            db.execute(
                "INSERT INTO dag_decompositions(proposal_id,run_id,parent_task_id,proposal_digest,payload) VALUES(?,?,?,?,?)",
                (proposal.proposal_id, run_id, proposal.parent_task_id, proposal.digest, _json(proposal.to_dict())),
            )
            db.execute(
                "INSERT OR IGNORE INTO dag_reports(report_id,run_id,task_id,attempt_id,payload) VALUES(?,?,?,?,?)",
                (report.report_id, run_id, parent.spec.task_id, attempt_id, _json(report.to_dict())),
            )
            attempt.status = DAGAttemptStatus.SUCCEEDED
            attempt.updated_at = utc_now()
            self._save_attempt_locked(db, attempt)
            parent.state.status = DAGTaskStatus.WAITING_DEPENDENCIES
            parent.state.active_attempt_id = None
            parent.state.decomposition_count += 1
            parent.state.dependency_revision += 1
            parent.state.state_version += 1
            parent.state.updated_at = utc_now()
            self._save_task_locked(db, run_id, parent)
            run.graph_revision += 1
            run.updated_at = utc_now()
            self._save_run_locked(db, run)
            self._append_event_locked(
                db,
                run_id,
                "dag.decomposition.accepted",
                task_id=parent.spec.task_id,
                attempt_id=attempt_id,
                data={
                    "proposal_id": proposal.proposal_id,
                    "new_task_ids": sorted(new_ids),
                    "reuse_task_ids": list(proposal.reuse_task_ids),
                    "graph_revision": run.graph_revision,
                },
            )
            return deepcopy(created_tasks)

    def block_attempt(self, attempt_id: str, lease_epoch: int, reason: str) -> DAGTask:
        with self._transaction() as db:
            attempt = self._require_attempt_locked(db, attempt_id)
            self._assert_attempt_current_locked(db, attempt, lease_epoch)
            attempt.status = DAGAttemptStatus.FAILED
            attempt.error = reason
            attempt.updated_at = utc_now()
            self._save_attempt_locked(db, attempt)
            task = self._require_task_locked(db, attempt.run_id, attempt.task_id)
            task.state.status = DAGTaskStatus.BLOCKED
            task.state.blocker = reason
            task.state.last_diagnostic = reason
            task.state.active_attempt_id = None
            task.state.state_version += 1
            task.state.updated_at = utc_now()
            self._save_task_locked(db, attempt.run_id, task)
            self._append_event_locked(
                db,
                attempt.run_id,
                "dag.task.blocked",
                task_id=attempt.task_id,
                attempt_id=attempt_id,
                data={"reason": reason},
            )
            self._refresh_run_status_locked(db, attempt.run_id)
            return deepcopy(task)

    def fail_attempt(
            self,
            attempt_id: str,
            lease_epoch: int,
            reason: str,
            max_attempts: int,
    ) -> DAGTask:
        with self._transaction() as db:
            attempt = self._require_attempt_locked(db, attempt_id)
            self._assert_attempt_current_locked(db, attempt, lease_epoch)
            attempt.status = DAGAttemptStatus.FAILED
            attempt.error = reason
            attempt.updated_at = utc_now()
            self._save_attempt_locked(db, attempt)
            task = self._require_task_locked(db, attempt.run_id, attempt.task_id)
            task.state.active_attempt_id = None
            task.state.last_diagnostic = reason
            task.state.status = (
                DAGTaskStatus.READY
                if task.state.attempt_count < max_attempts
                else DAGTaskStatus.FAILED
            )
            task.state.state_version += 1
            task.state.updated_at = utc_now()
            self._save_task_locked(db, attempt.run_id, task)
            self._append_event_locked(
                db,
                attempt.run_id,
                "dag.attempt.failed",
                task_id=attempt.task_id,
                attempt_id=attempt_id,
                data={"reason": reason, "retrying": task.state.status == DAGTaskStatus.READY},
            )
            self._refresh_run_status_locked(db, attempt.run_id)
            return deepcopy(task)

    def block_task(self, run_id: str, task_id: str, reason: str) -> DAGTask:
        with self._transaction() as db:
            task = self._require_task_locked(db, run_id, task_id)
            if task.state.status in {
                DAGTaskStatus.VERIFIED,
                DAGTaskStatus.FAILED,
                DAGTaskStatus.CANCELLED,
                DAGTaskStatus.SUPERSEDED,
            }:
                raise DAGError("VERSION-CONFLICT", "terminal task cannot be blocked")
            task.state.status = DAGTaskStatus.BLOCKED
            task.state.blocker = reason
            task.state.last_diagnostic = reason
            task.state.active_attempt_id = None
            task.state.state_version += 1
            task.state.updated_at = utc_now()
            self._save_task_locked(db, run_id, task)
            self._append_event_locked(db, run_id, "dag.task.blocked", task_id=task_id, data={"reason": reason})
            self._refresh_run_status_locked(db, run_id)
            return deepcopy(task)

    def resolve_blocker(self, run_id: str, task_id: str, reason: str | None = None) -> DAGTask:
        with self._transaction() as db:
            task = self._require_task_locked(db, run_id, task_id)
            if task.state.status not in {DAGTaskStatus.BLOCKED, DAGTaskStatus.WAITING_APPROVAL}:
                raise DAGError("VERSION-CONFLICT", "task is not blocked")
            task.state.status = DAGTaskStatus.READY
            task.state.blocker = None
            task.state.last_diagnostic = reason or task.state.last_diagnostic
            task.state.state_version += 1
            task.state.updated_at = utc_now()
            self._save_task_locked(db, run_id, task)
            self._update_run_locked(db, run_id, status=DAGRunStatus.RUNNING, blocker=None)
            self._append_event_locked(db, run_id, "dag.task.unblocked", task_id=task_id, data={"reason": reason})
            return deepcopy(task)

    def supersede_task(
            self,
            run_id: str,
            task_id: str,
            replacement: TaskSpec,
            *,
            expected_graph_revision: int,
            config: DAGConfig,
    ) -> DAGTask:
        with self._transaction() as db:
            run = self._require_run_locked(db, run_id)
            if run.graph_revision != expected_graph_revision:
                raise DAGError("VERSION-CONFLICT", "replacement graph revision is stale")
            original = self._require_task_locked(db, run_id, task_id)
            if original.state.status == DAGTaskStatus.VERIFIED:
                raise DAGError("VERSION-CONFLICT", "a verified task cannot be superseded in place")
            if replacement.task_id == task_id:
                raise ValueError("replacement task must have a new task_id")
            if replacement.supersedes_task_id not in {None, task_id}:
                raise ValueError("replacement supersedes_task_id does not match the original task")
            if task_id in replacement.depends_on:
                raise ValueError("replacement task cannot depend on the task it supersedes")
            if db.execute(
                "SELECT 1 FROM dag_tasks WHERE run_id=? AND task_id=?",
                (run_id, replacement.task_id),
            ).fetchone():
                raise DAGError("IDEMPOTENCY-CONFLICT", "replacement task_id already exists")
            dependents = db.execute(
                "SELECT t.spec,t.state,t.created_at FROM dag_dependencies d "
                "JOIN dag_tasks t ON t.run_id=d.run_id AND t.task_id=d.task_id "
                "WHERE d.run_id=? AND d.dependency_id=?",
                (run_id, task_id),
            ).fetchall()
            if any(self._task_from_row(row).state.status == DAGTaskStatus.VERIFIED for row in dependents):
                raise DAGError("VERSION-CONFLICT", "verified downstream tasks cannot be rewired in place")
            task_ids = {
                str(row["task_id"])
                for row in db.execute("SELECT task_id FROM dag_tasks WHERE run_id=?", (run_id,)).fetchall()
            } | {replacement.task_id}
            edges = {
                (str(row["task_id"]), str(row["dependency_id"]))
                for row in db.execute(
                    "SELECT task_id,dependency_id FROM dag_dependencies WHERE run_id=?",
                    (run_id,),
                ).fetchall()
            }
            edges = {
                (dependent, replacement.task_id if dependency == task_id else dependency)
                for dependent, dependency in edges
            }
            edges.update((replacement.task_id, dependency) for dependency in replacement.depends_on)
            if len(task_ids) > config.max_tasks or len(edges) > config.max_edges:
                raise DAGError("BUDGET-EXHAUSTED", "replacement exceeds graph limits")
            self._validate_graph(task_ids, edges)
            if original.state.active_attempt_id:
                attempt = self._require_attempt_locked(db, original.state.active_attempt_id)
                attempt.status = DAGAttemptStatus.CANCELLED
                attempt.error = "task was superseded"
                attempt.updated_at = utc_now()
                self._save_attempt_locked(db, attempt)
            original.state.status = DAGTaskStatus.SUPERSEDED
            original.state.active_attempt_id = None
            original.state.blocker = f"superseded by {replacement.task_id}"
            original.state.state_version += 1
            original.state.updated_at = utc_now()
            self._save_task_locked(db, run_id, original)
            state = TaskState(
                task_id=replacement.task_id,
                status=(
                    DAGTaskStatus.READY
                    if not replacement.depends_on
                    else DAGTaskStatus.WAITING_DEPENDENCIES
                ),
            )
            created = utc_now()
            db.execute(
                "INSERT INTO dag_tasks(run_id,task_id,status,priority,spec,state,created_at) VALUES(?,?,?,?,?,?,?)",
                (
                    run_id,
                    replacement.task_id,
                    state.status.value,
                    replacement.priority,
                    _json(replacement.to_dict()),
                    _json(state.to_dict()),
                    created,
                ),
            )
            db.execute(
                "UPDATE dag_dependencies SET dependency_id=? WHERE run_id=? AND dependency_id=?",
                (replacement.task_id, run_id, task_id),
            )
            for row in dependents:
                dependent = self._task_from_row(row)
                dependent.state.dependency_revision += 1
                dependent.state.state_version += 1
                dependent.state.updated_at = utc_now()
                self._save_task_locked(db, run_id, dependent)
            for dependency in replacement.depends_on:
                db.execute(
                    "INSERT OR IGNORE INTO dag_dependencies(run_id,task_id,dependency_id,decomposition_id) VALUES(?,?,?,?)",
                    (run_id, replacement.task_id, dependency, f"supersede:{task_id}"),
                )
            run.root_task_ids = [replacement.task_id if root == task_id else root for root in run.root_task_ids]
            run.graph_revision += 1
            run.updated_at = utc_now()
            self._save_run_locked(db, run)
            self._append_event_locked(
                db,
                run_id,
                "dag.task.superseded",
                task_id=task_id,
                data={
                    "replacement_task_id": replacement.task_id,
                    "graph_revision": run.graph_revision,
                },
            )
            return DAGTask(replacement, state, created)

    def set_run_status(self, run_id: str, status: DAGRunStatus, reason: str | None = None) -> DAGRun:
        with self._transaction() as db:
            run = self._require_run_locked(db, run_id)
            run.status = status
            run.blocker = reason
            run.updated_at = utc_now()
            self._save_run_locked(db, run)
            if status == DAGRunStatus.CANCELLED:
                rows = db.execute(
                    "SELECT spec,state,created_at FROM dag_tasks WHERE run_id=? AND status NOT IN (?,?,?,?)",
                    (
                        run_id,
                        DAGTaskStatus.VERIFIED.value,
                        DAGTaskStatus.FAILED.value,
                        DAGTaskStatus.CANCELLED.value,
                        DAGTaskStatus.SUPERSEDED.value,
                    ),
                ).fetchall()
                for row in rows:
                    task = self._task_from_row(row)
                    task.state.status = DAGTaskStatus.CANCELLED
                    task.state.active_attempt_id = None
                    task.state.blocker = reason
                    task.state.state_version += 1
                    task.state.updated_at = utc_now()
                    self._save_task_locked(db, run_id, task)
            event_name = {
                DAGRunStatus.PAUSED: "dag.run.paused",
                DAGRunStatus.RUNNING: "dag.run.resumed",
                DAGRunStatus.CANCELLED: "dag.run.cancelled",
                DAGRunStatus.SUCCEEDED: "dag.run.completed",
                DAGRunStatus.FAILED: "dag.run.failed",
                DAGRunStatus.BLOCKED: "dag.run.blocked",
            }[status]
            self._append_event_locked(db, run_id, event_name, data={"reason": reason})
            return deepcopy(run)

    def refresh_run_status(self, run_id: str) -> DAGRun:
        with self._transaction() as db:
            return deepcopy(self._refresh_run_status_locked(db, run_id))

    def list_artifacts(
            self,
            run_id: str,
            task_id: str | None = None,
            *,
            state: str | None = "published",
    ) -> list[ArtifactManifest]:
        clauses = ["run_id=?"]
        params: list[Any] = [run_id]
        if task_id is not None:
            clauses.append("task_id=?")
            params.append(task_id)
        if state is not None:
            clauses.append("state=?")
            params.append(state)
        rows = self._connection.execute(
            f"SELECT payload FROM dag_artifacts WHERE {' AND '.join(clauses)} ORDER BY artifact_id",
            tuple(params),
        ).fetchall()
        return [ArtifactManifest.from_dict(_loads(row["payload"])) for row in rows]

    def get_report(self, report_id: str) -> VerificationReport | None:
        row = self._connection.execute(
            "SELECT payload FROM dag_reports WHERE report_id=?",
            (report_id,),
        ).fetchone()
        return VerificationReport.from_dict(_loads(row["payload"])) if row else None

    @staticmethod
    def _validate_graph(task_ids: set[str], edges: set[tuple[str, str]]) -> None:
        unknown = sorted({item for edge in edges for item in edge if item not in task_ids})
        if unknown:
            raise DAGError("UNKNOWN-DEPENDENCY", f"unknown task IDs: {unknown}")
        if any(task_id == dependency_id for task_id, dependency_id in edges):
            raise DAGError("CYCLE", "self dependencies are not allowed")
        indegree = {task_id: 0 for task_id in task_ids}
        reverse: dict[str, list[str]] = {task_id: [] for task_id in task_ids}
        for task_id, dependency_id in edges:
            indegree[task_id] += 1
            reverse[dependency_id].append(task_id)
        ready = [task_id for task_id, degree in indegree.items() if degree == 0]
        visited = 0
        while ready:
            current = ready.pop()
            visited += 1
            for dependent in reverse[current]:
                indegree[dependent] -= 1
                if indegree[dependent] == 0:
                    ready.append(dependent)
        if visited != len(task_ids):
            raise DAGError("CYCLE", "task dependencies contain a cycle")

    def _task_from_row(self, row: sqlite3.Row) -> DAGTask:
        return DAGTask(
            spec=TaskSpec.from_dict(_loads(row["spec"])),
            state=TaskState.from_dict(_loads(row["state"])),
            created_at=str(row["created_at"]),
        )

    def _require_run_locked(self, db: sqlite3.Connection, run_id: str) -> DAGRun:
        row = db.execute("SELECT payload FROM dag_runs WHERE run_id=?", (run_id,)).fetchone()
        if row is None:
            raise KeyError(run_id)
        return DAGRun.from_dict(_loads(row["payload"]))

    def _require_task_locked(self, db: sqlite3.Connection, run_id: str, task_id: str) -> DAGTask:
        row = db.execute(
            "SELECT spec,state,created_at FROM dag_tasks WHERE run_id=? AND task_id=?",
            (run_id, task_id),
        ).fetchone()
        if row is None:
            raise KeyError(task_id)
        return self._task_from_row(row)

    def _require_attempt_locked(self, db: sqlite3.Connection, attempt_id: str) -> TaskAttempt:
        row = db.execute("SELECT payload FROM dag_attempts WHERE attempt_id=?", (attempt_id,)).fetchone()
        if row is None:
            raise KeyError(attempt_id)
        return TaskAttempt.from_dict(_loads(row["payload"]))

    def _assert_attempt_current_locked(
            self,
            db: sqlite3.Connection,
            attempt: TaskAttempt,
            lease_epoch: int,
    ) -> None:
        task = self._require_task_locked(db, attempt.run_id, attempt.task_id)
        if attempt.lease_epoch != lease_epoch or task.state.active_attempt_id != attempt.attempt_id:
            raise DAGError("STALE-ATTEMPT", "attempt no longer owns the task")
        if attempt.status in {DAGAttemptStatus.EXPIRED, DAGAttemptStatus.CANCELLED, DAGAttemptStatus.FAILED}:
            raise DAGError("STALE-ATTEMPT", f"attempt is {attempt.status.value}")
        if attempt.lease_expires_at and _parse_time(attempt.lease_expires_at) <= datetime.now(timezone.utc):
            raise DAGError("STALE-ATTEMPT", "attempt lease has expired")

    def _save_run_locked(self, db: sqlite3.Connection, run: DAGRun) -> None:
        db.execute(
            "UPDATE dag_runs SET status=?,graph_revision=?,scheduler_epoch=?,payload=?,updated_at=? WHERE run_id=?",
            (run.status.value, run.graph_revision, run.scheduler_epoch, _json(run.to_dict()), run.updated_at, run.run_id),
        )

    def _update_run_locked(
            self,
            db: sqlite3.Connection,
            run_id: str,
            *,
            status: DAGRunStatus | None = None,
            scheduler_epoch: int | None = None,
            blocker: str | None = None,
    ) -> DAGRun:
        run = self._require_run_locked(db, run_id)
        if status is not None:
            run.status = status
        if scheduler_epoch is not None:
            run.scheduler_epoch = scheduler_epoch
        run.blocker = blocker
        run.updated_at = utc_now()
        self._save_run_locked(db, run)
        return run

    def _save_task_locked(self, db: sqlite3.Connection, run_id: str, task: DAGTask) -> None:
        db.execute(
            "UPDATE dag_tasks SET status=?,priority=?,spec=?,state=? WHERE run_id=? AND task_id=?",
            (
                task.state.status.value,
                task.spec.priority,
                _json(task.spec.to_dict()),
                _json(task.state.to_dict()),
                run_id,
                task.spec.task_id,
            ),
        )

    def _save_attempt_locked(self, db: sqlite3.Connection, attempt: TaskAttempt) -> None:
        db.execute(
            "UPDATE dag_attempts SET status=?,lease_epoch=?,lease_expires_at=?,payload=? WHERE attempt_id=?",
            (
                attempt.status.value,
                attempt.lease_epoch,
                attempt.lease_expires_at,
                _json(attempt.to_dict()),
                attempt.attempt_id,
            ),
        )

    def _append_event_locked(
            self,
            db: sqlite3.Connection,
            run_id: str,
            event_type: str,
            *,
            task_id: str | None = None,
            attempt_id: str | None = None,
            data: Mapping[str, Any] | None = None,
    ) -> DAGEvent:
        row = db.execute(
            "SELECT COALESCE(MAX(sequence),0)+1 AS sequence FROM dag_events WHERE run_id=?",
            (run_id,),
        ).fetchone()
        event = DAGEvent(
            run_id=run_id,
            sequence=int(row["sequence"]),
            type=event_type,
            task_id=task_id,
            attempt_id=attempt_id,
            data=deepcopy(dict(data or {})),
        )
        db.execute(
            "INSERT INTO dag_events(run_id,sequence,payload) VALUES(?,?,?)",
            (run_id, event.sequence, _json(event.to_dict())),
        )
        return event

    def _dependencies_verified_locked(self, db: sqlite3.Connection, run_id: str, task_id: str) -> bool:
        row = db.execute(
            "SELECT COUNT(*) AS pending FROM dag_dependencies d "
            "JOIN dag_tasks t ON t.run_id=d.run_id AND t.task_id=d.dependency_id "
            "WHERE d.run_id=? AND d.task_id=? AND t.status != ?",
            (run_id, task_id, DAGTaskStatus.VERIFIED.value),
        ).fetchone()
        return int(row["pending"]) == 0

    def _dependency_manifest_locked(self, db: sqlite3.Connection, run_id: str, task_id: str) -> dict[str, list[str]]:
        rows = db.execute(
            "SELECT d.dependency_id,a.artifact_id FROM dag_dependencies d "
            "LEFT JOIN dag_artifacts a ON a.run_id=d.run_id AND a.task_id=d.dependency_id AND a.state='published' "
            "WHERE d.run_id=? AND d.task_id=? ORDER BY d.dependency_id,a.artifact_id",
            (run_id, task_id),
        ).fetchall()
        result: dict[str, list[str]] = {}
        for row in rows:
            result.setdefault(str(row["dependency_id"]), [])
            if row["artifact_id"] is not None:
                result[str(row["dependency_id"])].append(str(row["artifact_id"]))
        return result

    def _refresh_dependents_locked(self, db: sqlite3.Connection, run_id: str, dependency_id: str) -> None:
        rows = db.execute(
            "SELECT t.spec,t.state,t.created_at FROM dag_dependencies d "
            "JOIN dag_tasks t ON t.run_id=d.run_id AND t.task_id=d.task_id "
            "WHERE d.run_id=? AND d.dependency_id=?",
            (run_id, dependency_id),
        ).fetchall()
        for row in rows:
            task = self._task_from_row(row)
            if task.state.status != DAGTaskStatus.WAITING_DEPENDENCIES:
                continue
            if self._dependencies_verified_locked(db, run_id, task.spec.task_id):
                task.state.status = DAGTaskStatus.READY
                task.state.state_version += 1
                task.state.updated_at = utc_now()
                self._save_task_locked(db, run_id, task)
                self._append_event_locked(db, run_id, "dag.task.ready", task_id=task.spec.task_id)

    def _refresh_run_status_locked(self, db: sqlite3.Connection, run_id: str) -> DAGRun:
        run = self._require_run_locked(db, run_id)
        tasks = [
            self._task_from_row(row)
            for row in db.execute(
                "SELECT spec,state,created_at FROM dag_tasks WHERE run_id=?",
                (run_id,),
            ).fetchall()
        ]
        roots = [task for task in tasks if task.spec.task_id in run.root_task_ids]
        if roots and all(task.state.status == DAGTaskStatus.VERIFIED for task in roots):
            run.status = DAGRunStatus.SUCCEEDED
            run.blocker = None
            event = "dag.run.completed"
        elif any(task.state.status in {DAGTaskStatus.BLOCKED, DAGTaskStatus.WAITING_APPROVAL} for task in tasks) and not any(
            task.state.status in {DAGTaskStatus.READY, DAGTaskStatus.RUNNING, DAGTaskStatus.VERIFYING}
            for task in tasks
        ):
            run.status = DAGRunStatus.BLOCKED
            run.blocker = "workflow requires external action"
            event = "dag.run.blocked"
        elif not any(
            task.state.status in {
                DAGTaskStatus.READY,
                DAGTaskStatus.RUNNING,
                DAGTaskStatus.VERIFYING,
                DAGTaskStatus.RETRY_WAIT,
            }
            for task in tasks
        ) and any(task.state.status == DAGTaskStatus.FAILED for task in tasks):
            run.status = DAGRunStatus.FAILED
            run.blocker = "a required dependency task failed"
            event = "dag.run.failed"
        else:
            return run
        run.updated_at = utc_now()
        self._save_run_locked(db, run)
        last = db.execute(
            "SELECT payload FROM dag_events WHERE run_id=? ORDER BY sequence DESC LIMIT 1",
            (run_id,),
        ).fetchone()
        if not last or _loads(last["payload"])["type"] != event:
            self._append_event_locked(db, run_id, event, data={"reason": run.blocker})
        return run

    def _command_locked(
            self,
            db: sqlite3.Connection,
            run_id: str,
            command_key: str,
            request_digest: str,
    ) -> dict[str, Any] | None:
        row = db.execute(
            "SELECT request_digest,response FROM dag_commands WHERE run_id=? AND command_key=?",
            (run_id, command_key),
        ).fetchone()
        if row is None or row["request_digest"] != request_digest:
            return None
        return _loads(row["response"])

    def _save_command_locked(
            self,
            db: sqlite3.Connection,
            run_id: str,
            command_key: str,
            request_digest: str,
            response: Mapping[str, Any],
    ) -> None:
        db.execute(
            "INSERT INTO dag_commands(run_id,command_key,request_digest,response) VALUES(?,?,?,?)",
            (run_id, command_key, request_digest, _json(response)),
        )


__all__ = ["DAGError", "TaskGraphStore", "SqliteTaskGraphStore"]
