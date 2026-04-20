#!/usr/bin/env python3
"""
模式识别工具

职责: 识别技术分析模式，包括反转模式、持续模式、蜡烛图模式

主要功能:
- 反转模式识别: 头肩顶底、双顶底、三重顶底
- 持续模式识别: 三角形、旗形、楔形、矩形
- 蜡烛图模式识别: 单根、双根、三根蜡烛模式
- 模式强度评估: 评估模式的可靠性
- 模式目标计算: 计算模式目标价位
- 多时间框架模式: 跨时间框架模式识别

模式类型:
1. 反转模式: 预示趋势反转
2. 持续模式: 预示趋势延续
3. 蜡烛模式: 短期价格行为
4. 图表模式: 基于价格形态
5. 谐波模式: 基于斐波那契比例

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

class PatternType(Enum):
    """模式类型"""
    REVERSAL = "reversal"        # 反转模式
    CONTINUATION = "continuation"  # 持续模式
    CANDLESTICK = "candlestick"  # 蜡烛图模式
    CHART = "chart"              # 图表模式
    HARMONIC = "harmonic"        # 谐波模式

class PatternDirection(Enum):
    """模式方向"""
    BULLISH = "bullish"          # 看涨
    BEARISH = "bearish"          # 看跌
    NEUTRAL = "neutral"          # 中性

class PatternStatus(Enum):
    """模式状态"""
    FORMING = "forming"          # 形成中
    COMPLETE = "complete"        # 已完成
    CONFIRMED = "confirmed"      # 已确认
    INVALID = "invalid"          # 已失效

@dataclass
class Pattern:
    """技术模式"""
    pattern_type: PatternType
    pattern_name: str
    direction: PatternDirection
    status: PatternStatus
    confidence: float  # 0-1，置信度
    points: Dict[str, float]  # 关键点价格
    timeframe: str
    detected_at: str
    completion_time: Optional[str] = None
    confirmation_time: Optional[str] = None
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    risk_reward_ratio: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "pattern_type": self.pattern_type.value,
            "pattern_name": self.pattern_name,
            "direction": self.direction.value,
            "status": self.status.value,
            "confidence": round(self.confidence, 3),
            "points": {k: round(v, 2) for k, v in self.points.items()},
            "timeframe": self.timeframe,
            "detected_at": self.detected_at,
            "completion_time": self.completion_time,
            "confirmation_time": self.confirmation_time,
            "target_price": round(self.target_price, 2) if self.target_price else None,
            "stop_loss": round(self.stop_loss, 2) if self.stop_loss else None,
            "risk_reward_ratio": round(self.risk_reward_ratio, 2) if self.risk_reward_ratio else None
        }

@dataclass
class CandlestickPattern:
    """蜡烛图模式"""
    pattern_name: str
    direction: PatternDirection
    confidence: float
    candles: List[Dict[str, Any]]  # 蜡烛数据
    detected_at: str
    volume_confirmation: bool = False
    trend_alignment: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "pattern_name": self.pattern_name,
            "direction": self.direction.value,
            "confidence": round(self.confidence, 3),
            "candles_count": len(self.candles),
            "detected_at": self.detected_at,
            "volume_confirmation": self.volume_confirmation,
            "trend_alignment": self.trend_alignment
        }

@dataclass
class PatternAnalysisReport:
    """模式分析报告"""
    symbol: str
    timeframe: str
    timestamp: str
    current_price: float
    patterns: List[Pattern]
    candlestick_patterns: List[CandlestickPattern]
    active_patterns: List[Pattern]
    completed_patterns: List[Pattern]
    summary: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "timestamp": self.timestamp,
            "current_price": round(self.current_price, 2),
            "patterns": [pattern.to_dict() for pattern in self.patterns],
            "candlestick_patterns": [cp.to_dict() for cp in self.candlestick_patterns],
            "active_patterns": [pattern.to_dict() for pattern in self.active_patterns],
            "completed_patterns": [pattern.to_dict() for pattern in self.completed_patterns],
            "summary": self.summary
        }
    
    def to_json(self, indent: int = 2) -> str:
        """转换为JSON字符串"""
        import json
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    def print_summary(self):
        """打印摘要"""
        print("=" * 70)
        print(f"📊 模式识别分析: {self.symbol} ({self.timeframe})")
        print("=" * 70)
        print(f"📅 分析时间: {self.timestamp}")
        print(f"💰 当前价格: ${self.current_price:,.2f}")
        print()
        
        # 活跃模式
        if self.active_patterns:
            print(f"🔄 活跃模式 ({len(self.active_patterns)} 个):")
            for pattern in self.active_patterns[:3]:  # 显示前3个
                emoji = "🟢" if pattern.direction == PatternDirection.BULLISH else "🔴"
                print(f"  {emoji} {pattern.pattern_name} ({pattern.status.value})")
                print(f"     方向: {pattern.direction.value}")
                print(f"     置信度: {pattern.confidence:.1%}")
                if pattern.target_price:
                    distance = (pattern.target_price - self.current_price) / self.current_price * 100
                    print(f"     目标: ${pattern.target_price:,.2f} ({distance:+.1f}%)")
            if len(self.active_patterns) > 3:
                print(f"  ... 还有 {len(self.active_patterns) - 3} 个活跃模式")
            print()
        
        # 已完成模式
        if self.completed_patterns:
            print(f"✅ 已完成模式 ({len(self.completed_patterns)} 个):")
            for pattern in self.completed_patterns[:3]:  # 显示前3个
                emoji = "🟢" if pattern.direction == PatternDirection.BULLISH else "🔴"
                print(f"  {emoji} {pattern.pattern_name}")
                print(f"     方向: {pattern.direction.value}")
                print(f"     完成时间: {pattern.completion_time}")
            if len(self.completed_patterns) > 3:
                print(f"  ... 还有 {len(self.completed_patterns) - 3} 个已完成模式")
            print()
        
        # 蜡烛图模式
        if self.candlestick_patterns:
            print(f"🕯️  蜡烛图模式 ({len(self.candlestick_patterns)} 个):")
            for cp in self.candlestick_patterns[:5]:  # 显示前5个
                emoji = "🟢" if cp.direction == PatternDirection.BULLISH else "🔴"
                print(f"  {emoji} {cp.pattern_name}")
                print(f"     方向: {cp.direction.value}")
                print(f"     置信度: {cp.confidence:.1%}")
                print(f"     量价确认: {'✅' if cp.volume_confirmation else '❌'}")
            if len(self.candlestick_patterns) > 5:
                print(f"  ... 还有 {len(self.candlestick_patterns) - 5} 个蜡烛图模式")
            print()
        
        # 模式统计
        stats = self.summary.get("pattern_statistics", {})
        if stats:
            print(f"📊 模式统计:")
            for key, value in stats.items():
                if isinstance(value, (int, float)):
                    print(f"  {key}: {value}")
            print()
        
        print("=" * 70)

class PatternRecognizer:
    """模式识别器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化模式识别器
        
        参数:
            config: 配置字典
        """
        self.config = config or self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """默认配置"""
        return {
            # 反转模式配置
            "head_shoulders_min_swings": 5,
            "double_top_bottom_min_distance": 0.03,  # 3%
            "triple_top_bottom_min_distance": 0.02,  # 2%
            
            # 持续模式配置
            "triangle_min_swings": 4,
            "flag_pole_min_ratio": 0.5,  # 旗杆至少是旗形的50%
            "wedge_min_swings": 5,
            
            # 蜡烛图模式配置
            "doji_max_body_ratio": 0.1,  # 十字星最大实体比例
            "hammer_min_shadow_ratio": 2.0,  # 锤子线最小影线比例
            "engulfing_min_body_ratio": 1.5,  # 吞没形态最小实体比例
            "morning_star_max_gap_ratio": 0.01,  # 早晨之星最大缺口比例
            
            # 模式确认配置
            "confirmation_candles": 3,
            "volume_confirmation_ratio": 1.5,  # 确认成交量倍数
            "pattern_completion_threshold": 0.01,  # 模式完成阈值 (1%)
            
            # 目标计算配置
            "head_shoulders_target_ratio": 1.0,  # 头肩形态目标比例
            "double_top_bottom_target_ratio": 1.0,  # 双顶底目标比例
            "triangle_target_ratio": 1.0,  # 三角形目标比例
            "flag_target_ratio": 1.0,  # 旗形目标比例
        }
    
    def analyze(
        self,
        df: pd.DataFrame,
        symbol: str = "BTCUSDT",
        timeframe: str = "4h"
    ) -> PatternAnalysisReport:
        """
        分析技术模式
        
        参数:
            df: 价格数据DataFrame
            symbol: 交易对符号
            timeframe: 时间框架
        
        返回:
            PatternAnalysisReport: 模式分析报告
        """
        if df.empty or len(df) < 100:
            raise ValueError("数据不足，至少需要100个数据点进行模式分析")
        
        current_price = df['close'].iloc[-1] if 'close' in df.columns else df.iloc[-1, -1]
        
        # 1. 识别图表模式
        patterns = self._identify_chart_patterns(df, timeframe)
        
        # 2. 识别蜡烛图模式
        candlestick_patterns = self._identify_candlestick_patterns(df, timeframe)
        
        # 3. 更新模式状态
        active_patterns = []
        completed_patterns = []
        
        for pattern in patterns:
            updated_pattern = self._update_pattern_status(pattern, df)
            if updated_pattern.status == PatternStatus.COMPLETE or updated_pattern.status == PatternStatus.CONFIRMED:
                completed_patterns.append(updated_pattern)
            elif updated_pattern.status == PatternStatus.FORMING:
                active_patterns.append(updated_pattern)
        
        # 4. 生成报告
        return PatternAnalysisReport(
            symbol=symbol,
            timeframe=timeframe,
            timestamp=datetime.now().isoformat(),
            current_price=current_price,
            patterns=patterns,
            candlestick_patterns=candlestick_patterns,
            active_patterns=active_patterns,
            completed_patterns=completed_patterns,
            summary=self._generate_summary(
                patterns, candlestick_patterns,
                active_patterns, completed_patterns
            )
        )
    
    def _identify_chart_patterns(self, df: pd.DataFrame, timeframe: str) -> List[Pattern]:
        """识别图表模式"""
        patterns = []
        
        # 提取价格数据
        highs = df['high'].values if 'high' in df.columns else df['close'].values
        lows = df['low'].values if 'low' in df.columns else df['close'].values
        closes = df['close'].values if 'close' in df.columns else df.iloc[:, -1].values
        
        # 识别头肩顶/底
        head_shoulders_patterns = self._identify_head_shoulders(highs, lows, closes, timeframe)
        patterns.extend(head_shoulders_patterns)
        
        # 识别双顶/底
        double_top_bottom_patterns = self._identify_double_top_bottom(highs, lows, closes, timeframe)
        patterns.extend(double_top_bottom_patterns)
        
        # 识别三角形
        triangle_patterns = self._identify_triangles(highs, lows, closes, timeframe)
        patterns.extend(triangle_patterns)
        
        # 识别旗形/楔形
        flag_wedge_patterns = self._identify_flags_wedges(highs, lows, closes, timeframe)
        patterns.extend(flag_wedge_patterns)
        
        return patterns
    
    def _identify_head_shoulders(self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, timeframe: str) -> List[Pattern]:
        """识别头肩形态"""
        patterns = []
        
        if len(highs) < self.config["head_shoulders_min_swings"] * 3:
            return patterns
        
        # 寻找潜在的头部和肩部
        swing_highs = self._find_swing_highs(highs, lookback=5)
        swing_lows = self._find_swing_lows(lows, lookback=5)
        
        # 识别头肩顶 (看跌反转)
        for i in range(2, len(swing_highs) - 2):
            # 检查左肩-头-右肩结构
            left_shoulder_idx = swing_highs[i-2]
            head_idx = swing_highs[i]
            right_shoulder_idx = swing_highs[i+2]
            
            # 检查颈线 (连接两个低点)
            neckline_start_idx = swing_lows[i-1] if i-1 < len(swing_lows) else None
            neckline_end_idx = swing_lows[i+1] if i+1 < len(swing_lows) else None
            
            if (left_shoulder_idx is not None and head_idx is not None and 
                right_shoulder_idx is not None and neckline_start_idx is not None and 
                neckline_end_idx is not None):
                
                left_shoulder_price = highs[left_shoulder_idx]
                head_price = highs[head_idx]
                right_shoulder_price = highs[right_shoulder_idx]
                neckline_start_price = lows[neckline_start_idx]
                neckline_end_price = lows[neckline_end_idx]
                
                # 检查头肩顶条件
                if (head_price > left_shoulder_price and head_price > right_shoulder_price and
                    abs(left_shoulder_price - right_shoulder_price) / head_price < 0.05 and  # 肩部大致对称
                    neckline_start_price < neckline_end_price):  # 颈线上倾 (头肩顶特征)
                    
                    # 计算目标价位
                    head_height = head_price - (neckline_start_price + neckline_end_price) / 2
                    target_price = (neckline_start_price + neckline_end_price) / 2 - head_height * self.config["head_shoulders_target_ratio"]
                    
                    pattern = Pattern(
                        pattern_type=PatternType.REVERSAL,
                        pattern_name="头肩顶",
                        direction=PatternDirection.BEARISH,
                        status=PatternStatus.FORMING,
                        confidence=0.7,
                        points={
                            "left_shoulder": left_shoulder_price,
                            "head": head_price,
                            "right_shoulder": right_shoulder_price,
                            "neckline_start": neckline_start_price,
                            "neckline_end": neckline_end_price
                        },
                        timeframe=timeframe,
                        detected_at=datetime.now().isoformat(),
                        target_price=target_price
                    )
                    patterns.append(pattern)
        
        # 识别头肩底 (看涨反转) - 类似逻辑但使用低点
        for i in range(2, len(swing_lows) - 2):
            left_shoulder_idx = swing_lows[i-2]
            head_idx = swing_lows[i]
            right_shoulder_idx = swing_lows[i+2]
            
            neckline_start_idx = swing_highs[i-1] if i-1 < len(swing_highs) else None
            neckline_end_idx = swing_highs[i+1] if i+1 < len(swing_highs) else None
            
            if (left