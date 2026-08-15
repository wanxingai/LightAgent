# Enterprise API Connector Skeleton

This example keeps provider transport outside the LightAgent core. The default
`FakeTicketClient` is deterministic and makes no network request. Production
applications should inject a client that reads credentials from their secret
manager or environment, applies timeouts, and enforces tenant authorization.

```python
from connector import BASE_PATH, create_connector
from LightAgent import LightAgent, validate_connector

client = MyAuthenticatedTicketClient()  # application-owned implementation
connector = create_connector(client)
report = validate_connector(connector, base_path=BASE_PATH)
if not report.valid:
    raise ValueError(report.to_dict())

agent = LightAgent(
    model="your-model",
    api_key="your-api-key",
    base_url="your-base-url",
    tools=list(connector.tools),
)
```

The optional `http` extra is descriptive metadata for this connector; it does
not install packages or create a client during validation.
