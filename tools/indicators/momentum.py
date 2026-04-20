#!/usr/bin/env python3
"""
动量指标工具模块

职责: 计算动量相关的技术指标，用于识别价格变化的速度和强度。

主要功能:
- 相对强弱指数 (RSI)
- 随机震荡指标 (Stochastic)
- 商品通道指数 (CCI)
- 动量指标 (Momentum)
- 变动率指标 (ROC)
- 威廉指标 (Williams %R)

版本: 1.0.0
作者: 量化团队
更新日期: 2026-04-19
"""

import numpy as np
from typing import List, Dict, Union, Optional, Any
from decimal import Decimal, ROUND_HALF_UP

def calculate_rsi(
    prices: List[float],
    period: int = 14
) -> List[Optional[float]]:
    """
    计算相对强弱指数 (Relative Strength Index)
    
    参数:
        prices (List[float]): 价格序列 (通常是收盘价)
        period (int): 计算周期，默认14
    
    返回:
        List[Optional[float]]: RSI值列表，前period个为None
    
    公式:
        上涨幅度 = 当日收盘价 - 前日收盘价 (如果上涨)
        下跌幅度 = 前日收盘价 - 当日收盘价 (如果下跌)
        平均上涨 = EMA(上涨幅度, period)
        平均下跌 = EMA(下跌幅度, period)
        RS = 平均上涨 / 平均下跌
        RSI = 100 - (100 / (1 + RS))
    
    示例:
        >>> prices = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109]
        >>> rsi = calculate_rsi(prices, 5)
        >>> 0 <= rsi[-1] <= 100
        True
    
    特点:
        - 范围0-100，通常30以下超卖，70以上超买
        - 识别价格动量和超买超卖
        - 背离信号可能预示趋势反转
    """
    if not prices or period <= 0 or len(prices) <= period:
        return [None] * len(prices)
    
    rsi_values = [None] * period
    
    # 计算价格变化
    deltas = []
    for i in range(1, len(prices)):
        delta = prices[i] - prices[i-1]
        deltas.append(delta)
    
    # 初始化平均上涨和下跌
    gains = [max(d, 0) for d in deltas]
    losses = [abs(min(d, 0)) for d in deltas]
    
    # 计算初始平均值
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    
    # 计算第一个RSI
    if avg_loss == 0:
        rsi = 100.0
    else:
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
    rsi_values.append(float(rsi))
    
    # 计算后续RSI (使用平滑)
    for i in range(period, len(deltas)):
        gain = gains[i]
        loss = losses[i]
        
        # 平滑计算平均上涨和下跌
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
        
        if avg_loss == 0:
            rsi = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        rsi_values.append(float(rsi))
    
    return rsi_values

def calculate_stochastic(
    high_prices: List[float],
    low_prices: List[float],
    close_prices: List[float],
    k_period: int = 14,
    d_period: int = 3,
    smooth: int = 3
) -> Dict[str, List[Optional[float]]]:
    """
    计算随机震荡指标 (Stochastic Oscillator)
    
    参数:
        high_prices (List[float]): 最高价序列
        low_prices (List[float]): 最低价序列
        close_prices (List[float]): 收盘价序列
        k_period (int): %K周期，默认14
        d_period (int): %D周期，默认3
        smooth (int): 平滑周期，默认3
    
    返回:
        Dict: 包含随机指标各线:
            - k_line: %K线 (快速线)
            - d_line: %D线 (慢速线，%K的SMA)
    
    公式:
        %K = (当前收盘价 - N日最低价) / (N日最高价 - N日最低价) × 100
        %D = SMA(%K, M)
    
    示例:
        >>> highs = [105, 106, 108, 107, 109, 111, 110, 112]
        >>> lows = [100, 101, 103, 104, 105, 107, 108, 109]
        >>> closes = [102, 104, 106, 105, 108, 110, 109, 111]
        >>> stoch = calculate_stochastic(highs, lows, closes, 5)
        >>> 0 <= stoch['k_line'][-1] <= 100
        True
    
    特点:
        - 范围0-100，通常20以下超卖，80以上超买
        - %K和%D交叉产生交易信号
        - 背离可能预示趋势反转
    """
    if not high_prices or not low_prices or not close_prices:
        return {"k_line": [], "d_line": []}
    
    if len(high_prices) != len(low_prices) or len(high_prices) != len(close_prices):
        raise ValueError("价格序列长度必须相同")
    
    n = len(close_prices)
    if n < k_period:
        return {"k_line": [None] * n, "d_line": [None] * n}
    
    # 计算%K线
    k_line = [None] * (k_period - 1)
    
    for i in range(k_period - 1, n):
        # 获取窗口内的最高价和最低价
        window_highs = high_prices[i - k_period + 1:i + 1]
        window_lows = low_prices[i - k_period + 1:i + 1]
        
        highest_high = max(window_highs)
        lowest_low = min(window_lows)
        
        if highest_high == lowest_low:
            k_value = 50.0  # 避免除零
        else:
            k_value = ((close_prices[i] - lowest_low) / (highest_high - lowest_low)) * 100
        
        k_line.append(float(k_value))
    
    # 平滑%K线 (如果需要)
    if smooth > 1:
        smoothed_k = []
        for i in range(len(k_line)):
            if i < smooth - 1:
                smoothed_k.append(None)
            else:
                window = k_line[i - smooth + 1:i + 1]
                if any(x is None for x in window):
                    smoothed_k.append(None)
                else:
                    smoothed_k.append(sum(window) / smooth)
        k_line = smoothed_k
    
    # 计算%D线 (%K线的SMA)
    d_line = [None] * (d_period - 1)
    
    for i in range(d_period - 1, len(k_line)):
        if k_line[i] is None:
            d_line.append(None)
        else:
            window = k_line[i - d_period + 1:i + 1]
            if any(x is None for x in window):
                d_line.append(None)
            else:
                d_value = sum(window) / d_period
                d_line.append(float(d_value))
    
    # 对齐长度
    d_line = d_line + [None] * (len(k_line) - len(d_line))
    
    return {
        "k_line": k_line,
        "d_line": d_line
    }

def calculate_cci(
    high_prices: List[float],
    low_prices: List[float],
    close_prices: List[float],
    period: int = 20
) -> List[Optional[float]]:
    """
    计算商品通道指数 (Commodity Channel Index)
    
    参数:
        high_prices (List[float]): 最高价序列
        low_prices (List[float]): 最低价序列
        close_prices (List[float]): 收盘价序列
        period (int): 计算周期，默认20
    
    返回:
        List[Optional[float]]: CCI值列表，前period-1个为None
    
    公式:
        典型价格 = (最高价 + 最低价 + 收盘价) / 3
        SMA = SMA(典型价格, period)
        平均偏差 = 平均(|典型价格 - SMA|)
        CCI = (典型价格 - SMA) / (0.015 × 平均偏差)
    
    示例:
        >>> highs = [105, 106, 108, 107, 109, 111, 110, 112]
        >>> lows = [100, 101, 103, 104, 105, 107, 108, 109]
        >>> closes = [102, 104, 106, 105, 108, 110, 109, 111]
        >>> cci = calculate_cci(highs, lows, closes, 5)
        >>> cci[-1]  # 最后一个CCI值
        某个数值
    
    特点:
        - 识别超买超卖，通常+100以上超买，-100以下超卖
        - 识别趋势强度和反转
        - 适合波动性较大的市场
    """
    if not high_prices or not low_prices or not close_prices:
        return []
    
    if len(high_prices) != len(low_prices) or len(high_prices) != len(close_prices):
        raise ValueError("价格序列长度必须相同")
    
    n = len(close_prices)
    if n < period:
        return [None] * n
    
    # 计算典型价格
    typical_prices = []
    for i in range(n):
        tp = (high_prices[i] + low_prices[i] + close_prices[i]) / 3
        typical_prices.append(tp)
    
    # 计算CCI
    cci_values = [None] * (period - 1)
    
    for i in range(period - 1, n):
        # 获取窗口数据
        window = typical_prices[i - period + 1:i + 1]
        
        # 计算SMA
        sma = sum(window) / period
        
        # 计算平均偏差
        deviations = [abs(tp - sma) for tp in window]
        mean_deviation = sum(deviations) / period
        
        if mean_deviation == 0:
            cci = 0.0
        else:
            cci = (typical_prices[i] - sma) / (0.015 * mean_deviation)
        
        cci_values.append(float(cci))
    
    return cci_values

def calculate_momentum(
    prices: List[float],
    period: int = 10
) -> List[Optional[float]]:
    """
    计算动量指标 (Momentum)
    
    参数:
        prices (List[float]): 价格序列
        period (int): 计算周期，默认10
    
    返回:
        List[Optional[float]]: 动量值列表，前period个为None
    
    公式:
        动量 = 当前价格 - N日前价格
    
    示例:
        >>> prices = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109]
        >>> momentum = calculate_momentum(prices, 5)
        >>> momentum[-1]  # 最后一个动量值
        4.0  # 109 - 105
    
    特点:
        - 简单直观的价格变化度量
        - 正值为上涨动量，负值为下跌动量
        - 零线交叉可能预示趋势变化
    """
    if not prices or period <= 0:
        return []
    
    n = len(prices)
    if n <= period:
        return [None] * n
    
    momentum_values = [None] * period
    
    for i in range(period, n):
        momentum = prices[i] - prices[i - period]
        momentum_values.append(float(momentum))
    
    return momentum_values

def calculate_roc(
    prices: List[float],
    period: int = 12
) -> List[Optional[float]]:
    """
    计算变动率指标 (Rate of Change)
    
    参数:
        prices (List[float]): 价格序列
        period (int): 计算周期，默认12
    
    返回:
        List[Optional[float]]: ROC值列表，前period个为None
    
    公式:
        ROC = (当前价格 - N日前价格) / N日前价格 × 100
    
    示例:
        >>> prices = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109]
        >>> roc = calculate_roc(prices, 5)
        >>> roc[-1]  # 最后一个ROC值
        3.81  # (109 - 105) / 105 × 100
    
    特点:
        - 百分比形式的价格变化率
        - 识别价格变化的速度
        - 零线交叉和背离信号
    """
    if not prices or period <= 0:
        return []
    
    n = len(prices)
    if n <= period:
        return [None] * n
    
    roc_values = [None] * period
    
    for i in range(period, n):
        if prices[i - period] == 0:
            roc = 0.0
        else:
            roc = ((prices[i] - prices[i - period]) / prices[i - period]) * 100
        roc_values.append(float(roc))
    
    return roc_values

def calculate_williams_r(
    high_prices: List[float],
    low_prices: List[float],
    close_prices: List[float],
    period: int = 14
) -> List[Optional[float]]:
    """
    计算威廉指标 (Williams %R)
    
    参数:
        high_prices (List[float]): 最高价序列
        low_prices (List[float]): 最低价序列
        close_prices (List[float]): 收盘价序列
        period (int): 计算周期，默认14
    
    返回:
        List[Optional[float]]: Williams %R值列表，前period-1个为None
    
    公式:
        %R = (N日最高价 - 当前收盘价) / (N日最高价 - N日最低价) × (-100)
    
    示例:
        >>> highs = [105, 106, 108, 107, 109, 111, 110, 112]
        >>> lows = [100, 101, 103, 104, 105, 107, 108, 109]
        >>> closes = [102, 104, 106, 105, 108, 110, 109, 111]
        >>> williams = calculate_williams_r(highs, lows, closes, 5)
        >>> -100 <= williams[-1] <= 0
        True
    
    特点:
        - 范围-100到0，通常-20以上超买，-80以下超卖
        - 与随机指标类似但刻度相反
        - 识别超买超卖水平
    """
    if not high_prices or not low_prices or not close_prices:
        return []
    
    if len(high_prices) != len(low_prices) or len(high_prices) != len(close_prices):
        raise ValueError("价格序列长度必须相同")
    
    n = len(close_prices)
    if n < period:
        return [None] * n
    
    williams_values = [None] * (period - 1)
    
    for i in range(period - 1, n):
        # 获取窗口内的最高价和最低价
        window_highs = high_prices[i - period + 1:i + 1]
        window_lows = low_prices[i - period + 1:i + 1]
        
        highest_high = max(window_highs)
        lowest_low = min(window_lows)
        
        if highest_high == lowest_low:
            williams = -50.0  # 避免除零
        else:
            williams = ((highest_high - close_prices[i]) / (highest_high - lowest_low)) * (-100)
        
        williams_values.append(float(williams))
    
    return williams_values

def identify_momentum_signals(
    prices: List[float],
    rsi_period: int = 14,
    stochastic_period: int = 14
) -> Dict[str, Any]:
    """
    识别动量信号
    
    参数:
        prices (List[float]): 价格序列
        rsi_period (int): RSI计算周期
        stochastic_period (int): 随机指标计算周期
    
    返回:
        Dict: 包含动量分析结果:
            - rsi_value: 当前RSI值
            - rsi_signal: RSI信号 (oversold/overbought/neutral)
            - stochastic_k: 随机%K值
            - stochastic_d: 随机%D值
            - stochastic_signal: 随机指标信号
            - momentum: 动量值
            - overall_signal: 综合信号
    
    示例:
        >>> prices = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109] * 10
        >>> signals = identify_momentum_signals