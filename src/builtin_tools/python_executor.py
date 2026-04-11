#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
作者: [weego/WXAI-Team]
最后更新: 2026-02-22

内置工具：安全执行Python代码
"""

import os
import sys
import json
import tempfile
import subprocess
import traceback
import re
import ast
from typing import Dict, Any, List, Optional, Union, Tuple


def _parse_code_parameter(code_param: Union[str, Dict, Any]) -> str:
    """
    解析可能包含在各种格式中的代码参数

    Args:
        code_param: 可能以各种形式传入的代码参数

    Returns:
        提取出的代码字符串
    """
    # 如果已经是字符串，直接返回
    if isinstance(code_param, str):
        return code_param

    # 如果是字典，尝试提取常见的键
    if isinstance(code_param, dict):
        # 尝试各种可能的键名
        possible_keys = ['code', 'script', 'python_code', 'source', 'content', 'program']
        for key in possible_keys:
            if key in code_param:
                value = code_param[key]
                if isinstance(value, str):
                    return value
                elif isinstance(value, dict):
                    # 递归处理嵌套字典
                    return _parse_code_parameter(value)

        # 如果字典只有一个值，可能是直接传入的
        if len(code_param) == 1:
            value = next(iter(code_param.values()))
            if isinstance(value, str):
                return value

        # 尝试将整个字典转换为字符串
        return json.dumps(code_param, ensure_ascii=False)

    # 如果是列表，尝试连接或提取
    if isinstance(code_param, list):
        # 如果列表中的元素都是字符串，连接它们
        if all(isinstance(item, str) for item in code_param):
            return '\n'.join(code_param)
        # 否则转换为字符串
        return str(code_param)

    # 其他类型直接转字符串
    return str(code_param)


def _clean_code_string(code_str: str) -> str:
    """
    清理和修复代码字符串中的转义和格式问题

    Args:
        code_str: 原始代码字符串

    Returns:
        清理后的代码字符串
    """
    if not isinstance(code_str, str):
        code_str = str(code_str)

    # 步骤1: 修复常见的JSON转义问题
    # 将 \\n 替换为 \n，但要小心不要破坏已有的双反斜杠
    code_str = code_str.replace('\\n', '\n')
    code_str = code_str.replace('\\t', '\t')
    code_str = code_str.replace('\\r', '\r')

    # 步骤2: 修复引号转义
    # 将 \" 替换为 "，但要小心不要破坏字符串内部的转义引号
    code_str = code_str.replace('\\"', '"')
    code_str = code_str.replace("\\'", "'")

    # 步骤3: 修复双重转义
    code_str = code_str.replace('\\\\', '\\')

    # 步骤4: 修复Python f-string中的双花括号
    # f-string中的 {{ 和 }} 需要被保留
    # 这里只修复那些可能是JSON转义导致的多余花括号
    pattern = r'\{(\{[^}]*\})\}'
    code_str = re.sub(pattern, r'\1', code_str)

    # 步骤5: 移除可能存在的JSON包装
    # 有时代码可能被包装在JSON字符串中
    if code_str.startswith('"') and code_str.endswith('"'):
        try:
            code_str = json.loads(code_str)
        except:
            code_str = code_str[1:-1]

    # 步骤6: 尝试解析为JSON并提取代码字段
    try:
        # 尝试将整个字符串解析为JSON
        parsed = json.loads(code_str)
        if isinstance(parsed, dict):
            # 查找常见的代码字段
            code = _parse_code_parameter(parsed)
            if code != code_str:
                return _clean_code_string(code)  # 递归清理
        elif isinstance(parsed, str):
            return _clean_code_string(parsed)  # 递归清理
    except:
        pass

    return code_str


def _extract_code_from_text(text: str) -> str:
    """
    从文本中提取代码块

    Args:
        text: 可能包含代码块的文本

    Returns:
        提取出的代码字符串
    """
    # 查找Python代码块（```python ... ```）
    python_block_pattern = r'```python\s*\n(.*?)\n```'
    matches = re.findall(python_block_pattern, text, re.DOTALL)
    if matches:
        return '\n'.join(matches)

    # 查找通用代码块（``` ... ```）
    code_block_pattern = r'```\s*\n(.*?)\n```'
    matches = re.findall(code_block_pattern, text, re.DOTALL)
    if matches:
        return '\n'.join(matches)

    # 查找内联代码（`...`）
    inline_pattern = r'`([^`]+)`'
    matches = re.findall(inline_pattern, text)
    if matches:
        return '\n'.join(matches)

    return text


def _safe_import_check(code: str) -> tuple[bool, str]:
    """
    检查代码中的导入是否安全

    Args:
        code: Python代码

    Returns:
        (是否安全, 错误信息)
    """
    dangerous_modules = ['os', 'subprocess', 'sys', 'shutil', 'glob',
                         'pickle', 'shelve', 'ctypes', 'pty', 'socket',
                         'importlib', '__builtins__', 'eval', 'exec',
                         'compile', 'open', 'input', 'raw_input']

    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            # 检查导入语句
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in dangerous_modules:
                        return False, f"禁止导入危险模块 '{alias.name}'"
                    # 检查是否尝试导入子模块
                    if any(alias.name.startswith(mod + '.') for mod in dangerous_modules):
                        return False, f"禁止导入危险模块 '{alias.name}'"
            elif isinstance(node, ast.ImportFrom):
                if node.module in dangerous_modules:
                    return False, f"禁止从危险模块 '{node.module}' 导入"
                # 检查导入的函数是否危险
                if node.module in ['builtins', '__builtins__']:
                    for alias in node.names:
                        if alias.name in ['eval', 'exec', 'compile', 'open', 'input']:
                            return False, f"禁止使用内置函数 '{alias.name}'"

            # 检查函数调用
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ['eval', 'exec', 'compile', '__import__']:
                        return False, f"禁止使用 '{node.func.id}' 函数"
                elif isinstance(node.func, ast.Attribute):
                    if node.func.attr in ['system', 'popen', 'call', 'run']:
                        return False, f"禁止使用子进程函数 '{node.func.attr}'"
    except SyntaxError as e:
        return False, f"语法错误：{str(e)}"

    return True, ""


def _install_requirements(requirements: List[str], python_path: str, tmpdir: str) -> Tuple[bool, str]:
    """
    安装依赖，自动处理pip升级

    Args:
        requirements: 依赖包列表
        python_path: Python解释器路径
        tmpdir: 临时目录路径

    Returns:
        (是否成功, 错误信息或成功信息)
    """
    try:
        # 先升级pip
        print(f"正在升级pip...")
        pip_upgrade = subprocess.run(
            [python_path, "-m", "pip", "install", "--upgrade", "pip"],
            capture_output=True,
            text=True,
            timeout=60
        )

        if pip_upgrade.returncode != 0:
            return False, f"pip升级失败：{pip_upgrade.stderr}"

        print(f"pip升级成功，开始安装依赖...")

        # 安装依赖
        for req in requirements:
            # 确保req是字符串
            if not isinstance(req, str):
                req = str(req)

            print(f"正在安装: {req}")
            result = subprocess.run(
                [python_path, "-m", "pip", "install", req],
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode != 0:
                return False, f"安装 {req} 失败：{result.stderr}"
            print(f"安装 {req} 成功")

        return True, "依赖安装成功"
    except subprocess.TimeoutExpired:
        return False, "安装超时"
    except Exception as e:
        return False, f"安装异常：{str(e)}"


def execute_python_code(
        code: Union[str, Dict, List, Any],
        timeout: int = 30,
        requirements: List[str] = None,
        input_data: str = None,
        capture_output: bool = True
) -> str:
    """
    在隔离的临时目录中安全执行Python代码

    Args:
        code: 要执行的Python代码（可以是字符串、字典或列表）
        timeout: 执行超时时间（秒）
        requirements: 需要安装的依赖包列表
        input_data: 传递给代码的标准输入数据
        capture_output: 是否捕获输出

    Returns:
        执行结果或错误信息
    """
    # 步骤1: 解析代码参数
    raw_code = _parse_code_parameter(code)

    # 步骤2: 清理代码字符串
    cleaned_code = _clean_code_string(raw_code)

    # 步骤3: 从文本中提取代码块
    final_code = _extract_code_from_text(cleaned_code)

    # 如果代码为空，返回错误
    if not final_code.strip():
        return "错误：没有找到可执行的代码"

    # 步骤4: 安全检查
    is_safe, error_msg = _safe_import_check(final_code)
    if not is_safe:
        return f"安全错误：{error_msg}"

    # 创建临时目录
    with tempfile.TemporaryDirectory(prefix="lightagent_python_") as tmpdir:
        script_path = os.path.join(tmpdir, "script.py")
        output_path = os.path.join(tmpdir, "output.json")
        error_path = os.path.join(tmpdir, "error.txt")

        # 写入代码文件
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(final_code)

        # 如果需要安装依赖
        if requirements:
            try:
                # 创建虚拟环境
                venv_path = os.path.join(tmpdir, "venv")
                venv_result = subprocess.run(
                    [sys.executable, "-m", "venv", venv_path],
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                if venv_result.returncode != 0:
                    return f"创建虚拟环境失败：{venv_result.stderr}"

                # 获取pip路径
                if os.name == 'nt':  # Windows
                    pip_path = os.path.join(venv_path, "Scripts", "pip")
                    python_path = os.path.join(venv_path, "Scripts", "python")
                else:  # Unix/Linux/Mac
                    pip_path = os.path.join(venv_path, "bin", "pip")
                    python_path = os.path.join(venv_path, "bin", "python")

                # 使用改进的依赖安装函数
                success, message = _install_requirements(requirements, python_path, tmpdir)
                if not success:
                    return f"依赖安装失败：{message}"

                print(message)

            except subprocess.TimeoutExpired:
                return "依赖安装超时"
            except Exception as e:
                return f"依赖安装异常：{str(e)}"
        else:
            python_path = sys.executable
            venv_path = None

        # 准备执行命令
        cmd = [python_path, script_path]

        # 准备标准输入
        stdin_data = input_data.encode('utf-8') if input_data else None

        try:
            # 执行代码
            result = subprocess.run(
                cmd,
                input=stdin_data,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                cwd=tmpdir,
                env={} if venv_path else os.environ.copy()
            )

            # 构建输出结果
            output_parts = []

            if result.stdout:
                output_parts.append(result.stdout)

            if result.stderr:
                output_parts.append(result.stderr)

            if result.returncode != 0:
                output_parts.append(f"【退出代码】{result.returncode}")

            final_output = "\n".join(output_parts) if output_parts else "【执行完成，无输出】"

            return final_output

        except subprocess.TimeoutExpired:
            return f"执行超时（超过{timeout}秒）"
        except Exception as e:
            return f"执行异常：{str(e)}\n{traceback.format_exc()}"


def execute_python_file(
        file_path: str,
        timeout: int = 30,
        requirements: List[str] = None,
        args: List[str] = None
) -> str:
    """
    执行指定的Python文件（在隔离环境中）

    Args:
        file_path: Python文件路径
        timeout: 执行超时时间（秒）
        requirements: 需要安装的依赖包列表
        args: 传递给脚本的命令行参数

    Returns:
        执行结果或错误信息
    """
    if not os.path.exists(file_path):
        return f"错误：文件 '{file_path}' 不存在"

    if not file_path.endswith('.py'):
        return f"错误：'{file_path}' 不是Python文件"

    # 读取文件内容
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
    except Exception as e:
        return f"读取文件失败：{str(e)}"

    # 添加命令行参数支持
    if args:
        code = f"import sys\nsys.argv = ['{file_path}'] + {args}\n" + code

    return execute_python_code(code, timeout, requirements)


def execute_python_code_stream(
        code: Union[str, Dict, List, Any],
        timeout: int = 30,
        requirements: List[str] = None,
        chunk_size: int = 100
):
    """
    流式执行Python代码，逐步返回结果

    Args:
        code: 要执行的Python代码
        timeout: 执行超时时间（秒）
        requirements: 需要安装的依赖包列表
        chunk_size: 每次返回的字符数
    """
    # 解析和清理代码
    raw_code = _parse_code_parameter(code)
    cleaned_code = _clean_code_string(raw_code)
    final_code = _extract_code_from_text(cleaned_code)

    if not final_code.strip():
        yield "错误：没有找到可执行的代码"
        return

    # 安全检查
    is_safe, error_msg = _safe_import_check(final_code)
    if not is_safe:
        yield f"安全错误：{error_msg}"
        return

    with tempfile.TemporaryDirectory(prefix="lightagent_python_") as tmpdir:
        script_path = os.path.join(tmpdir, "script.py")

        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(final_code)

        # 如果需要安装依赖
        if requirements:
            try:
                venv_path = os.path.join(tmpdir, "venv")
                venv_result = subprocess.run(
                    [sys.executable, "-m", "venv", venv_path],
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                if venv_result.returncode != 0:
                    yield f"创建虚拟环境失败：{venv_result.stderr}"
                    return

                if os.name == 'nt':
                    pip_path = os.path.join(venv_path, "Scripts", "pip")
                    python_path = os.path.join(venv_path, "Scripts", "python")
                else:
                    pip_path = os.path.join(venv_path, "bin", "pip")
                    python_path = os.path.join(venv_path, "bin", "python")

                # 使用改进的依赖安装函数
                success, message = _install_requirements(requirements, python_path, tmpdir)
                if not success:
                    yield f"依赖安装失败：{message}"
                    return

                print(message)

            except Exception as e:
                yield f"依赖安装异常：{str(e)}"
                return
        else:
            python_path = sys.executable

        # 使用Popen进行流式输出
        try:
            process = subprocess.Popen(
                [python_path, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                cwd=tmpdir
            )

            # 流式读取输出
            current_chunk = ""
            for line in process.stdout:
                current_chunk += line
                if len(current_chunk) >= chunk_size:
                    yield current_chunk
                    current_chunk = ""

            if current_chunk:
                yield current_chunk

            # 读取错误输出
            stderr = process.stderr.read()
            if stderr:
                yield f"\n【错误】\n{stderr}"

            process.wait(timeout=timeout)

        except subprocess.TimeoutExpired:
            process.kill()
            yield f"\n执行超时（超过{timeout}秒）"
        except Exception as e:
            yield f"\n执行异常：{str(e)}"


# 工具信息定义
execute_python_code.tool_info = {
    "tool_name": "execute_python_code",
    "tool_title": "执行Python代码",
    "tool_description": "在隔离环境中安全执行Python代码，自动处理各种输入格式，支持依赖安装和输入数据传递",
    "tool_params": [
        {
            "name": "code",
            "description": "要执行的Python代码（可以是字符串、字典或列表，工具会自动解析）",
            "type": "string",
            "required": True
        },
        {
            "name": "timeout",
            "description": "执行超时时间（秒），默认30秒",
            "type": "integer",
            "required": False
        },
        {
            "name": "requirements",
            "description": "需要安装的依赖包列表，例如 ['requests', 'numpy==1.21.0']",
            "type": "array",
            "items": {"type": "string"},
            "required": False
        },
        {
            "name": "input_data",
            "description": "传递给代码的标准输入数据",
            "type": "string",
            "required": False
        }
    ]
}

execute_python_file.tool_info = {
    "tool_name": "execute_python_file",
    "tool_title": "执行Python文件",
    "tool_description": "在隔离环境中执行指定的Python文件，支持依赖安装和命令行参数",
    "tool_params": [
        {
            "name": "file_path",
            "description": "Python文件的路径",
            "type": "string",
            "required": True
        },
        {
            "name": "timeout",
            "description": "执行超时时间（秒），默认30秒",
            "type": "integer",
            "required": False
        },
        {
            "name": "requirements",
            "description": "需要安装的依赖包列表",
            "type": "array",
            "items": {"type": "string"},
            "required": False
        },
        {
            "name": "args",
            "description": "传递给脚本的命令行参数列表",
            "type": "array",
            "items": {"type": "string"},
            "required": False
        }
    ]
}

execute_python_code_stream.tool_info = {
    "tool_name": "execute_python_code_stream",
    "tool_title": "流式执行Python代码",
    "tool_description": "流式执行Python代码，逐步返回执行结果（用于长时间运行的任务）",
    "tool_params": [
        {
            "name": "code",
            "description": "要执行的Python代码",
            "type": "string",
            "required": True
        },
        {
            "name": "timeout",
            "description": "执行超时时间（秒），默认30秒",
            "type": "integer",
            "required": False
        },
        {
            "name": "requirements",
            "description": "需要安装的依赖包列表 示例：['openpyxl']",
            "type": "array",
            "items": {"type": "string"},
            "required": False
        }
    ]
}