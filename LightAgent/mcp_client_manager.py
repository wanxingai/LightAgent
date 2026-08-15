#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
作者: [weego/WXAI-Team]
最后更新: 2026-02-20
"""

import re
import inspect
from functools import partial
from typing import Optional, Dict, Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
try:
    from mcp.client.streamable_http import streamablehttp_client
except ImportError:  # Older MCP SDKs retain stdio/SSE compatibility.
    streamablehttp_client = None
from contextlib import AsyncExitStack

from .tools import ToolRegistry  # 关键修改：从当前包导入


class MCPClientManager:
    """增强版MCP客户端管理器"""

    def __init__(self, config: dict, tool_registry: ToolRegistry, credential_provider: Any = None):
        self.config = config
        self.tool_registry = tool_registry
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.server_sessions = {}
        self.last_mcp_errors = []
        self.credential_provider = credential_provider
        self._registered_tools: Dict[str, set[str]] = {}
        self._tool_owners: Dict[str, str] = {}

    async def _create_session(self, server_name: str, config: dict):
        """创建并管理会话上下文"""
        headers = dict(config.get('headers', {}))
        if self.credential_provider is not None:
            resolver = getattr(self.credential_provider, "headers", self.credential_provider)
            supplied = resolver(server_name, dict(config))
            if inspect.isawaitable(supplied):
                supplied = await supplied
            headers.update(dict(supplied or {}))
        transport_name = str(config.get("transport", "")).lower()
        if transport_name in {"streamable-http", "streamable_http", "http"}:
            if streamablehttp_client is None:
                raise RuntimeError("installed MCP SDK does not support Streamable HTTP")
            streams_context = streamablehttp_client(url=config['url'], headers=headers)
            streams = await self.exit_stack.enter_async_context(streams_context)
            session_context = ClientSession(*streams[:2])
            self.session = await self.exit_stack.enter_async_context(session_context)
        elif 'url' in config:
            # SSE 服务器连接
            streams_context = sse_client(
                url=config['url'],
                headers=headers
            )
            streams = await self.exit_stack.enter_async_context(streams_context)
            session_context = ClientSession(*streams)
            self.session = await self.exit_stack.enter_async_context(session_context)
        else:
            # 标准输入输出服务器连接
            server_params = StdioServerParameters(
                command=config["command"],
                args=config["args"],
                env=config.get("env")
            )
            transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            stdio, write = transport
            session_context = ClientSession(stdio, write)
            self.session = await self.exit_stack.enter_async_context(session_context)

        await self.session.initialize()
        self.server_sessions[server_name] = self.session

    async def cleanup(self):
        """清理所有会话资源"""
        await self.exit_stack.aclose()
        self.server_sessions.clear()
        self.session = None
        self.exit_stack = AsyncExitStack()

    async def register_mcp_tool(self) -> bool:
        """自动注册所有MCP服务的工具"""
        self.last_mcp_errors.clear()
        registered_count = 0
        enabled_servers = [
            (name, config)
            for name, config in self.config["mcpServers"].items()
            if not config.get("disabled", False)
        ]

        for server_name, config in enabled_servers:
            try:
                await self._create_session(server_name, config)
                tools_response = await self.session.list_tools()
                print(f"🔍 Registering MCP tools for server : {server_name} ...")

                for tool in tools_response.tools:
                    try:
                        public_name = self._public_tool_name(server_name, config, tool.name)
                        # 构建工具元数据
                        tool_info = {
                            "tool_name": public_name,
                            "tool_description": tool.description,
                            "tool_params": []
                        }

                        # 解析参数模式
                        properties = tool.inputSchema.get("properties", {})
                        required_fields = tool.inputSchema.get("required", [])

                        for param_name, param_schema in properties.items():
                            tool_info["tool_params"].append({
                                "name": param_name,
                                "type": param_schema.get("type", "string"),
                                "description": param_schema.get("title", ""),
                                "required": param_name in required_fields
                            })

                        # 注册到工具注册表
                        self.tool_registry.function_info[public_name] = tool_info
                        self.tool_registry.function_mappings[public_name] = partial(
                            self._call_tool_wrapper,
                            tool_name=tool.name,
                            target_server=server_name
                        )

                        # 构建OpenAI格式
                        openai_schema = {
                            "type": "function",
                            "function": {
                                "name": public_name,
                                "description": tool.description,
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        k: {"type": v["type"], "description": v.get("title", "")}
                                        for k, v in properties.items()
                                    },
                                    "required": required_fields
                                }
                            }
                        }
                        self.tool_registry.openai_function_schemas.append(openai_schema)
                        self._registered_tools.setdefault(server_name, set()).add(public_name)
                        self._tool_owners[public_name] = server_name
                        registered_count += 1
                        print(f"✅ The registered MCP tool : {tool.name}")
                    except Exception as e:
                        self._record_error(server_name, f"register_tool:{getattr(tool, 'name', 'unknown')}", e)
                        continue
            except Exception as e:
                self._record_error(server_name, "register_server", e)
                continue

        await self.cleanup()
        return registered_count > 0

    async def refresh_tools(self, server_name: str | None = None) -> bool:
        """Refresh MCP tool lists without leaving duplicate registrations."""
        targets = [server_name] if server_name else list(self._registered_tools)
        for target in targets:
            for name in self._registered_tools.pop(target, set()):
                self.tool_registry.function_info.pop(name, None)
                self.tool_registry.function_mappings.pop(name, None)
                self._tool_owners.pop(name, None)
                self.tool_registry.openai_function_schemas = [
                    schema for schema in self.tool_registry.openai_function_schemas
                    if schema.get("function", {}).get("name") != name
                ]
        if server_name is None:
            return await self.register_mcp_tool()
        original = self.config["mcpServers"]
        self.config["mcpServers"] = {
            name: {**config, "disabled": name != server_name}
            for name, config in original.items()
        }
        try:
            return await self.register_mcp_tool()
        finally:
            self.config["mcpServers"] = original

    def _public_tool_name(self, server_name: str, config: dict, tool_name: str) -> str:
        namespace = re.sub(r"[^A-Za-z0-9_-]", "_", str(config.get("namespace") or server_name))
        namespaced = f"{namespace}__{tool_name}"
        if config.get("namespace_tools") or (
                tool_name in self.tool_registry.function_mappings
                and self._tool_owners.get(tool_name) != server_name
        ):
            return namespaced
        return tool_name

    async def _call_tool_wrapper(self, tool_name: str, target_server: str, **kwargs):
        """参数转换适配器"""
        return await self.call_tool(
            tool_name=tool_name,
            arguments=kwargs,
            target_server=target_server
        )

    async def call_tool(self, tool_name: str, arguments: dict, target_server: str = None):
        """通用工具调用方法"""
        self.last_mcp_errors.clear()
        enabled_servers = [
            (name, config)
            for name, config in self.config["mcpServers"].items()
            if not config.get("disabled", False)
        ]

        if target_server:
            enabled_servers = [s for s in enabled_servers if s[0] == target_server]

        for server_name, config in enabled_servers:
            max_attempts = max(1, int(config.get("reconnect_attempts", 0)) + 1)
            for attempt in range(max_attempts):
                try:
                    session = self.server_sessions.get(server_name)
                    if not session:
                        await self._create_session(server_name, config)
                        session = self.session

                    tools = await session.list_tools()
                    available_tools = {t.name: t for t in tools.tools}

                    if tool_name in available_tools:
                        # 验证参数类型
                        schema = available_tools[tool_name].inputSchema
                        self._validate_arguments(arguments, schema)

                        # 执行调用
                        result = await session.call_tool(tool_name, arguments)
                        await self.cleanup()
                        return {
                            "server": server_name,
                            "tool": tool_name,
                            "result": result.content[0].text
                        }
                except Exception as e:
                    self._record_error(server_name, f"call_tool:{tool_name}", e)
                    await self.cleanup()
                    if attempt + 1 >= max_attempts:
                        break

        raise ValueError(self._format_tool_not_found(tool_name))

    def _validate_arguments(self, arguments: dict, schema: dict):
        """简单参数校验"""
        required_fields = schema.get("required", [])
        for field in required_fields:
            if field not in arguments:
                raise ValueError(f"缺少必要参数: {field}")

    def _record_error(self, server_name: str, phase: str, error: Exception):
        """记录MCP失败原因，避免把真实连接/执行失败伪装成工具不存在。"""
        self.last_mcp_errors.append({
            "server": server_name,
            "phase": phase,
            "error_type": type(error).__name__,
            "message": self._sanitize_error_message(str(error)),
        })

    def _format_tool_not_found(self, tool_name: str) -> str:
        if not self.last_mcp_errors:
            return f"工具 {tool_name} 在可用服务器中未找到"

        details = "; ".join(
            f"{item['server']}::{item['phase']} -> {item['error_type']}: {item['message']}"
            for item in self.last_mcp_errors[:3]
        )
        if len(self.last_mcp_errors) > 3:
            details += f"; ... {len(self.last_mcp_errors) - 3} more"
        return f"工具 {tool_name} 在可用服务器中未找到。MCP诊断: {details}"

    @staticmethod
    def _sanitize_error_message(message: str) -> str:
        message = re.sub(r"(Bearer\s+)[A-Za-z0-9._~+/=-]+", r"\1[redacted]", message)
        message = re.sub(r"(sk-[A-Za-z0-9_-]{8,})", "[redacted]", message)
        return message
