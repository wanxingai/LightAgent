# Local Research Connector

**v1.0.0 (2026-11-15):** [Released on GitHub](https://github.com/wanxingai/LightAgent/releases/tag/v1.0.0).
Skills and PyYAML are included in the base install. This local connector does
not require MCP or the separate LightResearch extension; see the
[v1.0.0 overview](../../../README.md#v100-durable-execution-and-recovery).

This example bundles an offline search-style Python tool and a local Skill. It
does not use credentials, provider SDKs, or network services.

```python
from LightAgent import LightAgent, validate_connector
from connector import BASE_PATH, connector

report = validate_connector(connector, base_path=BASE_PATH)
if not report.valid:
    raise ValueError(report.to_dict())

agent = LightAgent(
    model="your-model",
    api_key="your-api-key",
    base_url="your-base-url",
    tools=list(connector.tools),
    skills_directories=[str(BASE_PATH / "skills")],
)
```

The manifest does not automatically register or execute its components. The
application remains responsible for selecting and configuring them.
