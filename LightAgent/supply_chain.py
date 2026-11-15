"""Host-approved, signed Provider bindings. No package loading or self-trust."""
from copy import deepcopy
from dataclasses import asdict, dataclass
import base64
import hashlib
import inspect
import json
import math
import os
from pathlib import Path
import re
import stat
import time

from .capabilities import ProviderHealth
from .security import ProviderManifest, canonical_digest

SUPPLY_CHAIN_SCHEMA_VERSION = 1
_LABEL = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")


class TrustError(PermissionError):
    pass


def artifact_digest(directory):
    """Bounded manifest of every regular file; nothing is implicitly excluded."""
    if os.name != "posix":
        raise TrustError("signed local artifact inspection currently requires POSIX")
    root = Path(directory).expanduser().absolute()
    if root.is_symlink() or not root.is_dir():
        raise TrustError("artifact root must be a real directory")
    entries, total, count = [], 0, 0
    def names_at(directory_fd):
        names = []
        with os.scandir(directory_fd) as iterator:
            for entry in iterator:
                names.append(entry.name)
                if len(names) > 2048:
                    raise TrustError("artifact entry budget exceeded")
        return sorted(names)

    def walk(directory_fd, prefix, depth):
        nonlocal total, count
        if depth > 32:
            raise TrustError("artifact directory depth exceeded")
        names = names_at(directory_fd)
        for name in names:
            count += 1
            if count > 2048:
                raise TrustError("artifact entry budget exceeded")
            before = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
            relative = prefix + name
            if stat.S_ISDIR(before.st_mode):
                child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory_fd)
                try:
                    walk(child, relative + "/", depth + 1)
                finally:
                    os.close(child)
            elif stat.S_ISREG(before.st_mode) and before.st_nlink == 1:
                fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory_fd)
                with os.fdopen(fd, "rb") as stream:
                    info = os.fstat(stream.fileno())
                    if not stat.S_ISREG(info.st_mode) or info.st_size > 2 * 1024 * 1024:
                        raise TrustError("artifact file exceeds its regular-file budget")
                    data = stream.read(2 * 1024 * 1024 + 1)
                    after = os.fstat(stream.fileno())
                    if (info.st_ino, info.st_mtime_ns, info.st_size) != (after.st_ino, after.st_mtime_ns, after.st_size):
                        raise TrustError("artifact changed during inspection")
                total += len(data)
                entries.append([relative, hashlib.sha256(data).hexdigest()])
                if len(data) > 2 * 1024 * 1024 or len(entries) > 1024 or total > 16 * 1024 * 1024:
                    raise TrustError("artifact exceeds its aggregate budget")
            else:
                raise TrustError("artifact contains a symlink, hardlink or special file")
            after = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
            if (before.st_ino, before.st_mtime_ns, before.st_size) != (after.st_ino, after.st_mtime_ns, after.st_size):
                raise TrustError("artifact changed during inspection")
        if names != names_at(directory_fd):
            raise TrustError("artifact entries changed during inspection")
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        walk(fd, "", 0)
    finally:
        os.close(fd)
    if not entries:
        raise TrustError("empty artifacts cannot be approved")
    return canonical_digest(entries)


@dataclass(frozen=True)
class ProviderAttestation:
    publisher: str
    key_id: str
    kind: str
    name: str
    version: str
    release_sequence: int
    artifact_digest: str
    provider_digest: str
    issued_at: float
    expires_at: float
    schema_version: int = SUPPLY_CHAIN_SCHEMA_VERSION

    def __post_init__(self):
        if self.schema_version != 1 or type(self.schema_version) is not int:
            raise TrustError("unsupported attestation schema")
        if self.kind not in {"skill", "mcp", "provider"}:
            raise TrustError("unsupported artifact kind")
        if any(not isinstance(v, str) or not _LABEL.fullmatch(v) for v in
               (self.publisher, self.key_id, self.name, self.version)):
            raise TrustError("invalid publisher or Provider identity")
        if type(self.release_sequence) is not int or self.release_sequence < 1:
            raise TrustError("release sequence must be a positive integer")
        if any(not isinstance(v, str) or not re.fullmatch(r"[a-f0-9]{64}", v)
               for v in (self.artifact_digest, self.provider_digest)):
            raise TrustError("invalid attestation digest")
        if any(type(v) not in (int, float) or not math.isfinite(v) for v in (self.issued_at, self.expires_at)):
            raise TrustError("invalid attestation lifetime")
        if not 0 <= self.issued_at < self.expires_at:
            raise TrustError("invalid attestation lifetime")

    def signing_bytes(self):
        return b"LightAgent.ProviderAttestation.v1\x00" + json.dumps(
            asdict(self), sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()

    @property
    def digest(self):
        return hashlib.sha256(self.signing_bytes()).hexdigest()

    @classmethod
    def inspect(cls, provider, directory, *, publisher, key_id, kind, release_sequence, issued_at, expires_at):
        manifest = ProviderManifest.from_provider(provider)
        return cls(publisher, key_id, kind, manifest.name, manifest.version, release_sequence,
                   artifact_digest(directory), canonical_digest(manifest.to_dict()), issued_at, expires_at)


class ProviderTrustStore:
    """Explicit host approval and revocation in the existing transactional store."""

    def __init__(self, store, *, public_keys):
        self.store = store
        self.public_keys = dict(public_keys)  # (publisher, key_id) -> raw Ed25519 public bytes

    @staticmethod
    def _key(attestation):
        return canonical_digest([attestation.publisher, attestation.kind, attestation.name])

    def _verify(self, provider, directory, attestation, signature, *, db=None):
        if not isinstance(attestation, ProviderAttestation):
            raise TrustError("a typed ProviderAttestation is required")
        now = time.time()
        if not attestation.issued_at <= now < attestation.expires_at:
            raise TrustError("attestation expired or not yet valid")
        key_id = canonical_digest([attestation.publisher, attestation.key_id])
        if self.store.get("publisher_revocation", key_id, db):
            raise TrustError("publisher key has been revoked")
        raw = self.public_keys.get((attestation.publisher, attestation.key_id))
        if not isinstance(raw, bytes) or len(raw) != 32:
            raise TrustError("publisher key is not trusted")
        try:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
            if not isinstance(signature, str) or len(signature) > 128:
                raise ValueError("signature must be bounded base64")
            decoded = base64.b64decode(signature, validate=True)
            if len(decoded) != 64:
                raise ValueError("invalid signature length")
            Ed25519PublicKey.from_public_bytes(raw).verify(decoded, attestation.signing_bytes())
        except ImportError as error:
            raise TrustError("signed Providers require the optional cryptography dependency") from error
        except Exception as error:
            raise TrustError("invalid Provider signature") from error
        manifest = ProviderManifest.from_provider(provider)
        if (manifest.name != attestation.name or manifest.version != attestation.version
                or canonical_digest(manifest.to_dict()) != attestation.provider_digest):
            raise TrustError("Provider configuration/capabilities changed; host reapproval required")
        if artifact_digest(directory) != attestation.artifact_digest:
            raise TrustError("artifact content changed; host reapproval required")

    def approve(self, provider, directory, attestation, signature, *, expected_digest, note):
        if not isinstance(note, str) or not note.strip() or len(note.encode()) > 4096:
            raise ValueError("approval requires a bounded host note")
        if expected_digest != attestation.digest:
            raise TrustError("attestation changed since host inspection")
        with self.store.transaction() as db:
            self._verify(provider, directory, attestation, signature, db=db)
            key = self._key(attestation)
            old = self.store.get("provider_trust", key, db)
            if old and (attestation.release_sequence < old["release_sequence"] or
                        (attestation.release_sequence == old["release_sequence"] and old["digest"] != attestation.digest)):
                raise TrustError("signed release downgrade or sequence reuse rejected")
            value = dict(id=key, agent="supply-chain", digest=attestation.digest,
                         release_sequence=attestation.release_sequence, active=True,
                         directory=str(Path(directory).resolve()),
                         revision=old["revision"] if old else 0)
            self.store.put("provider_trust", value, db)
            self.store.event("supply-chain", "provider.trusted",
                             dict(identity=key, digest=attestation.digest, note_digest=canonical_digest(note)), db)

    def verify(self, provider, directory, attestation, signature):
        with self.store.read_transaction() as db:
            self._verify(provider, directory, attestation, signature, db=db)
            record = self.store.get("provider_trust", self._key(attestation), db)
            if not record or not record["active"] or record["digest"] != attestation.digest:
                raise TrustError("Provider release requires explicit host approval")
            if record["directory"] != str(Path(directory).resolve()):
                raise TrustError("artifact location changed; host reapproval required")

    def revoke(self, attestation):
        with self.store.transaction() as db:
            value = self.store.get("provider_trust", self._key(attestation), db)
            if value:
                if value["digest"] != attestation.digest:
                    raise TrustError("stale release revocation rejected")
                value["active"] = False
                self.store.put("provider_trust", value, db)
            self.store.event("supply-chain", "provider.revoked", {"identity": self._key(attestation)}, db)

    def revoke_key(self, publisher, key_id):
        with self.store.transaction() as db:
            key = canonical_digest([publisher, key_id])
            if not self.store.get("publisher_revocation", key, db):
                self.store.put("publisher_revocation", dict(id=key, agent="supply-chain"), db)
                self.store.event("supply-chain", "publisher.revoked", {"identity": key}, db)


class AttestedProvider:
    """Wrap trusted host code; manifests cannot select imports or grant policy."""

    def __init__(self, provider, *, directory, attestation, signature, trust_store):
        self._provider = provider
        self.directory = Path(directory).absolute()
        self.attestation, self.signature, self.trust_store = attestation, signature, trust_store

    @property
    def name(self):
        return self._provider.name

    @property
    def version(self):
        return self._provider.version

    @property
    def capabilities(self):
        return self._provider.capabilities

    @property
    def config(self):
        return self._provider.config

    def _check(self):
        self.trust_store.verify(self._provider, self.directory, self.attestation, self.signature)

    async def _call(self, method, *args, **kwargs):
        result = getattr(self._provider, method)(*args, **kwargs)
        return await result if inspect.isawaitable(result) else result

    async def mount(self, context):
        self._check()
        return await self._call("mount", context)

    async def start(self):
        self._check()
        return await self._call("start")

    async def invoke(self, capability, **arguments):
        self._check()
        if capability not in self.capabilities:
            raise LookupError(capability)
        return await self._call("invoke", capability, **arguments)

    async def health(self):
        try:
            self._check()
        except (PermissionError, ValueError, OSError):
            return ProviderHealth(False, "untrusted", "Provider requires host reapproval")
        return await self._call("health")

    async def reload(self, config):
        self._check()
        if config != self.config:
            raise TrustError("configuration changes require a new, host-approved Provider instance")
        return await self._call("reload", deepcopy(config))

    async def stop(self):
        return await self._call("stop")

    async def unmount(self):
        return await self._call("unmount")
