#!/usr/bin/env python3
"""
BacktestEngine条件评估属性测试
使用Hypothesis进行基于属性的测试，验证入场信号生成、出场条件触发和OR逻辑功能

任务 5.2: 为条件评估编写属性测试
- Property 2: Entry Signal Generation
- Property 6: Exit Condition Triggering
- Property 7: OR Logic for Exit Conditions
"""

import pytest
import pandas as pd
import numpy as np
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime, timedelta

from backend.backtest.engine import BacktestEngine
from backend.backtest.models import (
    StrategyConfig,
    EntryConditions,
    ExitConditions,
    IndicatorCondition,
    ComparisonOperator,
    LogicOperator,
    Position
)


# ============================================================================
# Hypothesis策略：生成测试数据
# ============================================================================

@st.composite
def indicator_value_strategy(draw):
    """生成合理的指标值"""
    return draw(st.floats(min_value=0.1, max_value=100000.0, allow_nan=False, allow_infinity=False))


@st.composite
def market_row_strategy(draw):
    """生成市场数据行（包含价格和指标）"""
    base_price = draw(st.floats(min_value=10000.0, max_value=100000.0))
    
    return pd.Series({
        'timestamp': draw(st.integers(min_value=1609459200000, max_value=1704067200000)),
        'open': base_price,
        'high': base_price * draw(st.floats(min_value=1.0, max_value=1.05)),
        'low': base_price * draw(st.floats(min_value=0.95, max_value=1.0)),
        'close': base_price,
        'volume': draw(st.floats(min_value=100.0, max_value=1000000.0)),
        'EMA7': draw(indicator_value_strategy()),
        'EMA25': draw(indicator_value_strategy()),
        'EMA50': draw(indicator_value_strategy()),
        'RSI14': draw(st.floats(min_value=0.0, max_value=100.0)),
        'RSI6': draw(st.floats(min_value=0.0, max_value=100.0)),
        'MACD_DIF': draw(st.floats(min_value=-1000.0, max_value=1000.0)),
        'MACD_DEA': draw(st.floats(min_value=-1000.0, max_value=1000.0)),
        'MACD_Histogram': draw(st.floats(min_value=-500.0, max_value=500.0)),
        'Bollinger_Upper': base_price * 1.02,
        'Bollinger_Middle': base_price,
        'Bollinger_Lower': base_price * 0.98,
        'ATR': draw(st.floats(min_value=100.0, max_value=5000.0))
    })


@st.composite
def indicator_condition_strategy(draw, ensure_satisfiable=False):
    """生成指标条件"""
    indicator = draw(st.sampled_from([
        'EMA7', 'EMA25', 'EMA50', 'RSI14', 'RSI6', 
        'MACD_DIF', 'MACD_DEA', 'MACD_Histogram',
        'Bollinger_Upper', 'Bollinger_Middle', 'Bollinger_Lower',
        'ATR', 'Price', 'Volume'
    ]))
    
    operator = draw(st.sampled_from([
        ComparisonOperator.GT,
        ComparisonOperator.LT,
        ComparisonOperator.GTE,
        ComparisonOperator.LTE
    ]))
    
    # 生成合理的阈值
    if indicator.startswith('RSI'):
        value = draw(st.floats(min_value=0.0, max_value=100.0))
    elif indicator.startswith('MACD'):
        value = draw(st.floats(min_value=-1000.0, max_value=1000.0))
    elif indicator == 'ATR':
        value = draw(st.floats(min_value=100.0, max_value=5000.0))
    elif indicator in ['Price', 'Bollinger_Upper', 'Bollinger_Middle', 'Bollinger_Lower']:
        value = draw(st.floats(min_value=10000.0, max_value=100000.0))
    elif indicator == 'Volume':
        value = draw(st.floats(min_value=100.0, max_value=1000000.0))
    else:  # EMA
        value = draw(st.floats(min_value=0.1, max_value=100000.0))
    
    return IndicatorCondition(
        indicator=indicator,
        operator=operator,
        value=value
    )


@st.composite
def entry_conditions_strategy(draw, num_conditions=None):
    """生成开仓条件"""
    if num_conditions is None:
        num_conditions = draw(st.integers(min_value=1, max_value=4))
    
    conditions = [draw(indicator_condition_strategy()) for _ in range(num_conditions)]
    logic_operator = draw(st.sampled_from([LogicOperator.AND, LogicOperator.OR]))
    
    return EntryConditions(
        conditions=conditions,
        logic_operator=logic_operator
    )


@st.composite
def exit_conditions_strategy(draw, num_conditions=None):
    """生成出场条件"""
    if num_conditions is None:
        num_conditions = draw(st.integers(min_value=1, max_value=4))
    
    indicator_conditions = [draw(indicator_condition_strategy()) for _ in range(num_conditions)]
    
    # 随机决定是否包含止盈止损
    include_tp_sl = draw(st.booleans())
    
    if include_tp_sl:
        take_profit_pct = draw(st.floats(min_value=1.0, max_value=50.0))
        stop_loss_pct = draw(st.floats(min_value=1.0, max_value=30.0))
    else:
        take_profit_pct = None
        stop_loss_pct = None
    
    return ExitConditions(
        indicator_conditions=indicator_conditions,
        take_profit_amount=None,
        stop_loss_amount=None,
        take_profit_pct=take_profit_pct,
        stop_loss_pct=stop_loss_pct,
        logic_operator=LogicOperator.OR  # 默认使用OR逻辑
    )


@st.composite
def strategy_config_strategy(draw):
    """生成策略配置"""
    return StrategyConfig(
        name=draw(st.text(min_size=1, max_size=50)),
        description=draw(st.text(min_size=0, max_size=200)),
        timeframe=draw(st.sampled_from(['1m', '1w', '1d', '4h'])),
        position_direction=draw(st.sampled_from(['long', 'short'])),
        position_size_type=draw(st.sampled_from(['amount', 'percentage'])),
        position_size_value=draw(st.floats(min_value=1.0, max_value=100.0)),
        entry_conditions=draw(entry_conditions_strategy()),
        exit_conditions=draw(exit_conditions_strategy()),
        initial_capital=draw(st.floats(min_value=10000.0, max_value=1000000.0))
    )


@st.composite
def position_strategy(draw, direction='long'):
    """生成持仓对象"""
    entry_price = draw(st.floats(min_value=10000.0, max_value=100000.0))
    entry_capital = draw(st.floats(min_value=1000.0, max_value=100000.0))
    position_size = entry_capital / entry_price
    
    return Position(
        entry_time=datetime.now() - timedelta(days=draw(st.integers(min_value=1, max_value=30))),
        entry_price=entry_price,
        position_size=position_size,
        position_value=entry_capital,
        direction=direction,
        entry_capital=entry_capital
    )


# ============================================================================
# Property 2: Entry Signal Generation
# ============================================================================

class TestEntrySignalGeneration:
    """测试入场信号生成属性"""
    
    @given(
        row=market_row_strategy(),
        logic_operator=st.sampled_from([LogicOperator.AND, LogicOperator.OR])
    )
    @settings(max_examples=100, deadline=None)
    def test_property_2_entry_signal_generation_and_logic(self, row, logic_operator):
        """
        **Validates: Requirements 2.1, 2.2**
        
        Property 2: Entry Signal Generation
        For any set of indicator conditions and market data where all conditions 
        are satisfied according to the specified logic operator (AND/OR), 
        an entry signal SHALL be generated.
        
        测试AND/OR逻辑：所有条件都满足时应该生成入场信号
        """
        # 创建条件，确保它们都能被满足
        rsi_value = float(row['RSI14'])
        ema_value = float(row['EMA7'])
        
        # 确保值不是NaN
        assume(not pd.isna(rsi_value))
        assume(not pd.isna(ema_value))
        assume(ema_value > 1000.0)  # 确保有足够的空间
        
        # 创建两个必然满足的条件
        conditions = [
            IndicatorCondition(
                indicator='RSI14',
                operator=ComparisonOperator.LT,
                value=rsi_value + 10.0  # 确保条件满足
            ),
            IndicatorCondition(
                indicator='EMA7',
                operator=ComparisonOperator.GT,
                value=ema_value - 1000.0  # 确保条件满足
            )
        ]
        
        entry_conditions = EntryConditions(
            conditions=conditions,
            logic_operator=logic_operator
        )
        
        strategy = StrategyConfig(
            name="Test Strategy",
            description="Test",
            timeframe="1d",
            position_direction="long",
            position_size_type="amount",
            position_size_value=10000.0,
            entry_conditions=entry_conditions,
            exit_conditions=ExitConditions(indicator_conditions=[])
        )
        
        # 创建简单的K线数据
        kline_data = pd.DataFrame([row])
        engine = BacktestEngine(strategy, kline_data)
        
        # 评估入场条件
        result = engine._evaluate_entry_conditions(row)
        
        # 验证：当所有条件都满足时，应该生成入场信号
        assert result == True, \
            f"当所有条件都满足时（逻辑运算符={logic_operator}），应该生成入场信号"
    
    @given(row=market_row_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_2_entry_signal_or_logic_single_condition(self, row):
        """
        **Validates: Requirements 2.1, 2.2**
        
        Property 2: Entry Signal Generation (OR Logic)
        测试OR逻辑：至少一个条件满足时应该生成入场信号
        """
        rsi_value = float(row['RSI14'])
        
        # 创建两个条件：一个满足，一个不满足
        conditions = [
            IndicatorCondition(
                indicator='RSI14',
                operator=ComparisonOperator.LT,
                value=rsi_value + 10.0  # 这个条件满足
            ),
            IndicatorCondition(
                indicator='RSI14',
                operator=ComparisonOperator.GT,
                value=rsi_value + 20.0  # 这个条件不满足
            )
        ]
        
        entry_conditions = EntryConditions(
            conditions=conditions,
            logic_operator=LogicOperator.OR
        )
        
        strategy = StrategyConfig(
            name="Test Strategy",
            description="Test",
            timeframe="1d",
            position_direction="long",
            position_size_type="amount",
            position_size_value=10000.0,
            entry_conditions=entry_conditions,
            exit_conditions=ExitConditions(indicator_conditions=[])
        )
        
        kline_data = pd.DataFrame([row])
        engine = BacktestEngine(strategy, kline_data)
        
        # 评估入场条件
        result = engine._evaluate_entry_conditions(row)
        
        # 验证：OR逻辑下，至少一个条件满足时应该生成入场信号
        assert result == True, \
            "OR逻辑下，至少一个条件满足时应该生成入场信号"
    
    @given(row=market_row_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_2_no_signal_when_and_conditions_not_all_met(self, row):
        """
        **Validates: Requirements 2.1, 2.2**
        
        Property 2: Entry Signal Generation (AND Logic - Negative Case)
        测试AND逻辑：不是所有条件都满足时不应该生成入场信号
        """
        rsi_value = float(row['RSI14'])
        
        # 创建两个条件：一个满足，一个不满足
        conditions = [
            IndicatorCondition(
                indicator='RSI14',
                operator=ComparisonOperator.LT,
                value=rsi_value + 10.0  # 这个条件满足
            ),
            IndicatorCondition(
                indicator='RSI14',
                operator=ComparisonOperator.GT,
                value=rsi_value + 20.0  # 这个条件不满足
            )
        ]
        
        entry_conditions = EntryConditions(
            conditions=conditions,
            logic_operator=LogicOperator.AND
        )
        
        strategy = StrategyConfig(
            name="Test Strategy",
            description="Test",
            timeframe="1d",
            position_direction="long",
            position_size_type="amount",
            position_size_value=10000.0,
            entry_conditions=entry_conditions,
            exit_conditions=ExitConditions(indicator_conditions=[])
        )
        
        kline_data = pd.DataFrame([row])
        engine = BacktestEngine(strategy, kline_data)
        
        # 评估入场条件
        result = engine._evaluate_entry_conditions(row)
        
        # 验证：AND逻辑下，不是所有条件都满足时不应该生成入场信号
        assert result == False, \
            "AND逻辑下，不是所有条件都满足时不应该生成入场信号"


# ============================================================================
# Property 6: Exit Condition Triggering
# ============================================================================

class TestExitConditionTriggering:
    """测试出场条件触发属性"""
    
    @given(
        row=market_row_strategy(),
        position=position_strategy(direction='long')
    )
    @settings(max_examples=100, deadline=None)
    def test_property_6_exit_on_indicator_condition(self, row, position):
        """
        **Validates: Requirements 3.2, 3.3, 3.5**
        
        Property 6: Exit Condition Triggering
        For any open position where exit conditions are met (either indicator-based 
        or absolute value-based), the position SHALL be closed and a complete 
        Trade_Record SHALL be created.
        
        测试基于指标的出场条件触发
        """
        rsi_value = float(row['RSI14'])
        
        # 确保RSI值不是NaN
        assume(not pd.isna(rsi_value))
        assume(rsi_value > 10.0)  # 确保有足够的空间
        
        # 创建一个必然满足的出场条件
        exit_conditions = ExitConditions(
            indicator_conditions=[
                IndicatorCondition(
                    indicator='RSI14',
                    operator=ComparisonOperator.GT,
                    value=rsi_value - 10.0  # 确保条件满足
                )
            ],
            logic_operator=LogicOperator.OR
        )
        
        strategy = StrategyConfig(
            name="Test Strategy",
            description="Test",
            timeframe="1d",
            position_direction="long",
            position_size_type="amount",
            position_size_value=10000.0,
            entry_conditions=EntryConditions(conditions=[]),
            exit_conditions=exit_conditions
        )
        
        kline_data = pd.DataFrame([row])
        engine = BacktestEngine(strategy, kline_data)
        
        # 评估出场条件
        should_exit, exit_reason = engine._evaluate_exit_conditions(row, position)
        
        # 验证：当出场条件满足时，应该触发出场
        assert should_exit == True, \
            "当指标出场条件满足时，应该触发出场"
        assert exit_reason.startswith('indicator_'), \
            f"出场原因应该指示是基于指标的出场，实际原因: {exit_reason}"
    
    @given(
        row=market_row_strategy(),
        position=position_strategy(direction='long')
    )
    @settings(max_examples=100, deadline=None)
    def test_property_6_exit_on_take_profit_percentage(self, row, position):
        """
        **Validates: Requirements 3.2, 3.3, 3.5**
        
        Property 6: Exit Condition Triggering (Take Profit)
        测试百分比止盈触发
        """
        # 设置当前价格使其触发止盈（盈利超过10%）
        current_price = position.entry_price * 1.15  # 15%盈利
        row['close'] = current_price
        
        exit_conditions = ExitConditions(
            indicator_conditions=[],
            take_profit_pct=10.0,  # 10%止盈
            stop_loss_pct=5.0,
            logic_operator=LogicOperator.OR
        )
        
        strategy = StrategyConfig(
            name="Test Strategy",
            description="Test",
            timeframe="1d",
            position_direction=position.direction,
            position_size_type="amount",
            position_size_value=10000.0,
            entry_conditions=EntryConditions(conditions=[]),
            exit_conditions=exit_conditions
        )
        
        kline_data = pd.DataFrame([row])
        engine = BacktestEngine(strategy, kline_data)
        
        # 评估出场条件
        should_exit, exit_reason = engine._evaluate_exit_conditions(row, position)
        
        # 验证：当盈利达到止盈线时，应该触发出场
        assert should_exit == True, \
            "当盈利达到止盈线时，应该触发出场"
        assert exit_reason == "take_profit_percentage", \
            f"出场原因应该是百分比止盈，实际原因: {exit_reason}"
    
    @given(
        row=market_row_strategy(),
        position=position_strategy(direction='long')
    )
    @settings(max_examples=100, deadline=None)
    def test_property_6_exit_on_stop_loss_percentage(self, row, position):
        """
        **Validates: Requirements 3.2, 3.3, 3.5**
        
        Property 6: Exit Condition Triggering (Stop Loss)
        测试百分比止损触发
        """
        # 设置当前价格使其触发止损（亏损超过5%）
        current_price = position.entry_price * 0.92  # 8%亏损
        row['close'] = current_price
        
        exit_conditions = ExitConditions(
            indicator_conditions=[],
            take_profit_pct=10.0,
            stop_loss_pct=5.0,  # 5%止损
            logic_operator=LogicOperator.OR
        )
        
        strategy = StrategyConfig(
            name="Test Strategy",
            description="Test",
            timeframe="1d",
            position_direction=position.direction,
            position_size_type="amount",
            position_size_value=10000.0,
            entry_conditions=EntryConditions(conditions=[]),
            exit_conditions=exit_conditions
        )
        
        kline_data = pd.DataFrame([row])
        engine = BacktestEngine(strategy, kline_data)
        
        # 评估出场条件
        should_exit, exit_reason = engine._evaluate_exit_conditions(row, position)
        
        # 验证：当亏损达到止损线时，应该触发出场
        assert should_exit == True, \
            "当亏损达到止损线时，应该触发出场"
        assert exit_reason == "stop_loss_percentage", \
            f"出场原因应该是百分比止损，实际原因: {exit_reason}"


# ============================================================================
# Property 7: OR Logic for Exit Conditions
# ============================================================================

class TestExitConditionsORLogic:
    """测试出场条件OR逻辑属性"""
    
    @given(
        row=market_row_strategy(),
        position=position_strategy(direction='long')
    )
    @settings(max_examples=100, deadline=None)
    def test_property_7_or_logic_any_condition_triggers_exit(self, row, position):
        """
        **Validates: Requirements 3.4**
        
        Property 7: OR Logic for Exit Conditions
        For any set of exit conditions combined with OR logic, if any single 
        condition is satisfied, the position SHALL be closed.
        
        测试OR逻辑：任一条件满足即触发出场
        """
        rsi_value = float(row['RSI14'])
        ema_value = float(row['EMA7'])
        
        # 创建多个出场条件：确保至少一个满足
        exit_conditions = ExitConditions(
            indicator_conditions=[
                IndicatorCondition(
                    indicator='RSI14',
                    operator=ComparisonOperator.GT,
                    value=max(0.0, rsi_value - 10.0)  # 这个条件满足
                ),
                IndicatorCondition(
                    indicator='EMA7',
                    operator=ComparisonOperator.LT,
                    value=ema_value + 10000.0  # 这个条件不满足
                ),
                IndicatorCondition(
                    indicator='RSI14',
                    operator=ComparisonOperator.LT,
                    value=rsi_value - 50.0  # 这个条件也不满足
                )
            ],
            logic_operator=LogicOperator.OR
        )
        
        strategy = StrategyConfig(
            name="Test Strategy",
            description="Test",
            timeframe="1d",
            position_direction=position.direction,
            position_size_type="amount",
            position_size_value=10000.0,
            entry_conditions=EntryConditions(conditions=[]),
            exit_conditions=exit_conditions
        )
        
        kline_data = pd.DataFrame([row])
        engine = BacktestEngine(strategy, kline_data)
        
        # 评估出场条件
        should_exit, exit_reason = engine._evaluate_exit_conditions(row, position)
        
        # 验证：OR逻辑下，任一条件满足即应该触发出场
        assert should_exit == True, \
            "OR逻辑下，任一条件满足即应该触发出场"
        assert exit_reason.startswith('indicator_'), \
            f"出场原因应该指示是基于指标的出场，实际原因: {exit_reason}"
    
    @given(
        row=market_row_strategy(),
        position=position_strategy(direction='long')
    )
    @settings(max_examples=100, deadline=None)
    def test_property_7_or_logic_multiple_conditions_first_triggers(self, row, position):
        """
        **Validates: Requirements 3.4**
        
        Property 7: OR Logic for Exit Conditions (Multiple Satisfied)
        测试OR逻辑：多个条件同时满足时，应该记录第一个满足的条件
        """
        rsi_value = float(row['RSI14'])
        
        # 创建多个都满足的出场条件
        exit_conditions = ExitConditions(
            indicator_conditions=[
                IndicatorCondition(
                    indicator='RSI14',
                    operator=ComparisonOperator.GT,
                    value=max(0.0, rsi_value - 10.0)  # 第一个条件满足
                ),
                IndicatorCondition(
                    indicator='RSI14',
                    operator=ComparisonOperator.LT,
                    value=rsi_value + 10.0  # 第二个条件也满足
                )
            ],
            logic_operator=LogicOperator.OR
        )
        
        strategy = StrategyConfig(
            name="Test Strategy",
            description="Test",
            timeframe="1d",
            position_direction=position.direction,
            position_size_type="amount",
            position_size_value=10000.0,
            entry_conditions=EntryConditions(conditions=[]),
            exit_conditions=exit_conditions
        )
        
        kline_data = pd.DataFrame([row])
        engine = BacktestEngine(strategy, kline_data)
        
        # 评估出场条件
        should_exit, exit_reason = engine._evaluate_exit_conditions(row, position)
        
        # 验证：应该触发出场
        assert should_exit == True, \
            "当多个条件都满足时，应该触发出场"
        assert exit_reason.startswith('indicator_'), \
            "出场原因应该指示是基于指标的出场"
    
    @given(
        row=market_row_strategy(),
        position=position_strategy(direction='long')
    )
    @settings(max_examples=100, deadline=None)
    def test_property_7_or_logic_no_exit_when_no_conditions_met(self, row, position):
        """
        **Validates: Requirements 3.4**
        
        Property 7: OR Logic for Exit Conditions (Negative Case)
        测试OR逻辑：所有条件都不满足时不应该触发出场
        """
        rsi_value = float(row['RSI14'])
        
        # 创建多个都不满足的出场条件
        exit_conditions = ExitConditions(
            indicator_conditions=[
                IndicatorCondition(
                    indicator='RSI14',
                    operator=ComparisonOperator.GT,
                    value=rsi_value + 20.0  # 不满足
                ),
                IndicatorCondition(
                    indicator='RSI14',
                    operator=ComparisonOperator.LT,
                    value=max(0.0, rsi_value - 20.0)  # 不满足
                )
            ],
            logic_operator=LogicOperator.OR
        )
        
        strategy = StrategyConfig(
            name="Test Strategy",
            description="Test",
            timeframe="1d",
            position_direction=position.direction,
            position_size_type="amount",
            position_size_value=10000.0,
            entry_conditions=EntryConditions(conditions=[]),
            exit_conditions=exit_conditions
        )
        
        kline_data = pd.DataFrame([row])
        engine = BacktestEngine(strategy, kline_data)
        
        # 评估出场条件
        should_exit, exit_reason = engine._evaluate_exit_conditions(row, position)
        
        # 验证：当所有条件都不满足时，不应该触发出场
        assert should_exit == False, \
            "OR逻辑下，当所有条件都不满足时，不应该触发出场"
        assert exit_reason == "", \
            "当不触发出场时，出场原因应该为空"


# ============================================================================
# 综合测试：条件评估的完整性
# ============================================================================

class TestConditionEvaluationIntegration:
    """条件评估的综合集成测试"""
    
    @given(
        row=market_row_strategy(),
        direction=st.sampled_from(['long', 'short'])
    )
    @settings(max_examples=50, deadline=None)
    def test_entry_and_exit_evaluation_consistency(self, row, direction):
        """测试入场和出场条件评估的一致性"""
        # 创建简单的策略配置
        entry_conditions = EntryConditions(
            conditions=[
                IndicatorCondition(
                    indicator='RSI14',
                    operator=ComparisonOperator.LT,
                    value=50.0
                )
            ],
            logic_operator=LogicOperator.AND
        )
        
        exit_conditions = ExitConditions(
            indicator_conditions=[
                IndicatorCondition(
                    indicator='RSI14',
                    operator=ComparisonOperator.GT,
                    value=60.0
                )
            ],
            take_profit_pct=10.0,
            stop_loss_pct=5.0,
            logic_operator=LogicOperator.OR
        )
        
        strategy = StrategyConfig(
            name="Test Strategy",
            description="Test",
            timeframe="1d",
            position_direction=direction,
            position_size_type="amount",
            position_size_value=10000.0,
            entry_conditions=entry_conditions,
            exit_conditions=exit_conditions,
            initial_capital=100000.0
        )
        
        kline_data = pd.DataFrame([row])
        engine = BacktestEngine(strategy, kline_data)
        
        # 评估入场条件
        entry_result = engine._evaluate_entry_conditions(row)
        
        # 验证：结果应该是布尔值
        assert isinstance(entry_result, bool), \
            "入场条件评估结果应该是布尔值"
        
        # 创建持仓对象
        entry_price = float(row['close'])
        position = Position(
            entry_time=datetime.now(),
            entry_price=entry_price,
            position_size=1.0,
            position_value=entry_price,
            direction=direction,
            entry_capital=entry_price
        )
        
        should_exit, exit_reason = engine._evaluate_exit_conditions(row, position)
        
        # 验证：出场评估结果应该是布尔值和字符串
        assert isinstance(should_exit, bool), \
            "出场条件评估结果应该是布尔值"
        assert isinstance(exit_reason, str), \
            "出场原因应该是字符串"
        
        # 验证：如果触发出场，出场原因不应该为空
        if should_exit:
            assert len(exit_reason) > 0, \
                "如果触发出场，出场原因不应该为空"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
