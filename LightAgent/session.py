"""Event-sourced sessions, persistence, replay, and context projection."""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import hashlib
from copy import deepcopy
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Protocol
from uuid import uuid4


SESSION_SCHEMA_VERSION = 1
_SENSITIVE_KEYS = {
    "api_key",
    "apikey",
    "authorization",
    "credential",
    "credentials",
    "password",
    "secret",
    "token",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SessionMigrationRegistry:
    """Ordered migrations for persisted Session payloads and events."""

    def __init__(self):
        self._session_migrations: dict[int, Callable[[dict[str, Any]], dict[str, Any]]] = {}
        self._event_migrations: dict[int, Callable[[dict[str, Any]], dict[str, Any]]] = {}

    def register_session(self, from_version: int, migration: Callable[[dict[str, Any]], dict[str, Any]]) -> None:
        self._session_migrations[from_version] = migration

    def register_event(self, from_version: int, migration: Callable[[dict[str, Any]], dict[str, Any]]) -> None:
        self._event_migrations[from_version] = migration

    def migrate(self, value: dict[str, Any]) -> dict[str, Any]:
        payload = deepcopy(value)
        version = int(payload.get("schema_version", 1))
        if version > SESSION_SCHEMA_VERSION:
            raise ValueError(
                f"unsupported Session schema_version={version}; maximum supported={SESSION_SCHEMA_VERSION}"
            )
        while version < SESSION_SCHEMA_VERSION:
            migration = self._session_migrations.get(version)
            if migration is None:
                raise ValueError(f"missing Session migration from schema_version={version}")
            payload = migration(payload)
            version = int(payload.get("schema_version", version + 1))
        payload["events"] = [self.migrate_event(event) for event in payload.get("events", [])]
        return payload

    def migrate_event(self, value: dict[str, Any]) -> dict[str, Any]:
        payload = deepcopy(value)
        version = int(payload.get("schema_version", 1))
        if version > SESSION_SCHEMA_VERSION:
            raise ValueError(
                f"unsupported SessionEvent schema_version={version}; maximum supported={SESSION_SCHEMA_VERSION}"
            )
        while version < SESSION_SCHEMA_VERSION:
            migration = self._event_migrations.get(version)
            if migration is None:
                raise ValueError(f"missing SessionEvent migration from schema_version={version}")
            payload = migration(payload)
            version = int(payload.get("schema_version", version + 1))
        return payload


session_migrations = SessionMigrationRegistry()


def _json_safe(value: Any, *, key: str | None = None) -> Any:
    """Return a JSON-safe copy while removing common credential fields."""
    if key is not None and key.lower() in _SENSITIVE_KEYS:
        return "[redacted]"
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if hasattr(value, "to_dict") and callable(value.to_dict):
        try:
            return _json_safe(value.to_dict())
        except TypeError:
            pass
    if isinstance(value, dict):
        return {str(item_key): _json_safe(item, key=str(item_key)) for item_key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return repr(value)


@dataclass
class SessionEvent:
    """One immutable fact in a session event log."""

    type: str
    session_id: str
    data: dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: uuid4().hex)
    timestamp: str = field(default_factory=_utc_now)
    sequence: int = 0
    schema_version: int = SESSION_SCHEMA_VERSION
    turn_id: str | None = None
    step_id: str | None = None
    run_id: str | None = None
    agent_id: str | None = None
    parent_event_id: str | None = None

    def __post_init__(self) -> None:
        if not self.type or not isinstance(self.type, str):
            raise ValueError("SessionEvent.type must be a non-empty string")
        if not self.session_id:
            raise ValueError("SessionEvent.session_id must not be empty")
        if self.sequence < 0:
            raise ValueError("SessionEvent.sequence must be non-negative")
        if self.schema_version < 1:
            raise ValueError("SessionEvent.schema_version must be at least 1")
        self.data = _json_safe(self.data)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "session_id": self.session_id,
            "type": self.type,
            "data": deepcopy(self.data),
            "timestamp": self.timestamp,
            "sequence": self.sequence,
            "schema_version": self.schema_version,
            "turn_id": self.turn_id,
            "step_id": self.step_id,
            "run_id": self.run_id,
            "agent_id": self.agent_id,
            "parent_event_id": self.parent_event_id,
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "SessionEvent":
        if not isinstance(value, dict):
            raise TypeError("SessionEvent payload must be a dictionary")
        return cls(
            event_id=str(value.get("event_id") or uuid4().hex),
            session_id=str(value["session_id"]),
            type=str(value["type"]),
            data=dict(value.get("data") or {}),
            timestamp=str(value.get("timestamp") or _utc_now()),
            sequence=int(value.get("sequence", 0)),
            schema_version=int(value.get("schema_version", SESSION_SCHEMA_VERSION)),
            turn_id=value.get("turn_id"),
            step_id=value.get("step_id"),
            run_id=value.get("run_id"),
            agent_id=value.get("agent_id"),
            parent_event_id=value.get("parent_event_id"),
        )


@dataclass
class SessionCheckpoint:
    checkpoint_id: str
    session_id: str
    sequence: int
    label: str | None = None
    created_at: str = field(default_factory=_utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(asdict(self))


@dataclass
class SessionReplay:
    session_id: str
    event_count: int
    completed_turns: list[str] = field(default_factory=list)
    incomplete_turns: list[str] = field(default_factory=list)
    failed_turns: list[str] = field(default_factory=list)
    last_sequence: int = 0
    last_event_type: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Session:
    """Append-only session state reconstructed from versioned events."""

    session_id: str = field(default_factory=lambda: uuid4().hex)
    metadata: dict[str, Any] = field(default_factory=dict)
    events: list[SessionEvent] = field(default_factory=list)
    created_at: str = field(default_factory=_utc_now)
    updated_at: str = field(default_factory=_utc_now)
    schema_version: int = SESSION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.session_id:
            raise ValueError("Session.session_id must not be empty")
        self.metadata = _json_safe(self.metadata)
        self.events = sorted(list(self.events), key=lambda event: event.sequence)
        self.validate()

    @property
    def next_sequence(self) -> int:
        return self.events[-1].sequence + 1 if self.events else 1

    def append(
            self,
            event_type: str,
            data: dict[str, Any] | None = None,
            *,
            turn_id: str | None = None,
            step_id: str | None = None,
            run_id: str | None = None,
            agent_id: str | None = None,
            parent_event_id: str | None = None,
    ) -> SessionEvent:
        event = SessionEvent(
            type=event_type,
            session_id=self.session_id,
            data=data or {},
            sequence=self.next_sequence,
            schema_version=self.schema_version,
            turn_id=turn_id,
            step_id=step_id,
            run_id=run_id,
            agent_id=agent_id,
            parent_event_id=parent_event_id,
        )
        self.events.append(event)
        self.updated_at = event.timestamp
        return event

    def append_event(self, event: SessionEvent) -> SessionEvent:
        if event.session_id != self.session_id:
            raise ValueError("event session_id does not match Session")
        expected = self.next_sequence
        if event.sequence == 0:
            event.sequence = expected
        if event.sequence != expected:
            raise ValueError(f"event sequence must be {expected}, got {event.sequence}")
        if any(existing.event_id == event.event_id for existing in self.events):
            raise ValueError(f"duplicate event_id: {event.event_id}")
        self.events.append(event)
        self.updated_at = event.timestamp
        return event

    def page(self, *, after: int = 0, limit: int = 100) -> list[SessionEvent]:
        if limit < 1:
            raise ValueError("limit must be at least 1")
        return [event for event in self.events if event.sequence > after][:limit]

    def checkpoint(self, label: str | None = None, metadata: dict[str, Any] | None = None) -> SessionCheckpoint:
        checkpoint = SessionCheckpoint(
            checkpoint_id=uuid4().hex,
            session_id=self.session_id,
            sequence=self.events[-1].sequence if self.events else 0,
            label=label,
            metadata=_json_safe(metadata or {}),
        )
        self.append("session.checkpointed", {"checkpoint": checkpoint.to_dict()})
        return checkpoint

    def fork(
            self,
            *,
            new_session_id: str | None = None,
            through_sequence: int | None = None,
            metadata: dict[str, Any] | None = None,
    ) -> "Session":
        boundary = through_sequence if through_sequence is not None else (self.events[-1].sequence if self.events else 0)
        if boundary < 0 or boundary > (self.events[-1].sequence if self.events else 0):
            raise ValueError("through_sequence is outside the session event range")
        forked = Session(
            session_id=new_session_id or uuid4().hex,
            metadata={
                **deepcopy(self.metadata),
                **(metadata or {}),
                "forked_from": self.session_id,
                "forked_at_sequence": boundary,
            },
        )
        forked.append("session.started", {"forked_from": self.session_id, "through_sequence": boundary})
        for event in self.events:
            if event.sequence > boundary:
                break
            forked.append(
                event.type,
                {
                    **deepcopy(event.data),
                    "source_session_id": self.session_id,
                    "source_event_id": event.event_id,
                    "source_sequence": event.sequence,
                },
                turn_id=event.turn_id,
                step_id=event.step_id,
                run_id=event.run_id,
                agent_id=event.agent_id,
                parent_event_id=event.event_id,
            )
        forked.append("session.forked", {"source_session_id": self.session_id, "through_sequence": boundary})
        return forked

    def replay(self) -> SessionReplay:
        started: set[str] = set()
        completed: set[str] = set()
        failed: set[str] = set()
        for event in self.events:
            if not event.turn_id:
                continue
            if event.type == "turn.started":
                started.add(event.turn_id)
            elif event.type == "turn.completed":
                completed.add(event.turn_id)
            elif event.type == "turn.failed":
                failed.add(event.turn_id)
        return SessionReplay(
            session_id=self.session_id,
            event_count=len(self.events),
            completed_turns=sorted(completed),
            incomplete_turns=sorted(started - completed - failed),
            failed_turns=sorted(failed),
            last_sequence=self.events[-1].sequence if self.events else 0,
            last_event_type=self.events[-1].type if self.events else None,
        )

    def validate(self) -> None:
        seen_ids: set[str] = set()
        expected = 1
        for event in self.events:
            if event.session_id != self.session_id:
                raise ValueError("session contains an event for another session")
            if event.event_id in seen_ids:
                raise ValueError(f"duplicate event_id: {event.event_id}")
            if event.sequence != expected:
                raise ValueError(f"event sequence gap: expected {expected}, got {event.sequence}")
            if event.schema_version > SESSION_SCHEMA_VERSION:
                raise ValueError(
                    f"unsupported SessionEvent schema_version={event.schema_version}; "
                    f"maximum supported={SESSION_SCHEMA_VERSION}"
                )
            seen_ids.add(event.event_id)
            expected += 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "metadata": deepcopy(self.metadata),
            "events": [event.to_dict() for event in self.events],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Session":
        value = session_migrations.migrate(value)
        return cls(
            session_id=str(value["session_id"]),
            metadata=dict(value.get("metadata") or {}),
            events=[SessionEvent.from_dict(event) for event in value.get("events", [])],
            created_at=str(value.get("created_at") or _utc_now()),
            updated_at=str(value.get("updated_at") or _utc_now()),
            schema_version=int(value.get("schema_version", SESSION_SCHEMA_VERSION)),
        )


class SessionStore(Protocol):
    def create(self, session: Session | None = None, *, metadata: dict[str, Any] | None = None) -> Session:
        ...

    def get(self, session_id: str) -> Session | None:
        ...

    def save(self, session: Session) -> None:
        ...

    def list(self, *, limit: int = 100) -> list[Session]:
        ...

    def delete(self, session_id: str) -> bool:
        ...


class InMemorySessionStore:
    """Thread-safe dependency-free SessionStore."""

    def __init__(self):
        self._sessions: dict[str, Session] = {}
        self._lock = threading.RLock()

    def create(self, session: Session | None = None, *, metadata: dict[str, Any] | None = None) -> Session:
        with self._lock:
            value = session or Session(metadata=metadata or {})
            if value.session_id in self._sessions:
                raise ValueError(f"session already exists: {value.session_id}")
            self._sessions[value.session_id] = deepcopy(value)
            return deepcopy(value)

    def get(self, session_id: str) -> Session | None:
        with self._lock:
            value = self._sessions.get(str(session_id))
            return deepcopy(value) if value is not None else None

    def save(self, session: Session) -> None:
        session.validate()
        with self._lock:
            current = self._sessions.get(session.session_id)
            if current and current.events and session.events:
                if session.events[-1].sequence < current.events[-1].sequence:
                    raise ValueError("refusing to replace a Session with an older event sequence")
            self._sessions[session.session_id] = deepcopy(session)

    def list(self, *, limit: int = 100) -> list[Session]:
        if limit < 1:
            raise ValueError("limit must be at least 1")
        with self._lock:
            values = sorted(self._sessions.values(), key=lambda item: item.updated_at, reverse=True)
            return deepcopy(values[:limit])

    def delete(self, session_id: str) -> bool:
        with self._lock:
            return self._sessions.pop(str(session_id), None) is not None


class JsonlSessionStore:
    """One append-readable JSONL file per Session with atomic full saves."""

    def __init__(self, directory: str | os.PathLike[str]):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

    @staticmethod
    def _safe_id(session_id: str) -> str:
        value = str(session_id)
        if not value or any(character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for character in value):
            raise ValueError("session_id contains unsafe characters")
        return value

    def _path(self, session_id: str) -> Path:
        return self.directory / f"{self._safe_id(session_id)}.jsonl"

    def create(self, session: Session | None = None, *, metadata: dict[str, Any] | None = None) -> Session:
        value = session or Session(metadata=metadata or {})
        with self._lock:
            if self._path(value.session_id).exists():
                raise ValueError(f"session already exists: {value.session_id}")
            self.save(value)
        return deepcopy(value)

    def get(self, session_id: str) -> Session | None:
        path = self._path(session_id)
        if not path.exists():
            return None
        with self._lock, path.open("r", encoding="utf-8") as handle:
            lines = [json.loads(line) for line in handle if line.strip()]
        if not lines or lines[0].get("kind") != "session":
            raise ValueError(f"invalid Session JSONL header: {path}")
        header = lines[0]["value"]
        events = [SessionEvent.from_dict(line["value"]) for line in lines[1:] if line.get("kind") == "event"]
        return Session(
            session_id=header["session_id"],
            metadata=header.get("metadata") or {},
            events=events,
            created_at=header.get("created_at") or _utc_now(),
            updated_at=header.get("updated_at") or _utc_now(),
            schema_version=int(header.get("schema_version", SESSION_SCHEMA_VERSION)),
        )

    def save(self, session: Session) -> None:
        session.validate()
        path = self._path(session.session_id)
        temporary = path.with_suffix(f".tmp-{uuid4().hex}")
        header = {
            "session_id": session.session_id,
            "metadata": session.metadata,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "schema_version": session.schema_version,
        }
        with self._lock:
            with temporary.open("w", encoding="utf-8") as handle:
                handle.write(json.dumps({"kind": "session", "value": header}, ensure_ascii=False) + "\n")
                for event in session.events:
                    handle.write(json.dumps({"kind": "event", "value": event.to_dict()}, ensure_ascii=False) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)

    def list(self, *, limit: int = 100) -> list[Session]:
        if limit < 1:
            raise ValueError("limit must be at least 1")
        sessions = []
        for path in sorted(self.directory.glob("*.jsonl"), key=lambda item: item.stat().st_mtime, reverse=True):
            session = self.get(path.stem)
            if session is not None:
                sessions.append(session)
            if len(sessions) >= limit:
                break
        return sessions

    def delete(self, session_id: str) -> bool:
        path = self._path(session_id)
        with self._lock:
            if not path.exists():
                return False
            path.unlink()
            return True


class SqliteSessionStore:
    """Standard-library SQLite SessionStore with transactional saves."""

    def __init__(self, path: str | os.PathLike[str]):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    metadata TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    schema_version INTEGER NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS session_events (
                    session_id TEXT NOT NULL,
                    sequence INTEGER NOT NULL,
                    event_id TEXT NOT NULL UNIQUE,
                    payload TEXT NOT NULL,
                    PRIMARY KEY (session_id, sequence),
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                )
                """
            )

    def create(self, session: Session | None = None, *, metadata: dict[str, Any] | None = None) -> Session:
        value = session or Session(metadata=metadata or {})
        with self._lock, self._connect() as connection:
            existing = connection.execute(
                "SELECT 1 FROM sessions WHERE session_id = ?", (value.session_id,)
            ).fetchone()
            if existing:
                raise ValueError(f"session already exists: {value.session_id}")
        self.save(value)
        return deepcopy(value)

    def get(self, session_id: str) -> Session | None:
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM sessions WHERE session_id = ?", (str(session_id),)
            ).fetchone()
            if row is None:
                return None
            event_rows = connection.execute(
                "SELECT payload FROM session_events WHERE session_id = ? ORDER BY sequence",
                (str(session_id),),
            ).fetchall()
        return Session(
            session_id=row["session_id"],
            metadata=json.loads(row["metadata"]),
            events=[SessionEvent.from_dict(json.loads(event_row["payload"])) for event_row in event_rows],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            schema_version=row["schema_version"],
        )

    def save(self, session: Session) -> None:
        session.validate()
        with self._lock, self._connect() as connection:
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute(
                """
                INSERT INTO sessions(session_id, metadata, created_at, updated_at, schema_version)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    metadata=excluded.metadata,
                    updated_at=excluded.updated_at,
                    schema_version=excluded.schema_version
                """,
                (
                    session.session_id,
                    json.dumps(session.metadata, ensure_ascii=False),
                    session.created_at,
                    session.updated_at,
                    session.schema_version,
                ),
            )
            connection.execute("DELETE FROM session_events WHERE session_id = ?", (session.session_id,))
            connection.executemany(
                "INSERT INTO session_events(session_id, sequence, event_id, payload) VALUES (?, ?, ?, ?)",
                [
                    (
                        session.session_id,
                        event.sequence,
                        event.event_id,
                        json.dumps(event.to_dict(), ensure_ascii=False),
                    )
                    for event in session.events
                ],
            )

    def list(self, *, limit: int = 100) -> list[Session]:
        if limit < 1:
            raise ValueError("limit must be at least 1")
        with self._lock, self._connect() as connection:
            rows = connection.execute(
                "SELECT session_id FROM sessions ORDER BY updated_at DESC LIMIT ?", (int(limit),)
            ).fetchall()
        return [session for row in rows if (session := self.get(row["session_id"])) is not None]

    def delete(self, session_id: str) -> bool:
        with self._lock, self._connect() as connection:
            connection.execute("PRAGMA foreign_keys=ON")
            cursor = connection.execute("DELETE FROM sessions WHERE session_id = ?", (str(session_id),))
            return cursor.rowcount > 0


class ContextProjector:
    """Project model messages and runtime views from Session events."""

    def messages(self, session: Session, *, turn_id: str | None = None) -> list[dict[str, Any]]:
        requested = [
            event for event in session.events
            if event.type == "model.requested"
            and (turn_id is None or event.turn_id == turn_id)
            and isinstance(event.data.get("messages"), list)
        ]
        messages: list[dict[str, Any]] = []
        for event in session.events:
            if turn_id is not None and event.turn_id != turn_id:
                continue
            if event.type in {"message.received", "message.created"}:
                messages.append({"role": event.data.get("role", "user"), "content": event.data.get("content", "")})
            elif event.type in {"assistant.completed", "model.completed"} and event.data.get("content") is not None:
                messages.append({"role": "assistant", "content": event.data.get("content", "")})
            elif event.type == "tool.completed":
                messages.append({
                    "role": "tool",
                    "tool_call_id": event.data.get("tool_call_id"),
                    "content": str(event.data.get("output", "")),
                })
        if messages:
            return messages
        if requested:
            return deepcopy(requested[-1].data["messages"])
        return []

    def model_request(
            self,
            session: Session,
            *,
            sequence: int | None = None,
    ) -> list[dict[str, Any]]:
        """Reconstruct the exact messages sent for one persisted model request."""
        requested = [
            event for event in session.events
            if event.type == "model.requested"
            and isinstance(event.data.get("messages"), list)
            and (sequence is None or event.sequence == sequence)
        ]
        if not requested:
            raise LookupError("model request event was not found")
        return deepcopy(requested[-1].data["messages"])

    def trace(self, session: Session, *, turn_id: str | None = None) -> list[dict[str, Any]]:
        trace = []
        for event in session.events:
            if turn_id is not None and event.turn_id != turn_id:
                continue
            trace_type = event.data.get("trace_type")
            if trace_type:
                trace.append({
                    "type": trace_type,
                    "data": deepcopy(event.data.get("trace_data") or {}),
                    "timestamp": event.timestamp,
                    "trace_id": event.data.get("trace_id"),
                    "parent_trace_id": event.data.get("parent_trace_id"),
                    "run_group_id": event.data.get("run_group_id"),
                })
        return trace


@dataclass
class CompactionResult:
    messages: list[dict[str, Any]]
    removed_count: int
    summary: str | None = None
    spilled: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class ContextBudget:
    """Dependency-free context budget using a conservative character estimate."""

    max_tokens: int = 8192
    reserved_output_tokens: int = 1024
    chars_per_token: float = 4.0

    def __post_init__(self) -> None:
        if self.max_tokens < 1 or self.reserved_output_tokens < 0:
            raise ValueError("context token limits must be non-negative")
        if self.reserved_output_tokens >= self.max_tokens:
            raise ValueError("reserved_output_tokens must be smaller than max_tokens")
        if self.chars_per_token <= 0:
            raise ValueError("chars_per_token must be positive")

    def estimate(self, messages: Iterable[dict[str, Any]]) -> int:
        rendered = json.dumps(list(messages), ensure_ascii=False, sort_keys=True)
        return max(1, int(len(rendered) / self.chars_per_token) + 1)

    def fits(self, messages: Iterable[dict[str, Any]]) -> bool:
        return self.estimate(messages) <= self.max_tokens - self.reserved_output_tokens


class ContextCompactor:
    """Deterministic message trimming with optional summary generation."""

    def __init__(
            self,
            summarizer: Callable[[list[dict[str, Any]]], str] | None = None,
            *,
            max_inline_tool_chars: int = 12000,
    ):
        self.summarizer = summarizer
        self.max_inline_tool_chars = max_inline_tool_chars

    def compact(self, messages: Iterable[dict[str, Any]], *, max_messages: int = 20) -> CompactionResult:
        values, spilled = self._spill_tool_results(messages)
        if max_messages < 2:
            raise ValueError("max_messages must be at least 2")
        if len(values) <= max_messages:
            return CompactionResult(messages=values, removed_count=0, spilled=spilled)

        system = [message for message in values if message.get("role") == "system"][:1]
        non_system = [message for message in values if message.get("role") != "system"]
        keep_count = max_messages - len(system)
        kept = non_system[-keep_count:]
        removed = non_system[:-keep_count]

        while kept and kept[0].get("role") == "tool":
            removed.append(kept.pop(0))
        summary = self.summarizer(deepcopy(removed)) if self.summarizer and removed else None
        if summary:
            summary_message = {
                "role": "system",
                "content": f"Previous conversation summary:\n{summary}",
                "metadata": {"compacted": True, "removed_count": len(removed)},
            }
            result_messages = system + [summary_message] + kept
        else:
            result_messages = system + kept
        return CompactionResult(
            messages=result_messages,
            removed_count=len(removed),
            summary=summary,
            spilled=spilled,
        )

    def compact_to_budget(
            self,
            messages: Iterable[dict[str, Any]],
            budget: ContextBudget,
    ) -> CompactionResult:
        values = list(messages)
        if budget.fits(values):
            prepared, spilled = self._spill_tool_results(values)
            return CompactionResult(messages=prepared, removed_count=0, spilled=spilled)
        max_messages = max(2, len(values))
        while max_messages > 2:
            result = self.compact(values, max_messages=max_messages)
            if budget.fits(result.messages):
                return result
            max_messages -= 1
        return self.compact(values, max_messages=2)

    def _spill_tool_results(
            self,
            messages: Iterable[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        prepared: list[dict[str, Any]] = []
        spilled: list[dict[str, Any]] = []
        for message in messages:
            value = deepcopy(message)
            content = value.get("content")
            if value.get("role") == "tool" and isinstance(content, str) and len(content) > self.max_inline_tool_chars:
                digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
                reference = f"tool-result:sha256:{digest}"
                spilled.append({
                    "reference": reference,
                    "sha256": digest,
                    "size": len(content),
                    "content": content,
                })
                value["content"] = f"[Tool result stored outside context: {reference}, {len(content)} chars]"
                value.setdefault("metadata", {})["content_reference"] = reference
            prepared.append(value)
        return prepared, spilled


__all__ = [
    "SESSION_SCHEMA_VERSION",
    "SessionMigrationRegistry",
    "session_migrations",
    "SessionEvent",
    "SessionCheckpoint",
    "SessionReplay",
    "Session",
    "SessionStore",
    "InMemorySessionStore",
    "JsonlSessionStore",
    "SqliteSessionStore",
    "ContextProjector",
    "CompactionResult",
    "ContextBudget",
    "ContextCompactor",
]
