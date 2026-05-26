import requests

def get_stock_kline(
    stock_code: str,
    scale: str = "240",
    ma: str = "no",
    datalen: str = "1023"
) -> str:
    """
    Get the historical K-line data for `stock_code`
    """
    if not isinstance(stock_code, str):
        raise TypeError("Stock code must be a string")

    try:
        resp = requests.get(f"http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={stock_code}&scale={scale}&ma={ma}&datalen={datalen}")
        resp.raise_for_status()
        return resp.text
    except:
        import traceback
        return "Error encountered while fetching stock K-line data!\n" + traceback.format_exc()

# Define tool information inside the function
get_stock_kline.tool_info = {
    "tool_name": "get_stock_kline",
    "tool_title": "股票K线图查询",
    "tool_description": "获取指定股票的历史K线图数据",
    "tool_params": [
        {"name": "stock_code", "description": "要查询的股票代码", "type": "string", "required": True},
        {"name": "scale", "description": "时间周期", "type": "string", "required": False},
        {"name": "ma", "description": "均线周期", "type": "string", "required": False},
        {"name": "datalen", "description": "数据长度", "type": "string", "required": False}
    ]
}