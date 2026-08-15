import asyncio

import pytest

from LightAgent import (
    CapabilityRegistry,
    InMemorySessionStore,
    MCPProviderAdapter,
    RetrievalDocument,
    RuntimeContext,
    Session,
    SessionSearchProvider,
    SkillProviderAdapter,
    SqliteFTSRetrievalProvider,
    WorkflowProviderAdapter,
)
from LightAgent.skills import Skill


def test_sqlite_fts_ingest_search_citation_and_scope(tmp_path):
    provider = SqliteFTSRetrievalProvider(tmp_path / "rag.sqlite3", chunk_size=100, chunk_overlap=10)
    provider.ingest(RetrievalDocument(
        document_id="d1",
        title="Runtime",
        source="guide.md",
        content="LightAgent durable session checkpoint recovery",
        scope="workspace",
        owner_id="team-a",
    ))

    results = provider.search("checkpoint", owner_id="team-a")

    assert results[0].document_id == "d1"
    assert results[0].citation_id.startswith("rag:d1:")
    assert provider.search("checkpoint", owner_id="team-b") == []


def test_rag_provider_can_be_invoked_through_registry(tmp_path):
    provider = SqliteFTSRetrievalProvider(tmp_path / "rag.sqlite3")
    registry = CapabilityRegistry()
    registry.register(provider)

    document_id = asyncio.run(registry.invoke("rag.ingest", {
        "document": {"content": "provider registry policy", "document_id": "d1"}
    }, context=RuntimeContext(runtime_id="r1")))
    results = asyncio.run(registry.invoke("rag.search", {"query": "registry"}))

    assert document_id == "d1"
    assert results[0].document_id == "d1"


def test_session_search_is_separate_and_returns_event_citation():
    store = InMemorySessionStore()
    session = Session(session_id="s1")
    session.append("message.received", {"content": "quarterly forecast"})
    store.create(session)
    provider = SessionSearchProvider(store)

    result = provider.search("forecast")[0]

    assert result["citation_id"] == "session:s1:1"
    assert result["event_type"] == "message.received"


def test_rag_document_lifecycle_chunking_and_reindex(tmp_path):
    provider = SqliteFTSRetrievalProvider(tmp_path / "rag.sqlite3", chunk_size=100, chunk_overlap=20)
    document = RetrievalDocument(
        document_id="long",
        title="Long document",
        source="long.md",
        content="checkpoint " + ("x" * 130) + " recovery",
        metadata={"version": 1},
    )

    assert provider.ingest(document) == "long"
    chunks = [provider.read_chunk(f"long:{index}") for index in range(2)]
    assert [len(chunk.content) for chunk in chunks] == [100, 70]
    assert chunks[0].metadata == {"version": 1}
    assert provider.read_chunk("missing") is None
    assert [item.document_id for item in provider.list_documents()] == ["long"]

    provider.reindex()
    assert provider.search("checkpoint")[0].document_id == "long"
    assert provider.remove("long") is True
    assert provider.remove("long") is False
    assert provider.list_documents() == []
    assert provider.read_chunk("long:0") is None


def test_rag_scope_owner_and_tenant_filters_are_combined(tmp_path):
    provider = SqliteFTSRetrievalProvider(tmp_path / "rag.sqlite3")
    provider.ingest(RetrievalDocument(
        document_id="tenant-a",
        content="shared runtime handbook",
        scope="project",
        owner_id="owner-a",
        tenant_id="tenant-a",
    ))
    provider.ingest(RetrievalDocument(
        document_id="tenant-b",
        content="shared runtime handbook",
        scope="project",
        owner_id="owner-b",
        tenant_id="tenant-b",
    ))

    matches = provider.search(
        "runtime", scope="project", owner_id="owner-a", tenant_id="tenant-a", limit=10
    )

    assert [result.document_id for result in matches] == ["tenant-a"]
    assert provider.search("runtime", owner_id="owner-a", tenant_id="tenant-b") == []
    assert provider.search("   ") == []
    with pytest.raises(ValueError, match="limit must be at least 1"):
        provider.search("runtime", limit=0)


def test_rag_like_fallback_reports_degraded_health_and_searches(tmp_path):
    provider = SqliteFTSRetrievalProvider(tmp_path / "rag.sqlite3")
    provider.ingest(RetrievalDocument(document_id="fallback", content="Fallback Search Works"))
    provider._fts5 = False

    health = asyncio.run(provider.health())

    assert health.status == "degraded"
    assert health.degraded_capabilities == ["rag.search"]
    assert provider.search("search")[0].document_id == "fallback"
    provider.reindex()  # A degraded provider keeps the source tables intact.


def test_session_search_is_case_insensitive_bounded_and_handles_empty_query():
    store = InMemorySessionStore()
    for index in range(3):
        session = Session(session_id=f"s{index}")
        session.append("message.received", {"content": f"Quarterly Forecast {index}"})
        store.create(session)
    provider = SessionSearchProvider(store)

    matches = provider.search("FORECAST", limit=2)

    assert len(matches) == 2
    assert all(match["citation_id"].startswith("session:") for match in matches)
    assert provider.search("  ") == []


def test_skill_mcp_and_workflow_provider_adapters_delegate_arguments():
    class Skills:
        def __init__(self):
            self.skills = {"demo": Skill(name="demo", description="Demo", path="skills/demo")}

        def activate_skill(self, skill_name):
            return f"active:{skill_name}"

    class MCP:
        async def call_tool(self, name, arguments):
            return {"name": name, "arguments": arguments}

    class Flow:
        async def arun(self, query):
            return f"started:{query}"

        def get_run(self, run_id):
            return {"run_id": run_id}

        def resume(self, run_id, **kwargs):
            return {"resumed": run_id, **kwargs}

        def rerun_step(self, run_id, step_name):
            return {"rerun": run_id, "step": step_name}

    skills = SkillProviderAdapter(Skills())
    mcp = MCPProviderAdapter(MCP(), ["search"])
    workflow = WorkflowProviderAdapter(Flow())

    async def scenario():
        listed = await skills.invoke("skill.list")
        activated = await skills.invoke("skill.activate", skill_name="demo")
        called = await mcp.invoke("mcp.search", query="runtime")
        started = await workflow.invoke("workflow.start", query="draft")
        status = await workflow.invoke("workflow.status", run_id="run-1")
        resumed = await workflow.invoke("workflow.resume", run_id="run-1", trace=True)
        rerun = await workflow.invoke("workflow.rerun_step", run_id="run-1", step_name="write")
        return listed, activated, called, started, status, resumed, rerun

    listed, activated, called, started, status, resumed, rerun = asyncio.run(scenario())

    assert listed[0]["name"] == "demo"
    assert activated == "active:demo"
    assert called == {"name": "search", "arguments": {"query": "runtime"}}
    assert started == "started:draft"
    assert status == {"run_id": "run-1"}
    assert resumed == {"resumed": "run-1", "trace": True}
    assert rerun == {"rerun": "run-1", "step": "write"}
