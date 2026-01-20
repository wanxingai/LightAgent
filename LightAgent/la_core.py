#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
作者: [weego/WXAI-Team]
版本: 0.4.8
最后更新: 2025-12-14
"""

import asyncio
import importlib
import importlib.util
import inspect
import json
import logging
import os
import random
import re
import traceback
from contextlib import AsyncExitStack
from copy import deepcopy
from datetime import datetime
from functools import partial
from typing import List, Dict, Any, Callable, Union, Optional, Generator, AsyncGenerator, Protocol
from uuid import uuid4

import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from openai.types.chat import ChatCompletionChunk

__version__ = "0.4.8"  # 你可以根据需要设置版本号


# openai.langfuse_auth_check()

# 1. 定义内存接口协议
class MemoryProtocol(Protocol):
    def store(self, data: str, user_id: str) -> Any:
        ...

    def retrieve(self, query: str, user_id: str) -> List[Any]:
        ...


class ToolRegistry:
    """集中管理工具注册表，避免全局变量"""

    def __init__(self):
        self.function_mappings = {}  # 工具名称 -> 工具函数
        self.function_info = {}  # 工具名称 -> 工具info信息
        self.openai_function_schemas = []  # OpenAI 格式的工具描述

    def register_tool(self, func: Callable) -> bool:
        """注册单个工具"""
        if not hasattr(func, "tool_info"):
            return False

        tool_info = func.tool_info
        tool_name = tool_info["tool_name"]

        # 注册到字典
        self.function_info[tool_name] = tool_info
        self.function_mappings[tool_name] = func

        # 构建 OpenAI 格式的工具描述
        tool_params_openai = {}
        tool_required = []
        for param in tool_info["tool_params"]:
            tool_params_openai[param["name"]] = {
                "type": param["type"],
                "description": param["description"],
            }
            if param["required"]:
                tool_required.append(param["name"])

        tool_def_openai = {
            "type": "function",
            "function": {
                "name": tool_name,
                "description": tool_info["tool_description"],
                "parameters": {
                    "type": "object",
                    "properties": tool_params_openai,
                    "required": tool_required,
                },
            }
        }

        self.openai_function_schemas.append(tool_def_openai)
        return True

    def register_tools(self, tools: List[Callable]) -> bool:
        """批量注册工具"""
        success = True
        for func in tools:
            if not self.register_tool(func):
                success = False
        return success

    def get_tools(self) -> List[Dict[str, Any]]:
        """获取所有工具的描述（OpenAI 格式）"""
        return deepcopy(self.openai_function_schemas)

    def get_tools_str(self) -> str:
        """将工具描述转换为格式化的 JSON 字符串"""
        return json.dumps(self.openai_function_schemas, indent=4, ensure_ascii=False)

    def filter_tools(self, tool_reflection_result: str) -> List[Dict]:
        """根据内容过滤工具"""
        try:
            # 安全解析可能包含 Markdown 代码块的 JSON
            refined_content = tool_reflection_result.strip()
            if refined_content.startswith('```json') and refined_content.endswith('```'):
                refined_content = refined_content[7:-3].strip()

            parsed_data = json.loads(refined_content)
            valid_tools = {tool["name"].strip().lower() for tool in parsed_data.get("tools", [])}

            return [
                schema for schema in self.openai_function_schemas
                if isinstance(schema, dict) and
                   schema.get("function", {}).get("name", "").strip().lower() in valid_tools
            ]
        except (json.JSONDecodeError, KeyError, AttributeError) as e:
            raise ValueError(f"工具过滤失败: {str(e)}") from e


class ToolLoader:
    """工具加载器，支持动态加载和缓存"""

    def __init__(self, tools_directory: str = "tools"):
        self.tools_directory = tools_directory
        self.loaded_tools = {}

    def load_tool(self, tool_name: str) -> Callable:
        """加载单个工具"""
        if tool_name in self.loaded_tools:
            return self.loaded_tools[tool_name]

        tool_path = os.path.join(self.tools_directory, f"{tool_name}.py")
        if not os.path.exists(tool_path):
            raise FileNotFoundError(f"Tool '{tool_name}' not found in {tool_path}")

        # 动态加载模块
        spec = importlib.util.spec_from_file_location(tool_name, tool_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # 获取工具函数
        if hasattr(module, tool_name):
            tool_func = getattr(module, tool_name)
            if callable(tool_func) and hasattr(tool_func, "tool_info"):
                self.loaded_tools[tool_name] = tool_func
                return tool_func

        raise AttributeError(f"Tool '{tool_name}' is not properly defined in {tool_path}")

    def load_tools(self, tool_names: List[str]) -> Dict[str, Callable]:
        """批量加载工具"""
        for tool_name in tool_names:
            if tool_name not in self.loaded_tools:
                self.load_tool(tool_name)
        return self.loaded_tools


class AsyncToolDispatcher:
    """异步工具调度器"""

    async def dispatch(self, tool_name: str, tool_params: Dict[str, Any]) -> Union[
        str, Generator[str, None, None], AsyncGenerator[str, None]]:
        """调用工具执行，支持同步/异步工具及流式输出"""
        if tool_name not in self.function_mappings:
            return f"Tool `{tool_name}` not found."

        tool_call = self.function_mappings[tool_name]
        try:
            # 处理不同类型的工具
            if inspect.iscoroutinefunction(tool_call):
                result = await tool_call(**tool_params)
            elif inspect.isasyncgenfunction(tool_call):
                result = tool_call(**tool_params)
            else:
                result = tool_call(**tool_params)

            # 处理流式输出
            if inspect.isasyncgen(result):
                return self.async_stream_generator(result)
            elif inspect.isgenerator(result):
                return self.stream_generator(result)
            return str(result)
        except Exception as e:
            return f"Tool call error: {str(e)}\n{traceback.format_exc()}"

    async def async_stream_generator(self, async_gen: AsyncGenerator) -> AsyncGenerator[str, None]:
        async for chunk in async_gen:
            yield chunk

    def stream_generator(self, sync_gen: Generator) -> Generator[str, None, None]:
        for chunk in sync_gen:
            yield chunk


class LoggerManager:
    """集中管理日志系统"""

    def __init__(self, name: str, debug: bool, log_level: str, log_file: Optional[str] = None):
        self.name = name
        self.debug = debug
        self.logger = self._setup_logger(log_level, log_file)
        self.traceid = ""

    def _setup_logger(self, log_level: str, log_file: Optional[str] = None) -> logging.Logger:
        logger = logging.getLogger(self.name)
        logger.setLevel(log_level.upper())
        logger.propagate = False

        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

        if self.debug:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        if log_file:
            # 确保 log 目录存在
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)

            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        return logger

    def log(self, level: str, action: str, data: Any):
        """记录日志"""
        if not self.debug:
            return

        trace_info = f"[TraceID: {self.traceid}] " if self.traceid else ""
        log_message = f"{trace_info}{action}: {data}"
        safe_msg = log_message.encode('utf-8', 'ignore').decode('utf-8')

        if level == "DEBUG":
            self.logger.debug(safe_msg)
        elif level == "INFO":
            self.logger.info(safe_msg)
        elif level == "ERROR":
            self.logger.error(safe_msg)

    def set_traceid(self, traceid: str):
        """设置当前跟踪ID"""
        self.traceid = traceid


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


class LightAgent:
    __version__ = "0.4.8"  # 将版本号放在类中

    def __init__(
            self,
            *,
            name: Optional[str] = None,  # 代理名称
            instructions: Optional[str] = None,  # 代理指令
            role: Optional[str] = None,  # 代理角色
            model: str,  # agent模型名称
            api_key: str | None = None,  # 模型 api key
            base_url: str | httpx.URL | None = None,  # 模型 base url
            websocket_base_url: str | httpx.URL | None = None,  # 模型 websocket base url
            memory: Optional[MemoryProtocol] = None,  # 支持外部传入记忆模块
            tree_of_thought: bool = False,  # 是否启用链式思考
            tot_model: str | None = None,  # 链式思考模型
            tot_api_key: str | None = None,  # 链式思考模型API密钥
            tot_base_url: str | httpx.URL | None = None,  # 链式思考模型base_url
            filter_tools: bool = True,  # 是否启用工具过滤
            self_learning: bool = False,  # 是否启用agent自我学习
            tools: List[Union[str, Callable]] = None,  # 支持工具混合输入
            debug: bool = False,  # 是否启用调试模式
            log_level: str = "INFO",  # 日志级别（INFO, DEBUG, ERROR）
            log_file: Optional[str] = None,  # 日志文件路径
            tracetools: Optional[dict] = None,  # log跟踪工具
    ) -> None:
        """
        初始化 LightAgent。

        :param name: 代理名称。
        :param instructions: 代理指令。
        :param role: Agent 的角色描述。
        :param model: 使用的模型名称。
        :param api_key: API 密钥。
        :param base_url: API 的基础 URL。
        :param websocket_base_url: WebSocket 的基础 URL。
        :param memory: 外部传入的记忆模块，需实现 `retrieve` 和 `store` 方法。
        :param tree_of_thought: 是否启用思维链功能。
        :param tot_model: 使用的模型名称。
        :param tot_api_key: API 密钥。
        :param tot_base_url: API 的基础 URL。
        :param filter_tools: 是否启用工具过滤。
        :param tools: 工具列表，支持函数名称（字符串）或函数对象。
        :param debug: 是否启用调试模式。
        :param log_level: 日志级别（INFO, DEBUG, ERROR）。
        :param log_file: 日志文件路径。
        :param tracetools: log跟踪工具。
        """

        # 初始化核心组件
        self.tool_registry = ToolRegistry()
        self.tool_loader = ToolLoader()
        self.tool_dispatcher = AsyncToolDispatcher()
        self.tool_dispatcher.function_mappings = self.tool_registry.function_mappings

        self.mcp_setting = None
        self.mcp_client = None
        if not model:
            model = "gpt-4o-mini"  # 默认模型
        if not api_key:
            api_key = os.environ.get("OPENAI_API_KEY")
        if not base_url:
            base_url = os.environ.get("OPENAI_BASE_URL")
        self.loaded_tools = {}  # 用于存储已加载的工具函数
        if not name:
            random_suffix = random.randint(10000000, 99999999)  # 生成一个8位随机数作为agent编号
            name = f"LightAgent{random_suffix}"
        self.name = name
        if not instructions:
            instructions = "You are a helpful agent."
        self.instructions = instructions
        self.role = role
        self.model = model
        self.memory = memory
        self.tree_of_thought = tree_of_thought
        self.self_learning = self_learning
        self.filter_tools = filter_tools

        self.debug = debug
        self.log_level = log_level.upper()
        self.traceid = ""  # 用于存储 traceid
        # 确保 log 目录存在
        log_dir = 'logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        # 将 log_file 路径设置为 log 目录下的文件
        if debug:
            self.log_file = os.path.join(log_dir, log_file)
            # Set up the logger
            # 初始化日志系统
            self.logger = LoggerManager(
                name=self.name,
                debug=debug,
                log_level=log_level,
                log_file=log_file
            )

        if tools is None:
            self.tools = []
        if tools:
            self.tools = tools
            # 初始化工具列表
            self.load_tools(tools)
            # register_tool_manually(tools)

        if api_key is None:
            raise ValueError(
                "The api_key client option must be set either by passing api_key to the client or by setting the OPENAI_API_KEY environment variable"
            )
        self.api_key = api_key
        self.websocket_base_url = websocket_base_url
        self.base_url = base_url or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1"

        if self.tree_of_thought:
            if tot_api_key is None:
                tot_api_key = self.api_key
            if tot_base_url is None:
                tot_base_url = self.base_url
            if not tot_model:
                tot_model = "deepseek-r1"  # 默认思维推理模型为deepseek-r1
            self.tot_model = tot_model

        # 初始化客户端
        self._initialize_clients(tracetools, tot_api_key, tot_base_url, tot_model)
        self.chat_params = {}  # history 存储器

    def _initialize_clients(self, tracetools, tot_api_key, tot_base_url, tot_model):
        """初始化 OpenAI 客户端"""
        if tracetools:
            from langfuse.openai import openai as la_openai
            la_openai.langfuse_public_key = tracetools['TraceToolConfig']['langfuse_public_key']
            la_openai.langfuse_secret_key = tracetools['TraceToolConfig']['langfuse_secret_key']
            la_openai.langfuse_enabled = tracetools['TraceToolConfig']['langfuse_enabled']
            la_openai.langfuse_host = tracetools['TraceToolConfig']['langfuse_host']
            la_openai.base_url = self.base_url
            la_openai.api_key = self.api_key
            self.client = la_openai

            if self.tree_of_thought:
                la_openai.base_url = tot_base_url or self.base_url
                la_openai.api_key = tot_api_key or self.api_key
                self.tot_client = la_openai
        else:
            from openai import OpenAI as la_openai
            self.client = la_openai(
                base_url=self.base_url,
                api_key=self.api_key
            )
            if self.tree_of_thought:
                self.tot_client = la_openai(
                    base_url=tot_base_url or self.base_url,
                    api_key=tot_api_key or self.api_key
                )

    def get_history(self) -> List[Dict[str, Any]]:
        """
        获取对话的history的描述（OpenAI 格式）
        """
        return deepcopy(self.chat_params['messages'])

    def get_tools(self) -> List[Dict[str, Any]]:
        """
        获取所有工具的描述（OpenAI 格式）
        """
        return deepcopy(self.tool_registry.get_tools())

    def get_tool(self, tool_name: str) -> Callable:
        """
        用于外部可以获取已加载的工具函数
        :param tool_name: 工具名称
        :return: 工具函数
        """
        if tool_name in self.loaded_tools:
            return self.loaded_tools[tool_name]
        raise ValueError(f"Tool `{tool_name}` is not loaded.")

    def load_tools(self, tool_names: List[Union[str, Callable]], tools_directory: str = "tools"):
        """加载并注册工具"""
        for tool in tool_names:
            if isinstance(tool, str):
                try:
                    tool_func = self.tool_loader.load_tool(tool)
                    self.tool_registry.register_tool(tool_func)
                    self.log("DEBUG", "load_tools", {"tool": tool, "status": "success"})
                except Exception as e:
                    self.log("ERROR", "load_tools", {"tool": tool, "error": str(e)})
            elif callable(tool) and hasattr(tool, "tool_info"):
                if self.tool_registry.register_tool(tool):
                    self.log("DEBUG", "register_tool", {"tool": tool.__name__, "status": "success"})

    async def setup_mcp(
            self,
            mcp_setting: dict | None = None,  # mcp 设置
    ):
        if mcp_setting:
            self.mcp_setting = mcp_setting
        """单独初始化 MCP 模块"""
        if self.mcp_setting and not self.mcp_client:
            self.mcp_client = MCPClientManager(self.mcp_setting, self.tool_registry)
            await self.mcp_client.register_mcp_tool()
            self.log("INFO", "setup_mcp", "MCP 模块初始化成功")

    def log(self, level, action, data):
        """
        日志打印入口
        """
        if not self.debug:
            return
        self.logger.log(level, action, data)

    def run(
            self,
            query: str,
            tools: List[Union[str, Callable]] | None = None,  # 运行时传入的工具
            light_swarm=None,
            stream: bool = False,
            max_retry: int = 10,
            user_id: str = "default_user",
            history: list = None,
            metadata: Optional[Dict] = None,
    ) -> Union[Generator[str, None, None], str]:
        """
        运行代理，处理用户输入。

        :param query: 用户输入。
        :param tools: 运行时传入的工具列表，支持函数名称（字符串）或函数对象。
        :param light_swarm: LightSwarm 实例，用于任务转移。
        :param stream: 是否启用流式输出。
        :param max_retry: 最大重试次数。
        :param user_id: 用户 ID。
        :param history: 历史对话 。
        :param metadata: 元数据。
        :return: 代理的回复。
        """
        # 设置跟踪ID
        traceid = uuid4().hex
        if self.debug and hasattr(self, 'logger'):  # 仅在 debug=True 且 logger 存在时记录日志
            self.logger.set_traceid(traceid)
        self.log("INFO", "run_start", {"query": query, "user_id": user_id, "stream": stream})

        # 初始化历史记录
        history = history or []

        # 处理运行时传入的工具
        runtime_tools = []
        if tools:
            runtime_tools = self._process_runtime_tools(tools)

        # 0. 判断是否需要转移任务
        if light_swarm:
            result = self._handle_task_transfer(query, light_swarm, stream)
            if result is not None:
                return result

        # 1. 正常处理任务
        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M:%S")
        system_prompt = (
            f"##代理名称：{self.name}\n"
            f"##代理指令：{self.instructions}\n"
            f"##身份：{self.role}\n"
            f"请一步一步思考来完成用户的要求。尽可能完成用户的回答，如果有补充信息，请参考补充信息来调用工具，直到获取所有满足用户的提问所需的答案。\n"
            f"今日的日期: {current_date} 当前时间: {current_time}"
        )
        # 添加记忆上下文
        query = self._add_memory_context(query, user_id)

        # 思维链处理
        active_tools = []
        if self.tree_of_thought:
            tot_response, active_tools = self.run_thought(query, runtime_tools)
            system_prompt += f"\n##以下是问题的补充说明\n{tot_response}"
            self.log("DEBUG", "tree_of_thought", {"response": tot_response, "active_tools": active_tools})
        # 如果没有启用思维链且有运行时工具，则使用运行时工具
        elif runtime_tools:
            active_tools = runtime_tools
            self.log("DEBUG", "use_runtime_tools", {"runtime_tools": runtime_tools})

        # 在用户查询后追加 "no_think"
        # modified_query = query + "/no_think"
        # 准备API参数
        self.chat_params = {
            "model": self.model,
            "messages": [{"role": "system", "content": system_prompt}] + history + [
                {"role": "user", "content": query}],
            "stream": stream
        }

        # 添加参数
        if metadata:
            for key, value in metadata.items():
                self.chat_params[key] = value

        # 添加工具
        # 优先级：active_tools > runtime_tools > 初始化时的工具
        final_tools = []
        if active_tools:
            final_tools = active_tools
        elif runtime_tools:
            final_tools = runtime_tools
        else:
            final_tools = self.tool_registry.get_tools()

        if final_tools:
            self.chat_params["tools"] = final_tools
            self.chat_params["tool_choice"] = "auto"
            self.log("DEBUG", "final_tools_selected",
                     {"tools": [t.get("function", {}).get("name", str(t)) for t in final_tools]})

        # 添加跟踪会话
        if hasattr(self, 'tracetools') and self.tracetools:
            self.chat_params["session_id"] = traceid

        # 调用模型
        self.log("DEBUG", "first_request_params", {"params": self.chat_params})
        response = self.client.chat.completions.create(**self.chat_params)
        return self._core_run_logic(response, stream, max_retry)

    def _process_runtime_tools(self, tools: List[Union[str, Callable]]) -> List[Dict]:
        """
        处理运行时传入的工具，返回OpenAI格式的工具描述

        :param tools: 运行时传入的工具列表
        :return: OpenAI格式的工具描述列表
        """
        runtime_tools = []
        temp_registry = ToolRegistry()

        for tool in tools:
            if isinstance(tool, str):
                try:
                    tool_func = self.tool_loader.load_tool(tool)
                    temp_registry.register_tool(tool_func)
                except Exception as e:
                    self.log("ERROR", "load_runtime_tool", {"tool": tool, "error": str(e)})
            elif callable(tool) and hasattr(tool, "tool_info"):
                temp_registry.register_tool(tool)

        runtime_tools = temp_registry.get_tools()
        self.log("DEBUG", "runtime_tools_processed", {"count": len(runtime_tools)})
        return runtime_tools

    def _add_memory_context(self, query: str, user_id: str) -> str:
        """添加记忆上下文"""
        if not self.memory:
            return query

        context = ""
        related_memories = self.memory.retrieve(query=query, user_id=user_id)
        if related_memories and related_memories.get("results"):
            context += "\n##用户偏好\n用户之前提到了:\n" + "\n".join(
                [m["memory"] for m in related_memories["results"]]
            )
        self.memory.store(data=query, user_id=user_id)

        if self.self_learning:
            agent_memories = self.memory.retrieve(query=query, user_id=self.name)
            if agent_memories and agent_memories.get("results"):
                context += "\n##问题相关补充信息:\n" + "\n".join(
                    [m["memory"] for m in agent_memories["results"]]
                )
            self.memory.store(data=query, user_id=self.name)

        return f"{context}\n##用户提问：\n{query}" if context else query

    def _core_run_logic(self, response, stream, max_retry) -> Union[Generator[str, None, None], str]:
        """核心运行逻辑"""
        if stream:
            return self._run_stream_logic(response, max_retry)
        else:
            return self._run_non_stream_logic(response, max_retry)

    def _run_non_stream_logic(self, response, max_retry) -> Union[str, None]:
        """
        非流式处理逻辑。
        """
        for _ in range(max_retry):
            if response.choices[0].message.tool_calls:
                # 初始化一个列表，用于存储所有工具调用的结果
                tool_responses = []
                # 初始化变量
                output = ""
                function_call_name = ""
                tool_calls = response.choices[0].message.tool_calls
                self.log("DEBUG", "non_stream tool_calls", {"tool_calls": tool_calls})

                # 遍历所有工具调用
                for tool_call in tool_calls:
                    function_call = tool_call.function

                    # 尝试自动修复常见转义问题
                    fixed_args = function_call.arguments.replace('\\"', '"').replace('\\\\', '\\')
                    self.log("DEBUG", "non_stream function_call", {"function_call": fixed_args})

                    # 解析函数参数
                    function_args = json.loads(fixed_args)

                    # 调用工具并获取响应
                    tool_response = asyncio.run(self.tool_dispatcher.dispatch(function_call.name, function_args))
                    function_call_name = function_call.name
                    combined_response = ""
                    single_tool_response = ""

                    # 如果工具返回的是生成器（流式输出），则将所有 chunk 叠加
                    if isinstance(tool_response, Generator):
                        # print(f"Streaming response from tool: {function_call.name}")
                        for chunk in tool_response:
                            # print("Received chunk:", chunk)  # 打印每个 chunk
                            if function_call_name == 'finish':
                                content = chunk.choices[0].delta.content or ""
                                combined_response += content  # 将每个 chunk 叠加
                            else:
                                combined_response += chunk  # 将每个 chunk 叠加
                        if combined_response == "":
                            combined_response = "".join(tool_response)

                        # 将 combined_response 解析为 JSON 对象（如果它是 JSON 字符串）
                        try:
                            combined_response = json.loads(combined_response)  # 解析 JSON
                        except json.JSONDecodeError:
                            pass  # 如果不是 JSON 字符串，保持原样

                        # 将 JSON 对象中的 Unicode 编码转换为中文字符
                        if isinstance(combined_response, dict):
                            combined_response = json.dumps(combined_response, ensure_ascii=False)  # 确保中文字符不转义
                        single_tool_response = combined_response  # 处理单个工具的方法

                    else:
                        # print(f"Non-streaming response from tool: {function_call.name}")
                        combined_response = tool_response
                        # print("tool_response type:",type(combined_response))
                        # 如果是 JSON 字符串，解析并转换为中文
                        if isinstance(combined_response, str):
                            try:
                                combined_response = json.loads(combined_response)  # 解析 JSON
                                combined_response = json.dumps(combined_response, ensure_ascii=False)  # 转换为中文
                            except json.JSONDecodeError:
                                combined_response = tool_response
                                pass  # 如果不是 JSON 字符串，保持原样
                        single_tool_response = combined_response  # 处理单个工具的方法

                    self.log("INFO", "non_stream single_tool_response",
                             {"single_tool_response": single_tool_response})

                    # 将单个工具的响应结果添加到列表中
                    tool_responses.append(single_tool_response)

                # 将所有工具调用的结果合并为一个字符串
                self.log("DEBUG", "non_stream tool_responses", {"tool_responses": tool_responses})

                combined_tool_response = "\n".join(tool_responses)

                # 将工具调用和响应添加到消息列表中
                self.chat_params["messages"].append(
                    {
                        "role": "assistant",
                        "content": f"使用工具： \n {json.dumps([tool_call.function.model_dump() for tool_call in tool_calls], ensure_ascii=False)}\n",
                    }
                )
                self.chat_params["messages"].append(
                    {
                        "role": "user",
                        "content": f"工具响应内容：\n {combined_tool_response} \n 请给出下一步输出",
                    }
                )
            else:
                # 返回最终回复
                reply = response.choices[0].message.content
                self.log("INFO", "non_stream final_reply", {"reply": reply})
                return reply

            # 更新响应
            if function_call_name == 'finish':
                return  # 如果最后调用了finish工具，则结束生成器
            # print("params:",self.chat_params)
            self.log("DEBUG", "non_stream chat-completions params", {"params": self.chat_params})

            try:
                response = self.client.chat.completions.create(**self.chat_params)
            except Exception as e:
                print(f"An error occurred: {e}")

        # 重试次数用尽
        self.log("ERROR", "max_retry_reached", {"message": "Failed to generate a valid response."})
        return "Failed to generate a valid response."

    def _run_stream_logic(self, response, max_retry) -> Generator[str, None, None]:
        """流式处理逻辑"""
        for _ in range(max_retry):
            # 初始化变量
            output = ""
            tool_calls = []  # 用于存储所有工具调用的信息
            tool_responses = []  # 用于存储所有工具调用的结果
            finish_called = False  # 标记是否调用了finish工具
            reasoning_content = ""
            content = ""

            for chunk in response:

                if chunk.choices and len(chunk.choices) > 0:
                    choice = chunk.choices[0]

                if choice and hasattr(choice.delta, "reasoning_content") and choice.delta.reasoning_content is not None:
                    reasoning_content = choice.delta.reasoning_content or ""

                if reasoning_content:
                    output += reasoning_content

                if choice and hasattr(choice.delta, "content") and choice.delta.content is not None:
                    content = choice.delta.content or ""

                if content:
                    output += content

                yield chunk  # 流式返回内容

                try:
                    # 检查是否有工具调用
                    if chunk.choices and chunk.choices[0].delta.tool_calls:
                        tool_call_delta = chunk.choices[0].delta.tool_calls[0]

                        # 获取工具调用的索引，确保它是有效的整数
                        tool_call_index = tool_call_delta.index if hasattr(tool_call_delta,
                                                                           "index") and tool_call_delta.index is not None else 0

                        # 如果工具调用信息尚未记录，初始化一个空字典
                        if len(tool_calls) <= tool_call_index:
                            tool_calls.append({"name": "", "arguments": "", "index": tool_call_index, "title": ""})

                        # 更新工具调用的名称
                        if hasattr(tool_call_delta.function, "name") and tool_call_delta.function.name:
                            tool_calls[tool_call_index]["name"] = tool_call_delta.function.name

                        # 更新工具调用的参数
                        if hasattr(tool_call_delta.function, "arguments") and tool_call_delta.function.arguments:
                            tool_calls[tool_call_index]["arguments"] += tool_call_delta.function.arguments

                except (IndexError, AttributeError, KeyError) as e:
                    self.log("ERROR", "tool_call_error", {
                        "error": str(e),
                        "traceback": traceback.format_exc()
                    })

                # 如果流式输出结束
                finish_reason = chunk.choices[0].finish_reason if chunk.choices else None
                if finish_reason == "stop" and not any(tc["name"] for tc in tool_calls):
                    self.log("INFO", "stream_response", {"output": output})
                    return  # 结束生成器

                # 如果工具调用结束
                elif finish_reason in ("tool_calls", "stop") and any(tc["name"] for tc in tool_calls):
                    # 遍历所有工具调用
                    self.log("DEBUG", "stream tool_calls", {"tool_calls": tool_calls})
                    for tool_call in tool_calls:
                        if tool_call["name"]:  # 确保工具调用有名称
                            tool_name = tool_call["name"]
                            arguments = tool_call["arguments"]

                            # 从注册表中获取工具标题
                            tool_info = self.tool_registry.function_info.get(tool_name, {})
                            tool_title = tool_info.get("tool_title") or ""

                            # 更新工具调用信息
                            tool_call["title"] = tool_title

                            # 记录调用工具
                            tool_call_info = {
                                "name": tool_name,
                                "title": tool_title,
                                "arguments": arguments,
                            }
                            self.log("INFO", "stream function_call", {"tool_call_start": tool_call_info})
                            # 将工具的调用信息推送给开发者
                            yield tool_call_info

                            # 解析参数并调用工具
                            try:
                                # 使用正则表达式将多个 JSON 对象拆分开
                                json_objects = re.findall(r'\{.*?\}', tool_call_info["arguments"])

                                # 解析每个 JSON 对象并调用工具
                                # for json_obj in json_objects:
                                #     function_args = json.loads(json_obj)
                                #     tool_response = dispatch_tool(function_call["name"], function_args)
                                #     tool_responses.append(tool_response)

                                for json_obj in json_objects:
                                    # 尝试自动修复常见转义问题
                                    fixed_args = json_obj.replace('\\"', '"').replace('\\\\', '\\')
                                    self.log("DEBUG", "stream fixed_args", {"fixed_args": fixed_args})

                                    # 解析参数
                                    function_args = json.loads(fixed_args)

                                    # 调用工具
                                    tool_response = asyncio.run(self.tool_dispatcher.dispatch(tool_name, function_args))

                                    # 处理不同类型的工具响应
                                    combined_response = ""
                                    single_tool_response = ""

                                    # 如果工具返回的是生成器（流式输出），则将所有 chunk 叠加
                                    if isinstance(tool_response, Generator):
                                        # print(f"Streaming response from tool: {function_call['name']}")
                                        for chunk in tool_response:
                                            # 将工具返回的数据继续流出
                                            if isinstance(chunk, ChatCompletionChunk):
                                                yield chunk
                                            else:
                                                tool_output = {
                                                    "name": tool_name,
                                                    "title": tool_title,
                                                    "output": chunk,
                                                }
                                                self.log("DEBUG", "stream tool_output",
                                                         {"tool_output": tool_output})
                                                yield tool_output
                                            # 将工具的调用信息推送给开发者
                                            if tool_name == 'finish':
                                                content = chunk.choices[0].delta.content or ""
                                                combined_response += content  # 将每个 chunk 叠加
                                            else:
                                                combined_response += chunk  # 将每个 chunk 叠加
                                        single_tool_response = combined_response  # 处理单个工具的方法
                                    else:
                                        # print(f"Non-streaming response from tool: {tool_response}")
                                        combined_response = str(tool_response)
                                        single_tool_response = combined_response  # 处理单个工具的方法
                                        tool_output = {
                                            "name": tool_name,
                                            "title": tool_title,
                                            "output": combined_response
                                        }
                                        yield tool_output

                                    # 记录工具响应
                                    self.log("INFO", "stream single_tool_response",
                                             {"single_tool_response": single_tool_response})

                                    # 将单个工具的响应结果保存到列表中
                                    tool_responses.append(single_tool_response)

                                    # 检查是否调用了finish工具
                                    if tool_name == 'finish':
                                        finish_called = True
                                        self.log("INFO", "finish_tool_called", {"response": combined_response})

                            except json.JSONDecodeError as e:
                                error_msg = f"JSON解析错误: {str(e)}\n参数: {arguments}"
                                self.log("ERROR", "json_decode_error",
                                         {"tool": tool_name, "title": tool_title, "error": error_msg})
                                tool_responses.append(error_msg)
                                yield {"name": tool_name, "title": tool_title, "error": error_msg}

                            except Exception as e:
                                error_msg = f"工具调用错误: {str(e)}\n{traceback.format_exc()}"
                                self.log("ERROR", "tool_execution_error", {
                                    "tool": tool_name,
                                    "title": tool_title,
                                    "error": error_msg
                                })
                                tool_responses.append(error_msg)
                                yield {"name": tool_name, "title": tool_title, "error": error_msg}

                    # 如果调用了finish工具，则结束处理
                    if finish_called:
                        return

                    # 准备下一轮请求
                    combined_tool_response = "\n".join(tool_responses)
                    tool_str = json.dumps(
                        [{"name": tool_call["name"], "arguments": tool_call["arguments"]} for tool_call in tool_calls],
                        ensure_ascii=False)

                    # 添加工具调用和响应到消息历史
                    self.chat_params["messages"].append(
                        {
                            "role": "assistant",
                            "content": f"使用工具： \n {tool_str}\n"
                        }
                    )
                    self.chat_params["messages"].append(
                        {
                            "role": "user",
                            "content": combined_tool_response,
                        }
                    )

                    # 创建新的响应流
                    self.log("DEBUG", "stream next_request_params", {"params": self.chat_params})
                    response = self.client.chat.completions.create(**self.chat_params)
                    break

        # 重试次数用尽
        self.log("ERROR", "max_retry_reached", {"message": "Failed to stream a valid response."})
        yield "Failed to stream a valid response."

    def _handle_task_transfer(
            self,
            query: str,
            light_swarm: 'LightSwarm',
            stream: bool = False,
    ) -> Union[Generator[str, None, None], str, None]:
        """
        处理任务转移逻辑。

        :param query: 用户输入。
        :param light_swarm: LightSwarm 实例。
        :param stream: 是否启用流式输出。
        :return: 如果任务需要转移，返回生成器或字符串；否则返回 None。
        """
        intent = self._detect_intent(query, light_swarm)
        if intent and intent.get("transfer_to"):
            target_agent_name = intent["transfer_to"]
            self.log("INFO", "detect_intent", {"intent": intent})
            if target_agent_name == self.name:
                self.log("INFO", "self_transfer_detected", {"target_agent": target_agent_name})
                return None  # 如果是自身，直接返回 None
            if stream:
                return self._handle_task_transfer_stream(light_swarm.agents[target_agent_name], query, light_swarm)
            else:
                return self._handle_task_transfer_non_stream(light_swarm.agents[target_agent_name], query, light_swarm)
        return None

    def _handle_task_transfer_stream(
            self,
            target_agent: 'LightAgent',
            context: str,
            light_swarm: 'LightSwarm',
    ) -> Generator[str, None, None]:
        """
        处理任务转移逻辑（流式输出）。

        :param target_agent: 目标代理。
        :param context: 共享的上下文信息。
        :param light_swarm: LightSwarm 实例。
        :return: 生成器，用于流式输出。
        """
        self.log("INFO", "transfer_to_agent", {"from": self.name, "to": target_agent.name, "context": context})

        # 检查目标代理是否有效
        if not hasattr(target_agent, 'run'):
            self.log("ERROR", "invalid_target_agent", {"target_agent": target_agent})
            yield "Failed to transfer task: invalid target agent"
            return

        try:
            yield from target_agent.run(context, light_swarm=light_swarm, stream=True)
        except Exception as e:
            self.log("ERROR", "run_failed", {"error": str(e)})
            raise  # 重新抛出异常以便调试

    def _handle_task_transfer_non_stream(
            self,
            target_agent: 'LightAgent',
            context: str,
            light_swarm: 'LightSwarm',
    ) -> str:
        """
        处理任务转移逻辑（非流式输出）。

        :param target_agent: 目标代理。
        :param context: 共享的上下文信息。
        :param light_swarm: LightSwarm 实例。
        :return: 字符串，表示非流式输出结果。
        """
        self.log("INFO", "transfer_to_agent", {"from": self.name, "to": target_agent.name, "context": context})

        # 检查目标代理是否有效
        if not hasattr(target_agent, 'run'):
            self.log("ERROR", "invalid_target_agent", {"target_agent": target_agent})
            return "Failed to transfer task: invalid target agent"

        try:
            result = target_agent.run(context, light_swarm=light_swarm, stream=False)
            if isinstance(result, Generator):
                return "".join(result)  # 将生成器转换为字符串
            return result
        except Exception as e:
            self.log("ERROR", "run_failed", {"error": str(e)})
            raise  # 重新抛出异常以便调试

    def _build_context(self, related_memories):
        """
        构建上下文，将用户输入和记忆内容结合。
        :param related_memories: 从记忆中检索到的相关内容。
        :return: 结合记忆后的上下文。
        """
        if not related_memories or not related_memories["results"]:
            return ""

        memory_context = "\n".join([m["memory"] for m in related_memories["results"]])
        if not memory_context:
            return ""

        prompt = f"\n##用户偏好 \n用户之前提到了\n{memory_context}。"
        self.log("DEBUG", "related_memories", {"memory_context": memory_context})
        return prompt

    def _build_agent_memory(self, agent_memories):
        """
        构建上下文，将用户输入和记忆内容结合。

        :param agent_memories: 从记忆中检索到的相关内容。
        :return: 结合记忆后的上下文。
        """
        if not agent_memories or not agent_memories["results"]:
            return ""

        memory_context = "\n".join([m["memory"] for m in agent_memories["results"]])
        if not memory_context:
            return ""

        prompt = f"\n##以下是解决该问题的相关补充信息：\n{memory_context}。"
        self.log("DEBUG", "agent_memories", {"memory_context": memory_context})
        return prompt

    def run_thought(self, query: str, runtime_tools: List[Dict] | None = None) -> tuple:
        """使用思维树的方式 让大模型先根据get_tools_str生成一个解答用户query的工具使用计划"""
        tot_model = self.tot_model
        # 修改：优先使用运行时工具，如果没有则使用初始化时的工具
        if runtime_tools:
            # 将runtime_tools转换为字符串形式
            tools_str = json.dumps(runtime_tools, indent=4, ensure_ascii=False)
            # 创建一个临时的ToolRegistry来过滤工具
            temp_registry = ToolRegistry()
            # 将runtime_tools注册到临时注册表中
            for tool_schema in runtime_tools:
                # 这里需要将OpenAI格式的工具schema转换为内部格式
                # 由于时间关系，这里简化处理，实际可能需要更复杂的转换
                pass
        else:
            tools = self.tool_registry.get_tools_str()

        if not isinstance(tools, str):
            tools = str(tools)  # 确保 tools 是字符串
        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M:%S")

        system_prompt = f"""你是一个智能助手，请根据用户输入的问题，结合工具使用计划，生成一个思维树，并按照思维树依次调用工具步骤，最终生成一个最终回答。\n 今日的日期: {current_date} 当前时间: {current_time} \n 工具列表: {tools}"""
        self.log("DEBUG", "run_thought", {"system_prompt": system_prompt})

        try:
            # 1. 第一次请求，生成初始的工具使用计划
            params = dict(model=tot_model,
                          messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": query}],
                          stream=False)
            response = self.tot_client.chat.completions.create(**params)
            thought_response = response.choices[0].message.content
            self.log("DEBUG", "thought_response", {"response": thought_response})

            # 2. 第二次请求，请求大模型反思并生成新的工具使用规划
            reflection_prompt = "请反思你的回答，请严格按照<工具列表>中的工具来规划，不可以创造其他新的工具。请输出新的任务规划，不要输出其他分析和回答。"
            reflection_params = dict(model=tot_model, messages=[
                {"role": "user", "content": f"{system_prompt} /n 开始思考问题: {query}"},
                {"role": "assistant", "content": thought_response},
                {"role": "user", "content": reflection_prompt}
            ], stream=False)
            self.log("DEBUG", "reflection_params", {"params": reflection_params})
            reflection_response = self.tot_client.chat.completions.create(**reflection_params)
            refined_content = reflection_response.choices[0].message.content
            self.log("DEBUG", "reflection_response", {"response": refined_content})

            # 获取工具的使用集合
            tool_reflection_prompt = """请严格按以下要求执行：
            1. 分析问题需求并规划需要使用的工具
            2. 仅输出包含工具名称的JSON格式结果
            3. 使用以下结构（示例）：
            {"tools": [{"name": "工具名称1"}, {"name": "工具名称2"}]}
            4. 不要包含任何解释性内容"""

            tool_reflection_params = dict(
                model=tot_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"问题分析请求：{query}"},
                    {"role": "assistant", "content": refined_content},
                    {"role": "user", "content": tool_reflection_prompt}
                ],
                response_format={"type": "json_object"},  # 强制JSON输出格式
                stream=False
            )

            self.log("DEBUG", "tool_reflection_params", {"params": tool_reflection_params})
            tool_reflection_response = self.tot_client.chat.completions.create(**tool_reflection_params)
            tool_reflection_result = tool_reflection_response.choices[0].message.content
            self.log("DEBUG", "tool_reflection_result", {"result": tool_reflection_result})

            # 3.执行自适应工具过滤
            current_tools = []
            if self.filter_tools:
                # 修改：优先使用运行时工具进行过滤
                if runtime_tools:
                    # 使用临时注册表进行过滤
                    temp_registry = ToolRegistry()
                    for tool_schema in runtime_tools:
                        # 这里需要将OpenAI格式的schema转换为内部格式
                        # 简化处理：直接添加到注册表中
                        pass
                    current_tools = runtime_tools  # 暂时直接使用运行时工具
                else:
                    current_tools = self.tool_registry.filter_tools(tool_reflection_result)
                self.log("DEBUG", "current_tools", {"get_tools": current_tools})

            return refined_content, current_tools

        except Exception as e:
            self.log("ERROR", "run_thought_failure", {"error": str(e)})
            raise RuntimeError(f"思维链执行失败: {str(e)}") from e

    def _detect_intent(self, query: str, light_swarm=None) -> Optional[Dict]:
        """
        使用大模型判断用户意图。

        :param query: 用户输入。
        :param light_swarm: LightSwarm 实例，用于获取所有代理信息。
        :return: 意图信息，例如 {"transfer_to": "Agent B"}。
        """
        if not light_swarm:
            return None

        # 获取所有代理的信息
        agents_info = []
        for agent_name, agent in light_swarm.agents.items():
            agents_info.append(f"代理名称: {agent_name}, 代理指令: {agent.instructions}")

        # 将代理信息拼接为字符串
        agents_info_str = "\n".join(agents_info)

        # 构建提示词
        prompt = f"""请分析以下用户输入的意图，如果需要转移任务，请返回目标代理的名称格式如下。
        transfer to agent_name
        以下是所有可用代理的信息：
    {agents_info_str}
    用户输入: {query}
请返回目标代理的名称：
"""

        # 调用大模型进行意图判断
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": prompt}]
        )
        intent = response.choices[0].message.content
        self.log("DEBUG", "detect_intent", {"intent": intent})

        # # 使用正则表达式解析意图
        # match = re.search(r"transfer to (\w+)", intent, re.IGNORECASE)
        # if match:
        #     target_agent_name = match.group(1)
        #     if target_agent_name in light_swarm.agents:
        #         return {"transfer_to": target_agent_name}
        # return None

        # 解析意图
        for agent_name in light_swarm.agents.keys():
            if f"transfer to {agent_name}" in intent:
                return {"transfer_to": agent_name}
        return None

    def _transfer_to_agent(
            self,
            target_agent: 'LightAgent',
            context: str,
            light_swarm=None,
            stream: bool = False,
    ) -> Union[Generator[str, None, None], str]:
        """
        将任务转移给另一个代理，支持流式和非流式输出。

        :param target_agent: 目标代理。
        :param context: 共享的上下文信息。
        :param light_swarm: LightSwarm 实例。
        :param stream: 是否启用流式输出。
        :return: 如果 stream=True，返回生成器；否则返回完整结果字符串。
        """
        self.log("INFO", "transfer_to_agent", {"from": self.name, "to": target_agent.name, "context": context})

        # 检查目标代理是否有效
        if not hasattr(target_agent, 'run'):
            self.log("ERROR", "invalid_target_agent", {"target_agent": target_agent})
            return "Failed to transfer task: invalid target agent"
        #
        # # 调用目标代理的 run 方法
        # if stream:
        #     yield from target_agent.run(context, light_swarm=light_swarm, stream=stream)
        # else:
        #     result = target_agent.run(context, light_swarm=light_swarm, stream=stream)
        #     if isinstance(result, Generator):
        #         return "".join(result)  # 将生成器转换为字符串
        #     return result
        try:
            if stream:
                yield from target_agent.run(context, light_swarm=light_swarm, stream=stream)
            else:
                result = target_agent.run(context, light_swarm=light_swarm, stream=stream)
                if isinstance(result, Generator):
                    return "".join(result)  # 将生成器转换为字符串
                return result
        except Exception as e:
            self.log("ERROR", "run_failed", {"error": str(e)})
            raise  # 重新抛出异常以便调试

    def create_tool(self, user_input: str, tools_directory: str = "tools"):
        """
        根据用户输入的文本生成 Python 代码，并将其保存为工具
        """
        # 调用大模型生成 Python 代码
        system_prompt = """
        The user will provide some exam text. Please parse the "tool_name" and "code" and output them in JSON format. 

        EXAMPLE INPUT: 
        请根据文档生成一个天气调用的工具，API介绍如下

        EXAMPLE JSON OUTPUT:
        {'tools': [{
            "tool_name": "get_weather",
            "tool_code": "import requests
            def get_weather(
        city_name: str
) -> str:
    /"/"/"
    Get the current weather for `city_name`
    /"/"/"
    if not isinstance(city_name, str):
        raise TypeError("City name must be a string")

    key_selection = {
        "current_condition": ["temp_C", "FeelsLikeC", "humidity", "weatherDesc", "observation_time"],
    }
    try:
        resp = requests.get(f"https://wttr.in/{city_name}?format=j1")
        resp.raise_for_status()
        resp = resp.json()
        ret = {k: {_v: resp[k][0][_v] for _v in v} for k, v in key_selection.items()}
    except:
        import traceback
        ret = "Error encountered while fetching weather data!\n" + traceback.format_exc()

    return str(ret)

# 在函数内部定义工具信息
get_weather.tool_info = {
    "tool_name": "get_weather",
    "tool_title": "天气查询",
    "tool_description": "获取指定城市的当前天气信息",
    "tool_params": [
        {"name": "city_name", "description": "要查询的城市名称", "type": "string", "required": True},
    ]
}"
        }]}
        """
        params = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that generates Python code in JSON format."},
                {"role": "user", "content": f"Generate Python tools based on the following description. "
                                            f"Return a JSON array where each item contains 'tool_name' and 'tool_code'. "
                                            f"\n {system_prompt} "
                                            f"Description:\n{user_input}"},
            ],
            "response_format": {"type": "json_object"},
        }
        try:
            response = self.client.chat.completions.create(**params)
            response_data = json.loads(response.choices[0].message.content)

            # 确保返回的数据是 JSON 对象
            if not isinstance(response_data, dict):
                raise ValueError("Response is not a JSON object.")

            # 遍历每个工具
            for tool_data in response_data["tools"]:
                tool_name = tool_data.get("tool_name")
                tool_code = tool_data.get("tool_code")

                if not tool_name or not tool_code:
                    self.log("ERROR", "invalid_tool_data", {"tool_data": tool_data})
                    continue

                # 保存生成的代码到 tools 目录
                tool_path = os.path.join(tools_directory, f"{tool_name}.py")
                with open(tool_path, "w", encoding="utf-8") as f:
                    f.write(tool_code)
                self.log("INFO", "tool_created", {"tool_name": tool_name, "tool_path": tool_path})

                # 自动加载新创建的工具
                self.load_tools([tool_name], tools_directory)
        except Exception as e:
            self.log("ERROR", "tool_creation_failed", {"error": str(e)})


class LightSwarm:
    def __init__(self):
        self.agents: Dict[str, LightAgent] = {}

    def register_agent(self, *agents: LightAgent):
        """
        注册一个或多个代理。

        :param agents: 要注册的代理实例，支持多个代理。
        """
        for agent in agents:
            if agent.name in self.agents:
                # print(f"Agent '{agent.name}' is already registered.")
                agent.log("INFO", "register_agent", {"agent_name": agent.name, "status": "already_registered"})
            else:
                self.agents[agent.name] = agent
                # print(f"Agent '{agent.name}' registered.")
                agent.log("INFO", "register_agent", {"agent_name": agent.name, "status": "registered"})

    def run(self, agent: LightAgent, query: str, stream=False):
        """
        运行指定代理。

        :param agent_name: 代理名称。
        :param query: 用户输入。
        :return: 代理的回复。
        """
        if agent.name not in self.agents:
            raise ValueError(f"Agent '{agent.name}' not found.")
        return agent.run(query, light_swarm=self, stream=stream)


if __name__ == "__main__":
    # Example of registering and using a tool
    print("This is LightAgent")
    # print(dispatch_tool("example_tool", {"param1": "test"}))
