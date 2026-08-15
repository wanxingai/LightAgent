"""Capability Provider registry, lifecycle, permissions, and policy decisions."""

from __future__ import annotations

import asyncio
import inspect
import threading
import hashlib
import json
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Awaitable, Callable, Iterable, Protocol


class CapabilityScope(str, Enum):
    DEFAULT = "default"
    RUNTIME = "runtime"
    SESSION = "session"
    AGENT = "agent"


class CapabilityRisk(str, Enum):
    READ_ONLY = "L0"
    ISOLATED_WRITE = "L1"
    SENSITIVE = "L2"
    DESTRUCTIVE = "L3"


@dataclass(frozen=True)
class CapabilitySpec:
    name: str
    description: str = ""
    risk: CapabilityRisk = CapabilityRisk.READ_ONLY
    read: bool = False
    write: bool = False
    network: bool = False
    execute: bool = False
    persistent: bool = False
    cancellable: bool = False
    resumable: bool = False
    timeout: float | None = None
    output_limit: int | None = None
    requires_sandbox: bool = False
    requires_approval: bool = False
    ui_type: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("CapabilitySpec.name must not be empty")
        if self.timeout is not None and self.timeout <= 0:
            raise ValueError("CapabilitySpec.timeout must be positive")
        if self.output_limit is not None and self.output_limit < 1:
            raise ValueError("CapabilitySpec.output_limit must be at least 1")

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["risk"] = self.risk.value
        return value


@dataclass
class ProviderHealth:
    healthy: bool = True
    status: str = "ready"
    message: str | None = None
    degraded_capabilities: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RuntimeContext:
    runtime_id: str | None = None
    session_id: str | None = None
    agent_id: str | None = None
    user_id: str | None = None
    turn_id: str | None = None
    run_id: str | None = None
    permissions: "PermissionSet | None" = None
    metadata: dict[str, Any] = field(default_factory=dict)


class CapabilityProvider(Protocol):
    name: str
    version: str
    capabilities: dict[str, CapabilitySpec]

    async def mount(self, context: RuntimeContext) -> None:
        ...

    async def start(self) -> None:
        ...

    async def health(self) -> ProviderHealth:
        ...

    async def reload(self, config: dict[str, Any]) -> None:
        ...

    async def stop(self) -> None:
        ...

    async def unmount(self) -> None:
        ...


class ModelProvider(CapabilityProvider, Protocol):
    pass


class ToolProvider(CapabilityProvider, Protocol):
    pass


class FileSystemProvider(CapabilityProvider, Protocol):
    pass


class ShellProvider(CapabilityProvider, Protocol):
    pass


class TerminalProvider(CapabilityProvider, Protocol):
    pass


class BrowserProvider(CapabilityProvider, Protocol):
    pass


class WebProvider(CapabilityProvider, Protocol):
    pass


class LSPProvider(CapabilityProvider, Protocol):
    pass


class MemoryProvider(CapabilityProvider, Protocol):
    pass


class RAGProvider(CapabilityProvider, Protocol):
    pass


class SubagentProvider(CapabilityProvider, Protocol):
    pass


class WorkflowProvider(CapabilityProvider, Protocol):
    pass


class InteractionProvider(CapabilityProvider, Protocol):
    pass


class SandboxProvider(CapabilityProvider, Protocol):
    pass


class CredentialProvider(CapabilityProvider, Protocol):
    pass


class TelemetryProvider(CapabilityProvider, Protocol):
    pass


class BaseCapabilityProvider:
    """Small lifecycle implementation for Python-native Providers."""

    name = "provider"
    version = "1"

    def __init__(self, capabilities: Iterable[CapabilitySpec] | None = None):
        self.capabilities = {spec.name: spec for spec in capabilities or []}
        self.context: RuntimeContext | None = None
        self.config: dict[str, Any] = {}
        self.mounted = False
        self.started = False

    async def mount(self, context: RuntimeContext) -> None:
        self.context = context
        self.mounted = True

    async def start(self) -> None:
        if not self.mounted:
            raise RuntimeError(f"provider `{self.name}` must be mounted before start")
        self.started = True

    async def health(self) -> ProviderHealth:
        return ProviderHealth(healthy=self.started, status="ready" if self.started else "stopped")

    async def reload(self, config: dict[str, Any]) -> None:
        self.config = deepcopy(config)

    async def stop(self) -> None:
        self.started = False

    async def unmount(self) -> None:
        if self.started:
            await self.stop()
        self.context = None
        self.mounted = False


@dataclass(frozen=True)
class PermissionSet:
    """A capability allowlist that can only be narrowed by descendants."""

    allowed: frozenset[str] = field(default_factory=frozenset)
    denied: frozenset[str] = field(default_factory=frozenset)
    max_risk: CapabilityRisk = CapabilityRisk.DESTRUCTIVE

    def allows(self, capability: str, risk: CapabilityRisk = CapabilityRisk.READ_ONLY) -> bool:
        if capability in self.denied:
            return False
        if self.allowed and capability not in self.allowed:
            return False
        order = {
            CapabilityRisk.READ_ONLY: 0,
            CapabilityRisk.ISOLATED_WRITE: 1,
            CapabilityRisk.SENSITIVE: 2,
            CapabilityRisk.DESTRUCTIVE: 3,
        }
        return order[risk] <= order[self.max_risk]

    def narrow(
            self,
            *,
            allowed: Iterable[str] | None = None,
            denied: Iterable[str] | None = None,
            max_risk: CapabilityRisk | None = None,
    ) -> "PermissionSet":
        requested = frozenset(allowed) if allowed is not None else self.allowed
        if self.allowed and not requested.issubset(self.allowed):
            extra = sorted(requested - self.allowed)
            raise ValueError(f"child permissions cannot add capabilities: {extra}")
        risk = max_risk or self.max_risk
        order = {
            CapabilityRisk.READ_ONLY: 0,
            CapabilityRisk.ISOLATED_WRITE: 1,
            CapabilityRisk.SENSITIVE: 2,
            CapabilityRisk.DESTRUCTIVE: 3,
        }
        if order[risk] > order[self.max_risk]:
            raise ValueError("child permissions cannot increase max_risk")
        return PermissionSet(
            allowed=requested,
            denied=self.denied | frozenset(denied or []),
            max_risk=risk,
        )


@dataclass
class PolicyRequest:
    capability: CapabilitySpec
    provider_name: str
    arguments: dict[str, Any] = field(default_factory=dict)
    context: RuntimeContext = field(default_factory=RuntimeContext)


@dataclass
class PolicyDecision:
    allowed: bool
    reason: str | None = None
    requires_approval: bool = False
    arguments: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def allow(cls, arguments: dict[str, Any] | None = None, **metadata: Any) -> "PolicyDecision":
        return cls(allowed=True, arguments=arguments, metadata=metadata)

    @classmethod
    def block(cls, reason: str, **metadata: Any) -> "PolicyDecision":
        return cls(allowed=False, reason=reason, metadata=metadata)

    @classmethod
    def approval(cls, reason: str | None = None, **metadata: Any) -> "PolicyDecision":
        return cls(allowed=False, reason=reason, requires_approval=True, metadata=metadata)


PolicyCallable = Callable[[PolicyRequest], PolicyDecision | bool | dict[str, Any] | None | Awaitable[Any]]


class PolicyEngine:
    """Ordered fail-closed policy evaluation for capability execution."""

    def __init__(self, policies: Iterable[PolicyCallable] | None = None, *, fail_closed: bool = True):
        self.policies = list(policies or [])
        self.fail_closed = fail_closed

    def add(self, policy: PolicyCallable) -> None:
        self.policies.append(policy)

    async def evaluate(self, request: PolicyRequest) -> PolicyDecision:
        permissions = request.context.permissions
        if permissions and not permissions.allows(request.capability.name, request.capability.risk):
            return PolicyDecision.block(f"capability `{request.capability.name}` is outside the permission snapshot")
        if request.capability.requires_approval:
            return PolicyDecision.approval(f"capability `{request.capability.name}` requires approval")

        arguments = deepcopy(request.arguments)
        collected_metadata: dict[str, Any] = {}
        for policy in self.policies:
            try:
                result = policy(PolicyRequest(
                    capability=request.capability,
                    provider_name=request.provider_name,
                    arguments=deepcopy(arguments),
                    context=request.context,
                ))
                if inspect.isawaitable(result):
                    result = await result
                decision = self._coerce(result, arguments)
            except Exception as error:
                if self.fail_closed:
                    return PolicyDecision.block(
                        f"policy `{getattr(policy, '__name__', policy.__class__.__name__)}` failed: {type(error).__name__}"
                    )
                collected_metadata.setdefault("policy_errors", []).append(type(error).__name__)
                continue
            collected_metadata.update(decision.metadata)
            if not decision.allowed:
                decision.metadata = {**collected_metadata, **decision.metadata}
                return decision
            if decision.arguments is not None:
                arguments = deepcopy(decision.arguments)
        return PolicyDecision.allow(arguments, **collected_metadata)

    def evaluate_sync(self, request: PolicyRequest) -> PolicyDecision:
        return _run_sync(self.evaluate(request))

    @staticmethod
    def _coerce(value: Any, arguments: dict[str, Any]) -> PolicyDecision:
        if value is None or value is True:
            return PolicyDecision.allow(arguments)
        if value is False:
            return PolicyDecision.block("policy denied the capability")
        if isinstance(value, PolicyDecision):
            return value
        if isinstance(value, dict):
            if value.get("requires_approval"):
                return PolicyDecision.approval(value.get("reason"), **dict(value.get("metadata") or {}))
            allowed = bool(value.get("allowed", True))
            return PolicyDecision(
                allowed=allowed,
                reason=value.get("reason"),
                arguments=value.get("arguments", arguments),
                metadata=dict(value.get("metadata") or {}),
            )
        raise TypeError("policy must return PolicyDecision, bool, dict, or None")


@dataclass
class ProviderRegistration:
    provider: CapabilityProvider
    scope: CapabilityScope
    owner_id: str | None = None
    order: int = 0


class CapabilityRegistry:
    """Resolve Providers by capability and runtime/session/agent scope."""

    _precedence = {
        CapabilityScope.DEFAULT: 0,
        CapabilityScope.RUNTIME: 1,
        CapabilityScope.SESSION: 2,
        CapabilityScope.AGENT: 3,
    }

    def __init__(
            self,
            *,
            policy_engine: PolicyEngine | None = None,
            audit: Callable[[str, dict[str, Any]], Any] | None = None,
    ):
        self.policy_engine = policy_engine or PolicyEngine()
        self.audit = audit
        self._registrations: list[ProviderRegistration] = []
        self._conflicts: list[dict[str, Any]] = []
        self._counter = 0

    def register(
            self,
            provider: CapabilityProvider,
            *,
            scope: CapabilityScope | str = CapabilityScope.RUNTIME,
            owner_id: str | None = None,
    ) -> CapabilityProvider:
        resolved_scope = CapabilityScope(scope)
        if resolved_scope in {CapabilityScope.SESSION, CapabilityScope.AGENT} and not owner_id:
            raise ValueError(f"owner_id is required for {resolved_scope.value} scope")
        if any(
            item.provider.name == provider.name and item.scope == resolved_scope and item.owner_id == owner_id
            for item in self._registrations
        ):
            raise ValueError(
                f"provider `{provider.name}` is already registered for {resolved_scope.value}:{owner_id or '*'}"
            )
        self._counter += 1
        for existing in self._registrations:
            overlap = sorted(set(existing.provider.capabilities) & set(provider.capabilities))
            if overlap and existing.scope == resolved_scope and existing.owner_id == owner_id:
                self._conflicts.append({
                    "capabilities": overlap,
                    "winner": provider.name,
                    "shadowed": existing.provider.name,
                    "scope": resolved_scope.value,
                    "owner_id": owner_id,
                    "rule": "latest registration wins within an equal scope",
                })
        self._registrations.append(ProviderRegistration(provider, resolved_scope, owner_id, self._counter))
        return provider

    def conflicts(self) -> list[dict[str, Any]]:
        return deepcopy(self._conflicts)

    async def mount(self, context: RuntimeContext) -> None:
        for item in self._matching(context):
            await item.provider.mount(context)
            await item.provider.start()
            self._audit("provider.started", item, context=context)

    async def unregister(
            self,
            name: str,
            *,
            scope: CapabilityScope | str | None = None,
            owner_id: str | None = None,
    ) -> bool:
        resolved_scope = CapabilityScope(scope) if scope is not None else None
        matches = [
            item for item in self._registrations
            if item.provider.name == name
            and (resolved_scope is None or item.scope == resolved_scope)
            and (owner_id is None or item.owner_id == owner_id)
        ]
        for item in reversed(matches):
            await item.provider.stop()
            await item.provider.unmount()
            self._registrations.remove(item)
            self._audit("provider.unregistered", item)
        return bool(matches)

    def resolve(self, capability: str, context: RuntimeContext | None = None) -> CapabilityProvider:
        runtime_context = context or RuntimeContext()
        matches = [
            item for item in self._matching(runtime_context)
            if capability in item.provider.capabilities
        ]
        if not matches:
            raise LookupError(f"no Provider registered for capability `{capability}`")
        matches.sort(key=lambda item: (self._precedence[item.scope], item.order), reverse=True)
        return matches[0].provider

    def get(self, name: str, context: RuntimeContext | None = None) -> CapabilityProvider:
        matches = [item for item in self._matching(context or RuntimeContext()) if item.provider.name == name]
        if not matches:
            raise LookupError(f"provider `{name}` is not registered")
        matches.sort(key=lambda item: (self._precedence[item.scope], item.order), reverse=True)
        return matches[0].provider

    def list(self, context: RuntimeContext | None = None) -> list[dict[str, Any]]:
        values = []
        for item in self._matching(context or RuntimeContext()):
            values.append({
                "name": item.provider.name,
                "version": item.provider.version,
                "scope": item.scope.value,
                "owner_id": item.owner_id,
                "capabilities": [spec.to_dict() for spec in item.provider.capabilities.values()],
            })
        return values

    async def health(self, context: RuntimeContext | None = None) -> dict[str, ProviderHealth]:
        result = {}
        for item in self._matching(context or RuntimeContext()):
            result[item.provider.name] = await item.provider.health()
        return result

    async def reload(self, name: str, config: dict[str, Any], context: RuntimeContext | None = None) -> None:
        provider = self.get(name, context)
        await provider.reload(config)

    async def stop(self, context: RuntimeContext | None = None) -> None:
        for item in reversed(self._matching(context or RuntimeContext())):
            await item.provider.stop()
            await item.provider.unmount()
            self._audit("provider.stopped", item, context=context)

    async def invoke(
            self,
            capability: str,
            arguments: dict[str, Any] | None = None,
            *,
            context: RuntimeContext | None = None,
    ) -> Any:
        runtime_context = context or RuntimeContext()
        provider = self.resolve(capability, runtime_context)
        spec = provider.capabilities[capability]
        decision = await self.policy_engine.evaluate(PolicyRequest(
            capability=spec,
            provider_name=provider.name,
            arguments=arguments or {},
            context=runtime_context,
        ))
        self._audit("policy.decision", self._registration_for(provider), context=runtime_context, extra={
            "capability": capability,
            "allowed": decision.allowed,
            "requires_approval": decision.requires_approval,
            "reason": decision.reason,
        })
        if not decision.allowed:
            state = "requires approval" if decision.requires_approval else "was denied"
            raise PermissionError(f"capability `{capability}` {state}: {decision.reason or 'policy decision'}")
        invoke = getattr(provider, "invoke", None)
        if not callable(invoke):
            raise TypeError(f"provider `{provider.name}` does not implement invoke()")
        result = invoke(capability, **(decision.arguments or arguments or {}))
        if inspect.isawaitable(result):
            result = await asyncio.wait_for(result, timeout=spec.timeout) if spec.timeout else await result
        if spec.output_limit is not None and len(str(result)) > spec.output_limit:
            result = str(result)[:spec.output_limit]
        return result

    def _matching(self, context: RuntimeContext) -> list[ProviderRegistration]:
        return [
            item for item in self._registrations
            if item.scope in {CapabilityScope.DEFAULT, CapabilityScope.RUNTIME}
            or (item.scope == CapabilityScope.SESSION and item.owner_id == context.session_id)
            or (item.scope == CapabilityScope.AGENT and item.owner_id == context.agent_id)
        ]

    def _registration_for(self, provider: CapabilityProvider) -> ProviderRegistration:
        return next(item for item in self._registrations if item.provider is provider)

    def _audit(
            self,
            event_type: str,
            item: ProviderRegistration,
            *,
            context: RuntimeContext | None = None,
            extra: dict[str, Any] | None = None,
    ) -> None:
        if not self.audit:
            return
        self.audit(event_type, {
            "provider": item.provider.name,
            "provider_version": item.provider.version,
            "scope": item.scope.value,
            "owner_id": item.owner_id,
            "session_id": context.session_id if context else None,
            "agent_id": context.agent_id if context else None,
            "configuration_digest": self._configuration_digest(item.provider),
            **(extra or {}),
        })

    @staticmethod
    def _configuration_digest(provider: CapabilityProvider) -> str:
        config = getattr(provider, "config", {})
        safe = {
            key: "[redacted]" if any(token in str(key).lower() for token in ("key", "token", "secret", "password")) else value
            for key, value in dict(config or {}).items()
        }
        rendered = json.dumps(safe, ensure_ascii=True, sort_keys=True, default=repr)
        return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


class ToolProviderAdapter(BaseCapabilityProvider):
    name = "tools"

    def __init__(self, tool_registry: Any):
        self.tool_registry = tool_registry
        specs = [
            CapabilitySpec(
                name=f"tool.{name}",
                description=str(info.get("tool_description", "")),
                execute=True,
                risk=CapabilityRisk.SENSITIVE,
                cancellable=True,
            )
            for name, info in tool_registry.function_info.items()
        ]
        super().__init__(specs)

    async def invoke(self, capability: str, **arguments: Any) -> Any:
        name = capability.removeprefix("tool.")
        from .tools import AsyncToolDispatcher

        dispatcher = AsyncToolDispatcher(self.tool_registry.function_mappings, self.tool_registry.function_info)
        return await dispatcher.dispatch(name, arguments)


class MemoryProviderAdapter(BaseCapabilityProvider):
    name = "memory"

    def __init__(self, backend: Any):
        self.backend = backend
        super().__init__([
            CapabilitySpec("memory.retrieve", read=True),
            CapabilitySpec(
                "memory.store",
                write=True,
                persistent=True,
                risk=CapabilityRisk.ISOLATED_WRITE,
            ),
        ])

    async def invoke(self, capability: str, **arguments: Any) -> Any:
        if capability == "memory.retrieve":
            result = self.backend.retrieve(arguments["query"], arguments["user_id"])
        elif capability == "memory.store":
            result = self.backend.store(arguments["data"], arguments["user_id"])
        else:
            raise LookupError(capability)
        if inspect.isawaitable(result):
            return await result
        return result


def _run_sync(awaitable: Awaitable[Any]) -> Any:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(awaitable)

    result: list[Any] = []
    error: list[BaseException] = []

    def runner() -> None:
        try:
            result.append(asyncio.run(awaitable))
        except BaseException as exc:  # pragma: no cover - re-raised below
            error.append(exc)

    thread = threading.Thread(target=runner, daemon=True)
    thread.start()
    thread.join()
    if error:
        raise error[0]
    return result[0]


__all__ = [
    "CapabilityScope",
    "CapabilityRisk",
    "CapabilitySpec",
    "ProviderHealth",
    "RuntimeContext",
    "CapabilityProvider",
    "ModelProvider",
    "ToolProvider",
    "FileSystemProvider",
    "ShellProvider",
    "TerminalProvider",
    "BrowserProvider",
    "WebProvider",
    "LSPProvider",
    "MemoryProvider",
    "RAGProvider",
    "SubagentProvider",
    "WorkflowProvider",
    "InteractionProvider",
    "SandboxProvider",
    "CredentialProvider",
    "TelemetryProvider",
    "BaseCapabilityProvider",
    "PermissionSet",
    "PolicyRequest",
    "PolicyDecision",
    "PolicyEngine",
    "ProviderRegistration",
    "CapabilityRegistry",
    "ToolProviderAdapter",
    "MemoryProviderAdapter",
]
