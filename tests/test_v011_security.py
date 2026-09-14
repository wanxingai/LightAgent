import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from LightAgent.capabilities import (
    BaseCapabilityProvider,
    CapabilityRegistry,
    CapabilityRisk,
    CapabilitySpec,
    PermissionSet,
)
from LightAgent.runtime import AgentRuntime
from LightAgent.security import ApprovalToken, CapabilityGate, ProviderManifest, SecurityContext


def make_context(**kwargs):
    values = {
        "user_id": "alice",
        "tenant_id": "tenant-a",
        "project_id": "project-a",
        "run_id": "run-a",
        "permissions": PermissionSet(
            allowed=frozenset({"tool.read", "tool.write"}),
            max_risk=CapabilityRisk.SENSITIVE,
        ),
        "resources": frozenset({"workspace:a", "db:reports"}),
        "network_allowed": False,
        "sandbox_required": True,
        "policy_version": "policy-7",
    }
    values.update(kwargs)
    return SecurityContext(**values)


def test_security_context_round_trip_and_narrowing():
    parent = make_context()
    child = parent.narrow(
        task_id="task-a",
        attempt_id="attempt-a",
        agent_id="worker-a",
        allowed_capabilities={"tool.read"},
        resources={"workspace:a"},
        max_risk=CapabilityRisk.READ_ONLY,
    )

    restored = SecurityContext.from_dict(child.to_dict())

    assert restored.task_id == "task-a"
    assert restored.parent_agent_id is None
    assert restored.permissions.allowed == frozenset({"tool.read"})
    assert restored.resources == frozenset({"workspace:a"})
    with pytest.raises(ValueError, match="add capabilities"):
        child.narrow(allowed_capabilities={"tool.read", "tool.write"})
    with pytest.raises(ValueError, match="add resources"):
        child.narrow(resources={"workspace:a", "workspace:b"})
    with pytest.raises(ValueError, match="network"):
        child.narrow(network_allowed=True)
    with pytest.raises(ValueError, match="sandbox"):
        child.narrow(sandbox_required=False)


def test_approval_token_is_argument_identity_and_policy_bound():
    context = make_context(task_id="task-a", attempt_id="attempt-a")
    token = ApprovalToken.issue(
        "tool.write",
        {"path": "report.txt", "content": "ok"},
        context,
        resource="workspace:a",
    )

    token.verify(
        "tool.write",
        {"content": "ok", "path": "report.txt"},
        context,
        resource="workspace:a",
    )
    assert token.consumed_at is not None
    with pytest.raises(PermissionError, match="consumed"):
        token.verify(
            "tool.write",
            {"path": "report.txt", "content": "ok"},
            context,
            resource="workspace:a",
        )

    changed = ApprovalToken.issue("tool.write", {"path": "report.txt"}, context)
    with pytest.raises(PermissionError, match="does not match"):
        changed.verify("tool.write", {"path": "other.txt"}, context)

    restored = ApprovalToken.from_dict(ApprovalToken.issue(
        "tool.write", {"path": "report.txt"}, context
    ).to_dict())
    restored.verify("tool.write", {"path": "report.txt"}, context)


def test_security_context_normalizes_naive_and_aware_deadlines():
    parent_deadline = (datetime.now(timezone.utc) + timedelta(minutes=10)).replace(tzinfo=None).isoformat()
    child_deadline = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
    parent = make_context(deadline=parent_deadline)

    child = parent.narrow(deadline=child_deadline)

    assert child.expired is False


def test_capability_gate_requires_bound_approval_and_invokes_provider():
    class Provider(BaseCapabilityProvider):
        name = "writer"
        version = "2"

        def __init__(self):
            super().__init__([CapabilitySpec(
                "tool.write",
                risk=CapabilityRisk.SENSITIVE,
                write=True,
                requires_approval=True,
            )])

        async def invoke(self, capability, **arguments):
            return arguments["value"]

    provider = Provider()
    registry = CapabilityRegistry()
    registry.register(provider)
    gate = CapabilityGate(registry)
    context = make_context(resources=frozenset())

    with pytest.raises(PermissionError, match="requires approval"):
        asyncio.run(gate.invoke("tool.write", {"value": 3}, context))

    token = ApprovalToken.issue("tool.write", {"value": 3}, context)
    assert asyncio.run(gate.invoke("tool.write", {"value": 3}, context, approval_token=token)) == 3


def test_provider_manifest_hashes_secret_configuration():
    provider = BaseCapabilityProvider([CapabilitySpec("tool.read", read=True)])
    provider.name = "provider-a"
    provider.version = "4"
    provider.config = {"api_key": "super-secret", "region": "local"}

    manifest = ProviderManifest.from_provider(provider)
    rendered = repr(manifest.to_dict())

    assert manifest.capabilities == ("tool.read",)
    assert "super-secret" not in rendered
    assert len(manifest.configuration_digest) == 64


def test_registry_accepts_security_context_without_bypassing_approval():
    class Provider(BaseCapabilityProvider):
        name = "writer"

        def __init__(self):
            super().__init__([CapabilitySpec(
                "tool.write",
                risk=CapabilityRisk.SENSITIVE,
                write=True,
                requires_approval=True,
            )])

        async def invoke(self, capability, **arguments):
            assert self.context is None
            return arguments["value"]

    registry = CapabilityRegistry()
    registry.register(Provider())
    context = make_context(resources=frozenset())
    token = ApprovalToken.issue("tool.write", {"value": 7}, context)

    result = asyncio.run(registry.invoke(
        "tool.write",
        {"value": 7},
        context=context,
        approval_token=token,
    ))

    assert result == 7
    assert token.consumed_at is not None


def test_agent_runtime_binds_security_context_to_open_session():
    runtime = AgentRuntime()
    context = make_context(run_id=None).narrow(agent_id="agent-a")

    session = runtime.open_session("session-a", security_context=context)

    assert session.session_id == "session-a"
    assert runtime.context.session_id == "session-a"
    assert runtime.context.tenant_id == "tenant-a"
    assert runtime.context.project_id == "project-a"
    assert runtime.context.security_context is context

    conflicting = make_context(run_id=None)
    conflicting = SecurityContext.from_dict({**conflicting.to_dict(), "session_id": "other"})
    with pytest.raises(ValueError, match="does not match"):
        AgentRuntime().open_session("session-a", security_context=conflicting)
