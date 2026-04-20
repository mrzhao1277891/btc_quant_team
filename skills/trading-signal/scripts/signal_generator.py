#!/usr/bin/env python3
"""
交易信号生成器

功能:
1. 技术分析信号生成
2. 模式识别信号生成
3. 多时间框架信号生成
4. 市场情绪信号生成
5. 资金流向信号生成

版本: 1.0.0
作者: 交易信号专家
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
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SignalType(Enum):
    """信号类型"""
    TREND_FOLLOWING = "trend_following"      # 趋势跟踪
    REVERSAL = "reversal"                    # 反转
    BREAKOUT = "breakout"                    # 突破
    DIVERGENCE = "divergence"                # 背离
    SUPPORT_RESISTANCE = "support_resistance" # 支撑阻力
    PATTERN = "pattern"                      # 模式
    MULTI_CONFIRMATION = "multi_confirmation" # 多确认
    SENTIMENT = "sentiment"                  # 情绪
    FLOW = "flow"                            # 资金流向

class SignalDirection(Enum):
    """信号方向"""
    BULLISH = "bullish"      # 看涨
    BEARISH = "bearish"      # 看跌
    NEUTRAL = "neutral"      # 中性

class SignalPriority(Enum):
    """信号优先级"""
    CRITICAL = "critical"    # 关键
    HIGH = "high"            # 高
    MEDIUM = "medium"        # 中
    LOW = "low"              # 低

class SignalStatus(Enum):
    """信号状态"""
    GENERATED = "generated"      # 已生成
    CONFIRMED = "confirmed"      # 已确认
    EXECUTED = "executed"        # 已执行
    EXPIRED = "expired"          # 已过期
    CANCELLED = "cancelled"      # 已取消

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
    generated_at: datetime
    reasons: List[str] = field(default_factory=list)
    risk_reward_ratio: Optional[float] = None
    position_size: Optional[float] = None
    validity_period: Optional[int] = None  # 小时
    status: SignalStatus = SignalStatus.GENERATED
    confirmed_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    exit_price: Optional[float] = None
    pnl: Optional[float] = None
    pnl_percent: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['type'] = self.type.value
        data['direction'] = self.direction.value
        data['priority'] = self.priority.value
        data['status'] = self.status.value
        data['generated_at'] = self.generated_at.isoformat()
        
        if self.confirmed_at:
            data['confirmed_at'] = self.confirmed_at.isoformat()
        
        if self.executed_at:
            data['executed_at'] = self.executed_at.isoformat()
        
        return data
    
    def print_signal(self):
        """打印信号"""
        direction_emoji = "🟢" if self.direction == SignalDirection.BULLISH else "🔴" if self.direction == SignalDirection.BEARISH else "⚪"
        priority_emoji = {
            SignalPriority.CRITICAL: "🔥",
            SignalPriority.HIGH: "🚨",
            SignalPriority.MEDIUM: "⚠️",
            SignalPriority.LOW: "ℹ️"
        }
        
        print(f"{direction_emoji}{priority_emoji.get(self.priority, '❓')} 信号: {self.id}")
        print(f"  类型: {self.type.value}")
        print(f"  方向: {self.direction.value}")
        print(f"  标的: {self.symbol} ({self.timeframe})")
        print(f"  时间: {self.generated_at}")
        
        print(f"  价格:")
        print(f"    • 入场: ${self.entry_price:,.2f}")
        print(f"    • 止损: ${self.stop_loss:,.2f}")
        print(f"    • 止盈: ${self.take_profit:,.2f}")
        
        if self.risk_reward_ratio:
            print(f"  风险回报比: {self.risk_reward_ratio:.2f}:1")
        
        print(f"  置信度: {self.confidence:.1%}")
        print(f"  优先级: {self.priority.value}")
        print(f"  状态: {self.status.value}")
        
        if self.reasons:
            print(f"  理由:")
            for reason in self.reasons[:3]:  # 只显示前3个理由
                print(f"    • {reason}")
        
        if self.position_size:
            print(f"  建议仓位: {self.position_size:.4f}")
        
        if self.validity_period:
            expiry = self.generated_at + timedelta(hours=self.validity_period)
            print(f"  有效期至: {expiry}")
    
    def calculate_risk_reward(self) -> float:
        """计算风险回报比"""
        if self.direction == SignalDirection.BULLISH:
            risk = self.entry_price - self.stop_loss
            reward = self.take_profit - self.entry_price
        else:  # BEARISH
            risk = self.stop_loss - self.entry_price
            reward = self.entry_price - self.take_profit
        
        if risk > 0:
            return reward / risk
        return 0.0
    
    def is_valid(self) -> bool:
        """检查信号是否有效"""
        if self.status in [SignalStatus.EXPIRED, SignalStatus.CANCELLED]:
            return False
        
        if self.validity_period:
            expiry_time = self.generated_at + timedelta(hours=self.validity_period)
            if datetime.now() > expiry_time:
                return False
        
        return True
    
    def confirm(self):
        """确认信号"""
        self.status = SignalStatus.CONFIRMED
        self.confirmed_at = datetime.now()
        logger.info(f"信号确认: {self.id}")
    
    def execute(self, exit_price: Optional[float] = None):
        """执行信号"""
        self.status = SignalStatus.EXECUTED
        self.executed_at = datetime.now()
        
        if exit_price:
            self.exit_price = exit_price
            if self.direction == SignalDirection.BULLISH:
                self.pnl = (exit_price - self.entry_price) * (self.position_size or 1)
            else:  # BEARISH
                self.pnl = (self.entry_price - exit_price) * (self.position_size or 1)
            
            if self.entry_price > 0:
                self.pnl_percent = self.pnl / self.entry_price
        
        logger.info(f"信号执行: {self.id}, PnL: {self.pnl}")
    
    def expire(self):
        """使信号过期"""
        self.status = SignalStatus.EXPIRED
        logger.info(f"信号过期: {self.id}")
    
    def cancel(self):
        """取消信号"""
        self.status = SignalStatus.CANCELLED
        logger.info(f"信号取消: {self.id}")

@dataclass
class SignalGenerationResult:
    """信号生成结果"""
    symbol: str
    timeframe: str
    total_signals: int
    signals: List[TradingSignal]
    generation_time: datetime = field(default_factory=datetime.now)
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'total_signals': self.total_signals,
            'generation_time': self.generation_time.isoformat(),
            'parameters': self.parameters,
            'signals': [signal.to_dict() for signal in self.signals]
        }
    
    def print_summary(self):
        """打印摘要"""
        print("=" * 70)
        print(f"📊 信号生成结果: {self.symbol} ({self.timeframe})")
        print("=" * 70)
        
        print(f"总信号数: {self.total_signals}")
        print(f"生成时间: {self.generation_time}")
        
        # 按类型统计
        type_counts = {}
        direction_counts = {'bullish': 0, 'bearish': 0, 'neutral': 0}
        priority_counts = {}
        
        for signal in self.signals:
            # 类型统计
            sig_type = signal.type.value
            type_counts[sig_type] = type_counts.get(sig_type, 0) + 1
            
            # 方向统计
            if signal.direction == SignalDirection.BULLISH:
                direction_counts['bullish'] += 1
            elif signal.direction == SignalDirection.BEARISH:
                direction_counts['bearish'] += 1
            else:
                direction_counts['neutral'] += 1
            
            # 优先级统计
            priority = signal.priority.value
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        print(f"\n📈 信号类型分布:")
        for sig_type, count in type_counts.items():
            percentage = count / self.total_signals * 100
            print(f"  {sig_type}: {count} 个 ({percentage:.1f}%)")
        
        print(f"\n🎯 信号方向分布:")
        for direction, count in direction_counts.items():
            if count > 0:
                percentage = count / self.total_signals * 100
                print(f"  {direction}: {count} 个 ({percentage:.1f}%)")
        
        print(f"\n⚠️  信号优先级分布:")
        for priority, count in priority_counts.items():
            percentage = count / self.total_signals * 100
            print(f"  {priority}: {count} 个 ({percentage:.1f}%)")
        
        # 显示前3个信号
        if self.signals:
            print(f"\n🚦 前3个信号:")
            for i, signal in enumerate(self.signals[:3]):
                print(f"  {i+1}. {signal.type.value} @ ${signal.entry_price:,.2f} ({signal.direction.value})")
        
        print("=" * 70)
    
    def save_signals(self, filepath: str):
        """保存信号到文件"""
        signals_data = self.to_dict()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(signals_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"信号已保存到: {filepath}")
    
    def filter_signals(self, min_confidence: float = 0.0, min_rr: float = 0.0) -> List[TradingSignal]:
        """过滤信号"""
        filtered = []
        
        for signal in self.signals:
            if signal.confidence >= min_confidence:
                rr = signal.calculate_risk_reward()
                if rr >= min_rr:
                    filtered.append(signal)
        
        return filtered

class SignalGenerator:
    """交易信号生成器"""
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        data_source: Optional[Any] = None
    ):
        """
        初始化信号生成器
        
        参数:
            config_path: 配置文件路径
            data_source: 数据源
        """
        self.config_path = config_path or "config/default.yaml"
        self.data_source = data_source
        self.config = self.load_config()
        
        # 信号类型配置
        self.signal_types_enabled = self.config.get('signal_generation', {}).get('enabled_types', [])
        
        # 技术指标参数
        self.technical_params = self.config.get('technical_indicators', {})
        
        # 信号参数
        self.signal_params = {
            'min_confidence': self.config.get('signal_generation', {}).get('min_confidence', 0.6),
            'min_risk_reward': self.config.get('signal_generation', {}).get('min_risk_reward', 1.5),
            'default_validity_hours': self.config.get('signal_generation', {}).get('default_validity_hours', 24)
        }
        
        logger.info("交易信号生成器初始化完成")
    
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
            'signal_generation': {
                'enabled_types': ['technical', 'pattern', 'multi_timeframe'],
                'min_confidence': 0.6,
                'min_risk_reward': 1.5,
                'default_validity_hours': 24
            },
            'technical_indicators': {
                'moving_averages': {
                    'short_period': 10,
                    'medium_period': 20,
                    'long_period': 50
                },
                'rsi': {
                    'period': 14,
                    'overbought': 70,
                    'oversold': 30
                },
                'macd': {
                    'fast_period': 12,
                    'slow_period': 26,
                    'signal_period': 9
                },
                'bollinger_bands': {
                    'period': 20,
                    'std_dev': 2
                }
            }
        }
    
    def generate_signals(
        self,
        symbol: str,
        timeframe: str = "1d",
        days: int = 365,
        data: Optional[pd.DataFrame] = None,
        include_types: Optional[List[str]] = None
    ) -> SignalGenerationResult:
        """
        生成交易信号
        
        参数:
            symbol: 交易对符号
            timeframe: 时间框架
            days: 天数
            data: 数据DataFrame（可选）
            include_types: 包含的信号类型
        
        返回:
            SignalGenerationResult: 信号生成结果
        """
        logger.info(f"开始生成交易信号: {symbol} ({timeframe})")
        
        # 确定包含的信号类型
        if include_types is None:
            include_types = self.signal_types_enabled
        
        # 获取数据
        if data is None:
            data = self._load_data(symbol, timeframe, days)
        
        if data is None or data.empty:
            logger.error(f"无法加载数据: {symbol}")
            return SignalGenerationResult(
                symbol=symbol,
                timeframe=timeframe,
                total_signals=0,
                signals=[],
                parameters={'error': '数据加载失败'}
            )
        
        # 生成信号
        all_signals = []
        generation_params = {
            'symbol': symbol,
            'timeframe': timeframe,
            'days': days,
            'include_types': include_types
        }
        
        # 技术分析信号
        if 'technical' in include_types:
            technical_signals = self.generate_technical_signals(data, symbol, timeframe)
            all_signals.extend(technical_signals)
            logger.info(f"生成技术分析信号: {len(technical_signals)} 个")
        
        # 模式识别信号
        if 'pattern' in include_types:
            pattern_signals = self.generate_pattern_signals(data, symbol, timeframe)
            all_signals.extend(pattern_signals)
            logger.info(f"生成模式识别信号: {len(pattern_signals)} 个")
        
        # 多时间框架信号
        if 'multi_timeframe' in include_types:
            mtf_signals = self.generate_multi_timeframe_signals(symbol, timeframe)
            all_signals.extend(mtf_signals)
            logger.info(f"生成多时间框架信号: {len(mtf_signals)} 个")
        
        # 情绪信号
        if 'sentiment' in include_types:
            sentiment_signals = self.generate_sentiment_signals(symbol)
            all_signals.extend(sentiment_signals)
            logger.info(f"生成情绪信号: {len(sentiment_signals)} 个")
        
        # 资金流向信号
        if 'flow' in include_types:
            flow_signals = self.generate_flow_signals(symbol)
            all_signals.extend(flow_signals)
            logger.info(f"生成资金流向信号: {len(flow_signals)} 个")
        
        # 创建结果
        result = SignalGenerationResult(
            symbol=symbol,
            timeframe=timeframe,
            total_signals=len(all_signals),
            signals=all_signals,
            parameters=generation_params
        )
        
        logger.info(f"信号生成完成: {symbol} - 总信号数: {len(all_signals)}")
        return result
    
    def generate_technical_signals(
        self,
        data: pd.DataFrame,
        symbol: str,
        timeframe: str
    ) -> List[TradingSignal]:
        """生成技术分析信号"""
        signals = []
        
        try:
            # 确保有足够的数据
            if len