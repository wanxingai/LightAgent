#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
财经分析工具包 - 核心模块
提供股票分析、市场趋势、投资建议等功能
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class FinanceToolkit:
    """财经分析工具包核心类"""
    
    def __init__(self, cache_enabled=True):
        """
        初始化财经工具包
        
        Args:
            cache_enabled (bool): 是否启用缓存
        """
        self.cache_enabled = cache_enabled
        self.cache = {}
        print("📈 财经分析工具包已初始化")
    
    def get_stock_info(self, symbol):
        """
        获取股票基本信息
        
        Args:
            symbol (str): 股票代码（如：AAPL, 000001.SZ）
            
        Returns:
            dict: 股票信息字典
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            stock_info = {
                'symbol': symbol,
                'name': info.get('longName', 'N/A'),
                'current_price': info.get('currentPrice', info.get('regularMarketPrice', 0)),
                'previous_close': info.get('previousClose', 0),
                'change': info.get('currentPrice', 0) - info.get('previousClose', 0),
                'change_percent': ((info.get('currentPrice', 0) - info.get('previousClose', 0)) / info.get('previousClose', 0) * 100) if info.get('previousClose', 0) != 0 else 0,
                'market_cap': info.get('marketCap', 0),
                'volume': info.get('volume', 0),
                'avg_volume': info.get('averageVolume', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'dividend_yield': info.get('dividendYield', 0),
                'currency': info.get('currency', 'USD'),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return stock_info
            
        except Exception as e:
            print(f"❌ 获取股票信息失败: {e}")
            return None
    
    def get_historical_data(self, symbol, period="1mo", interval="1d"):
        """
        获取历史价格数据
        
        Args:
            symbol (str): 股票代码
            period (str): 时间周期（1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max）
            interval (str): 数据间隔（1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo）
            
        Returns:
            pandas.DataFrame: 历史价格数据
        """
        cache_key = f"{symbol}_{period}_{interval}"
        
        if self.cache_enabled and cache_key in self.cache:
            print(f"📂 从缓存加载数据: {cache_key}")
            return self.cache[cache_key]
        
        try:
            print(f"📥 下载数据: {symbol} ({period})")
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval=interval)
            
            if hist.empty:
                print(f"⚠️ 未找到{symbol}的历史数据")
                return pd.DataFrame()
            
            # 添加技术指标
            hist = self._add_technical_indicators(hist)
            
            if self.cache_enabled:
                self.cache[cache_key] = hist
            
            return hist
            
        except Exception as e:
            print(f"❌ 获取历史数据失败: {e}")
            return pd.DataFrame()
    
    def _add_technical_indicators(self, df):
        """添加技术指标到数据框"""
        if df.empty:
            return df
        
        # 移动平均线
        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA60'] = df['Close'].rolling(window=60).mean()
        
        # RSI (相对强弱指数)
        df['RSI'] = self._calculate_rsi(df['Close'])
        
        # MACD
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['Histogram'] = df['MACD'] - df['Signal']
        
        # 布林带
        df['BB_Middle'] = df['Close'].rolling(window=20).mean()
        bb_std = df['Close'].rolling(window=20).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        
        return df
    
    def _calculate_rsi(self, prices, period=14):
        """计算RSI指标"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def analyze_stock(self, symbol, period="3mo"):
        """
        综合分析股票
        
        Args:
            symbol (str): 股票代码
            period (str): 分析周期
            
        Returns:
            dict: 分析结果
        """
        print(f"🔍 正在分析股票: {symbol}")
        
        # 获取基本信息
        info = self.get_stock_info(symbol)
        if not info:
            return {"error": "无法获取股票信息"}
        
        # 获取历史数据
        hist = self.get_historical_data(symbol, period=period)
        if hist.empty:
            return {"error": "无法获取历史数据"}
        
        # 计算分析指标
        analysis = {
            'basic_info': info,
            'price_analysis': self._analyze_price(hist),
            'technical_analysis': self._analyze_technical(hist),
            'risk_analysis': self._analyze_risk(hist),
            'recommendation': self._generate_recommendation(hist, info)
        }
        
        return analysis
    
    def _analyze_price(self, df):
        """价格分析"""
        if df.empty:
            return {}
        
        latest = df.iloc[-1]
        prev_close = df.iloc[-2]['Close'] if len(df) > 1 else latest['Close']
        
        return {
            'current_price': latest['Close'],
            'price_change': latest['Close'] - prev_close,
            'price_change_percent': ((latest['Close'] - prev_close) / prev_close * 100) if prev_close != 0 else 0,
            'high_52w': df['High'].max(),
            'low_52w': df['Low'].min(),
            'current_vs_high': (latest['Close'] / df['High'].max() * 100) if df['High'].max() != 0 else 0,
            'current_vs_low': (latest['Close'] / df['Low'].min() * 100) if df['Low'].min() != 0 else 0,
            'volume_trend': '上升' if latest['Volume'] > df['Volume'].mean() else '下降'
        }
    
    def _analyze_technical(self, df):
        """技术分析"""
        if df.empty or len(df) < 20:
            return {}
        
        latest = df.iloc[-1]
        
        # 趋势判断
        trend = "震荡"
        if latest['Close'] > latest['MA20'] > latest['MA60']:
            trend = "强势上涨"
        elif latest['Close'] < latest['MA20'] < latest['MA60']:
            trend = "弱势下跌"
        elif latest['Close'] > latest['MA20']:
            trend = "短期上涨"
        elif latest['Close'] < latest['MA20']:
            trend = "短期下跌"
        
        # RSI信号
        rsi_signal = "中性"
        if latest['RSI'] > 70:
            rsi_signal = "超买"
        elif latest['RSI'] < 30:
            rsi_signal = "超卖"
        
        # MACD信号
        macd_signal = "中性"
        if latest['MACD'] > latest['Signal'] and latest['Histogram'] > 0:
            macd_signal = "金叉买入"
        elif latest['MACD'] < latest['Signal'] and latest['Histogram'] < 0:
            macd_signal = "死叉卖出"
        
        # 布林带信号
        bb_signal = "中性"
        if latest['Close'] > latest['BB_Upper']:
            bb_signal = "突破上轨"
        elif latest['Close'] < latest['BB_Lower']:
            bb_signal = "突破下轨"
        
        return {
            'trend': trend,
            'rsi': latest['RSI'],
            'rsi_signal': rsi_signal,
            'macd_signal': macd_signal,
            'bb_signal': bb_signal,
            'ma_position': {
                'above_ma5': latest['Close'] > latest['MA5'],
                'above_ma20': latest['Close'] > latest['MA20'],
                'above_ma60': latest['Close'] > latest['MA60']
            }
        }
    
    def _analyze_risk(self, df):
        """风险分析"""
        if df.empty or len(df) < 20:
            return {}
        
        # 计算波动率
        returns = df['Close'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(252)  # 年化波动率
        
        # 最大回撤
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # 夏普比率（假设无风险利率3%）
        risk_free_rate = 0.03
        excess_returns = returns.mean() * 252 - risk_free_rate
        sharpe_ratio = excess_returns / volatility if volatility != 0 else 0
        
        return {
            'annual_volatility': volatility,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'risk_level': self._assess_risk_level(volatility, max_drawdown)
        }
    
    def _assess_risk_level(self, volatility, max_drawdown):
        """评估风险等级"""
        if volatility < 0.2 and max_drawdown > -0.1:
            return "低风险"
        elif volatility < 0.35 and max_drawdown > -0.2:
            return "中风险"
        else:
            return "高风险"
    
    def _generate_recommendation(self, df, info):
        """生成投资建议"""
        if df.empty:
            return "数据不足，无法提供建议"
        
        latest = df.iloc[-1]
        price_analysis = self._analyze_price(df)
        technical = self._analyze_technical(df)
        risk = self._analyze_risk(df)
        
        recommendations = []
        
        # 基于价格分析
        if price_analysis.get('price_change_percent', 0) > 5:
            recommendations.append("近期涨幅较大，注意回调风险")
        elif price_analysis.get('price_change_percent', 0) < -5:
            recommendations.append("近期跌幅较大，关注超跌反弹机会")
        
        # 基于技术分析
        if technical.get('rsi_signal') == "超买":
            recommendations.append("RSI显示超买，建议谨慎追高")
        elif technical.get('rsi_signal') == "超卖":
            recommendations.append("RSI显示超卖，可能具备反弹机会")
        
        if technical.get('macd_signal') == "金叉买入":
            recommendations.append("MACD金叉，技术面偏多")
        elif technical.get('macd_signal') == "死叉卖出":
            recommendations.append("MACD死叉，技术面偏空")
        
        # 基于风险分析
        if risk.get('risk_level') == "高风险":
            recommendations.append("波动率较高，适合风险承受能力强的投资者")
        elif risk.get('risk_level') == "低风险":
            recommendations.append("波动率较低，适合稳健型投资者")
        
        # 基于基本面
        if info.get('pe_ratio', 0) > 0:
            if info['pe_ratio'] > 50:
                recommendations.append("估值较高，注意估值回归风险")
            elif info['pe_ratio'] < 15:
                recommendations.append("估值较低，具备安全边际")
        
        if info.get('dividend_yield', 0) > 0.03:
            recommendations.append("股息率较高，适合价值投资者")
        
        if not recommendations:
            recommendations.append("当前无明显买卖信号，建议观望")
        
        return {
            'action': self._determine_action(technical, risk),
            'confidence': self._calculate_confidence(df),
            'details': recommendations,
            'time_horizon': self._suggest_time_horizon(technical, risk)
        }
    
    def _determine_action(self, technical, risk):
        """确定操作建议"""
        score = 0
        
        # 技术面评分
        if technical.get('trend') == "强势上涨":
            score += 2
        elif technical.get('trend') == "弱势下跌":
            score -= 2
        
        if technical.get('rsi_signal') == "超卖":
            score += 1
        elif technical.get('rsi_signal') == "超买":
            score -= 1
        
        if technical.get('macd_signal') == "金叉买入":
            score += 1
        elif technical.get('macd_signal') == "死叉卖出":
            score -= 1
        
        # 风险面评分
        if risk.get('risk_level') == "低风险":
            score += 1
        elif risk.get('risk_level') == "高风险":
            score -= 1
        
        if score >= 2:
            return "买入"
        elif score <= -2:
            return "卖出"
        else:
            return "持有/观望"
    
    def _calculate_confidence(self, df):
        """计算信心指数"""
        if df.empty or len(df) < 20:
            return 0.5
        
        # 基于数据完整性和一致性
        data_quality = min(1.0, len(df) / 100)  # 数据量
        
        # 基于价格趋势一致性
        price_trend = abs(df['Close'].pct_change().mean() * 100)
        trend_consistency = 1.0 - min(1.0, price_trend / 50)  # 波动越小，信心越高
        
        confidence = (data_quality * 0.4 + trend_consistency * 0.6)
        return round(confidence, 2)
    
    def _suggest_time_horizon(self, technical, risk):
        """建议投资期限"""
        if risk.get('risk_level') == "高风险":
            return "短期（1-3个月）"
        elif technical.get('trend') in ["强势上涨", "弱势下跌"]:
            return "中期（3-12个月）"
        else:
            return "长期（1年以上）"
    
    def compare_stocks(self, symbols, period="3mo"):
        """
        比较多只股票
        
        Args:
            symbols (list): 股票代码列表
            period (str): 分析周期
            
        Returns:
            dict: 比较分析结果
        """
        print(f"📊 比较分析: {', '.join(symbols)}")
        
        comparison = {}
        for symbol in symbols:
            analysis = self.analyze_stock(symbol, period)
            if analysis and 'error' not in analysis:
                comparison[symbol] = {
                    'current_price': analysis['basic_info'].get('current_price', 0),
                    'change_percent': analysis['price_analysis'].get('price_change_percent', 0),
                    'trend': analysis['technical_analysis'].get('trend', '未知'),
                    'risk_level': analysis['risk_analysis'].get('risk_level', '未知'),
                    'recommendation': analysis['recommendation'].get('action', '未知'),
                    'confidence': analysis['recommendation'].get('confidence', 0.5)
                }
        
        # 排序：按推荐程度
        sorted_comparison = dict(sorted(
            comparison.items(),
            key=lambda x: (
                1 if x[1]['recommendation'] == '买入' else
                2 if x[1]['recommendation'] == '持有/观望' else 3,
                -x[1]['confidence']
            )
        ))
        
        return sorted_comparison
    
    def get_market_overview(self):
        """获取市场概览"""
        print("🌐 获取市场概览...")
        
        # 主要市场指数
        indices = {
            '^GSPC': '标普500',
            '^IXIC': '纳斯达克',
            '^DJI': '道琼斯',
            '000001.SS': '上证指数',
            '399001.SZ': '深证成指',
            '^HSI': '恒生指数',
            '^N225': '日经225',
            '^FTSE': '富时100'
        }
        
        market_data = {}
        for symbol, name in indices.items():
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                
                market_data[name] = {
                    'symbol': symbol,
                    'price': info.get('currentPrice', info.get('regularMarketPrice', 0)),
                    'change': info.get('currentPrice', 0) - info.get('previousClose', 0),
                    'change_percent': ((info.get('currentPrice', 0) - info.get('previousClose', 0)) / info.get('previousClose', 0) * 100) if info.get('previousClose', 0) != 0 else 0,
                    'status': '上涨' if info.get('currentPrice', 0) > info.get('previousClose', 0) else '下跌'
                }
            except Exception as e:
                print(f"⚠️ 获取{name}数据失败: {e}")
                market_data[name] = {'error': '获取失败'}
        
        return market_data
    
    def generate_report(self, symbol, period="3mo", output_format="text"):
        """
        生成分析报告
        
        Args:
            symbol (str): 股票代码
            period (str): 分析周期
            output_format (str): 输出格式（text, markdown, json）
            
        Returns:
            str/dict: 分析报告
        """
        print(f"📄 生成分析报告: {symbol}")
        
        analysis = self.analyze_stock(symbol, period)
        if 'error' in analysis:
            return f"❌ 分析失败: {analysis['error']}"
        
        basic = analysis['basic_info']
        price = analysis['price_analysis']
        technical = analysis['technical_analysis']
        risk = analysis['risk_analysis']
        recommendation = analysis['recommendation']
        
        if output_format == "json":
            return analysis
        
        elif output_format == "markdown":
            report = f"""# {basic.get('name', 'N/A')} ({symbol}) 分析报告

## 📊 基本信息
- **当前价格**: ${basic.get('current_price', 0):.2f} {basic.get('currency', 'USD')}
- **涨跌幅**: {price.get('price_change_percent', 0):.2f}%
- **市值**: ${basic.get('market_cap', 0):,.0f}
- **市盈率**: {basic.get('pe_ratio', 0):.2f}
- **股息率**: {basic.get('dividend_yield', 0):.2%}
- **行业**: {basic.get('industry', 'N/A')}

## 📈 技术分析
- **趋势**: {technical.get('trend', '未知')}
- **RSI**: {technical.get('rsi', 0):.2f} ({technical.get('rsi_signal', '中性')})
- **MACD信号**: {technical.get('macd_signal', '中性')}
- **布林带信号**: {technical.get('bb_signal', '中性')}

## ⚠️ 风险分析
- **风险等级**: {risk.get('risk_level', '未知')}
- **年化波动率**: {risk.get('annual_volatility', 0):.2%}
- **最大回撤**: {risk.get('max_drawdown', 0):.2%}
- **夏普比率**: {risk.get('sharpe_ratio', 0):.2f}

## 🎯 投资建议
- **操作建议**: **{recommendation.get('action', '未知')}**
- **信心指数**: {recommendation.get('confidence', 0):.2f}/1.0
- **投资期限**: {recommendation.get('time_horizon', '未知')}
- **详细建议**:
"""
            
            for detail in recommendation.get('details', []):
                report += f"  - {detail}\n"
            
            report += f"\n---\n*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
            return report
        
        else:  # text格式
            report = f"""
{'='*60}
{basic.get('name', 'N/A')} ({symbol}) 分析报告
{'='*60}

📊 基本信息：
  当前价格: ${basic.get('current_price', 0):.2f} {basic.get('currency', 'USD')}
  涨跌幅: {price.get('price_change_percent', 0):.2f}%
  市值: ${basic.get('market_cap', 0):,.0f}
  市盈率: {basic.get('pe_ratio', 0):.2f}
  股息率: {basic.get('dividend_yield', 0):.2%}
  行业: {basic.get('industry', 'N/A')}

📈 技术分析：
  趋势: {technical.get('trend', '未知')}
  RSI: {technical.get('rsi', 0):.2f} ({technical.get('rsi_signal', '中性')})
  MACD信号: {technical.get('macd_signal', '中性')}
  布林带信号: {technical.get('bb_signal', '中性')}

⚠️ 风险分析：
  风险等级: {risk.get('risk_level', '未知')}
  年化波动率: {risk.get('annual_volatility', 0):.2%}
  最大回撤: {risk.get('max_drawdown', 0):.2%}
  夏普比率: {risk.get('sharpe_ratio', 0):.2f}

🎯 投资建议：
  操作建议: 【{recommendation.get('action', '未知')}】
  信心指数: {recommendation.get('confidence', 0):.2f}/1.0
  投资期限: {recommendation.get('time_horizon', '未知')}

  详细建议：
"""
            
            for detail in recommendation.get('details', []):
                report += f"    • {detail}\n"
            
            report += f"\n{'='*60}\n报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{'='*60}"
            return report


# 使用示例
if __name__ == "__main__":
    print("🎯 财经分析工具包演示")
    print("-" * 40)
    
    # 初始化工具包
    toolkit = FinanceToolkit()
    
    # 示例1: 获取股票信息
    print("\n1. 获取苹果公司(AAPL)信息:")
    aapl_info = toolkit.get_stock_info("AAPL")
    if aapl_info:
        print(f"   名称: {aapl_info['name']}")
        print(f"   价格: ${aapl_info['current_price']:.2f}")
        print(f"   涨跌: {aapl_info['change_percent']:.2f}%")
        print(f"   市值: ${aapl_info['market_cap']:,.0f}")
    
    # 示例2: 分析股票
    print("\n2. 分析特斯拉(TSLA):")
    tsla_analysis = toolkit.analyze_stock("TSLA", period="1mo")
    if tsla_analysis and 'error' not in tsla_analysis:
        rec = tsla_analysis['recommendation']
        print(f"   建议: {rec['action']}")
        print(f"   信心: {rec['confidence']}/1.0")
        print(f"   期限: {rec['time_horizon']}")
    
    # 示例3: 生成报告
    print("\n3. 生成微软(MSFT)分析报告:")
    report = toolkit.generate_report("MSFT", period="3mo", output_format="text")
    print(report[:500] + "..." if len(report) > 500 else report)
    
    # 示例4: 市场概览
    print("\n4. 市场概览:")
    market = toolkit.get_market_overview()
    for name, data in list(market.items())[:3]:  # 只显示前3个
        if 'error' not in data:
            print(f"   {name}: {data['price']:.2f} ({data['change_percent']:.2f}%)")
    
    print("\n✅ 演示完成！")