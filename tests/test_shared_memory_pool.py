from types import SimpleNamespace

from LightAgent import LightAgent, MemoryPolicy, SharedMemoryPool


class StaticCompletions:
    def __init__(self, content="done"):
        self.calls = []
        self.content = content

    def create(self, **params):
        self.calls.append(params)
        message = SimpleNamespace(content=self.content, tool_calls=None)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def make_agent(memory, *, self_learning=False, memory_policy=None):
    agent = LightAgent(
        name="writer",
        model="gpt-4o-mini",
        api_key="test-key",
        base_url="http://127.0.0.1:9/v1",
        memory=memory,
        memory_policy=memory_policy,
        self_learning=self_learning,
        auto_discover_skills=False,
    )
    completions = StaticCompletions()
    agent.client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    return agent, completions


def test_shared_memory_pool_scopes_records_by_user():
    pool = SharedMemoryPool(agent_name="writer")

    pool.store("Alice prefers quiet beach towns", user_id="alice")
    pool.store("Bob prefers crowded ski resorts", user_id="bob")

    results = pool.retrieve("quiet beach", user_id="alice")["results"]

    assert [item["memory"] for item in results] == ["Alice prefers quiet beach towns"]
    assert results[0]["metadata"]["source"] == "user"
    assert results[0]["metadata"]["scope"] == "user"
    assert results[0]["metadata"]["agent_name"] == "writer"
    assert results[0]["metadata"]["user_id"] == "alice"


def test_shared_memory_pool_is_append_first_and_orders_by_overlap():
    pool = SharedMemoryPool(max_results=2)

    first = pool.store("Python graph extraction tests", user_id="alice")
    second = pool.store("Python Python graph graph extraction", user_id="alice")

    results = pool.retrieve("python graph", user_id="alice")["results"]

    assert len(pool) == 2
    assert first["memory_id"] != second["memory_id"]
    assert results[0]["memory"] == "Python Python graph graph extraction"
    assert results[1]["memory"] == "Python graph extraction tests"


def test_shared_memory_pool_filters_by_provenance():
    pool = SharedMemoryPool()
    pool.store(
        "User approved product name",
        user_id="tenant:alice",
        metadata={"source": "user", "scope": "user", "agent_name": "writer"},
    )
    pool.store(
        "Reflection draft should stay private",
        user_id="tenant:alice",
        metadata={"source": "reflection", "scope": "agent", "agent_name": "writer"},
    )

    results = pool.retrieve(
        "product name reflection",
        user_id="tenant:alice",
        source="user",
        scope="user",
        agent_name="writer",
    )["results"]

    assert [item["memory"] for item in results] == ["User approved product name"]


def test_lightagent_writes_memory_scope_metadata_to_shared_memory_pool():
    pool = SharedMemoryPool()
    policy = MemoryPolicy(
        namespace="tenant",
        allow_unattributed_results=False,
        allowed_sources=("user",),
        allowed_scopes=("user",),
    )
    agent, _ = make_agent(pool, memory_policy=policy)

    result = agent.run("Remember quiet launch notes", user_id="alice", result_format="object", trace=True)

    assert result.content == "done"
    stored = pool.list_records(user_id="tenant:alice")
    assert len(stored) == 1
    assert stored[0]["metadata"]["source"] == "user"
    assert stored[0]["metadata"]["scope"] == "user"
    assert stored[0]["metadata"]["agent_name"] == "writer"
    assert stored[0]["metadata"]["user_id"] == "tenant:alice"
    assert stored[0]["metadata"]["original_user_id"] == "alice"
    assert [event["type"] for event in result.trace if event["type"] == "memory_write"] == ["memory_write"]


def test_lightagent_keeps_reflection_memory_separate_in_shared_pool():
    pool = SharedMemoryPool()
    policy = MemoryPolicy(namespace="tenant", allow_unattributed_results=False)
    agent, _ = make_agent(pool, self_learning=True, memory_policy=policy)

    agent.run("Remember quiet launch notes", user_id="alice")

    user_records = pool.list_records(user_id="tenant:alice")
    agent_records = pool.list_records(user_id="tenant:writer")

    assert user_records[0]["metadata"]["source"] == "user"
    assert user_records[0]["metadata"]["scope"] == "user"
    assert agent_records[0]["metadata"]["source"] == "reflection"
    assert agent_records[0]["metadata"]["scope"] == "agent"
