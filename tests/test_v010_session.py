import json
import sqlite3

import pytest

from LightAgent import (
    ContextBudget,
    ContextCompactor,
    ContextProjector,
    InMemorySessionStore,
    JsonlSessionStore,
    Session,
    SessionEvent,
    SessionMigrationRegistry,
    SqliteSessionStore,
)


@pytest.mark.parametrize("store_factory", [
    lambda path: InMemorySessionStore(),
    lambda path: JsonlSessionStore(path / "jsonl"),
    lambda path: SqliteSessionStore(path / "sessions.sqlite3"),
])
def test_session_store_round_trip_and_replay(tmp_path, store_factory):
    store = store_factory(tmp_path)
    session = Session(session_id="session-1", metadata={"api_key": "secret"})
    session.append("turn.started", {}, turn_id="turn-1")
    session.append("message.received", {"role": "user", "content": "hello"}, turn_id="turn-1")
    session.append("turn.completed", {}, turn_id="turn-1")
    store.create(session)

    restored = store.get("session-1")

    assert restored is not None
    assert restored.metadata["api_key"] == "[redacted]"
    assert restored.replay().completed_turns == ["turn-1"]
    assert [event.sequence for event in restored.events] == [1, 2, 3]


def test_incomplete_turn_and_corrupt_sequence_are_detected():
    session = Session(session_id="session-1")
    session.append("turn.started", {}, turn_id="turn-1")
    assert session.replay().incomplete_turns == ["turn-1"]

    payload = session.to_dict()
    payload["events"][0]["sequence"] = 2
    with pytest.raises(ValueError, match="sequence gap"):
        Session.from_dict(payload)


def test_fork_preserves_projectable_events_without_reusing_ids():
    session = Session(session_id="source")
    source = session.append("message.received", {"role": "user", "content": "hello"}, turn_id="t1")
    forked = session.fork(new_session_id="fork")

    assert ContextProjector().messages(forked) == [{"role": "user", "content": "hello"}]
    imported = next(event for event in forked.events if event.type == "message.received")
    assert imported.event_id != source.event_id
    assert imported.data["source_event_id"] == source.event_id


def test_exact_model_request_can_be_reconstructed():
    session = Session(session_id="session-1")
    messages = [{"role": "system", "content": "policy"}, {"role": "user", "content": "hello"}]
    event = session.append("model.requested", {"messages": messages})

    assert ContextProjector().model_request(session, sequence=event.sequence) == messages


def test_compaction_spills_large_tool_results_and_meets_budget():
    messages = [
        {"role": "system", "content": "policy"},
        {"role": "user", "content": "first"},
        {"role": "assistant", "content": "working"},
        {"role": "tool", "content": "x" * 500},
        {"role": "user", "content": "last"},
    ]
    compactor = ContextCompactor(max_inline_tool_chars=100)
    result = compactor.compact_to_budget(
        messages,
        ContextBudget(max_tokens=100, reserved_output_tokens=10, chars_per_token=4),
    )

    assert result.spilled[0]["sha256"]
    assert result.spilled[0]["content"] == "x" * 500
    assert all(len(message.get("content", "")) < 500 for message in result.messages)


def test_migration_registry_applies_ordered_event_migration():
    registry = SessionMigrationRegistry()
    registry.register_event(0, lambda value: {**value, "schema_version": 1, "type": "message.received"})
    payload = SessionEvent(type="legacy", session_id="s").to_dict()
    payload["schema_version"] = 0

    migrated = registry.migrate_event(payload)

    assert migrated["schema_version"] == 1
    assert migrated["type"] == "message.received"


def test_jsonl_store_rejects_truncated_event(tmp_path):
    store = JsonlSessionStore(tmp_path)
    session = store.create(Session(session_id="broken"))
    path = tmp_path / "broken.jsonl"
    path.write_text(path.read_text(encoding="utf-8") + "{broken\n", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        store.get(session.session_id)


@pytest.mark.parametrize("store_factory", [
    lambda path: InMemorySessionStore(),
    lambda path: JsonlSessionStore(path / "jsonl"),
    lambda path: SqliteSessionStore(path / "sessions.sqlite3"),
])
def test_session_store_list_delete_and_duplicate_create(tmp_path, store_factory):
    store = store_factory(tmp_path)
    store.create(Session(session_id="one"))
    store.create(Session(session_id="two"))

    assert {session.session_id for session in store.list(limit=2)} == {"one", "two"}
    with pytest.raises(ValueError, match="already exists"):
        store.create(Session(session_id="one"))
    assert store.delete("one") is True
    assert store.delete("one") is False
    assert store.get("one") is None


def test_session_page_append_event_and_future_schema_validation():
    session = Session(session_id="session")
    first = session.append("one")
    session.append_event(SessionEvent(type="two", session_id="session"))

    assert [event.type for event in session.page(after=first.sequence, limit=1)] == ["two"]
    with pytest.raises(ValueError, match="limit must be at least 1"):
        session.page(limit=0)
    with pytest.raises(ValueError, match="does not match"):
        session.append_event(SessionEvent(type="bad", session_id="other"))

    payload = session.to_dict()
    payload["events"][0]["schema_version"] = 999
    with pytest.raises(ValueError, match="unsupported SessionEvent schema_version"):
        Session.from_dict(payload)


def test_in_memory_store_rejects_stale_session_save():
    store = InMemorySessionStore()
    original = Session(session_id="session")
    original.append("first")
    stale = store.create(original)
    current = store.get("session")
    current.append("second")
    store.save(current)

    with pytest.raises(ValueError, match="older event sequence"):
        store.save(stale)


def test_jsonl_atomic_save_failure_preserves_previous_session(tmp_path, monkeypatch):
    from LightAgent import session as session_module

    store = JsonlSessionStore(tmp_path)
    current = store.create(Session(session_id="atomic"))
    current.append("durable.event", {"value": 1})
    store.save(current)
    before = store.get("atomic").to_dict()
    current.append("new.event", {"value": 2})

    def fail_replace(source, destination):
        raise OSError("simulated replace failure")

    monkeypatch.setattr(session_module.os, "replace", fail_replace)
    with pytest.raises(OSError, match="simulated replace failure"):
        store.save(current)

    assert store.get("atomic").to_dict() == before


def test_sqlite_store_rejects_corrupt_persisted_event(tmp_path):
    path = tmp_path / "sessions.sqlite3"
    store = SqliteSessionStore(path)
    store.create(Session(session_id="corrupt"))
    with sqlite3.connect(path) as connection:
        connection.execute(
            "INSERT INTO session_events(session_id, sequence, event_id, payload) VALUES (?, ?, ?, ?)",
            ("corrupt", 1, "bad-event", "{not-json"),
        )

    with pytest.raises(json.JSONDecodeError):
        store.get("corrupt")


def test_jsonl_store_rejects_unsafe_session_id(tmp_path):
    store = JsonlSessionStore(tmp_path)

    with pytest.raises(ValueError, match="unsafe characters"):
        store.create(Session(session_id="../escape"))
