#!/usr/bin/env python3
"""
指标工具测试
"""

import pytest
import sys
import math
from pathlib import Path
from unittest.mock import Mock, patch

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from tools.indicators.trend_complete import (
    calculate_sma,
    calculate_ema,
    calculate_wma,
    calculate_macd,
    calculate_bollinger_bands,
    identify_trend_direction
)

from tools.indicators.momentum import (
    calculate_rsi,
    calculate_stochastic,
    calculate_cci,
    calculate_momentum,
    calculate_roc
)

from tools.indicators.volatility import (
    calculate_atr,
    calculate_standard_deviation,
    calculate_historical_volatility
)

from tools.indicators.volume import (
    calculate_volume_ma,
    calculate_obv,
    calculate_vwap
)

class TestTrendIndicators:
    """趋势指标测试类"""
    
    def test_calculate_sma_basic(self):
        """测试SMA基本计算"""
        prices = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109]
        
        # 测试周期5
        sma = calculate_sma(prices, 5)
        assert len(sma) == len(prices)
        assert sma[0] is None  # 前4个为None
        assert sma[1] is None
        assert sma[2] is None
        assert sma[3] is None
        assert sma[4] is not None  # 第5个开始有值
        
        # 验证计算正确性
        # 前5个价格: 100, 102, 101, 103, 105 = 511/5 = 102.2
        assert abs(sma[4] - 102.2) < 0.01
        
        # 最后5个价格: 105, 104, 106, 108, 107, 109
        # 最后SMA应该是最后5个: 105, 106, 108, 107, 109 = 535/5 = 107.0
        assert abs(sma[-1] - 107.0) < 0.01
    
    def test_calculate_sma_edge_cases(self):
        """测试SMA边界情况"""
        # 空列表
        assert calculate_sma([], 5) == []
        
        # 周期为0
        assert calculate_sma([100, 102], 0) == []
        
        # 周期大于数据长度
        prices = [100, 102, 101]
        sma = calculate_sma(prices, 5)
        assert sma == [None, None, None]
    
    def test_calculate_ema_basic(self):
        """测试EMA基本计算"""
        prices = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109]
        
        # 测试周期5
        ema = calculate_ema(prices, 5)
        assert len(ema) == len(prices)
        assert ema[0] is None  # 前4个为None
        assert ema[4] is not None  # 第5个开始有值
        
        # EMA应该比SMA对近期价格更敏感
        sma = calculate_sma(prices, 5)
        assert ema[-1] is not None
        assert sma[-1] is not None
    
    def test_calculate_macd_basic(self):
        """测试MACD基本计算"""
        prices = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109] * 5
        
        macd_data = calculate_macd(prices)
        
        assert "macd_line" in macd_data
        assert "signal_line" in macd_data
        assert "histogram" in macd_data
        
        assert len(macd_data["macd_line"]) == len(prices)
        assert len(macd_data["signal_line"]) == len(prices)
        assert len(macd_data["histogram"]) == len(prices)
        
        # 验证histogram = macd_line - signal_line
        for i in range(len(prices)):
            if (macd_data["macd_line"][i] is not None and 
                macd_data["signal_line"][i] is not None and
                macd_data["histogram"][i] is not None):
                expected = macd_data["macd_line"][i] - macd_data["signal_line"][i]
                assert abs(macd_data["histogram"][i] - expected) < 0.01
    
    def test_calculate_bollinger_bands(self):
        """测试布林带计算"""
        prices = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109] * 5
        
        bands = calculate_bollinger_bands(prices, period=5, std_dev=2.0)
        
        assert "upper" in bands
        assert "middle" in bands
        assert "lower" in bands
        
        # 验证上轨 > 中轨 > 下轨
        for i in range(len(prices)):
            if (bands["upper"][i] is not None and
                bands["middle"][i] is not None and
                bands["lower"][i] is not None):
                assert bands["upper"][i] >= bands["middle"][i]
                assert bands["middle"][i] >= bands["lower"][i]
    
    def test_identify_trend_direction(self):
        """测试趋势方向识别"""
        # 上升趋势数据
        rising_prices = [100 + i for i in range(50)]
        trend = identify_trend_direction(rising_prices, 10, 30)
        
        assert trend["direction"] in ["up", "down", "sideways", "unknown"]
        assert 0 <= trend["strength"] <= 1
        
        # 下降趋势数据
        falling_prices = [100 - i for i in range(50)]
        trend = identify_trend_direction(falling_prices, 10, 30)
        
        assert trend["direction"] in ["up", "down", "sideways", "unknown"]

class TestMomentumIndicators:
    """动量指标测试类"""
    
    def test_calculate_rsi_basic(self):
        """测试RSI基本计算"""
        prices = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109] * 5
        
        rsi = calculate_rsi(prices, 14)
        
        assert len(rsi) == len(prices)
        
        # RSI应该在0-100之间
        for value in rsi:
            if value is not None:
                assert 0 <= value <= 100
    
    def test_calculate_rsi_extreme_cases(self):
        """测试RSI极端情况"""
        # 连续上涨
        rising_prices = [100 + i for i in range(20)]
        rsi = calculate_rsi(rising_prices, 14)
        
        # 连续上涨时RSI应该接近100
        last_rsi = next((x for x in reversed(rsi) if x is not None), None)
        assert last_rsi is not None
        assert last_rsi > 70  # 应该处于超买区域
        
        # 连续下跌
        falling_prices = [100 - i for i in range(20)]
        rsi = calculate_rsi(falling_prices, 14)
        
        # 连续下跌时RSI应该接近0
        last_rsi = next((x for x in reversed(rsi) if x is not None), None)
        assert last_rsi is not None
        assert last_rsi < 30  # 应该处于超卖区域
    
    def test_calculate_stochastic(self):
        """测试随机指标计算"""
        highs = [105, 106, 108, 107, 109, 111, 110, 112] * 5
        lows = [100, 101, 103, 104, 105, 107, 108, 109] * 5
        closes = [102, 104, 106, 105, 108, 110, 109, 111] * 5
        
        stoch = calculate_stochastic(highs, lows, closes, k_period=14, d_period=3)
        
        assert "k_line" in stoch
        assert "d_line" in stoch
        
        # %K和%D应该在0-100之间
        for k, d in zip(stoch["k_line"], stoch["d_line"]):
            if k is not None:
                assert 0 <= k <= 100
            if d is not None:
                assert 0 <= d <= 100
    
    def test_calculate_momentum(self):
        """测试动量指标计算"""
        prices = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109]
        
        momentum = calculate_momentum(prices, period=5)
        
        assert len(momentum) == len(prices)
        
        # 验证计算正确性
        # 最后动量 = 109 - 105 = 4
        last_momentum = next((x for x in reversed(momentum) if x is not None), None)
        assert abs(last_momentum - 4.0) < 0.01
    
    def test_calculate_roc(self):
        """测试变动率指标计算"""
        prices = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109]
        
        roc = calculate_roc(prices, period=5)
        
        assert len(roc) == len(prices)
        
        # 验证计算正确性
        # 最后ROC = (109 - 105) / 105 × 100 = 3.81%
        last_roc = next((x for x in reversed(roc) if x is not None), None)
        assert abs(last_roc - 3.81) < 0.1

class TestVolatilityIndicators:
    """波动率指标测试类"""
    
    def test_calculate_atr(self):
        """测试ATR计算"""
        highs = [105, 106, 108, 107, 109, 111, 110, 112] * 5
        lows = [100, 101, 103, 104, 105, 107, 108, 109] * 5
        closes = [102, 104, 106, 105, 108, 110, 109, 111] * 5
        
        atr = calculate_atr(highs, lows, closes, period=14)
        
        assert len(atr) == len(closes)
        
        # ATR应该为正数
        for value in atr:
            if value is not None:
                assert value >= 0
    
    def test_calculate_standard_deviation(self):
        """测试标准差计算"""
        prices = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109] * 5
        
        std = calculate_standard_deviation(prices, period=20)
        
        assert len(std) == len(prices)
        
        # 标准差应该为非负数
        for value in std:
            if value is not None:
                assert value >= 0
    
    def test_calculate_historical_volatility(self):
        """测试历史波动率计算"""
        prices = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109] * 10
        
        hv = calculate_historical_volatility(prices, period=20, annualize=False)
        
        assert len(hv) == len(prices)
        
        # 波动率应该为非负数
        for value in hv:
            if value is not None:
                assert value >= 0

class TestVolumeIndicators:
    """成交量指标测试类"""
    
    def test_calculate_volume_ma(self):
        """测试成交量均线计算"""
        volumes = [1000, 1200, 1100, 1300, 1400, 1250, 1350, 1500, 1450, 1600]
        
        volume_ma = calculate_volume_ma(volumes, period=5)
        
        assert len(volume_ma) == len(volumes)
        
        # 验证计算正确性
        # 最后5个成交量: 1400, 1250, 1350, 1500, 1450, 1600
        # 最后MA应该是最后5个: 1250, 1350, 1500, 1450, 1600 = 7150/5 = 1430
        last_ma = next((x for x in reversed(volume_ma) if x is not None), None)
        assert abs(last_ma - 1430.0) < 0.01
    
    def test_calculate_obv(self):
        """测试OBV计算"""
        closes = [100, 102, 101, 103, 105]
        volumes = [1000, 1200, 1100, 1300, 1400]
        
        obv = calculate_obv(closes, volumes)
        
        assert len(obv) == len(closes)
        
        # 验证计算正确性
        # 第一天: 1000
        # 第二天上涨: 1000 + 1200 = 2200
        # 第三天下跌: 2200 - 1100 = 1100
        # 第四天上涨: 1100 + 1300 = 2400
        # 第五天上涨: 2400 + 1400 = 3800
        expected = [1000, 2200, 1100, 2400, 3800]
        
        for i, (actual, expected_val) in enumerate(zip(obv, expected)):
            assert abs(actual - expected_val) < 0.01, f"位置 {i}: 实际 {actual}, 期望 {expected_val}"
    
    def test_calculate_vwap(self):
        """测试VWAP计算"""
        highs = [105, 106, 108, 107, 109]
        lows = [100, 101, 103, 104, 105]
        closes = [102, 104, 106, 105, 108]
        volumes = [1000, 1200, 1100, 1300, 1400]
        
        vwap = calculate_vwap(highs, lows, closes, volumes, period=5)
        
        assert len(vwap) == len(closes)
        
        # VWAP应该是一个合理的价格
        last_vwap = next((x for x in reversed(vwap) if x is not None), None)
        assert last_vwap is not None
        assert 100 <= last_vwap <= 110

class TestIndicatorIntegration:
    """指标集成测试"""
    
    def test_multiple_indicators_together(self):
        """测试多个指标一起使用"""
        # 创建测试数据
        n = 100
        prices = [100 + i + (i % 10 - 5) for i in range(n)]  # 有波动的上升趋势
        highs = [p + 2 for p in prices]
        lows = [p - 2 for p in prices]
        closes = prices
        volumes = [1000 + i * 10 for i in range(n)]
        
        # 计算多个指标
        sma = calculate_sma(prices, 20)
        ema = calculate_ema(prices, 12)
        rsi = calculate_rsi(prices, 14)
        atr = calculate_atr(highs, lows, closes, 14)
        obv = calculate_obv(closes, volumes)
        
        # 验证所有指标都有正确长度
        assert len(sma) == n
        assert len(ema) == n
        assert len(rsi) == n
        assert len(atr) == n
        assert len(obv) == n
        
        # 验证指标合理性
        for i in range(n):
            # SMA和EMA应该接近
            if sma[i] is not None and ema[i] is not None:
                diff = abs(sma[i] - ema[i])
                assert diff < 20  # 差异不应该太大
            
            # RSI应该在0-100之间
            if rsi[i] is not None:
                assert 0 <= rsi[i] <= 100
            
            # ATR应该为正
            if atr[i] is not None:
                assert atr[i] >= 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])