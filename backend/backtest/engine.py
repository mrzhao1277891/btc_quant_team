"""
回测引擎模块

该模块实现回测引擎的核心逻辑，包括：
- 策略条件评估（开仓和平仓条件）
- 持仓管理（开仓、平仓、盈亏计算）
- 回测主循环执行
"""

import pandas as pd
from typing import Tuple, Optional
from datetime import datetime

from backend.backtest.models import (
    StrategyConfig,
    Position,
    TradeRecord,
    BacktestResult,
    PerformanceMetrics,
    IndicatorCondition,
    ComparisonOperator,
    LogicOperator
)
from backend.backtest.logger import logger
from backend.backtest.metrics import MetricsCalculator


class BacktestEngine:
    """回测引擎类
    
    负责执行策略回测的核心组件，管理持仓状态和交易记录。
    """
    
    def __init__(self, strategy_config: StrategyConfig, kline_data: pd.DataFrame):
        """初始化回测引擎
        
        Args:
            strategy_config: 策略配置对象
            kline_data: K线数据DataFrame，必须包含OHLCV和技术指标列
        """
        self.strategy_config = strategy_config
        self.kline_data = kline_data
        
        # 回测状态
        self.current_position: Optional[Position] = None
        self.trades: list[TradeRecord] = []
        self.capital = strategy_config.initial_capital
        self.trade_id_counter = 1
        
        logger.info(f"BacktestEngine initialized with strategy: {strategy_config.name}")
        logger.info(f"Initial capital: {self.capital}, Timeframe: {strategy_config.timeframe}")
    
    def _evaluate_condition(self, condition: IndicatorCondition, row: pd.Series) -> bool:
        """评估单个指标条件
        
        Args:
            condition: 指标条件对象
            row: 当前K线数据行
            
        Returns:
            bool: 条件是否满足
        """
        # 获取指标值
        indicator_name = condition.indicator
        
        # 特殊处理：Price指标使用close价格
        if indicator_name == "Price":
            indicator_value = row.get('close')
        elif indicator_name == "Volume":
            indicator_value = row.get('volume')
        else:
            indicator_value = row.get(indicator_name)
        
        # 如果指标值不存在或为NaN，条件不满足
        if indicator_value is None or pd.isna(indicator_value):
            return False
        
        # 根据比较运算符评估条件
        operator = condition.operator
        target_value = condition.value
        
        if operator == ComparisonOperator.GT:
            return indicator_value > target_value
        elif operator == ComparisonOperator.LT:
            return indicator_value < target_value
        elif operator == ComparisonOperator.GTE:
            return indicator_value >= target_value
        elif operator == ComparisonOperator.LTE:
            return indicator_value <= target_value
        elif operator == ComparisonOperator.EQ:
            return abs(indicator_value - target_value) < 1e-9  # 浮点数相等比较
        elif operator == ComparisonOperator.RANGE:
            # target_value应该是一个元组(min, max)
            if isinstance(target_value, (tuple, list)) and len(target_value) == 2:
                min_val, max_val = target_value
                return min_val <= indicator_value <= max_val
            else:
                logger.warning(f"RANGE operator requires tuple value, got {type(target_value)}")
                return False
        else:
            logger.warning(f"Unknown comparison operator: {operator}")
            return False
    
    def _evaluate_entry_conditions(self, row: pd.Series) -> bool:
        """评估开仓条件
        
        支持AND/OR逻辑运算符组合多个指标条件。
        
        Args:
            row: 当前K线数据行
            
        Returns:
            bool: 是否满足开仓条件
        """
        entry_conditions = self.strategy_config.entry_conditions
        conditions = entry_conditions.conditions
        logic_operator = entry_conditions.logic_operator
        
        # 如果没有条件，返回False
        if not conditions:
            return False
        
        # 评估所有条件
        results = [self._evaluate_condition(cond, row) for cond in conditions]
        
        # 根据逻辑运算符组合结果
        if logic_operator == LogicOperator.AND:
            return all(results)
        elif logic_operator == LogicOperator.OR:
            return any(results)
        else:
            logger.warning(f"Unknown logic operator: {logic_operator}")
            return False
    
    def _evaluate_exit_conditions(self, row: pd.Series, position: Position) -> Tuple[bool, str]:
        """评估平仓条件
        
        评估顺序：
        1. 绝对值止损（优先级最高）
        2. 绝对值止盈
        3. 百分比止损
        4. 百分比止盈
        5. 基于指标的平仓条件
        
        Args:
            row: 当前K线数据行
            position: 当前持仓对象
            
        Returns:
            Tuple[bool, str]: (是否平仓, 平仓原因)
        """
        exit_conditions = self.strategy_config.exit_conditions
        current_price = row['close']
        
        # 计算当前盈亏
        pnl_amount, pnl_pct = self._calculate_pnl(position, current_price)
        
        # 1. 检查绝对值止损（优先级最高）
        if exit_conditions.stop_loss_amount is not None:
            if pnl_amount <= -exit_conditions.stop_loss_amount:
                return True, "stop_loss_amount"
        
        # 2. 检查绝对值止盈
        if exit_conditions.take_profit_amount is not None:
            if pnl_amount >= exit_conditions.take_profit_amount:
                return True, "take_profit_amount"
        
        # 3. 检查百分比止损
        if exit_conditions.stop_loss_pct is not None:
            if pnl_pct <= -exit_conditions.stop_loss_pct:
                return True, "stop_loss_percentage"
        
        # 4. 检查百分比止盈
        if exit_conditions.take_profit_pct is not None:
            if pnl_pct >= exit_conditions.take_profit_pct:
                return True, "take_profit_percentage"
        
        # 5. 检查基于指标的平仓条件
        indicator_conditions = exit_conditions.indicator_conditions
        if indicator_conditions:
            results = [self._evaluate_condition(cond, row) for cond in indicator_conditions]
            
            # 使用OR逻辑：任一条件满足即平仓
            logic_operator = exit_conditions.logic_operator
            if logic_operator == LogicOperator.OR:
                if any(results):
                    # 找到第一个满足的条件作为平仓原因
                    for i, result in enumerate(results):
                        if result:
                            cond = indicator_conditions[i]
                            return True, f"indicator_{cond.indicator}_{cond.operator.value}"
            elif logic_operator == LogicOperator.AND:
                if all(results):
                    return True, "indicator_conditions_all_met"
        
        # 没有满足任何平仓条件
        return False, ""
    
    def _calculate_pnl(self, position: Position, current_price: float) -> Tuple[float, float]:
        """计算当前盈亏
        
        Args:
            position: 持仓对象
            current_price: 当前价格
            
        Returns:
            Tuple[float, float]: (绝对盈亏金额, 盈亏百分比)
        """
        if position.direction == "long":
            # 做多：盈亏 = (当前价格 - 开仓价格) * 持仓数量
            pnl_amount = (current_price - position.entry_price) * position.position_size
        else:  # short
            # 做空：盈亏 = (开仓价格 - 当前价格) * 持仓数量
            pnl_amount = (position.entry_price - current_price) * position.position_size
        
        # 计算盈亏百分比（相对于开仓资金）
        pnl_pct = (pnl_amount / position.entry_capital) * 100
        
        return pnl_amount, pnl_pct
    
    def _open_position(self, row: pd.Series) -> Optional[Position]:
        """开仓
        
        Args:
            row: 当前K线数据行
            
        Returns:
            Optional[Position]: 创建的持仓对象，如果资金不足则返回None
        """
        entry_price = row['close']
        entry_time = row['timestamp'] if 'timestamp' in row.index else row.name
        
        # 计算持仓大小
        if self.strategy_config.position_size_type == "amount":
            # 绝对金额
            entry_capital = self.strategy_config.position_size_value
        else:  # percentage
            # 百分比
            entry_capital = self.capital * (self.strategy_config.position_size_value / 100)
        
        # 检查资金是否足够
        if entry_capital > self.capital:
            logger.warning(
                f"Insufficient capital for entry. Required: {entry_capital}, "
                f"Available: {self.capital}. Skipping entry signal."
            )
            return None
        
        # 计算持仓数量（BTC数量）
        position_size = entry_capital / entry_price
        
        # 创建持仓对象
        position = Position(
            entry_time=entry_time,
            entry_price=entry_price,
            position_size=position_size,
            position_value=entry_capital,
            direction=self.strategy_config.position_direction,
            entry_capital=entry_capital
        )
        
        # 更新资金（扣除开仓资金）
        self.capital -= entry_capital
        
        logger.info(
            f"Position opened: {position.direction} {position.position_size:.6f} BTC "
            f"at {entry_price:.2f}, Capital used: {entry_capital:.2f}, "
            f"Remaining capital: {self.capital:.2f}"
        )
        
        return position
    
    def _close_position(self, position: Position, row: pd.Series, reason: str) -> TradeRecord:
        """平仓
        
        Args:
            position: 持仓对象
            row: 当前K线数据行
            reason: 平仓原因
            
        Returns:
            TradeRecord: 交易记录对象
        """
        exit_price = row['close']
        exit_time = row['timestamp'] if 'timestamp' in row.index else row.name
        
        # 计算盈亏
        pnl_amount, pnl_pct = self._calculate_pnl(position, exit_price)
        
        # 计算持仓时长
        if isinstance(position.entry_time, datetime) and isinstance(exit_time, datetime):
            holding_period = exit_time - position.entry_time
        else:
            # 如果时间戳不是datetime对象，尝试转换
            try:
                entry_dt = pd.to_datetime(position.entry_time)
                exit_dt = pd.to_datetime(exit_time)
                holding_period = exit_dt - entry_dt
            except:
                holding_period = pd.Timedelta(0)
        
        # 创建交易记录
        trade = TradeRecord(
            trade_id=self.trade_id_counter,
            entry_time=position.entry_time,
            entry_price=position.entry_price,
            exit_time=exit_time,
            exit_price=exit_price,
            position_size=position.position_size,
            direction=position.direction,
            profit_loss=pnl_amount,
            profit_loss_pct=pnl_pct,
            holding_period=holding_period,
            exit_reason=reason,
            entry_capital=position.entry_capital
        )
        
        # 更新资金（返还本金+盈亏）
        self.capital += position.entry_capital + pnl_amount
        
        # 增加交易ID计数器
        self.trade_id_counter += 1
        
        logger.info(
            f"Position closed: Trade #{trade.trade_id}, "
            f"P/L: {pnl_amount:.2f} ({pnl_pct:.2f}%), "
            f"Reason: {reason}, Capital: {self.capital:.2f}"
        )
        
        return trade
    
    def run(self) -> BacktestResult:
        """执行回测
        
        按时间顺序遍历K线数据，评估开仓和平仓条件，
        记录所有交易并计算性能指标。
        
        Returns:
            BacktestResult: 回测结果对象
        """
        logger.info("Starting backtest execution...")
        start_time = pd.Timestamp.now()
        
        # 确保数据按时间排序
        if 'timestamp' in self.kline_data.columns:
            self.kline_data = self.kline_data.sort_values('timestamp').reset_index(drop=True)
        
        # 权益曲线记录
        equity_curve = []
        
        # 遍历每一行K线数据
        for idx, row in self.kline_data.iterrows():
            # 记录当前权益
            current_equity = self.capital
            if self.current_position is not None:
                # 如果有持仓，加上持仓的当前价值
                current_price = row['close']
                pnl_amount, _ = self._calculate_pnl(self.current_position, current_price)
                current_equity += self.current_position.entry_capital + pnl_amount
            
            timestamp = row['timestamp'] if 'timestamp' in row.index else row.name
            equity_curve.append((timestamp, current_equity))
            
            # 如果有持仓，先评估平仓条件
            if self.current_position is not None:
                should_exit, exit_reason = self._evaluate_exit_conditions(row, self.current_position)
                
                if should_exit:
                    # 平仓
                    trade = self._close_position(self.current_position, row, exit_reason)
                    self.trades.append(trade)
                    self.current_position = None
            
            # 如果没有持仓，评估开仓条件
            if self.current_position is None:
                # 检查是否允许多仓位（当前实现只支持单仓位）
                if not self.strategy_config.allow_multiple_positions:
                    should_enter = self._evaluate_entry_conditions(row)
                    
                    if should_enter:
                        # 开仓
                        position = self._open_position(row)
                        if position is not None:
                            self.current_position = position
        
        # 如果回测结束时还有持仓，强制平仓
        if self.current_position is not None:
            last_row = self.kline_data.iloc[-1]
            logger.info("Backtest ended with open position, forcing close...")
            trade = self._close_position(self.current_position, last_row, "backtest_end")
            self.trades.append(trade)
            self.current_position = None
        
        # 计算执行时间
        end_time = pd.Timestamp.now()
        execution_time = (end_time - start_time).total_seconds()
        
        logger.info(f"Backtest completed in {execution_time:.2f} seconds")
        logger.info(f"Total trades: {len(self.trades)}")
        logger.info(f"Final capital: {self.capital:.2f}")
        
        # 计算性能指标
        if len(self.trades) > 0:
            # 创建权益曲线Series
            equity_series = pd.Series(
                [equity for _, equity in equity_curve],
                index=[timestamp for timestamp, _ in equity_curve]
            )
            
            # 计算收益率序列
            returns = equity_series.pct_change().dropna()
            
            # 使用MetricsCalculator计算所有指标
            calculator = MetricsCalculator(self.trades, self.strategy_config.initial_capital)
            metrics = calculator.calculate_all_metrics(equity_series, returns)
            
            logger.info(f"Performance metrics calculated: Win rate: {metrics.win_rate:.2%}, "
                       f"Max drawdown: {metrics.max_drawdown_pct:.2%}, "
                       f"Sharpe ratio: {metrics.sharpe_ratio:.2f}")
        else:
            # 如果没有交易，创建一个空的性能指标对象
            metrics = PerformanceMetrics(
                initial_capital=self.strategy_config.initial_capital,
                final_capital=self.capital,
                total_return=self.capital - self.strategy_config.initial_capital,
                total_return_pct=((self.capital - self.strategy_config.initial_capital) / 
                                 self.strategy_config.initial_capital * 100),
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0.0,
                avg_profit=0.0,
                avg_loss=0.0,
                profit_factor=0.0,
                max_drawdown=0.0,
                max_drawdown_pct=0.0,
                sharpe_ratio=0.0,
                longest_win_streak=0,
                longest_loss_streak=0
            )
            logger.info("No trades executed, metrics set to zero")
        
        # 创建回测结果对象
        result = BacktestResult(
            backtest_id=f"backtest_{start_time.strftime('%Y%m%d_%H%M%S')}",
            strategy_config=self.strategy_config,
            start_date=self.kline_data.iloc[0]['timestamp'] if 'timestamp' in self.kline_data.columns else pd.Timestamp.now(),
            end_date=self.kline_data.iloc[-1]['timestamp'] if 'timestamp' in self.kline_data.columns else pd.Timestamp.now(),
            trades=self.trades,
            metrics=metrics,
            equity_curve=equity_curve,
            data_quality_warnings=[],  # TODO: 从DatabaseConnector获取
            execution_time=execution_time
        )
        
        return result
