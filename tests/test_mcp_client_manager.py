import asyncio
from types import SimpleNamespace

import pytest

from LightAgent.mcp_client_manager import MCPClientManager
from LightAgent.tools import ToolRegistry


def mcp_tool(name="search_docs"):
    return SimpleNamespace(
        name=name,
        description="Search documentation",
        inputSchema={
            "type": "object",
            "properties": {"query": {"type": "string", "title": "Query"}},
            "required": ["query"],
        },
    )


class FakeSession:
    def __init__(self, tools=None, *, list_error=None, result="ok"):
        self.tools = tools or []
        self.list_error = list_error
        self.result = result

    async def list_tools(self):
        if self.list_error:
            raise self.list_error
        return SimpleNamespace(tools=self.tools)

    async def call_tool(self, name, arguments):
        return SimpleNamespace(content=[SimpleNamespace(text=self.result)])


def test_mcp_call_preserves_sanitized_failure_receipt():
    manager = MCPClientManager(
        {
            "mcpServers": {
                "broken": {
                    "disabled": False,
                    "command": "missing-command",
                    "args": [],
                }
            }
        },
        ToolRegistry(),
    )

    async def fail_create_session(server_name, config):
        raise RuntimeError("connection failed with Bearer secret-token and sk-1234567890abcdef")

    manager._create_session = fail_create_session

    with pytest.raises(ValueError) as exc_info:
        asyncio.run(manager.call_tool("search_docs", {}, target_server="broken"))

    message = str(exc_info.value)
    assert "MCP诊断" in message
    assert "broken::call_tool:search_docs -> RuntimeError" in message
    assert "secret-token" not in message
    assert "sk-1234567890abcdef" not in message
    assert manager.last_mcp_errors == [
        {
            "server": "broken",
            "phase": "call_tool:search_docs",
            "error_type": "RuntimeError",
            "message": "connection failed with Bearer [redacted] and [redacted]",
        }
    ]


def test_mcp_call_reconnects_and_succeeds_after_transient_failure():
    manager = MCPClientManager(
        {"mcpServers": {"docs": {"command": "unused", "args": [], "reconnect_attempts": 1}}},
        ToolRegistry(),
    )
    sessions = iter([
        FakeSession(list_error=ConnectionError("temporary disconnect")),
        FakeSession([mcp_tool()], result="found"),
    ])
    attempts = []

    async def create_session(server_name, config):
        attempts.append(server_name)
        manager.session = next(sessions)
        manager.server_sessions[server_name] = manager.session

    manager._create_session = create_session

    result = asyncio.run(manager.call_tool("search_docs", {"query": "runtime"}, target_server="docs"))

    assert result == {"server": "docs", "tool": "search_docs", "result": "found"}
    assert attempts == ["docs", "docs"]
    assert manager.last_mcp_errors[0]["error_type"] == "ConnectionError"
    assert manager.server_sessions == {}


def test_mcp_refresh_replaces_namespaced_tools_without_duplicates():
    config = {
        "mcpServers": {
            "docs one": {
                "command": "unused",
                "args": [],
                "namespace": "docs-one",
                "namespace_tools": True,
            },
            "docs-two": {
                "command": "unused",
                "args": [],
                "namespace_tools": True,
            },
        }
    }
    registry = ToolRegistry()
    manager = MCPClientManager(config, registry)
    sessions = {
        "docs one": FakeSession([mcp_tool()]),
        "docs-two": FakeSession([mcp_tool()]),
    }

    async def create_session(server_name, server_config):
        manager.session = sessions[server_name]
        manager.server_sessions[server_name] = manager.session

    manager._create_session = create_session

    assert asyncio.run(manager.register_mcp_tool()) is True
    assert set(registry.function_mappings) == {"docs-one__search_docs", "docs-two__search_docs"}

    sessions["docs one"] = FakeSession([mcp_tool(), mcp_tool("read_page")])
    assert asyncio.run(manager.refresh_tools("docs one")) is True

    names = [schema["function"]["name"] for schema in registry.openai_function_schemas]
    assert set(names) == {"docs-one__search_docs", "docs-one__read_page", "docs-two__search_docs"}
    assert len(names) == len(set(names))
    assert set(config["mcpServers"]) == {"docs one", "docs-two"}


def test_streamable_http_uses_async_credential_provider(monkeypatch):
    from LightAgent import mcp_client_manager as mcp_module

    captured = {}

    class AsyncContext:
        def __init__(self, value):
            self.value = value

        async def __aenter__(self):
            return self.value

        async def __aexit__(self, exc_type, exc, traceback):
            return False

    class InitializedSession:
        initialized = False

        async def initialize(self):
            self.initialized = True

    def streamable_client(*, url, headers):
        captured.update(url=url, headers=headers)
        return AsyncContext(("reader", "writer", "session-id"))

    initialized = InitializedSession()
    monkeypatch.setattr(mcp_module, "streamablehttp_client", streamable_client)
    monkeypatch.setattr(mcp_module, "ClientSession", lambda *streams: AsyncContext(initialized))

    async def credentials(server_name, config):
        assert server_name == "remote"
        return {"Authorization": "Bearer dynamic-token"}

    manager = MCPClientManager(
        {
            "mcpServers": {
                "remote": {
                    "transport": "streamable-http",
                    "url": "https://mcp.example.test",
                    "headers": {"X-Client": "LightAgent"},
                }
            }
        },
        ToolRegistry(),
        credential_provider=credentials,
    )

    async def scenario():
        await manager._create_session("remote", manager.config["mcpServers"]["remote"])
        assert manager.server_sessions["remote"] is initialized
        await manager.cleanup()

    asyncio.run(scenario())

    assert initialized.initialized
    assert captured == {
        "url": "https://mcp.example.test",
        "headers": {"X-Client": "LightAgent", "Authorization": "Bearer dynamic-token"},
    }
