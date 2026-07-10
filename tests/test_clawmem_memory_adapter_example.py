import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

from LightAgent import LightAgent, MemoryPolicy


def load_example_module():
    example_path = Path(__file__).resolve().parents[1] / "example" / "clawmem_memory_adapter.py"
    spec = importlib.util.spec_from_file_location("clawmem_memory_adapter_example", example_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FakeClawMemClient:
    def __init__(self):
        self.created_payloads = []
        self.search_calls = []
        self.search_results = []

    def create_memory(self, payload):
        self.created_payloads.append(payload)
        return {"id": f"memory-{len(self.created_payloads)}"}

    def search_memories(self, query, *, user_id, limit, metadata_filter=None):
        self.search_calls.append({
            "query": query,
            "user_id": user_id,
            "limit": limit,
            "metadata_filter": metadata_filter,
        })
        return self.search_results[:limit]


class StaticCompletions:
    def __init__(self, content="done"):
        self.calls = []
        self.content = content

    def create(self, **params):
        self.calls.append(params)
        message = SimpleNamespace(content=self.content, tool_calls=None)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def test_clawmem_adapter_stores_memory_with_policy_metadata():
    module = load_example_module()
    client = FakeClawMemClient()
    adapter = module.ClawMemMemoryAdapter(client, agent_name="travel-agent")

    result = adapter.store(
        "Alice prefers quiet beach towns",
        user_id="tenant:alice",
        metadata={
            "source": "user",
            "scope": "user",
            "agent_name": "travel-agent",
            "trace_id": "trace-1",
            "original_user_id": "alice",
        },
    )

    payload = client.created_payloads[0]
    assert result == {"stored": True, "user_id": "tenant:alice", "memory_id": "memory-1"}
    assert payload["title"] == "Alice prefers quiet beach towns"
    assert payload["content"] == "Alice prefers quiet beach towns"
    assert payload["user_id"] == "tenant:alice"
    assert payload["metadata"]["source"] == "user"
    assert payload["metadata"]["scope"] == "user"
    assert payload["metadata"]["agent_name"] == "travel-agent"
    assert payload["metadata"]["trace_id"] == "trace-1"
    assert "source:user" in payload["tags"]
    assert "scope:user" in payload["tags"]
    assert "agent:travel-agent" in payload["tags"]


def test_clawmem_adapter_returns_memory_policy_compatible_results():
    module = load_example_module()
    client = FakeClawMemClient()
    client.search_results = [
        {
            "content": "Alice prefers quiet beach towns",
            "score": 0.91,
            "user_id": "tenant:alice",
            "metadata": {
                "source": "user",
                "scope": "user",
                "agent_name": "travel-agent",
                "user_id": "tenant:alice",
            },
        }
    ]
    adapter = module.ClawMemMemoryAdapter(client, agent_name="travel-agent", top_k=3)

    results = adapter.retrieve("quiet beach", user_id="tenant:alice")

    assert client.search_calls == [{
        "query": "quiet beach",
        "user_id": "tenant:alice",
        "limit": 3,
        "metadata_filter": {
            "source": "user",
            "scope": "user",
            "agent_name": "travel-agent",
        },
    }]
    assert results["results"] == [{
        "memory": "Alice prefers quiet beach towns",
        "score": 0.91,
        "user_id": "tenant:alice",
        "metadata": {
            "source": "user",
            "scope": "user",
            "agent_name": "travel-agent",
            "user_id": "tenant:alice",
        },
    }]


def test_clawmem_adapter_works_with_lightagent_memory_policy():
    module = load_example_module()
    client = FakeClawMemClient()
    client.search_results = [
        {
            "content": "Alice prefers quiet beach towns",
            "score": 0.95,
            "user_id": "tenant:alice",
            "metadata": {
                "source": "user",
                "scope": "user",
                "agent_name": "travel-agent",
                "user_id": "tenant:alice",
            },
        },
        {
            "content": "Reflection draft should stay private",
            "score": 0.99,
            "user_id": "tenant:alice",
            "metadata": {
                "source": "reflection",
                "scope": "agent",
                "agent_name": "travel-agent",
                "user_id": "tenant:alice",
            },
        },
    ]
    memory = module.ClawMemMemoryAdapter(client, agent_name="travel-agent")
    agent = LightAgent(
        name="travel-agent",
        model="gpt-4o-mini",
        api_key="test-key",
        base_url="http://127.0.0.1:9/v1",
        memory=memory,
        memory_policy=MemoryPolicy(
            namespace="tenant",
            allow_unattributed_results=False,
            allowed_sources=("user",),
            allowed_scopes=("user",),
            allowed_agent_names=("travel-agent",),
        ),
        auto_discover_skills=False,
    )
    completions = StaticCompletions("done")
    agent.client = SimpleNamespace(chat=SimpleNamespace(completions=completions))

    result = agent.run("Where should I travel next?", user_id="alice", result_format="object", trace=True)

    prompt = completions.calls[0]["messages"][-1]["content"]
    assert result.content == "done"
    assert "Alice prefers quiet beach towns" in prompt
    assert "Reflection draft should stay private" not in prompt
    assert client.created_payloads[0]["user_id"] == "tenant:alice"
    assert client.created_payloads[0]["metadata"]["original_user_id"] == "alice"
