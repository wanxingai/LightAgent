import asyncio
import importlib.util
import json
import os
import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

from LightAgent.tools import ToolRegistry


@pytest.fixture
def example():
    path = Path(__file__).resolve().parents[1] / "example" / "deed_page_mcp.py"
    spec = importlib.util.spec_from_file_location("deed_security", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_token_path_is_outside_working_directory(example):
    assert Path(example.DEFAULT_TOKEN_FILE).is_absolute()
    assert Path(example.DEFAULT_TOKEN_FILE).parent.name == "credentials"


def test_private_directory_and_atomic_token_publication(example, tmp_path):
    path = tmp_path / "private" / "owner"
    example.save_token("test-owner", path)
    assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert example.read_token(path) == "test-owner"
    assert list(path.parent.iterdir()) == [path]
    example.save_token("test-owner", path)


def test_existing_token_is_not_silently_overwritten(example, tmp_path):
    path = example.save_token("old-owner", tmp_path / "owner")
    with pytest.raises(FileExistsError):
        example.save_token("new-owner", path)
    assert example.read_token(path) == "old-owner"


@pytest.mark.parametrize("kind", ["symlink", "directory", "fifo"])
def test_non_regular_token_paths_are_rejected(example, tmp_path, kind):
    path = tmp_path / "owner"
    target = tmp_path / "unrelated"
    target.write_text("unchanged")
    if kind == "symlink":
        path.symlink_to(target)
    elif kind == "directory":
        path.mkdir()
    else:
        os.mkfifo(path)
    with pytest.raises((OSError, ValueError)):
        example.save_token("test-owner", path)
    assert target.read_text() == "unchanged"


def test_existing_world_readable_token_is_not_written(example, tmp_path):
    path = tmp_path / "owner"
    path.write_text("original")
    path.chmod(0o644)
    with pytest.raises(PermissionError):
        example.save_token("new-owner", path)
    assert path.read_text() == "original"


def test_symlink_created_during_publication_is_not_followed(example, tmp_path, monkeypatch):
    path = tmp_path / "owner"
    target = tmp_path / "unrelated"
    target.write_text("unchanged")
    real_link = os.link

    def concurrent_link(source, destination, **kwargs):
        path.symlink_to(target)
        return real_link(source, destination, **kwargs)

    monkeypatch.setattr(example.os, "link", concurrent_link)
    with pytest.raises(OSError):
        example.save_token("test-owner", path)
    assert target.read_text() == "unchanged"
    assert not list(tmp_path.glob(".deedpage-*"))


def test_failed_publication_removes_temporary_file(example, tmp_path, monkeypatch):
    def fail(*args, **kwargs):
        raise OSError("simulated publication failure")

    monkeypatch.setattr(example.os, "link", fail)
    with pytest.raises(OSError):
        example.save_token("test-owner", tmp_path / "owner")
    assert list(tmp_path.iterdir()) == []


def test_credentials_reuse_saved_token_and_prefer_environment(example, tmp_path, monkeypatch):
    monkeypatch.delenv("DEEDPAGE_TOKEN", raising=False)
    path = tmp_path / "owner"
    assert example.credential_headers(path) == {}
    example.save_token("stored-owner", path)
    assert example.credential_headers(path) == {"Authorization": "Bearer stored-owner"}
    config = example.deed_page_mcp_config(env={}, token_file=path)
    assert config["mcpServers"]["deedpage"]["headers"] == {"Authorization": "Bearer stored-owner"}
    monkeypatch.setenv("DEEDPAGE_TOKEN", "environment-owner")
    assert example.credential_headers(path) == {"Authorization": "Bearer environment-owner"}


def test_token_save_failure_does_not_return_secret_or_success(example, tmp_path):
    registry = ToolRegistry()

    async def publish(**kwargs):
        return {"result": json.dumps({"token": "new-secret", "url": "https://example.test"})}

    registry.function_mappings["deedpage__publish_site"] = publish
    path = example.save_token("old-secret", tmp_path / "owner")
    example.protect_publish_token(registry, path)
    with pytest.raises(FileExistsError) as info:
        asyncio.run(registry.function_mappings["deedpage__publish_site"]())
    assert "new-secret" not in str(info.value)
    assert example.read_token(path) == "old-secret"


def test_setup_rejects_reserved_namespace_before_network(example, tmp_path):
    registry = ToolRegistry()
    registry.function_mappings["deedpage__publish_site"] = object()
    agent = SimpleNamespace(tool_registry=registry)
    with pytest.raises(ValueError, match="namespace"):
        asyncio.run(example.setup_deed_page(agent, tmp_path / "owner"))


def test_refresh_reapplies_filter_and_token_protection(example, tmp_path):
    registry = ToolRegistry()
    local = object()
    registry.function_mappings["publish_site"] = local

    class Client:
        async def refresh_tools(self, server):
            assert server == "deedpage"

            async def publish(**kwargs):
                return {"result": json.dumps({"token": "test-owner", "url": "https://example.test"})}

            registry.function_mappings.update({
                "deedpage__publish_site": publish, "deedpage__get_site": object(),
                "deedpage__delete_site": object(),
            })

    agent = SimpleNamespace(tool_registry=registry, mcp_client=Client())
    path = tmp_path / "owner"

    async def scenario():
        await example.refresh_deed_page(agent, path)
        result = await registry.function_mappings["deedpage__publish_site"]()
        assert "test-owner" not in result["result"]

    asyncio.run(scenario())
    assert registry.function_mappings["publish_site"] is local
    assert "deedpage__delete_site" not in registry.function_mappings
    assert example.read_token(path) == "test-owner"


def test_setup_keeps_local_name_and_reuses_token_between_publishes(example, tmp_path, monkeypatch):
    monkeypatch.delenv("DEEDPAGE_TOKEN", raising=False)
    registry = ToolRegistry()
    local = object()
    registry.function_mappings["publish_site"] = local
    observed = []
    path = tmp_path / "owner"

    class Agent:
        tool_registry = registry
        mcp_client = None

        async def setup_mcp(self, *, mcp_setting):
            assert mcp_setting["mcpServers"]["deedpage"]["namespace_tools"] is True
            self.mcp_client = SimpleNamespace(credential_provider=None, config=mcp_setting)

            async def publish(**kwargs):
                headers = self.mcp_client.credential_provider("deedpage", {})
                observed.append(headers)
                response = {"url": "https://example.test"}
                if not headers:
                    response["token"] = "first-owner"
                return {"result": json.dumps(response)}

            registry.function_mappings.update({
                "deedpage__publish_site": publish,
                "deedpage__delete_site": object(),
            })

    async def scenario():
        agent = Agent()
        await example.setup_deed_page(agent, path)
        assert "headers" not in agent.mcp_client.config["mcpServers"]["deedpage"]
        assert agent.mcp_client.credential_provider("unrelated-server", {}) == {}
        for _ in range(2):
            result = await registry.function_mappings["deedpage__publish_site"]()
            assert "first-owner" not in result["result"]

    asyncio.run(scenario())
    assert observed == [{}, {"Authorization": "Bearer first-owner"}]
    assert registry.function_mappings["publish_site"] is local
    assert "deedpage__delete_site" not in registry.function_mappings


def test_saved_marker_is_only_added_after_success(example, tmp_path, monkeypatch):
    def fail(*args, **kwargs):
        raise OSError("save failed")

    payload = json.dumps({"token": "private-value", "url": "https://example.test"})
    assert "token_saved" not in example.split_token(payload)[0]
    monkeypatch.setattr(example, "save_token", fail)
    with pytest.raises(OSError) as error:
        example.protected_result(payload, tmp_path / "owner")
    assert "private-value" not in str(error.value)


@pytest.mark.parametrize("phase", ["setup", "refresh"])
def test_partial_discovery_failure_still_removes_dangerous_tools(example, tmp_path, phase):
    registry = ToolRegistry()

    async def partial_failure(*args, **kwargs):
        registry.function_mappings["deedpage__delete_site"] = object()
        raise RuntimeError("simulated discovery failure")

    agent = SimpleNamespace(
        tool_registry=registry, setup_mcp=partial_failure,
        mcp_client=None if phase == "setup" else SimpleNamespace(refresh_tools=partial_failure),
    )
    operation = example.setup_deed_page if phase == "setup" else example.refresh_deed_page
    with pytest.raises(RuntimeError, match="discovery failure"):
        asyncio.run(operation(agent, tmp_path / "owner"))
    assert "deedpage__delete_site" not in registry.function_mappings


def test_setup_does_not_replace_existing_mcp_credentials(example, tmp_path):
    provider = object()
    client = SimpleNamespace(credential_provider=provider)
    agent = SimpleNamespace(tool_registry=ToolRegistry(), mcp_client=client)
    with pytest.raises(ValueError, match="existing MCP client"):
        asyncio.run(example.setup_deed_page(agent, tmp_path / "owner"))
    assert client.credential_provider is provider
