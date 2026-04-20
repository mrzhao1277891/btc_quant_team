#!/usr/bin/env python3
"""
成交量指标工具模块

职责: 计算成交量相关的技术指标，用于分析交易活跃度和资金流向。

主要功能:
- 成交量移动平均线 (Volume MA)
- 成交量加权平均价格 (VWAP)
- 能量潮指标 (OBV)
- 资金流量指数 (MFI)
- 成交量比率 (Volume Ratio)
- 成交量震荡指标 (Volume Oscillator)

版本: 1.0.0
作者: 量化团队
更新日期: 2026-04-19
"""

import numpy as np
from typing import List, Dict, Union, Optional, Any
from decimal import Decimal, ROUND_HALF_UP

def calculate_volume_ma(
    volumes: List[float],
    period: int = 20
) -> List[Optional[float]]:
    """
    计算成交量移动平均线 (Volume Moving Average)
    
    参数:
        volumes (List[float]): 成交量序列
        period (int): 计算周期，默认20
    
    返回:
        List[Optional[float]]: 成交量均线列表，前period-1个为None
    
    公式:
        Volume MA = SMA(成交量, period)
    
    示例:
        >>> volumes = [1000, 1200, 1100, 1300, 1400, 1250, 1350, 1500]
        >>> volume_ma = calculate_volume_ma(volumes, 5)
        >>> volume_ma[-1]  # 最后一个值
        1320.0
    
    特点:
        - 平滑成交量数据
        - 识别成交量趋势
        - 成交量高于均线表示活跃
    """
    if not volumes or period <= 0:
        return []
    
    if period > len(volumes):
        return [None] * len(volumes)
    
    volume_ma_values = [None] * (period - 1)
    
    for i in range(period - 1, len(volumes)):
        window = volumes[i - period + 1:i + 1]
        ma = sum(window) / period
        volume_ma_values.append(float(ma))
    
    return volume_ma_values

def calculate_vwap(
    high_prices: List[float],
    low_prices: List[float],
    close_prices: List[float],
    volumes: List[float],
    period: int = 20
) -> List[Optional[float]]:
    """
    计算成交量加权平均价格 (Volume Weighted Average Price)
    
    参数:
        high_prices (List[float]): 最高价序列
        low_prices (List[float]): 最低价序列
        close_prices (List[float]): 收盘价序列
        volumes (List[float]): 成交量序列
        period (int): 计算周期，默认20
    
    返回:
        List[Optional[float]]: VWAP值列表，前period-1个为None
    
    公式:
        典型价格 = (最高价 + 最低价 + 收盘价) / 3
        成交量加权和 = Σ(典型价格 × 成交量)
        总成交量 = Σ(成交量)
        VWAP = 成交量加权和 / 总成交量
    
    示例:
        >>> highs = [105, 106, 108, 107, 109]
        >>> lows = [100, 101, 103, 104, 105]
        >>> closes = [102, 104, 106, 105, 108]
        >>> volumes = [1000, 1200, 1100, 1300, 1400]
        >>> vwap = calculate_vwap(highs, lows, closes, volumes, 5)
        >>> vwap[-1]
        105.8
    
    特点:
        - 反映平均成交价格
        - 用于日内交易参考
        - 价格在VWAP之上为强势
    """
    if not high_prices or not low_prices or not close_prices or not volumes:
        return []
    
    n = len(close_prices)
    if n != len(high_prices) or n != len(low_prices) or n != len(volumes):
        raise ValueError("所有序列长度必须相同")
    
    if n < period:
        return [None] * n
    
    vwap_values = [None] * (period - 1)
    
    for i in range(period - 1, n):
        # 获取窗口数据
        high_window = high_prices[i - period + 1:i + 1]
        low_window = low_prices[i - period + 1:i + 1]
        close_window = close_prices[i - period + 1:i + 1]
        volume_window = volumes[i - period + 1:i + 1]
        
        # 计算典型价格和加权和
        weighted_sum = 0
        total_volume = 0
        
        for j in range(period):
            typical_price = (high_window[j] + low_window[j] + close_window[j]) / 3
            weighted_sum += typical_price * volume_window[j]
            total_volume += volume_window[j]
        
        if total_volume == 0:
            vwap = 0.0
        else:
            vwap = weighted_sum / total_volume
        
        vwap_values.append(float(vwap))
    
    return vwap_values

def calculate_obv(
    close_prices: List[float],
    volumes: List[float]
) -> List[float]:
    """
    计算能量潮指标 (On-Balance Volume)
    
    参数:
        close_prices (List[float]): 收盘价序列
        volumes (List[float]): 成交量序列
    
    返回:
        List[float]: OBV值列表
    
    公式:
        如果今日收盘价 > 昨日收盘价: OBV = 前日OBV + 今日成交量
        如果今日收盘价 < 昨日收盘价: OBV = 前日OBV - 今日成交量
        如果今日收盘价 = 昨日收盘价: OBV = 前日OBV
    
    示例:
        >>> closes = [100, 102, 101, 103, 105]
        >>> volumes = [1000, 1200, 1100, 1300, 1400]
        >>> obv = calculate_obv(closes, volumes)
        >>> obv
        [1000, 2200, 1100, 2400, 3800]
    
    特点:
        - 反映资金流向
        - OBV与价格背离可能预示反转
        - 识别成交量确认的趋势
    """
    if not close_prices or not volumes:
        return []
    
    n = len(close_prices)
    if n != len(volumes):
        raise ValueError("收盘价和成交量序列长度必须相同")
    
    if n == 0:
        return []
    
    obv_values = [float(volumes[0])]  # 第一天OBV等于当日成交量
    
    for i in range(1, n):
        prev_obv = obv_values[i-1]
        
        if close_prices[i] > close_prices[i-1]:
            # 价格上涨，成交量加入
            obv = prev_obv + volumes[i]
        elif close_prices[i] < close_prices[i-1]:
            # 价格下跌，成交量减去
            obv = prev_obv - volumes[i]
        else:
            # 价格不变，OBV不变
            obv = prev_obv
        
        obv_values.append(float(obv))
    
    return obv_values

def calculate_mfi(
    high_prices: List[float],
    low_prices: List[float],
    close_prices: List[float],
    volumes: List[float],
    period: int = 14
) -> List[Optional[float]]:
    """
    计算资金流量指数 (Money Flow Index)
    
    参数:
        high_prices (List[float]): 最高价序列
        low_prices (List[float]): 最低价序列
        close_prices (List[float]): 收盘价序列
        volumes (List[float]): 成交量序列
        period (int): 计算周期，默认14
    
    返回:
        List[Optional[float]]: MFI值列表，前period个为None
    
    公式:
        典型价格 = (最高价 + 最低价 + 收盘价) / 3
        资金流 = 典型价格 × 成交量
        如果今日典型价格 > 昨日典型价格: 正资金流
        如果今日典型价格 < 昨日典型价格: 负资金流
        资金比率 = (正资金流和) / (负资金流和)
        MFI = 100 - (100 / (1 + 资金比率))
    
    示例:
        >>> highs = [105, 106, 108, 107, 109, 111, 110, 112]
        >>> lows = [100, 101, 103, 104, 105, 107, 108, 109]
        >>> closes = [102, 104, 106, 105, 108, 110, 109, 111]
        >>> volumes = [1000, 1200, 1100, 1300, 1400, 1500, 1450, 1600]
        >>> mfi = calculate_mfi(highs, lows, closes, volumes, 5)
        >>> 0 <= mfi[-1] <= 100
        True
    
    特点:
        - 成交量加权的RSI
        - 范围0-100，通常20以下超卖，80以上超买
        - 识别资金流入流出
    """
    if not high_prices or not low_prices or not close_prices or not volumes:
        return []
    
    n = len(close_prices)
    if n != len(high_prices) or n != len(low_prices) or n != len(volumes):
        raise ValueError("所有序列长度必须相同")
    
    if n <= period:
        return [None] * n
    
    # 计算典型价格
    typical_prices = []
    for i in range(n):
        tp = (high_prices[i] + low_prices[i] + close_prices[i]) / 3
        typical_prices.append(tp)
    
    # 计算原始资金流
    raw_money_flow = []
    for i in range(n):
        mf = typical_prices[i] * volumes[i]
        raw_money_flow.append(mf)
    
    # 计算正负资金流
    positive_flow = [0.0] * n
    negative_flow = [0.0] * n
    
    for i in range(1, n):
        if typical_prices[i] > typical_prices[i-1]:
            positive_flow[i] = raw_money_flow[i]
        elif typical_prices[i] < typical_prices[i-1]:
            negative_flow[i] = raw_money_flow[i]
        # 价格相等时，资金流为0
    
    # 计算MFI
    mfi_values = [None] * period
    
    for i in range(period, n):
        # 获取窗口内的正负资金流
        pos_window = positive_flow[i - period + 1:i + 1]
        neg_window = negative_flow[i - period + 1:i + 1]
        
        sum_pos = sum(pos_window)
        sum_neg = sum(neg_window)
        
        if sum_neg == 0:
            mfi = 100.0
        else:
            money_ratio = sum_pos / sum_neg
            mfi = 100 - (100 / (1 + money_ratio))
        
        mfi_values.append(float(mfi))
    
    return mfi_values

def calculate_volume_ratio(
    volumes: List[float],
    short_period: int = 5,
    long_period: int = 20
) -> List[Optional[float]]:
    """
    计算成交量比率 (Volume Ratio)
    
    参数:
        volumes (List[float]): 成交量序列
        short_period (int): 短期均线周期
        long_period (int): 长期均线周期
    
    返回:
        List[Optional[float]]: 成交量比率列表
    
    公式:
        短期均量 = SMA(成交量, short_period)
        长期均量 = SMA(成交量, long_period)
        成交量比率 = 短期均量 / 长期均量
    
    示例:
        >>> volumes = [1000, 1200, 1100, 1300, 1400, 1500, 1450, 1600]
        >>> vr = calculate_volume_ratio(volumes, 3, 5)
        >>> vr[-1]
        1.07
    
    特点:
        - 识别成交量异常
        - 比率>1表示成交量放大
        - 用于确认价格突破
    """
    if not volumes:
        return []
    
    max_period = max(short_period, long_period)
    n = len(volumes)
    
    if n < max_period:
        return [None] * n
    
    # 计算短期和长期成交量均线
    short_ma = calculate_volume_ma(volumes, short_period)
    long_ma = calculate_volume_ma(volumes, long_period)
    
    # 计算比率
    ratio_values = [None] * max_period
    
    for i in range(max_period, n):
        if short_ma[i] is not None and long_ma[i] is not None:
            if long_ma[i] == 0:
                ratio = 1.0
            else:
                ratio = short_ma[i] / long_ma[i]
            ratio_values.append(float(ratio))
        else:
            ratio_values.append(None)
    
    return ratio_values

def calculate_volume_oscillator(
    volumes: List[float],
    short_period: int = 12,
    long_period: int = 26
) -> List[Optional[float]]:
    """
    计算成交量震荡指标 (Volume Oscillator)
    
    参数:
        volumes (List[float]): 成交量序列
        short_period (int): 短期均线周期
        long_period (int): 长期均线周期
    
    返回:
        List[Optional[float]]: 成交量震荡指标值
    
    公式:
        VO = (短期成交量均线 - 长期成交量均线) / 长期成交量均线 × 100
    
    示例:
        >>> volumes = [1000, 1200, 1100, 1300, 1400, 1500, 1450, 1600]
        >>> vo = calculate_volume_oscillator(volumes, 3, 5)
        >>> vo[-1]
        7.14
    
    特点:
        - 百分比形式的成交量变化
        - 正值为成交量放大
        - 负值为成交量萎缩
    """
    if not volumes:
        return []
    
    max_period = max(short_period, long_period)
    n = len(volumes)
    
    if n < max_period:
        return [None] * n
    
    # 计算短期和长期成交量均线
    short_ma = calculate_volume_ma(volumes, short_period)
    long_ma = calculate_volume_ma(volumes, long_period)
    
    # 计算震荡指标
    oscillator_values = [None] * max_period
    
    for i in range(max_period, n):
        if short_ma[i] is not None and long_ma[i] is not None:
            if long_ma[i] == 0:
                vo = 0.0
            else:
                vo = ((short_ma[i] - long_ma[i]) / long_ma[i]) * 100
            oscillator_values.append(float(vo))
        else:
            oscillator_values.append(None)
    
    return oscillator_values

def identify_volume_signals(
    close_prices: List[float],
    volumes: List[float],
    price_period: int = 20,
    volume_period: int = 20
) -> Dict[str, Any]:
    """
    识别成交量信号
    
    参数:
        close_prices (List[float]): 收盘价序列
        volumes (List[float]): 成交量序列
        price_period (int): 价格分析周期
        volume_period (int): 成交量分析周期
    
    返回:
        Dict: 包含成交量分析结果:
            - volume_ma: 成交量均线值
            - volume_ratio: 成交量比率
            - price_trend: 价格趋势
            - volume_trend: 成交量趋势
            - confirmation: 量价确认信号
            - divergence: 量价背离信号
    
    示例:
        >>> closes = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109]
        >>> volumes = [1000, 1200, 1100, 1300, 1400, 1250, 1350, 1500, 1450, 1600]
        >>> signals = identify_volume_signals(closes, volumes, 5, 5)
        >>> signals['confirmation']
        'confirmed' 或 'divergence'
    """
    if not close_prices or not volumes:
        return {
            "volume_ma": None,
            "volume_ratio": None,
            "price_trend": "unknown",
            "volume_trend": "unknown",
            "confirmation": "unknown",
            "divergence": "none"
        }
    
    n = len(close_prices)
    if n != len(volumes):
        raise ValueError("收盘价和成交量序列长度必须相同")
    
    if n < max(price_period, volume_period):
        return {
            "volume_ma": None,
            "volume_ratio": None,
            "price_trend": "unknown",
            "volume_trend": "unknown",
            "confirmation": "unknown",
            "divergence": "none"
        }
    
    # 计算价格趋势 (使用简单斜率)
    price_trend = "sideways"
    if n >= price_period:
        recent_prices = close_prices[-price_period:]
        if len(recent_prices