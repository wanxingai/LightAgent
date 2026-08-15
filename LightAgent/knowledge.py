"""Optional knowledge Providers for RAG, Session search, Skills, MCP, and LightFlow."""

from __future__ import annotations

import inspect
import json
import sqlite3
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Protocol
from uuid import uuid4

from .capabilities import (
    BaseCapabilityProvider,
    CapabilityRisk,
    CapabilitySpec,
    ProviderHealth,
)
from .session import SessionStore, _utc_now


@dataclass
class RetrievalDocument:
    content: str
    title: str | None = None
    source: str | None = None
    document_id: str = field(default_factory=lambda: uuid4().hex)
    scope: str = "workspace"
    owner_id: str | None = None
    tenant_id: str | None = None
    created_at: str = field(default_factory=_utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RetrievalResult:
    document_id: str
    chunk_id: str
    content: str
    citation_id: str
    title: str | None = None
    source: str | None = None
    position: int = 0
    score: float | None = None
    scope: str = "workspace"
    owner_id: str | None = None
    tenant_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class RetrievalProvider(Protocol):
    def ingest(self, document: RetrievalDocument) -> str:
        ...

    def remove(self, document_id: str) -> bool:
        ...

    def list_documents(self) -> list[RetrievalDocument]:
        ...

    def search(self, query: str, *, limit: int = 5, **filters: Any) -> list[RetrievalResult]:
        ...

    def read_chunk(self, chunk_id: str) -> RetrievalResult | None:
        ...

    def reindex(self) -> None:
        ...


class SqliteFTSRetrievalProvider(BaseCapabilityProvider):
    """Dependency-free SQLite FTS5 retrieval with source-aware chunks."""

    name = "sqlite-fts5-rag"
    version = "1"

    def __init__(self, path: str | Path, *, chunk_size: int = 1200, chunk_overlap: int = 120):
        if chunk_size < 100:
            raise ValueError("chunk_size must be at least 100")
        if chunk_overlap < 0 or chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be non-negative and smaller than chunk_size")
        self.path = str(path)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self._fts5 = True
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        super().__init__([
            CapabilitySpec("rag.ingest", write=True, persistent=True, risk=CapabilityRisk.ISOLATED_WRITE),
            CapabilitySpec("rag.remove", write=True, persistent=True, risk=CapabilityRisk.DESTRUCTIVE),
            CapabilitySpec("rag.list_documents", read=True),
            CapabilitySpec("rag.search", read=True),
            CapabilitySpec("rag.read_chunk", read=True),
            CapabilitySpec("rag.reindex", write=True, persistent=True, risk=CapabilityRisk.SENSITIVE),
        ])
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS rag_documents (
                    document_id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS rag_chunks (
                    chunk_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    FOREIGN KEY(document_id) REFERENCES rag_documents(document_id) ON DELETE CASCADE
                )
                """
            )
            try:
                connection.execute(
                    "CREATE VIRTUAL TABLE IF NOT EXISTS rag_chunks_fts USING fts5(chunk_id UNINDEXED, content)"
                )
            except sqlite3.OperationalError:
                self._fts5 = False

    async def health(self) -> ProviderHealth:
        return ProviderHealth(
            healthy=True,
            status="ready" if self._fts5 else "degraded",
            message=None if self._fts5 else "SQLite FTS5 unavailable; LIKE search fallback is active",
            degraded_capabilities=[] if self._fts5 else ["rag.search"],
        )

    def ingest(self, document: RetrievalDocument | dict[str, Any]) -> str:
        value = document if isinstance(document, RetrievalDocument) else RetrievalDocument(**document)
        chunks = self._chunks(value.content)
        with self._connect() as connection:
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute(
                "INSERT OR REPLACE INTO rag_documents(document_id, payload) VALUES (?, ?)",
                (value.document_id, json.dumps(value.to_dict(), ensure_ascii=False)),
            )
            old_chunks = connection.execute(
                "SELECT chunk_id FROM rag_chunks WHERE document_id = ?", (value.document_id,)
            ).fetchall()
            if self._fts5:
                connection.executemany(
                    "DELETE FROM rag_chunks_fts WHERE chunk_id = ?",
                    [(row["chunk_id"],) for row in old_chunks],
                )
            connection.execute("DELETE FROM rag_chunks WHERE document_id = ?", (value.document_id,))
            for position, content in enumerate(chunks):
                chunk_id = f"{value.document_id}:{position}"
                connection.execute(
                    "INSERT INTO rag_chunks(chunk_id, document_id, position, content) VALUES (?, ?, ?, ?)",
                    (chunk_id, value.document_id, position, content),
                )
                if self._fts5:
                    connection.execute(
                        "INSERT INTO rag_chunks_fts(chunk_id, content) VALUES (?, ?)",
                        (chunk_id, content),
                    )
        return value.document_id

    def remove(self, document_id: str) -> bool:
        with self._connect() as connection:
            connection.execute("PRAGMA foreign_keys=ON")
            rows = connection.execute(
                "SELECT chunk_id FROM rag_chunks WHERE document_id = ?", (document_id,)
            ).fetchall()
            if self._fts5:
                connection.executemany(
                    "DELETE FROM rag_chunks_fts WHERE chunk_id = ?", [(row["chunk_id"],) for row in rows]
                )
            cursor = connection.execute("DELETE FROM rag_documents WHERE document_id = ?", (document_id,))
            return cursor.rowcount > 0

    def list_documents(self) -> list[RetrievalDocument]:
        with self._connect() as connection:
            rows = connection.execute("SELECT payload FROM rag_documents ORDER BY rowid").fetchall()
        return [RetrievalDocument(**json.loads(row["payload"])) for row in rows]

    def search(
            self,
            query: str,
            *,
            limit: int = 5,
            scope: str | None = None,
            owner_id: str | None = None,
            tenant_id: str | None = None,
    ) -> list[RetrievalResult]:
        if not query.strip():
            return []
        if limit < 1:
            raise ValueError("limit must be at least 1")
        with self._connect() as connection:
            if self._fts5:
                rows = connection.execute(
                    """
                    SELECT c.*, d.payload, bm25(rag_chunks_fts) AS rank
                    FROM rag_chunks_fts
                    JOIN rag_chunks c ON c.chunk_id = rag_chunks_fts.chunk_id
                    JOIN rag_documents d ON d.document_id = c.document_id
                    WHERE rag_chunks_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                    """,
                    (query, max(limit * 10, limit)),
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT c.*, d.payload, NULL AS rank
                    FROM rag_chunks c
                    JOIN rag_documents d ON d.document_id = c.document_id
                    WHERE lower(c.content) LIKE ?
                    ORDER BY c.rowid
                    LIMIT ?
                    """,
                    (f"%{query.lower()}%", max(limit * 10, limit)),
                ).fetchall()
        results = []
        for row in rows:
            document = RetrievalDocument(**json.loads(row["payload"]))
            if scope is not None and document.scope != scope:
                continue
            if owner_id is not None and document.owner_id != owner_id:
                continue
            if tenant_id is not None and document.tenant_id != tenant_id:
                continue
            results.append(self._result(row, document))
            if len(results) >= limit:
                break
        return results

    def read_chunk(self, chunk_id: str) -> RetrievalResult | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT c.*, d.payload, NULL AS rank
                FROM rag_chunks c JOIN rag_documents d ON d.document_id = c.document_id
                WHERE c.chunk_id = ?
                """,
                (chunk_id,),
            ).fetchone()
        if row is None:
            return None
        return self._result(row, RetrievalDocument(**json.loads(row["payload"])))

    def reindex(self) -> None:
        if not self._fts5:
            return
        with self._connect() as connection:
            connection.execute("DELETE FROM rag_chunks_fts")
            rows = connection.execute("SELECT chunk_id, content FROM rag_chunks ORDER BY rowid").fetchall()
            connection.executemany(
                "INSERT INTO rag_chunks_fts(chunk_id, content) VALUES (?, ?)",
                [(row["chunk_id"], row["content"]) for row in rows],
            )

    async def invoke(self, capability: str, **arguments: Any) -> Any:
        method_name = capability.removeprefix("rag.")
        method = getattr(self, method_name)
        return method(**arguments)

    def _chunks(self, content: str) -> list[str]:
        if not content:
            return [""]
        step = self.chunk_size - self.chunk_overlap
        return [content[index:index + self.chunk_size] for index in range(0, len(content), step)]

    @staticmethod
    def _result(row: sqlite3.Row, document: RetrievalDocument) -> RetrievalResult:
        rank = row["rank"]
        return RetrievalResult(
            document_id=document.document_id,
            chunk_id=row["chunk_id"],
            content=row["content"],
            citation_id=f"rag:{row['chunk_id']}",
            title=document.title,
            source=document.source,
            position=row["position"],
            score=None if rank is None else float(-rank),
            scope=document.scope,
            owner_id=document.owner_id,
            tenant_id=document.tenant_id,
            metadata=deepcopy(document.metadata),
        )


class SessionSearchProvider(BaseCapabilityProvider):
    """Literal cross-Session search kept separate from knowledge-base RAG."""

    name = "session-search"
    version = "1"

    def __init__(self, store: SessionStore):
        self.store = store
        super().__init__([CapabilitySpec("session.search", read=True)])

    def search(self, query: str, *, limit: int = 20) -> list[dict[str, Any]]:
        if not query.strip():
            return []
        needle = query.casefold()
        matches: list[dict[str, Any]] = []
        for session in self.store.list(limit=max(limit, 100)):
            for event in reversed(session.events):
                rendered = json.dumps(event.data, ensure_ascii=False, sort_keys=True)
                if needle not in rendered.casefold():
                    continue
                matches.append({
                    "session_id": session.session_id,
                    "event_id": event.event_id,
                    "sequence": event.sequence,
                    "event_type": event.type,
                    "citation_id": f"session:{session.session_id}:{event.sequence}",
                    "timestamp": event.timestamp,
                    "data": deepcopy(event.data),
                })
                if len(matches) >= limit:
                    return matches
        return matches

    async def invoke(self, capability: str, **arguments: Any) -> Any:
        if capability != "session.search":
            raise LookupError(capability)
        return self.search(**arguments)


class SkillProviderAdapter(BaseCapabilityProvider):
    name = "skills"
    version = "1"

    def __init__(self, skill_manager: Any):
        self.skill_manager = skill_manager
        super().__init__([
            CapabilitySpec("skill.list", read=True),
            CapabilitySpec("skill.activate", read=True),
            CapabilitySpec("skill.read_reference", read=True),
            CapabilitySpec(
                "skill.execute_script",
                execute=True,
                risk=CapabilityRisk.SENSITIVE,
                requires_sandbox=True,
                requires_approval=True,
            ),
        ])

    async def invoke(self, capability: str, **arguments: Any) -> Any:
        if capability == "skill.list":
            return [asdict(skill) for skill in self.skill_manager.skills.values()]
        method_name = capability.removeprefix("skill.")
        method = getattr(self.skill_manager, method_name)
        return method(**arguments)


class MCPProviderAdapter(BaseCapabilityProvider):
    name = "mcp"
    version = "1"

    def __init__(self, manager: Any, tool_names: Iterable[str] | None = None):
        self.manager = manager
        names = list(tool_names or [])
        super().__init__([
            CapabilitySpec(
                f"mcp.{name}",
                network=True,
                execute=True,
                risk=CapabilityRisk.SENSITIVE,
                cancellable=True,
            )
            for name in names
        ])

    async def invoke(self, capability: str, **arguments: Any) -> Any:
        tool_name = capability.removeprefix("mcp.")
        return await self.manager.call_tool(tool_name, arguments)


class WorkflowProviderAdapter(BaseCapabilityProvider):
    name = "lightflow"
    version = "1"

    def __init__(self, flow: Any):
        self.flow = flow
        super().__init__([
            CapabilitySpec("workflow.start", execute=True, cancellable=True),
            CapabilitySpec("workflow.status", read=True),
            CapabilitySpec("workflow.resume", execute=True, resumable=True),
            CapabilitySpec("workflow.rerun_step", execute=True, risk=CapabilityRisk.SENSITIVE),
        ])

    async def invoke(self, capability: str, **arguments: Any) -> Any:
        if capability == "workflow.start":
            method = getattr(self.flow, "arun", None)
            if callable(method):
                return await method(**arguments)
            return await _call_in_thread(self.flow.run, **arguments)
        if capability == "workflow.status":
            return self.flow.get_run(arguments["run_id"])
        if capability == "workflow.resume":
            return await _call_in_thread(self.flow.resume, arguments["run_id"], **{
                key: value for key, value in arguments.items() if key != "run_id"
            })
        if capability == "workflow.rerun_step":
            return await _call_in_thread(
                self.flow.rerun_step,
                arguments["run_id"],
                arguments["step_name"],
            )
        raise LookupError(capability)


async def _call_in_thread(function: Any, *args: Any, **kwargs: Any) -> Any:
    result = await __import__("asyncio").to_thread(function, *args, **kwargs)
    if inspect.isawaitable(result):
        return await result
    return result


__all__ = [
    "RetrievalDocument",
    "RetrievalResult",
    "RetrievalProvider",
    "SqliteFTSRetrievalProvider",
    "SessionSearchProvider",
    "SkillProviderAdapter",
    "MCPProviderAdapter",
    "WorkflowProviderAdapter",
]
