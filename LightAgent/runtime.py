"""Long-task runtime controls built on the Session event log."""

from __future__ import annotations

import asyncio
import inspect
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Awaitable, Callable, Iterable
from uuid import uuid4

from .capabilities import CapabilityRegistry, PermissionSet, RuntimeContext
from .session import InMemorySessionStore, Session, SessionCheckpoint, SessionStore, _utc_now


class InboxMessageType(str, Enum):
    FOLLOWUP = "followup"
    STEERING = "steering"
    CONTEXT = "context"
    APPROVAL = "approval"


class InboxMessageStatus(str, Enum):
    PENDING = "pending"
    CLAIMED = "claimed"
    COMPLETED = "completed"
    REJECTED = "rejected"


@dataclass
class InboxMessage:
    type: InboxMessageType
    content: Any
    message_id: str = field(default_factory=lambda: uuid4().hex)
    status: InboxMessageStatus = InboxMessageStatus.PENDING
    created_at: str = field(default_factory=_utc_now)
    claimed_at: str | None = None
    completed_at: str | None = None
    correlation_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["type"] = self.type.value
        value["status"] = self.status.value
        return value

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "InboxMessage":
        return cls(
            message_id=str(value.get("message_id") or uuid4().hex),
            type=InboxMessageType(value["type"]),
            content=deepcopy(value.get("content")),
            status=InboxMessageStatus(value.get("status", "pending")),
            created_at=str(value.get("created_at") or _utc_now()),
            claimed_at=value.get("claimed_at"),
            completed_at=value.get("completed_at"),
            correlation_id=value.get("correlation_id"),
            metadata=dict(value.get("metadata") or {}),
        )


class AgentInbox:
    """Ordered, idempotent Inbox whose mutations are Session events."""

    def __init__(self, event_sink: Callable[[str, dict[str, Any]], Any] | None = None):
        self._messages: list[InboxMessage] = []
        self._event_sink = event_sink

    def enqueue(
            self,
            message_type: InboxMessageType | str,
            content: Any,
            *,
            message_id: str | None = None,
            correlation_id: str | None = None,
            metadata: dict[str, Any] | None = None,
    ) -> InboxMessage:
        resolved_id = message_id or uuid4().hex
        existing = self.get(resolved_id)
        if existing is not None:
            return existing
        message = InboxMessage(
            message_id=resolved_id,
            type=InboxMessageType(message_type),
            content=deepcopy(content),
            correlation_id=correlation_id,
            metadata=deepcopy(metadata or {}),
        )
        self._messages.append(message)
        self._emit("inbox.enqueued", {"message": message.to_dict()})
        return deepcopy(message)

    def pending(self, message_type: InboxMessageType | str | None = None) -> list[InboxMessage]:
        resolved_type = InboxMessageType(message_type) if message_type is not None else None
        return deepcopy([
            message for message in self._messages
            if message.status == InboxMessageStatus.PENDING
            and (resolved_type is None or message.type == resolved_type)
        ])

    def claim_next(self, *, safe_boundary: bool = True) -> InboxMessage | None:
        for message in self._messages:
            if message.status != InboxMessageStatus.PENDING:
                continue
            if message.type == InboxMessageType.STEERING and not safe_boundary:
                continue
            message.status = InboxMessageStatus.CLAIMED
            message.claimed_at = _utc_now()
            self._emit("inbox.claimed", {"message": message.to_dict()})
            return deepcopy(message)
        return None

    def complete(self, message_id: str, *, result: Any = None) -> InboxMessage:
        message = self._require(message_id)
        if message.status == InboxMessageStatus.COMPLETED:
            return deepcopy(message)
        if message.status != InboxMessageStatus.CLAIMED:
            raise ValueError("only claimed Inbox messages can be completed")
        message.status = InboxMessageStatus.COMPLETED
        message.completed_at = _utc_now()
        self._emit("inbox.completed", {"message": message.to_dict(), "result": deepcopy(result)})
        return deepcopy(message)

    def reject(self, message_id: str, reason: str) -> InboxMessage:
        message = self._require(message_id)
        message.status = InboxMessageStatus.REJECTED
        message.completed_at = _utc_now()
        self._emit("inbox.rejected", {"message": message.to_dict(), "reason": reason})
        return deepcopy(message)

    def get(self, message_id: str) -> InboxMessage | None:
        message = next((item for item in self._messages if item.message_id == message_id), None)
        return deepcopy(message) if message else None

    def list(self) -> list[InboxMessage]:
        return deepcopy(self._messages)

    def restore(self, session: Session) -> None:
        self._messages = []
        by_id: dict[str, InboxMessage] = {}
        for event in session.events:
            if not event.type.startswith("inbox."):
                continue
            value = event.data.get("message")
            if not isinstance(value, dict):
                continue
            message = InboxMessage.from_dict(value)
            by_id[message.message_id] = message
        self._messages = sorted(by_id.values(), key=lambda item: item.created_at)

    def _require(self, message_id: str) -> InboxMessage:
        message = next((item for item in self._messages if item.message_id == message_id), None)
        if message is None:
            raise KeyError(message_id)
        return message

    def _emit(self, event_type: str, data: dict[str, Any]) -> None:
        if self._event_sink:
            self._event_sink(event_type, data)


class GoalStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


@dataclass
class Goal:
    objective: str
    goal_id: str = field(default_factory=lambda: uuid4().hex)
    status: GoalStatus = GoalStatus.PENDING
    acceptance_criteria: list[str] = field(default_factory=list)
    parent_goal_id: str | None = None
    evidence: list[Any] = field(default_factory=list)
    blocker: str | None = None
    created_at: str = field(default_factory=_utc_now)
    updated_at: str = field(default_factory=_utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        return value

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Goal":
        return cls(
            goal_id=str(value.get("goal_id") or uuid4().hex),
            objective=str(value["objective"]),
            status=GoalStatus(value.get("status", "pending")),
            acceptance_criteria=list(value.get("acceptance_criteria") or []),
            parent_goal_id=value.get("parent_goal_id"),
            evidence=deepcopy(value.get("evidence") or []),
            blocker=value.get("blocker"),
            created_at=str(value.get("created_at") or _utc_now()),
            updated_at=str(value.get("updated_at") or _utc_now()),
            metadata=dict(value.get("metadata") or {}),
        )


class GoalManager:
    def __init__(self, event_sink: Callable[[str, dict[str, Any]], Any] | None = None):
        self._goals: dict[str, Goal] = {}
        self._event_sink = event_sink

    def create(
            self,
            objective: str,
            *,
            acceptance_criteria: Iterable[str] | None = None,
            parent_goal_id: str | None = None,
            metadata: dict[str, Any] | None = None,
    ) -> Goal:
        if not objective.strip():
            raise ValueError("goal objective must not be empty")
        if parent_goal_id and parent_goal_id not in self._goals:
            raise KeyError(parent_goal_id)
        goal = Goal(
            objective=objective,
            acceptance_criteria=list(acceptance_criteria or []),
            parent_goal_id=parent_goal_id,
            metadata=deepcopy(metadata or {}),
        )
        self._goals[goal.goal_id] = goal
        self._emit("goal.created", goal)
        return deepcopy(goal)

    def activate(self, goal_id: str) -> Goal:
        return self._transition(goal_id, GoalStatus.ACTIVE)

    def complete(self, goal_id: str, *, evidence: Iterable[Any] | None = None) -> Goal:
        goal = self._require(goal_id)
        goal.evidence.extend(deepcopy(list(evidence or [])))
        goal.blocker = None
        return self._transition(goal_id, GoalStatus.COMPLETED, event_type="goal.completed")

    def block(self, goal_id: str, reason: str) -> Goal:
        goal = self._require(goal_id)
        goal.blocker = reason
        return self._transition(goal_id, GoalStatus.BLOCKED, event_type="goal.blocked")

    def cancel(self, goal_id: str, reason: str | None = None) -> Goal:
        goal = self._require(goal_id)
        goal.blocker = reason
        return self._transition(goal_id, GoalStatus.CANCELLED, event_type="goal.cancelled")

    def get(self, goal_id: str) -> Goal:
        return deepcopy(self._require(goal_id))

    def list(self, *, status: GoalStatus | str | None = None) -> list[Goal]:
        resolved = GoalStatus(status) if status is not None else None
        return deepcopy([goal for goal in self._goals.values() if resolved is None or goal.status == resolved])

    def restore(self, session: Session) -> None:
        by_id: dict[str, Goal] = {}
        for event in session.events:
            if not event.type.startswith("goal."):
                continue
            value = event.data.get("goal")
            if isinstance(value, dict):
                goal = Goal.from_dict(value)
                by_id[goal.goal_id] = goal
        self._goals = by_id

    def _transition(self, goal_id: str, status: GoalStatus, event_type: str = "goal.updated") -> Goal:
        goal = self._require(goal_id)
        if goal.status in {GoalStatus.COMPLETED, GoalStatus.CANCELLED} and goal.status != status:
            raise ValueError(f"terminal goal `{goal_id}` cannot transition from {goal.status.value}")
        goal.status = status
        goal.updated_at = _utc_now()
        self._emit(event_type, goal)
        return deepcopy(goal)

    def _require(self, goal_id: str) -> Goal:
        if goal_id not in self._goals:
            raise KeyError(goal_id)
        return self._goals[goal_id]

    def _emit(self, event_type: str, goal: Goal) -> None:
        if self._event_sink:
            self._event_sink(event_type, {"goal": goal.to_dict()})


@dataclass(frozen=True)
class BudgetLimits:
    model_calls: int | None = None
    tool_calls: int | None = None
    tokens: int | None = None
    seconds: float | None = None
    cost: float | None = None

    def __post_init__(self) -> None:
        for name, value in asdict(self).items():
            if value is not None and value < 0:
                raise ValueError(f"budget limit `{name}` must be non-negative")


@dataclass
class BudgetUsage:
    model_calls: int = 0
    tool_calls: int = 0
    tokens: int = 0
    seconds: float = 0.0
    cost: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class BudgetExceeded(RuntimeError):
    def __init__(self, dimension: str, limit: float, used: float):
        super().__init__(f"budget exceeded for {dimension}: used={used}, limit={limit}")
        self.dimension = dimension
        self.limit = limit
        self.used = used


class BudgetManager:
    def __init__(
            self,
            limits: BudgetLimits | None = None,
            event_sink: Callable[[str, dict[str, Any]], Any] | None = None,
    ):
        self.limits = limits or BudgetLimits()
        self.usage = BudgetUsage()
        self._event_sink = event_sink

    def consume(
            self,
            *,
            model_calls: int = 0,
            tool_calls: int = 0,
            tokens: int = 0,
            seconds: float = 0.0,
            cost: float = 0.0,
    ) -> BudgetUsage:
        candidate = BudgetUsage(
            model_calls=self.usage.model_calls + model_calls,
            tool_calls=self.usage.tool_calls + tool_calls,
            tokens=self.usage.tokens + tokens,
            seconds=self.usage.seconds + seconds,
            cost=self.usage.cost + cost,
        )
        for dimension, limit in asdict(self.limits).items():
            used = getattr(candidate, dimension)
            if limit is not None and used > limit:
                if self._event_sink:
                    self._event_sink("budget.exhausted", {
                        "dimension": dimension,
                        "limit": limit,
                        "used": used,
                    })
                raise BudgetExceeded(dimension, limit, used)
        self.usage = candidate
        if self._event_sink:
            self._event_sink("budget.consumed", {"usage": self.usage.to_dict()})
        return deepcopy(self.usage)

    def remaining(self) -> dict[str, float | int | None]:
        return {
            dimension: None if limit is None else max(0, limit - getattr(self.usage, dimension))
            for dimension, limit in asdict(self.limits).items()
        }

    def restore(self, session: Session) -> None:
        for event in reversed(session.events):
            if event.type == "budget.consumed" and isinstance(event.data.get("usage"), dict):
                self.usage = BudgetUsage(**event.data["usage"])
                return
        self.usage = BudgetUsage()


@dataclass
class ProgressState:
    steps: int = 0
    unchanged_steps: int = 0
    repeated_tool_calls: int = 0
    last_output: str | None = None
    last_tool_signature: str | None = None


class ProgressTracker:
    """Detect bounded no-progress and repeated-tool loops."""

    def __init__(
            self,
            *,
            max_unchanged_steps: int = 3,
            max_repeated_tool_calls: int = 3,
            event_sink: Callable[[str, dict[str, Any]], Any] | None = None,
    ):
        self.max_unchanged_steps = max_unchanged_steps
        self.max_repeated_tool_calls = max_repeated_tool_calls
        self.state = ProgressState()
        self._event_sink = event_sink

    def record(self, *, output: Any = None, tool: str | None = None, arguments: Any = None) -> ProgressState:
        rendered = repr(output)
        signature = repr((tool, arguments)) if tool else None
        self.state.steps += 1
        self.state.unchanged_steps = self.state.unchanged_steps + 1 if rendered == self.state.last_output else 0
        self.state.repeated_tool_calls = (
            self.state.repeated_tool_calls + 1
            if signature is not None and signature == self.state.last_tool_signature
            else 0
        )
        self.state.last_output = rendered
        self.state.last_tool_signature = signature
        if self.state.unchanged_steps >= self.max_unchanged_steps:
            self._emit("progress.stalled", "unchanged_output")
        if self.state.repeated_tool_calls >= self.max_repeated_tool_calls:
            self._emit("progress.stalled", "repeated_tool_call")
        return deepcopy(self.state)

    @property
    def stalled(self) -> bool:
        return (
            self.state.unchanged_steps >= self.max_unchanged_steps
            or self.state.repeated_tool_calls >= self.max_repeated_tool_calls
        )

    def _emit(self, event_type: str, reason: str) -> None:
        if self._event_sink:
            self._event_sink(event_type, {"reason": reason, "state": asdict(self.state)})


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
    metadata: dict[str, Any] = field(default_factory=dict)
    output: list[Any] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        return value


class JobManager:
    """Manage cancellable background coroutines and persist their state."""

    def __init__(
            self,
            event_sink: Callable[[str, dict[str, Any]], Any] | None = None,
            inbox: AgentInbox | None = None,
    ):
        self._records: dict[str, JobRecord] = {}
        self._tasks: dict[str, asyncio.Task[Any]] = {}
        self._event_sink = event_sink
        self._inbox = inbox

    def start(
            self,
            name: str,
            operation: Callable[[], Any] | Awaitable[Any],
            *,
            owner_agent_id: str | None = None,
            metadata: dict[str, Any] | None = None,
    ) -> JobRecord:
        loop = asyncio.get_running_loop()
        record = JobRecord(name=name, owner_agent_id=owner_agent_id, metadata=deepcopy(metadata or {}))
        self._records[record.job_id] = record
        self._emit("job.created", record)
        self._tasks[record.job_id] = loop.create_task(self._execute(record.job_id, operation))
        return deepcopy(record)

    async def _execute(self, job_id: str, operation: Callable[[], Any] | Awaitable[Any]) -> None:
        record = self._records[job_id]
        record.status = JobStatus.RUNNING
        record.started_at = _utc_now()
        self._emit("job.started", record)
        try:
            value = operation() if callable(operation) else operation
            if inspect.isawaitable(value):
                value = await value
            record.result = value
            record.status = JobStatus.SUCCESS
            record.completed_at = _utc_now()
            self._emit("job.completed", record)
        except asyncio.CancelledError:
            record.status = JobStatus.CANCELLED
            record.error = "cancelled"
            record.completed_at = _utc_now()
            self._emit("job.cancelled", record)
            raise
        except Exception as error:
            record.status = JobStatus.FAILED
            record.error = f"{type(error).__name__}: {error}"
            record.completed_at = _utc_now()
            self._emit("job.failed", record)
        finally:
            if record.completed_at is None:
                record.completed_at = _utc_now()
            if self._inbox:
                self._inbox.enqueue(
                    InboxMessageType.CONTEXT,
                    {"job": record.to_dict()},
                    correlation_id=record.job_id,
                    metadata={"kind": "job_completion"},
                )

    async def wait(self, job_id: str) -> JobRecord:
        if job_id not in self._records:
            raise KeyError(job_id)
        task = self._tasks.get(job_id)
        if task is not None:
            try:
                await task
            except asyncio.CancelledError:
                pass
        return deepcopy(self._records[job_id])

    def cancel(self, job_id: str) -> bool:
        task = self._tasks.get(job_id)
        if task is None or task.done():
            return False
        return task.cancel()

    def emit_output(self, job_id: str, value: Any) -> JobRecord:
        record = self._records.get(job_id)
        if record is None:
            raise KeyError(job_id)
        record.output.append(deepcopy(value))
        self._emit("job.output", record)
        return deepcopy(record)

    def get(self, job_id: str) -> JobRecord:
        if job_id not in self._records:
            raise KeyError(job_id)
        return deepcopy(self._records[job_id])

    def list(self) -> list[JobRecord]:
        return deepcopy(list(self._records.values()))

    def mark_interrupted(self) -> None:
        for record in self._records.values():
            if record.status in {JobStatus.PENDING, JobStatus.RUNNING}:
                record.status = JobStatus.INTERRUPTED
                record.completed_at = _utc_now()
                self._emit("job.interrupted", record)

    def restore(self, session: Session) -> None:
        records: dict[str, JobRecord] = {}
        for event in session.events:
            if not event.type.startswith("job."):
                continue
            value = event.data.get("job")
            if not isinstance(value, dict):
                continue
            payload = dict(value)
            payload["status"] = JobStatus(payload.get("status", "pending"))
            record = JobRecord(**payload)
            records[record.job_id] = record
        self._records = records
        self._tasks = {}

    def _emit(self, event_type: str, record: JobRecord) -> None:
        if self._event_sink:
            self._event_sink(event_type, {"job": record.to_dict()})


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


class SubagentManager:
    def __init__(
            self,
            *,
            max_depth: int = 2,
            max_agents: int = 8,
            max_concurrency: int = 4,
            event_sink: Callable[[str, dict[str, Any]], Any] | None = None,
    ):
        self.max_depth = max_depth
        self.max_agents = max_agents
        self.max_concurrency = max_concurrency
        self._event_sink = event_sink
        self._agents: dict[str, tuple[Any, SubagentRecord]] = {}
        self._running = 0

    def register(
            self,
            agent: Any,
            *,
            parent_agent_id: str | None = None,
            parent_permissions: PermissionSet | None = None,
            allowed_capabilities: Iterable[str] | None = None,
            max_risk: Any = None,
            persistent: bool = False,
            metadata: dict[str, Any] | None = None,
    ) -> SubagentRecord:
        if len(self._agents) >= self.max_agents:
            raise RuntimeError("subagent limit reached")
        parent_record = self._agents.get(parent_agent_id, (None, None))[1] if parent_agent_id else None
        depth = parent_record.depth + 1 if parent_record else 1
        if depth > self.max_depth:
            raise RuntimeError("subagent depth limit reached")
        base_permissions = parent_permissions or (parent_record.permissions if parent_record else PermissionSet())
        permissions = base_permissions.narrow(
            allowed=allowed_capabilities,
            max_risk=max_risk,
        )
        agent_id = uuid4().hex
        record = SubagentRecord(
            agent_id=agent_id,
            name=str(getattr(agent, "name", agent_id)),
            parent_agent_id=parent_agent_id,
            depth=depth,
            permissions=permissions,
            persistent=persistent,
            metadata=deepcopy(metadata or {}),
        )
        self._agents[agent_id] = (agent, record)
        self._emit("subagent.created", record)
        return deepcopy(record)

    async def run(self, agent_id: str, query: str, **kwargs: Any) -> Any:
        if agent_id not in self._agents:
            raise KeyError(agent_id)
        agent, record = self._agents[agent_id]
        if self._running >= self.max_concurrency:
            raise RuntimeError("subagent concurrency limit reached")
        self._running += 1
        record.status = "running"
        self._emit("subagent.started", record)
        try:
            arun = getattr(agent, "arun", None)
            if callable(arun):
                result = await arun(query, **kwargs)
            else:
                result = await asyncio.to_thread(agent.run, query, **kwargs)
            record.status = "success"
            self._emit("subagent.completed", record, result=result)
            return result
        except Exception as error:
            record.status = "failed"
            self._emit("subagent.failed", record, error=f"{type(error).__name__}: {error}")
            raise
        finally:
            self._running -= 1

    def list(self) -> list[SubagentRecord]:
        return deepcopy([record for _, record in self._agents.values()])

    def tree(self) -> list[dict[str, Any]]:
        return [
            {
                "agent_id": record.agent_id,
                "name": record.name,
                "parent_agent_id": record.parent_agent_id,
                "depth": record.depth,
                "status": record.status,
                "persistent": record.persistent,
            }
            for _, record in self._agents.values()
        ]

    def send(self, agent_id: str, content: Any, *, message_type: InboxMessageType | str = InboxMessageType.CONTEXT) -> Any:
        if agent_id not in self._agents:
            raise KeyError(agent_id)
        agent, _ = self._agents[agent_id]
        runtime = getattr(agent, "runtime", None)
        if runtime is None or runtime.session is None:
            raise RuntimeError("target subagent does not have an open runtime Session")
        return runtime.inbox.enqueue(message_type, content)

    def _emit(self, event_type: str, record: SubagentRecord, **extra: Any) -> None:
        if self._event_sink:
            data = {
                "agent": {
                    **asdict(record),
                    "permissions": {
                        "allowed": sorted(record.permissions.allowed),
                        "denied": sorted(record.permissions.denied),
                        "max_risk": record.permissions.max_risk.value,
                    },
                },
                **extra,
            }
            self._event_sink(event_type, data)


class AgentRuntime:
    """Bundle Session, Registry, Inbox, Goal, Budget, Job, and Subagent state."""

    def __init__(
            self,
            *,
            session_store: SessionStore | None = None,
            capability_registry: CapabilityRegistry | None = None,
            budget_limits: BudgetLimits | None = None,
            runtime_id: str | None = None,
    ):
        self.runtime_id = runtime_id or uuid4().hex
        self.session_store = session_store or InMemorySessionStore()
        self.registry = capability_registry or CapabilityRegistry()
        self.session: Session | None = None
        self.context = RuntimeContext(runtime_id=self.runtime_id)
        self.inbox = AgentInbox(self._append)
        self.goals = GoalManager(self._append)
        self.budget = BudgetManager(budget_limits, self._append)
        self.jobs = JobManager(self._append, self.inbox)
        self.subagents = SubagentManager(event_sink=self._append)
        self.progress = ProgressTracker(event_sink=self._append)

    def open_session(
            self,
            session_id: str | None = None,
            *,
            metadata: dict[str, Any] | None = None,
            agent_id: str | None = None,
            user_id: str | None = None,
    ) -> Session:
        session = self.session_store.get(session_id) if session_id else None
        if session is None:
            session = Session(session_id=session_id or uuid4().hex, metadata=metadata or {})
            session.append("session.started", {"runtime_id": self.runtime_id})
            self.session_store.create(session)
        self.session = session
        self.context.session_id = session.session_id
        self.context.agent_id = agent_id
        self.context.user_id = user_id
        self.inbox.restore(session)
        self.goals.restore(session)
        self.budget.restore(session)
        self.jobs.restore(session)
        self.jobs.mark_interrupted()
        return deepcopy(session)

    def checkpoint(self, label: str | None = None, metadata: dict[str, Any] | None = None) -> SessionCheckpoint:
        session = self._require_session()
        checkpoint = session.checkpoint(label, metadata)
        self.session_store.save(session)
        return checkpoint

    def fork(
            self,
            *,
            through_sequence: int | None = None,
            metadata: dict[str, Any] | None = None,
    ) -> Session:
        forked = self._require_session().fork(through_sequence=through_sequence, metadata=metadata)
        self.session_store.create(forked)
        return forked

    def snapshot(self) -> dict[str, Any]:
        session = self._require_session()
        return {
            "runtime_id": self.runtime_id,
            "session": session.to_dict(),
            "replay": session.replay().to_dict(),
            "inbox": [message.to_dict() for message in self.inbox.list()],
            "goals": [goal.to_dict() for goal in self.goals.list()],
            "budget": {
                "limits": asdict(self.budget.limits),
                "usage": self.budget.usage.to_dict(),
                "remaining": self.budget.remaining(),
            },
            "jobs": [job.to_dict() for job in self.jobs.list()],
            "progress": asdict(self.progress.state),
        }

    def pause(self, reason: str | None = None) -> None:
        self._append("session.paused", {"reason": reason})

    def resume(self, reason: str | None = None) -> None:
        self._append("session.resumed", {"reason": reason})

    def cancel(self, reason: str | None = None) -> None:
        self._append("session.cancelled", {"reason": reason})

    def continue_run(self, reason: str | None = None) -> None:
        self._append("session.continued", {"reason": reason})

    def _append(self, event_type: str, data: dict[str, Any]) -> None:
        session = self._require_session()
        session.append(
            event_type,
            data,
            turn_id=self.context.turn_id,
            run_id=self.context.run_id,
            agent_id=self.context.agent_id,
        )
        self.session_store.save(session)

    def _require_session(self) -> Session:
        if self.session is None:
            raise RuntimeError("open_session() must be called first")
        return self.session


__all__ = [
    "InboxMessageType",
    "InboxMessageStatus",
    "InboxMessage",
    "AgentInbox",
    "GoalStatus",
    "Goal",
    "GoalManager",
    "BudgetLimits",
    "BudgetUsage",
    "BudgetExceeded",
    "BudgetManager",
    "ProgressState",
    "ProgressTracker",
    "JobStatus",
    "JobRecord",
    "JobManager",
    "SubagentRecord",
    "SubagentManager",
    "AgentRuntime",
]
