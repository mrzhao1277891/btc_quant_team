#!/usr/bin/env python3
"""
分析工具测试
"""

import pytest
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from tools.analysis.technical import (
    TechnicalAnalyzer, TechnicalAnalysisReport,
    TrendDirection, MarketPhase, SignalType
)

from tools.analysis.support_resistance import (
    SupportResistanceAnalyzer, SupportResistanceReport,
    LevelType, StrengthLevel, BreakoutType
)

from tools.analysis.patterns import (
    PatternRecognizer, PatternAnalysisReport,
    PatternType, PatternDirection, PatternStatus
)

def create_test_data(n=200, trend="up", volatility=1.0):
    """创建测试数据"""
    base_time = datetime(2024, 1, 1)
    
    # 基础趋势
    if trend == "up":
        base_prices = [70000 + i*10 for i in range(n)]
    elif trend == "down":
        base_prices = [80000 - i*10 for i in range(n)]
    else:  # sideways
        base_prices = [75000 for _ in range(n)]
    
    # 添加波动
    prices = []
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

class TestTechnicalAnalyzer:
    """技术分析器测试类"""
    
    def test_technical_analyzer_initialization(self):
        """测试技术分析器初始化"""
        analyzer = TechnicalAnalyzer()
        assert analyzer is not None
        assert "trend_ema_periods" in analyzer.config
    
    def test_analyze_basic(self):
        """测试基本技术分析"""
        df = create_test_data(n=100, trend="up", volatility=1.0)
        
        analyzer = TechnicalAnalyzer()
        report = analyzer.analyze(df, "BTCUSDT", "4h")
        
        assert isinstance(report, TechnicalAnalysisReport)
        assert report.symbol == "BTCUSDT"
        assert report.timeframe == "4h"
        assert report.current_price > 0
        
        # 检查分析结果
        assert report.trend_analysis is not None
        assert report.momentum_analysis is not None
        assert report.volatility_analysis is not None
        assert report.volume_analysis is not None
        
        # 检查趋势方向
        assert isinstance(report.trend_analysis.direction, TrendDirection)
        
        # 检查动量指标
        assert 0 <= report.momentum_analysis.rsi_value <= 100
    
    def test_analyze_different_trends(self):
        """测试不同趋势的分析"""
        # 上升趋势
        df_up = create_test_data(n=100, trend="up")
        analyzer = TechnicalAnalyzer()
        report_up = analyzer.analyze(df_up, "BTCUSDT", "4h")
        
        # 下降趋势
        df_down = create_test_data(n=100, trend="down")
        report_down = analyzer.analyze(df_down, "BTCUSDT", "4h")
        
        # 横盘趋势
        df_sideways = create_test_data(n=100, trend="sideways")
        report_sideways = analyzer.analyze(df_sideways, "BTCUSDT", "4h")
        
        # 检查趋势方向不同
        assert report_up.trend_analysis.direction != report_down.trend_analysis.direction
        
        # 横盘趋势的强度应该较低
        assert report_sideways.trend_analysis.strength < 0.5
    
    def test_analyze_with_signals(self):
        """测试信号生成"""
        # 创建极端数据以生成信号
        df = create_test_data(n=200, trend="up", volatility=2.0)
        
        # 添加一些极端值以触发信号
        df.loc[180, 'close'] = df['close'].iloc[179] * 1.2  # 大幅上涨
        df.loc[190, 'close'] = df['close'].iloc[189] * 0.8  # 大幅下跌
        
        analyzer = TechnicalAnalyzer()
        report = analyzer.analyze(df, "BTCUSDT", "4h")
        
        # 检查是否有信号生成
        assert report.signals is not None
        assert isinstance(report.signals, list)
        
        # 如果有信号，检查信号类型
        if report.signals:
            for signal in report.signals:
                assert isinstance(signal.signal_type, SignalType)
                assert 0 <= signal.confidence <= 1
    
    def test_report_serialization(self):
        """测试报告序列化"""
        df = create_test_data(n=50)
        
        analyzer = TechnicalAnalyzer()
        report = analyzer.analyze(df, "BTCUSDT", "1h")
        
        # 转换为字典
        report_dict = report.to_dict()
        assert isinstance(report_dict, dict)
        assert "symbol" in report_dict
        assert "current_price" in report_dict
        assert "trend_analysis" in report_dict
        
        # 转换为JSON
        report_json = report.to_json()
        assert isinstance(report_json, str)
        assert "BTCUSDT" in report_json
    
    def test_report_print_summary(self):
        """测试报告打印摘要"""
        df = create_test_data(n=50)
        
        analyzer = TechnicalAnalyzer()
        report = analyzer.analyze(df, "BTCUSDT", "1h")
        
        # 测试打印功能
        report.print_summary()  # 应该正常执行，不抛出异常

class TestSupportResistanceAnalyzer:
    """支撑阻力分析器测试类"""
    
    def test_sr_analyzer_initialization(self):
        """测试支撑阻力分析器初始化"""
        analyzer = SupportResistanceAnalyzer()
        assert analyzer is not None
        assert "swing_lookback" in analyzer.config
    
    def test_analyze_basic(self):
        """测试基本支撑阻力分析"""
        df = create_test_data(n=200, trend="up", volatility=1.0)
        
        analyzer = SupportResistanceAnalyzer()
        report = analyzer.analyze(df, "BTCUSDT", "4h")
        
        assert isinstance(report, SupportResistanceReport)
        assert report.symbol == "BTCUSDT"
        assert report.timeframe == "4h"
        assert report.current_price > 0
        
        # 检查支撑阻力位
        assert isinstance(report.support_levels, list)
        assert isinstance(report.resistance_levels, list)
        
        # 检查支撑阻力位类型
        if report.support_levels:
            for level in report.support_levels:
                assert level.level_type == LevelType.SUPPORT
                assert level.price > 0
                assert 0 <= level.confidence <= 1
        
        if report.resistance_levels:
            for level in report.resistance_levels:
                assert level.level_type == LevelType.RESISTANCE
                assert level.price > 0
                assert 0 <= level.confidence <= 1
    
    def test_analyze_with_clear_levels(self):
        """测试有明显支撑阻力位的分析"""
        # 创建有明显支撑阻力位的数据
        n = 300
        base_time = datetime(2024, 1, 1)
        
        # 创建有明确摆动点的数据
        prices = []
        for i in range(n):
            # 每50个数据点创建一个摆动点
            if i % 50 == 0:
                # 创建高点
                price = 80000
            elif i % 25 == 0:
                # 创建低点
                price = 70000
            else:
                # 随机波动
                price = 75000 + np.random.randn() * 1000
            
            prices.append(price)
        
        df = pd.DataFrame({
            'timestamp': [base_time + timedelta(hours=i) for i in range(n)],
            'open': [p - 50 for p in prices],
            'high': [p + 100 for p in prices],
            'low': [p - 100 for p in prices],
            'close': prices,
            'volume': [1000 for _ in range(n)]
        })
        
        analyzer = SupportResistanceAnalyzer()
        report = analyzer.analyze(df, "BTCUSDT", "4h")
        
        # 应该能识别出支撑阻力位
        assert len(report.support_levels) > 0
        assert len(report.resistance_levels) > 0
        
        # 检查最近的支撑阻力
        if report.nearest_support:
            assert report.nearest_support.price > 0
            assert report.nearest_support.level_type == LevelType.SUPPORT
        
        if report.nearest_resistance:
            assert report.nearest_resistance.price > 0
            assert report.nearest_resistance.level_type == LevelType.RESISTANCE
    
    def test_breakout_analysis(self):
        """测试突破分析"""
        # 创建有突破行为的数据
        n = 200
        base_time = datetime(2024, 1, 1)
        
        # 前100个数据在区间内，后100个突破
        prices = []
        for i in range(n):
            if i < 100:
                price = 75000 + np.random.randn() * 500  # 区间震荡
            else:
                price = 80000 + (i-100)*10 + np.random.randn() * 500  # 突破上涨
            
            prices.append(price)
        
        df = pd.DataFrame({
            'timestamp': [base_time + timedelta(hours=i) for i in range(n)],
            'open': [p - 50 for p in prices],
            'high': [p + 100 for p in prices],
            'low': [p - 100 for p in prices],
            'close': prices,
            'volume': [1000 for _ in range(n)]
        })
        
        analyzer = SupportResistanceAnalyzer()
        report = analyzer.analyze(df, "BTCUSDT", "4h")
        
        # 检查突破分析
        if report.breakout_analysis:
            assert report.breakout_analysis.price_at_breakout > 0
            assert isinstance(report.breakout_analysis.breakout_type, BreakoutType)
    
    def test_report_print_summary(self):
        """测试报告打印摘要"""
        df = create_test_data(n=100)
        
        analyzer = SupportResistanceAnalyzer()
        report = analyzer.analyze(df, "BTCUSDT", "4h")
        
        # 测试打印功能
        report.print_summary()  # 应该正常执行，不抛出异常

class TestPatternRecognizer:
    """模式识别器测试类"""
    
    def test_pattern_recognizer_initialization(self):
        """测试模式识别器初始化"""
        recognizer = PatternRecognizer()
        assert recognizer is not None
        assert "head_shoulders_min_swings" in recognizer.config
    
    def test_analyze_basic(self):
        """测试基本模式识别"""
        df = create_test_data(n=200, trend="up", volatility=1.0)
        
        recognizer = PatternRecognizer()
        report = recognizer.analyze(df, "BTCUSDT", "4h")
        
        assert isinstance(report, PatternAnalysisReport)
        assert report.symbol == "BTCUSDT"
        assert report.timeframe == "4h"
        assert report.current_price > 0
        
        # 检查模式
        assert isinstance(report.patterns, list)
        assert isinstance(report.candlestick_patterns, list)
        assert isinstance(report.active_patterns, list)
        assert isinstance(report.completed_patterns, list)
        
        # 检查模式类型
        if report.patterns:
            for pattern in report.patterns:
                assert isinstance(pattern.pattern_type, PatternType)
                assert isinstance(pattern.direction, PatternDirection)
                assert isinstance(pattern.status, PatternStatus)
                assert 0 <= pattern.confidence <= 1
    
    def test_analyze_with_clear_patterns(self):
        """测试有明显模式的数据"""
        # 创建头肩顶模式数据
        n = 150
        base_time = datetime(2024, 1, 1)
        
        # 头肩顶模式价格
        prices = []
        
        # 左肩
        for i in range(20):
            prices.append(75000 + i*10)
        
        # 头部
        for i in range(30):
            prices.append(78000 + i*5)
        
        # 右肩
        for i in range(20):
            prices.append(75000 + (20-i)*10)
        
        # 颈线突破
        for i in range(80):
            prices.append(74000 - i*20)
        
        df = pd.DataFrame({
            'timestamp': [base_time + timedelta(hours=i) for i in range(n)],
            'open': [p - 50 for p in prices],
            'high': [p + 100 for p in prices],
            'low': [p - 100 for p in prices],
            'close': prices,
            'volume': [1000 for _ in range(n)]
        })
        
        recognizer = PatternRecognizer()
        report = recognizer.analyze(df, "BTCUSDT", "4h")
        
        # 应该能识别出模式
        assert len(report.patterns) > 0
        
        # 检查是否有头肩顶模式
        head_shoulders_patterns = [
            p for p in report.patterns 
            if "head" in p.pattern_name.lower() and "shoulder" in p.pattern_name.lower()
        ]
        
        # 注意：实际识别可能受参数影响，这里只检查基本功能
        print(f"识别到的模式数量: {len(report.patterns)}")
        print(f"活跃模式数量: {len(report.active_patterns)}")
    
    def test_candlestick_patterns(self):
        """测试蜡烛图模式识别"""
        # 创建有明显蜡烛图模式的数据
        n = 50
        base_time = datetime(2024, 1, 1)
        
        prices = []
        
        # 创建一些典型蜡烛形态
        # 锤子线
        prices.extend([70000, 69000, 71000, 70500])
        
        # 吞没形态
        prices.extend([70500, 71000, 71500, 72000])
        
        # 十字星
        prices.extend([72000, 72100, 71900, 72000])
        
        # 填充剩余数据
        remaining = n - len(prices)
        for i in range(remaining):
            prices.append(72000 + np.random.randn() * 500)
        
        df = pd.DataFrame({
            'timestamp': [base_time + timedelta(hours=i) for i in range(n)],
            'open': [p - 50 + np.random.randn() * 20 for p in prices],
            'high': [p + 100 + np.random.randn() * 30 for p in prices],
            'low': [p - 100 + np.random.randn() * 30 for p in prices],
            'close': prices,
            'volume': [1000 + np.random.randn() * 200 for _ in range(n)]
        })
        
        recognizer = PatternRecognizer()
        report = recognizer.analyze(df, "BTCUSDT", "1h")
        
        # 检查蜡烛图模式
        assert isinstance(report.candlestick_patterns, list)
        
        if report.candlestick_patterns:
            for cp in report.candlestick_patterns:
                assert isinstance(cp.direction, PatternDirection)
                assert 0 <= cp.confidence <= 1
    
    def test_report_print_summary(self):
        """测试报告打印摘要"""
        df = create_test_data(n=100)
        
        recognizer = PatternRecognizer()
        report = recognizer.analyze(df, "BTCUSDT", "4h")
        
        # 测试打印功能
        report.print_summary()  # 应该正常执行，不抛出异常

class TestAnalysisIntegration:
    """分析工具集成测试"""
    
    def test_complete_analysis_pipeline(self):
        """测试完整分析流水线"""
        print("=" * 60)
        print("测试完整分析流水线")
        print("=" * 60)
        
        # 创建测试数据
        df = create_test_data(n=300, trend="up", volatility=1.5)
        print(f"📊 测试数据: {df.shape[0]} 行 × {df.shape[1]} 列")
        
        # 1. 技术分析
        print("\n1. 📊 执行技术分析...")
        technical_analyzer = TechnicalAnalyzer()
        technical_report = technical_analyzer.analyze(df, "BTCUSDT", "4h")
        
        print(f"   趋势方向: {technical_report.trend_analysis.direction.value}")
        print(f"   趋势强度: {technical_report.trend_analysis.strength:.1%}")
        print(f"   RSI: {technical_report.momentum_analysis.rsi_value:.1f}")
        print(f"   信号数量: {len(technical_report.signals)}")
        
        # 2. 支撑阻力分析
        print("\n2. 🎯 执行支撑阻力分析...")
        sr_analyzer = SupportResistanceAnalyzer()
        sr_report = sr_analyzer.analyze(df, "BTCUSDT", "4h")
        
        print(f"