#!/usr/bin/env python3
"""
多时间框架分析器

功能:
1. 金字塔式多时间框架分析
2. 趋势一致性判断
3. 信号共振检测
4. 基于框架的决策建议

版本: 1.0.0
作者: 市场分析专家
更新日期: 2026-04-19
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging
import yaml
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TimeframeHierarchy(Enum):
    """时间框架层级"""
    STRATEGIC = "strategic"      # 战略层 (月线、周线)
    TACTICAL = "tactical"        # 战术层 (日线)
    EXECUTION = "execution"      # 执行层 (4小时、1小时)
    MONITORING = "monitoring"    # 监控层 (15分钟、5分钟)

class DecisionConfidence(Enum):
    """决策置信度"""
    VERY_HIGH = "very_high"      # 置信度非常高
    HIGH = "high"                # 置信度高
    MODERATE = "moderate"        # 置信度中等
    LOW = "low"                  # 置信度低
    VERY_LOW = "very_low"        # 置信度非常低

@dataclass
class TimeframeAnalysis:
    """时间框架分析结果"""
    timeframe: str
    hierarchy: TimeframeHierarchy
    weight: float
    trend_direction: str
    trend_strength: float
    key_levels: Dict[str, Any]
    signals: List[Dict[str, Any]]
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "timeframe": self.timeframe,
            "hierarchy": self.hierarchy.value,
            "weight": self.weight,
            "trend_direction": self.trend_direction,
            "trend_strength": self.trend_strength,
            "key_levels": self.key_levels,
            "signals": self.signals,
            "confidence": self.confidence
        }

@dataclass
class MultiTimeframeDecision:
    """多时间框架决策"""
    symbol: str
    timestamp: str
    strategic_direction: str
    tactical_suggestion: str
    execution_timing: str
    confidence: DecisionConfidence
    timeframe_analyses: Dict[str, TimeframeAnalysis]
    alignment_score: float
    resonance_signals: List[Dict[str, Any]]
    risk_assessment: Dict[str, Any]
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp,
            "strategic_direction": self.strategic_direction,
            "tactical_suggestion": self.tactical_suggestion,
            "execution_timing": self.execution_timing,
            "confidence": self.confidence.value,
            "timeframe_analyses": {tf: analysis.to_dict() for tf, analysis in self.timeframe_analyses.items()},
            "alignment_score": self.alignment_score,
            "resonance_signals": self.resonance_signals,
            "risk_assessment": self.risk_assessment,
            "recommendations": self.recommendations
        }
    
    def print_summary(self):
        """打印决策摘要"""
        print("=" * 80)
        print(f"🌐 多时间框架决策: {self.symbol}")
        print("=" * 80)
        print(f"📅 分析时间: {self.timestamp}")
        print()
        
        # 决策信息
        confidence_emoji = {
            "very_high": "🟢",
            "high": "🟡",
            "moderate": "🟠",
            "low": "🔴",
            "very_low": "💀"
        }.get(self.confidence.value, "⚪")
        
        print(f"{confidence_emoji} 决策置信度: {self.confidence.value}")
        print(f"📈 战略方向: {self.strategic_direction}")
        print(f"🎯 战术建议: {self.tactical_suggestion}")
        print(f"⏰ 执行时机: {self.execution_timing}")
        print(f"🔗 趋势对齐: {self.alignment_score:.1%}")
        print()
        
        # 时间框架分析
        print(f"📊 时间框架分析:")
        for timeframe, analysis in self.timeframe_analyses.items():
            hierarchy_emoji = {
                "strategic": "👑",
                "tactical": "🎯",
                "execution": "⚡",
                "monitoring": "👀"
            }.get(analysis.hierarchy.value, "⚪")
            
            trend_emoji = "📈" if analysis.trend_direction == "bullish" else "📉" if analysis.trend_direction == "bearish" else "↔️"
            
            print(f"  {hierarchy_emoji} {timeframe}: {trend_emoji} {analysis.trend_direction}")
            print(f"     强度: {analysis.trend_strength:.1%}, 权重: {analysis.weight:.1%}, 置信度: {analysis.confidence:.1%}")
        print()
        
        # 共振信号
        if self.resonance_signals:
            print(f"🎵 共振信号 ({len(self.resonance_signals)} 个):")
            for signal in self.resonance_signals[:3]:  # 显示前3个
                timeframe_count = len(signal.get('timeframes', []))
                print(f"  • {signal.get('type', 'N/A')} ({timeframe_count}个时间框架确认)")
        print()
        
        # 风险评估
        if self.risk_assessment:
            risk_level = self.risk_assessment.get('level', 'moderate')
            risk_emoji = {
                "low": "🟢",
                "moderate": "🟡",
                "high": "🔴",
                "very_high": "💀"
            }.get(risk_level, "⚪")
            
            print(f"⚠️  风险评估: {risk_emoji} {risk_level}")
            if 'key_risks' in self.risk_assessment:
                for risk in self.risk_assessment['key_risks'][:2]:
                    print(f"  • {risk}")
        print()
        
        # 建议
        if self.recommendations:
            print(f"💡 操作建议:")
            for rec in self.recommendations[:3]:  # 显示前3个建议
                print(f"  • {rec}")
        
        print("=" * 80)

class MultiTimeframeAnalyzer:
    """多时间框架分析器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化多时间框架分析器
        
        参数:
            config_path: 配置文件路径
        """
        self.config_path = config_path or "config/frameworks/crypto_mtf.yaml"
        self.framework = self.load_framework()
        
        logger.info(f"多时间框架分析器初始化完成，框架: {self.framework.get('name', 'N/A')}")
    
    def load_framework(self, framework_name: Optional[str] = None) -> Dict[str, Any]:
        """加载分析框架"""
        if framework_name:
            config_file = Path(f"config/frameworks/{framework_name}.yaml")
        else:
            config_file = Path(self.config_path)
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    framework = yaml.safe_load(f) or {}
                    logger.info(f"加载分析框架: {framework.get('name', 'N/A')}")
                    return framework
            except Exception as e:
                logger.error(f"加载分析框架失败: {e}")
        
        # 默认框架
        return {
            "name": "默认多时间框架框架",
            "description": "基础的多时间框架分析框架",
            "timeframes": {
                "strategic": [
                    {"name": "周线", "timeframe": "1w", "weight": 0.35, "indicators": ["EMA25", "MACD"]}
                ],
                "tactical": [
                    {"name": "日线", "timeframe": "1d", "weight": 0.30, "indicators": ["EMA12", "EMA25", "RSI"]}
                ],
                "execution": [
                    {"name": "4小时线", "timeframe": "4h", "weight": 0.25, "indicators": ["EMA12", "EMA25", "随机指标"]}
                ],
                "monitoring": [
                    {"name": "1小时线", "timeframe": "1h", "weight": 0.10, "indicators": ["EMA7", "EMA12", "RSI"]}
                ]
            },
            "decision_rules": {
                "trend_confirmation": [
                    "至少2个战略层时间框架趋势一致",
                    "战术层趋势与战略层方向相同"
                ],
                "signal_strength": [
                    "多时间框架信号共振增加强度",
                    "成交量确认增加可信度"
                ]
            }
        }
    
    def analyze(
        self,
        symbol: str,
        timeframes: Optional[List[str]] = None,
        data: Optional[Dict[str, pd.DataFrame]] = None,
        analysis_results: Optional[Dict[str, Any]] = None
    ) -> MultiTimeframeDecision:
        """
        执行多时间框架分析
        
        参数:
            symbol: 交易对符号
            timeframes: 时间框架列表
            data: 价格数据
            analysis_results: 预分析结果
        
        返回:
            MultiTimeframeDecision: 多时间框架决策
        """
        logger.info(f"开始多时间框架分析: {symbol}")
        
        # 确定要分析的时间框架
        if timeframes is None:
            timeframes = self._get_default_timeframes()
        
        # 分析每个时间框架
        timeframe_analyses = {}
        for timeframe in timeframes:
            analysis = self._analyze_timeframe(symbol, timeframe, data, analysis_results)
            if analysis:
                timeframe_analyses[timeframe] = analysis
        
        # 计算趋势对齐分数
        alignment_score = self._calculate_alignment_score(timeframe_analyses)
        
        # 检测共振信号
        resonance_signals = self._detect_resonance_signals(timeframe_analyses)
        
        # 确定战略方向
        strategic_direction = self._determine_strategic_direction(timeframe_analyses)
        
        # 生成战术建议
        tactical_suggestion = self._generate_tactical_suggestion(timeframe_analyses, strategic_direction)
        
        # 确定执行时机
        execution_timing = self._determine_execution_timing(timeframe_analyses, tactical_suggestion)
        
        # 评估风险
        risk_assessment = self._assess_risk(timeframe_analyses, strategic_direction)
        
        # 确定置信度
        confidence = self._determine_confidence(alignment_score, resonance_signals, risk_assessment)
        
        # 生成建议
        recommendations = self._generate_recommendations(
            strategic_direction, tactical_suggestion, execution_timing, confidence, risk_assessment
        )
        
        # 创建决策
        decision = MultiTimeframeDecision(
            symbol=symbol,
            timestamp=datetime.now().isoformat(),
            strategic_direction=strategic_direction,
            tactical_suggestion=tactical_suggestion,
            execution_timing=execution_timing,
            confidence=confidence,
            timeframe_analyses=timeframe_analyses,
            alignment_score=alignment_score,
            resonance_signals=resonance_signals,
            risk_assessment=risk_assessment,
            recommendations=recommendations
        )
        
        logger.info(f"多时间框架分析完成: {symbol} - 战略方向: {strategic_direction}, 置信度: {confidence.value}")
        return decision
    
    def _get_default_timeframes(self) -> List[str]:
        """获取默认时间框架"""
        timeframes = []
        
        for hierarchy in ["strategic", "tactical", "execution", "monitoring"]:
            if hierarchy in self.framework.get("timeframes", {}):
                for tf_config in self.framework["timeframes"][hierarchy]:
                    timeframes.append(tf_config["timeframe"])
        
        return timeframes if timeframes else ["1w", "1d", "4h", "1h"]
    
    def _analyze_timeframe(
        self,
        symbol: str,
        timeframe: str,
        data: Optional[Dict[str, pd.DataFrame]] = None,
        analysis_results: Optional[Dict[str, Any]] = None
    ) -> Optional[TimeframeAnalysis]:
        """分析单个时间框架"""
        try:
            # 确定层级和权重
            hierarchy, weight = self._get_timeframe_hierarchy_and_weight(timeframe)
            
            # 获取分析结果
            if analysis_results and timeframe in analysis_results.get("timeframes", {}):
                tf_analysis = analysis_results["timeframes"][timeframe]
                
                # 提取趋势信息
                trend_direction = "neutral"
                trend_strength = 0.5
                
                if "technical" in tf_analysis:
                    tech = tf_analysis["technical"]
                    if "trend_analysis" in tech:
                        trend = tech["trend_analysis"]
                        trend_direction = trend.get("direction", "neutral")
                        trend_strength = trend.get("strength", 0.5)
                
                # 提取关键水平
                key_levels = {}
                if "support_resistance" in tf_analysis:
                    sr = tf_analysis["support_resistance"]
                    key_levels = {
                        "support": [level.get("price") for level in sr.get("support_levels", [])[:3]],
                        "resistance": [level.get("price") for level in sr.get("resistance_levels", [])[:3]]
                    }
                
                # 提取信号
                signals = []
                if "patterns" in tf_analysis:
                    patterns = tf_analysis["patterns"]
                    for pattern in patterns.get("patterns", [])[:5]:
                        signals.append({
                            "type": "pattern",
                            "pattern_name": pattern.get("pattern_name"),
                            "direction": pattern.get("direction"),
                            "confidence": pattern.get("confidence", 0.5)
                        })
                
                # 计算置信度
                confidence = self._calculate_timeframe_confidence(tf_analysis)
                
                return TimeframeAnalysis(
                    timeframe=timeframe,
                    hierarchy=hierarchy,
                    weight=weight,
                    trend_direction=trend_direction,
                    trend_strength=trend_strength,
                    key_levels=key_levels,
                    signals=signals,
                    confidence=confidence
                )
            
            return None
            
        except Exception as e:
            logger.error(f"分析时间框架 {timeframe} 失败: {e}")
            return None
    
    def _get_timeframe_hierarchy_and_weight(self, timeframe: str) -> Tuple[TimeframeHierarchy, float]:
        """获取时间框架的层级和权重"""
        # 默认映射
        default_mapping = {
            "1M": (TimeframeHierarchy.STRATEGIC, 0.40),
            "1w": (TimeframeHierarchy.STRATEGIC, 0.35),
            "1d": (TimeframeHierarchy.TACTICAL, 0.30),
            "4h": (TimeframeHierarchy.EXECUTION, 0.25),
            "1h": (TimeframeHierarchy.EXECUTION, 0.20),
            "15m": (TimeframeHierarchy.MONITORING, 0.10),
            "5m": (TimeframeHierarchy.MONITORING, 0.05)
        }
        
        # 从框架配置中获取
        for hierarchy in ["strategic", "tactical", "execution", "monitoring"]:
            if hierarchy in self.framework.get("timeframes", {}):
                for tf_config in self.framework["timeframes"][hierarchy]:
                    if tf_config["timeframe"] == timeframe:
                        hierarchy_enum = TimeframeHierarchy(hierarchy.upper())
                        return hierarchy_enum, tf_config.get("weight", 0.1)
        
        # 使用默认映射
        if timeframe in default_mapping:
            return default_mapping[timeframe]
        
        # 默认值
        return TimeframeHierarchy.MONITORING, 0.1
    
    def _calculate_timeframe_confidence(self, analysis: Dict[str, Any]) -> float:
        """计算时间框架分析置信度"""
        confidence = 0.5  # 基础置信度
        
        try:
            # 技术分析质量
            if "technical" in analysis:
                tech = analysis["technical"]
                
                # 趋势强度
                if "trend_analysis" in tech:
                    trend_strength = tech["trend_analysis"].get("strength", 0.5)
                    confidence += (trend_strength - 0.5) * 0.3
                
                # 动量确认
                if "momentum_analysis" in tech:
                    rsi = tech["momentum_analysis"].get("rsi_value", 50)
                    # RSI在极端区域时置信度降低
                    if rsi > 70 or rsi < 30:
                        confidence -= 0.1
                    else:
                        confidence += 0.05
            
            # 支撑阻力清晰度
            if "support_resistance" in analysis:
                sr = analysis["support_resistance"]
                support_count = len