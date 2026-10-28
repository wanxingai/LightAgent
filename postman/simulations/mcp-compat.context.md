# MCP compatibility simulation

Local contract fixture for MCP SDK interoperability, validated 2026-10-28.

## Purpose

Exercise the real `MCPClientManager` and SDK HTTP transport against the
stateless JSON-RPC contract in `postman/mocks/mcp-contract/default.js`.
The owning-mock search was unavailable because Postman was signed out; this
fixture models the MCP initialize/list/call contract, not a vendor service.

## Execution

```bash
postman simulation run postman/simulations/mcp-compat.sim.yaml --port auto --no-history --output ndjson
# Use the listening event's port; /remote selects the member and /mcp is its endpoint.
PYTHONPATH=. python tests/mcp_http_probe.py http://127.0.0.1:PORT/remote/mcp
```

Run the probe in separate environments with MCP 1.12.4, 1.30.0, and 2.3.0.
Stop the simulation with Ctrl-C. No login, deployment, production credentials,
or external server is required. The probe accepts only local URLs.

## Assumptions

- The stand-in echoes the client's supported protocol version and uses JSON
  responses without sessions. Stateful SSE, OAuth, and real service behavior
  are outside this check. (contract fixture, 2026-10-28)
- `X-LightAgent-Test` carries a non-secret sentinel; a provider overrides the
  static value. No real credential belongs in this fixture. (observed 2026-10-28)
- Legacy SDK tests need the historical Pydantic combination. CI pins 2.10.4
  from poetry.lock for MCP 1.12.4; modern SDK jobs use 2.12+. (observed 2026-10-28)

## Observations

<!-- begin:observations -->
2026-10-28: the only member served initialize, initialized, tools/list, and
tools/call for all three SDK versions after the schema-field compatibility fix.
The echo confirmed credential-header propagation and the probe confirmed cleanup.
<!-- end:observations -->

## What didn't work

- 2026-10-28: the CLI rejected a directory-valued mock path; the simulation now
  names `config.yaml` explicitly.
- 2026-10-28: MCP 2.3.0 connected but failed before tools/call with
  `AttributeError: 'Tool' object has no attribute 'inputSchema'`. The manager
  now supports the SDK's `input_schema` field as well as the older spelling.
- 2026-10-28: fresh MCP 1.12.4 installation with latest Pydantic failed to
  import `eval_type_backport` before any request. The historical dependency
  job now retains the repository's locked Pydantic rather than latest.
