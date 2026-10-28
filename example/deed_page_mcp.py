"""Publish LightAgent output as a static page through deed.page's remote MCP server.

deed.page (https://deed.page) is a static hosting service with a Streamable
HTTP MCP endpoint at https://deed.page/mcp. This example uses LightAgent's
existing ``transport: "streamable-http"`` support; it adds no dependency and
makes no network request at import time.

Two modes:

* ``--direct`` calls ``publish_site`` through ``MCPClientManager`` without a
  model, which is a quick way to check the connection.
* the default mode runs a LightAgent agent (any OpenAI-compatible model) that
  writes a page and publishes it with ``publish_site``.

Credentials:

* ``DEEDPAGE_TOKEN`` (optional) is sent as a Bearer header. Without it the first
  publish is anonymous and the service returns a new owner token once. The
  helpers below remove that token from the tool result before it reaches the
  model or the console, and write it to ``--token-file`` with mode 0600.
* ``LIGHTAGENT_MODEL``, ``OPENAI_API_KEY`` and ``OPENAI_BASE_URL`` configure the
  model for the agent mode.
"""

from __future__ import annotations

import argparse
import asyncio
import inspect
import json
import os
import stat
import tempfile
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

DEED_PAGE_MCP_URL = "https://deed.page/mcp"
SERVER_NAME = "deedpage"
TOKEN_ENV = "DEEDPAGE_TOKEN"
DEFAULT_TOKEN_FILE = str(
    Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    / "lightagent" / "credentials" / "deedpage.token"
)
TOOL_PREFIX = f"{SERVER_NAME}__"
# publish_site and get_site are enough for "write a page, return the link".
# The server also exposes delete_site, rotate_token, add_domain and others;
# keep those away from the model unless the application needs them.
DEFAULT_ALLOWED_TOOLS = (f"{TOOL_PREFIX}publish_site", f"{TOOL_PREFIX}get_site")

SAMPLE_PAGE = """<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>LightAgent + deed.page</title></head>
<body>
<h1>Published from LightAgent</h1>
<p>This page was published through the deed.page MCP server.</p>
</body>
</html>
"""


def deed_page_mcp_config(
        env: Mapping[str, str] | None = None,
        *, token_file: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    """Return an ``mcp_setting`` dict for ``LightAgent.setup_mcp``.

    The token is read by Python from the environment; LightAgent does not
    interpolate header strings.
    """
    env = os.environ if env is None else env
    server: dict[str, Any] = {
        "transport": "streamable-http", "url": DEED_PAGE_MCP_URL,
        "namespace": SERVER_NAME, "namespace_tools": True,
    }
    token = (env.get(TOKEN_ENV) or "").strip()
    if not token and token_file is not None:
        token = read_token(token_file)
    if token:
        server["headers"] = {"Authorization": f"Bearer {token}"}
    return {"mcpServers": {SERVER_NAME: server}}


def split_token(result_text: str) -> tuple[str, str | None]:
    """Remove the one-time owner ``token`` from a publish result.

    Returns the cleaned result text and the token (or ``None``). Non-JSON text
    is returned unchanged.
    """
    try:
        payload = json.loads(result_text)
    except (TypeError, ValueError):
        return result_text, None
    if not isinstance(payload, dict) or "token" not in payload:
        return result_text, None
    token = payload.pop("token")
    return json.dumps(payload), str(token) if token else None


def save_token(token: str, token_file: str | os.PathLike[str]) -> Path:
    """Atomically publish a private token file without replacing another token."""
    path = Path(token_file)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.parent.is_symlink() or stat.S_IMODE(path.parent.stat().st_mode) & 0o022:
        raise PermissionError("Token directory must not be a symlink or writable by other users")
    existing = read_token(path)
    if existing is not None:
        if existing != token:
            raise FileExistsError("Refusing to replace an existing owner token")
        return path
    fd, temporary = tempfile.mkstemp(prefix=".deedpage-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            os.fchmod(handle.fileno(), 0o600)
            handle.write(token)
            handle.flush()
            os.fsync(handle.fileno())
        # A hard link publishes a complete file atomically and refuses an
        # existing destination, including a symlink created during this write.
        try:
            os.link(temporary, path, follow_symlinks=False)
        except FileExistsError:
            if read_token(path) != token:
                raise FileExistsError("Refusing to replace an existing owner token") from None
    finally:
        os.unlink(temporary)
    return path


def read_token(token_file: str | os.PathLike[str]) -> str | None:
    """Read only an owner-only regular file, without following symlinks."""
    if not hasattr(os, "O_NOFOLLOW"):
        raise RuntimeError("Secure token files require O_NOFOLLOW; use DEEDPAGE_TOKEN on this platform")
    try:
        fd = os.open(token_file, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except FileNotFoundError:
        return None
    with os.fdopen(fd, "r", encoding="utf-8") as handle:
        info = os.fstat(handle.fileno())
        if not stat.S_ISREG(info.st_mode):
            raise ValueError("Token file must be a regular file")
        if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
            raise PermissionError("Token file must be owned by the current user with mode 0600")
        token = handle.read().strip()
    if not token:
        raise ValueError("Token file is empty")
    return token


def credential_headers(token_file: str | os.PathLike[str]) -> dict[str, str]:
    token = (os.environ.get(TOKEN_ENV) or "").strip() or read_token(token_file)
    return {"Authorization": f"Bearer {token}"} if token else {}


def protected_result(result_text: str, token_file: str | os.PathLike[str]) -> str:
    cleaned, token = split_token(result_text)
    if token:
        save_token(token, token_file)
        payload = json.loads(cleaned)
        payload["token_saved"] = True
        return json.dumps(payload)
    return cleaned


def restrict_new_tools(tool_registry: Any, before: Iterable[str], allowed: Iterable[str]) -> list[str]:
    """Drop tools registered since ``before`` unless they are in ``allowed``.

    Only the reserved deedpage namespace is affected. The before snapshot must
    not contain that namespace; setup checks this before connecting.
    """
    if any(name.startswith(TOOL_PREFIX) for name in before):
        raise ValueError("The deedpage namespace is already in use")
    allowed_set = set(allowed)
    removed = [
        name for name in list(tool_registry.function_mappings)
        if name.startswith(TOOL_PREFIX) and name not in allowed_set
    ]
    for name in removed:
        tool_registry.function_mappings.pop(name, None)
        tool_registry.function_info.pop(name, None)
    tool_registry.openai_function_schemas = [
        schema for schema in tool_registry.openai_function_schemas
        if schema.get("function", {}).get("name") not in removed
    ]
    return removed


def protect_publish_token(tool_registry: Any, token_file: str | os.PathLike[str]) -> bool:
    """Wrap the registered ``publish_site`` so a returned owner token is saved, not shown."""
    tool_name = f"{TOOL_PREFIX}publish_site"
    original = tool_registry.function_mappings.get(tool_name)
    if original is None:
        return False

    async def publish_site(**kwargs: Any) -> Any:
        result = original(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        if isinstance(result, dict) and isinstance(result.get("result"), str):
            result = {**result, "result": protected_result(result["result"], token_file)}
        return result

    tool_registry.function_mappings[tool_name] = publish_site
    return True


async def setup_deed_page(agent: Any, token_file: str | os.PathLike[str]) -> None:
    """Reserve the MCP namespace and install credentials and result protection."""
    if any(name.startswith(TOOL_PREFIX) for name in agent.tool_registry.function_mappings):
        raise ValueError("The deedpage namespace is already in use")
    if getattr(agent, "mcp_client", None) is not None:
        raise ValueError("Use a separate agent instead of replacing an existing MCP client")
    config = deed_page_mcp_config(token_file=token_file)
    try:
        await agent.setup_mcp(mcp_setting=config)
    finally:
        # Bootstrap credentials are needed during discovery; later calls must
        # use the live resolver so deleted/revoked credentials cannot linger.
        config["mcpServers"][SERVER_NAME].pop("headers", None)
        restrict_new_tools(agent.tool_registry, (), DEFAULT_ALLOWED_TOOLS)
        protected = protect_publish_token(agent.tool_registry, token_file)
    if agent.mcp_client is None:
        raise RuntimeError("MCP setup failed")
    agent.mcp_client.credential_provider = (
        lambda server, config: credential_headers(token_file) if server == SERVER_NAME else {}
    )
    if not protected:
        raise RuntimeError("The deedpage publishing tool is unavailable")


async def refresh_deed_page(agent: Any, token_file: str | os.PathLike[str]) -> None:
    try:
        await agent.mcp_client.refresh_tools(SERVER_NAME)
    finally:
        restrict_new_tools(agent.tool_registry, (), DEFAULT_ALLOWED_TOOLS)
        protected = protect_publish_token(agent.tool_registry, token_file)
    if not protected:
        raise RuntimeError("The deedpage publishing tool is unavailable")


async def publish_direct(html: str, ttl_seconds: int | None, token_file: str) -> dict[str, Any]:
    """Publish ``html`` as index.html without a model and return the cleaned result."""
    from LightAgent.mcp_client_manager import MCPClientManager
    from LightAgent.tools import ToolRegistry

    manager = MCPClientManager(
        deed_page_mcp_config(env={}), ToolRegistry(),
        credential_provider=lambda server, config: credential_headers(token_file) if server == SERVER_NAME else {},
    )
    arguments: dict[str, Any] = {"files": {"index.html": html}}
    if ttl_seconds:
        arguments["ttl_seconds"] = ttl_seconds
    try:
        response = await manager.call_tool("publish_site", arguments, target_server=SERVER_NAME)
    finally:
        await manager.cleanup()
    cleaned = protected_result(response["result"], token_file)
    return json.loads(cleaned)


def run_agent(task: str, token_file: str) -> str:
    """Run a LightAgent agent that can publish with ``publish_site``."""
    from LightAgent import LightAgent

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Set OPENAI_API_KEY (and OPENAI_BASE_URL / LIGHTAGENT_MODEL) for the agent mode.")
    agent = LightAgent(
        model=os.environ.get("LIGHTAGENT_MODEL", "gpt-4o-mini"),
        api_key=api_key,
        base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        role="You write small, self-contained HTML pages and publish them when asked.",
    )
    asyncio.run(setup_deed_page(agent, token_file))
    return agent.run(task, stream=False)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--direct", action="store_true", help="publish a sample page without a model")
    parser.add_argument("--ttl", type=int, default=3600, help="expire the page after N seconds (0 = permanent)")
    parser.add_argument("--token-file", default=DEFAULT_TOKEN_FILE)
    parser.add_argument(
        "--task",
        default=(
            "Write a one-page HTML summary of what LightAgent is, then publish it with deedpage__publish_site "
            "using files {\"index.html\": <the html>} and ttl_seconds 3600. Reply with the URL."
        ),
    )
    args = parser.parse_args()
    if args.direct:
        result = asyncio.run(publish_direct(SAMPLE_PAGE, args.ttl or None, args.token_file))
        print(json.dumps({key: result.get(key) for key in ("url", "slug", "version", "expires_at")}, indent=2))
    else:
        print(run_agent(args.task, args.token_file))


if __name__ == "__main__":
    main()
