import requests

def get_stock_quote(
    stock_code: str
) -> str:
    """
    Get the current stock quote for `stock_code`
    """
    if not isinstance(stock_code, str):
        raise TypeError("Stock code must be a string")

    headers = {
        "Referer": "https://finance.sina.com.cn/"
    }
    try:
        resp = requests.get(f"http://hq.sinajs.cn/list={stock_code}", headers=headers)
        resp.raise_for_status()
        return resp.text
    except:
        import traceback
        return "Error encountered while fetching stock quote data!\n" + traceback.format_exc()

# Define tool information inside the function
get_stock_quote.tool_info = {
    "tool_name": "get_stock_quote",
    "tool_title": "股票行情查询",
    "tool_description": "获取指定股票的实时行情数据",
    "tool_params": [
        {"name": "stock_code", "description": "要查询的股票代码", "type": "string", "required": True},
    ]
}