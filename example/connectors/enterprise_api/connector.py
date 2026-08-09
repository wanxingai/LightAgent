"""Enterprise API connector skeleton with injected, fake-by-default transport."""

from pathlib import Path
from typing import Protocol

from LightAgent import ConnectorManifest, validate_connector


BASE_PATH = Path(__file__).parent


class TicketClient(Protocol):
    def get_ticket(self, ticket_id: str) -> dict:
        ...


class FakeTicketClient:
    """Local client used by docs and tests; it never performs network I/O."""

    def get_ticket(self, ticket_id: str) -> dict:
        return {"id": ticket_id, "status": "demo", "source": "fake-client"}


def create_connector(client: TicketClient | None = None) -> ConnectorManifest:
    selected_client = client or FakeTicketClient()

    def get_enterprise_ticket(ticket_id: str) -> dict:
        return selected_client.get_ticket(ticket_id)

    get_enterprise_ticket.tool_info = {
        "tool_name": "get_enterprise_ticket",
        "tool_description": "Read one enterprise ticket through an injected client.",
        "tool_params": [{
            "name": "ticket_id",
            "type": "string",
            "description": "Enterprise ticket identifier.",
            "required": True,
        }],
    }
    return ConnectorManifest(
        name="enterprise-api",
        version="1.0.0",
        description="Credential-free enterprise API connector skeleton.",
        tools=[get_enterprise_ticket],
        extras={"http": ["httpx>=0.28.0"]},
        docs=["README.md"],
    )


connector = create_connector()


if __name__ == "__main__":
    print(validate_connector(connector, base_path=BASE_PATH).to_dict())
