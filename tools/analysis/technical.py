#!/usr/bin/env python3
"""
技术分析工具

职责: 执行技术分析，包括趋势分析、动量分析、波动率分析等

主要功能:
- 趋势分析: 识别趋势方向、强度、阶段
- 动量分析: 分析价格变化的速度和强度
- 波动率分析: 分析价格波动程度
- 形态识别: 识别技术形态
- 信号生成: 生成交易信号
- 多时间框架分析: 跨时间框架分析

分析类型:
1. 趋势分析: 识别市场趋势
2. 动量分析: 分析价格动能
3. 波动率分析: 分析市场波动
4. 成交量分析: 分析交易活跃度
5. 综合分析: 多维度综合分析

版本: 1.0.0
作者: 量化团队
更新日期: 2026-04-19
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import warnings

# 导入指标工具
from ..indicators import (
    calculate_ema, calculate_macd, calculate_rsi,
    calculate_bollinger_bands, calculate_atr,
    calculate_stochastic, calculate_cci
)

class TrendDirection(Enum):
    """趋势方向"""
    STRONG_UP = "strong_up"      # 强势上涨
    MODERATE_UP = "moderate_up"  # 温和上涨
    SIDEWAYS = "sideways"        # 横盘整理
    MODERATE_DOWN = "moderate_down"  # 温和下跌
    STRONG_DOWN = "strong_down"  # 强势下跌

class MarketPhase(Enum):
    """市场阶段"""
    ACCUMULATION = "accumulation"  # 吸筹阶段
    UPTREND = "uptrend"           # 上升趋势
    DISTRIBUTION = "distribution"  # 派发阶段
    DOWNTREND = "downtrend"       # 下降趋势
    CONSOLIDATION = "consolidation"  # 盘整阶段

class SignalType(Enum):
    """信号类型"""
    STRONG_BUY = "strong_buy"     # 强烈买入
    BUY = "buy"                   # 买入
    NEUTRAL = "neutral"           # 中性
    SELL = "sell"                 # 卖出
    STRONG_SELL = "strong_sell"   # 强烈卖出

@dataclass
class TrendAnalysis:
    """趋势分析结果"""
    direction: TrendDirection
    strength: float  # 0-1，趋势强度
    phase: MarketPhase
    ema_alignment: Dict[str, Any]  # 均线排列
    macd_signal: str  # MACD信号
    adx_strength: Optional[float] = None  # ADX强度
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "direction": self.direction.value,
            "strength": round(self.strength, 3),
            "phase": self.phase.value,
            "ema_alignment": self.ema_alignment,
            "macd_signal": self.macd_signal,
            "adx_strength": self.adx_strength
        }

@dataclass
class MomentumAnalysis:
    """动量分析结果"""
    rsi_value: float
    rsi_signal: str  # oversold/overbought/neutral
    stochastic_k: float
    stochastic_d: float
    stochastic_signal: str  # bullish/bearish
    cci_value: float
    cci_signal: str  # oversold/overbought/neutral
    momentum_value: float
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "rsi_value": round(self.rsi_value, 2),
            "rsi_signal": self.rsi_signal,
            "stochastic_k": round(self.stochastic_k, 2),
            "stochastic_d": round(self.stochastic_d, 2),
            "stochastic_signal": self.stochastic_signal,
            "cci_value": round(self.cci_value, 2),
            "cci_signal": self.cci_signal,
            "momentum_value": round(self.momentum_value, 2)
        }

@dataclass
class VolatilityAnalysis:
    """波动率分析结果"""
    atr_value: float
    atr_percent: float  # ATR占价格百分比
    bollinger_width: float  # 布林带宽度
    bollinger_position: str  # upper/middle/lower
    volatility_regime: str  # high/low/normal
    historical_volatility: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "atr_value": round(self.atr_value, 2),
            "atr_percent": round(self.atr_percent, 3),
            "bollinger_width": round(self.bollinger_width, 2),
            "bollinger_position": self.bollinger_position,
            "volatility_regime": self.volatility_regime,
            "historical_volatility": self.historical_volatility
        }

@dataclass
class VolumeAnalysis:
    """成交量分析结果"""
    volume_trend: str  # increasing/decreasing/stable
    volume_ma_ratio: float  # 成交量/均量比
    obv_trend: str  # rising/falling
    volume_confirmation: bool  # 量价是否确认
    volume_climax: Optional[bool] = None  # 是否量能高潮
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "volume_trend": self.volume_trend,
            "volume_ma_ratio": round(self.volume_ma_ratio, 2),
            "obv_trend": self.obv_trend,
            "volume_confirmation": self.volume_confirmation,
            "volume_climax": self.volume_climax
        }

@dataclass
class TechnicalSignal:
    """技术信号"""
    signal_type: SignalType
    confidence: float  # 0-1，信号置信度
    reasons: List[str]  # 信号原因
    timeframe: str  # 时间框架
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "signal_type": self.signal_type.value,
            "confidence": round(self.confidence, 3),
            "reasons": self.reasons,
            "timeframe": self.timeframe,
            "timestamp": self.timestamp
        }

@dataclass
class TechnicalAnalysisReport:
    """技术分析报告"""
    symbol: str
    timeframe: str
    timestamp: str
    current_price: float
    trend_analysis: TrendAnalysis
    momentum_analysis: MomentumAnalysis
    volatility_analysis: VolatilityAnalysis
    volume_analysis: VolumeAnalysis
    signals: List[TechnicalSignal]
    summary: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "timestamp": self.timestamp,
            "current_price": round(self.current_price, 2),
            "trend_analysis": self.trend_analysis.to_dict(),
            "momentum_analysis": self.momentum_analysis.to_dict(),
            "volatility_analysis": self.volatility_analysis.to_dict(),
            "volume_analysis": self.volume_analysis.to_dict(),
            "signals": [signal.to_dict() for signal in self.signals],
            "summary": self.summary
        }
    
    def to_json(self, indent: int = 2) -> str:
        """转换为JSON字符串"""
        import json
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    def print_summary(self):
        """打印摘要"""
        print("=" * 70)
        print(f"📊 技术分析报告: {self.symbol} ({self.timeframe})")
        print("=" * 70)
        print(f"📅 分析时间: {self.timestamp}")
        print(f"💰 当前价格: ${self.current_price:,.2f}")
        print()
        
        # 趋势分析
        trend = self.trend_analysis
        print(f"📈 趋势分析:")
        print(f"  方向: {trend.direction.value}")
        print(f"  强度: {trend.strength:.1%}")
        print(f"  阶段: {trend.phase.value}")
        print(f"  MACD信号: {trend.macd_signal}")
        print()
        
        # 动量分析
        momentum = self.momentum_analysis
        print(f"⚡ 动量分析:")
        print(f"  RSI: {momentum.rsi_value:.1f} ({momentum.rsi_signal})")
        print(f"  随机指标: K={momentum.stochastic_k:.1f}, D={momentum.stochastic_d:.1f}")
        print(f"  CCI: {momentum.cci_value:.1f} ({momentum.cci_signal})")
        print()
        
        # 波动率分析
        volatility = self.volatility_analysis
        print(f"📊 波动率分析:")
        print(f"  ATR: {volatility.atr_value:.2f} ({volatility.atr_percent:.1%})")
        print(f"  布林带位置: {volatility.bollinger_position}")
        print(f"  波动率状态: {volatility.volatility_regime}")
        print()
        
        # 成交量分析
        volume = self.volume_analysis
        print(f"📈 成交量分析:")
        print(f"  成交量趋势: {volume.volume_trend}")
        print(f"  量比: {volume.volume_ma_ratio:.2f}")
        print(f"  OBV趋势: {volume.obv_trend}")
        print(f"  量价确认: {'✅' if volume.volume_confirmation else '❌'}")
        print()
        
        # 信号
        if self.signals:
            print(f"🚦 技术信号:")
            for signal in self.signals:
                emoji = {
                    "strong_buy": "🟢",
                    "buy": "🟡",
                    "neutral": "⚪",
                    "sell": "🟠",
                    "strong_sell": "🔴"
                }.get(signal.signal_type.value, "⚪")
                
                print(f"  {emoji} {signal.signal_type.value.upper()} (置信度: {signal.confidence:.1%})")
                for reason in signal.reasons[:2]:  # 显示前两个原因
                    print(f"    • {reason}")
            print()
        
        print("=" * 70)

class TechnicalAnalyzer:
    """技术分析器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化技术分析器
        
        参数:
            config: 配置字典
        """
        self.config = config or self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """默认配置"""
        return {
            # 趋势分析配置
            "trend_ema_periods": [7, 12, 25, 50],
            "macd_fast": 12,
            "macd_slow": 26,
            "macd_signal": 9,
            
            # 动量分析配置
            "rsi_period": 14,
            "stochastic_k_period": 14,
            "stochastic_d_period": 3,
            "cci_period": 20,
            
            # 波动率分析配置
            "bollinger_period": 20,
            "bollinger_std": 2.0,
            "atr_period": 14,
            
            # 成交量分析配置
            "volume_ma_period": 20,
            
            # 信号阈值
            "rsi_oversold": 30,
            "rsi_overbought": 70,
            "stochastic_oversold": 20,
            "stochastic_overbought": 80,
            "cci_oversold": -100,
            "cci_overbought": 100
        }
    
    def analyze(
        self,
        df: pd.DataFrame,
        symbol: str = "BTCUSDT",
        timeframe: str = "4h"
    ) -> TechnicalAnalysisReport:
        """
        执行技术分析
        
        参数:
            df: 包含价格数据的DataFrame
            symbol: 交易对符号
            timeframe: 时间框架
        
        返回:
            TechnicalAnalysisReport: 技术分析报告
        """
        if df.empty or len(df) < 50:
            raise ValueError("数据不足，至少需要50个数据点")
        
        # 提取价格序列
        closes = df['close'].values if 'close' in df.columns else df.iloc[:, -1].values
        highs = df['high'].values if 'high' in df.columns else closes
        lows = df['low'].values if 'low' in df.columns else closes
        volumes = df['volume'].values if 'volume' in df.columns else None
        
        current_price = closes[-1]
        
        # 1. 趋势分析
        trend_analysis = self._analyze_trend(closes, highs, lows)
        
        # 2. 动量分析
        momentum_analysis = self._analyze_momentum(closes, highs, lows)
        
        # 3. 波动率分析
        volatility_analysis = self._analyze_volatility(closes, highs, lows)
        
        # 4. 成交量分析
        volume_analysis = self._analyze_volume(closes, volumes) if volumes is not None else None
        
        # 5. 生成信号
        signals = self._generate_signals(
            trend_analysis, momentum_analysis,
            volatility_analysis, volume_analysis,
            timeframe
        )
        
        # 6. 生成报告
        return TechnicalAnalysisReport(
            symbol=symbol,
            timeframe=timeframe,
            timestamp=datetime.now().isoformat(),
            current_price=current_price,
            trend_analysis=trend_analysis,
            momentum_analysis=momentum_analysis,
            volatility_analysis=volatility_analysis,
            volume_analysis=volume_analysis or VolumeAnalysis(
                volume_trend="unknown",
                volume_ma_ratio=1.0,
                obv_trend="unknown",
                volume_confirmation=False
            ),
            signals=signals,
            summary=self._generate_summary(
                trend_analysis, momentum_analysis,
                volatility_analysis, signals
            )
        )
    
    def _analyze_trend(
        self,
        closes: np.ndarray,
        highs: np.ndarray,
        lows: np.ndarray
    ) -> TrendAnalysis:
        """分析趋势"""
        # 计算EMA
        ema_values = {}
        for period in self.config["trend_ema_periods"]:
            ema = calculate_ema(list(closes), period)
            if ema and ema[-1] is not None:
                ema_values[f"ema{period}"] = ema[-1]
        
        # 分析均线排列
        ema_alignment = self._analyze_ema_alignment(ema_values)
        
        # 计算MACD
        macd_data = calculate_macd(
            list(closes),
            fast_period=self.config["macd_fast"],
            slow_period=self.config["macd_slow"],
            signal_period=self.config["macd_signal"]
        )
        
        macd_line = macd_data["macd_line"]
        signal_line = macd_data["signal_line"]
        
        # 分析MACD信号
        if macd_line[-1] is not None and signal_line[-1] is not None:
            if macd_line[-1] > signal_line[-1]:
                macd_signal = "bullish"
            else:
                macd_signal = "bearish"
        else:
            macd_signal = "neutral"
        
        # 判断趋势方向和强度
        direction, strength = self._determine_trend_direction(
            closes, ema_values, macd_line, signal_line
        )
        
        # 判断市场阶段
        phase = self._determine_market_phase(
            direction, strength, ema_alignment, macd_signal
        )
        
        return TrendAnalysis(
            direction=direction,
            strength=strength,
            phase=phase,
            ema_alignment=ema_alignment,
            macd_signal=macd_signal,
            adx_strength=None  # 可以后续添加ADX计算
        )
    
    def _analyze_ema_alignment(self, ema_values: Dict[str, float]) -> Dict[str, Any]:
        """分析均线排列"""
        if not ema_values:
            return {"alignment": "unknown", "details": {}}
        
        # 按周期排序
        sorted_emas = sorted(
            [(int(k[3:]), v) for k, v in ema_values.items()],
            key=lambda x: x[0]
        )
        
        periods = [p for p, _ in sorted_emas]
        values = [v for _, v in sorted_emas]
        
        # 判断排列
        if all(values[i] < values[i+1] for i in range(len(values)-1)):
            alignment = "bullish"  # 多头排列
        elif all(values[i] > values[i+1] for i in range(len(values)-1)):
            alignment = "bearish"  # 空头排列
        else:
            alignment = "mixed"  # 混合排列
        
        # 计算均线间距
        spacing = {}
        for i in range(len(values)-1):
            diff = values[i+1] - values[i]
            spacing[f"{periods[i]}-{periods[i+1