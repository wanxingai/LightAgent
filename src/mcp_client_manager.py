#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
作者: [weego/WXAI-Team]
最后更新: 2026-02-20
"""

from functools import partial
from typing import Optional, Dict, Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack

from .tools import ToolRegistry  # 关键修改：从当前包导入


class MCPClientManager:
    """增强版MCP客户端管理器"""

    def __init__(self, config: dict, tool_registry: ToolRegistry):
        self.config = config
        self.tool_registry = tool_registry
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.server_sessions = {}

    async def _create_session(self, server_name: str, config: dict):
        """创建并管理会话上下文"""
        if 'url' in config:
            # SSE 服务器连接
            streams_context = sse_client(
                url=config['url'],
                headers=config.get('headers', {})
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

    async def register_mcp_tool(self) -> bool:
        """自动注册所有MCP服务的工具"""
        registered_count = 0
        enabled_servers = [
            (name, config)
            for name, config in self.config["mcpServers"].items()
            if not config["disabled"]
        ]

        for server_name, config in enabled_servers:
            try:
                await self._create_session(server_name, config)
                tools_response = await self.session.list_tools()
                print(f"🔍 Registering MCP tools for server : {server_name} ...")

                for tool in tools_response.tools:
                    try:
                        # 构建工具元数据
                        tool_info = {
                            "tool_name": tool.name,
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
                        self.tool_registry.function_info[tool.name] = tool_info
                        self.tool_registry.function_mappings[tool.name] = partial(
                            self._call_tool_wrapper,
                            tool_name=tool.name,
                            target_server=server_name
                        )

                        # 构建OpenAI格式
                        openai_schema = {
                            "type": "function",
                            "function": {
                                "name": tool.name,
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
                        registered_count += 1
                        print(f"✅ The registered MCP tool : {tool.name}")
                    except Exception as e:
                        continue
            except Exception as e:
                continue

        await self.cleanup()
        return registered_count > 0

    async def _call_tool_wrapper(self, tool_name: str, target_server: str, **kwargs):
        """参数转换适配器"""
        return await self.call_tool(
            tool_name=tool_name,
            arguments=kwargs,
            target_server=target_server
        )

    async def call_tool(self, tool_name: str, arguments: dict, target_server: str = None):
        """通用工具调用方法"""
        enabled_servers = [
            (name, config)
            for name, config in self.config["mcpServers"].items()
            if not config["disabled"]
        ]

        if target_server:
            enabled_servers = [s for s in enabled_servers if s[0] == target_server]

        for server_name, config in enabled_servers:
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
                continue

        raise ValueError(f"工具 {tool_name} 在可用服务器中未找到")

    def _validate_arguments(self, arguments: dict, schema: dict):
        """简单参数校验"""
        required_fields = schema.get("required", [])
        for field in required_fields:
            if field not in arguments:
                raise ValueError(f"缺少必要参数: {field}")
