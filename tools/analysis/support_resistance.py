#!/usr/bin/env python3
"""
支撑阻力分析工具

职责: 识别和分析支撑阻力位，包括技术位和心理位

主要功能:
- 技术支撑阻力: 基于技术指标
- 心理支撑阻力: 基于整数关口
- 动态支撑阻力: 基于移动平均线
- 多时间框架支撑阻力: 跨时间框架分析
- 支撑阻力强度评估: 评估位位的可靠性
- 突破分析: 分析突破信号

支撑阻力类型:
1. 技术位: 前期高低点、趋势线、形态颈线
2. 心理位: 整数关口、重要价格水平
3. 动态位: 移动平均线、布林带
4. 斐波那契位: 回调位、扩展位
5. 枢纽点: 日内交易枢纽点

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

class LevelType(Enum):
    """支撑阻力位类型"""
    SUPPORT = "support"          # 支撑位
    RESISTANCE = "resistance"    # 阻力位
    PSYCHOLOGICAL = "psychological"  # 心理位
    DYNAMIC = "dynamic"          # 动态位
    FIBONACCI = "fibonacci"      # 斐波那契位
    PIVOT = "pivot"              # 枢纽点

class StrengthLevel(Enum):
    """强度等级"""
    WEAK = "weak"                # 弱
    MODERATE = "moderate"        # 中等
    STRONG = "strong"            # 强
    VERY_STRONG = "very_strong"  # 非常强

class BreakoutType(Enum):
    """突破类型"""
    BREAKOUT = "breakout"        # 向上突破
    BREAKDOWN = "breakdown"      # 向下跌破
    FALSE_BREAKOUT = "false_breakout"  # 假突破
    TESTING = "testing"          # 测试中

@dataclass
class SupportResistanceLevel:
    """支撑阻力位"""
    level_type: LevelType
    price: float
    strength: StrengthLevel
    confidence: float  # 0-1，置信度
    reasons: List[str]  # 形成原因
    timeframe: str  # 识别的时间框架
    first_touched: Optional[str] = None  # 首次触及时间
    last_tested: Optional[str] = None  # 最后测试时间
    test_count: int = 0  # 测试次数
    holding: bool = True  # 是否仍然有效
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "level_type": self.level_type.value,
            "price": round(self.price, 2),
            "strength": self.strength.value,
            "confidence": round(self.confidence, 3),
            "reasons": self.reasons,
            "timeframe": self.timeframe,
            "first_touched": self.first_touched,
            "last_tested": self.last_tested,
            "test_count": self.test_count,
            "holding": self.holding
        }

@dataclass
class BreakoutAnalysis:
    """突破分析"""
    breakout_type: BreakoutType
    level: SupportResistanceLevel
    price_at_breakout: float
    volume_at_breakout: Optional[float] = None
    confirmation: bool = False  # 是否确认突破
    retest_occurred: bool = False  # 是否回测
    retest_successful: Optional[bool] = None  # 回测是否成功
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "breakout_type": self.breakout_type.value,
            "level": self.level.to_dict(),
            "price_at_breakout": round(self.price_at_breakout, 2),
            "volume_at_breakout": self.volume_at_breakout,
            "confirmation": self.confirmation,
            "retest_occurred": self.retest_occurred,
            "retest_successful": self.retest_successful
        }

@dataclass
class SupportResistanceReport:
    """支撑阻力分析报告"""
    symbol: str
    timeframe: str
    timestamp: str
    current_price: float
    support_levels: List[SupportResistanceLevel]
    resistance_levels: List[SupportResistanceLevel]
    nearest_support: Optional[SupportResistanceLevel] = None
    nearest_resistance: Optional[SupportResistanceLevel] = None
    breakout_analysis: Optional[BreakoutAnalysis] = None
    summary: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "timestamp": self.timestamp,
            "current_price": round(self.current_price, 2),
            "support_levels": [level.to_dict() for level in self.support_levels],
            "resistance_levels": [level.to_dict() for level in self.resistance_levels],
            "nearest_support": self.nearest_support.to_dict() if self.nearest_support else None,
            "nearest_resistance": self.nearest_resistance.to_dict() if self.nearest_resistance else None,
            "breakout_analysis": self.breakout_analysis.to_dict() if self.breakout_analysis else None,
            "summary": self.summary
        }
    
    def to_json(self, indent: int = 2) -> str:
        """转换为JSON字符串"""
        import json
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    def print_summary(self):
        """打印摘要"""
        print("=" * 70)
        print(f"📊 支撑阻力分析: {self.symbol} ({self.timeframe})")
        print("=" * 70)
        print(f"📅 分析时间: {self.timestamp}")
        print(f"💰 当前价格: ${self.current_price:,.2f}")
        print()
        
        # 最近的支撑阻力
        if self.nearest_support:
            support = self.nearest_support
            distance = (self.current_price - support.price) / self.current_price * 100
            print(f"📉 最近支撑: ${support.price:,.2f}")
            print(f"   距离: {distance:+.1f}%")
            print(f"   强度: {support.strength.value}")
            print(f"   置信度: {support.confidence:.1%}")
            if support.reasons:
                print(f"   原因: {support.reasons[0]}")
            print()
        
        if self.nearest_resistance:
            resistance = self.nearest_resistance
            distance = (resistance.price - self.current_price) / self.current_price * 100
            print(f"📈 最近阻力: ${resistance.price:,.2f}")
            print(f"   距离: {distance:+.1f}%")
            print(f"   强度: {resistance.strength.value}")
            print(f"   置信度: {resistance.confidence:.1%}")
            if resistance.reasons:
                print(f"   原因: {resistance.reasons[0]}")
            print()
        
        # 支撑位列表
        if self.support_levels:
            print(f"📋 支撑位列表 ({len(self.support_levels)} 个):")
            for i, level in enumerate(self.support_levels[:5], 1):  # 显示前5个
                distance = (self.current_price - level.price) / self.current_price * 100
                print(f"  {i}. ${level.price:,.2f} ({distance:+.1f}%) - {level.strength.value}")
            if len(self.support_levels) > 5:
                print(f"  ... 还有 {len(self.support_levels) - 5} 个支撑位")
            print()
        
        # 阻力位列表
        if self.resistance_levels:
            print(f"📋 阻力位列表 ({len(self.resistance_levels)} 个):")
            for i, level in enumerate(self.resistance_levels[:5], 1):  # 显示前5个
                distance = (level.price - self.current_price) / self.current_price * 100
                print(f"  {i}. ${level.price:,.2f} ({distance:+.1f}%) - {level.strength.value}")
            if len(self.resistance_levels) > 5:
                print(f"  ... 还有 {len(self.resistance_levels) - 5} 个阻力位")
            print()
        
        # 突破分析
        if self.breakout_analysis:
            breakout = self.breakout_analysis
            print(f"🚀 突破分析:")
            print(f"   类型: {breakout.breakout_type.value}")
            print(f"   价格: ${breakout.price_at_breakout:,.2f}")
            print(f"   确认: {'✅' if breakout.confirmation else '❌'}")
            if breakout.retest_occurred:
                print(f"   回测: {'✅ 成功' if breakout.retest_successful else '❌ 失败'}")
            print()
        
        print("=" * 70)

class SupportResistanceAnalyzer:
    """支撑阻力分析器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化支撑阻力分析器
        
        参数:
            config: 配置字典
        """
        self.config = config or self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """默认配置"""
        return {
            # 技术位配置
            "swing_lookback": 20,  # 摆动点回溯周期
            "swing_min_distance": 0.02,  # 摆动点最小距离 (2%)
            
            # 心理位配置
            "psychological_intervals": [100, 500, 1000, 5000, 10000],
            
            # 动态位配置
            "ema_periods": [7, 12, 25, 50, 100, 200],
            "bollinger_period": 20,
            "bollinger_std": 2.0,
            
            # 斐波那契配置
            "fibonacci_levels": [0.236, 0.382, 0.5, 0.618, 0.786],
            
            # 强度评估配置
            "confluence_bonus": 0.2,  # 多时间框架重合奖励
            "test_count_bonus": 0.1,  # 测试次数奖励
            "time_decay_factor": 0.1,  # 时间衰减因子
            
            # 突破分析配置
            "breakout_threshold": 0.01,  # 突破阈值 (1%)
            "confirmation_candles": 3,  # 确认蜡烛数
            "volume_multiplier": 1.5,  # 突破成交量倍数
        }
    
    def analyze(
        self,
        df: pd.DataFrame,
        symbol: str = "BTCUSDT",
        timeframe: str = "4h",
        multi_timeframe_data: Optional[Dict[str, pd.DataFrame]] = None
    ) -> SupportResistanceReport:
        """
        分析支撑阻力位
        
        参数:
            df: 当前时间框架数据
            symbol: 交易对符号
            timeframe: 当前时间框架
            multi_timeframe_data: 多时间框架数据 {timeframe: df}
        
        返回:
            SupportResistanceReport: 支撑阻力分析报告
        """
        if df.empty or len(df) < 50:
            raise ValueError("数据不足，至少需要50个数据点")
        
        current_price = df['close'].iloc[-1] if 'close' in df.columns else df.iloc[-1, -1]
        
        # 1. 识别支撑阻力位
        support_levels = []
        resistance_levels = []
        
        # 技术位 (前期高低点)
        technical_levels = self._identify_technical_levels(df)
        support_levels.extend([l for l in technical_levels if l.level_type == LevelType.SUPPORT])
        resistance_levels.extend([l for l in technical_levels if l.level_type == LevelType.RESISTANCE])
        
        # 心理位 (整数关口)
        psychological_levels = self._identify_psychological_levels(current_price)
        support_levels.extend([l for l in psychological_levels if l.level_type == LevelType.SUPPORT])
        resistance_levels.extend([l for l in psychological_levels if l.level_type == LevelType.RESISTANCE])
        
        # 动态位 (移动平均线)
        dynamic_levels = self._identify_dynamic_levels(df)
        support_levels.extend([l for l in dynamic_levels if l.level_type == LevelType.SUPPORT])
        resistance_levels.extend([l for l in dynamic_levels if l.level_type == LevelType.RESISTANCE])
        
        # 2. 多时间框架分析 (如果提供)
        if multi_timeframe_data:
            self._apply_multi_timeframe_analysis(
                support_levels, resistance_levels,
                multi_timeframe_data, timeframe
            )
        
        # 3. 评估强度
        self._evaluate_level_strength(support_levels, df, current_price)
        self._evaluate_level_strength(resistance_levels, df, current_price)
        
        # 4. 排序和过滤
        support_levels = self._sort_and_filter_levels(support_levels, current_price, is_support=True)
        resistance_levels = self._sort_and_filter_levels(resistance_levels, current_price, is_support=False)
        
        # 5. 找到最近的支撑阻力
        nearest_support = self._find_nearest_level(support_levels, current_price, is_support=True)
        nearest_resistance = self._find_nearest_level(resistance_levels, current_price, is_support=False)
        
        # 6. 突破分析
        breakout_analysis = self._analyze_breakouts(df, support_levels, resistance_levels)
        
        # 7. 生成报告
        return SupportResistanceReport(
            symbol=symbol,
            timeframe=timeframe,
            timestamp=datetime.now().isoformat(),
            current_price=current_price,
            support_levels=support_levels,
            resistance_levels=resistance_levels,
            nearest_support=nearest_support,
            nearest_resistance=nearest_resistance,
            breakout_analysis=breakout_analysis,
            summary=self._generate_summary(
                support_levels, resistance_levels,
                nearest_support, nearest_resistance,
                breakout_analysis
            )
        )
    
    def _identify_technical_levels(self, df: pd.DataFrame) -> List[SupportResistanceLevel]:
        """识别技术支撑阻力位 (前期高低点)"""
        levels = []
        
        if len(df) < self.config["swing_lookback"] * 2:
            return levels
        
        # 提取价格
        highs = df['high'].values if 'high' in df.columns else df['close'].values
        lows = df['low'].values if 'low' in df.columns else df['close'].values
        
        # 识别摆动高点 (阻力位)
        for i in range(self.config["swing_lookback"], len(highs) - self.config["swing_lookback"]):
            # 检查是否是局部高点
            window_start = i - self.config["swing_lookback"]
            window_end = i + self.config["swing_lookback"]
            
            if highs[i] == max(highs[window_start:window_end]):
                # 检查是否足够显著
                is_significant = True
                for level in levels:
                    if level.level_type == LevelType.RESISTANCE:
                        price_diff = abs(highs[i] - level.price) / level.price
                        if price_diff < self.config["swing_min_distance"]:
                            is_significant = False
                            break
                
                if is_significant:
                    level = SupportResistanceLevel(
                        level_type=LevelType.RESISTANCE,
                        price=float(highs[i]),
                        strength=StrengthLevel.MODERATE,
                        confidence=0.7,
                        reasons=["前期摆动高点"],
                        timeframe="current",
                        first_touched=df.index[i].isoformat() if hasattr(df.index[i], 'isoformat') else str(df.index[i]),
                        test_count=1
                    )
                    levels.append(level)
        
        # 识别摆动低点 (支撑位)
        for i in range(self.config["swing_lookback"], len(lows) - self.config["swing_lookback"]):
            # 检查是否是局部低点
            window_start = i - self.config["swing_lookback"]
            window_end = i + self.config["swing_lookback"]
            
            if lows[i] == min(lows[window_start:window_end]):
                # 检查是否足够显著
                is_significant = True
                for level in levels:
                    if level.level_type == LevelType.SUPPORT:
                        price_diff = abs(lows[i] - level.price) / level.price
                        if price_diff < self.config["swing_min_distance"]:
                            is_significant = False
                            break
                
                if is_significant:
                    level = SupportResistanceLevel(
                        level_type=LevelType.SUPPORT,
                        price=float(lows[i]),
                        strength=StrengthLevel.MODERATE,
                        confidence=0.7,
                        reasons=["前期摆动低点"],
                        timeframe="current",
                        first_touched=df.index[i].isoformat() if hasattr(df.index[i], 'isoformat') else str(df.index[i]),
                        test_count=1
                    )
                    levels