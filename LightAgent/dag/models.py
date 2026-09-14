"""Versioned public data contracts for the experimental LightDAG runtime."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping
from uuid import uuid4

from ..security import SecurityContext, canonical_digest


DAG_SCHEMA_VERSION = 1


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class DAGRunStatus(str, Enum):
    RUNNING = "running"
    PAUSED = "paused"
    BLOCKED = "blocked"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DAGTaskStatus(str, Enum):
    READY = "ready"
    RUNNING = "running"
    VERIFYING = "verifying"
    WAITING_DEPENDENCIES = "waiting_dependencies"
    RETRY_WAIT = "retry_wait"
    WAITING_APPROVAL = "waiting_approval"
    BLOCKED = "blocked"
    VERIFIED = "verified"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SUPERSEDED = "superseded"


class DAGAttemptStatus(str, Enum):
    CLAIMED = "claimed"
    RUNNING = "running"
    SUBMITTED = "submitted"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class VerificationVerdict(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    INCONCLUSIVE = "inconclusive"
    ERROR = "error"


class AssuranceLevel(str, Enum):
    FORMAL = "formal"
    EXECUTABLE_CHECKS = "executable_checks"
    HUMAN_REVIEW = "human_review"


class TaskOutcomeKind(str, Enum):
    CANDIDATE = "candidate"
    DECOMPOSITION = "decomposition"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class DAGConfig:
    max_tasks: int = 1000
    max_edges: int = 3000
    max_decomposition_depth: int = 8
    max_attempts_per_task: int = 3
    max_decompositions_per_task: int = 1
    max_concurrency: int = 4
    verification_concurrency: int = 4
    max_pending_verifications: int = 16
    max_artifact_bytes: int = 10 * 1024 * 1024
    scheduler_lease_seconds: float = 60.0
    task_lease_seconds: float = 60.0
    failure_policy: str = "continue_independent"
    schema_version: int = DAG_SCHEMA_VERSION

    def __post_init__(self) -> None:
        positive = (
            "max_tasks",
            "max_edges",
            "max_decomposition_depth",
            "max_attempts_per_task",
            "max_decompositions_per_task",
            "max_concurrency",
            "verification_concurrency",
            "max_pending_verifications",
            "max_artifact_bytes",
            "scheduler_lease_seconds",
            "task_lease_seconds",
        )
        for name in positive:
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive")
        if self.failure_policy not in {"continue_independent", "fail_fast"}:
            raise ValueError("failure_policy must be continue_independent or fail_fast")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TaskSpec:
    goal: str
    acceptance_contract: Any
    worker_key: str
    verifier_key: str
    task_id: str = field(default_factory=lambda: uuid4().hex)
    decomposer_key: str | None = None
    depends_on: tuple[str, ...] = field(default_factory=tuple)
    resource_requirements: tuple[str, ...] = field(default_factory=tuple)
    created_by_task_id: str | None = None
    supersedes_task_id: str | None = None
    priority: int = 0
    metadata: Mapping[str, Any] = field(default_factory=dict)
    contract_hash: str = ""
    schema_version: int = DAG_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.goal.strip():
            raise ValueError("TaskSpec.goal must not be empty")
        if not self.worker_key.strip() or not self.verifier_key.strip():
            raise ValueError("TaskSpec worker_key and verifier_key must not be empty")
        if self.task_id in self.depends_on:
            raise ValueError("a task cannot depend on itself")
        object.__setattr__(self, "depends_on", tuple(dict.fromkeys(self.depends_on)))
        object.__setattr__(self, "resource_requirements", tuple(dict.fromkeys(self.resource_requirements)))
        object.__setattr__(self, "metadata", deepcopy(dict(self.metadata)))
        expected_contract_hash = canonical_digest(self.acceptance_contract)
        if self.contract_hash and self.contract_hash != expected_contract_hash:
            raise ValueError("TaskSpec.contract_hash does not match acceptance_contract")
        object.__setattr__(self, "contract_hash", expected_contract_hash)

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "depends_on": list(self.depends_on),
            "resource_requirements": list(self.resource_requirements),
            "metadata": deepcopy(dict(self.metadata)),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "TaskSpec":
        payload = dict(value)
        payload["depends_on"] = tuple(payload.get("depends_on") or ())
        payload["resource_requirements"] = tuple(payload.get("resource_requirements") or ())
        return cls(**payload)


@dataclass
class TaskState:
    task_id: str
    status: DAGTaskStatus = DAGTaskStatus.READY
    state_version: int = 0
    dependency_revision: int = 0
    attempt_count: int = 0
    decomposition_count: int = 0
    verification_failure_count: int = 0
    next_eligible_at: str | None = None
    blocker: str | None = None
    active_attempt_id: str | None = None
    verified_artifact_ids: list[str] = field(default_factory=list)
    last_diagnostic: str | None = None
    updated_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        return value

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "TaskState":
        payload = dict(value)
        payload["status"] = DAGTaskStatus(payload.get("status", DAGTaskStatus.READY.value))
        return cls(**payload)


@dataclass
class DAGTask:
    spec: TaskSpec
    state: TaskState
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {"spec": self.spec.to_dict(), "state": self.state.to_dict(), "created_at": self.created_at}


@dataclass
class DAGRun:
    tenant_id: str
    project_id: str
    root_task_ids: list[str]
    run_id: str = field(default_factory=lambda: uuid4().hex)
    status: DAGRunStatus = DAGRunStatus.RUNNING
    graph_revision: int = 0
    scheduler_epoch: int = 0
    config_digest: str = ""
    policy_digest: str = ""
    budget_limits: dict[str, Any] = field(default_factory=dict)
    security_context: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    schema_version: int = DAG_SCHEMA_VERSION
    blocker: str | None = None

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        return value

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "DAGRun":
        payload = dict(value)
        payload["status"] = DAGRunStatus(payload.get("status", DAGRunStatus.RUNNING.value))
        return cls(**payload)


@dataclass(frozen=True)
class TaskDependency:
    run_id: str
    task_id: str
    dependency_id: str
    decomposition_id: str = "initial"


@dataclass
class TaskAttempt:
    run_id: str
    task_id: str
    attempt_no: int
    worker_id: str
    input_snapshot_hash: str
    attempt_id: str = field(default_factory=lambda: uuid4().hex)
    phase: str = "solve"
    session_id: str | None = None
    workspace_ref: str | None = None
    lease_epoch: int = 1
    lease_expires_at: str | None = None
    status: DAGAttemptStatus = DAGAttemptStatus.CLAIMED
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        return value

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "TaskAttempt":
        payload = dict(value)
        payload["status"] = DAGAttemptStatus(payload.get("status", DAGAttemptStatus.CLAIMED.value))
        return cls(**payload)


@dataclass(frozen=True)
class DecompositionProposal:
    parent_task_id: str
    new_tasks: tuple[TaskSpec, ...]
    reuse_task_ids: tuple[str, ...] = field(default_factory=tuple)
    rationale: str = ""
    composition_contract: Any = None
    expected_graph_revision: int = 0
    proposal_id: str = field(default_factory=lambda: uuid4().hex)
    verification_report_id: str | None = None
    schema_version: int = DAG_SCHEMA_VERSION

    def __post_init__(self) -> None:
        normalized_tasks = []
        for task in self.new_tasks:
            if task.created_by_task_id not in {None, self.parent_task_id}:
                raise ValueError("decomposition task has a different created_by_task_id")
            normalized_tasks.append(
                task
                if task.created_by_task_id == self.parent_task_id
                else replace(task, created_by_task_id=self.parent_task_id)
            )
        object.__setattr__(self, "new_tasks", tuple(normalized_tasks))
        object.__setattr__(self, "reuse_task_ids", tuple(dict.fromkeys(self.reuse_task_ids)))

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "parent_task_id": self.parent_task_id,
            "new_tasks": [task.to_dict() for task in self.new_tasks],
            "reuse_task_ids": list(self.reuse_task_ids),
            "rationale": self.rationale,
            "composition_contract": deepcopy(self.composition_contract),
            "expected_graph_revision": self.expected_graph_revision,
            "proposal_id": self.proposal_id,
            "verification_report_id": self.verification_report_id,
            "schema_version": self.schema_version,
        }


@dataclass
class ArtifactManifest:
    run_id: str
    task_id: str
    attempt_id: str
    tenant_id: str
    project_id: str
    content_hash: str
    relative_blob_path: str
    media_type: str
    byte_size: int
    contract_hash: str
    dependency_manifest: dict[str, list[str]] = field(default_factory=dict)
    artifact_id: str = field(default_factory=lambda: uuid4().hex)
    verification_report_id: str | None = None
    state: str = "staged"
    created_at: str = field(default_factory=utc_now)
    schema_version: int = DAG_SCHEMA_VERSION
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ArtifactManifest":
        return cls(**dict(value))


@dataclass
class VerificationReport:
    kind: str
    verdict: VerificationVerdict
    assurance_level: AssuranceLevel
    verifier_key: str
    verifier_version: str
    config_digest: str
    input_snapshot_hash: str
    artifact_hashes: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    diagnostics: list[str] = field(default_factory=list)
    report_id: str = field(default_factory=lambda: uuid4().hex)
    created_at: str = field(default_factory=utc_now)
    schema_version: int = DAG_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["verdict"] = self.verdict.value
        value["assurance_level"] = self.assurance_level.value
        return value

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "VerificationReport":
        payload = dict(value)
        payload["verdict"] = VerificationVerdict(payload["verdict"])
        payload["assurance_level"] = AssuranceLevel(payload["assurance_level"])
        return cls(**payload)


@dataclass
class DAGEvent:
    run_id: str
    sequence: int
    type: str
    event_id: str = field(default_factory=lambda: uuid4().hex)
    task_id: str | None = None
    attempt_id: str | None = None
    data: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now)
    schema_version: int = DAG_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TaskContext:
    run: DAGRun
    task: DAGTask
    attempt: TaskAttempt
    dependency_artifacts: Mapping[str, tuple[ArtifactManifest, ...]]
    security_context: SecurityContext
    cancellation_token: Any
    last_diagnostic: str | None = None


@dataclass(frozen=True)
class TaskOutcome:
    kind: TaskOutcomeKind
    content: Any = None
    media_type: str = "text/plain"
    decomposition: DecompositionProposal | None = None
    blocker: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.kind == TaskOutcomeKind.CANDIDATE and self.decomposition is not None:
            raise ValueError("candidate outcome cannot include a decomposition")
        if self.kind == TaskOutcomeKind.DECOMPOSITION and self.decomposition is None:
            raise ValueError("decomposition outcome requires a proposal")
        if self.kind == TaskOutcomeKind.BLOCKED and not self.blocker:
            raise ValueError("blocked outcome requires a reason")

    @classmethod
    def candidate(cls, content: Any, *, media_type: str = "text/plain", **metadata: Any) -> "TaskOutcome":
        return cls(TaskOutcomeKind.CANDIDATE, content=content, media_type=media_type, metadata=metadata)

    @classmethod
    def decompose(cls, proposal: DecompositionProposal, **metadata: Any) -> "TaskOutcome":
        return cls(TaskOutcomeKind.DECOMPOSITION, decomposition=proposal, metadata=metadata)

    @classmethod
    def blocked(cls, reason: str, **metadata: Any) -> "TaskOutcome":
        return cls(TaskOutcomeKind.BLOCKED, blocker=reason, metadata=metadata)


@dataclass(frozen=True)
class VerificationRequest:
    kind: str
    run: DAGRun
    task: DAGTask
    attempt: TaskAttempt
    input_snapshot_hash: str
    candidate: ArtifactManifest | None = None
    candidate_content: bytes | None = None
    decomposition: DecompositionProposal | None = None
    dependency_artifacts: Mapping[str, tuple[ArtifactManifest, ...]] = field(default_factory=dict)
    security_context: SecurityContext | None = None


@dataclass
class DAGRunResult:
    run_id: str
    status: DAGRunStatus
    root_artifacts: dict[str, list[ArtifactManifest]] = field(default_factory=dict)
    failed_tasks: list[str] = field(default_factory=list)
    blockers: dict[str, str] = field(default_factory=dict)
    pending_approvals: list[str] = field(default_factory=list)
    usage: dict[str, Any] = field(default_factory=dict)
    event_cursor: int = 0

    @property
    def success(self) -> bool:
        return self.status == DAGRunStatus.SUCCEEDED

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "status": self.status.value,
            "root_artifacts": {
                task_id: [artifact.to_dict() for artifact in artifacts]
                for task_id, artifacts in self.root_artifacts.items()
            },
            "failed_tasks": list(self.failed_tasks),
            "blockers": dict(self.blockers),
            "pending_approvals": list(self.pending_approvals),
            "usage": deepcopy(self.usage),
            "event_cursor": self.event_cursor,
            "success": self.success,
        }


__all__ = [
    "DAG_SCHEMA_VERSION",
    "DAGRunStatus",
    "DAGTaskStatus",
    "DAGAttemptStatus",
    "VerificationVerdict",
    "AssuranceLevel",
    "TaskOutcomeKind",
    "DAGConfig",
    "TaskSpec",
    "TaskState",
    "DAGTask",
    "DAGRun",
    "TaskDependency",
    "TaskAttempt",
    "DecompositionProposal",
    "ArtifactManifest",
    "VerificationReport",
    "DAGEvent",
    "TaskContext",
    "TaskOutcome",
    "VerificationRequest",
    "DAGRunResult",
    "utc_now",
]
