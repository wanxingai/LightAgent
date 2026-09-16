"""Verification protocols and deterministic callable adapters."""

from __future__ import annotations

import asyncio
import inspect
from copy import deepcopy
from typing import Any, Awaitable, Callable, Mapping, Protocol

from ..security import canonical_digest
from .models import AssuranceLevel, VerificationReport, VerificationRequest, VerificationVerdict


class Verifier(Protocol):
    key: str
    version: str

    async def verify(self, request: VerificationRequest) -> VerificationReport:
        ...


VerifierCallable = Callable[[VerificationRequest], Any | Awaitable[Any]]


class CallableVerifier:
    """Adapt a trusted deterministic callable to the Verifier protocol."""

    def __init__(
            self,
            key: str,
            function: VerifierCallable,
            *,
            version: str = "1",
            assurance_level: AssuranceLevel | str = AssuranceLevel.EXECUTABLE_CHECKS,
            timeout: float | None = None,
            config: Mapping[str, Any] | None = None,
    ):
        if not key.strip():
            raise ValueError("verifier key must not be empty")
        if timeout is not None and timeout <= 0:
            raise ValueError("verifier timeout must be positive")
        self.key = key
        self.function = function
        self.version = version
        self.assurance_level = AssuranceLevel(assurance_level)
        self.timeout = timeout
        self.config_digest = canonical_digest(config or {})

    async def verify(self, request: VerificationRequest) -> VerificationReport:
        try:
            if inspect.iscoroutinefunction(self.function):
                operation = self.function(request)
            else:
                operation = asyncio.to_thread(self.function, request)
            raw = await asyncio.wait_for(operation, self.timeout) if self.timeout else await operation
            return self._normalize(raw, request)
        except asyncio.CancelledError:
            raise
        except Exception as error:
            return self._report(
                request,
                VerificationVerdict.ERROR,
                diagnostics=[f"verifier failed: {type(error).__name__}"],
            )

    def _normalize(self, raw: Any, request: VerificationRequest) -> VerificationReport:
        if isinstance(raw, VerificationReport):
            if raw.input_snapshot_hash != request.input_snapshot_hash:
                return self._report(
                    request,
                    VerificationVerdict.ERROR,
                    diagnostics=["verifier returned a report for a different input snapshot"],
                )
            return raw
        if raw is True:
            return self._report(request, VerificationVerdict.PASS)
        if raw is False or raw is None:
            return self._report(request, VerificationVerdict.FAIL, diagnostics=["verification failed"])
        if isinstance(raw, Mapping):
            verdict = VerificationVerdict(str(raw.get("verdict", "error")))
            assurance = AssuranceLevel(str(raw.get("assurance_level", self.assurance_level.value)))
            return self._report(
                request,
                verdict,
                assurance_level=assurance,
                diagnostics=[str(item) for item in raw.get("diagnostics", [])],
                evidence_refs=[str(item) for item in raw.get("evidence_refs", [])],
            )
        return self._report(
            request,
            VerificationVerdict.ERROR,
            diagnostics=["verifier returned an unsupported result type"],
        )

    def _report(
            self,
            request: VerificationRequest,
            verdict: VerificationVerdict,
            *,
            assurance_level: AssuranceLevel | None = None,
            diagnostics: list[str] | None = None,
            evidence_refs: list[str] | None = None,
    ) -> VerificationReport:
        hashes = [request.candidate.content_hash] if request.candidate else []
        return VerificationReport(
            kind=request.kind,
            verdict=verdict,
            assurance_level=assurance_level or self.assurance_level,
            verifier_key=self.key,
            verifier_version=self.version,
            config_digest=self.config_digest,
            input_snapshot_hash=request.input_snapshot_hash,
            artifact_hashes=hashes,
            evidence_refs=deepcopy(evidence_refs or []),
            diagnostics=deepcopy(diagnostics or []),
        )


__all__ = ["Verifier", "VerifierCallable", "CallableVerifier"]
