import asyncio

import pytest

from LightAgent.mcp_client_manager import MCPClientManager
from LightAgent.tools import ToolRegistry


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
