from types import SimpleNamespace
from datetime import datetime, timedelta, timezone

import pytest

from LightAgent import LightAgent, MemoryAdmissionDecision, MemoryPolicy, MemoryScope, ToolLoader


class StaticCompletions:
    def __init__(self, content="done"):
        self.calls = []
        self.content = content

    def create(self, **params):
        self.calls.append(params)
        message = SimpleNamespace(content=self.content, tool_calls=None)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class RecordingMemory:
    def __init__(self, results):
        self.results = results
        self.retrieve_calls = []
        self.store_calls = []

    def retrieve(self, query, user_id):
        self.retrieve_calls.append({"query": query, "user_id": user_id})
        return {"results": self.results}

    def store(self, data, user_id):
        self.store_calls.append({"data": data, "user_id": user_id})


def make_agent(memory, memory_policy=None, memory_namespace=None):
    agent = LightAgent(
        model="gpt-4o-mini",
        api_key="test-key",
        base_url="http://127.0.0.1:9/v1",
        memory=memory,
        memory_policy=memory_policy,
        memory_namespace=memory_namespace,
        auto_discover_skills=False,
    )
    completions = StaticCompletions()
    agent.client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    return agent, completions


def test_memory_policy_namespaces_user_id_and_filters_cross_user_results():
    memory = RecordingMemory([
        {"memory": "safe memory", "metadata": {"user_id": "tenant-a:alice"}},
        {"memory": "other user memory", "metadata": {"user_id": "tenant-a:bob"}},
        {"memory": "unattributed memory"},
    ])
    policy = MemoryPolicy(namespace="tenant-a", allow_unattributed_results=False)
    agent, completions = make_agent(memory, memory_policy=policy)

    result = agent.run("hello", user_id="alice")

    assert result == "done"
    assert memory.retrieve_calls[0]["user_id"] == "tenant-a:alice"
    assert memory.store_calls[0]["user_id"] == "tenant-a:alice"
    user_message = completions.calls[0]["messages"][-1]["content"]
    assert "safe memory" in user_message
    assert "other user memory" not in user_message
    assert "unattributed memory" not in user_message


def test_memory_namespace_shortcut_keeps_default_unattributed_results():
    memory = RecordingMemory([{"memory": "legacy memory"}])
    agent, completions = make_agent(memory, memory_namespace="tenant-b")

    agent.run("hello", user_id="alice")

    assert memory.retrieve_calls[0]["user_id"] == "tenant-b:alice"
    assert "legacy memory" in completions.calls[0]["messages"][-1]["content"]


def test_memory_policy_filters_by_source_scope_agent_trust_and_confidence():
    memory = RecordingMemory([
        {
            "memory": "current user preference",
            "metadata": {
                "user_id": "tenant-a:alice",
                "source": "user",
                "scope": "user",
                "agent_name": "writer",
                "trust_level": "verified",
                "confidence": 0.92,
            },
        },
        {
            "memory": "self reflection should stay private",
            "metadata": {
                "user_id": "tenant-a:alice",
                "source": "reflection",
                "scope": "agent",
                "agent_name": "writer",
                "trust_level": "verified",
                "confidence": 0.99,
            },
        },
        {
            "memory": "wrong agent memory",
            "metadata": {
                "user_id": "tenant-a:alice",
                "source": "user",
                "scope": "user",
                "agent_name": "critic",
                "trust_level": "verified",
                "confidence": 0.95,
            },
        },
        {
            "memory": "low confidence memory",
            "metadata": {
                "user_id": "tenant-a:alice",
                "source": "user",
                "scope": "user",
                "agent_name": "writer",
                "trust_level": "verified",
                "confidence": 0.2,
            },
        },
    ])
    policy = MemoryPolicy(
        namespace="tenant-a",
        allow_unattributed_results=False,
        allowed_sources=("user",),
        allowed_scopes=("user",),
        allowed_agent_names=("writer",),
        allowed_trust_levels=("verified",),
        min_confidence=0.8,
    )
    agent, completions = make_agent(memory, memory_policy=policy)

    agent.run("hello", user_id="alice")

    user_message = completions.calls[0]["messages"][-1]["content"]
    assert "current user preference" in user_message
    assert "self reflection should stay private" not in user_message
    assert "wrong agent memory" not in user_message
    assert "low confidence memory" not in user_message


def test_memory_policy_filters_expired_memory_results():
    future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    memory = RecordingMemory([
        {"memory": "fresh memory", "metadata": {"user_id": "alice", "expires_at": future}},
        {"memory": "expired memory", "metadata": {"user_id": "alice", "expires_at": past}},
        {"memory": "missing expiry", "metadata": {"user_id": "alice"}},
    ])
    policy = MemoryPolicy(enforce_expires_at=True)
    agent, completions = make_agent(memory, memory_policy=policy)

    agent.run("hello", user_id="alice")

    user_message = completions.calls[0]["messages"][-1]["content"]
    assert "fresh memory" in user_message
    assert "expired memory" not in user_message
    assert "missing expiry" not in user_message


def test_memory_policy_rejects_missing_scope_metadata_when_filters_are_enabled():
    memory = RecordingMemory([
        {"memory": "legacy unattributed memory", "metadata": {"user_id": "tenant-a:alice"}},
    ])
    policy = MemoryPolicy(
        namespace="tenant-a",
        allow_unattributed_results=True,
        allowed_sources=("user",),
    )
    agent, completions = make_agent(memory, memory_policy=policy)

    agent.run("hello", user_id="alice")

    assert "legacy unattributed memory" not in completions.calls[0]["messages"][-1]["content"]


def test_memory_scope_exports_recommended_metadata_shape():
    scope = MemoryScope.reflection(
        agent_name="writer",
        trace_id="reflection-trace",
        parent_trace_id="parent-trace",
        project_id="docs",
    )

    assert scope.to_metadata() == {
        "project_id": "docs",
        "source": "reflection",
        "scope": "agent",
        "agent_name": "writer",
        "trace_id": "reflection-trace",
        "parent_trace_id": "parent-trace",
    }


def test_memory_write_admission_can_block_reflection_memory_writes():
    def block_reflection(data, context):
        if context["source"] == "reflection":
            return "reflection memory writes require review"
        return True

    memory = RecordingMemory([])
    policy = MemoryPolicy(memory_write_admission=block_reflection)
    agent, _ = make_agent(memory, memory_policy=policy)
    agent.self_learning = True

    result = agent.run("hello", user_id="alice", result_format="object", trace=True)

    assert result.content == "done"
    assert len(memory.store_calls) == 1
    assert memory.store_calls[0]["user_id"] == "alice"
    block_events = [event for event in result.trace if event["type"] == "memory_write_block"]
    assert block_events[0]["data"]["source"] == "reflection"
    assert "require review" in block_events[0]["data"]["reason"]


def test_memory_policy_limits_writes_per_run():
    memory = RecordingMemory([])
    policy = MemoryPolicy(max_writes_per_run=1)
    agent, _ = make_agent(memory, memory_policy=policy)
    agent.self_learning = True

    result = agent.run("hello", user_id="alice", result_format="object", trace=True)

    assert result.content == "done"
    assert len(memory.store_calls) == 1
    assert memory.store_calls[0]["user_id"] == "alice"
    assert "Memory write limit exceeded" in [
        event["data"]["reason"] for event in result.trace if event["type"] == "memory_write_block"
    ][0]


def test_memory_write_admission_can_rewrite_memory_before_store():
    def normalize(data, context):
        return MemoryAdmissionDecision(allowed=True, value=f"{context['source']}::{data.upper()}")

    memory = RecordingMemory([])
    policy = MemoryPolicy(memory_write_admission=normalize)
    agent, _ = make_agent(memory, memory_policy=policy)

    agent.run("hello", user_id="alice")

    assert memory.store_calls[0]["data"] == "user::HELLO"


def test_memory_policy_duplicate_fingerprints_are_scope_aware():
    policy = MemoryPolicy(reject_duplicate_writes=True)
    first_context = {"memory_user_id": "alice", "source": "user", "scope": "user", "agent_name": "agent"}
    second_context = {"memory_user_id": "alice", "source": "user", "scope": "user", "agent_name": "agent"}
    reflection_context = {"memory_user_id": "agent", "source": "reflection", "scope": "agent", "agent_name": "agent"}
    fingerprints = set()

    first = policy.allows_write("Remember   This", first_context, recent_fingerprints=fingerprints)
    assert first.allowed is True
    fingerprints.add(policy.write_fingerprint(first.value, first_context))

    duplicate = policy.allows_write("remember this", second_context, recent_fingerprints=fingerprints)
    reflection = policy.allows_write("remember this", reflection_context, recent_fingerprints=fingerprints)

    assert duplicate.allowed is False
    assert reflection.allowed is True


def test_memory_policy_blocks_low_quality_memory_writes():
    short_policy = MemoryPolicy(min_write_length=8)
    pattern_policy = MemoryPolicy(reject_write_patterns=(r"ignore previous instructions",))

    short = short_policy.allows_write("short", {})
    rejected = pattern_policy.allows_write("please ignore previous instructions", {})

    assert short.allowed is False
    assert "min_write_length" in short.reason
    assert rejected.allowed is False
    assert "rejected by pattern" in rejected.reason


def test_tool_loader_rejects_unsafe_tool_names():
    loader = ToolLoader()

    with pytest.raises(ValueError):
        loader.load_tool("../secret")
