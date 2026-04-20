#!/usr/bin/env python3
"""
趋势指标工具模块

职责: 计算趋势相关的技术指标，包括移动平均线、趋势线等。

主要功能:
- 简单移动平均线 (SMA)
- 指数移动平均线 (EMA)
- 加权移动平均线 (WMA)
- 移动平均收敛发散 (MACD)
- 布林带 (Bollinger Bands)
- 抛物线转向指标 (SAR)

版本: 1.0.0
作者: 量化团队
更新日期: 2026-04-19
"""

import numpy as np
from typing import List, Dict, Union, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP

def calculate_sma(
    prices: List[float],
    period: int = 20
) -> List[Optional[float]]:
    """
    计算简单移动平均线 (Simple Moving Average)
    
    参数:
        prices (List[float]): 价格序列 (通常是收盘价)
        period (int): 计算周期，默认20
    
    返回:
        List[Optional[float]]: SMA值列表，前period-1个为None
    
    公式:
        SMA = (P1 + P2 + ... + Pn) / n
        其中n为周期，P为价格
    
    示例:
        >>> prices = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109]
        >>> sma = calculate_sma(prices, 5)
        >>> sma[-1]  # 最后一个SMA值
        106.8
    
    特点:
        - 对历史数据同等权重
        - 滞后性较大
        - 适合识别长期趋势
    """
    if not prices or period <= 0:
        return []
    
    if period > len(prices):
        return [None] * len(prices)
    
    sma_values = [None] * (period - 1)
    
    for i in range(period - 1, len(prices)):
        window = prices[i - period + 1:i + 1]
        sma = sum(window) / period
        sma_values.append(float(sma))
    
    return sma_values

def calculate_ema(
    prices: List[float],
    period: int = 12,
    smoothing: float = 2.0
) -> List[Optional[float]]:
    """
    计算指数移动平均线 (Exponential Moving Average)
    
    参数:
        prices (List[float]): 价格序列
        period (int): 计算周期，默认12
        smoothing (float): 平滑系数，默认2.0
    
    返回:
        List[Optional[float]]: EMA值列表，前period-1个为None
    
    公式:
        乘数 = smoothing / (1 + period)
        EMA = (当前价格 × 乘数) + (前一日EMA × (1 - 乘数))
    
    示例:
        >>> prices = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109]
        >>> ema = calculate_ema(prices, 5)
        >>> ema[-1]  # 最后一个EMA值
        107.13
    
    特点:
        - 对近期数据权重更高
        - 响应更快，滞后性较小
        - 适合短期趋势分析
    """
    if not prices or period <= 0:
        return []
    
    if period > len(prices):
        return [None] * len(prices)
    
    # 计算乘数
    multiplier = smoothing / (1 + period)
    
    # 初始化EMA列表
    ema_values = [None] * len(prices)
    
    # 第一个EMA使用SMA
    first_window = prices[:period]
    ema_values[period - 1] = sum(first_window) / period
    
    # 计算后续EMA
    for i in range(period, len(prices)):
        current_price = prices[i]
        prev_ema = ema_values[i - 1]
        ema = (current_price * multiplier) + (prev_ema * (1 - multiplier))
        ema_values[i] = float(ema)
    
    return ema_values

def calculate_wma(
    prices: List[float],
    period: int = 20
) -> List[Optional[float]]:
    """
    计算加权移动平均线 (Weighted Moving Average)
    
    参数:
        prices (List[float]): 价格序列
        period (int): 计算周期，默认20
    
    返回:
        List[Optional[float]]: WMA值列表，前period-1个为None
    
    公式:
        WMA = (P1×1 + P2×2 + ... + Pn×n) / (1+2+...+n)
        其中n为周期，P为价格，权重线性递增
    
    示例:
        >>> prices = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109]
        >>> wma = calculate_wma(prices, 5)
        >>> wma[-1]  # 最后一个WMA值
        107.33
    
    特点:
        - 近期数据权重线性增加
        - 滞后性介于SMA和EMA之间
        - 适合中期趋势分析
    """
    if not prices or period <= 0:
        return []
    
    if period > len(prices):
        return [None] * len(prices)
    
    wma_values = [None] * (period - 1)
    
    # 计算权重和
    weight_sum = sum(range(1, period + 1))
    
    for i in range(period - 1, len(prices)):
        window = prices[i - period + 1:i + 1]
        
        # 计算加权和
        weighted_sum = 0
        for j, price in enumerate(window, 1):
            weighted_sum += price * j
        
        wma = weighted_sum / weight_sum
        wma_values.append(float(wma))
    
    return wma_values

def calculate_macd(
    prices: List[float],
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> Dict[str, List[Optional[float]]]:
    """
    计算移动平均收敛发散指标 (MACD)
    
    参数:
        prices (List[float]): 价格序列
        fast_period (int): 快线周期，默认12
        slow_period (int): 慢线周期，默认26
        signal_period (int): 信号线周期，默认9
    
    返回:
        Dict: 包含MACD各组成部分:
            - macd_line: MACD线 (快线-慢线)
            - signal_line: 信号线 (MACD的EMA)
            - histogram: 柱状图 (MACD-信号线)
    
    公式:
        MACD线 = EMA(快周期) - EMA(慢周期)
        信号线 = EMA(MACD线, 信号周期)
        柱状图 = MACD线 - 信号线
    
    示例:
        >>> prices = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109] * 10
        >>> macd_data = calculate_macd(prices)
        >>> len(macd_data['macd_line'])
        100
    
    特点:
        - 识别趋势强度和方向
        - 金叉死叉作为买卖信号
        - 柱状图表示动量
    """
    if not prices:
        return {
            "macd_line": [],
            "signal_line": [],
            "histogram": []
        }
    
    # 计算快慢EMA
    fast_ema = calculate_ema(prices, fast_period)
    slow_ema = calculate_ema(prices, slow_period)
    
    # 计算MACD线
    macd_line = []
    min_len = max(len(fast_ema), len(slow_ema))
    
    for i in range(min_len):
        if fast_ema[i] is None or slow_ema[i] is None:
            macd_line.append(None)
        else:
            macd_line.append(fast_ema[i] - slow_ema[i])
    
    # 计算信号线 (MACD线的EMA)
    signal_line = calculate_ema([x for x in macd_line if x is not None], signal_period)
    
    # 对齐长度
    signal_line = [None] * (len(macd_line) - len(signal_line)) + signal_line
    
    # 计算柱状图
    histogram = []
    for i in range(len(macd_line)):
        if macd_line[i] is None or signal_line[i] is None:
            histogram.append(None)
        else:
            histogram.append(macd_line[i] - signal_line[i])
    
    return {
        "macd_line": macd_line,
        "signal_line": signal_line,
        "histogram": histogram
    }

def calculate_bollinger_bands(
    prices: List[float],
    period: int = 20,
    std_dev: float = 2.0
) -> Dict[str, List[Optional[float]]]:
    """
    计算布林带 (Bollinger Bands)
    
    参数:
        prices (List[float]): 价格序列
        period (int): 计算周期，默认20
        std_dev (float): 标准差倍数，默认2.0
    
    返回:
        Dict: 包含布林带各线:
            - upper: 上轨
            - middle: 中轨 (SMA)
            - lower: 下轨
    
    公式:
        中轨 = SMA(period)
        标准差 = std(窗口价格)
        上轨 = 中轨 + (标准差 × std_dev)
        下轨 = 中轨 - (标准差 × std_dev)
    
    示例:
        >>> prices = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109] * 10
        >>> bands = calculate_bollinger_bands(prices)
        >>> bands['upper'][-1] > bands['lower'][-1]
        True
    
    特点:
        - 识别波动率和超买超卖
        - 带宽收缩表示波动率低，可能突破
        - 价格触及上下轨可能反转
    """
    if not prices or period <= 0:
        return {
            "upper": [],
            "middle": [],
            "lower": []
        }
    
    # 计算中轨 (SMA)
    middle_band = calculate_sma(prices, period)
    
    # 初始化上下轨
    upper_band = [None] * len(prices)
    lower_band = [None] * len(prices)
    
    # 计算标准差和布林带
    for i in range(period - 1, len(prices)):
        if middle_band[i] is None:
            continue
        
        # 获取窗口数据
        window = prices[i - period + 1:i + 1]
        
        # 计算标准差
        if len(window) > 1:
            std = np.std(window, ddof=1)  # 样本标准差
        else:
            std = 0.0
        
        # 计算上下轨
        upper_band[i] = float(middle_band[i] + (std * std_dev))
        lower_band[i] = float(middle_band[i] - (std * std_dev))
    
    return {
        "upper": upper_band,
        "middle": middle_band,
        "lower": lower_band
    }

def calculate_parabolic_sar(
    high_prices: List[float],
    low_prices: List[float],
    acceleration: float = 0.02,
    maximum: float = 0.2
) -> List[Optional[float]]:
    """
    计算抛物线转向指标 (Parabolic SAR)
    
    参数:
        high_prices (List[float]): 最高价序列
        low_prices (List[float]): 最低价序列
        acceleration (float): 加速因子，默认0.02
        maximum (float): 最大加速因子，默认0.2
    
    返回:
        List[Optional[float]]: SAR值列表
    
    公式:
        SAR = 前一日SAR + AF × (EP - 前一日SAR)
        其中AF为加速因子，EP为极值点
    
    示例:
        >>> highs = [105, 106, 108, 107, 109, 111, 110, 112]
        >>> lows = [100, 101, 103, 104, 105, 107, 108, 109]
        >>> sar = calculate_parabolic_sar(highs, lows)
        >>> len(sar)
        8
    
    特点:
        - 跟踪止损和反转点
        - 上升趋势中SAR在价格下方
        - 下降趋势中SAR在价格上方
        - AF随趋势发展而增加
    """
    if not high_prices or not low_prices:
        return []
    
    if len(high_prices) != len(low_prices):
        raise ValueError("最高价和最低价序列长度必须相同")
    
    n = len(high_prices)
    if n < 2:
        return [None] * n
    
    # 初始化SAR
    sar_values = [None] * n
    
    # 确定初始趋势 (前两天的价格比较)
    trend_up = high_prices[1] > high_prices[0]
    
    # 初始SAR和极值点
    if trend_up:
        sar = low_prices[0]
        ep = high_prices[0]  # 上升趋势的极值点是最高点
    else:
        sar = high_prices[0]
        ep = low_prices[0]   # 下降趋势的极值点是最低点
    
    sar_values[0] = float(sar)
    af = acceleration
    
    # 计算后续SAR
    for i in range(1, n):
        # 保存前一日值
        prev_sar = sar
        prev_ep = ep
        prev_af = af
        
        # 计算当日SAR
        sar = prev_sar + prev_af * (prev_ep - prev_sar)
        
        # 调整SAR避免穿越价格
        if trend_up:
            # 上升趋势中，SAR不能高于前两天最低价
            if i >= 2:
                sar = min(sar, low_prices[i-1], low_prices[i-2])
            # 检查趋势反转
            if low_prices[i] < sar:
                trend_up = False
                sar = max(high_prices[i], prev_ep)
                ep = low_prices[i]
                af = acceleration
            else:
                # 更新极值点和加速因子
                if high_prices[i] > prev_ep:
                    ep = high_prices[i]
                    af = min(prev_af + acceleration, maximum)
        else:
            # 下降趋势中，SAR不能低于前两天最高价
            if i >= 2:
                sar = max(sar, high_prices[i-1], high_prices[i-2])
            # 检查趋势反转
            if high_prices[i] > sar:
                trend_up = True
                sar = min(low_prices[i], prev_ep)
                ep = high_prices[i]
                af = acceleration
            else:
                # 更新极值点和加速因子
                if low_prices[i] < prev_ep:
                    ep = low_prices[i]
                    af = min(prev_af + acceleration, maximum)
        
        sar_values[i] = float(sar)
    
    return sar_values

def identify_trend_direction(
    prices: List[float],
    short_period: int = 10,
    long_period: int = 30
) -> Dict[str, Any]:
    """
    识别趋势方向
    
    参数:
        prices (List[float]): 价格序列
        short_period (int): 短期均线周期，默认10
        long_period (int): 长期均线周期，默认30
    
    返回:
        Dict: 包含趋势分析结果:
            - direction: 趋势方向 (up/down/sideways)
            - strength: 趋势强度 (0-1)
            - crossover: 金叉死叉信号
            - short_ma: 短期均线值
            - long_ma: 长期均线值
    
    示例:
        >>> prices = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109] * 10
        >>> trend = identify_trend_direction(prices)
        >>> trend['direction']
        'up'
    """
    if not prices or len(prices) < max(short_period, long_period):
        return {
            "direction": "unknown",
            "strength": 0.0,
            "crossover": "none",
            "short_ma": None,
            "long_ma": None
        }
    
    # 计算短期和长期均线
    short_ma = calculate_ema(prices, short_period)
    long_ma = calculate_ema(prices, long_period)
    
    # 获取最新有效值
    short_val = next((x for x in reversed(short_ma) if x is not None), None)
    long_val = next((x for x in reversed(long_ma) if x is not None), None)
    
    if short_val is None or long_val is None:
        return {
            "direction": "unknown",
            "strength": 0.0,
            "crossover": "none",
            "short_ma": short_val,
            "long_ma": long_val
        }
    
    # 判断趋势方向
    if short_val > long_val:
        direction = "up"
        strength = min((short_val - long_val) / long_val * 10, 1.0)
    elif short_val < long_val:
        direction = "down"
        strength = min((long_val - short_val) / long_val * 10, 1.0)
    else:
        direction = "sideways