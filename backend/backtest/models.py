"""
核心数据模型

定义回测系统的所有数据结构，包括：
- StrategyConfig: 策略配置
- Position: 持仓信息
- TradeRecord: 交易记录
- PerformanceMetrics: 性能指标
- BacktestResult: 回测结果
"""

from dataclasses import dataclass, field, asdict
from typing import List, Literal, Optional, Tuple, Union
from enum import Enum
from datetime import datetime, timedelta
import json


class LogicOperator(Enum):
    """逻辑运算符"""
    AND = "AND"
    OR = "OR"


class ComparisonOperator(Enum):
    """比较运算符"""
    GT = ">"      # 大于
    LT = "<"      # 小于
    GTE = ">="    # 大于等于
    LTE = "<="    # 小于等于
    EQ = "=="     # 等于
    RANGE = "range"  # 范围内


@dataclass
class IndicatorCondition:
    """指标条件"""
    indicator: str              # 指标名称: "EMA7", "RSI14", "MACD_DIF", etc.
    operator: ComparisonOperator
    value: Union[float, Tuple[float, float]]  # 单值或范围(min, max)
    timeframe: str = "1d"       # 时间周期
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "indicator": self.indicator,
            "operator": self.operator.value if isinstance(self.operator, ComparisonOperator) else self.operator,
            "value": self.value,
            "timeframe": self.timeframe
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "IndicatorCondition":
        """从字典创建"""
        operator = data["operator"]
        if isinstance(operator, str):
            operator = ComparisonOperator(operator)
        return cls(
            indicator=data["indicator"],
            operator=operator,
            value=data["value"],
            timeframe=data.get("timeframe", "1d")
        )


@dataclass
class EntryConditions:
    """开仓条件"""
    conditions: List[IndicatorCondition]
    logic_operator: LogicOperator = LogicOperator.AND
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "conditions": [c.to_dict() for c in self.conditions],
            "logic_operator": self.logic_operator.value if isinstance(self.logic_operator, LogicOperator) else self.logic_operator
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "EntryConditions":
        """从字典创建"""
        logic_op = data.get("logic_operator", "AND")
        if isinstance(logic_op, str):
            logic_op = LogicOperator(logic_op)
        return cls(
            conditions=[IndicatorCondition.from_dict(c) for c in data["conditions"]],
            logic_operator=logic_op
        )


@dataclass
class ExitConditions:
    """平仓条件"""
    indicator_conditions: List[IndicatorCondition]  # 基于指标的平仓条件
    take_profit_amount: Optional[float] = None      # 止盈金额
    stop_loss_amount: Optional[float] = None        # 止损金额
    take_profit_pct: Optional[float] = None         # 止盈百分比
    stop_loss_pct: Optional[float] = None           # 止损百分比
    logic_operator: LogicOperator = LogicOperator.OR  # 任一条件触发即平仓
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "indicator_conditions": [c.to_dict() for c in self.indicator_conditions],
            "take_profit_amount": self.take_profit_amount,
            "stop_loss_amount": self.stop_loss_amount,
            "take_profit_pct": self.take_profit_pct,
            "stop_loss_pct": self.stop_loss_pct,
            "logic_operator": self.logic_operator.value if isinstance(self.logic_operator, LogicOperator) else self.logic_operator
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ExitConditions":
        """从字典创建"""
        logic_op = data.get("logic_operator", "OR")
        if isinstance(logic_op, str):
            logic_op = LogicOperator(logic_op)
        return cls(
            indicator_conditions=[IndicatorCondition.from_dict(c) for c in data.get("indicator_conditions", [])],
            take_profit_amount=data.get("take_profit_amount"),
            stop_loss_amount=data.get("stop_loss_amount"),
            take_profit_pct=data.get("take_profit_pct"),
            stop_loss_pct=data.get("stop_loss_pct"),
            logic_operator=logic_op
        )


@dataclass
class StrategyConfig:
    """策略配置"""
    name: str
    description: str
    timeframe: str                    # 主时间周期
    position_direction: Literal["long", "short"]
    position_size_type: Literal["amount", "percentage"]
    position_size_value: float
    entry_conditions: EntryConditions
    exit_conditions: ExitConditions
    initial_capital: float = 100000.0
    allow_multiple_positions: bool = False
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "timeframe": self.timeframe,
            "position_direction": self.position_direction,
            "position_size_type": self.position_size_type,
            "position_size_value": self.position_size_value,
            "entry_conditions": self.entry_conditions.to_dict(),
            "exit_conditions": self.exit_conditions.to_dict(),
            "initial_capital": self.initial_capital,
            "allow_multiple_positions": self.allow_multiple_positions
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "StrategyConfig":
        """从字典创建"""
        return cls(
            name=data["name"],
            description=data["description"],
            timeframe=data["timeframe"],
            position_direction=data["position_direction"],
            position_size_type=data["position_size_type"],
            position_size_value=data["position_size_value"],
            entry_conditions=EntryConditions.from_dict(data["entry_conditions"]),
            exit_conditions=ExitConditions.from_dict(data["exit_conditions"]),
            initial_capital=data.get("initial_capital", 100000.0),
            allow_multiple_positions=data.get("allow_multiple_positions", False)
        )
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> "StrategyConfig":
        """从JSON字符串创建"""
        return cls.from_dict(json.loads(json_str))


@dataclass
class Position:
    """持仓信息"""
    entry_time: datetime
    entry_price: float
    position_size: float            # 持仓数量（BTC数量）
    position_value: float           # 持仓价值（USDT）
    direction: Literal["long", "short"]
    entry_capital: float            # 开仓时使用的资金
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "entry_time": self.entry_time.isoformat(),
            "entry_price": self.entry_price,
            "position_size": self.position_size,
            "position_value": self.position_value,
            "direction": self.direction,
            "entry_capital": self.entry_capital
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Position":
        """从字典创建"""
        return cls(
            entry_time=datetime.fromisoformat(data["entry_time"]) if isinstance(data["entry_time"], str) else data["entry_time"],
            entry_price=data["entry_price"],
            position_size=data["position_size"],
            position_value=data["position_value"],
            direction=data["direction"],
            entry_capital=data["entry_capital"]
        )


@dataclass
class TradeRecord:
    """交易记录"""
    trade_id: int
    entry_time: datetime
    entry_price: float
    exit_time: datetime
    exit_price: float
    position_size: float
    direction: Literal["long", "short"]
    profit_loss: float              # 盈亏金额
    profit_loss_pct: float          # 盈亏百分比
    holding_period: timedelta       # 持仓时长
    exit_reason: str                # 平仓原因
    entry_capital: float            # 开仓资金
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "trade_id": self.trade_id,
            "entry_time": self.entry_time.isoformat(),
            "entry_price": self.entry_price,
            "exit_time": self.exit_time.isoformat(),
            "exit_price": self.exit_price,
            "position_size": self.position_size,
            "direction": self.direction,
            "profit_loss": self.profit_loss,
            "profit_loss_pct": self.profit_loss_pct,
            "holding_period": str(self.holding_period),
            "exit_reason": self.exit_reason,
            "entry_capital": self.entry_capital
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "TradeRecord":
        """从字典创建"""
        return cls(
            trade_id=data["trade_id"],
            entry_time=datetime.fromisoformat(data["entry_time"]) if isinstance(data["entry_time"], str) else data["entry_time"],
            entry_price=data["entry_price"],
            exit_time=datetime.fromisoformat(data["exit_time"]) if isinstance(data["exit_time"], str) else data["exit_time"],
            exit_price=data["exit_price"],
            position_size=data["position_size"],
            direction=data["direction"],
            profit_loss=data["profit_loss"],
            profit_loss_pct=data["profit_loss_pct"],
            holding_period=timedelta(seconds=float(data["holding_period"].split()[0])) if isinstance(data["holding_period"], str) else data["holding_period"],
            exit_reason=data["exit_reason"],
            entry_capital=data["entry_capital"]
        )


@dataclass
class PerformanceMetrics:
    """性能指标"""
    initial_capital: float
    final_capital: float
    total_return: float             # 总收益金额
    total_return_pct: float         # 总收益率百分比
    
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float                 # 胜率
    
    avg_profit: float               # 平均盈利
    avg_loss: float                 # 平均亏损
    profit_factor: float            # 盈亏比
    
    max_drawdown: float             # 最大回撤金额
    max_drawdown_pct: float         # 最大回撤百分比
    
    sharpe_ratio: float             # 夏普比率
    
    longest_win_streak: int         # 最长连胜
    longest_loss_streak: int        # 最长连亏
    
    total_fees: float = 0.0         # 总手续费（暂不实现）
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "PerformanceMetrics":
        """从字典创建"""
        return cls(**data)


@dataclass
class BacktestResult:
    """回测结果"""
    backtest_id: str
    strategy_config: StrategyConfig
    start_date: datetime
    end_date: datetime
    trades: List[TradeRecord]
    metrics: PerformanceMetrics
    equity_curve: List[Tuple[datetime, float]]  # 权益曲线 (timestamp, capital)
    data_quality_warnings: List[str]
    execution_time: float           # 执行时间（秒）
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "backtest_id": self.backtest_id,
            "strategy_config": self.strategy_config.to_dict(),
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "trades": [t.to_dict() for t in self.trades],
            "metrics": self.metrics.to_dict(),
            "equity_curve": [(t.isoformat(), c) for t, c in self.equity_curve],
            "data_quality_warnings": self.data_quality_warnings,
            "execution_time": self.execution_time
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "BacktestResult":
        """从字典创建"""
        return cls(
            backtest_id=data["backtest_id"],
            strategy_config=StrategyConfig.from_dict(data["strategy_config"]),
            start_date=datetime.fromisoformat(data["start_date"]) if isinstance(data["start_date"], str) else data["start_date"],
            end_date=datetime.fromisoformat(data["end_date"]) if isinstance(data["end_date"], str) else data["end_date"],
            trades=[TradeRecord.from_dict(t) for t in data["trades"]],
            metrics=PerformanceMetrics.from_dict(data["metrics"]),
            equity_curve=[(datetime.fromisoformat(t) if isinstance(t, str) else t, c) for t, c in data["equity_curve"]],
            data_quality_warnings=data["data_quality_warnings"],
            execution_time=data["execution_time"]
        )
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> "BacktestResult":
        """从JSON字符串创建"""
        return cls.from_dict(json.loads(json_str))
