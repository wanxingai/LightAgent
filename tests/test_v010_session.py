import json

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
