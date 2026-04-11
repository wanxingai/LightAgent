#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
财经分析工具包 - 基础使用示例
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from finance_toolkit import FinanceToolkit

def demo_basic_functions():
    """演示基础功能"""
    print("📈 财经分析工具包 - 基础使用示例")
    print("=" * 50)
    
    # 初始化工具包
    toolkit = FinanceToolkit(cache_enabled=True)
    
    # 1. 获取股票基本信息
    print("\n1. 获取股票基本信息:")
    print("-" * 30)
    
    stocks = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
    for symbol in stocks[:3]:  # 只演示前3个
        info = toolkit.get_stock_info(symbol)
        if info:
            print(f"\n{symbol} - {info['name']}:")
            print(f"  价格: ${info['current_price']:.2f}")
            print(f"  涨跌: {info['change_percent']:.2f}%")
            print(f"  市值: ${info['market_cap']:,.0f}")
            print(f"  市盈率: {info['pe_ratio']:.2f}")
    
    # 2. 分析单只股票
    print("\n\n2. 股票综合分析:")
    print("-" * 30)
    
    symbol = "AAPL"
    print(f"\n分析 {symbol}:")
    analysis = toolkit.analyze_stock(symbol, period="3mo")
    
    if analysis and 'error' not in analysis:
        basic = analysis['basic_info']
        price = analysis['price_analysis']
        technical = analysis['technical_analysis']
        risk = analysis['risk_analysis']
        recommendation = analysis['recommendation']
        
        print(f"  当前趋势: {technical['trend']}")
        print(f"  RSI状态: {technical['rsi_signal']} ({technical['rsi']:.2f})")
        print(f"  风险等级: {risk['risk_level']}")
        print(f"  操作建议: {recommendation['action']}")
        print(f"  信心指数: {recommendation['confidence']}/1.0")
    
    # 3. 比较多只股票
    print("\n\n3. 股票比较分析:")
    print("-" * 30)
    
    comparison = toolkit.compare_stocks(["AAPL", "MSFT", "GOOGL"], period="1mo")
    print("\n股票比较结果:")
    for symbol, data in comparison.items():
        print(f"\n{symbol}:")
        print(f"  价格: ${data['current_price']:.2f}")
        print(f"  涨跌: {data['change_percent']:.2f}%")
        print(f"  趋势: {data['trend']}")
        print(f"  风险: {data['risk_level']}")
        print(f"  建议: {data['recommendation']}")
        print(f"  信心: {data['confidence']}")
    
    # 4. 生成分析报告
    print("\n\n4. 生成分析报告:")
    print("-" * 30)
    
    report = toolkit.generate_report("MSFT", period="3mo", output_format="text")
    print(report[:300] + "..." if len(report) > 300 else report)
    
    # 5. 市场概览
    print("\n\n5. 全球市场概览:")
    print("-" * 30)
    
    market = toolkit.get_market_overview()
    print("\n主要市场指数:")
    for name, data in market.items():
        if 'error' not in data:
            change_icon = "📈" if data['change_percent'] >= 0 else "📉"
            print(f"  {name}: {data['price']:.2f} {change_icon} {data['change_percent']:.2f}%")

def demo_advanced_features():
    """演示高级功能"""
    print("\n\n🎯 高级功能演示")
    print("=" * 50)
    
    toolkit = FinanceToolkit()
    
    # 1. 获取历史数据
    print("\n1. 获取历史数据:")
    print("-" * 30)
    
    hist_data = toolkit.get_historical_data("AAPL", period="1mo", interval="1d")
    if not hist_data.empty:
        print(f"获取到 {len(hist_data)} 条历史数据")
        print("最新5条数据:")
        print(hist_data[['Close', 'Volume', 'MA20', 'RSI']].tail())
    
    # 2. 批量分析
    print("\n\n2. 批量分析投资组合:")
    print("-" * 30)
    
    portfolio = ["AAPL", "MSFT", "AMZN", "GOOGL", "META"]
    print(f"分析投资组合: {', '.join(portfolio)}")
    
    for symbol in portfolio[:3]:  # 只分析前3个
        analysis = toolkit.analyze_stock(symbol, period="1mo")
        if analysis and 'error' not in analysis:
            rec = analysis['recommendation']
            print(f"\n{symbol}: {rec['action']} (信心: {rec['confidence']})")

if __name__ == "__main__":
    demo_basic_functions()
    demo_advanced_features()
    
    print("\n" + "=" * 50)
    print("✅ 示例演示完成！")
    print("\n更多功能请参考:")
    print("1. 查看完整文档: README.md")
    print("2. 运行完整分析: python -m finance_toolkit")
    print("3. 自定义分析: 修改 examples/ 中的脚本")