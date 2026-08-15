import asyncio

import pytest

from LightAgent import (
    BaseCapabilityProvider,
    CapabilityRegistry,
    CapabilityRisk,
    CapabilityScope,
    CapabilitySpec,
    PermissionSet,
    PolicyDecision,
    PolicyEngine,
    ProviderHealth,
    RuntimeContext,
)


class EchoProvider(BaseCapabilityProvider):
    name = "echo"
    version = "test"

    def __init__(self, prefix=""):
        super().__init__([CapabilitySpec("text.echo", read=True, timeout=0.1)])
        self.config = {"prefix": prefix, "api_key": "do-not-audit"}
        self.prefix = prefix

    async def invoke(self, capability, **arguments):
        return self.prefix + arguments["text"]


def test_provider_lifecycle_and_health():
    provider = EchoProvider()
    context = RuntimeContext(runtime_id="runtime")

    asyncio.run(provider.mount(context))
    asyncio.run(provider.start())
    health = asyncio.run(provider.health())
    asyncio.run(provider.stop())
    asyncio.run(provider.unmount())

    assert health == ProviderHealth(healthy=True, status="ready")
    assert not provider.mounted


def test_registry_scope_precedence_and_conflict_diagnostics():
    registry = CapabilityRegistry()
    registry.register(EchoProvider("runtime:"), scope=CapabilityScope.RUNTIME)
    registry.register(EchoProvider("agent:"), scope=CapabilityScope.AGENT, owner_id="a1")

    result = asyncio.run(registry.invoke(
        "text.echo", {"text": "hello"}, context=RuntimeContext(agent_id="a1")
    ))

    assert result == "agent:hello"
    assert registry.conflicts() == []


def test_equal_scope_conflict_is_diagnostic_and_latest_wins():
    registry = CapabilityRegistry()
    registry.register(EchoProvider("one:"))
    second = EchoProvider("two:")
    second.name = "echo-two"
    registry.register(second)

    assert registry.conflicts()[0]["winner"] == "echo-two"
    assert asyncio.run(registry.invoke("text.echo", {"text": "x"})) == "two:x"


def test_permission_snapshot_cannot_escalate():
    parent = PermissionSet(
        allowed=frozenset({"text.echo"}),
        max_risk=CapabilityRisk.ISOLATED_WRITE,
    )

    child = parent.narrow(allowed={"text.echo"}, max_risk=CapabilityRisk.READ_ONLY)

    assert child.allows("text.echo")
    with pytest.raises(ValueError, match="cannot add"):
        parent.narrow(allowed={"text.echo", "shell.execute"})


def test_policy_can_rewrite_or_deny_arguments():
    def policy(request):
        if request.arguments["text"] == "deny":
            return PolicyDecision.block("blocked by test")
        return PolicyDecision.allow({"text": request.arguments["text"].upper()})

    registry = CapabilityRegistry(policy_engine=PolicyEngine([policy]))
    registry.register(EchoProvider())

    assert asyncio.run(registry.invoke("text.echo", {"text": "ok"})) == "OK"
    with pytest.raises(PermissionError, match="blocked by test"):
        asyncio.run(registry.invoke("text.echo", {"text": "deny"}))


def test_audit_contains_digest_but_not_credentials():
    events = []
    registry = CapabilityRegistry(audit=lambda event, data: events.append((event, data)))
    registry.register(EchoProvider())

    asyncio.run(registry.invoke("text.echo", {"text": "ok"}))

    decision = next(data for event, data in events if event == "policy.decision")
    assert len(decision["configuration_digest"]) == 64
    assert "do-not-audit" not in repr(decision)
