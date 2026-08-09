from pathlib import Path

from LightAgent import (
    ConnectorManifest,
    ConnectorValidator,
    Skill,
    validate_connector,
)


def make_tool(name="search_local", description="Search a local corpus."):
    def tool(query):
        return query

    tool.tool_info = {
        "tool_name": name,
        "tool_description": description,
        "tool_params": [{
            "name": "query",
            "type": "string",
            "description": "Local search query.",
            "required": True,
        }],
    }
    return tool


def write_connector_files(tmp_path: Path):
    docs = tmp_path / "README.md"
    docs.write_text("# Connector\n", encoding="utf-8")
    skill_dir = tmp_path / "skills" / "research"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: research\ndescription: Search local notes.\n---\n\nUse local evidence.\n",
        encoding="utf-8",
    )
    return docs, skill_dir


def test_valid_connector_manifest_has_no_diagnostics(tmp_path):
    _, skill_dir = write_connector_files(tmp_path)

    class MemoryAdapter:
        def store(self, data, user_id):
            return None

        def retrieve(self, query, user_id):
            return []

    manifest = ConnectorManifest(
        name="local-research",
        version="1.0.0",
        description="Offline local research primitives.",
        tools=[make_tool()],
        skills=[Skill("research", "Search local notes.", str(skill_dir))],
        mcp_servers={"local": {"command": "python", "args": ["server.py"], "disabled": True}},
        hooks=[lambda context: None],
        memory_adapters={"local": MemoryAdapter()},
        extras={"search": ["local-search>=1.0"]},
        docs=["README.md"],
    )

    report = validate_connector(manifest, base_path=tmp_path)

    assert report.valid is True
    assert report.diagnostics == ()
    assert report.to_dict() == {
        "connector": "local-research",
        "valid": True,
        "diagnostics": [],
    }


def test_manifest_normalizes_component_sequences():
    tool = make_tool()
    hook = lambda context: None
    manifest = ConnectorManifest("demo", "1.2.3", "Demo.", tools=tool, hooks=hook, docs="README.md")

    assert manifest.tools == (tool,)
    assert manifest.hooks == (hook,)
    assert manifest.docs == ("README.md",)


def test_connector_reports_identity_and_missing_docs():
    report = validate_connector(ConnectorManifest(name="bad/name", version="latest"))

    assert report.valid is False
    assert {item.field for item in report.errors} == {"name", "version"}
    assert {item.field for item in report.warnings} == {"description", "docs"}


def test_connector_reuses_tool_schema_validation_and_detects_duplicates(tmp_path):
    (tmp_path / "README.md").write_text("docs", encoding="utf-8")
    first = make_tool(description="")
    second = make_tool()

    report = validate_connector(
        ConnectorManifest("duplicate-tools", "1.0.0", "Demo.", tools=[first, second], docs=["README.md"]),
        base_path=tmp_path,
    )

    assert report.valid is False
    assert any(item.field == "tools" and "duplicate tool name" in item.message for item in report.errors)
    assert any(item.field.endswith("tool_description") for item in report.warnings)


def test_connector_validation_never_invokes_tool_or_hook(tmp_path):
    (tmp_path / "README.md").write_text("docs", encoding="utf-8")
    calls = []

    def tool(query):
        calls.append(("tool", query))

    tool.tool_info = make_tool().tool_info

    def hook(context):
        calls.append(("hook", context))

    report = validate_connector(
        ConnectorManifest("offline", "1.0.0", "Offline.", tools=[tool], hooks=[hook], docs=["README.md"]),
        base_path=tmp_path,
    )

    assert report.valid is True
    assert calls == []


def test_connector_warns_about_unsafe_and_network_import_hints(tmp_path):
    (tmp_path / "README.md").write_text("docs", encoding="utf-8")

    def external_tool(query):
        import os
        import requests
        return os.getenv(query) or requests.__name__

    external_tool.tool_info = make_tool("external_tool").tool_info
    report = validate_connector(
        ConnectorManifest("external", "1.0.0", "External.", tools=[external_tool], docs=["README.md"]),
        base_path=tmp_path,
    )

    messages = [item.message for item in report.warnings]
    assert any("host operating-system access" in message for message in messages)
    assert any("network client `requests`" in message for message in messages)


def test_connector_checks_mcp_shape_and_literal_credentials(tmp_path):
    (tmp_path / "README.md").write_text("docs", encoding="utf-8")
    manifest = ConnectorManifest(
        "mcp-demo",
        "1.0.0",
        "MCP demo.",
        mcp_servers={
            "ambiguous": {"url": "https://example.invalid/sse", "command": "server"},
            "literal": {
                "url": "https://example.invalid/sse",
                "headers": {"Authorization": "Bearer live-secret"},
            },
            "placeholder": {
                "url": "https://example.invalid/sse",
                "headers": {"Authorization": "Bearer ${ENTERPRISE_API_TOKEN}"},
            },
        },
        docs=["README.md"],
    )

    report = validate_connector(manifest, base_path=tmp_path)

    assert any(item.field == "mcp_servers.ambiguous" for item in report.errors)
    assert any(item.field.endswith("literal.headers.Authorization") for item in report.warnings)
    assert not any(item.field.endswith("placeholder.headers.Authorization") for item in report.warnings)


def test_connector_checks_skill_adapter_extra_and_hook_contracts(tmp_path):
    (tmp_path / "README.md").write_text("docs", encoding="utf-8")
    report = ConnectorValidator(base_path=tmp_path).validate(ConnectorManifest(
        "invalid-components",
        "1.0.0",
        "Invalid component examples.",
        skills=["missing-skill"],
        hooks=[object()],
        memory_adapters={"broken": object()},
        extras={"bad/extra": "requests", "valid": ["not a requirement ???"]},
        docs=["README.md"],
    ))

    fields = {item.field for item in report.errors}
    assert "skills[0]" in fields
    assert "hooks[0]" in fields
    assert "memory_adapters.broken" in fields
    assert "extras.bad/extra" in fields
    assert "extras.valid[0]" in fields


def test_connector_reports_non_manifest_input():
    report = ConnectorValidator().validate({"name": "demo"})

    assert report.valid is False
    assert report.errors[0].field == "manifest"
