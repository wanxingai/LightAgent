"""Single-host concurrent scheduler for persistent, verification-gated task DAGs."""

from __future__ import annotations

import asyncio
import json
from copy import deepcopy
from dataclasses import replace
from typing import Any, Iterable, Mapping
from uuid import uuid4

from ..cancellation import CancellationToken
from ..capabilities import CapabilityRisk, CapabilitySpec
from ..security import CapabilityGate, SecurityContext, canonical_digest
from .artifacts import ArtifactStore, LocalArtifactStore
from .models import (
    DAGConfig,
    DAGRun,
    DAGRunResult,
    DAGRunStatus,
    DAGTask,
    DAGTaskStatus,
    TaskContext,
    TaskOutcomeKind,
    TaskSpec,
    VerificationRequest,
    VerificationVerdict,
)
from .store import DAGError, SqliteTaskGraphStore, TaskGraphStore
from .verification import Verifier
from .worker import DAGWorkerProtocolError, RegistryWorkerFactory, WorkerFactory


class LightDAG:
    """Opt-in persistent DAG runtime with explicit Worker and Verifier contracts."""

    execution_capability = CapabilitySpec(
        "dag.task.execute",
        description="Execute one isolated LightDAG task attempt",
        risk=CapabilityRisk.SENSITIVE,
        execute=True,
        persistent=True,
        cancellable=True,
    )

    def __init__(
            self,
            *,
            store: TaskGraphStore | None = None,
            artifact_store: ArtifactStore | None = None,
            worker_factory: WorkerFactory | None = None,
            verifiers: Mapping[str, Verifier] | None = None,
            capability_gate: CapabilityGate | None = None,
            config: DAGConfig | None = None,
            scheduler_id: str | None = None,
    ):
        self.store = store or SqliteTaskGraphStore()
        self.config = config or DAGConfig()
        self.artifact_store = artifact_store or LocalArtifactStore(
            ".lightagent/artifacts",
            max_artifact_bytes=self.config.max_artifact_bytes,
        )
        self.worker_factory = worker_factory or RegistryWorkerFactory()
        self.verifiers = dict(verifiers or {})
        self.capability_gate = capability_gate or CapabilityGate()
        self.scheduler_id = scheduler_id or uuid4().hex
        self._run_tokens: dict[str, CancellationToken] = {}
        self._verification_semaphore = asyncio.Semaphore(self.config.verification_concurrency)

    def register_worker(self, key: str, worker: Any) -> None:
        register = getattr(self.worker_factory, "register", None)
        if not callable(register):
            raise TypeError("configured WorkerFactory does not support registrations")
        register(key, worker)

    def register_worker_factory(self, key: str, factory: Any) -> None:
        register = getattr(self.worker_factory, "register_factory", None)
        if not callable(register):
            raise TypeError("configured WorkerFactory does not support factory registrations")
        register(key, factory)

    def register_verifier(self, key: str, verifier: Verifier) -> None:
        if not key.strip():
            raise ValueError("verifier key must not be empty")
        self.verifiers[key] = verifier

    def create_run(
            self,
            root_tasks: Iterable[TaskSpec | Mapping[str, Any]],
            *,
            run_id: str | None = None,
            context: SecurityContext,
            root_task_ids: Iterable[str] | None = None,
    ) -> DAGRun:
        tasks = [task if isinstance(task, TaskSpec) else TaskSpec.from_dict(task) for task in root_tasks]
        if not context.tenant_id or not context.project_id:
            raise DAGError("IDENTITY-REQUIRED", "SecurityContext requires tenant_id and project_id")
        resolved_run_id = run_id or context.run_id or uuid4().hex
        if context.run_id not in {None, resolved_run_id}:
            raise ValueError("SecurityContext run_id does not match the requested run")
        run_context = replace(context, run_id=resolved_run_id)
        task_ids = {task.task_id for task in tasks}
        if root_task_ids is None:
            dependency_ids = {dependency for task in tasks for dependency in task.depends_on}
            roots = sorted(task_ids - dependency_ids)
        else:
            roots = list(dict.fromkeys(root_task_ids))
        if not roots:
            raise ValueError("at least one root task is required")
        self._validate_initial_registrations(tasks)
        run = DAGRun(
            run_id=resolved_run_id,
            tenant_id=context.tenant_id,
            project_id=context.project_id,
            root_task_ids=roots,
            status=DAGRunStatus.RUNNING,
            config_digest=canonical_digest(self.config.to_dict()),
            policy_digest=canonical_digest({"policy_version": context.policy_version}),
            security_context=run_context.to_dict(),
        )
        return self.store.create_run(run, tasks, self.config)

    async def arun(
            self,
            run_id: str,
            *,
            context: SecurityContext | None = None,
    ) -> DAGRunResult:
        run = self._require_run(run_id)
        if run.status in {DAGRunStatus.SUCCEEDED, DAGRunStatus.FAILED, DAGRunStatus.CANCELLED}:
            return self._result(run_id)
        if run.status in {DAGRunStatus.PAUSED, DAGRunStatus.BLOCKED}:
            return self._result(run_id)
        if run.config_digest != canonical_digest(self.config.to_dict()):
            raise DAGError(
                "RECOVERY-CONFIG-MISMATCH",
                "the active LightDAG configuration differs from the persisted run",
            )
        self._validate_initial_registrations([
            task.spec for task in self.store.list_tasks(run_id)
            if task.state.status not in {
                DAGTaskStatus.VERIFIED,
                DAGTaskStatus.FAILED,
                DAGTaskStatus.CANCELLED,
                DAGTaskStatus.SUPERSEDED,
            }
        ])
        base_context = self._resolve_context(run, context)
        token = CancellationToken(run_id=run_id)
        self._run_tokens[run_id] = token
        epoch = self.store.acquire_scheduler_lease(
            run_id,
            self.scheduler_id,
            self.config.scheduler_lease_seconds,
        )
        try:
            self.store.expire_attempts(run_id)
            while True:
                run = self._require_run(run_id)
                if token.cancelled and run.status != DAGRunStatus.CANCELLED:
                    self.store.set_run_status(run_id, DAGRunStatus.CANCELLED, token.reason)
                    break
                if run.status != DAGRunStatus.RUNNING:
                    break
                self.store.renew_scheduler_lease(
                    run_id,
                    self.scheduler_id,
                    epoch,
                    self.config.scheduler_lease_seconds,
                )
                claims = []
                for _ in range(self.config.max_concurrency):
                    claim = self.store.claim_ready_task(
                        run_id,
                        worker_id=f"{self.scheduler_id}:{uuid4().hex}",
                        lease_seconds=self.config.task_lease_seconds,
                    )
                    if claim is None:
                        break
                    claims.append(claim)
                if not claims:
                    run = self.store.refresh_run_status(run_id)
                    if run.status == DAGRunStatus.RUNNING:
                        self.store.set_run_status(
                            run_id,
                            DAGRunStatus.BLOCKED,
                            "no runnable tasks; inspect dependencies, leases, and registrations",
                        )
                    break
                await asyncio.gather(*(
                    self._execute_claim(run_id, task, attempt, base_context, token)
                    for task, attempt in claims
                ))
                if self.config.failure_policy == "fail_fast" and any(
                    task.state.status == DAGTaskStatus.FAILED
                    for task in self.store.list_tasks(run_id)
                ):
                    self.store.set_run_status(
                        run_id,
                        DAGRunStatus.FAILED,
                        "fail_fast stopped the run after a task failure",
                    )
                    break
        finally:
            self.store.release_scheduler_lease(run_id, self.scheduler_id, epoch)
            self._run_tokens.pop(run_id, None)
        return self._result(run_id)

    def run(self, run_id: str, *, context: SecurityContext | None = None) -> DAGRunResult:
        from ..capabilities import _run_sync

        return _run_sync(self.arun(run_id, context=context))

    async def resume(
            self,
            run_id: str,
            *,
            context: SecurityContext | None = None,
    ) -> DAGRunResult:
        run = self._require_run(run_id)
        if run.status in {DAGRunStatus.SUCCEEDED, DAGRunStatus.FAILED, DAGRunStatus.CANCELLED}:
            return self._result(run_id)
        self.store.set_run_status(run_id, DAGRunStatus.RUNNING, "resume requested")
        return await self.arun(run_id, context=context)

    def pause(self, run_id: str, reason: str | None = None) -> DAGRun:
        return self.store.set_run_status(run_id, DAGRunStatus.PAUSED, reason or "pause requested")

    def cancel(self, run_id: str, reason: str | None = None) -> DAGRun:
        token = self._run_tokens.get(run_id)
        if token:
            token.cancel(reason or "cancel requested")
        return self.store.set_run_status(run_id, DAGRunStatus.CANCELLED, reason or "cancel requested")

    def resolve_blocker(self, run_id: str, task_id: str, reason: str | None = None) -> DAGTask:
        return self.store.resolve_blocker(run_id, task_id, reason)

    def resolve_approval(self, run_id: str, task_id: str, reason: str | None = None) -> DAGTask:
        return self.resolve_blocker(run_id, task_id, reason or "approval resolved")

    def supersede_task(
            self,
            run_id: str,
            task_id: str,
            replacement: TaskSpec | Mapping[str, Any],
            *,
            expected_graph_revision: int | None = None,
    ) -> DAGTask:
        value = replacement if isinstance(replacement, TaskSpec) else TaskSpec.from_dict(replacement)
        run = self._require_run(run_id)
        return self.store.supersede_task(
            run_id,
            task_id,
            value,
            expected_graph_revision=(
                run.graph_revision if expected_graph_revision is None else expected_graph_revision
            ),
            config=self.config,
        )

    def get_run(self, run_id: str) -> DAGRun | None:
        return self.store.get_run(run_id)

    def list_tasks(self, run_id: str) -> list[DAGTask]:
        return self.store.list_tasks(run_id)

    def get_task(self, run_id: str, task_id: str) -> DAGTask | None:
        return self.store.get_task(run_id, task_id)

    def events(self, run_id: str, *, after: int = 0, limit: int = 100):
        return self.store.events(run_id, after=after, limit=limit)

    async def _execute_claim(self, run_id, task, attempt, base_context, run_token) -> None:
        token = run_token.child(run_id=run_id)
        worker = None
        context = None
        resources = task.spec.resource_requirements or tuple(base_context.resources)
        try:
            attempt = self.store.mark_attempt_running(attempt.attempt_id, attempt.lease_epoch)
            task_context_security = base_context.narrow(
                task_id=task.spec.task_id,
                attempt_id=attempt.attempt_id,
                agent_id=attempt.worker_id,
                resources=resources,
                metadata={"dag_phase": attempt.phase},
            )
            arguments = {
                "run_id": run_id,
                "task_id": task.spec.task_id,
                "attempt_id": attempt.attempt_id,
                "worker_key": task.spec.worker_key,
                "phase": attempt.phase,
            }
            if resources:
                for resource in resources:
                    await self.capability_gate.authorize(
                        self.execution_capability,
                        task.spec.worker_key,
                        arguments,
                        task_context_security,
                        resource=resource,
                    )
            else:
                await self.capability_gate.authorize(
                    self.execution_capability,
                    task.spec.worker_key,
                    arguments,
                    task_context_security,
                )
            dependency_artifacts = {
                dependency_id: tuple(self.store.list_artifacts(run_id, dependency_id))
                for dependency_id in self.store.dependencies(run_id, task.spec.task_id)
            }
            context = TaskContext(
                run=self._require_run(run_id),
                task=task,
                attempt=attempt,
                dependency_artifacts=dependency_artifacts,
                security_context=task_context_security,
                cancellation_token=token,
                last_diagnostic=task.state.last_diagnostic,
            )
            worker = await self.worker_factory.create(task.spec.worker_key, context)
            outcome = await worker.execute(context)
            if token.cancelled:
                raise asyncio.CancelledError
            if outcome.kind == TaskOutcomeKind.BLOCKED:
                self.store.block_attempt(attempt.attempt_id, attempt.lease_epoch, outcome.blocker or "blocked")
                return
            verifier_key = task.spec.decomposer_key if outcome.kind == TaskOutcomeKind.DECOMPOSITION else task.spec.verifier_key
            verifier_key = verifier_key or task.spec.verifier_key
            verifier = self.verifiers.get(verifier_key)
            if verifier is None:
                self.store.block_attempt(
                    attempt.attempt_id,
                    attempt.lease_epoch,
                    f"verifier `{verifier_key}` is not registered",
                )
                return
            if outcome.kind == TaskOutcomeKind.DECOMPOSITION:
                request = VerificationRequest(
                    kind="decomposition",
                    run=context.run,
                    task=task,
                    attempt=attempt,
                    input_snapshot_hash=attempt.input_snapshot_hash,
                    decomposition=outcome.decomposition,
                    dependency_artifacts=dependency_artifacts,
                    security_context=task_context_security,
                )
                async with self._verification_semaphore:
                    report = await verifier.verify(request)
                if report.verdict == VerificationVerdict.PASS:
                    self.store.accept_decomposition(
                        run_id,
                        attempt.attempt_id,
                        attempt.lease_epoch,
                        outcome.decomposition,
                        report,
                        self.config,
                    )
                else:
                    self.store.reject_candidate(
                        attempt.attempt_id,
                        attempt.lease_epoch,
                        report,
                        self.config.max_attempts_per_task,
                    )
                return
            content = self._candidate_bytes(outcome.content)
            manifest = self.artifact_store.stage(
                content,
                run=context.run,
                task=task,
                attempt=attempt,
                media_type=outcome.media_type,
                dependency_manifest={
                    key: [artifact.artifact_id for artifact in values]
                    for key, values in dependency_artifacts.items()
                },
            )
            manifest.metadata.update(deepcopy(dict(outcome.metadata)))
            manifest = self.store.save_staged_artifact(manifest, attempt.lease_epoch)
            if not self.artifact_store.check_integrity(manifest):
                raise DAGError("ARTIFACT-INTEGRITY", "staged artifact failed integrity verification")
            request = VerificationRequest(
                kind="completion",
                run=context.run,
                task=task,
                attempt=attempt,
                input_snapshot_hash=attempt.input_snapshot_hash,
                candidate=manifest,
                candidate_content=content,
                dependency_artifacts=dependency_artifacts,
                security_context=task_context_security,
            )
            async with self._verification_semaphore:
                report = await verifier.verify(request)
            if report.verdict == VerificationVerdict.PASS:
                self.store.publish_artifact(manifest, report, attempt.lease_epoch)
            else:
                self.store.reject_candidate(
                    attempt.attempt_id,
                    attempt.lease_epoch,
                    report,
                    self.config.max_attempts_per_task,
                )
        except asyncio.CancelledError:
            current = self.store.get_attempt(attempt.attempt_id)
            if current and current.status.value not in {"expired", "cancelled", "failed"}:
                try:
                    self.store.block_attempt(attempt.attempt_id, attempt.lease_epoch, token.reason or "cancelled")
                except DAGError:
                    pass
            raise
        except Exception as error:
            reason = f"task attempt failed: {type(error).__name__}"
            try:
                self.store.fail_attempt(
                    attempt.attempt_id,
                    attempt.lease_epoch,
                    reason,
                    self.config.max_attempts_per_task,
                )
            except (DAGError, KeyError):
                pass
        finally:
            if worker is not None and context is not None:
                try:
                    await self.worker_factory.release(worker, context)
                except Exception:
                    pass

    def _validate_initial_registrations(self, tasks: list[TaskSpec]) -> None:
        registrations = getattr(self.worker_factory, "registrations", None)
        if registrations is not None:
            missing_workers = sorted({task.worker_key for task in tasks if task.worker_key not in registrations})
            if missing_workers:
                raise DAGError("RECOVERY-CONFIG-MISMATCH", f"unregistered workers: {missing_workers}")
        missing_verifiers = sorted({
            key
            for task in tasks
            for key in (task.verifier_key, task.decomposer_key)
            if key and key not in self.verifiers
        })
        if missing_verifiers:
            raise DAGError("VERIFIER-UNAVAILABLE", f"unregistered verifiers: {missing_verifiers}")

    @staticmethod
    def _candidate_bytes(content: Any) -> bytes:
        if isinstance(content, bytes):
            return content
        if isinstance(content, str):
            return content.encode("utf-8")
        return json.dumps(content, ensure_ascii=False, sort_keys=True, default=repr).encode("utf-8")

    def _resolve_context(self, run: DAGRun, context: SecurityContext | None) -> SecurityContext:
        stored = SecurityContext.from_dict(run.security_context)
        value = context or stored
        if value.tenant_id != run.tenant_id or value.project_id != run.project_id:
            raise PermissionError("SecurityContext does not match the DAG tenant/project")
        if value.run_id not in {None, run.run_id}:
            raise PermissionError("SecurityContext does not match the DAG run")
        return replace(value, run_id=run.run_id)

    def _require_run(self, run_id: str) -> DAGRun:
        run = self.store.get_run(run_id)
        if run is None:
            raise KeyError(run_id)
        return run

    def _result(self, run_id: str) -> DAGRunResult:
        run = self._require_run(run_id)
        tasks = self.store.list_tasks(run_id)
        events = self.store.events(run_id, after=0, limit=1_000_000)
        root_artifacts = {
            task_id: self.store.list_artifacts(run_id, task_id)
            for task_id in run.root_task_ids
        }
        for artifacts in root_artifacts.values():
            for manifest in artifacts:
                if not self.artifact_store.check_integrity(manifest):
                    raise DAGError(
                        "ARTIFACT-INTEGRITY",
                        f"published artifact `{manifest.artifact_id}` failed integrity verification",
                    )
        return DAGRunResult(
            run_id=run_id,
            status=run.status,
            root_artifacts=root_artifacts,
            failed_tasks=[
                task.spec.task_id
                for task in tasks
                if task.state.status == DAGTaskStatus.FAILED
            ],
            blockers={
                task.spec.task_id: task.state.blocker or task.state.last_diagnostic or "blocked"
                for task in tasks
                if task.state.status in {DAGTaskStatus.BLOCKED, DAGTaskStatus.WAITING_APPROVAL}
            },
            event_cursor=events[-1].sequence if events else 0,
        )


__all__ = ["LightDAG"]
