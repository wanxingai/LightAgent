from types import SimpleNamespace
from datetime import datetime, timedelta, timezone

import pytest

from LightAgent import (
    HookDecision,
    LightAgent,
    MemoryAdmissionDecision,
    MemoryPolicy,
    MemoryPromotionDecision,
    MemoryScope,
    PolicyHook,
    ToolLoader,
)


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


class MetadataRecordingMemory(RecordingMemory):
    def store(self, data, user_id, metadata=None):
        self.store_calls.append({"data": data, "user_id": user_id, "metadata": metadata or {}})


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


def test_memory_policy_preserves_legacy_positional_arguments():
    policy = MemoryPolicy(
        "tenant-a",
        False,
        ("user",),
        ("user",),
        ("writer",),
        ("verified",),
        0.8,
        True,
        None,
        7,
        True,
        4,
        (r"ignore previous instructions",),
    )

    assert policy.max_writes_per_run == 7
    assert policy.reject_duplicate_writes is True
    assert policy.min_write_length == 4
    assert policy.reject_write_patterns == (r"ignore previous instructions",)
    assert policy.memory_promotion_admission is None
    assert policy.require_promotion_for_internal_memory is True
    assert policy.require_write_admission is False


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


def test_internal_reflection_memory_becomes_non_injectable_candidate_by_default():
    memory = MetadataRecordingMemory([])
    agent, _ = make_agent(memory)
    agent.self_learning = True

    result = agent.run("hello", user_id="alice", result_format="object", trace=True)

    assert result.content == "done"
    assert len(memory.store_calls) == 1
    assert memory.store_calls[0]["user_id"] == "alice"
    candidates = agent.list_memory_candidates()
    assert len(candidates) == 1
    assert candidates[0]["source"] == "reflection"
    assert candidates[0]["scope"] == "agent"
    assert candidates[0]["status"] == "kept"
    assert candidates[0]["injectable"] is False
    required_event = next(event for event in result.trace if event["type"] == "memory_promotion_required")
    assert "data" not in required_event["data"]
    assert any(event["type"] == "memory_promotion_blocked" for event in result.trace)


def test_memory_promotion_policy_approves_reflection_before_persisting():
    def approve_reflection(candidate, context):
        assert candidate.source == "reflection"
        assert context["candidate_id"] == candidate.candidate_id
        return MemoryPromotionDecision.approve(metadata={"reviewed_by": "policy"})

    memory = MetadataRecordingMemory([])
    policy = MemoryPolicy(memory_promotion_admission=approve_reflection)
    agent, _ = make_agent(memory, memory_policy=policy)
    agent.self_learning = True

    result = agent.run("hello", user_id="alice", result_format="object", trace=True)

    assert result.content == "done"
    assert len(memory.store_calls) == 2
    promoted = memory.store_calls[1]
    assert promoted["user_id"] == agent.name
    assert promoted["metadata"]["source"] == "reflection"
    assert promoted["metadata"]["scope"] == "agent"
    assert promoted["metadata"]["promotion_status"] == "promoted"
    assert promoted["metadata"]["injectable"] is True
    assert promoted["metadata"]["reviewed_by"] == "policy"
    assert agent.list_memory_candidates()[0]["status"] == "promoted"
    assert any(event["type"] == "memory_promotion_approved" for event in result.trace)


def test_memory_promotion_policy_can_rewrite_internal_memory():
    def rewrite_reflection(candidate, context):
        return MemoryPromotionDecision.rewrite(f"reviewed::{candidate.data}")

    memory = MetadataRecordingMemory([])
    policy = MemoryPolicy(memory_promotion_admission=rewrite_reflection)
    agent, _ = make_agent(memory, memory_policy=policy)
    agent.self_learning = True

    result = agent.run("hello", user_id="alice", result_format="object", trace=True)

    assert memory.store_calls[1]["data"] == "reviewed::hello"
    assert memory.store_calls[1]["metadata"]["promotion_decision"] == "rewrite"
    assert any(event["type"] == "memory_promotion_rewritten" for event in result.trace)


def test_before_memory_promote_hook_can_approve_and_rewrite_candidate():
    def approve_with_hook(ctx):
        if ctx.phase == "before_memory_promote":
            return HookDecision.replace({
                **ctx.payload,
                "decision": MemoryPromotionDecision.rewrite(f"hooked::{ctx.payload['data']}"),
            })
        return None

    memory = MetadataRecordingMemory([])
    agent = LightAgent(
        model="gpt-4o-mini",
        api_key="test-key",
        base_url="http://127.0.0.1:9/v1",
        memory=memory,
        self_learning=True,
        auto_discover_skills=False,
        hooks=[approve_with_hook],
    )
    agent.client = SimpleNamespace(chat=SimpleNamespace(completions=StaticCompletions()))

    result = agent.run("hello", user_id="alice", result_format="object", trace=True)

    assert memory.store_calls[1]["data"] == "hooked::hello"
    assert memory.store_calls[1]["metadata"]["promotion_status"] == "promoted"
    assert any(event["type"] == "memory_promotion_rewritten" for event in result.trace)


def test_memory_promotion_closes_promotion_and_write_hook_lifecycles():
    phases = []

    def capture_lifecycle(ctx):
        if ctx.phase in {
            "before_memory_write",
            "before_memory_promote",
            "after_memory_promote",
            "after_memory_write",
        }:
            phases.append(ctx.phase)

    memory = MetadataRecordingMemory([])
    policy = MemoryPolicy(
        memory_promotion_admission=lambda candidate, context: MemoryPromotionDecision.approve()
    )
    agent = LightAgent(
        model="gpt-4o-mini",
        api_key="test-key",
        base_url="http://127.0.0.1:9/v1",
        memory=memory,
        memory_policy=policy,
        self_learning=True,
        auto_discover_skills=False,
        hooks=[capture_lifecycle],
    )
    agent.client = SimpleNamespace(chat=SimpleNamespace(completions=StaticCompletions()))

    agent.run("hello", user_id="alice", result_format="object", trace=True)

    reflection_phases = phases[phases.index("before_memory_promote") - 1:]
    assert reflection_phases == [
        "before_memory_write",
        "before_memory_promote",
        "after_memory_promote",
        "after_memory_write",
    ]


def test_memory_policy_filters_unpromoted_internal_results_before_prompt_injection():
    policy = MemoryPolicy(allow_unattributed_results=True)

    unpromoted_reflection = {
        "memory": "private reflection",
        "metadata": {"user_id": "agent", "source": "reflection", "scope": "agent"},
    }
    explicit_candidate = {
        "memory": "candidate text",
        "metadata": {"user_id": "alice", "source": "user", "scope": "user", "promotion_status": "candidate"},
    }
    promoted_reflection = {
        "memory": "approved reflection",
        "metadata": {
            "user_id": "agent",
            "source": "reflection",
            "scope": "agent",
            "promotion_status": "promoted",
            "injectable": True,
        },
    }

    assert policy.allows_result(unpromoted_reflection, "agent", "agent") is False
    assert policy.allows_result(explicit_candidate, "alice", "alice") is False
    assert policy.allows_result(promoted_reflection, "agent", "agent") is True


def test_business_status_does_not_block_user_memory():
    policy = MemoryPolicy(require_promotion_for_internal_memory=False)
    order_memory = {
        "memory": "Customer order is pending",
        "metadata": {
            "user_id": "alice",
            "source": "user",
            "scope": "user",
            "status": "pending",
        },
    }

    assert policy.allows_result(order_memory, "alice", "alice") is True


def test_legacy_internal_memory_can_use_compatibility_opt_out():
    legacy_reflection = {
        "memory": "Legacy reflection",
        "metadata": {
            "user_id": "writer",
            "source": "reflection",
            "scope": "agent",
        },
    }

    assert MemoryPolicy().allows_result(legacy_reflection, "writer", "writer") is False
    compatibility_policy = MemoryPolicy(require_promotion_for_internal_memory=False)
    assert compatibility_policy.allows_result(legacy_reflection, "writer", "writer") is True


def test_before_memory_promote_policy_hook_can_fail_closed():
    def broken_policy(ctx):
        raise RuntimeError("review service unavailable")

    memory = MetadataRecordingMemory([])
    agent = LightAgent(
        model="gpt-4o-mini",
        api_key="test-key",
        base_url="http://127.0.0.1:9/v1",
        memory=memory,
        self_learning=True,
        auto_discover_skills=False,
        hooks=[PolicyHook(broken_policy, phases={"before_memory_promote"})],
    )
    agent.client = SimpleNamespace(chat=SimpleNamespace(completions=StaticCompletions()))

    result = agent.run("hello", user_id="alice", result_format="object", trace=True)

    assert result.content == "done"
    assert len(memory.store_calls) == 1
    assert agent.list_memory_candidates()[0]["status"] == "blocked"
    assert any(event["type"] == "hook_block" and event["data"]["phase"] == "before_memory_promote" for event in result.trace)
    assert any(event["type"] == "memory_promotion_blocked" for event in result.trace)


def test_memory_promotion_admission_exception_fails_closed():
    def broken_admission(candidate, context):
        raise RuntimeError("review service unavailable")

    memory = MetadataRecordingMemory([])
    policy = MemoryPolicy(memory_promotion_admission=broken_admission)
    agent, _ = make_agent(memory, memory_policy=policy)
    agent.self_learning = True

    result = agent.run("hello", user_id="alice", result_format="object", trace=True)

    assert result.content == "done"
    assert len(memory.store_calls) == 1
    assert agent.list_memory_candidates()[0]["status"] == "kept"
    blocked_event = next(event for event in result.trace if event["type"] == "memory_promotion_blocked")
    assert blocked_event["data"]["reason"] == "Memory promotion admission failed: RuntimeError"
    assert "review service unavailable" not in blocked_event["data"]["reason"]


def test_memory_candidate_can_be_promoted_explicitly_after_run():
    memory = MetadataRecordingMemory([])
    agent, _ = make_agent(memory)
    agent.self_learning = True

    agent.run("hello", user_id="alice", result_format="object", trace=True)
    candidate_id = agent.list_memory_candidates()[0]["candidate_id"]

    promoted = agent.promote_memory_candidate(candidate_id)

    assert promoted is True
    assert len(memory.store_calls) == 2
    assert memory.store_calls[1]["metadata"]["candidate_id"] == candidate_id
    assert memory.store_calls[1]["metadata"]["promotion_status"] == "promoted"
    assert memory.store_calls[1]["metadata"]["injectable"] is True


def test_memory_candidate_promotion_is_idempotent():
    memory = MetadataRecordingMemory([])
    agent, _ = make_agent(memory)
    agent.self_learning = True

    agent.run("hello", user_id="alice")
    candidate_id = agent.list_memory_candidates()[0]["candidate_id"]

    assert agent.promote_memory_candidate(candidate_id) is True
    assert agent.promote_memory_candidate(candidate_id) is True
    assert len(memory.store_calls) == 2
    assert agent.list_memory_candidates()[0]["status"] == "promoted"


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

    result = agent.run("hello", user_id="alice", result_format="object", trace=True)

    assert memory.store_calls[0]["data"] == "user::HELLO"
    adapter_event = next(event for event in result.trace if event["type"] == "hook_decision")
    assert adapter_event["data"]["hook"] == "memory_write_admission"
    assert adapter_event["data"]["action"] == "replace"


def test_required_memory_write_admission_fails_closed():
    policy = MemoryPolicy(require_write_admission=True)

    missing = policy.allows_write("unreviewed", {"user_id": "alice"})

    assert missing.allowed is False
    assert missing.reason == "Memory write requires an explicit admission decision."


def test_required_memory_write_admission_needs_explicit_callback_approval():
    policy = MemoryPolicy(
        require_write_admission=True,
        memory_write_admission=lambda data, context: None,
    )

    undecided = policy.allows_write("unreviewed", {"user_id": "alice"})

    assert undecided.allowed is False
    assert undecided.reason == "Memory write admission did not explicitly approve this write."


def test_memory_write_admission_exception_fails_closed_and_redacts_details():
    def broken_admission(data, context):
        raise RuntimeError("private review service details")

    policy = MemoryPolicy(memory_write_admission=broken_admission)

    decision = policy.allows_write("unreviewed", {"user_id": "alice"})

    assert decision.allowed is False
    assert decision.reason == "Memory write admission failed: RuntimeError"
    assert "private review service details" not in decision.reason


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


def test_memory_write_hook_and_trace_hierarchy_metadata_are_stored():
    def normalize_memory(ctx):
        if ctx.phase == "before_memory_write":
            return {
                "payload": {
                    **ctx.payload,
                    "data": f"normalized::{ctx.payload['data']}",
                }
            }
        return None

    memory = MetadataRecordingMemory([])
    agent = LightAgent(
        model="gpt-4o-mini",
        api_key="test-key",
        base_url="http://127.0.0.1:9/v1",
        memory=memory,
        auto_discover_skills=False,
        hooks=[normalize_memory],
    )
    agent.client = SimpleNamespace(chat=SimpleNamespace(completions=StaticCompletions()))

    result = agent.run(
        "hello",
        user_id="alice",
        result_format="object",
        trace=True,
        parent_trace_id="parent-trace",
        run_group_id="group-1",
    )

    stored = memory.store_calls[0]
    assert stored["data"] == "normalized::hello"
    assert stored["metadata"]["trace_id"] == result.trace_id
    assert stored["metadata"]["parent_trace_id"] == "parent-trace"
    assert stored["metadata"]["run_group_id"] == "group-1"


def test_memory_retrieve_hooks_can_rewrite_and_filter_results():
    calls = []

    def memory_hooks(ctx):
        calls.append((ctx.phase, dict(ctx.payload)))
        if ctx.phase == "before_memory_retrieve":
            return HookDecision.replace({
                **ctx.payload,
                "query": "rewritten query",
                "memory_user_id": "tenant-a:alice",
            })
        if ctx.phase == "after_memory_retrieve":
            memories = dict(ctx.payload["memories"])
            memories["results"] = [
                item for item in memories["results"]
                if item["memory"] == "allowed memory"
            ]
            return HookDecision.replace({**ctx.payload, "memories": memories})
        return None

    memory = RecordingMemory([
        {"memory": "allowed memory", "metadata": {"user_id": "tenant-a:alice"}},
        {"memory": "blocked memory", "metadata": {"user_id": "tenant-a:alice"}},
    ])
    agent = LightAgent(
        model="gpt-4o-mini",
        api_key="test-key",
        base_url="http://127.0.0.1:9/v1",
        memory=memory,
        memory_policy=MemoryPolicy(namespace="tenant-a"),
        auto_discover_skills=False,
        hooks=[memory_hooks],
    )
    completions = StaticCompletions()
    agent.client = SimpleNamespace(chat=SimpleNamespace(completions=completions))

    result = agent.run("hello", user_id="alice", result_format="object", trace=True)

    assert result.content == "done"
    assert memory.retrieve_calls[0] == {"query": "rewritten query", "user_id": "tenant-a:alice"}
    user_message = completions.calls[0]["messages"][-1]["content"]
    assert "allowed memory" in user_message
    assert "blocked memory" not in user_message
    memory_phases = [phase for phase, _ in calls if phase in ("before_memory_retrieve", "after_memory_retrieve")]
    assert memory_phases == ["before_memory_retrieve", "after_memory_retrieve"]
    assert any(event["type"] == "hook_decision" for event in result.trace)


def test_before_memory_retrieve_hook_can_block_prompt_injection():
    def block_retrieve(ctx):
        if ctx.phase == "before_memory_retrieve":
            return HookDecision.block("tenant disabled memory reads")
        return None

    memory = RecordingMemory([{"memory": "should not appear", "metadata": {"user_id": "alice"}}])
    agent = LightAgent(
        model="gpt-4o-mini",
        api_key="test-key",
        base_url="http://127.0.0.1:9/v1",
        memory=memory,
        auto_discover_skills=False,
        hooks=[block_retrieve],
    )
    completions = StaticCompletions()
    agent.client = SimpleNamespace(chat=SimpleNamespace(completions=completions))

    result = agent.run("hello", user_id="alice", result_format="object", trace=True)

    assert result.content == "done"
    assert memory.retrieve_calls == []
    assert "should not appear" not in completions.calls[0]["messages"][-1]["content"]
    assert any(event["type"] == "memory_retrieve_block" for event in result.trace)


def test_tool_loader_rejects_unsafe_tool_names():
    loader = ToolLoader()

    with pytest.raises(ValueError):
        loader.load_tool("../secret")
