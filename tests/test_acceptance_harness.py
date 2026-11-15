import importlib.util
import json
from pathlib import Path
import sqlite3
import subprocess

import pytest


def module(name):
    path = Path(__file__).with_name("acceptance") / (name + ".py")
    spec = importlib.util.spec_from_file_location("acceptance_" + name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def test_junit_summary_and_unexpected_skips_fail_closed(tmp_path):
    verify = module("verify")
    path = tmp_path / "junit.xml"
    path.write_text('<testsuites><testsuite tests="3" failures="0" errors="0" skipped="1">'
                    '<testcase/><testcase/><testcase><skipped message="missing Node"/></testcase>'
                    '</testsuite></testsuites>')
    summary = verify.junit_summary(path)
    assert summary["passed"] == 2
    with pytest.raises(RuntimeError, match="unexpected skips"):
        verify.require_complete(summary)
    summary["skip_reasons"] = []
    verify.require_complete(summary)
    summary["tests"] = 0
    with pytest.raises(RuntimeError):
        verify.require_complete(summary)


def test_snapshot_excludes_local_credentials_examples_and_generated_files(tmp_path):
    matrix = module("clean_matrix")
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    (root / "LightAgent").mkdir()
    (root / "LightAgent/core.py").write_text("# public framework\n")
    (root / "LightAgent/private.bak").write_text("do not copy")
    (root / "LightAgent/.DS_Store").write_text("do not copy platform cache")
    (root / ".env").write_text("do not copy")
    research = tmp_path / "LightResearch"
    research.mkdir()
    (research / "pyproject.toml").write_text("[project]\nname = 'LightResearch'\n")
    (research / "__init__.py").write_text("# extension\n")
    (research / ".env").write_text("do not copy")
    (research / "notes.txt").write_text("do not copy")
    wheel = tmp_path / "lightresearch-0.1.0.dev0-py3-none-any.whl"
    wheel.write_bytes(b"wheel fixture")
    (root / "tests").mkdir()
    for name in ("test_mcp_client_manager.py", "test_tool_schema_validation.py"):
        (root / "tests" / name).write_text("# tracked fixture\n")
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "-c", "user.name=Acceptance", "-c", "user.email=test@example.invalid",
                    "commit", "-qm", "fixture"], check=True)
    (root / "tests/example.py").write_text("do not copy local business examples")
    destination = tmp_path / "snapshot"
    assert len(matrix.snapshot(root, destination)) == 64
    assert (destination / "LightAgent/core.py").exists()
    assert not (destination / ".env").exists()
    assert not (destination / "LightAgent/private.bak").exists()
    assert not (destination / "LightAgent/.DS_Store").exists()
    assert not (destination / "tests/example.py").exists()
    assert not (destination / "research-input").exists()
    assert not (destination / "LightResearch").exists()
    with pytest.raises(ValueError):
        matrix.snapshot(root, destination)

    staged = tmp_path / "source-snapshot"
    matrix.snapshot(root, staged, research_source=research)
    assert {p.name for p in (staged / "research-input/source").iterdir()} == {"pyproject.toml", "__init__.py"}
    manifest = json.loads((tmp_path / "snapshot.json").read_text())["files"]
    assert "research-input/source/__init__.py" in manifest
    assert not (research / "build").exists()

    staged = tmp_path / "wheel-snapshot"
    matrix.snapshot(root, staged, research_wheel=wheel)
    assert (staged / "research-input/wheel" / wheel.name).read_bytes() == wheel.read_bytes()
    with pytest.raises(ValueError, match="either"):
        matrix.snapshot(root, tmp_path / "ambiguous", research_source=research, research_wheel=wheel)


def test_wheel_directory_must_have_one_wheel(tmp_path):
    verify = module("verify")
    with pytest.raises(ValueError, match="found 0"):
        verify.resolve_wheel(tmp_path)
    wheel = tmp_path / "lightresearch-0.1.0.dev0-py3-none-any.whl"
    wheel.touch()
    assert verify.resolve_wheel(tmp_path) == wheel
    (tmp_path / "extra.whl").touch()
    with pytest.raises(ValueError, match="found 2"):
        verify.resolve_wheel(tmp_path)


def test_python310_sqlite_error_code_names_are_optional(monkeypatch):
    from LightAgent.persistent.jobs import _database_busy
    monkeypatch.delattr(sqlite3, "SQLITE_BUSY", raising=False)
    monkeypatch.delattr(sqlite3, "SQLITE_LOCKED", raising=False)
    for code, expected in ((5, True), (6, True), (5 | 512, True), (10, False)):
        error = sqlite3.OperationalError("redacted")
        error.sqlite_errorcode = code
        assert _database_busy(error) is expected


def test_short_soak_is_only_a_pilot_and_checks_real_crash_recovery(tmp_path):
    report = module("soak").run_soak(tmp_path / "pilot", seconds=.1, concurrency=2,
                                      interval=0, fault_interval=60, min_rounds=1)
    assert report["status"] == "passed" and not report["release_gate"]
    assert report["completed"] >= 2
    assert report["crashes_reconciled"] == 1


def test_soak_failure_still_persists_a_failed_report(tmp_path, monkeypatch):
    soak = module("soak")
    def fail(supervisor):
        supervisor.errors.append(RuntimeError("injected supervisor failure"))
    monkeypatch.setattr(soak.Supervisor, "start", fail)
    with pytest.raises(RuntimeError):
        soak.run_soak(tmp_path / "failed", seconds=.1, concurrency=1, min_rounds=1)
    report = json.loads((tmp_path / "failed/report.json").read_text())
    assert report["status"] == "failed"
    assert "batch failed to settle" in report["error"]
