#!/usr/bin/env python3
"""
分析工具演示脚本

展示如何使用分析工具进行技术分析、支撑阻力分析、模式识别和多时间框架分析
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tools.analysis.technical import TechnicalAnalyzer
from tools.analysis.support_resistance import SupportResistanceAnalyzer
from tools.analysis.patterns import PatternRecognizer
from tools.analysis.multi_timeframe import MultiTimeframeAnalyzer

def create_sample_data(n=200, trend="up", volatility=1.0, pattern=None):
    """
    创建示例数据
    
    参数:
        n: 数据点数
        trend: 趋势类型 ("up", "down", "sideways")
        volatility: 波动率系数
        pattern: 模式类型 ("head_shoulders", "double_top", "triangle")
    """
    base_time = datetime(2024, 1, 1)
    
    # 基础趋势
    if trend == "up":
        base_prices = [70000 + i*10 for i in range(n)]
    elif trend == "down":
        base_prices = [80000 - i*10 for i in range(n)]
    else:  # sideways
        base_prices = [75000 for _ in range(n)]
    
    # 添加模式
    prices = []
    if pattern == "head_shoulders":
        # 头肩顶模式
        for i in range(n):
            if i < 30:
                price = 75000 + i*5  # 左肩
            elif i < 60:
                price = 78000 + (i-30)*3  # 头部
            elif i < 90:
                price = 75000 + (90-i)*5  # 右肩
            else:
                price = 74000 - (i-90)*10  # 突破下跌
            prices.append(price + np.random.randn() * 100 * volatility)
    
    elif pattern == "double_top":
        # 双顶模式
        for i in range(n):
            if i < 50:
                price = 73000 + i*8  # 第一个顶部
            elif i < 100:
                price = 77000 - (i-50)*8  # 回调
            elif i < 150:
                price = 73000 + (i-100)*8  # 第二个顶部
            else:
                price = 77000 - (i-150)*10  # 突破下跌
            prices.append(price + np.random.randn() * 100 * volatility)
    
    elif pattern == "triangle":
        # 三角形模式
        for i in range(n):
            if i < n/2:
                # 收敛三角形
                high = 78000 - i*5
                low = 72000 + i*5
                price = (high + low) / 2
            else:
                # 突破
                price = 80000 + (i-n/2)*8
            prices.append(price + np.random.randn() * 100 * volatility)
    
    else:
        # 随机波动
        for base in base_prices:
            price = base + np.random.randn() * 100 * volatility
            prices.append(price)
    
    # 创建DataFrame
    df = pd.DataFrame({
        'timestamp': [base_time + timedelta(hours=i) for i in range(n)],
        'open': [p - 50 + np.random.randn() * 20 for p in prices],
        'high': [p + 100 + np.random.randn() * 30 for p in prices],
        'low': [p - 100 + np.random.randn() * 30 for p in prices],
        'close': prices,
        'volume': [1000 + np.random.randn() * 200 for _ in range(n)]
    })
    
    return df

def demo_technical_analysis():
    """演示技术分析"""
    print("=" * 70)
    print("📊 演示: 技术分析工具")
    print("=" * 70)
    
    # 创建测试数据
    df = create_sample_data(n=200, trend="up", volatility=1.5)
    print(f"📈 测试数据: {df.shape[0]} 行 × {df.shape[1]} 列")
    print(f"💰 价格范围: ${df['close'].min():,.0f} - ${df['close'].max():,.0f}")
    print(f"📅 时间范围: {df['timestamp'].iloc[0]} 到 {df['timestamp'].iloc[-1]}")
    print()
    
    # 创建技术分析器
    analyzer = TechnicalAnalyzer()
    
    # 执行分析
    print("🔍 执行技术分析...")
    report = analyzer.analyze(df, "BTCUSDT", "4h")
    
    # 打印报告
    report.print_summary()
    
    # 显示详细分析
    print("\n📋 详细分析结果:")
    
    # 趋势分析
    trend = report.trend_analysis
    print(f"📈 趋势分析:")
    print(f"  方向: {trend.direction.value}")
    print(f"  强度: {trend.strength:.1%}")
    print(f"  阶段: {trend.phase.value}")
    print(f"  MACD信号: {trend.macd_signal}")
    print(f"  均线排列: {trend.ema_alignment.get('alignment', 'unknown')}")
    
    # 动量分析
    momentum = report.momentum_analysis
    print(f"\n⚡ 动量分析:")
    print(f"  RSI: {momentum.rsi_value:.1f} ({momentum.rsi_signal})")
    print(f"  随机指标: K={momentum.stochastic_k:.1f}, D={momentum.stochastic_d:.1f}")
    print(f"  CCI: {momentum.cci_value:.1f} ({momentum.cci_signal})")
    print(f"  动量值: {momentum.momentum_value:.2f}")
    
    # 波动率分析
    volatility = report.volatility_analysis
    print(f"\n📊 波动率分析:")
    print(f"  ATR: {volatility.atr_value:.2f} ({volatility.atr_percent:.1%})")
    print(f"  布林带宽度: {volatility.bollinger_width:.2f}")
    print(f"  布林带位置: {volatility.bollinger_position}")
    print(f"  波动率状态: {volatility.volatility_regime}")
    
    # 成交量分析
    volume = report.volume_analysis
    print(f"\n📈 成交量分析:")
    print(f"  成交量趋势: {volume.volume_trend}")
    print(f"  量比: {volume.volume_ma_ratio:.2f}")
    print(f"  OBV趋势: {volume.obv_trend}")
    print(f"  量价确认: {'✅' if volume.volume_confirmation else '❌'}")
    
    return report

def demo_support_resistance_analysis():
    """演示支撑阻力分析"""
    print("\n" + "=" * 70)
    print("🎯 演示: 支撑阻力分析工具")
    print("=" * 70)
    
    # 创建有明显支撑阻力位的测试数据
    df = create_sample_data(n=300, trend="up", volatility=2.0)
    
    # 手动添加一些明显的支撑阻力位
    df.loc[50, 'high'] = 78000  # 阻力位1
    df.loc[100, 'low'] = 72000  # 支撑位1
    df.loc[150, 'high'] = 80000  # 阻力位2
    df.loc[200, 'low'] = 74000  # 支撑位2
    
    print(f"📊 测试数据: {df.shape[0]} 行 × {df.shape[1]} 列")
    print(f"💰 当前价格: ${df['close'].iloc[-1]:,.2f}")
    print()
    
    # 创建支撑阻力分析器
    analyzer = SupportResistanceAnalyzer()
    
    # 执行分析
    print("🔍 执行支撑阻力分析...")
    report = analyzer.analyze(df, "BTCUSDT", "4h")
    
    # 打印报告
    report.print_summary()
    
    # 显示详细支撑阻力位
    print("\n📋 详细支撑阻力位:")
    
    # 支撑位
    if report.support_levels:
        print(f"📉 支撑位 ({len(report.support_levels)} 个):")
        for i, level in enumerate(report.support_levels[:5], 1):
            distance = (report.current_price - level.price) / report.current_price * 100
            print(f"  {i}. ${level.price:,.2f} ({distance:+.1f}% 下方)")
            print(f"     强度: {level.strength.value}")
            print(f"     置信度: {level.confidence:.1%}")
            print(f"     类型: {level.level_type.value}")
            if level.reasons:
                print(f"     原因: {level.reasons[0]}")
            print()
    
    # 阻力位
    if report.resistance_levels:
        print(f"📈 阻力位 ({len(report.resistance_levels)} 个):")
        for i, level in enumerate(report.resistance_levels[:5], 1):
            distance = (level.price - report.current_price) / report.current_price * 100
            print(f"  {i}. ${level.price:,.2f} ({distance:+.1f}% 上方)")
            print(f"     强度: {level.strength.value}")
            print(f"     置信度: {level.confidence:.1%}")
            print(f"     类型: {level.level_type.value}")
            if level.reasons:
                print(f"     原因: {level.reasons[0]}")
            print()
    
    # 突破分析
    if report.breakout_analysis:
        breakout = report.breakout_analysis
        print(f"🚀 突破分析:")
        print(f"  类型: {breakout.breakout_type.value}")
        print(f"  价格: ${breakout.price_at_breakout:,.2f}")
        print(f"  确认: {'✅' if breakout.confirmation else '❌'}")
        if breakout.retest_occurred:
            print(f"  回测: {'✅ 成功' if breakout.retest_successful else '❌ 失败'}")
    
    return report

def demo_pattern_recognition():
    """演示模式识别"""
    print("\n" + "=" * 70)
    print("🔄 演示: 模式识别工具")
    print("=" * 70)
    
    # 创建有明显模式的测试数据
    df = create_sample_data(n=250, trend="up", volatility=1.0, pattern="head_shoulders")
    
    print(f"📊 测试数据: {df.shape[0]} 行 × {df.shape[1]} 列")
    print(f"💰 当前价格: ${df['close'].iloc[-1]:,.2f}")
    print(f"📈 数据包含: 头肩顶模式")
    print()
    
    # 创建模式识别器
    recognizer = PatternRecognizer()
    
    # 执行分析
    print("🔍 执行模式识别...")
    report = recognizer.analyze(df, "BTCUSDT", "4h")
    
    # 打印报告
    report.print_summary()
    
    # 显示详细模式
    print("\n📋 详细模式分析:")
    
    # 图表模式
    if report.patterns:
        print(f"📊 图表模式 ({len(report.patterns)} 个):")
        for i, pattern in enumerate(report.patterns[:3], 1):
            direction_emoji = "🟢" if pattern.direction.value == "bullish" else "🔴"
            print(f"  {i}. {direction_emoji} {pattern.pattern_name}")
            print(f"     类型: {pattern.pattern_type.value}")
            print(f"     方向: {pattern.direction.value}")
            print(f"     状态: {pattern.status.value}")
            print(f"     置信度: {pattern.confidence:.1%}")
            if pattern.target_price:
                distance = (pattern.target_price - report.current_price) / report.current_price * 100
                print(f"     目标: ${pattern.target_price:,.2f} ({distance:+.1f}%)")
            print()
    
    # 活跃模式
    if report.active_patterns:
        print(f"🔄 活跃模式 ({len(report.active_patterns)} 个):")
        for i, pattern in enumerate(report.active_patterns[:3], 1):
            direction_emoji = "🟢" if pattern.direction.value == "bullish" else "🔴"
            print(f"  {i}. {direction_emoji} {pattern.pattern_name}")
            print(f"     置信度: {pattern.confidence:.1%}")
            print(f"     检测时间: {pattern.detected_at}")
            print()
    
    # 蜡烛图模式
    if report.candlestick_patterns:
        print(f"🕯️  蜡烛图模式 ({len(report.candlestick_patterns)} 个):")
        for i, cp in enumerate(report.candlestick_patterns[:5], 1):
            direction_emoji = "🟢" if cp.direction.value == "bullish" else "🔴"
            print(f"  {i}. {direction_emoji} {cp.pattern_name}")
            print(f"     方向: {cp.direction.value}")
            print(f"     置信度: {cp.confidence:.1%}")
            print(f"     蜡烛数: {cp.candles_count}")
            print(f"     量价确认: {'✅' if cp.volume_confirmation else '❌'}")
            print()
    
    return report

def demo_multi_timeframe_analysis():
    """演示多时间框架分析"""
    print("\n" + "=" * 70)
    print("🌐 演示: 多时间框架分析工具")
    print("=" * 70)
    
    # 创建多个时间框架的测试数据
    print("📊 创建多时间框架测试数据...")
    
    mtf_data = {}
    
    # 1日线数据 (宏观趋势)
    df_1d = create_sample_data(n=100, trend="up", volatility=3.0)
    df_1d['timestamp'] = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(100)]
    mtf_data["1d"] = df_1d
    
    # 4小时数据 (中级趋势)
    df_4h = create_sample_data(n=200, trend="up", volatility=2.0)
    df_4h['timestamp'] = [datetime(2024, 3, 1) + timedelta(hours=4*i) for i in range(200)]
    mtf_data["4h"] = df_4h
    
    # 1小时数据 (微观趋势)
    df_1h = create_sample_data(n=300, trend="up", volatility=1.5)
    df_1h['timestamp'] = [datetime(2024, 3, 15) + timedelta(hours=i) for i in range(300)]
    mtf_data["1h"] = df_1h
    
    # 15分钟数据 (交易趋势)
    df_15m = create_sample_data(n=400, trend="up", volatility=1.0)
    df_15m['timestamp'] = [datetime(2024, 3, 20) + timedelta(minutes=15*i) for i in range(400)]
    mtf_data["15m"] = df_15m
    
    print(f"✅ 创建了 {len(mtf_data)} 个时间框架数据:")
    for timeframe, df in mtf_data.items():
        print(f"  {timeframe}: {df.shape[0]} 行 × {df.shape[1]} 列")
    print()
    
    # 创建多时间框架分析器
    analyzer = MultiTimeframeAnalyzer()
    
    # 执行分析
    print("🔍 执行多时间框架分析...")
    report = analyzer.analyze(mtf_data, "BTCUSDT")
    
    # 打印报告
    report.print_summary()
    
    # 显示详细分析
    print("\n📋 详细多时间框架分析:")
    
    # 趋势对齐
    alignment = report.trend_alignment
    print(f"📈 趋势对齐分析:")
    print(f"  状态: {alignment.status.value}")
    print(f"  分数: {alignment.score:.1%}")
    print(f"  宏观趋势: {alignment.macro_trend.value}")
    print(f"  中级趋势: {alignment.intermediate_trend.value}")
    print(f"  微观趋势: {alignment.micro_trend.value}")
    print(f"  交易趋势: {alignment.trading_trend.value}")
    print()
    
    # 信号确认
    if report.signal_confirmations:
        print(f"🚦 信号确认分析:")
        for signal in report.signal_confirmations:
            emoji = {
                "strong_buy": "🟢",
                "buy": "🟡",
                "neutral": "⚪",
                "sell": "🟠",
                "strong_sell": "🔴"
            }.get(signal.signal_type.value, "⚪")
            
            print(f"  {emoji} {signal.signal_type.value.upper()}")
            print(f"     确认分数: {signal.confirmation_score:.1%}")
            print(f"     加权置信度: {signal.weighted_confidence:.1%}")
            print(f"     确认时间框架: {len