import requests

def get_stock_realtime_data(
    stock_code: str
) -> str:
    """
    Get the real-time stock data for `stock_code`
    """
    if not isinstance(stock_code, str):
        raise TypeError("Stock code must be a string")

    headers = {
        "Referer": "https://finance.sina.com.cn/"
    }
    try:
        resp = requests.get(f"http://hq.sinajs.cn/list={stock_code}", headers=headers)
        resp.raise_for_status()
        ret = resp.text
    except:
        import traceback
        ret = "Error encountered while fetching stock data!\n" + traceback.format_exc()

    return str(ret)

# 在函数内部定义工具信息
get_stock_realtime_data.tool_info = {
    "tool_name": "get_stock_realtime_data",
    "tool_description": "获取指定股票的实时行情数据",
    "tool_params": [
        {"name": "stock_code", "description": "要查询的股票代码", "type": "string", "required": True},
    ]
}