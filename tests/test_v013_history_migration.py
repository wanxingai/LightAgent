import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3

import pytest

from LightAgent import AgentRuntime, Session, SqliteSessionStore, SequenceConflict
from LightAgent.backends import BackendError, BackendSessionStore
from LightAgent.history import HistoryBundle
from LightAgent.persistent import ControlStore


def make_legacy(tmp_path):
    root = tmp_path / "old"
    root.mkdir()
    store = SqliteSessionStore(root / "sessions.sqlite3")
    session = Session(session_id="legacy")
    session.append("message.received", {"content": "retained input"})
    store.create(session)
    with store.transaction() as db:
        db.execute("DELETE FROM session_anchors")
        db.execute("DELETE FROM session_integrity")
    control = ControlStore(root / "control")
    with control.transaction() as db:
        control.put("version", dict(id="v", agent="a", authority={"digest": "pinned-old"}), db)
    (root / "artifact.txt").write_text("verified evidence", encoding="utf-8")
    return root, store


def test_copy_migration_anchors_only_after_explicit_inspection_and_rolls_back(tmp_path):
    root, old = make_legacy(tmp_path)
    original = old.get("legacy").to_dict()
    bundle = tmp_path / "backup"
    HistoryBundle.capture(root, bundle, quiescent=True)
    candidate = HistoryBundle.restore(bundle, tmp_path / "candidate")
    upgraded = SqliteSessionStore(candidate / "sessions.sqlite3")
    assert upgraded.integrity("legacy")["status"] == "legacy_unanchored"
    digest = upgraded.history_digest("legacy")
    assert upgraded.anchor_legacy("legacy", expected_digest=digest, note="Host inspected the frozen backup")["status"] == "verified"
    assert upgraded.get("legacy").to_dict() == original
    upgraded.append_if_sequence("legacy", "new.event", {})
    assert old.get("legacy").to_dict() == original
    assert old.integrity("legacy")["status"] == "legacy_unanchored"
    rolled_back = HistoryBundle.restore(bundle, tmp_path / "rollback")
    with sqlite3.connect(rolled_back / "sessions.sqlite3") as db:
        assert db.execute("SELECT count(*) FROM session_anchors").fetchone()[0] == 0
    assert SqliteSessionStore(rolled_back / "sessions.sqlite3").get("legacy").to_dict() == original
    assert ControlStore(rolled_back / "control").get("version", "v")["authority"]["digest"] == "pinned-old"
    assert (rolled_back / "artifact.txt").read_text() == "verified evidence"


def test_anchor_rejects_changed_history_and_cannot_reanchor(tmp_path):
    _, store = make_legacy(tmp_path)
    stale = store.history_digest("legacy")
    store.append_if_sequence("legacy", "new", {})
    with pytest.raises(SequenceConflict, match="changed"):
        store.anchor_legacy("legacy", expected_digest=stale, note="inspected")
    assert store.integrity("legacy")["status"] == "legacy_unanchored"
    digest = store.history_digest("legacy")
    store.anchor_legacy("legacy", expected_digest=digest, note="inspected")
    with pytest.raises(SequenceConflict, match="already anchored"):
        store.anchor_legacy("legacy", expected_digest=digest, note="do not overwrite")
    with store.transaction() as db:
        assert db.execute("SELECT source_digest FROM session_migrations").fetchone()[0] == digest


def test_bundle_corruption_or_extra_files_prevents_restore(tmp_path):
    root, _ = make_legacy(tmp_path)
    bundle = tmp_path / "backup"
    HistoryBundle.capture(root, bundle, quiescent=True)
    (bundle / "payload" / "injected.txt").write_text("unexpected")
    with pytest.raises(ValueError, match="digest"):
        HistoryBundle.restore(bundle, tmp_path / "rollback")
    assert not (tmp_path / "rollback").exists()


def test_backup_requires_offline_confirmation_and_never_overwrites(tmp_path):
    root, _ = make_legacy(tmp_path)
    with pytest.raises(RuntimeError, match="quiescent"):
        HistoryBundle.capture(root, tmp_path / "backup")
    with pytest.raises(ValueError):
        HistoryBundle.capture(root, root / "nested", quiescent=True)
    HistoryBundle.capture(root, tmp_path / "backup", quiescent=True)
    with pytest.raises(ValueError):
        HistoryBundle.capture(root, tmp_path / "backup", quiescent=True)
    with pytest.raises(ValueError):
        HistoryBundle.restore(tmp_path / "backup", root)
    with pytest.raises(ValueError):
        HistoryBundle.restore(tmp_path / "backup", tmp_path / "backup" / "recursive")


def test_live_supervisor_lock_prevents_backup(tmp_path):
    root, _ = make_legacy(tmp_path)
    with BackendSessionStore(root / "control" / "bindings").lock("supervisor", "main"):
        with pytest.raises(BackendError, match="busy"):
            HistoryBundle.capture(root, tmp_path / "backup", quiescent=True)
    assert not (tmp_path / "backup").exists()


def test_backup_rejects_symlinks(tmp_path):
    root, _ = make_legacy(tmp_path)
    (root / "link").symlink_to(root / "artifact.txt")
    with pytest.raises(ValueError, match="symlink"):
        HistoryBundle.capture(root, tmp_path / "backup", quiescent=True)


def test_failed_copy_cleans_only_new_destination(tmp_path, monkeypatch):
    import LightAgent.history as history
    root, _ = make_legacy(tmp_path)
    def fail(*args):
        raise OSError("injected disk failure")
    monkeypatch.setattr(history.shutil, "copyfile", fail)
    with pytest.raises(OSError):
        HistoryBundle.capture(root, tmp_path / "backup", quiescent=True)
    assert not (tmp_path / "backup").exists()
    assert (root / "artifact.txt").exists()


def test_legacy_anchor_detects_later_tampering(tmp_path):
    _, store = make_legacy(tmp_path)
    store.anchor_legacy("legacy", expected_digest=store.history_digest("legacy"), note="reviewed backup")
    with store.transaction() as db:
        row = db.execute("SELECT payload FROM session_events").fetchone()
        event = json.loads(row[0])
        event["data"]["content"] = "changed"
        db.execute("UPDATE session_events SET payload=?", (json.dumps(event),))
    with pytest.raises(SequenceConflict, match="integrity"):
        store.get("legacy")


def test_live_runtime_lease_prevents_offline_backup(tmp_path):
    root, store = make_legacy(tmp_path)
    session = store.get("legacy")
    session.append("job.started", {"job": dict(job_id="live", status="running",
        lease_expires_at=(datetime.now(timezone.utc) + timedelta(seconds=30)).isoformat())})
    store.save(session)
    with pytest.raises(RuntimeError, match="live Job lease"):
        HistoryBundle.capture(root, tmp_path / "backup", quiescent=True)
