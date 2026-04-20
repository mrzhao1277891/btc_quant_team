#!/usr/bin/env python3
"""
波动率指标工具模块

职责: 计算波动率相关的技术指标，用于衡量价格波动的程度。

主要功能:
- 平均真实波幅 (ATR)
- 标准差 (Standard Deviation)
- 波动率通道 (Volatility Channels)
- 肯特纳通道 (Keltner Channels)
- 唐奇安通道 (Donchian Channels)
- 历史波动率 (Historical Volatility)

版本: 1.0.0
作者: 量化团队
更新日期: 2026-04-19
"""

import numpy as np
import math
from typing import List, Dict, Union, Optional, Any
from decimal import Decimal, ROUND_HALF_UP

def calculate_atr(
    high_prices: List[float],
    low_prices: List[float],
    close_prices: List[float],
    period: int = 14
) -> List[Optional[float]]:
    """
    计算平均真实波幅 (Average True Range)
    
    参数:
        high_prices (List[float]): 最高价序列
        low_prices (List[float]): 最低价序列
        close_prices (List[float]): 收盘价序列
        period (int): 计算周期，默认14
    
    返回:
        List[Optional[float]]: ATR值列表，前period个为None
    
    公式:
        真实波幅 = max(以下三者):
            1. 当日最高价 - 当日最低价
            2. |当日最高价 - 前日收盘价|
            3. |当日最低价 - 前日收盘价|
        ATR = EMA(真实波幅, period)
    
    示例:
        >>> highs = [105, 106, 108, 107, 109, 111, 110, 112]
        >>> lows = [100, 101, 103, 104, 105, 107, 108, 109]
        >>> closes = [102, 104, 106, 105, 108, 110, 109, 111]
        >>> atr = calculate_atr(highs, lows, closes, 5)
        >>> atr[-1] > 0
        True
    
    特点:
        - 衡量价格波动性
        - 用于设置止损和仓位大小
        - 波动率增加可能预示趋势变化
    """
    if not high_prices or not low_prices or not close_prices:
        return []
    
    if len(high_prices) != len(low_prices) or len(high_prices) != len(close_prices):
        raise ValueError("价格序列长度必须相同")
    
    n = len(close_prices)
    if n < period + 1:  # 需要至少period+1个数据点
        return [None] * n
    
    # 计算真实波幅
    true_ranges = [None]  # 第一天没有前日收盘价
    
    for i in range(1, n):
        high = high_prices[i]
        low = low_prices[i]
        prev_close = close_prices[i-1]
        
        # 计算三种波幅
        range1 = high - low
        range2 = abs(high - prev_close)
        range3 = abs(low - prev_close)
        
        # 取最大值作为真实波幅
        true_range = max(range1, range2, range3)
        true_ranges.append(true_range)
    
    # 计算ATR (使用EMA平滑)
    atr_values = [None] * period
    
    # 计算初始ATR (前period个真实波幅的简单平均)
    initial_atr = sum(true_ranges[1:period+1]) / period
    atr_values.append(float(initial_atr))
    
    # 计算后续ATR (使用EMA)
    multiplier = 2.0 / (period + 1)
    
    for i in range(period + 1, n):
        current_tr = true_ranges[i]
        prev_atr = atr_values[i-1]
        
        atr = (current_tr * multiplier) + (prev_atr * (1 - multiplier))
        atr_values.append(float(atr))
    
    return atr_values

def calculate_standard_deviation(
    prices: List[float],
    period: int = 20,
    use_sample: bool = True
) -> List[Optional[float]]:
    """
    计算标准差 (Standard Deviation)
    
    参数:
        prices (List[float]): 价格序列
        period (int): 计算周期，默认20
        use_sample (bool): 是否使用样本标准差，默认True
    
    返回:
        List[Optional[float]]: 标准差列表，前period-1个为None
    
    公式:
        均值 = SMA(prices, period)
        方差 = Σ(价格 - 均值)² / (n - 1) [样本] 或 / n [总体]
        标准差 = √方差
    
    示例:
        >>> prices = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109]
        >>> std = calculate_standard_deviation(prices, 5)
        >>> std[-1] >= 0
        True
    
    特点:
        - 衡量价格波动性
        - 用于布林带等指标
        - 识别波动率变化
    """
    if not prices or period <= 0:
        return []
    
    n = len(prices)
    if n < period:
        return [None] * n
    
    std_values = [None] * (period - 1)
    
    for i in range(period - 1, n):
        window = prices[i - period + 1:i + 1]
        
        if len(window) < 2:
            std = 0.0
        else:
            mean = sum(window) / period
            variance = sum((x - mean) ** 2 for x in window)
            
            if use_sample:
                variance /= (period - 1)
            else:
                variance /= period
            
            std = math.sqrt(variance)
        
        std_values.append(float(std))
    
    return std_values

def calculate_keltner_channels(
    high_prices: List[float],
    low_prices: List[float],
    close_prices: List[float],
    ema_period: int = 20,
    atr_period: int = 10,
    multiplier: float = 2.0
) -> Dict[str, List[Optional[float]]]:
    """
    计算肯特纳通道 (Keltner Channels)
    
    参数:
        high_prices (List[float]): 最高价序列
        low_prices (List[float]): 最低价序列
        close_prices (List[float]): 收盘价序列
        ema_period (int): EMA周期，默认20
        atr_period (int): ATR周期，默认10
        multiplier (float): ATR乘数，默认2.0
    
    返回:
        Dict: 包含肯特纳通道各线:
            - upper: 上轨
            - middle: 中轨 (EMA)
            - lower: 下轨
    
    公式:
        中轨 = EMA(收盘价, ema_period)
        上轨 = 中轨 + (ATR × multiplier)
        下轨 = 中轨 - (ATR × multiplier)
    
    示例:
        >>> highs = [105, 106, 108, 107, 109, 111, 110, 112]
        >>> lows = [100, 101, 103, 104, 105, 107, 108, 109]
        >>> closes = [102, 104, 106, 105, 108, 110, 109, 111]
        >>> channels = calculate_keltner_channels(highs, lows, closes, 5, 5)
        >>> channels['upper'][-1] > channels['lower'][-1]
        True
    
    特点:
        - 基于波动率的通道指标
        - 价格突破通道可能预示趋势开始
        - 通道宽度反映波动率
    """
    if not high_prices or not low_prices or not close_prices:
        return {"upper": [], "middle": [], "lower": []}
    
    if len(high_prices) != len(low_prices) or len(high_prices) != len(close_prices):
        raise ValueError("价格序列长度必须相同")
    
    n = len(close_prices)
    max_period = max(ema_period, atr_period)
    
    if n < max_period + 1:
        empty = [None] * n
        return {"upper": empty, "middle": empty, "lower": empty}
    
    # 导入EMA计算函数
    from .trend import calculate_ema
    
    # 计算中轨 (收盘价的EMA)
    middle_band = calculate_ema(close_prices, ema_period)
    
    # 计算ATR
    atr_values = calculate_atr(high_prices, low_prices, close_prices, atr_period)
    
    # 计算上下轨
    upper_band = [None] * n
    lower_band = [None] * n
    
    for i in range(n):
        if middle_band[i] is not None and atr_values[i] is not None:
            upper_band[i] = float(middle_band[i] + (atr_values[i] * multiplier))
            lower_band[i] = float(middle_band[i] - (atr_values[i] * multiplier))
    
    return {
        "upper": upper_band,
        "middle": middle_band,
        "lower": lower_band
    }

def calculate_donchian_channels(
    high_prices: List[float],
    low_prices: List[float],
    period: int = 20
) -> Dict[str, List[Optional[float]]]:
    """
    计算唐奇安通道 (Donchian Channels)
    
    参数:
        high_prices (List[float]): 最高价序列
        low_prices (List[float]): 最低价序列
        period (int): 计算周期，默认20
    
    返回:
        Dict: 包含唐奇安通道各线:
            - upper: 上轨 (N日最高价)
            - middle: 中轨 (上轨+下轨)/2
            - lower: 下轨 (N日最低价)
    
    公式:
        上轨 = max(最近N日最高价)
        下轨 = min(最近N日最低价)
        中轨 = (上轨 + 下轨) / 2
    
    示例:
        >>> highs = [105, 106, 108, 107, 109, 111, 110, 112]
        >>> lows = [100, 101, 103, 104, 105, 107, 108, 109]
        >>> channels = calculate_donchian_channels(highs, lows, 5)
        >>> channels['upper'][-1] >= channels['lower'][-1]
        True
    
    特点:
        - 简单的通道突破系统
        - 用于识别趋势和突破
        - 海龟交易法则的基础
    """
    if not high_prices or not low_prices:
        return {"upper": [], "middle": [], "lower": []}
    
    if len(high_prices) != len(low_prices):
        raise ValueError("最高价和最低价序列长度必须相同")
    
    n = len(high_prices)
    if n < period:
        empty = [None] * n
        return {"upper": empty, "middle": empty, "lower": empty}
    
    upper_band = [None] * (period - 1)
    middle_band = [None] * (period - 1)
    lower_band = [None] * (period - 1)
    
    for i in range(period - 1, n):
        # 获取窗口数据
        high_window = high_prices[i - period + 1:i + 1]
        low_window = low_prices[i - period + 1:i + 1]
        
        # 计算上下轨
        upper = max(high_window)
        lower = min(low_window)
        middle = (upper + lower) / 2
        
        upper_band.append(float(upper))
        middle_band.append(float(middle))
        lower_band.append(float(lower))
    
    return {
        "upper": upper_band,
        "middle": middle_band,
        "lower": lower_band
    }

def calculate_historical_volatility(
    prices: List[float],
    period: int = 20,
    annualize: bool = True,
    trading_days: int = 252
) -> List[Optional[float]]:
    """
    计算历史波动率 (Historical Volatility)
    
    参数:
        prices (List[float]): 价格序列 (通常是收盘价)
        period (int): 计算周期，默认20
        annualize (bool): 是否年化，默认True
        trading_days (int): 年交易天数，默认252
    
    返回:
        List[Optional[float]]: 波动率列表，前period个为None
    
    公式:
        收益率 = ln(今日价格 / 昨日价格)
        收益率标准差 = std(收益率)
        日波动率 = 收益率标准差
        年化波动率 = 日波动率 × √交易天数
    
    示例:
        >>> prices = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109]
        >>> hv = calculate_historical_volatility(prices, 5)
        >>> hv[-1] >= 0
        True
    
    特点:
        - 衡量价格波动性的统计指标
        - 用于期权定价和风险管理
        - 识别波动率变化
    """
    if not prices or period <= 1:
        return []
    
    n = len(prices)
    if n <= period:
        return [None] * n
    
    # 计算对数收益率
    returns = []
    for i in range(1, n):
        if prices[i-1] == 0:
            returns.append(0.0)
        else:
            ret = math.log(prices[i] / prices[i-1])
            returns.append(ret)
    
    # 计算波动率
    volatility_values = [None] * period
    
    for i in range(period - 1, len(returns)):
        window = returns[i - period + 1:i + 1]
        
        if len(window) < 2:
            daily_vol = 0.0
        else:
            mean = sum(window) / len(window)
            variance = sum((x - mean) ** 2 for x in window) / (len(window) - 1)
            daily_vol = math.sqrt(variance)
        
        # 年化 (如果需要)
        if annualize:
            vol = daily_vol * math.sqrt(trading_days)
        else:
            vol = daily_vol
        
        volatility_values.append(float(vol))
    
    return volatility_values

def calculate_volatility_ratio(
    prices: List[float],
    short_period: int = 10,
    long_period: int = 30
) -> List[Optional[float]]:
    """
    计算波动率比率 (Volatility Ratio)
    
    参数:
        prices (List[float]): 价格序列
        short_period (int): 短期波动率周期
        long_period (int): 长期波动率周期
    
    返回:
        List[Optional[float]]: 波动率比率列表
    
    公式:
        短期波动率 = 历史波动率(short_period)
        长期波动率 = 历史波动率(long_period)
        波动率比率 = 短期波动率 / 长期波动率
    
    示例:
        >>> prices = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109] * 10
        >>> vr = calculate_volatility_ratio(prices, 10, 30)
        >>> vr[-1] >= 0
        True
    
    特点:
        - 识别波动率变化
        - 比率>1表示波动率增加
        - 用于识别波动率突破
    """
    if not prices:
        return []
    
    max_period = max(short_period, long_period)
    n = len(prices)
    
    if n <= max_period:
        return [None] * n
    
    # 计算短期和长期波动率
    short_vol = calculate_historical_volatility(prices, short_period, annualize=False)
    long_vol = calculate_historical_volatility(prices, long_period, annualize=False)
    
    # 计算比率
    ratio_values = [None] * max_period
    
    for i in range(max_period, n):
        if short_vol[i] is not None and long_vol[i] is not None:
            if long_vol[i] == 0:
                ratio = 1.0
            else:
                ratio = short_vol[i] / long_vol[i]
            ratio_values.append(float(ratio))
        else:
            ratio_values.append(None)
    
    return ratio_values

def identify_volatility_regime(
    prices: List[float],
    short_period: int = 10,
    long_period: int = 30,
    threshold: float = 1.5
) -> Dict[str, Any]:
    """
    识别波动率状态
    
    参数:
        prices (List[float]): 价格序列
        short_period (int): 短期波动率周期
        long_period (int): 长期波动率周期
        threshold (float): 高波动率阈值
    
    返回:
        Dict: 包含波动率分析结果:
            - current_volatility: 当前波动率
            - volatility_ratio: 波动率比率
            - regime: 波动率状态 (high/low/normal)
            - trend: 波动率趋势 (increasing/decreasing/stable)
    
    示例:
        >>> prices = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109] * 10
