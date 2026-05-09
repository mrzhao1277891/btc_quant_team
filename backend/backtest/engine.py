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
        
        # 记录策略配置详情
        self._log_strategy_config()
    
    def _log_strategy_config(self):
        """记录策略配置详情"""
        logger.info("=" * 80)
        logger.info("策略配置详情:")
        logger.info(f"  策略名称: {self.strategy_config.name}")
        logger.info(f"  时间周期: {self.strategy_config.timeframe}")
        logger.info(f"  初始资金: {self.strategy_config.initial_capital}")
        logger.info(f"  持仓大小类型: {self.strategy_config.position_size_type}")
        logger.info(f"  持仓大小值: {self.strategy_config.position_size_value}")
        logger.info(f"  杠杆倍数: {self.strategy_config.leverage}")
        
        # 做多开仓条件
        if self.strategy_config.long_entry_conditions:
            logger.info(f"\n  做多开仓条件 (逻辑: {self.strategy_config.long_entry_conditions.logic_operator.value}):")
            for i, cond in enumerate(self.strategy_config.long_entry_conditions.conditions, 1):
                logger.info(f"    {i}. {cond.indicator} {cond.operator.value} {cond.value}")
        
        # 做空开仓条件
        if self.strategy_config.short_entry_conditions:
            logger.info(f"\n  做空开仓条件 (逻辑: {self.strategy_config.short_entry_conditions.logic_operator.value}):")
            for i, cond in enumerate(self.strategy_config.short_entry_conditions.conditions, 1):
                logger.info(f"    {i}. {cond.indicator} {cond.operator.value} {cond.value}")
        
        # 做多平仓条件
        if self.strategy_config.long_exit_conditions:
            logger.info(f"\n  做多平仓条件 (逻辑: {self.strategy_config.long_exit_conditions.logic_operator.value}):")
            for i, cond in enumerate(self.strategy_config.long_exit_conditions.indicator_conditions, 1):
                logger.info(f"    {i}. {cond.indicator} {cond.operator.value} {cond.value}")
            if self.strategy_config.long_exit_conditions.take_profit_pct:
                logger.info(f"    止盈: {self.strategy_config.long_exit_conditions.take_profit_pct}%")
            if self.strategy_config.long_exit_conditions.stop_loss_pct:
                logger.info(f"    止损: {self.strategy_config.long_exit_conditions.stop_loss_pct}%")
        
        # 做空平仓条件
        if self.strategy_config.short_exit_conditions:
            logger.info(f"\n  做空平仓条件 (逻辑: {self.strategy_config.short_exit_conditions.logic_operator.value}):")
            for i, cond in enumerate(self.strategy_config.short_exit_conditions.indicator_conditions, 1):
                logger.info(f"    {i}. {cond.indicator} {cond.operator.value} {cond.value}")
            if self.strategy_config.short_exit_conditions.take_profit_pct:
                logger.info(f"    止盈: {self.strategy_config.short_exit_conditions.take_profit_pct}%")
            if self.strategy_config.short_exit_conditions.stop_loss_pct:
                logger.info(f"    止损: {self.strategy_config.short_exit_conditions.stop_loss_pct}%")
        
        logger.info("=" * 80)
    
    def _evaluate_condition(self, condition: IndicatorCondition, row: pd.Series) -> bool:
        """评估单个指标条件
        
        Args:
            condition: 指标条件对象
            row: 当前K线数据行
            
        Returns:
            bool: 条件是否满足
        """
        # 指标名称别名映射
        indicator_aliases = {
            'ema7': 'EMA7',
            'ema25': 'EMA25',
            'ema50': 'EMA50',
            'rsi14': 'RSI14',
            'rsi6': 'RSI6',
            'dif': 'MACD_DIF',
            'dea': 'MACD_DEA',
            'macd': 'MACD_Histogram',
            'boll_up': 'Bollinger_Upper',
            'boll_md': 'Bollinger_Middle',
            'boll_dn': 'Bollinger_Lower',
            'atr': 'ATR'
        }
        
        # 获取指标值
        indicator_name = condition.indicator
        
        # 尝试使用别名
        if indicator_name.lower() in indicator_aliases:
            indicator_name = indicator_aliases[indicator_name.lower()]
        
        # 特殊处理：Price指标使用close价格
        if indicator_name.lower() == "price" or indicator_name.lower() == "close":
            indicator_value = row.get('close')
        elif indicator_name.lower() == "volume":
            indicator_value = row.get('volume')
        else:
            # 尝试大小写不敏感的匹配
            indicator_value = None
            for col in row.index:
                if col.lower() == indicator_name.lower():
                    indicator_value = row.get(col)
                    break
            
            # 如果还是找不到，尝试直接获取
            if indicator_value is None:
                indicator_value = row.get(indicator_name)
        
        # 如果指标值不存在或为NaN，条件不满足
        if indicator_value is None or pd.isna(indicator_value):
            return False
        
        # 根据比较运算符评估条件
        operator = condition.operator
        target_value = condition.value
        
        # 如果target_value是字符串，可能是另一个指标名称
        if isinstance(target_value, str):
            # 尝试使用别名
            target_indicator_name = target_value
            if target_value.lower() in indicator_aliases:
                target_indicator_name = indicator_aliases[target_value.lower()]
            
            # 尝试获取对应的指标值
            target_indicator_value = None
            for col in row.index:
                if col.lower() == target_indicator_name.lower():
                    target_indicator_value = row.get(col)
                    break
            
            if target_indicator_value is None:
                target_indicator_value = row.get(target_indicator_name)
            
            # 如果找到了指标值，使用它；否则尝试转换为数值
            if target_indicator_value is not None and not pd.isna(target_indicator_value):
                target_value = float(target_indicator_value)
            else:
                # 尝试将字符串转换为数值
                try:
                    target_value = float(target_value)
                except (ValueError, TypeError):
                    logger.warning(f"Cannot convert target_value '{target_value}' to number and not found as indicator")
                    return False
        
        # 执行比较并返回结果
        result = False
        if operator == ComparisonOperator.GT:
            result = float(indicator_value) > float(target_value)
        elif operator == ComparisonOperator.LT:
            result = float(indicator_value) < float(target_value)
        elif operator == ComparisonOperator.GTE:
            result = float(indicator_value) >= float(target_value)
        elif operator == ComparisonOperator.LTE:
            result = float(indicator_value) <= float(target_value)
        elif operator == ComparisonOperator.EQ:
            result = abs(float(indicator_value) - float(target_value)) < 1e-9  # 浮点数相等比较
        elif operator == ComparisonOperator.RANGE:
            # target_value应该是一个元组(min, max)
            if isinstance(target_value, (tuple, list)) and len(target_value) == 2:
                min_val, max_val = target_value
                result = min_val <= indicator_value <= max_val
            else:
                logger.warning(f"RANGE operator requires tuple value, got {type(target_value)}")
                return False
        else:
            logger.warning(f"Unknown comparison operator: {operator}")
            return False
        
        return result
    
    def _evaluate_condition_with_log(self, condition: IndicatorCondition, row: pd.Series) -> tuple[bool, str]:
        """评估单个指标条件并返回详细日志
        
        Args:
            condition: 指标条件对象
            row: 当前K线数据行
            
        Returns:
            tuple[bool, str]: (条件是否满足, 评估详情日志)
        """
        # 指标名称别名映射
        indicator_aliases = {
            'ema7': 'ema7',
            'ema25': 'ema25',
            'ema50': 'ema50',
            'rsi14': 'rsi14',
            'rsi6': 'rsi6',
            'dif': 'dif',
            'dea': 'dea',
            'macd': 'macd',
            'boll_up': 'boll_up',
            'boll_md': 'boll_md',
            'boll_dn': 'boll_dn',
            'atr': 'atr'
        }
        
        # 获取指标值
        indicator_name = condition.indicator
        original_indicator_name = indicator_name
        
        # 尝试使用别名
        if indicator_name.lower() in indicator_aliases:
            indicator_name = indicator_aliases[indicator_name.lower()]
        
        # 特殊处理：Price指标使用close价格
        if indicator_name.lower() == "price" or indicator_name.lower() == "close":
            indicator_value = row.get('close')
        elif indicator_name.lower() == "volume":
            indicator_value = row.get('volume')
        else:
            # 尝试大小写不敏感的匹配
            indicator_value = None
            for col in row.index:
                if col.lower() == indicator_name.lower():
                    indicator_value = row.get(col)
                    break
            
            # 如果还是找不到，尝试直接获取
            if indicator_value is None:
                indicator_value = row.get(indicator_name)
        
        # 如果指标值不存在或为NaN，条件不满足
        if indicator_value is None or pd.isna(indicator_value):
            log_msg = f"    ❌ {original_indicator_name} {condition.operator.value} {condition.value} => 指标值不存在或为NaN"
            return False, log_msg
        
        # 根据比较运算符评估条件
        operator = condition.operator
        target_value = condition.value
        
        # 如果target_value是字符串，可能是另一个指标名称
        if isinstance(target_value, str):
            target_indicator_name = target_value
            if target_value.lower() in indicator_aliases:
                target_indicator_name = indicator_aliases[target_value.lower()]
            
            # 尝试获取对应的指标值
            target_indicator_value = None
            for col in row.index:
                if col.lower() == target_indicator_name.lower():
                    target_indicator_value = row.get(col)
                    break
            
            if target_indicator_value is None:
                target_indicator_value = row.get(target_indicator_name)
            
            # 如果找到了指标值，使用它；否则尝试转换为数值
            if target_indicator_value is not None and not pd.isna(target_indicator_value):
                target_value = float(target_indicator_value)
            else:
                try:
                    target_value = float(target_value)
                except (ValueError, TypeError):
                    log_msg = f"    ❌ {original_indicator_name} {condition.operator.value} {condition.value} => 目标值无法解析"
                    return False, log_msg
        
        # 执行比较
        result = False
        if operator == ComparisonOperator.GT:
            result = float(indicator_value) > float(target_value)
        elif operator == ComparisonOperator.LT:
            result = float(indicator_value) < float(target_value)
        elif operator == ComparisonOperator.GTE:
            result = float(indicator_value) >= float(target_value)
        elif operator == ComparisonOperator.LTE:
            result = float(indicator_value) <= float(target_value)
        elif operator == ComparisonOperator.EQ:
            result = abs(float(indicator_value) - float(target_value)) < 1e-9
        elif operator == ComparisonOperator.RANGE:
            if isinstance(target_value, (tuple, list)) and len(target_value) == 2:
                min_val, max_val = target_value
                result = min_val <= indicator_value <= max_val
        
        # 生成日志
        status = "✅" if result else "❌"
        log_msg = f"    {status} {original_indicator_name}({float(indicator_value):.4f}) {condition.operator.value} {target_value} => {result}"
        
        return result, log_msg
    
    def _evaluate_entry_conditions(self, row: pd.Series) -> bool:
        """评估开仓条件（旧版单向策略兼容方法）
        
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
    
    def _check_long_entry_signal(self, row: pd.Series) -> bool:
        """检测做多开仓信号
        
        评估策略配置中的做多开仓条件（long_entry_conditions）。
        
        Args:
            row: 当前K线数据行
            
        Returns:
            bool: 是否满足做多开仓条件
        """
        # 如果没有配置做多开仓条件，返回False
        if self.strategy_config.long_entry_conditions is None:
            return False
        
        long_entry_conditions = self.strategy_config.long_entry_conditions
        conditions = long_entry_conditions.conditions
        logic_operator = long_entry_conditions.logic_operator
        
        # 如果没有条件，返回False
        if not conditions:
            return False
        
        # 评估所有条件并记录日志
        results = []
        log_messages = []
        
        for cond in conditions:
            result, log_msg = self._evaluate_condition_with_log(cond, row)
            results.append(result)
            log_messages.append(log_msg)
        
        # 根据逻辑运算符组合结果
        if logic_operator == LogicOperator.AND:
            final_result = all(results)
        elif logic_operator == LogicOperator.OR:
            final_result = any(results)
        else:
            logger.warning(f"Unknown logic operator: {logic_operator}")
            final_result = False
        
        # 如果满足开多仓条件，记录详细日志
        if final_result:
            timestamp = row.get('timestamp', row.name)
            if hasattr(timestamp, 'to_pydatetime'):
                timestamp = timestamp.to_pydatetime()
            
            logger.info("=" * 80)
            logger.info(f"🟢 做多开仓信号触发 @ {timestamp}")
            logger.info(f"  价格: {row.get('close', 'N/A')}")
            logger.info(f"  逻辑运算符: {logic_operator.value}")
            logger.info(f"  条件评估结果:")
            for log_msg in log_messages:
                logger.info(log_msg)
            logger.info(f"  最终结果: {'✅ 满足' if final_result else '❌ 不满足'}")
            logger.info("=" * 80)
        
        return final_result
    
    def _check_short_entry_signal(self, row: pd.Series) -> bool:
        """检测做空开仓信号
        
        评估策略配置中的做空开仓条件（short_entry_conditions）。
        
        Args:
            row: 当前K线数据行
            
        Returns:
            bool: 是否满足做空开仓条件
        """
        # 如果没有配置做空开仓条件，返回False
        if self.strategy_config.short_entry_conditions is None:
            return False
        
        short_entry_conditions = self.strategy_config.short_entry_conditions
        conditions = short_entry_conditions.conditions
        logic_operator = short_entry_conditions.logic_operator
        
        # 如果没有条件，返回False
        if not conditions:
            return False
        
        # 评估所有条件并记录日志
        results = []
        log_messages = []
        
        for cond in conditions:
            result, log_msg = self._evaluate_condition_with_log(cond, row)
            results.append(result)
            log_messages.append(log_msg)
        
        # 根据逻辑运算符组合结果
        if logic_operator == LogicOperator.AND:
            final_result = all(results)
        elif logic_operator == LogicOperator.OR:
            final_result = any(results)
        else:
            logger.warning(f"Unknown logic operator: {logic_operator}")
            final_result = False
        
        # 如果满足开空仓条件，记录详细日志
        if final_result:
            timestamp = row.get('timestamp', row.name)
            if hasattr(timestamp, 'to_pydatetime'):
                timestamp = timestamp.to_pydatetime()
            
            logger.info("=" * 80)
            logger.info(f"🔴 做空开仓信号触发 @ {timestamp}")
            logger.info(f"  价格: {row.get('close', 'N/A')}")
            logger.info(f"  逻辑运算符: {logic_operator.value}")
            logger.info(f"  条件评估结果:")
            for log_msg in log_messages:
                logger.info(log_msg)
            logger.info(f"  最终结果: {'✅ 满足' if final_result else '❌ 不满足'}")
            logger.info("=" * 80)
        
        return final_result
    
    def _check_entry_signal(self, row: pd.Series) -> Tuple[bool, Optional[str]]:
        """检测开仓信号（双向策略支持）
        
        根据策略配置检测做多或做空信号。
        处理同时满足双向信号的情况：
        - 如果当前有持仓，保持当前持仓方向（不触发新信号）
        - 如果当前空仓，优先做多信号
        
        Args:
            row: 当前K线数据行
            
        Returns:
            Tuple[bool, Optional[str]]: (是否有开仓信号, 开仓方向 "long"/"short"/None)
        """
        # 检测做多和做空信号
        long_signal = self._check_long_entry_signal(row)
        short_signal = self._check_short_entry_signal(row)
        
        # 如果同时满足双向信号
        if long_signal and short_signal:
            # 如果当前有持仓，保持当前持仓方向（不触发新信号）
            if self.current_position is not None:
                logger.debug(
                    f"Both long and short signals triggered, but position exists. "
                    f"Maintaining current position direction: {self.current_position.direction}"
                )
                return False, None
            else:
                # 如果当前空仓，优先做多信号
                logger.debug(
                    "Both long and short signals triggered with no position. "
                    "Prioritizing long signal."
                )
                return True, "long"
        
        # 只有做多信号
        if long_signal:
            return True, "long"
        
        # 只有做空信号
        if short_signal:
            return True, "short"
        
        # 没有信号
        return False, None
    
    def _check_long_exit_signal(self, row: pd.Series, position: Position) -> Tuple[bool, str]:
        """检测做多平仓信号
        
        评估策略配置中的做多平仓条件（long_exit_conditions）。
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
        # 如果没有配置做多平仓条件，返回False
        if self.strategy_config.long_exit_conditions is None:
            return False, ""
        
        exit_conditions = self.strategy_config.long_exit_conditions
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
            
            # 使用逻辑运算符组合结果
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
    
    def _check_short_exit_signal(self, row: pd.Series, position: Position) -> Tuple[bool, str]:
        """检测做空平仓信号
        
        评估策略配置中的做空平仓条件（short_exit_conditions）。
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
        # 如果没有配置做空平仓条件，返回False
        if self.strategy_config.short_exit_conditions is None:
            return False, ""
        
        exit_conditions = self.strategy_config.short_exit_conditions
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
            
            # 使用逻辑运算符组合结果
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
    
    def _check_exit_signal(self, row: pd.Series, position: Position) -> Tuple[bool, str]:
        """检测平仓信号（双向策略支持）
        
        根据当前持仓方向调用对应的平仓检测方法。
        
        Args:
            row: 当前K线数据行
            position: 当前持仓对象
            
        Returns:
            Tuple[bool, str]: (是否平仓, 平仓原因)
        """
        if position.direction == "long":
            return self._check_long_exit_signal(row, position)
        elif position.direction == "short":
            return self._check_short_exit_signal(row, position)
        else:
            logger.warning(f"Unknown position direction: {position.direction}")
            return False, ""
    
    def _evaluate_exit_conditions(self, row: pd.Series, position: Position) -> Tuple[bool, str]:
        """评估平仓条件（旧版单向策略兼容方法）
        
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
    
    def _open_position(self, row: pd.Series, direction: str = None) -> Optional[Position]:
        """开仓
        
        Args:
            row: 当前K线数据行
            direction: 开仓方向 "long" 或 "short"，如果为None则使用旧版配置
            
        Returns:
            Optional[Position]: 创建的持仓对象，如果资金不足则返回None
        """
        entry_price = row['close']
        entry_time = row['timestamp'] if 'timestamp' in row.index else row.name
        # 转换 pandas Timestamp 为 Python datetime
        if hasattr(entry_time, 'to_pydatetime'):
            entry_time = entry_time.to_pydatetime()
        
        # 确定开仓方向（支持新版双向策略和旧版单向策略）
        if direction is None:
            # 旧版兼容：使用 position_direction 字段
            direction = self.strategy_config.position_direction
        
        # 计算持仓大小
        if self.strategy_config.position_size_type == "amount":
            # 绝对金额（这是实际仓位大小）
            position_value = self.strategy_config.position_size_value
        else:  # percentage
            # 百分比（基于当前资金）
            position_value = self.capital * (self.strategy_config.position_size_value / 100)
        
        # 获取杠杆倍数
        leverage = self.strategy_config.leverage
        
        logger.info(
            f"Opening {direction} position: position_size_type={self.strategy_config.position_size_type}, "
            f"position_size_value={self.strategy_config.position_size_value}, "
            f"position_value={position_value}, leverage={leverage}"
        )
        
        # 计算实际需要的保证金（本金）
        # 实际仓位 = 保证金 × 杠杆
        # 保证金 = 实际仓位 / 杠杆
        entry_capital = position_value / leverage
        
        # 检查资金是否足够（检查保证金是否足够）
        if entry_capital > self.capital:
            logger.warning(
                f"Insufficient capital for {direction} entry. Required margin: {entry_capital:.2f}, "
                f"Available: {self.capital:.2f}, Position value: {position_value:.2f}, "
                f"Leverage: {leverage}x. Skipping entry signal."
            )
            return None
        
        # 计算持仓数量（BTC数量）= 实际仓位 / 价格
        position_size = position_value / entry_price
        
        # 创建持仓对象
        position = Position(
            entry_time=entry_time,
            entry_price=entry_price,
            position_size=position_size,
            position_value=position_value,  # 实际仓位价值（含杠杆）
            direction=direction,
            entry_capital=entry_capital  # 实际使用的保证金
        )
        
        # 更新资金（扣除保证金）
        self.capital -= entry_capital
        
        logger.info(
            f"Position opened: {position.direction} {position.position_size:.6f} BTC "
            f"at {entry_price:.2f}, Position value: {position_value:.2f}, "
            f"Margin used: {entry_capital:.2f} (Leverage: {leverage}x), "
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
        # 转换 pandas Timestamp 为 Python datetime
        if hasattr(exit_time, 'to_pydatetime'):
            exit_time = exit_time.to_pydatetime()
        
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
            # 转换 pandas Timestamp 为 Python datetime
            if hasattr(timestamp, 'to_pydatetime'):
                timestamp = timestamp.to_pydatetime()
            equity_curve.append((timestamp, float(current_equity)))
            
            # 如果有持仓，先评估平仓条件
            if self.current_position is not None:
                # 使用新版双向平仓检测（根据持仓方向自动选择）
                should_exit, exit_reason = self._check_exit_signal(row, self.current_position)
                
                if should_exit:
                    # 平仓
                    trade = self._close_position(self.current_position, row, exit_reason)
                    self.trades.append(trade)
                    self.current_position = None
                else:
                    # 如果没有触发平仓条件，检查是否有反向信号
                    has_signal, signal_direction = self._check_entry_signal(row)
                    
                    if has_signal and signal_direction is not None:
                        # 如果信号方向与当前持仓方向相反，执行反向操作（先平后开）
                        if signal_direction != self.current_position.direction:
                            logger.info(
                                f"Reverse signal detected: current position is {self.current_position.direction}, "
                                f"new signal is {signal_direction}. Closing current position and opening new one."
                            )
                            # 先平仓
                            trade = self._close_position(self.current_position, row, "reverse_signal")
                            self.trades.append(trade)
                            self.current_position = None
                            
                            # 再开新仓
                            position = self._open_position(row, direction=signal_direction)
                            if position is not None:
                                self.current_position = position
                            else:
                                logger.warning(
                                    f"Failed to open {signal_direction} position after reverse signal due to insufficient capital"
                                )
            
            # 如果没有持仓，评估开仓条件
            if self.current_position is None:
                # 检查是否允许多仓位（当前实现只支持单仓位）
                if not self.strategy_config.allow_multiple_positions:
                    # 使用新版双向信号检测
                    has_signal, signal_direction = self._check_entry_signal(row)
                    
                    if has_signal and signal_direction is not None:
                        # 开仓
                        position = self._open_position(row, direction=signal_direction)
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
