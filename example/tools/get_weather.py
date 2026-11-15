import httpx
def get_weather(
    city_name: str
) -> str:
    """
    Get the current weather for `city_name`
    """
    if not isinstance(city_name, str):
        raise TypeError("City name must be a string")

    key_selection = {
        "current_condition": ["temp_C", "FeelsLikeC", "humidity", "weatherDesc", "observation_time"],
    }
    try:
        resp = httpx.get(f"https://wttr.in/{city_name}?format=j1", timeout=10.0)
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
}
