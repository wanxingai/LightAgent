import asyncio
import importlib.util
import json
import stat
import sys
from pathlib import Path

from LightAgent.tools import ToolRegistry


def load_example_module():
    path = Path(__file__).resolve().parents[1] / "example" / "deed_page_mcp.py"
    spec = importlib.util.spec_from_file_location("deed_page_mcp_example", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def schema(name):
    return {"type": "function", "function": {"name": name, "parameters": {"type": "object", "properties": {}}}}


def test_config_without_token_has_no_auth_header():
    module = load_example_module()
    config = module.deed_page_mcp_config(env={})
    server = config["mcpServers"]["deedpage"]
    assert server == {
        "transport": "streamable-http", "url": "https://deed.page/mcp",
        "namespace": "deedpage", "namespace_tools": True,
    }


def test_config_reads_token_from_environment_mapping():
    module = load_example_module()
    config = module.deed_page_mcp_config(env={"DEEDPAGE_TOKEN": " abc123 "})
    assert config["mcpServers"]["deedpage"]["headers"] == {"Authorization": "Bearer abc123"}


def test_split_token_removes_owner_token():
    module = load_example_module()
    text = json.dumps({"url": "https://example.deed.page/", "token": "secret-token"})
    cleaned, token = module.split_token(text)
    assert token == "secret-token"
    assert "secret-token" not in cleaned
    assert json.loads(cleaned) == {"url": "https://example.deed.page/"}


def test_split_token_leaves_other_text_unchanged():
    module = load_example_module()
    assert module.split_token("not json") == ("not json", None)
    plain = json.dumps({"url": "https://example.deed.page/"})
    assert module.split_token(plain) == (plain, None)


def test_save_token_is_owner_only(tmp_path):
    module = load_example_module()
    path = module.save_token("secret-token", tmp_path / "token")
    assert path.read_text(encoding="utf-8") == "secret-token"
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_restrict_new_tools_keeps_local_and_allowed_tools():
    module = load_example_module()
    registry = ToolRegistry()
    for name in ("local_tool", "publish_site", "other__delete_site", "deedpage__publish_site", "deedpage__get_site",
                 "deedpage__delete_site", "deedpage__rotate_token"):
        registry.function_mappings[name] = object()
        registry.function_info[name] = {"tool_name": name}
        registry.openai_function_schemas.append(schema(name))

    removed = module.restrict_new_tools(registry, before={"local_tool"}, allowed=module.DEFAULT_ALLOWED_TOOLS)

    assert sorted(removed) == ["deedpage__delete_site", "deedpage__rotate_token"]
    expected = ["deedpage__get_site", "deedpage__publish_site", "local_tool", "other__delete_site", "publish_site"]
    assert sorted(registry.function_mappings) == expected
    assert sorted(registry.function_info) == expected
    assert sorted(s["function"]["name"] for s in registry.openai_function_schemas) == [
        *expected,
    ]


def test_protect_publish_token_saves_token_and_hides_it(tmp_path):
    module = load_example_module()
    registry = ToolRegistry()
    calls = []

    async def fake_publish_site(**kwargs):
        calls.append(kwargs)
        return {
            "server": "deedpage",
            "tool": "publish_site",
            "result": json.dumps({"url": "https://example.deed.page/", "token": "secret-token"}),
        }

    registry.function_mappings["deedpage__publish_site"] = fake_publish_site
    token_file = tmp_path / "token"
    assert module.protect_publish_token(registry, token_file) is True

    result = asyncio.run(registry.function_mappings["deedpage__publish_site"](files={"index.html": "<h1>x</h1>"}))

    assert calls == [{"files": {"index.html": "<h1>x</h1>"}}]
    assert "secret-token" not in result["result"]
    assert token_file.read_text(encoding="utf-8") == "secret-token"


def test_protect_publish_token_is_noop_without_publish_tool(tmp_path):
    module = load_example_module()
    assert module.protect_publish_token(ToolRegistry(), tmp_path / "token") is False
