#!/usr/bin/env python3
"""
风险管理器

功能:
1. 动态止损止盈计算
2. 基于风险的仓位大小计算
3. 风险暴露和回撤管理
4. 投资组合风险分析

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

class RiskLevel(Enum):
    """风险等级"""
    VERY_LOW = "very_low"      # 风险极低
    LOW = "low"                # 风险低
    MODERATE = "moderate"      # 风险中等
    HIGH = "high"              # 风险高
    VERY_HIGH = "very_high"    # 风险极高

class PositionSizeMethod(Enum):
    """仓位计算方法"""
    FIXED_RISK = "fixed_risk"          # 固定风险
    KELLY_CRITERION = "kelly_criterion"  # 凯利公式
    VOLATILITY_ADJUSTED = "volatility_adjusted"  # 波动率调整
    CONFIDENCE_BASED = "confidence_based"  # 置信度基础

@dataclass
class TradeParameters:
    """交易参数"""
    symbol: str
    entry_price: float
    stop_loss: float
    take_profit: float
    position_size: float
    risk_amount: float
    risk_percent: float
    potential_profit: float
    risk_reward_ratio: float
    confidence: float
    adjusted_stop_loss: Optional[float] = None
    adjusted_take_profit: Optional[float] = None
    max_position_size: Optional[float] = None
    volatility_factor: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    def print_summary(self):
        """打印交易参数摘要"""
        print("=" * 60)
        print(f"📊 交易参数: {self.symbol}")
        print("=" * 60)
        
        # 价格信息
        print(f"💰 入场价格: ${self.entry_price:,.2f}")
        print(f"🛑 止损价格: ${self.stop_loss:,.2f}")
        print(f"🎯 止盈价格: ${self.take_profit:,.2f}")
        
        # 风险信息
        stop_distance = abs(self.entry_price - self.stop_loss) / self.entry_price * 100
        profit_distance = abs(self.take_profit - self.entry_price) / self.entry_price * 100
        
        print(f"📏 止损距离: {stop_distance:.2f}%")
        print(f"📏 止盈距离: {profit_distance:.2f}%")
        print(f"⚖️  风险回报比: {self.risk_reward_ratio:.2f}:1")
        
        # 仓位信息
        print(f"📦 仓位大小: {self.position_size:.6f}")
        print(f"💸 风险金额: ${self.risk_amount:,.2f}")
        print(f"📊 风险比例: {self.risk_percent:.2%}")
        print(f"💰 潜在利润: ${self.potential_profit:,.2f}")
        
        # 调整后的参数
        if self.adjusted_stop_loss:
            adjusted_stop_distance = abs(self.entry_price - self.adjusted_stop_loss) / self.entry_price * 100
            print(f"🔧 调整止损: ${self.adjusted_stop_loss:,.2f} ({adjusted_stop_distance:.2f}%)")
        
        if self.adjusted_take_profit:
            adjusted_profit_distance = abs(self.adjusted_take_profit - self.entry_price) / self.entry_price * 100
            print(f"🔧 调整止盈: ${self.adjusted_take_profit:,.2f} ({adjusted_profit_distance:.2f}%)")
        
        if self.max_position_size:
            print(f"📈 最大仓位: {self.max_position_size:.6f}")
        
        if self.volatility_factor:
            print(f"📊 波动率因子: {self.volatility_factor:.2f}")
        
        print(f"🎯 置信度: {self.confidence:.1%}")
        print("=" * 60)

@dataclass
class PortfolioRisk:
    """投资组合风险"""
    total_value: float
    total_risk: float
    max_drawdown: float
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    var_95: Optional[float] = None  # 95% VaR
    cvar_95: Optional[float] = None  # 95% CVaR
    correlation_matrix: Optional[pd.DataFrame] = None
    risk_contributions: Optional[Dict[str, float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        if self.correlation_matrix is not None:
            data['correlation_matrix'] = self.correlation_matrix.to_dict()
        return data
    
    def print_summary(self):
        """打印投资组合风险摘要"""
        print("=" * 60)
        print("📊 投资组合风险分析")
        print("=" * 60)
        
        print(f"💰 总价值: ${self.total_value:,.2f}")
        print(f"⚠️  总风险: ${self.total_risk:,.2f} ({self.total_risk/self.total_value:.2%})")
        print(f"📉 最大回撤: {self.max_drawdown:.2%}")
        
        if self.sharpe_ratio is not None:
            print(f"📈 夏普比率: {self.sharpe_ratio:.2f}")
        
        if self.sortino_ratio is not None:
            print(f"📊 索提诺比率: {self.sortino_ratio:.2f}")
        
        if self.var_95 is not None:
            print(f"🎯 95% VaR: ${self.var_95:,.2f} ({self.var_95/self.total_value:.2%})")
        
        if self.cvar_95 is not None:
            print(f"🎯 95% CVaR: ${self.cvar_95:,.2f} ({self.cvar_95/self.total_value:.2%})")
        
        if self.risk_contributions:
            print(f"📋 风险贡献:")
            for symbol, contribution in list(self.risk_contributions.items())[:5]:
                print(f"  {symbol}: {contribution:.2%}")
        
        print("=" * 60)

class RiskManager:
    """风险管理器"""
    
    def __init__(
        self,
        account_size: float = 10000,
        max_risk_per_trade: float = 0.02,  # 2% per trade
        max_drawdown: float = 0.20,        # 20% max drawdown
        risk_free_rate: float = 0.02,      # 2% risk-free rate
        config_path: Optional[str] = None
    ):
        """
        初始化风险管理器
        
        参数:
            account_size: 账户规模
            max_risk_per_trade: 单笔交易最大风险比例
            max_drawdown: 最大回撤限制
            risk_free_rate: 无风险利率
            config_path: 配置文件路径
        """
        self.account_size = account_size
        self.max_risk_per_trade = max_risk_per_trade
        self.max_drawdown = max_drawdown
        self.risk_free_rate = risk_free_rate
        
        self.config_path = config_path or "config/risk.yaml"
        self.config = self.load_config()
        
        # 交易历史
        self.trade_history = []
        self.current_drawdown = 0.0
        self.current_risk_exposure = 0.0
        
        logger.info(f"风险管理器初始化完成，账户规模: ${account_size:,.2f}")
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置"""
        config_file = Path(self.config_path)
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.error(f"加载风险配置失败: {e}")
                return {}
        
        # 默认配置
        return {
            "stop_loss_methods": {
                "fixed_percent": {
                    "long": 0.03,   # 3% for long
                    "short": 0.03   # 3% for short
                },
                "atr_based": {
                    "multiplier": 2.0,  # 2x ATR
                    "min_percent": 0.01,  # 至少1%
                    "max_percent": 0.10   # 最多10%
                },
                "support_resistance": {
                    "buffer_percent": 0.005  # 0.5% buffer
                }
            },
            "take_profit_methods": {
                "risk_reward": {
                    "min_ratio": 1.5,
                    "target_ratio": 2.0,
                    "max_ratio": 3.0
                },
                "resistance_support": {
                    "use_key_levels": True,
                    "buffer_percent": 0.005
                },
                "trailing_stop": {
                    "activation_percent": 0.05,  # 5% profit激活
                    "trailing_percent": 0.02     # 2% trailing
                }
            },
            "position_sizing": {
                "methods": {
                    "fixed_risk": {
                        "base_risk": 0.02,
                        "confidence_multiplier": {
                            "very_high": 1.5,
                            "high": 1.2,
                            "medium": 1.0,
                            "low": 0.5
                        }
                    },
                    "kelly_criterion": {
                        "max_fraction": 0.25,  # 最大凯利分数
                        "min_fraction": 0.01   # 最小凯利分数
                    },
                    "volatility_adjusted": {
                        "target_volatility": 0.20,  # 20%年化波动率
                        "lookback_period": 20       # 20天
                    }
                },
                "constraints": {
                    "max_position_per_symbol": 0.20,  # 单个标的最大仓位
                    "max_total_exposure": 0.50,       # 总风险暴露
                    "min_position_size": 0.001        # 最小仓位
                }
            },
            "portfolio_risk": {
                "var_confidence": 0.95,
                "lookback_period": 252,  # 1年交易日
                "correlation_lookback": 63  # 3个月
            }
        }
    
    def calculate_trade(
        self,
        symbol: str,
        entry_price: float,
        stop_loss: float,
        confidence: float = 0.5,
        direction: str = "long",
        volatility: Optional[float] = None,
        method: PositionSizeMethod = PositionSizeMethod.FIXED_RISK,
        use_adjusted_stops: bool = True
    ) -> TradeParameters:
        """
        计算交易参数
        
        参数:
            symbol: 交易对符号
            entry_price: 入场价格
            stop_loss: 止损价格
            confidence: 交易置信度 (0-1)
            direction: 交易方向 (long/short)
            volatility: 波动率 (年化)
            method: 仓位计算方法
            use_adjusted_stops: 是否使用调整后的止损止盈
        
        返回:
            TradeParameters: 交易参数
        """
        logger.info(f"计算交易参数: {symbol} @ ${entry_price:,.2f}")
        
        try:
            # 1. 计算止损距离
            if direction == "long":
                stop_distance = (entry_price - stop_loss) / entry_price
                stop_distance_abs = entry_price - stop_loss
            else:  # short
                stop_distance = (stop_loss - entry_price) / entry_price
                stop_distance_abs = stop_loss - entry_price
            
            # 2. 调整止损（如果需要）
            adjusted_stop_loss = None
            if use_adjusted_stops and volatility:
                adjusted_stop_loss = self._adjust_stop_loss(
                    entry_price, stop_loss, direction, volatility
                )
            
            # 3. 计算止盈
            take_profit = self._calculate_take_profit(
                entry_price, stop_loss, direction, confidence
            )
            
            # 4. 调整止盈（如果需要）
            adjusted_take_profit = None
            if use_adjusted_stops:
                adjusted_take_profit = self._adjust_take_profit(
                    entry_price, take_profit, direction, confidence
                )
            
            # 5. 计算风险回报比
            if direction == "long":
                profit_distance = (take_profit - entry_price) / entry_price
                profit_distance_abs = take_profit - entry_price
            else:  # short
                profit_distance = (entry_price - take_profit) / entry_price
                profit_distance_abs = entry_price - take_profit
            
            risk_reward_ratio = profit_distance / stop_distance if stop_distance > 0 else 0
            
            # 6. 计算仓位大小
            position_size = self._calculate_position_size(
                entry_price, stop_loss, direction, confidence, volatility, method
            )
            
            # 7. 计算风险金额
            risk_amount = position_size * stop_distance_abs
            risk_percent = risk_amount / self.account_size
            
            # 8. 计算潜在利润
            potential_profit = position_size * profit_distance_abs
            
            # 9. 检查约束
            max_position_size = self._get_max_position_size(symbol, volatility)
            
            # 如果仓位超过限制，调整
            if position_size > max_position_size:
                logger.warning(f"仓位大小超过限制: {position_size:.6f} > {max_position_size:.6f}")
                position_size = max_position_size
                risk_amount = position_size * stop_distance_abs
                risk_percent = risk_amount / self.account_size
                potential_profit = position_size * profit_distance_abs
            
            # 10. 创建交易参数
            trade_params = TradeParameters(
                symbol=symbol,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                position_size=position_size,
                risk_amount=risk_amount,
                risk_percent=risk_percent,
                potential_profit=potential_profit,
                risk_reward_ratio=risk_reward_ratio,
                confidence=confidence,
                adjusted_stop_loss=adjusted_stop_loss,
                adjusted_take_profit=adjusted_take_profit,
                max_position_size=max_position_size,
                volatility_factor=volatility
            )
            
            logger.info(f"交易参数计算完成: 仓位={position_size:.6f}, 风险=${risk_amount:,.2f}, 风险回报比={risk_reward_ratio:.2f}")
            return trade_params
            
        except Exception as e:
            logger.error(f"计算交易参数失败: {e}")
            raise
    
    def _adjust_stop_loss(
        self,
        entry_price: float,
        stop_loss: float,
        direction: str,
        volatility: float
    ) -> float:
        """调整止损价格"""
        try:
            config = self.config["stop_loss_methods"]
            
            # 1. ATR基础止损
            if "atr_based" in config:
                atr_config = config["atr_based"]
                
                # 计算ATR距离（假设volatility是年化波动率）
                daily_volatility = volatility / np.sqrt(252)
                atr_distance = daily_volatility * atr_config["multiplier"]
                
                # 转换为价格距离
                price_distance = entry_price * atr_distance
                
                # 应用最小最大限制
                min_distance = entry_price * atr_config["min_percent"]
                max_distance = entry_price * atr_config["max_percent"]
                price_distance = max(min_distance, min(price_distance, max_distance))
                
                # 计算调整后的止损
                if direction == "long":
                    atr_stop_loss = entry_price - price_distance
                else:  # short
                    atr_stop_loss = entry_price + price_distance
                
                # 选择更保守的止损
                if direction == "long":
                    adjusted_stop_loss = min(stop_loss, atr_stop_loss)
                else:  # short
                    adjusted_stop_loss = max(stop_loss, atr_stop_loss)
                
                return adjusted_stop_loss
            
            return stop_loss
            
        except Exception as e:
            logger.error(f"调整止损失败: {e}")
            return stop_loss
    
    def _calculate_take_profit(
        self,
        entry_price: float,
        stop_loss: float,
        direction: str,
        confidence: float
    ) -> float:
        """计算止盈价格"""
        try:
            config = self.config["take_profit_methods"]
            
            # 计算止损距离
            if direction == "long":
                stop_distance = entry_price - stop_loss
            else:  # short
                stop_distance = stop_loss - entry_price
            
            # 1. 风险回报比方法
            if "risk_reward" in config["take_profit_methods"]:
                rr_config = config["take_profit_methods"]["risk_reward"]
                target_ratio = rr_config.get("target_ratio", 2.0)
                
                if direction == "long":
                    take_profit = entry_price + (stop_distance * target_ratio)
                else:  # short
                    take_profit = entry_price - (stop_distance * target_ratio)
            
            return take_profit
        
        except Exception as e:
            logger.error(f"计算止盈失败: {e}")
            # 默认使用2倍风险回报比
            if direction == "long":
                return entry_price + (stop_distance * 2.0)
            else:
                return entry_price - (stop_distance * 2.0)