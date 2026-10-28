import asyncio
from types import SimpleNamespace

import pytest

from LightAgent.mcp_client_manager import MCPClientManager
from LightAgent.tools import ToolRegistry


def mcp_tool(name="search_docs", *, snake_case=False):
    value = SimpleNamespace(
        name=name,
        description="Search documentation",
        inputSchema={
            "type": "object",
            "properties": {"query": {"type": "string", "title": "Query"}},
            "required": ["query"],
        },
    )
    if snake_case:
        value.input_schema = value.inputSchema
        del value.inputSchema
    return value


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


@pytest.mark.parametrize("snake_case", [False, True])
def test_tool_schema_registration_and_call_accept_sdk_field_names(snake_case):
    registry = ToolRegistry()
    manager = MCPClientManager({"mcpServers": {"remote": {"command": "unused", "args": []}}}, registry)
    session = FakeSession([mcp_tool(snake_case=snake_case)])

    async def create_session(server, config):
        manager.session = session
        manager.server_sessions[server] = session

    manager._create_session = create_session
    assert asyncio.run(manager.register_mcp_tool())
    schema = registry.openai_function_schemas[0]["function"]["parameters"]
    assert schema["required"] == ["query"]
    assert schema["properties"]["query"]["type"] == "string"
    assert asyncio.run(manager.call_tool("search_docs", {"query": "hello"}))["result"] == "ok"
    with pytest.raises(ValueError, match="query"):
        asyncio.run(manager.call_tool("search_docs", {}))


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


def test_streamable_http_works_on_mcp_2_without_streamablehttp_client(monkeypatch):
    # mcp 2.x removed streamablehttp_client; streamable_http_client takes an httpx client
    # (which carries the headers) and yields (read, write) instead of three streams.
    from LightAgent import mcp_client_manager as mcp_module

    captured = {}
    closed = []

    class AsyncContext:
        def __init__(self, value, label):
            self.value = value
            self.label = label

        async def __aenter__(self):
            return self.value

        async def __aexit__(self, exc_type, exc, traceback):
            closed.append(self.label)
            return False

    class InitializedSession:
        initialized = False

        async def initialize(self):
            self.initialized = True

    def http_client_factory(*, headers):
        captured["headers"] = headers
        return AsyncContext("http-client", "http")

    def streamable_client(*, url, http_client):
        captured.update(url=url, http_client=http_client)
        return AsyncContext(("reader", "writer"), "transport")

    initialized = InitializedSession()
    monkeypatch.setattr(mcp_module, "streamablehttp_client", None)
    monkeypatch.setattr(mcp_module, "streamable_http_client", streamable_client)
    monkeypatch.setattr(mcp_module, "create_mcp_http_client", http_client_factory)
    monkeypatch.setattr(
        mcp_module,
        "ClientSession",
        lambda *streams: captured.update(streams=streams) or AsyncContext(initialized, "session"),
    )

    async def credentials(server_name, config):
        assert server_name == "remote"
        return {"Authorization": "Bearer dynamic-token"}

    manager = MCPClientManager(
        {
            "mcpServers": {
                "remote": {
                    "transport": "streamable-http",
                    "url": "https://mcp.example.test",
                    "headers": {"X-Client": "LightAgent", "Authorization": "Bearer static-token"},
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
        "headers": {"X-Client": "LightAgent", "Authorization": "Bearer dynamic-token"},
        "url": "https://mcp.example.test",
        "http_client": "http-client",
        "streams": ("reader", "writer"),
    }
    assert closed == ["session", "transport", "http"]


def test_streamable_http_without_supported_transport_fails_clearly(monkeypatch):
    from LightAgent import mcp_client_manager as mcp_module

    monkeypatch.setattr(mcp_module, "streamablehttp_client", None)
    monkeypatch.setattr(mcp_module, "streamable_http_client", None)
    monkeypatch.setattr(mcp_module, "create_mcp_http_client", None)
    manager = MCPClientManager({"mcpServers": {}}, ToolRegistry())
    with pytest.raises(RuntimeError, match="does not support Streamable HTTP"):
        asyncio.run(manager._create_session("remote", {"transport": "http", "url": "https://example.test"}))


def test_modern_transport_closes_failed_attempt_before_reconnect(monkeypatch):
    from LightAgent import mcp_client_manager as mcp_module

    events = []
    attempts = []

    class Context:
        def __init__(self, value, label):
            self.value, self.label = value, label

        async def __aenter__(self):
            events.append(f"open:{self.label}")
            return self.value

        async def __aexit__(self, *args):
            events.append(f"close:{self.label}")

    class Session(FakeSession):
        async def initialize(self):
            if len(attempts) == 1:
                raise ConnectionError("temporary initialize failure")

    def http_factory(**kwargs):
        attempts.append(len(attempts) + 1)
        return Context(attempts[-1], f"http-{attempts[-1]}")

    def transport(*, url, http_client):
        return Context((http_client, "writer"), f"transport-{http_client}")

    def session(reader, writer):
        return Context(Session([mcp_tool()], result="found"), f"session-{reader}")

    monkeypatch.setattr(mcp_module, "streamablehttp_client", None)
    monkeypatch.setattr(mcp_module, "streamable_http_client", transport)
    monkeypatch.setattr(mcp_module, "create_mcp_http_client", http_factory)
    monkeypatch.setattr(mcp_module, "ClientSession", session)
    manager = MCPClientManager({"mcpServers": {"remote": {
        "transport": "http", "url": "https://example.test", "reconnect_attempts": 1,
    }}}, ToolRegistry())
    result = asyncio.run(manager.call_tool("search_docs", {"query": "hello"}, target_server="remote"))
    assert result["result"] == "found"
    assert attempts == [1, 2]
    assert events.index("close:http-1") < events.index("open:http-2")
    assert events[-3:] == ["close:session-2", "close:transport-2", "close:http-2"]
    for attempt in attempts:
        assert f"close:http-{attempt}" in events
    assert manager.server_sessions == {}


@pytest.mark.parametrize("transport", ["sse", "stdio"])
def test_other_transports_do_not_require_streamable_http_helpers(monkeypatch, transport):
    from LightAgent import mcp_client_manager as mcp_module

    class Context:
        def __init__(self, value):
            self.value = value

        async def __aenter__(self):
            return self.value

        async def __aexit__(self, *args):
            pass

    class Session:
        async def initialize(self):
            pass

    initialized = Session()
    monkeypatch.setattr(mcp_module, "streamablehttp_client", None)
    monkeypatch.setattr(mcp_module, "streamable_http_client", None)
    monkeypatch.setattr(mcp_module, "create_mcp_http_client", None)
    monkeypatch.setattr(mcp_module, "sse_client", lambda **kwargs: Context(("read", "write")))
    monkeypatch.setattr(mcp_module, "stdio_client", lambda params: Context(("read", "write")))
    monkeypatch.setattr(mcp_module, "ClientSession", lambda *streams: Context(initialized))
    config = {"url": "https://example.test"} if transport == "sse" else {"command": "unused", "args": []}
    manager = MCPClientManager({"mcpServers": {}}, ToolRegistry())

    async def scenario():
        await manager._create_session("remote", config)
        assert manager.server_sessions["remote"] is initialized
        await manager.cleanup()

    asyncio.run(scenario())
