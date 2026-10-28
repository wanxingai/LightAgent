"""Manual real-SDK probe against the local Postman MCP contract simulation."""

import argparse
import asyncio
from importlib.metadata import version
from urllib.parse import urlparse

from LightAgent.mcp_client_manager import MCPClientManager
from LightAgent.tools import ToolRegistry


async def probe(url):
    if urlparse(url).hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("The compatibility probe only permits a local simulation")

    async def credentials(server, config):
        return {"X-LightAgent-Test": "credential-header"}

    manager = MCPClientManager({"mcpServers": {"contract": {
        "transport": "streamable-http",
        "url": url,
        "headers": {"X-LightAgent-Test": "static-header"},
    }}}, ToolRegistry(), credential_provider=credentials)
    try:
        response = await asyncio.wait_for(
            manager.call_tool("echo_header", {}, target_server="contract"), timeout=15,
        )
        assert response["result"] == "credential-header", response
        assert manager.server_sessions == {}
        print(f"mcp {version('mcp')}: initialize/list/call, credential header, and cleanup passed")
    finally:
        await manager.cleanup()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    asyncio.run(probe(parser.parse_args().url))
