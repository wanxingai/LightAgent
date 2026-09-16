"""Unified identity, approval, and capability-gating contracts."""

from __future__ import annotations

import asyncio
import hashlib
import inspect
import json
import threading
from copy import deepcopy
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Iterable, Mapping
from uuid import uuid4

from .capabilities import (
    CapabilityRisk,
    CapabilityRegistry,
    CapabilitySpec,
    PermissionSet,
    PolicyDecision,
    PolicyEngine,
    PolicyRequest,
    RuntimeContext,
)


SECURITY_CONTEXT_SCHEMA_VERSION = 1
APPROVAL_TOKEN_SCHEMA_VERSION = 1
PROVIDER_MANIFEST_SCHEMA_VERSION = 1


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), default=repr)


def canonical_digest(value: Any) -> str:
    """Return a stable SHA-256 digest for a JSON-compatible value."""

    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _secret_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        result = {}
        for key, item in value.items():
            name = str(key)
            if any(token in name.lower() for token in ("key", "token", "secret", "password", "credential")):
                result[name] = {"secret_digest": canonical_digest(item)}
            else:
                result[name] = _secret_safe(item)
        return result
    if isinstance(value, (list, tuple)):
        return [_secret_safe(item) for item in value]
    return value


@dataclass(frozen=True)
class SecurityContext:
    """Trusted runtime identity and a narrowing-only permission snapshot."""

    user_id: str | None = None
    tenant_id: str | None = None
    project_id: str | None = None
    session_id: str | None = None
    run_id: str | None = None
    task_id: str | None = None
    attempt_id: str | None = None
    agent_id: str | None = None
    parent_agent_id: str | None = None
    permissions: PermissionSet = field(default_factory=PermissionSet)
    resources: frozenset[str] = field(default_factory=frozenset)
    network_allowed: bool = False
    sandbox_required: bool = False
    deadline: str | None = None
    policy_version: str = "1"
    approval_token_ids: frozenset[str] = field(default_factory=frozenset)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    schema_version: int = SECURITY_CONTEXT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != SECURITY_CONTEXT_SCHEMA_VERSION:
            raise ValueError(f"unsupported SecurityContext schema version: {self.schema_version}")
        if self.deadline is not None:
            _parse_utc(self.deadline)
        object.__setattr__(self, "resources", frozenset(self.resources))
        object.__setattr__(self, "approval_token_ids", frozenset(self.approval_token_ids))
        object.__setattr__(self, "metadata", deepcopy(dict(self.metadata)))

    @property
    def expired(self) -> bool:
        if self.deadline is None:
            return False
        return datetime.now(timezone.utc) >= _parse_utc(self.deadline)

    def narrow(
            self,
            *,
            task_id: str | None = None,
            attempt_id: str | None = None,
            agent_id: str | None = None,
            allowed_capabilities: Iterable[str] | None = None,
            denied_capabilities: Iterable[str] | None = None,
            max_risk: Any = None,
            resources: Iterable[str] | None = None,
            network_allowed: bool | None = None,
            sandbox_required: bool | None = None,
            deadline: str | None = None,
            metadata: Mapping[str, Any] | None = None,
    ) -> "SecurityContext":
        requested_resources = frozenset(resources) if resources is not None else self.resources
        if self.resources and not requested_resources.issubset(self.resources):
            raise ValueError("child security context cannot add resources")
        requested_network = self.network_allowed if network_allowed is None else network_allowed
        if requested_network and not self.network_allowed:
            raise ValueError("child security context cannot enable network access")
        requested_sandbox = self.sandbox_required if sandbox_required is None else sandbox_required
        if self.sandbox_required and not requested_sandbox:
            raise ValueError("child security context cannot remove the sandbox requirement")
        resolved_deadline = deadline or self.deadline
        if self.deadline and resolved_deadline:
            parent_deadline = _parse_utc(self.deadline)
            child_deadline = _parse_utc(resolved_deadline)
            if child_deadline > parent_deadline:
                raise ValueError("child security context cannot extend the deadline")
        return replace(
            self,
            task_id=task_id if task_id is not None else self.task_id,
            attempt_id=attempt_id if attempt_id is not None else self.attempt_id,
            agent_id=agent_id if agent_id is not None else self.agent_id,
            parent_agent_id=self.agent_id or self.parent_agent_id,
            permissions=self.permissions.narrow(
                allowed=allowed_capabilities,
                denied=denied_capabilities,
                max_risk=max_risk,
            ),
            resources=requested_resources,
            network_allowed=requested_network,
            sandbox_required=requested_sandbox,
            deadline=resolved_deadline,
            metadata={**dict(self.metadata), **dict(metadata or {})},
        )

    def to_runtime_context(self) -> RuntimeContext:
        return RuntimeContext(
            session_id=self.session_id,
            agent_id=self.agent_id,
            user_id=self.user_id,
            tenant_id=self.tenant_id,
            project_id=self.project_id,
            run_id=self.run_id,
            task_id=self.task_id,
            attempt_id=self.attempt_id,
            permissions=self.permissions,
            security_context=self,
            metadata={
                **dict(self.metadata),
                "tenant_id": self.tenant_id,
                "project_id": self.project_id,
                "task_id": self.task_id,
                "attempt_id": self.attempt_id,
                "policy_version": self.policy_version,
                "security_context_schema": self.schema_version,
            },
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "permissions": {
                "allowed": sorted(self.permissions.allowed),
                "denied": sorted(self.permissions.denied),
                "max_risk": self.permissions.max_risk.value,
            },
            "resources": sorted(self.resources),
            "approval_token_ids": sorted(self.approval_token_ids),
            "metadata": deepcopy(dict(self.metadata)),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "SecurityContext":
        payload = dict(value)
        permissions = payload.get("permissions") or {}
        if not isinstance(permissions, PermissionSet):
            permissions = PermissionSet(
                allowed=frozenset(permissions.get("allowed") or ()),
                denied=frozenset(permissions.get("denied") or ()),
                max_risk=CapabilityRisk(permissions.get("max_risk", CapabilityRisk.DESTRUCTIVE.value)),
            )
        payload["permissions"] = permissions
        payload["resources"] = frozenset(payload.get("resources") or ())
        payload["approval_token_ids"] = frozenset(payload.get("approval_token_ids") or ())
        return cls(**payload)


@dataclass
class ApprovalToken:
    """Versioned approval bound to one canonical operation and security identity."""

    operation: str
    arguments_digest: str
    policy_version: str
    token_id: str = field(default_factory=lambda: uuid4().hex)
    tenant_id: str | None = None
    project_id: str | None = None
    run_id: str | None = None
    task_id: str | None = None
    attempt_id: str | None = None
    resource: str | None = None
    issued_at: str = field(default_factory=_utc_now)
    expires_at: str | None = None
    reusable: bool = False
    consumed_at: str | None = None
    schema_version: int = APPROVAL_TOKEN_SCHEMA_VERSION
    metadata: dict[str, Any] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False, compare=False)

    @classmethod
    def issue(
            cls,
            operation: str,
            arguments: Mapping[str, Any],
            context: SecurityContext,
            *,
            ttl_seconds: float = 300,
            resource: str | None = None,
            reusable: bool = False,
            metadata: Mapping[str, Any] | None = None,
    ) -> "ApprovalToken":
        if not operation.strip():
            raise ValueError("approval operation must not be empty")
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        expires = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
        return cls(
            operation=operation,
            arguments_digest=canonical_digest(arguments),
            policy_version=context.policy_version,
            tenant_id=context.tenant_id,
            project_id=context.project_id,
            run_id=context.run_id,
            task_id=context.task_id,
            attempt_id=context.attempt_id,
            resource=resource,
            expires_at=expires.isoformat(),
            reusable=reusable,
            metadata=deepcopy(dict(metadata or {})),
        )

    @property
    def expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) >= _parse_utc(self.expires_at)

    def verify(
            self,
            operation: str,
            arguments: Mapping[str, Any],
            context: SecurityContext,
            *,
            resource: str | None = None,
            consume: bool = True,
    ) -> None:
        with self._lock:
            if self.schema_version != APPROVAL_TOKEN_SCHEMA_VERSION:
                raise PermissionError("unsupported approval token schema")
            if self.expired:
                raise PermissionError("approval token has expired")
            if self.consumed_at is not None and not self.reusable:
                raise PermissionError("approval token has already been consumed")
            expected = (
                self.operation,
                self.arguments_digest,
                self.policy_version,
                self.tenant_id,
                self.project_id,
                self.run_id,
                self.task_id,
                self.attempt_id,
                self.resource,
            )
            actual = (
                operation,
                canonical_digest(arguments),
                context.policy_version,
                context.tenant_id,
                context.project_id,
                context.run_id,
                context.task_id,
                context.attempt_id,
                resource,
            )
            if expected != actual:
                raise PermissionError("approval token does not match the current operation")
            if consume and not self.reusable:
                self.consumed_at = _utc_now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation": self.operation,
            "arguments_digest": self.arguments_digest,
            "policy_version": self.policy_version,
            "token_id": self.token_id,
            "tenant_id": self.tenant_id,
            "project_id": self.project_id,
            "run_id": self.run_id,
            "task_id": self.task_id,
            "attempt_id": self.attempt_id,
            "resource": self.resource,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "reusable": self.reusable,
            "consumed_at": self.consumed_at,
            "schema_version": self.schema_version,
            "metadata": deepcopy(self.metadata),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ApprovalToken":
        payload = dict(value)
        payload["metadata"] = deepcopy(dict(payload.get("metadata") or {}))
        return cls(**payload)


@dataclass(frozen=True)
class ProviderManifest:
    """Serializable Provider identity without raw configuration secrets."""

    name: str
    version: str
    capabilities: tuple[str, ...]
    configuration_digest: str
    capability_digest: str
    schema_version: int = PROVIDER_MANIFEST_SCHEMA_VERSION
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_provider(cls, provider: Any) -> "ProviderManifest":
        capabilities = tuple(sorted(str(name) for name in provider.capabilities))
        safe_config = _secret_safe(getattr(provider, "config", {}) or {})
        capability_payload = {
            name: provider.capabilities[name].to_dict()
            for name in capabilities
        }
        return cls(
            name=str(provider.name),
            version=str(provider.version),
            capabilities=capabilities,
            configuration_digest=canonical_digest(safe_config),
            capability_digest=canonical_digest(capability_payload),
            metadata={},
        )

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["capabilities"] = list(self.capabilities)
        value["metadata"] = deepcopy(dict(self.metadata))
        return value


class CapabilityGate:
    """Apply identity, permission, policy, approval, and deadline checks."""

    def __init__(
            self,
            registry: CapabilityRegistry | None = None,
            *,
            policy_engine: PolicyEngine | None = None,
            audit: Callable[[str, dict[str, Any]], Any] | None = None,
    ):
        self.registry = registry
        self.policy_engine = policy_engine or (registry.policy_engine if registry else PolicyEngine())
        self.audit = audit

    async def authorize(
            self,
            capability: CapabilitySpec,
            provider_name: str,
            arguments: Mapping[str, Any] | None,
            context: SecurityContext,
            *,
            approval_token: ApprovalToken | None = None,
            resource: str | None = None,
    ) -> PolicyDecision:
        if context.expired:
            raise PermissionError("security context deadline has expired")
        if resource is not None and context.resources and resource not in context.resources:
            raise PermissionError(f"resource `{resource}` is outside the security context")
        if capability.network and not context.network_allowed:
            raise PermissionError(f"capability `{capability.name}` requires network access")
        if capability.requires_sandbox and not context.sandbox_required:
            raise PermissionError(f"capability `{capability.name}` requires a sandbox-bound context")

        requested_arguments = deepcopy(dict(arguments or {}))
        policy_capability = capability
        if capability.requires_approval and approval_token is not None:
            approval_token.verify(
                capability.name,
                requested_arguments,
                context,
                resource=resource,
            )
            policy_capability = replace(capability, requires_approval=False)
        decision = await self.policy_engine.evaluate(PolicyRequest(
            capability=policy_capability,
            provider_name=provider_name,
            arguments=requested_arguments,
            context=context.to_runtime_context(),
        ))
        self._audit("capability.gate", {
            "capability": capability.name,
            "provider": provider_name,
            "allowed": decision.allowed,
            "requires_approval": decision.requires_approval,
            "reason": decision.reason,
            "run_id": context.run_id,
            "task_id": context.task_id,
            "attempt_id": context.attempt_id,
            "policy_version": context.policy_version,
            "arguments_digest": canonical_digest(requested_arguments),
        })
        if not decision.allowed:
            state = "requires approval" if decision.requires_approval else "was denied"
            raise PermissionError(
                f"capability `{capability.name}` {state}: {decision.reason or 'policy decision'}"
            )
        return decision

    async def invoke(
            self,
            capability_name: str,
            arguments: Mapping[str, Any] | None,
            context: SecurityContext,
            *,
            approval_token: ApprovalToken | None = None,
            resource: str | None = None,
    ) -> Any:
        if self.registry is None:
            raise RuntimeError("CapabilityGate.invoke requires a CapabilityRegistry")
        runtime_context = context.to_runtime_context()
        provider = self.registry.resolve(capability_name, runtime_context)
        capability = provider.capabilities[capability_name]
        decision = await self.authorize(
            capability,
            provider.name,
            arguments,
            context,
            approval_token=approval_token,
            resource=resource,
        )
        invoke = getattr(provider, "invoke", None)
        if not callable(invoke):
            raise TypeError(f"provider `{provider.name}` does not implement invoke()")
        result = invoke(capability_name, **(decision.arguments or dict(arguments or {})))
        if inspect.isawaitable(result):
            result = await asyncio.wait_for(result, timeout=capability.timeout) if capability.timeout else await result
        if capability.output_limit is not None and len(str(result)) > capability.output_limit:
            result = str(result)[:capability.output_limit]
        return result

    def authorize_sync(self, *args: Any, **kwargs: Any) -> PolicyDecision:
        from .capabilities import _run_sync

        return _run_sync(self.authorize(*args, **kwargs))

    def _audit(self, event_type: str, data: dict[str, Any]) -> None:
        if self.audit:
            self.audit(event_type, deepcopy(data))


__all__ = [
    "SECURITY_CONTEXT_SCHEMA_VERSION",
    "APPROVAL_TOKEN_SCHEMA_VERSION",
    "PROVIDER_MANIFEST_SCHEMA_VERSION",
    "canonical_digest",
    "SecurityContext",
    "ApprovalToken",
    "ProviderManifest",
    "CapabilityGate",
]
