import requests

def get_stock_kline_data(
    stock_code: str,
    scale: int,
    ma: str,
    datalen: int
) -> str:
    """
    Get the historical K-line stock data for `stock_code`
    """
    if not isinstance(stock_code, str):
        raise TypeError("Stock code must be a string")

    try:
        resp = requests.get(f"http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={stock_code}&scale={scale}&ma={ma}&datalen={datalen}")
        resp.raise_for_status()
        ret = resp.json()
    except:
        import traceback
        ret = "Error encountered while fetching stock K-line data!\n" + traceback.format_exc()

    return str(ret)

# 在函数内部定义工具信息
get_stock_kline_data.tool_info = {
    "tool_name": "get_stock_kline_data",
    "tool_description": "获取指定股票的历史K线图数据",
    "tool_params": [
        {"name": "stock_code", "description": "要查询的股票代码", "type": "string", "required": True},
        {"name": "scale", "description": "时间周期", "type": "int", "required": True},
        {"name": "ma", "description": "均线周期", "type": "string", "required": True},
        {"name": "datalen", "description": "数据长度", "type": "int", "required": True}
    ]
}