#!/usr/bin/env python3
"""
多时间框架分析工具

职责: 跨多个时间框架进行综合分析，识别趋势一致性、信号确认等

主要功能:
- 趋势一致性分析: 分析不同时间框架趋势是否一致
- 信号确认分析: 分析信号在不同时间框架的确认情况
- 支撑阻力聚合: 聚合不同时间框架的支撑阻力位
- 模式确认分析: 分析模式在不同时间框架的确认
- 时间框架权重分配: 根据重要性分配权重
- 综合分析报告: 生成多时间框架综合分析报告

时间框架层级:
1. 宏观框架 (1M, 1w): 长期趋势
2. 中级框架 (1d, 4h): 中期趋势
3. 微观框架 (1h, 30m, 15m): 短期趋势
4. 交易框架 (5m, 1m): 入场时机

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

# 导入其他分析工具
from .technical import TechnicalAnalyzer, TechnicalAnalysisReport, TrendDirection, SignalType
from .support_resistance import SupportResistanceAnalyzer, SupportResistanceReport
from .patterns import PatternRecognizer, PatternAnalysisReport

class TimeframeHierarchy(Enum):
    """时间框架层级"""
    MACRO = "macro"      # 宏观: 1M, 1w
    INTERMEDIATE = "intermediate"  # 中级: 1d, 4h
    MICRO = "micro"      # 微观: 1h, 30m, 15m
    TRADING = "trading"  # 交易: 5m, 1m

class AlignmentStatus(Enum):
    """对齐状态"""
    STRONG_ALIGNMENT = "strong_alignment"    # 强对齐
    MODERATE_ALIGNMENT = "moderate_alignment"  # 中等对齐
    NEUTRAL = "neutral"                      # 中性
    MODERATE_CONFLICT = "moderate_conflict"  # 中等冲突
    STRONG_CONFLICT = "strong_conflict"      # 强冲突

@dataclass
class TimeframeAnalysis:
    """单个时间框架分析"""
    timeframe: str
    hierarchy: TimeframeHierarchy
    weight: float  # 权重 0-1
    technical_report: TechnicalAnalysisReport
    support_resistance_report: SupportResistanceReport
    pattern_report: PatternAnalysisReport
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "timeframe": self.timeframe,
            "hierarchy": self.hierarchy.value,
            "weight": round(self.weight, 3),
            "technical_summary": self.technical_report.summary,
            "support_resistance_summary": {
                "support_count": len(self.support_resistance_report.support_levels),
                "resistance_count": len(self.support_resistance_report.resistance_levels),
                "nearest_support": self.support_resistance_report.nearest_support.price if self.support_resistance_report.nearest_support else None,
                "nearest_resistance": self.support_resistance_report.nearest_resistance.price if self.support_resistance_report.nearest_resistance else None
            },
            "pattern_summary": {
                "active_patterns": len(self.pattern_report.active_patterns),
                "completed_patterns": len(self.pattern_report.completed_patterns),
                "candlestick_patterns": len(self.pattern_report.candlestick_patterns)
            }
        }

@dataclass
class TrendAlignment:
    """趋势对齐分析"""
    status: AlignmentStatus
    score: float  # 0-1，对齐分数
    macro_trend: TrendDirection
    intermediate_trend: TrendDirection
    micro_trend: TrendDirection
    trading_trend: TrendDirection
    details: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "status": self.status.value,
            "score": round(self.score, 3),
            "macro_trend": self.macro_trend.value,
            "intermediate_trend": self.intermediate_trend.value,
            "micro_trend": self.micro_trend.value,
            "trading_trend": self.trading_trend.value,
            "details": self.details
        }

@dataclass
class SignalConfirmation:
    """信号确认分析"""
    signal_type: SignalType
    confirmed_timeframes: List[str]  # 确认的时间框架
    conflicted_timeframes: List[str]  # 冲突的时间框架
    confirmation_score: float  # 0-1，确认分数
    weighted_confidence: float  # 加权置信度
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "signal_type": self.signal_type.value,
            "confirmed_timeframes": self.confirmed_timeframes,
            "conflicted_timeframes": self.conflicted_timeframes,
            "confirmation_score": round(self.confirmation_score, 3),
            "weighted_confidence": round(self.weighted_confidence, 3)
        }

@dataclass
class SupportResistanceConfluence:
    """支撑阻力重合分析"""
    price: float
    confluence_score: float  # 0-1，重合分数
    timeframes: List[str]  # 重合的时间框架
    level_types: List[str]  # 位位类型
    average_strength: float  # 平均强度
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "price": round(self.price, 2),
            "confluence_score": round(self.confluence_score, 3),
            "timeframes": self.timeframes,
            "level_types": self.level_types,
            "average_strength": round(self.average_strength, 3)
        }

@dataclass
class MultiTimeframeReport:
    """多时间框架分析报告"""
    symbol: str
    timestamp: str
    current_price: float
    timeframe_analyses: Dict[str, TimeframeAnalysis]
    trend_alignment: TrendAlignment
    signal_confirmations: List[SignalConfirmation]
    support_resistance_confluences: List[SupportResistanceConfluence]
    pattern_confluences: Dict[str, Any]
    summary: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp,
            "current_price": round(self.current_price, 2),
            "timeframe_analyses": {tf: analysis.to_dict() for tf, analysis in self.timeframe_analyses.items()},
            "trend_alignment": self.trend_alignment.to_dict(),
            "signal_confirmations": [sc.to_dict() for sc in self.signal_confirmations],
            "support_resistance_confluences": [src.to_dict() for src in self.support_resistance_confluences],
            "pattern_confluences": self.pattern_confluences,
            "summary": self.summary
        }
    
    def to_json(self, indent: int = 2) -> str:
        """转换为JSON字符串"""
        import json
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    def print_summary(self):
        """打印摘要"""
        print("=" * 80)
        print(f"🌐 多时间框架分析: {self.symbol}")
        print("=" * 80)
        print(f"📅 分析时间: {self.timestamp}")
        print(f"💰 当前价格: ${self.current_price:,.2f}")
        print()
        
        # 趋势对齐
        alignment = self.trend_alignment
        print(f"📈 趋势对齐分析:")
        print(f"  状态: {alignment.status.value}")
        print(f"  分数: {alignment.score:.1%}")
        print(f"  宏观趋势: {alignment.macro_trend.value}")
        print(f"  中级趋势: {alignment.intermediate_trend.value}")
        print(f"  微观趋势: {alignment.micro_trend.value}")
        print(f"  交易趋势: {alignment.trading_trend.value}")
        print()
        
        # 信号确认
        if self.signal_confirmations:
            print(f"🚦 信号确认分析:")
            for signal in self.signal_confirmations:
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
                print(f"     确认时间框架: {len(signal.confirmed_timeframes)} 个")
                if signal.conflicted_timeframes:
                    print(f"     冲突时间框架: {len(signal.conflicted_timeframes)} 个")
            print()
        
        # 支撑阻力重合
        if self.support_resistance_confluences:
            print(f"🎯 支撑阻力重合位 (前5个):")
            for i, confluence in enumerate(self.support_resistance_confluences[:5], 1):
                distance = (confluence.price - self.current_price) / self.current_price * 100
                position = "上方" if distance > 0 else "下方"
                print(f"  {i}. ${confluence.price:,.2f} ({abs(distance):.1f}% {position})")
                print(f"     重合分数: {confluence.confluence_score:.1%}")
                print(f"     时间框架: {len(confluence.timeframes)} 个")
                print(f"     平均强度: {confluence.average_strength:.1%}")
            if len(self.support_resistance_confluences) > 5:
                print(f"  ... 还有 {len(self.support_resistance_confluences) - 5} 个重合位")
            print()
        
        # 时间框架分析摘要
        print(f"📊 时间框架分析摘要:")
        for timeframe, analysis in self.timeframe_analyses.items():
            tech = analysis.technical_report
            print(f"  {timeframe}:")
            print(f"     趋势: {tech.trend_analysis.direction.value}")
            print(f"     RSI: {tech.momentum_analysis.rsi_value:.1f}")
            print(f"     权重: {analysis.weight:.1%}")
        print()
        
        print("=" * 80)

class MultiTimeframeAnalyzer:
    """多时间框架分析器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化多时间框架分析器
        
        参数:
            config: 配置字典
        """
        self.config = config or self._default_config()
        
        # 初始化子分析器
        self.technical_analyzer = TechnicalAnalyzer()
        self.support_resistance_analyzer = SupportResistanceAnalyzer()
        self.pattern_recognizer = PatternRecognizer()
    
    def _default_config(self) -> Dict[str, Any]:
        """默认配置"""
        return {
            # 时间框架配置
            "timeframes": ["1M", "1w", "1d", "4h", "1h", "30m", "15m", "5m"],
            "timeframe_weights": {
                "1M": 0.25,   # 宏观
                "1w": 0.20,   # 宏观
                "1d": 0.15,   # 中级
                "4h": 0.12,   # 中级
                "1h": 0.10,   # 微观
                "30m": 0.08,  # 微观
                "15m": 0.06,  # 微观
                "5m": 0.04    # 交易
            },
            "timeframe_hierarchy": {
                "1M": TimeframeHierarchy.MACRO,
                "1w": TimeframeHierarchy.MACRO,
                "1d": TimeframeHierarchy.INTERMEDIATE,
                "4h": TimeframeHierarchy.INTERMEDIATE,
                "1h": TimeframeHierarchy.MICRO,
                "30m": TimeframeHierarchy.MICRO,
                "15m": TimeframeHierarchy.MICRO,
                "5m": TimeframeHierarchy.TRADING
            },
            
            # 趋势对齐配置
            "alignment_thresholds": {
                "strong_alignment": 0.8,
                "moderate_alignment": 0.6,
                "neutral": 0.4,
                "moderate_conflict": 0.2,
                "strong_conflict": 0.0
            },
            
            # 信号确认配置
            "signal_confirmation_threshold": 0.7,  # 信号确认阈值
            "weighted_confidence_threshold": 0.6,  # 加权置信度阈值
            
            # 支撑阻力重合配置
            "confluence_price_tolerance": 0.005,  # 价格容差 (0.5%)
            "confluence_min_timeframes": 2,  # 最小重合时间框架数
            "confluence_score_weights": {
                "macro": 0.4,
                "intermediate": 0.3,
                "micro": 0.2,
                "trading": 0.1
            }
        }
    
    def analyze(
        self,
        multi_timeframe_data: Dict[str, pd.DataFrame],
        symbol: str = "BTCUSDT"
    ) -> MultiTimeframeReport:
        """
        执行多时间框架分析
        
        参数:
            multi_timeframe_data: 多时间框架数据 {timeframe: df}
            symbol: 交易对符号
        
        返回:
            MultiTimeframeReport: 多时间框架分析报告
        """
        if not multi_timeframe_data:
            raise ValueError("需要提供多时间框架数据")
        
        # 获取当前价格 (使用最小时间框架)
        min_timeframe = min(multi_timeframe_data.keys(), key=lambda x: self._timeframe_to_minutes(x))
        current_price = multi_timeframe_data[min_timeframe]['close'].iloc[-1]
        
        # 1. 分析每个时间框架
        timeframe_analyses = {}
        for timeframe, df in multi_timeframe_data.items():
            if timeframe in self.config["timeframes"]:
                analysis = self._analyze_single_timeframe(df, symbol, timeframe)
                timeframe_analyses[timeframe] = analysis
        
        # 2. 趋势对齐分析
        trend_alignment = self._analyze_trend_alignment(timeframe_analyses)
        
        # 3. 信号确认分析
        signal_confirmations = self._analyze_signal_confirmation(timeframe_analyses)
        
        # 4. 支撑阻力重合分析
        support_resistance_confluences = self._analyze_support_resistance_confluence(timeframe_analyses)
        
        # 5. 模式重合分析
        pattern_confluences = self._analyze_pattern_confluence(timeframe_analyses)
        
        # 6. 生成报告
        return MultiTimeframeReport(
            symbol=symbol,
            timestamp=datetime.now().isoformat(),
            current_price=current_price,
            timeframe_analyses=timeframe_analyses,
            trend_alignment=trend_alignment,
            signal_confirmations=signal_confirmations,
            support_resistance_confluences=support_resistance_confluences,
            pattern_confluences=pattern_confluences,
            summary=self._generate_summary(
                timeframe_analyses, trend_alignment,
                signal_confirmations, support_resistance_confluences
            )
        )
    
    def _analyze_single_timeframe(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str
    ) -> TimeframeAnalysis:
        """分析单个时间框架"""
        # 获取权重和层级
        weight = self.config["timeframe_weights"].get(timeframe, 0.1)
        hierarchy = self.config["timeframe_hierarchy"].get(timeframe, TimeframeHierarchy.MICRO)
        
        # 技术分析
        technical_report = self.technical_analyzer.analyze(df, symbol, timeframe)
        
        # 支撑阻力分析
        support_resistance_report = self.support_resistance_analyzer.analyze(df, symbol, timeframe)
        
        # 模式识别
        pattern_report = self.pattern_recognizer.analyze(df, symbol, timeframe)
        
        return TimeframeAnalysis(
            timeframe=timeframe,
            hierarchy=hierarchy,
            weight=weight,
            technical_report=technical_report,
            support_resistance_report=support_resistance_report,
            pattern_report=pattern_report
        )
    
    def _analyze_trend_alignment(
        self,
        timeframe_analyses: Dict[str, TimeframeAnalysis]
    ) -> TrendAlignment:
        """分析趋势对齐"""
        # 按层级分组趋势
        trends_by_hierarchy = {}
        for timeframe, analysis in timeframe_analyses.items():
            hierarchy = analysis.hierarchy
            trend = analysis.technical_report.trend_analysis.direction
            
            if hierarchy not in trends_by_hierarchy:
                trends_by_hierarchy[hierarchy] = []
            trends_by_hierarchy[hierarchy].append((timeframe, trend, analysis.weight))
        
        # 计算各层级的主要趋势
        hierarchy_trends = {}
        for hierarchy, trend_data in trends_by_hierarchy.items():
            # 加权投票
            trend_scores = {}
            for timeframe, trend, weight in trend_data:
                if trend not in trend_scores:
                    trend_scores[trend] = 0
                trend_scores[trend] += weight
            
            # 选择得分最高的趋势
            if trend_s