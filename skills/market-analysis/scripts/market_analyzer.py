#!/usr/bin/env python3
"""
市场分析器

功能:
1. 综合市场分析 (技术面、基本面、情绪面)
2. 多时间框架趋势分析
3. 市场状态判断和强度评分
4. 专业分析报告生成

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

# 导入分析工具
try:
    from tools.analysis import (
        TechnicalAnalyzer, SupportResistanceAnalyzer,
        PatternRecognizer, MultiTimeframeAnalyzer
    )
    ANALYSIS_TOOLS_AVAILABLE = True
except ImportError:
    ANALYSIS_TOOLS_AVAILABLE = False
    print("⚠️  分析工具不可用，请确保tools目录在Python路径中")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MarketState(Enum):
    """市场状态"""
    STRONG_UPTREND = "strong_uptrend"      # 强势上涨
    MODERATE_UPTREND = "moderate_uptrend"  # 温和上涨
    CONSOLIDATION = "consolidation"        # 盘整
    MODERATE_DOWNTREND = "moderate_downtrend"  # 温和下跌
    STRONG_DOWNTREND = "strong_downtrend"  # 强势下跌
    TREND_REVERSAL = "trend_reversal"      # 趋势反转

class RiskLevel(Enum):
    """风险等级"""
    VERY_LOW = "very_low"      # 风险极低
    LOW = "low"                # 风险低
    MODERATE = "moderate"      # 风险中等
    HIGH = "high"              # 风险高
    VERY_HIGH = "very_high"    # 风险极高

class AnalysisDimension(Enum):
    """分析维度"""
    TECHNICAL = "technical"      # 技术分析
    FUNDAMENTAL = "fundamental"  # 基本面分析
    SENTIMENT = "sentiment"      # 情绪分析
    FLOW = "flow"                # 资金流向
    VOLATILITY = "volatility"    # 波动率分析

@dataclass
class MarketAnalysis:
    """市场分析结果"""
    symbol: str
    timestamp: str
    current_price: float
    market_state: MarketState
    trend_direction: str
    strength_score: float  # 0-100
    risk_level: RiskLevel
    key_levels: Dict[str, Any]
    technical_analysis: Dict[str, Any]
    sentiment_analysis: Optional[Dict[str, Any]] = None
    fundamental_analysis: Optional[Dict[str, Any]] = None
    flow_analysis: Optional[Dict[str, Any]] = None
    volatility_analysis: Optional[Dict[str, Any]] = None
    signals: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['market_state'] = self.market_state.value
        data['risk_level'] = self.risk_level.value
        return data
    
    def to_json(self, indent: int = 2) -> str:
        """转换为JSON字符串"""
        import json
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    def print_summary(self):
        """打印分析摘要"""
        print("=" * 80)
        print(f"📊 市场分析摘要: {self.symbol}")
        print("=" * 80)
        print(f"📅 分析时间: {self.timestamp}")
        print(f"💰 当前价格: ${self.current_price:,.2f}")
        print()
        
        # 市场状态
        state_emoji = {
            "strong_uptrend": "📈🟢",
            "moderate_uptrend": "📈🟡",
            "consolidation": "↔️⚪",
            "moderate_downtrend": "📉🟠",
            "strong_downtrend": "📉🔴",
            "trend_reversal": "🔄🟣"
        }.get(self.market_state.value, "⚪")
        
        print(f"{state_emoji} 市场状态: {self.market_state.value}")
        print(f"📈 趋势方向: {self.trend_direction}")
        print(f"💪 强度评分: {self.strength_score}/100")
        
        # 风险等级
        risk_emoji = {
            "very_low": "🟢",
            "low": "🟡",
            "moderate": "🟠",
            "high": "🔴",
            "very_high": "💀"
        }.get(self.risk_level.value, "⚪")
        
        print(f"{risk_emoji} 风险等级: {self.risk_level.value}")
        print()
        
        # 关键水平
        if self.key_levels:
            print(f"🎯 关键水平:")
            if 'support' in self.key_levels:
                supports = self.key_levels['support'][:3]
                for i, support in enumerate(supports, 1):
                    distance = (self.current_price - support) / self.current_price * 100
                    print(f"  支撑{i}: ${support:,.2f} ({distance:+.1f}%)")
            
            if 'resistance' in self.key_levels:
                resistances = self.key_levels['resistance'][:3]
                for i, resistance in enumerate(resistances, 1):
                    distance = (resistance - self.current_price) / self.current_price * 100
                    print(f"  阻力{i}: ${resistance:,.2f} ({distance:+.1f}%)")
            print()
        
        # 技术分析摘要
        if self.technical_analysis:
            tech = self.technical_analysis
            print(f"📊 技术分析:")
            
            if 'trend' in tech:
                print(f"  趋势: {tech['trend'].get('direction', 'N/A')}")
                print(f"  强度: {tech['trend'].get('strength', 0):.1%}")
            
            if 'momentum' in tech:
                print(f"  动量: RSI={tech['momentum'].get('rsi', 0):.1f}")
            
            if 'volatility' in tech:
                print(f"  波动率: {tech['volatility'].get('regime', 'N/A')}")
            print()
        
        # 信号
        if self.signals:
            print(f"🚦 交易信号 ({len(self.signals)} 个):")
            for signal in self.signals[:3]:  # 显示前3个信号
                confidence = signal.get('confidence', 0)
                if confidence > 0.7:
                    emoji = "🟢" if signal.get('direction') == 'bullish' else "🔴"
                    print(f"  {emoji} {signal.get('type', 'N/A')} (置信度: {confidence:.1%})")
            print()
        
        # 建议
        if self.recommendations:
            print(f"💡 交易建议:")
            for rec in self.recommendations[:3]:  # 显示前3个建议
                print(f"  • {rec}")
        
        print("=" * 80)

class MarketAnalyzer:
    """市场分析器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化市场分析器
        
        参数:
            config_path: 配置文件路径
        """
        self.config_path = config_path or "config/default.yaml"
        self.config = self.load_config()
        
        # 初始化分析工具
        if ANALYSIS_TOOLS_AVAILABLE:
            self.technical_analyzer = TechnicalAnalyzer()
            self.support_resistance_analyzer = SupportResistanceAnalyzer()
            self.pattern_recognizer = PatternRecognizer()
            self.multi_timeframe_analyzer = MultiTimeframeAnalyzer()
        else:
            logger.warning("分析工具不可用，部分功能受限")
            self.technical_analyzer = None
            self.support_resistance_analyzer = None
            self.pattern_recognizer = None
            self.multi_timeframe_analyzer = None
        
        logger.info("市场分析器初始化完成")
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置"""
        config_file = Path(self.config_path)
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.error(f"加载配置失败: {e}")
                return {}
        
        # 默认配置
        return {
            "analysis": {
                "default_timeframes": ["1d", "4h", "1h"],
                "include_sentiment": True,
                "include_fundamental": False,
                "include_flow": True,
                "strength_thresholds": {
                    "very_strong": 80,
                    "strong": 60,
                    "moderate": 40,
                    "weak": 20
                }
            },
            "data": {
                "cache_ttl": 300,  # 5分钟
                "max_data_points": 1000
            }
        }
    
    def analyze_comprehensive(
        self,
        symbol: str,
        timeframes: Optional[List[str]] = None,
        include_sentiment: Optional[bool] = None,
        include_fundamental: Optional[bool] = None,
        include_flow: Optional[bool] = None,
        data: Optional[Dict[str, pd.DataFrame]] = None
    ) -> MarketAnalysis:
        """
        执行全面市场分析
        
        参数:
            symbol: 交易对符号
            timeframes: 时间框架列表
            include_sentiment: 是否包含情绪分析
            include_fundamental: 是否包含基本面分析
            include_flow: 是否包含资金流向分析
            data: 预加载的数据
        
        返回:
            MarketAnalysis: 市场分析结果
        """
        logger.info(f"开始全面市场分析: {symbol}")
        
        # 使用配置或参数
        timeframes = timeframes or self.config["analysis"]["default_timeframes"]
        include_sentiment = include_sentiment if include_sentiment is not None else self.config["analysis"]["include_sentiment"]
        include_flow = include_flow if include_flow is not None else self.config["analysis"]["include_flow"]
        
        # 获取当前价格
        current_price = self._get_current_price(symbol)
        
        # 技术分析
        technical_analysis = self._analyze_technical(symbol, timeframes, data)
        
        # 支撑阻力分析
        key_levels = self._analyze_key_levels(symbol, timeframes, data)
        
        # 市场状态判断
        market_state, trend_direction = self._determine_market_state(technical_analysis)
        
        # 强度评分
        strength_score = self._calculate_strength_score(technical_analysis, market_state)
        
        # 风险等级
        risk_level = self._assess_risk_level(technical_analysis, market_state, strength_score)
        
        # 情绪分析
        sentiment_analysis = None
        if include_sentiment:
            sentiment_analysis = self._analyze_sentiment(symbol)
        
        # 资金流向分析
        flow_analysis = None
        if include_flow:
            flow_analysis = self._analyze_flow(symbol)
        
        # 波动率分析
        volatility_analysis = self._analyze_volatility(symbol, timeframes, data)
        
        # 生成信号
        signals = self._generate_signals(technical_analysis, key_levels, market_state)
        
        # 生成建议
        recommendations = self._generate_recommendations(
            market_state, trend_direction, strength_score, risk_level, signals
        )
        
        # 创建分析结果
        analysis = MarketAnalysis(
            symbol=symbol,
            timestamp=datetime.now().isoformat(),
            current_price=current_price,
            market_state=market_state,
            trend_direction=trend_direction,
            strength_score=strength_score,
            risk_level=risk_level,
            key_levels=key_levels,
            technical_analysis=technical_analysis,
            sentiment_analysis=sentiment_analysis,
            flow_analysis=flow_analysis,
            volatility_analysis=volatility_analysis,
            signals=signals,
            recommendations=recommendations
        )
        
        logger.info(f"市场分析完成: {symbol} - 状态: {market_state.value}, 强度: {strength_score}/100")
        return analysis
    
    def _get_current_price(self, symbol: str) -> float:
        """获取当前价格"""
        # 这里可以集成价格获取逻辑
        # 暂时返回一个默认值
        return 75000.0  # 默认值
    
    def _analyze_technical(
        self,
        symbol: str,
        timeframes: List[str],
        data: Optional[Dict[str, pd.DataFrame]] = None
    ) -> Dict[str, Any]:
        """技术分析"""
        technical_analysis = {
            "timeframes": {},
            "summary": {},
            "indicators": {}
        }
        
        if not self.technical_analyzer or not data:
            return technical_analysis
        
        try:
            # 分析每个时间框架
            for timeframe in timeframes:
                if timeframe in data:
                    df = data[timeframe]
                    
                    # 技术分析
                    tech_report = self.technical_analyzer.analyze(df, symbol, timeframe)
                    
                    # 支撑阻力分析
                    sr_report = self.support_resistance_analyzer.analyze(df, symbol, timeframe)
                    
                    # 模式识别
                    pattern_report = self.pattern_recognizer.analyze(df, symbol, timeframe)
                    
                    technical_analysis["timeframes"][timeframe] = {
                        "technical": tech_report.to_dict(),
                        "support_resistance": sr_report.to_dict(),
                        "patterns": pattern_report.to_dict()
                    }
            
            # 生成摘要
            technical_analysis["summary"] = self._summarize_technical_analysis(technical_analysis["timeframes"])
            
        except Exception as e:
            logger.error(f"技术分析失败: {e}")
        
        return technical_analysis
    
    def _summarize_technical_analysis(self, timeframe_analyses: Dict[str, Any]) -> Dict[str, Any]:
        """汇总技术分析"""
        summary = {
            "trend": {"direction": "neutral", "strength": 0.5},
            "momentum": {"rsi": 50, "signal": "neutral"},
            "volatility": {"regime": "normal", "atr_percent": 0.02},
            "volume": {"trend": "neutral", "confirmation": False}
        }
        
        if not timeframe_analyses:
            return summary
        
        try:
            # 收集各时间框架的趋势
            trends = []
            rsi_values = []
            
            for timeframe, analysis in timeframe_analyses.items():
                if "technical" in analysis:
                    tech = analysis["technical"]
                    
                    # 趋势
                    if "trend_analysis" in tech:
                        trend = tech["trend_analysis"]
                        trends.append({
                            "timeframe": timeframe,
                            "direction": trend.get("direction", "neutral"),
                            "strength": trend.get("strength", 0.5)
                        })
                    
                    # RSI
                    if "momentum_analysis" in tech:
                        momentum = tech["momentum_analysis"]
                        rsi_values.append(momentum.get("rsi_value", 50))
            
            # 确定主要趋势
            if trends:
                # 加权趋势判断（更高时间框架权重更大）
                direction_counts = {}
                for trend in trends:
                    direction = trend["direction"]
                    weight = 1.0
                    if trend["timeframe"] in ["1d", "1w"]:
                        weight = 1.5
                    elif trend["timeframe"] in ["4h", "1h"]:
                        weight = 1.0
                    else:
                        weight = 0.5
                    
                    if direction not in direction_counts:
                        direction_counts[direction] = 0
                    direction_counts[direction] += weight
                
                # 选择最常见的趋势方向
                if direction_counts:
                    main_direction = max(direction_counts, key=direction_counts.get)
                    summary["trend"]["direction"] = main_direction
            
            # 平均RSI
            if rsi_values:
                summary["momentum"]["rsi"] = sum(rsi_values) / len(rsi_values)
                if summary["momentum"]["rsi"] > 70:
                    summary["momentum"]["signal"] = "overbought"
                elif summary["momentum"]["rsi"] < 30:
                    summary["momentum"]["signal"] = "oversold"
                else:
                    summary["momentum"]["signal"] = "neutral"
        
        except Exception as e:
            logger.error(f"汇总技术分析失败: {e}")
        
        return summary
    
    def _analyze_key_levels(
        self,
        symbol: str,
        timeframes: List[str],
        data: Optional[Dict[str, pd.DataFrame]] = None
    ) -> Dict[str, Any]:
        """分析关键水平"""
        key_levels = {
            "support": [],
            "resistance": [],
            "psychological": []
        }
        
        if not self.support_resistance_analyzer or not data:
            return key_levels
        
        try:
            # 这里添加支撑阻力分析逻辑
            pass
        except Exception as e:
            logger.error(f"分析关键水平失败: {e}")
