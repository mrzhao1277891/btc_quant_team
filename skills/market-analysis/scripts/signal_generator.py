#!/usr/bin/env python3
"""
信号生成器

功能:
1. 基于多维度分析生成交易信号
2. 信号分类和置信度计算
3. 风险管理参数计算
4. 信号过滤和优先级排序

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

class SignalType(Enum):
    """信号类型"""
    TREND_FOLLOWING = "trend_following"      # 趋势跟随
    REVERSAL = "reversal"                    # 反转
    BREAKOUT = "breakout"                    # 突破
    DIVERGENCE = "divergence"                # 背离
    SUPPORT_RESISTANCE = "support_resistance"  # 支撑阻力
    PATTERN = "pattern"                      # 模式
    MULTI_CONFIRMATION = "multi_confirmation"  # 多确认

class SignalDirection(Enum):
    """信号方向"""
    BULLISH = "bullish"      # 看涨
    BEARISH = "bearish"      # 看跌
    NEUTRAL = "neutral"      # 中性

class SignalPriority(Enum):
    """信号优先级"""
    CRITICAL = "critical"    # 关键信号
    HIGH = "high"            # 高优先级
    MEDIUM = "medium"        # 中等优先级
    LOW = "low"              # 低优先级

@dataclass
class TradingSignal:
    """交易信号"""
    id: str
    type: SignalType
    direction: SignalDirection
    symbol: str
    timeframe: str
    entry_price: float
    stop_loss: float
    take_profit: float
    confidence: float  # 0-1
    priority: SignalPriority
    generated_at: str
    reasons: List[str]
    risk_reward_ratio: float
    position_size: Optional[float] = None
    validity_period: Optional[int] = None  # 有效期(小时)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['type'] = self.type.value
        data['direction'] = self.direction.value
        data['priority'] = self.priority.value
        return data
    
    def print_signal(self):
        """打印信号信息"""
        direction_emoji = "🟢" if self.direction == SignalDirection.BULLISH else "🔴"
        priority_emoji = {
            "critical": "🚨",
            "high": "⚠️",
            "medium": "🔔",
            "low": "ℹ️"
        }.get(self.priority.value, "⚪")
        
        print(f"{priority_emoji}{direction_emoji} 交易信号: {self.type.value}")
        print(f"  符号: {self.symbol} ({self.timeframe})")
        print(f"  方向: {self.direction.value}")
        print(f"  入场: ${self.entry_price:,.2f}")
        print(f"  止损: ${self.stop_loss:,.2f}")
        print(f"  止盈: ${self.take_profit:,.2f}")
        print(f"  风险回报比: {self.risk_reward_ratio:.2f}:1")
        print(f"  置信度: {self.confidence:.1%}")
        print(f"  优先级: {self.priority.value}")
        
        if self.position_size:
            print(f"  建议仓位: {self.position_size:.4f}")
        
        if self.reasons:
            print(f"  理由:")
            for reason in self.reasons[:3]:  # 显示前3个理由
                print(f"    • {reason}")
        
        if self.validity_period:
            expiry = datetime.fromisoformat(self.generated_at) + timedelta(hours=self.validity_period)
            print(f"  有效期至: {expiry.strftime('%Y-%m-%d %H:%M')}")
        
        print()

class SignalGenerator:
    """信号生成器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化信号生成器
        
        参数:
            config_path: 配置文件路径
        """
        self.config_path = config_path or "config/signals.yaml"
        self.config = self.load_config()
        
        # 信号计数器
        self.signal_counter = 0
        
        logger.info("信号生成器初始化完成")
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置"""
        config_file = Path(self.config_path)
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.error(f"加载信号配置失败: {e}")
                return {}
        
        # 默认配置
        return {
            "signal_thresholds": {
                "confidence": {
                    "critical": 0.85,
                    "high": 0.70,
                    "medium": 0.55,
                    "low": 0.40
                },
                "risk_reward": {
                    "minimum": 1.5,
                    "good": 2.0,
                    "excellent": 3.0
                }
            },
            "position_sizing": {
                "base_risk_per_trade": 0.02,  # 2% per trade
                "max_position_size": 0.10,    # 10% of portfolio
                "confidence_multiplier": {
                    "critical": 1.5,
                    "high": 1.2,
                    "medium": 1.0,
                    "low": 0.5
                }
            },
            "signal_rules": {
                "trend_following": {
                    "required_conditions": [
                        "trend_strength > 0.6",
                        "multiple_timeframe_confirmation",
                        "volume_confirmation"
                    ],
                    "confidence_boosters": [
                        "strong_trend_alignment",
                        "clear_support_resistance",
                        "low_volatility_entry"
                    ]
                },
                "reversal": {
                    "required_conditions": [
                        "divergence_present",
                        "oversold_overbought_condition",
                        "pattern_confirmation"
                    ],
                    "confidence_boosters": [
                        "multiple_divergence",
                        "volume_spike",
                        "key_level_rejection"
                    ]
                },
                "breakout": {
                    "required_conditions": [
                        "consolidation_period",
                        "volume_confirmation",
                        "clear_breakout_level"
                    ],
                    "confidence_boosters": [
                        "multiple_timeframe_breakout",
                        "retest_successful",
                        "fundamental_catalyst"
                    ]
                }
            }
        }
    
    def generate_signals(
        self,
        symbol: str,
        analysis_data: Dict[str, Any],
        risk_tolerance: str = "medium",
        account_size: Optional[float] = None
    ) -> List[TradingSignal]:
        """
        生成交易信号
        
        参数:
            symbol: 交易对符号
            analysis_data: 市场分析数据
            risk_tolerance: 风险容忍度 (low, medium, high)
            account_size: 账户规模（用于仓位计算）
        
        返回:
            List[TradingSignal]: 交易信号列表
        """
        logger.info(f"开始生成交易信号: {symbol}")
        
        signals = []
        
        try:
            # 1. 趋势跟随信号
            trend_signals = self._generate_trend_signals(symbol, analysis_data)
            signals.extend(trend_signals)
            
            # 2. 反转信号
            reversal_signals = self._generate_reversal_signals(symbol, analysis_data)
            signals.extend(reversal_signals)
            
            # 3. 突破信号
            breakout_signals = self._generate_breakout_signals(symbol, analysis_data)
            signals.extend(breakout_signals)
            
            # 4. 背离信号
            divergence_signals = self._generate_divergence_signals(symbol, analysis_data)
            signals.extend(divergence_signals)
            
            # 5. 支撑阻力信号
            sr_signals = self._generate_support_resistance_signals(symbol, analysis_data)
            signals.extend(sr_signals)
            
            # 6. 模式信号
            pattern_signals = self._generate_pattern_signals(symbol, analysis_data)
            signals.extend(pattern_signals)
            
            # 7. 多确认信号
            multi_confirmation_signals = self._generate_multi_confirmation_signals(signals)
            signals.extend(multi_confirmation_signals)
            
            # 过滤和排序信号
            filtered_signals = self._filter_and_sort_signals(
                signals, risk_tolerance, account_size
            )
            
            logger.info(f"信号生成完成: {symbol} - 生成 {len(signals)} 个信号，过滤后 {len(filtered_signals)} 个")
            return filtered_signals
            
        except Exception as e:
            logger.error(f"生成信号失败: {e}")
            return []
    
    def _generate_trend_signals(
        self,
        symbol: str,
        analysis_data: Dict[str, Any]
    ) -> List[TradingSignal]:
        """生成趋势跟随信号"""
        signals = []
        
        try:
            # 检查市场状态
            market_state = analysis_data.get("market_state", "")
            trend_direction = analysis_data.get("trend_direction", "")
            strength_score = analysis_data.get("strength_score", 0)
            
            # 只在趋势明确时生成趋势信号
            if market_state in ["strong_uptrend", "moderate_uptrend", "strong_downtrend", "moderate_downtrend"]:
                # 获取关键水平
                key_levels = analysis_data.get("key_levels", {})
                
                if trend_direction == "bullish":
                    # 生成做多信号
                    entry_price = self._calculate_trend_entry_price(
                        symbol, analysis_data, "bullish"
                    )
                    
                    if entry_price:
                        stop_loss = self._calculate_stop_loss(
                            entry_price, "bullish", analysis_data
                        )
                        take_profit = self._calculate_take_profit(
                            entry_price, stop_loss, analysis_data
                        )
                        
                        # 计算置信度
                        confidence = self._calculate_trend_confidence(
                            analysis_data, "bullish"
                        )
                        
                        # 确定优先级
                        priority = self._determine_signal_priority(confidence)
                        
                        # 生成信号
                        signal = TradingSignal(
                            id=f"trend_{self._get_next_signal_id()}",
                            type=SignalType.TREND_FOLLOWING,
                            direction=SignalDirection.BULLISH,
                            symbol=symbol,
                            timeframe="4h",  # 趋势信号通常基于4小时或日线
                            entry_price=entry_price,
                            stop_loss=stop_loss,
                            take_profit=take_profit,
                            confidence=confidence,
                            priority=priority,
                            generated_at=datetime.now().isoformat(),
                            reasons=[
                                f"市场处于{market_state}",
                                f"趋势强度评分: {strength_score}/100",
                                "多时间框架趋势确认"
                            ],
                            risk_reward_ratio=self._calculate_risk_reward_ratio(
                                entry_price, stop_loss, take_profit
                            )
                        )
                        
                        signals.append(signal)
                
                elif trend_direction == "bearish":
                    # 生成做空信号
                    entry_price = self._calculate_trend_entry_price(
                        symbol, analysis_data, "bearish"
                    )
                    
                    if entry_price:
                        stop_loss = self._calculate_stop_loss(
                            entry_price, "bearish", analysis_data
                        )
                        take_profit = self._calculate_take_profit(
                            entry_price, stop_loss, analysis_data
                        )
                        
                        # 计算置信度
                        confidence = self._calculate_trend_confidence(
                            analysis_data, "bearish"
                        )
                        
                        # 确定优先级
                        priority = self._determine_signal_priority(confidence)
                        
                        # 生成信号
                        signal = TradingSignal(
                            id=f"trend_{self._get_next_signal_id()}",
                            type=SignalType.TREND_FOLLOWING,
                            direction=SignalDirection.BEARISH,
                            symbol=symbol,
                            timeframe="4h",
                            entry_price=entry_price,
                            stop_loss=stop_loss,
                            take_profit=take_profit,
                            confidence=confidence,
                            priority=priority,
                            generated_at=datetime.now().isoformat(),
                            reasons=[
                                f"市场处于{market_state}",
                                f"趋势强度评分: {strength_score}/100",
                                "多时间框架趋势确认"
                            ],
                            risk_reward_ratio=self._calculate_risk_reward_ratio(
                                entry_price, stop_loss, take_profit
                            )
                        )
                        
                        signals.append(signal)
        
        except Exception as e:
            logger.error(f"生成趋势信号失败: {e}")
        
        return signals
    
    def _generate_reversal_signals(
        self,
        symbol: str,
        analysis_data: Dict[str, Any]
    ) -> List[TradingSignal]:
        """生成反转信号"""
        signals = []
        
        try:
            # 检查是否处于极端状态
            technical_analysis = analysis_data.get("technical_analysis", {})
            summary = technical_analysis.get("summary", {})
            
            momentum = summary.get("momentum", {})
            rsi = momentum.get("rsi", 50)
            rsi_signal = momentum.get("signal", "neutral")
            
            # 检查超买超卖
            if rsi_signal == "overbought" and rsi > 75:
                # 可能的价格顶部，考虑做空反转
                signals.extend(self._generate_reversal_signal(
                    symbol, analysis_data, "bearish", "overbought"
                ))
            
            elif rsi_signal == "oversold" and rsi < 25:
                # 可能的价格底部，考虑做多反转
                signals.extend(self._generate_reversal_signal(
                    symbol, analysis_data, "bullish", "oversold"
                ))
            
            # 检查趋势反转模式
            market_state = analysis_data.get("market_state", "")
            if market_state == "trend_reversal":
                # 趋势反转确认
                trend_direction = analysis_data.get("trend_direction", "")
                
                if trend_direction == "bullish":
                    signals.extend(self._generate_reversal_signal(
                        symbol, analysis_data, "bullish", "trend_reversal"
                    ))
                elif trend_direction == "bearish":
                    signals.extend(self._generate_reversal_signal(
                        symbol, analysis_data, "bearish", "trend_reversal"
                    ))
        
        except Exception as e:
            logger.error(f"生成反转信号失败: {e}")
        
        return signals
    
    def _generate_reversal_signal(
        self,
        symbol: str,
        analysis_data: Dict[str, Any],
        direction: str,
        reason: str
    ) -> List[TradingSignal]:
        """生成单个反转信号"""
        signals = []
        
        try:
            entry_price = self._calculate_reversal_entry_price(
                symbol, analysis_data, direction
            )
            
            if entry_price:
                stop_loss = self._calculate_stop_loss(
                    entry_price, direction, analysis_data
                )
                take_profit = self._calculate_take_profit(
                    entry_price, stop_loss, analysis_data
                )
                
                # 计算置信度（反转信号通常置信度较低）
                base_confidence = 0.5
                
                # 根据原因调整置信度
                if reason == "overbought" or reason == "oversold":
                    base_confidence = 0.6
                elif reason == "trend_reversal":
                    base_confidence = 0.7
                
                # 技术分析确认
                technical_analysis = analysis_data.get("technical_analysis", {})
                if technical_analysis:
                    base_confidence += 0.1
                
                confidence = min(0.9, base_confidence)
                
                # 确定优先级
                priority = self._determine_signal_priority(confidence)
                
                # 生成信号
                signal_direction = SignalDirection.BULLISH if direction == "bullish" else SignalDirection.BEARISH
                
                signal = TradingSignal(
                    id=f"reversal_{self._get_next_signal_id()}",
                    type=SignalType.REVERSAL,
                    direction=signal_direction,
                    symbol=symbol,
                    timeframe="1d",  # 反转信号通常基于日线
                    entry_price=entry_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    confidence=confidence,
                    priority=priority,
                    generated_at=datetime.now().isoformat(),
                    reasons=[
                        f"{reason}条件触发",
                        "潜在趋势反转",
                        "技术指标确认"
                    ],
                    risk_reward_ratio=self._calculate_risk_reward_ratio(
                        entry_price, stop_loss, take_profit
                    ),
                    validity_period=48  # 反转信号有效期48小时
                )
                
                signals.append(signal)
        
        except Exception as e:
            logger.error(f"生成反转信号失败: {e}")
        
        return signals
    
    def _generate_breakout_signals(
        self,
        symbol: str,
        analysis_data: Dict[str, Any]
    ) -> List[TradingSignal]:
        """生成突破信号"""
        signals = []
        
        try:
            # 检查关键水平
            key_levels = analysis_data.get("key_levels", {})
            resistances = key_levels.get("resistance", [])
            # 这里添加突破信号生成逻辑
            pass
        except Exception as e:
            logger.error(f"生成突破信号失败: {e}")
        
        return signals