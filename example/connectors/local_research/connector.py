"""Dependency-free local research connector example."""

from pathlib import Path

from LightAgent import ConnectorManifest, validate_connector


BASE_PATH = Path(__file__).parent
LOCAL_CORPUS = {
    "lightagent": "LightAgent is a lightweight Python agent framework.",
    "connectors": "Connectors bundle existing tools, skills, hooks, MCP settings, and adapters.",
    "security": "Connector validation is offline and does not execute bundled tools.",
}


def search_local_notes(query: str) -> str:
    """Search a small in-process corpus without making a network request."""
    terms = {term.lower() for term in query.split() if term.strip()}
    matches = [text for key, text in LOCAL_CORPUS.items() if key in terms or any(term in text.lower() for term in terms)]
    return "\n".join(matches) if matches else "No local notes matched."


search_local_notes.tool_info = {
    "tool_name": "search_local_notes",
    "tool_description": "Search the connector's local research notes.",
    "tool_params": [{
        "name": "query",
        "type": "string",
        "description": "Words to find in the local notes.",
        "required": True,
    }],
}


connector = ConnectorManifest(
    name="local-research",
    version="1.0.0",
    description="Offline research tool and reusable research Skill.",
    tools=[search_local_notes],
    skills=["skills/local-research"],
    docs=["README.md"],
)


if __name__ == "__main__":
    print(validate_connector(connector, base_path=BASE_PATH).to_dict())
