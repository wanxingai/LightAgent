"""Offline signed Provider approval. Demo keys are ephemeral, never production keys."""
import asyncio
import base64
from pathlib import Path
from tempfile import TemporaryDirectory
import time

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from LightAgent import (AttestedProvider, BaseCapabilityProvider, CapabilityGate, CapabilityRegistry,
    CapabilitySpec, ControlStore, ProviderAttestation, ProviderTrustStore, SecurityContext, TrustError)


class LocalProvider(BaseCapabilityProvider):
    name, version = "local-fixture", "1"
    def __init__(self):
        super().__init__([CapabilitySpec("fixture.read", read=True)])
    async def invoke(self, capability, **arguments):
        return "reviewed local data"


async def main(root):
    artifact = root / "reviewed-bundle"
    artifact.mkdir()
    (artifact / "instructions.md").write_text("Local fixture; no automatic policy grants.")
    provider = LocalProvider()
    key = Ed25519PrivateKey.generate()
    public = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    attestation = ProviderAttestation.inspect(provider, artifact, publisher="demo", key_id="test-key",
        kind="provider", release_sequence=1, issued_at=time.time() - 1, expires_at=time.time() + 300)
    signature = base64.b64encode(key.sign(attestation.signing_bytes())).decode()
    trust = ProviderTrustStore(ControlStore(root / "private-control"), public_keys={("demo", "test-key"): public})
    # Signing is not permission: the host must separately approve the inspected digest.
    trust.approve(provider, artifact, attestation, signature,
                  expected_digest=attestation.digest, note="Offline host review")
    registry = CapabilityRegistry()
    wrapped = AttestedProvider(provider, directory=artifact, attestation=attestation, signature=signature,
                               trust_store=trust)
    registry.register(wrapped)
    gate = CapabilityGate(registry)
    print(await gate.invoke("fixture.read", {}, SecurityContext()))
    (artifact / "instructions.md").write_text("Changed after approval")
    try:
        await gate.invoke("fixture.read", {}, SecurityContext())
    except TrustError:
        print("Changed bundle rejected; a new signed release and host approval are required.")
    else:
        raise AssertionError("changed content was unexpectedly accepted")


if __name__ == "__main__":
    with TemporaryDirectory() as directory:
        asyncio.run(main(Path(directory)))
