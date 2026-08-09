## Lightweight Connector Contract

LightAgent v0.9.7 provides a dependency-free connector manifest for grouping
existing extension primitives. A connector is not a second plugin runtime and
does not automatically install dependencies, connect to MCP servers, register
tools, or execute hooks.

### Manifest Fields

| Field | Purpose |
| --- | --- |
| `name`, `version`, `description` | Stable connector identity and summary. |
| `tools` | Python callables with existing `tool_info` metadata. |
| `skills` | `Skill` objects or local directories containing `SKILL.md`. |
| `mcp_servers` | Existing MCP server settings without the outer `mcpServers` key. |
| `hooks` | Callables or objects implementing existing lifecycle hook phases. |
| `memory_adapters` | Named objects implementing `store()` and `retrieve()`. |
| `extras` | Descriptive optional dependency groups. Validation never installs them. |
| `docs` | Local usage documents, resolved relative to a supplied base path. |

### Build A Connector In 10 Minutes

1. Create one or more ordinary LightAgent tools.
2. Add optional Skills, hooks, MCP settings, or memory adapters.
3. Put those components in a `ConnectorManifest`.
4. Run offline validation before passing selected components to an agent.

```python
from pathlib import Path

from LightAgent import ConnectorManifest, LightAgent, validate_connector


def search_records(query: str) -> str:
    return f"local result for: {query}"


search_records.tool_info = {
    "tool_name": "search_records",
    "tool_description": "Search local records.",
    "tool_params": [{
        "name": "query",
        "type": "string",
        "description": "Search query.",
        "required": True,
    }],
}

connector = ConnectorManifest(
    name="records",
    version="1.0.0",
    description="Local records connector.",
    tools=[search_records],
    docs=["README.md"],
)

report = validate_connector(connector, base_path=Path(__file__).parent)
if not report.valid:
    raise ValueError(report.to_dict())

agent = LightAgent(
    model="your-model",
    api_key="your-api-key",
    base_url="your-base-url",
    tools=list(connector.tools),
)
```

Applications explicitly choose what to activate. For example, pass
`connector.hooks` to `LightAgent(..., hooks=...)`, choose one named memory
adapter for `memory=...`, load connector Skill directories with the existing
`SkillManager`, and wrap MCP settings as follows:

```python
await agent.setup_mcp({"mcpServers": dict(connector.mcp_servers)})
```

### Offline Diagnostics

`validate_connector()` returns a `ConnectorValidationReport` with `valid`,
`errors`, `warnings`, and `to_dict()`. It checks:

- connector identity and semantic version shape;
- tool schemas and duplicate tool names;
- local `SKILL.md` and documentation paths;
- MCP transport shape and credential-like literal values;
- hook and memory-adapter protocols;
- optional dependency declarations;
- static source hints for process, filesystem, dynamic import, and network use.

Warnings are review prompts, not proof that a connector is malicious. Static
source inspection is incomplete and must not replace code review, dependency
pinning, runtime authorization, network restrictions, or secret management.

### Examples

- `example/connectors/local_research` bundles an offline search tool and Skill.
- `example/connectors/enterprise_api` injects a fake-by-default API client and
  shows how optional provider transport remains application-owned.

The core repository does not provide a connector marketplace, hosted runtime,
automatic provider discovery, or automatic dependency installation.
