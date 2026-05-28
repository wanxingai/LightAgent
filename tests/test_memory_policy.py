from types import SimpleNamespace

import pytest

from LightAgent import LightAgent, MemoryPolicy, ToolLoader


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


def test_tool_loader_rejects_unsafe_tool_names():
    loader = ToolLoader()

    with pytest.raises(ValueError):
        loader.load_tool("../secret")
