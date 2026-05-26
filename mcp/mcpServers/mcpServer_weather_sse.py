#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MCP SSE Weather Service (FastMCP 实现版)

基于FastMCP框架的SSE天气服务，通过 @mcp.tool 装饰器声明可调用的天气服务工具函数。
服务通过SSE(Server-Sent Events)协议提供天气数据推送能力。

运行方式:
    python weather_server_sse.py

客户端连接:
1. 启动服务后，将打印的SSE endpoint添加到MCP客户端
2. 客户端示例代码：
   mcp-client add-endpoint http://localhost:8000/sse

开发说明:
1. 通过 FastMCP("WeatherServer") 创建服务实例
2. 使用 @mcp.tool 装饰器声明服务工具函数
3. 通过 mcp.run(transport="sse") 启动SSE服务

依赖安装:
    pip install fastmcp  # 根据实际MCP框架安装

特性:
• 声明式工具函数注册
• 自动SSE协议适配
• 类型标注的参数验证
• 启动时显示客户端接入指引

作者: [weego/WXAI-Team]
版本: 1.0.0
最后更新: 2025-03-31
"""
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("WeatherServer", port=8001)


@mcp.tool()
async def get_weather(location: str) -> str:
    """获取指定地区的天气信息"""
    async with httpx.AsyncClient() as client:

        if not isinstance(location, str):
            raise TypeError("City name must be a string")

        key_selection = {
            "current_condition": ["temp_C", "FeelsLikeC", "humidity", "weatherDesc", "observation_time"],
        }
        try:
            resp = await client.get(f"https://wttr.in/{location}?format=j1")
            resp.raise_for_status()
            resp = resp.json()
            ret = {k: {_v: resp[k][0][_v] for _v in v} for k, v in key_selection.items()}
        except:
            import traceback
            ret = "Error encountered while fetching weather data!\n" + traceback.format_exc()

        return str(ret)


def show_client_help(host: str, port: int):
    """显示客户端连接帮助信息"""
    print("\n" + "=" * 50)
    print(f"SSE服务已启动: http://{host}:{port}")
    print("请将以下url添加到MCP客户端sse配置中:")
    print(f"\033[1;32mhttp://{host}:{port}/sse\033[0m")  # 绿色高亮显示
    print("lightagent添加lightagent_mcp_settings.json配置示例：")
    print(
        f"\033[1;33m    \"example-sse\": {{\n      \"url\": \"http://{host}:{port}/sse\",\n      \"disabled\": false \n   }}\033[0m")  # 黄色高亮配置块
    print("=" * 50 + "\n")


if __name__ == "__main__":
    # 配置服务参数
    host = "0.0.0.0"  # 允许外部访问
    port = 8000  # 默认端口

    # 显示客户端连接指引
    show_client_help(host="localhost" if host == "0.0.0.0" else host, port=port)

    # 启动SSE服务（假设FastMCP支持host/port参数）
    mcp.run(
        transport="sse",
    )
