---
name: 财经分析工具包
description: 专业的财经分析工具包，提供股票分析、市场趋势预测、投资建议等功能，帮助Agent进行财经决策和市场研究。
version: 1.0.0
icon: 📈
metadata:
  clawdbot:
    emoji: 📈
    requires:
      bins: ["python", "curl"]
    install:
      - id: python-deps
        kind: pip
        packages:
          - yfinance
          - pandas
          - numpy
          - matplotlib
        label: Install Python dependencies for financial analysis
---

# 财经分析工具包

专业的财经分析工具包，为AI Agent提供全面的财经分析能力。包含股票数据分析、市场趋势预测、投资组合优化等功能。

## 📊 功能模块

### 1. 股票数据分析
- 实时股票价格获取
- 历史数据查询与分析
- 技术指标计算（MA, RSI, MACD等）
- 基本面数据获取

### 2. 市场趋势分析
- 大盘指数监控
- 行业板块分析
- 市场情绪指标
- 宏观经济数据集成

### 3. 投资建议引擎
- 风险评估模型
- 投资组合优化
- 资产配置建议
- 止损止盈策略

### 4. 财经新闻聚合
- 实时财经新闻
- 热点事件分析
- 舆情监控
- 影响评估

## 🚀 快速开始

### 安装依赖
```bash
pip install yfinance pandas numpy matplotlib
```

### 基本使用示例
```python
from finance_toolkit import StockAnalyzer

# 创建分析器
analyzer = StockAnalyzer()

# 获取股票数据
data = analyzer.get_stock_data("AAPL", period="1mo")

# 技术分析
analysis = analyzer.technical_analysis(data)
print(analysis)
```

## 📁 文件结构
```
finance-toolkit/
├── SKILL.md              # 技能说明文档
├── README.md             # 用户文档
├── finance_toolkit.py    # 核心Python模块
├── stock_analyzer.py     # 股票分析模块
├── market_trends.py      # 市场趋势模块
├── investment_advisor.py # 投资建议模块
├── news_aggregator.py    # 新闻聚合模块
└── examples/             # 使用示例
```

## 🔧 工具函数

### 股票分析工具
- `get_stock_price(symbol)` - 获取实时股价
- `get_historical_data(symbol, period)` - 获取历史数据
- `calculate_technical_indicators(data)` - 计算技术指标
- `analyze_fundamentals(symbol)` - 分析基本面

### 市场分析工具
- `get_market_indices()` - 获取大盘指数
- `analyze_sector_performance()` - 分析行业表现
- `get_market_sentiment()` - 获取市场情绪
- `predict_market_trend()` - 预测市场趋势

### 投资建议工具
- `assess_risk_profile()` - 评估风险偏好
- `optimize_portfolio(assets)` - 优化投资组合
- `generate_investment_advice()` - 生成投资建议
- `set_stop_loss_targets()` - 设置止损止盈

## 📈 数据源
- Yahoo Finance (yfinance)
- 公开市场数据API
- 财经新闻API
- 宏观经济数据库

## ⚠️ 免责声明
本工具包提供的分析结果仅供参考，不构成投资建议。投资有风险，决策需谨慎。

## 🔗 相关资源
- [Yahoo Finance API](https://pypi.org/project/yfinance/)
- [Pandas数据分析](https://pandas.pydata.org/)
- [财经数据源列表](https://github.com/awesomedata/awesome-public-datasets#finance)

## 📝 更新日志
- v1.0.0 (2026-02-20): 初始版本发布，包含基础股票分析和市场趋势功能