# 财经分析工具包

一个专业的财经分析工具包，为AI Agent提供全面的财经分析能力。

## 🌟 特性

### 核心功能
- **实时股票数据**：获取全球股票实时价格和历史数据
- **技术分析**：支持多种技术指标计算和分析
- **基本面分析**：公司财务数据、估值指标等
- **市场趋势**：大盘指数、行业板块分析
- **投资建议**：风险评估、投资组合优化

### 高级功能
- **多市场支持**：A股、港股、美股等
- **数据可视化**：生成K线图、趋势图等
- **新闻聚合**：实时财经新闻和舆情分析
- **预警系统**：价格预警、技术指标预警

## 🛠️ 安装

### 前置要求
- Python 3.8+
- pip包管理器

### 安装步骤
```bash
# 克隆或下载本工具包
git clone https://github.com/yourusername/finance-toolkit.git
cd finance-toolkit

# 安装依赖
pip install -r requirements.txt
```

### 依赖包
```txt
yfinance>=0.2.28
pandas>=2.0.0
numpy>=1.24.0
matplotlib>=3.7.0
requests>=2.31.0
```

## 📖 使用指南

### 基础使用
```python
from finance_toolkit import FinanceToolkit

# 初始化工具包
toolkit = FinanceToolkit()

# 获取股票信息
stock_info = toolkit.get_stock_info("AAPL")
print(f"苹果公司当前股价: ${stock_info['price']}")

# 获取历史数据
history = toolkit.get_history("AAPL", period="1y")
```

### 技术分析示例
```python
# 计算技术指标
from finance_toolkit.technical import TechnicalAnalyzer

analyzer = TechnicalAnalyzer()
data = analyzer.get_data("TSLA", period="6mo")

# 计算移动平均线
ma_data = analyzer.calculate_ma(data, windows=[20, 50, 200])

# 计算RSI
rsi = analyzer.calculate_rsi(data)

# 生成分析报告
report = analyzer.generate_report(data)
```

### 投资组合分析
```python
from finance_toolkit.portfolio import PortfolioManager

# 创建投资组合
portfolio = PortfolioManager()
portfolio.add_asset("AAPL", weight=0.3)
portfolio.add_asset("MSFT", weight=0.3)
portfolio.add_asset("GOOGL", weight=0.4)

# 分析组合表现
performance = portfolio.analyze_performance(period="1y")
risk_metrics = portfolio.calculate_risk_metrics()

print(f"年化收益率: {performance['annual_return']:.2%}")
print(f"夏普比率: {risk_metrics['sharpe_ratio']:.2f}")
```

## 🔍 功能详解

### 1. 股票数据模块
- **实时报价**：获取最新股价、涨跌幅、成交量等
- **历史数据**：日线、周线、月线数据
- **公司信息**：基本面数据、财务报告
- **分红信息**：股息率、分红历史

### 2. 技术分析模块
- **趋势指标**：移动平均线、布林带、MACD
- **动量指标**：RSI、随机指标、威廉指标
- **成交量指标**：OBV、成交量加权平均价
- **波动率指标**：ATR、波动率通道

### 3. 基本面分析模块
- **财务比率**：PE、PB、ROE、ROA等
- **财务报表**：利润表、资产负债表、现金流量表
- **估值模型**：DCF模型、相对估值法
- **行业对比**：同行业公司比较分析

### 4. 市场分析模块
- **大盘指数**：上证指数、深证成指、纳斯达克等
- **行业板块**：行业轮动、板块热度
- **市场情绪**：恐慌贪婪指数、投资者情绪
- **宏观经济**：GDP、CPI、利率等数据

## 📊 数据可视化

工具包内置数据可视化功能：

```python
from finance_toolkit.visualization import ChartGenerator

# 创建K线图
chart = ChartGenerator()
chart.plot_candlestick("AAPL", period="1mo")

# 创建技术指标图
chart.plot_technical("MSFT", indicators=["MA20", "MA50", "RSI"])

# 创建投资组合收益图
chart.plot_portfolio_performance(portfolio)
```

## ⚙️ 配置选项

可以通过配置文件自定义工具包行为：

```python
# config.yaml
data_source:
  primary: "yfinance"
  fallback: "alpha_vantage"
  
cache:
  enabled: true
  ttl: 3600  # 缓存时间（秒）
  
api_keys:
  alpha_vantage: "your_api_key"
  finnhub: "your_api_key"
```

## 🚨 预警系统

设置价格和技术指标预警：

```python
from finance_toolkit.alerts import AlertSystem

alerts = AlertSystem()

# 价格预警
alerts.add_price_alert("AAPL", target_price=180, direction="above")

# 技术指标预警
alerts.add_technical_alert("TSLA", indicator="RSI", condition="<", value=30)

# 启动监控
alerts.start_monitoring()
```

## 📈 实战案例

### 案例1：选股策略
```python
from finance_toolkit.strategies import ValueInvestingStrategy

strategy = ValueInvestingStrategy()
candidates = strategy.screen_stocks(
    min_market_cap=10e9,  # 最小市值100亿
    max_pe_ratio=20,      # 最高PE20倍
    min_roe=0.15,         # 最低ROE15%
    dividend_yield=0.02   # 股息率2%以上
)

print(f"找到{len(candidates)}只符合价值的股票")
```

### 案例2：趋势跟踪
```python
from finance_toolkit.strategies import TrendFollowingStrategy

strategy = TrendFollowingStrategy()
signals = strategy.generate_signals("QQQ", period="3mo")

for signal in signals:
    print(f"日期: {signal['date']}, 信号: {signal['action']}, 价格: ${signal['price']}")
```

## 🔒 安全与隐私

- 所有API调用使用HTTPS加密
- 本地缓存数据，减少API调用
- 支持API密钥加密存储
- 不存储用户交易记录

## 📄 许可证

MIT License

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 📞 支持与反馈

如有问题或建议，请：
1. 查看[常见问题解答](FAQ.md)
2. 提交[Issue](https://github.com/yourusername/finance-toolkit/issues)
3. 发送邮件至 support@example.com

## 🎯 路线图

- [ ] 添加更多数据源（东方财富、新浪财经等）
- [ ] 支持期货、外汇、加密货币
- [ ] 集成机器学习预测模型
- [ ] 开发Web界面
- [ ] 添加回测框架
- [ ] 支持实时数据流

---

**免责声明**：本工具包仅供学习和研究使用，不构成投资建议。投资有风险，入市需谨慎。