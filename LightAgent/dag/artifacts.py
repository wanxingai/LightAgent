"""Content-addressed local artifact storage for verified DAG outputs."""

from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path
from typing import Any, Iterable, Protocol

from ..security import SecurityContext
from .models import ArtifactManifest, DAGRun, DAGTask, TaskAttempt
from .store import DAGError


class ArtifactStore(Protocol):
    def stage(
            self,
            content: bytes | str,
            *,
            run: DAGRun,
            task: DAGTask,
            attempt: TaskAttempt,
            media_type: str = "text/plain",
            dependency_manifest: dict[str, list[str]] | None = None,
    ) -> ArtifactManifest:
        ...

    def read(
            self,
            manifest: ArtifactManifest,
            context: SecurityContext,
            *,
            require_published: bool = True,
    ) -> bytes:
        ...


class LocalArtifactStore:
    """Write immutable blobs first; SQLite controls staged/published authority."""

    def __init__(self, root: str | Path, *, max_artifact_bytes: int = 10 * 1024 * 1024):
        if max_artifact_bytes <= 0:
            raise ValueError("max_artifact_bytes must be positive")
        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.max_artifact_bytes = max_artifact_bytes

    def stage(
            self,
            content: bytes | str,
            *,
            run: DAGRun,
            task: DAGTask,
            attempt: TaskAttempt,
            media_type: str = "text/plain",
            dependency_manifest: dict[str, list[str]] | None = None,
    ) -> ArtifactManifest:
        payload = content.encode("utf-8") if isinstance(content, str) else bytes(content)
        if len(payload) > self.max_artifact_bytes:
            raise DAGError("BUDGET-EXHAUSTED", "artifact exceeds max_artifact_bytes")
        digest = hashlib.sha256(payload).hexdigest()
        relative = Path(run.tenant_id) / run.project_id / digest[:2] / digest
        destination = self._resolve(relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            if destination.is_symlink() or self._digest_file(destination) != digest:
                raise DAGError("ARTIFACT-INTEGRITY", "existing artifact bytes do not match the content hash")
        else:
            descriptor, temporary_name = tempfile.mkstemp(prefix=f".{digest}.", dir=destination.parent)
            temporary = Path(temporary_name)
            try:
                with os.fdopen(descriptor, "wb") as stream:
                    stream.write(payload)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary, destination)
            finally:
                if temporary.exists():
                    temporary.unlink()
        return ArtifactManifest(
            run_id=run.run_id,
            task_id=task.spec.task_id,
            attempt_id=attempt.attempt_id,
            tenant_id=run.tenant_id,
            project_id=run.project_id,
            content_hash=digest,
            relative_blob_path=relative.as_posix(),
            media_type=media_type,
            byte_size=len(payload),
            contract_hash=task.spec.contract_hash,
            dependency_manifest=dependency_manifest or {},
        )

    def read(
            self,
            manifest: ArtifactManifest,
            context: SecurityContext,
            *,
            require_published: bool = True,
    ) -> bytes:
        if context.tenant_id != manifest.tenant_id or context.project_id != manifest.project_id:
            raise PermissionError("artifact is outside the tenant/project security context")
        if require_published and manifest.state != "published":
            raise PermissionError("staged artifacts are not readable as trusted results")
        path = self._resolve(Path(manifest.relative_blob_path))
        if not path.is_file() or path.is_symlink():
            raise DAGError("ARTIFACT-INTEGRITY", "artifact blob is missing or not a regular file")
        payload = path.read_bytes()
        if len(payload) != manifest.byte_size or hashlib.sha256(payload).hexdigest() != manifest.content_hash:
            raise DAGError("ARTIFACT-INTEGRITY", "artifact content failed integrity verification")
        return payload

    def check_integrity(self, manifest: ArtifactManifest) -> bool:
        try:
            path = self._resolve(Path(manifest.relative_blob_path))
            return (
                path.is_file()
                and not path.is_symlink()
                and path.stat().st_size == manifest.byte_size
                and self._digest_file(path) == manifest.content_hash
            )
        except (OSError, DAGError):
            return False

    def remove_orphans(self, manifests: Iterable[ArtifactManifest], *, dry_run: bool = True) -> list[str]:
        referenced = {manifest.relative_blob_path for manifest in manifests}
        orphans = []
        for path in self.root.rglob("*"):
            if not path.is_file() or path.is_symlink():
                continue
            relative = path.relative_to(self.root).as_posix()
            if relative in referenced:
                continue
            orphans.append(relative)
            if not dry_run:
                path.unlink()
        return sorted(orphans)

    def _resolve(self, relative: Path) -> Path:
        if relative.is_absolute() or ".." in relative.parts:
            raise DAGError("ARTIFACT-INTEGRITY", "artifact path must stay within the store root")
        path = (self.root / relative).resolve()
        try:
            path.relative_to(self.root)
        except ValueError as exc:
            raise DAGError("ARTIFACT-INTEGRITY", "artifact path escaped the store root") from exc
        return path

    @staticmethod
    def _digest_file(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()


__all__ = ["ArtifactStore", "LocalArtifactStore"]
