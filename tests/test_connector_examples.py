import importlib.util
import sys
from pathlib import Path

from LightAgent import LightAgent, validate_connector


ROOT = Path(__file__).parents[1]


def load_example(name, relative_path):
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_local_research_connector_is_valid_and_searches_offline():
    module = load_example(
        "lightagent_local_research_connector",
        "example/connectors/local_research/connector.py",
    )

    report = validate_connector(module.connector, base_path=module.BASE_PATH)

    assert report.valid is True
    assert report.diagnostics == ()
    assert "lightweight Python agent framework" in module.search_local_notes("LightAgent")
    assert module.search_local_notes("unmatched-term") == "No local notes matched."


def test_enterprise_connector_uses_injected_client_without_credentials():
    module = load_example(
        "lightagent_enterprise_api_connector",
        "example/connectors/enterprise_api/connector.py",
    )

    class RecordingClient:
        def __init__(self):
            self.calls = []

        def get_ticket(self, ticket_id):
            self.calls.append(ticket_id)
            return {"id": ticket_id, "status": "open"}

    client = RecordingClient()
    connector = module.create_connector(client)
    report = validate_connector(connector, base_path=module.BASE_PATH)

    assert report.valid is True
    assert report.diagnostics == ()
    assert connector.tools[0]("INC-42") == {"id": "INC-42", "status": "open"}
    assert client.calls == ["INC-42"]


def test_connector_tools_use_existing_lightagent_registry():
    module = load_example(
        "lightagent_registry_connector",
        "example/connectors/local_research/connector.py",
    )

    agent = LightAgent(
        model="gpt-4o-mini",
        api_key="test-key",
        base_url="http://127.0.0.1:9/v1",
        tools=list(module.connector.tools),
        auto_discover_skills=False,
    )

    assert agent.get_tool("search_local_notes") is module.search_local_notes
    assert any(
        schema["function"]["name"] == "search_local_notes"
        for schema in agent.get_tools()
    )
