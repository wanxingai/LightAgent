#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
作者: [weego/WXAI-Team]
最后更新: 2026-02-20
"""

import json
import importlib
import importlib.util
import inspect
import os
import re
import traceback
from copy import deepcopy
from typing import List, Dict, Any, Callable, Union, Generator, AsyncGenerator

from .errors import format_error_code, format_lightagent_error


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
            param_def = {k: v for k, v in param.items() if k not in ("name", "required")}
            tool_params_openai[param["name"]] = param_def
            if param.get("required", False):
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

        self.openai_function_schemas = [
            schema for schema in self.openai_function_schemas
            if schema.get("function", {}).get("name") != tool_name
        ]
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
        if not self._is_safe_tool_name(tool_name):
            raise ValueError(f"Invalid tool name: {tool_name}")

        if tool_name in self.loaded_tools:
            return self.loaded_tools[tool_name]

        tools_directory = os.path.abspath(self.tools_directory)
        tool_path = os.path.abspath(os.path.join(tools_directory, f"{tool_name}.py"))
        if not tool_path.startswith(tools_directory + os.sep):
            raise ValueError(f"Tool path escapes tools directory: {tool_name}")
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

    @staticmethod
    def _is_safe_tool_name(tool_name: str) -> bool:
        return bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", str(tool_name)))

    def load_tools(self, tool_names: List[str]) -> Dict[str, Callable]:
        """批量加载工具"""
        for tool_name in tool_names:
            if tool_name not in self.loaded_tools:
                self.load_tool(tool_name)
        return self.loaded_tools


class AsyncToolDispatcher:
    """异步工具调度器"""

    def __init__(self, function_mappings: Dict[str, Callable] = None, function_info: Dict[str, Dict[str, Any]] = None):
        self.function_mappings = function_mappings or {}
        self.function_info = function_info or {}

    async def dispatch(self, tool_name: str, tool_params: Dict[str, Any]) -> Union[
        str, Generator[str, None, None], AsyncGenerator[str, None]]:
        """调用工具执行，支持同步/异步工具及流式输出"""
        if tool_name not in self.function_mappings:
            return format_error_code("LA-TOOL", f"Tool `{tool_name}` not found.")

        tool_call = self.function_mappings[tool_name]
        validation_error = self._validate_tool_params(tool_name, tool_params)
        if validation_error:
            return validation_error
        try:
            # 处理不同类型的工具
            if inspect.iscoroutinefunction(tool_call):
                # 异步函数 - 直接 await 获取结果
                result = await tool_call(**tool_params)
            # elif inspect.isasyncgenfunction(tool_call):
                # 异步生成器 - 需要收集所有结果
                # result = []
                # async for chunk in tool_call(**tool_params):
                #     result.append(chunk)
                # # 如果只有一个结果，直接返回；否则返回列表
                # if len(result) == 1:
                #     result = result[0]
            elif inspect.isasyncgenfunction(tool_call):
                # 返回异步生成器对象，不做消费
                return tool_call(**tool_params)
            elif inspect.isgeneratorfunction(tool_call):
                # 同步生成器 - 收集所有结果
                return tool_call(**tool_params)
                # result = list(tool_call(**tool_params))
                # if len(result) == 1:
                #     result = result[0]
            else:
                # 普通函数 - 直接调用
                result = tool_call(**tool_params)

            # 将结果转换为字符串（OpenAI 要求 tool content 必须是字符串）
            return self._serialize_result(result)
        except Exception as e:
            return f"{format_lightagent_error(e, 'execute tool', default_code='LA-TOOL')}\n{traceback.format_exc()}"

    def _serialize_result(self, result: Any) -> str:
        """将任意类型的结果序列化为字符串"""
        if result is None:
            return "Tool executed successfully (no output)"
        elif isinstance(result, (dict, list)):
            return json.dumps(result, ensure_ascii=False)
        else:
            return str(result)

    def _validate_tool_params(self, tool_name: str, tool_params: Dict[str, Any]) -> str | None:
        """Validate required tool parameters and basic JSON-schema-like types."""
        tool_info = self.function_info.get(tool_name) or {}
        params = tool_info.get("tool_params") or []
        if not params:
            return None

        if not isinstance(tool_params, dict):
            return format_error_code("LA-TOOL", f"Tool `{tool_name}` arguments must be an object.")

        for param in params:
            name = param.get("name")
            if not name:
                continue
            required = bool(param.get("required", False))
            if required and name not in tool_params:
                return format_error_code("LA-TOOL", f"Tool `{tool_name}` missing required parameter `{name}`.")
            if name in tool_params and not self._matches_declared_type(tool_params[name], param.get("type")):
                expected = param.get("type")
                actual = type(tool_params[name]).__name__
                return format_error_code(
                    "LA-TOOL",
                    f"Tool `{tool_name}` parameter `{name}` expected `{expected}`, got `{actual}`.",
                )
        return None

    @staticmethod
    def _matches_declared_type(value: Any, declared_type: Any) -> bool:
        if declared_type is None:
            return True
        if isinstance(declared_type, str):
            normalized = declared_type.lower()
        else:
            normalized = str(declared_type).lower()

        if normalized in ("string", "str"):
            return isinstance(value, str)
        if normalized in ("integer", "int"):
            return isinstance(value, int) and not isinstance(value, bool)
        if normalized in ("number", "float"):
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        if normalized in ("boolean", "bool"):
            return isinstance(value, bool)
        if normalized in ("array", "list"):
            return isinstance(value, list)
        if normalized in ("object", "dict"):
            return isinstance(value, dict)
        return True

    async def async_stream_generator(self, async_gen: AsyncGenerator) -> AsyncGenerator[str, None]:
        async for chunk in async_gen:
            yield chunk

    def stream_generator(self, sync_gen: Generator) -> Generator[str, None, None]:
        for chunk in sync_gen:
            yield chunk
