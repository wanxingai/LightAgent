"""Offline, copy-only history migration and rollback bundles.

All writers must be stopped by the host. Bundles preserve historical authority;
they never import backend code, replay Jobs or re-sign research profiles.
"""

from contextlib import ExitStack, closing, contextmanager
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import stat

from .job_lifecycle import ACTIVE, expired, status_of


def _digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def _files(root, *, ignore_sqlite_sidecars=False):
    files = []
    for path in sorted(root.rglob("*")):
        base = next((Path(str(path)[:-len(s)]) for s in ("-wal", "-shm", "-journal") if str(path).endswith(s)), None)
        sidecar = ignore_sqlite_sidecars and base is not None and base.is_file() and _is_sqlite(base)
        try:
            mode = path.lstat().st_mode
        except FileNotFoundError:
            if sidecar:
                continue
            raise
        if stat.S_ISLNK(mode) or not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
            raise ValueError("history source contains a symlink or special file")
        if sidecar:
            continue
        if path.is_file():
            files.append(path)
    return files


def _is_sqlite(path):
    with path.open("rb") as stream:
        return stream.read(16) == b"SQLite format 3\x00"


def _connect(path):
    return sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=1)


def _logical_digest(connection):
    value = list(connection.iterdump())
    return hashlib.sha256(json.dumps(value, ensure_ascii=False).encode()).hexdigest()


@contextmanager
def _offline(databases):
    from .backends import BackendSessionStore
    with ExitStack() as stack:
        for path in databases:
            with closing(_connect(path)) as connection:
                names = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                if {"sessions", "session_events"} <= names:
                    latest = {}
                    for row in connection.execute("SELECT payload FROM session_events ORDER BY session_id,sequence"):
                        event = json.loads(row[0])
                        job = event.get("data", {}).get("job")
                        if event.get("type", "").startswith("job.") and isinstance(job, dict):
                            latest[job["job_id"]] = job
                    if any(status_of(job) in ACTIVE and job.get("lease_expires_at") and not expired(job) for job in latest.values()):
                        raise RuntimeError("history contains a live Job lease; stop/drain its owner first")
                if {"records", "events"} <= names:
                    bindings = BackendSessionStore(path.parent / "bindings")
                    stack.enter_context(bindings.lock("supervisor", "main"))
                    for row in connection.execute("SELECT body FROM records WHERE kind='job'"):
                        job = json.loads(row[0])
                        if job["status"] in ("launching", "running", "uncertain"):
                            stack.enter_context(bindings.lock("job", job["id"]))
        yield


class HistoryBundle:
    """Create immutable offline evidence, then restore into a new directory."""

    @staticmethod
    def capture(source, destination, *, quiescent=False):
        if quiescent is not True:
            raise RuntimeError("stop all writers and explicitly confirm quiescent=True")
        source = Path(source).expanduser().resolve(strict=True)
        destination = Path(destination).expanduser().absolute()
        if not source.is_dir() or destination.exists() or source == destination or source in destination.resolve().parents:
            raise ValueError("bundle destination must be new and outside the source")
        files = _files(source, ignore_sqlite_sidecars=True)
        databases = [p for p in files if _is_sqlite(p)]
        sidecars = {str(p) + suffix for p in databases for suffix in ("-wal", "-shm", "-journal")}
        with _offline(databases):
            files = [p for p in _files(source, ignore_sqlite_sidecars=True) if str(p) not in sidecars]
            before = {p.relative_to(source).as_posix(): _digest(p) for p in files if p not in databases}
            database_digests = {}
            for path in databases:
                with closing(_connect(path)) as connection:
                    database_digests[path] = _logical_digest(connection)
            destination.mkdir(mode=0o700, parents=True, exist_ok=False)
            try:
                payload = destination / "payload"
                payload.mkdir(mode=0o700)
                directories = [p.relative_to(source).as_posix() for p in sorted(source.rglob("*")) if p.is_dir()]
                for directory in directories:
                    (payload / directory).mkdir(parents=True, exist_ok=True, mode=0o700)
                for path in files:
                    target = payload / path.relative_to(source)
                    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                    if path in databases:
                        with closing(_connect(path)) as old, closing(sqlite3.connect(target)) as new:
                            previous = _logical_digest(old)
                            old.backup(new)
                            if previous != _logical_digest(new) or previous != _logical_digest(old):
                                raise RuntimeError("history changed during SQLite backup")
                            if new.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                                raise ValueError("SQLite integrity check failed")
                            # Seal a standalone backup, not live WAL/SHM files.
                            new.execute("PRAGMA journal_mode=DELETE")
                    else:
                        shutil.copyfile(path, target)
                    target.chmod(0o600)
                after = {p.relative_to(source).as_posix(): _digest(p) for p in _files(source, ignore_sqlite_sidecars=True)
                         if str(p) not in sidecars and p not in databases}
                if before != after:
                    raise RuntimeError("history files changed during backup")
                if directories != [p.relative_to(source).as_posix() for p in sorted(source.rglob("*")) if p.is_dir()]:
                    raise RuntimeError("history directories changed during backup")
                for path, expected in database_digests.items():
                    with closing(_connect(path)) as connection:
                        if _logical_digest(connection) != expected:
                            raise RuntimeError("history database changed during backup")
                for directory in payload.rglob("*"):
                    if directory.is_dir():
                        directory.chmod(0o700)
                entries = {p.relative_to(payload).as_posix(): _digest(p) for p in _files(payload)}
                manifest = dict(schema_version=1, files=entries, directories=directories)
                manifest_path = destination / "manifest.json"
                manifest_path.write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")
                manifest_path.chmod(0o600)
                return manifest
            except BaseException:
                shutil.rmtree(destination)
                raise

    @staticmethod
    def verify(bundle):
        bundle = Path(bundle).expanduser().resolve(strict=True)
        if (bundle / "manifest.json").is_symlink() or (bundle / "payload").is_symlink():
            raise ValueError("bundle symlinks are forbidden")
        if not (bundle / "payload").is_dir():
            raise ValueError("history payload is missing")
        manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
        if manifest.get("schema_version") != 1 or not isinstance(manifest.get("files"), dict):
            raise ValueError("unsupported history bundle")
        actual = {p.relative_to(bundle / "payload").as_posix(): _digest(p) for p in _files(bundle / "payload")}
        if actual != manifest["files"]:
            raise ValueError("history bundle digest mismatch")
        directories = [p.relative_to(bundle / "payload").as_posix()
                       for p in sorted((bundle / "payload").rglob("*")) if p.is_dir()]
        if directories != manifest.get("directories"):
            raise ValueError("history bundle directory mismatch")
        return manifest

    @staticmethod
    def restore(bundle, destination):
        """Rollback is a fresh copy, never an overwrite of possibly live data."""
        manifest = HistoryBundle.verify(bundle)
        bundle = Path(bundle).resolve()
        destination = Path(destination).expanduser().absolute()
        if destination.exists() or destination.is_symlink() or bundle in destination.resolve().parents:
            raise ValueError("restore destination must be new and outside the bundle")
        try:
            shutil.copytree(bundle / "payload", destination)
            actual = {p.relative_to(destination).as_posix(): _digest(p) for p in _files(destination)}
            if actual != manifest["files"]:
                raise ValueError("history changed during restore")
            return destination
        except BaseException:
            if destination.exists():
                shutil.rmtree(destination)
            raise
