import importlib.util
import sys
from pathlib import Path


def load_example_module():
    example_path = Path(__file__).resolve().parents[1] / "example" / "11.vector_memory_adapter.py"
    spec = importlib.util.spec_from_file_location("vector_memory_adapter_example", example_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_local_vector_memory_adapter_scopes_results_by_user():
    module = load_example_module()
    memory = module.LocalVectorMemoryAdapter(agent_name="test-agent")

    memory.store("Alice prefers quiet beach towns", user_id="alice")
    memory.store("Bob prefers crowded ski resorts", user_id="bob")

    results = memory.retrieve("quiet beach", user_id="alice")["results"]

    assert [item["memory"] for item in results] == ["Alice prefers quiet beach towns"]
    assert results[0]["metadata"]["source"] == "user"
    assert results[0]["metadata"]["scope"] == "user"
    assert results[0]["metadata"]["user_id"] == "alice"


def test_local_vector_memory_adapter_orders_by_similarity():
    module = load_example_module()
    memory = module.LocalVectorMemoryAdapter(agent_name="test-agent")

    memory.store("Python graph extraction tests", user_id="alice")
    memory.store("Python Python graph graph extraction", user_id="alice")

    results = memory.retrieve("python graph", user_id="alice")["results"]

    assert results[0]["memory"] == "Python Python graph graph extraction"
    assert results[0]["score"] >= results[1]["score"]
