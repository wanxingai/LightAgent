import asyncio

from LightAgent import (
    CapabilityRegistry,
    InMemorySessionStore,
    RetrievalDocument,
    RuntimeContext,
    Session,
    SessionSearchProvider,
    SqliteFTSRetrievalProvider,
)


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
