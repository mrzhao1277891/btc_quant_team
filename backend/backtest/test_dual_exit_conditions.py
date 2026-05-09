"""
测试双向平仓条件评估功能

验证 BacktestEngine 的双向平仓条件检测方法：
- _check_long_exit_signal()
- _check_short_exit_signal()
- _check_exit_signal()
"""

import pytest
import pandas as pd
from datetime import datetime

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


def create_test_kline_data():
    """创建测试用的K线数据"""
    return pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=10, freq='1D'),
        'open': [50000.0] * 10,
        'high': [51000.0] * 10,
        'low': [49000.0] * 10,
        'close': [50000.0, 51000.0, 52000.0, 53000.0, 54000.0, 
                  53000.0, 52000.0, 51000.0, 50000.0, 49000.0],
        'volume': [100.0] * 10,
        'RSI14': [30, 35, 40, 45, 50, 55, 60, 65, 70, 75],
        'EMA7': [50000.0] * 10,
        'EMA25': [50000.0] * 10
    })


def test_check_long_exit_signal_with_take_profit_pct():
    """测试做多平仓信号 - 止盈百分比触发"""
    # 创建策略配置
    strategy_config = StrategyConfig(
        name="Test Long Exit",
        description="Test",
        timeframe="1d",
        position_size_type="amount",
        position_size_value=10000.0,
        initial_capital=100000.0,
        long_entry_conditions=EntryConditions(
            conditions=[IndicatorCondition("RSI14", ComparisonOperator.LT, 30)],
            logic_operator=LogicOperator.AND
        ),
        long_exit_conditions=ExitConditions(
            indicator_conditions=[],
            take_profit_pct=10.0,  # 10% 止盈
            stop_loss_pct=5.0
        )
    )
    
    kline_data = create_test_kline_data()
    engine = BacktestEngine(strategy_config, kline_data)
    
    # 创建一个做多持仓（开仓价 50000，持仓数量 0.2 BTC）
    position = Position(
        entry_time=datetime(2024, 1, 1),
        entry_price=50000.0,
        position_size=0.2,
        position_value=10000.0,
        direction="long",
        entry_capital=10000.0
    )
    
    # 测试价格上涨 10% 触发止盈（当前价 55000）
    row = pd.Series({
        'timestamp': datetime(2024, 1, 5),
        'close': 55000.0,
        'RSI14': 50
    })
    
    should_exit, reason = engine._check_long_exit_signal(row, position)
    assert should_exit is True
    assert reason == "take_profit_percentage"


def test_check_long_exit_signal_with_stop_loss_pct():
    """测试做多平仓信号 - 止损百分比触发"""
    strategy_config = StrategyConfig(
        name="Test Long Exit",
        description="Test",
        timeframe="1d",
        position_size_type="amount",
        position_size_value=10000.0,
        initial_capital=100000.0,
        long_entry_conditions=EntryConditions(
            conditions=[IndicatorCondition("RSI14", ComparisonOperator.LT, 30)],
            logic_operator=LogicOperator.AND
        ),
        long_exit_conditions=ExitConditions(
            indicator_conditions=[],
            take_profit_pct=10.0,
            stop_loss_pct=5.0  # 5% 止损
        )
    )
    
    kline_data = create_test_kline_data()
    engine = BacktestEngine(strategy_config, kline_data)
    
    position = Position(
        entry_time=datetime(2024, 1, 1),
        entry_price=50000.0,
        position_size=0.2,
        position_value=10000.0,
        direction="long",
        entry_capital=10000.0
    )
    
    # 测试价格下跌 5% 触发止损（当前价 47500）
    row = pd.Series({
        'timestamp': datetime(2024, 1, 5),
        'close': 47500.0,
        'RSI14': 50
    })
    
    should_exit, reason = engine._check_long_exit_signal(row, position)
    assert should_exit is True
    assert reason == "stop_loss_percentage"


def test_check_short_exit_signal_with_take_profit_pct():
    """测试做空平仓信号 - 止盈百分比触发"""
    strategy_config = StrategyConfig(
        name="Test Short Exit",
        description="Test",
        timeframe="1d",
        position_size_type="amount",
        position_size_value=10000.0,
        initial_capital=100000.0,
        short_entry_conditions=EntryConditions(
            conditions=[IndicatorCondition("RSI14", ComparisonOperator.GT, 70)],
            logic_operator=LogicOperator.AND
        ),
        short_exit_conditions=ExitConditions(
            indicator_conditions=[],
            take_profit_pct=10.0,  # 10% 止盈
            stop_loss_pct=5.0
        )
    )
    
    kline_data = create_test_kline_data()
    engine = BacktestEngine(strategy_config, kline_data)
    
    # 创建一个做空持仓（开仓价 50000，持仓数量 0.2 BTC）
    position = Position(
        entry_time=datetime(2024, 1, 1),
        entry_price=50000.0,
        position_size=0.2,
        position_value=10000.0,
        direction="short",
        entry_capital=10000.0
    )
    
    # 测试价格下跌 10% 触发止盈（当前价 45000）
    # 做空盈利 = (50000 - 45000) * 0.2 = 1000
    # 盈利百分比 = 1000 / 10000 * 100 = 10%
    row = pd.Series({
        'timestamp': datetime(2024, 1, 5),
        'close': 45000.0,
        'RSI14': 50
    })
    
    should_exit, reason = engine._check_short_exit_signal(row, position)
    assert should_exit is True
    assert reason == "take_profit_percentage"


def test_check_short_exit_signal_with_stop_loss_pct():
    """测试做空平仓信号 - 止损百分比触发"""
    strategy_config = StrategyConfig(
        name="Test Short Exit",
        description="Test",
        timeframe="1d",
        position_size_type="amount",
        position_size_value=10000.0,
        initial_capital=100000.0,
        short_entry_conditions=EntryConditions(
            conditions=[IndicatorCondition("RSI14", ComparisonOperator.GT, 70)],
            logic_operator=LogicOperator.AND
        ),
        short_exit_conditions=ExitConditions(
            indicator_conditions=[],
            take_profit_pct=10.0,
            stop_loss_pct=5.0  # 5% 止损
        )
    )
    
    kline_data = create_test_kline_data()
    engine = BacktestEngine(strategy_config, kline_data)
    
    position = Position(
        entry_time=datetime(2024, 1, 1),
        entry_price=50000.0,
        position_size=0.2,
        position_value=10000.0,
        direction="short",
        entry_capital=10000.0
    )
    
    # 测试价格上涨 5% 触发止损（当前价 52500）
    # 做空亏损 = (50000 - 52500) * 0.2 = -500
    # 亏损百分比 = -500 / 10000 * 100 = -5%
    row = pd.Series({
        'timestamp': datetime(2024, 1, 5),
        'close': 52500.0,
        'RSI14': 50
    })
    
    should_exit, reason = engine._check_short_exit_signal(row, position)
    assert should_exit is True
    assert reason == "stop_loss_percentage"


def test_check_long_exit_signal_with_indicator_condition():
    """测试做多平仓信号 - 指标条件触发"""
    strategy_config = StrategyConfig(
        name="Test Long Exit",
        description="Test",
        timeframe="1d",
        position_size_type="amount",
        position_size_value=10000.0,
        initial_capital=100000.0,
        long_entry_conditions=EntryConditions(
            conditions=[IndicatorCondition("RSI14", ComparisonOperator.LT, 30)],
            logic_operator=LogicOperator.AND
        ),
        long_exit_conditions=ExitConditions(
            indicator_conditions=[
                IndicatorCondition("RSI14", ComparisonOperator.GT, 70)
            ],
            logic_operator=LogicOperator.OR
        )
    )
    
    kline_data = create_test_kline_data()
    engine = BacktestEngine(strategy_config, kline_data)
    
    position = Position(
        entry_time=datetime(2024, 1, 1),
        entry_price=50000.0,
        position_size=0.2,
        position_value=10000.0,
        direction="long",
        entry_capital=10000.0
    )
    
    # 测试 RSI > 70 触发平仓
    row = pd.Series({
        'timestamp': datetime(2024, 1, 5),
        'close': 52000.0,
        'RSI14': 75
    })
    
    should_exit, reason = engine._check_long_exit_signal(row, position)
    assert should_exit is True
    assert "indicator_RSI14" in reason


def test_check_short_exit_signal_with_indicator_condition():
    """测试做空平仓信号 - 指标条件触发"""
    strategy_config = StrategyConfig(
        name="Test Short Exit",
        description="Test",
        timeframe="1d",
        position_size_type="amount",
        position_size_value=10000.0,
        initial_capital=100000.0,
        short_entry_conditions=EntryConditions(
            conditions=[IndicatorCondition("RSI14", ComparisonOperator.GT, 70)],
            logic_operator=LogicOperator.AND
        ),
        short_exit_conditions=ExitConditions(
            indicator_conditions=[
                IndicatorCondition("RSI14", ComparisonOperator.LT, 30)
            ],
            logic_operator=LogicOperator.OR
        )
    )
    
    kline_data = create_test_kline_data()
    engine = BacktestEngine(strategy_config, kline_data)
    
    position = Position(
        entry_time=datetime(2024, 1, 1),
        entry_price=50000.0,
        position_size=0.2,
        position_value=10000.0,
        direction="short",
        entry_capital=10000.0
    )
    
    # 测试 RSI < 30 触发平仓
    row = pd.Series({
        'timestamp': datetime(2024, 1, 5),
        'close': 48000.0,
        'RSI14': 25
    })
    
    should_exit, reason = engine._check_short_exit_signal(row, position)
    assert should_exit is True
    assert "indicator_RSI14" in reason


def test_check_exit_signal_routes_to_long():
    """测试 _check_exit_signal 正确路由到做多平仓检测"""
    strategy_config = StrategyConfig(
        name="Test Exit Routing",
        description="Test",
        timeframe="1d",
        position_size_type="amount",
        position_size_value=10000.0,
        initial_capital=100000.0,
        long_entry_conditions=EntryConditions(
            conditions=[IndicatorCondition("RSI14", ComparisonOperator.LT, 30)],
            logic_operator=LogicOperator.AND
        ),
        long_exit_conditions=ExitConditions(
            indicator_conditions=[],
            take_profit_pct=10.0
        )
    )
    
    kline_data = create_test_kline_data()
    engine = BacktestEngine(strategy_config, kline_data)
    
    position = Position(
        entry_time=datetime(2024, 1, 1),
        entry_price=50000.0,
        position_size=0.2,
        position_value=10000.0,
        direction="long",
        entry_capital=10000.0
    )
    
    row = pd.Series({
        'timestamp': datetime(2024, 1, 5),
        'close': 55000.0,
        'RSI14': 50
    })
    
    should_exit, reason = engine._check_exit_signal(row, position)
    assert should_exit is True
    assert reason == "take_profit_percentage"


def test_check_exit_signal_routes_to_short():
    """测试 _check_exit_signal 正确路由到做空平仓检测"""
    strategy_config = StrategyConfig(
        name="Test Exit Routing",
        description="Test",
        timeframe="1d",
        position_size_type="amount",
        position_size_value=10000.0,
        initial_capital=100000.0,
        short_entry_conditions=EntryConditions(
            conditions=[IndicatorCondition("RSI14", ComparisonOperator.GT, 70)],
            logic_operator=LogicOperator.AND
        ),
        short_exit_conditions=ExitConditions(
            indicator_conditions=[],
            take_profit_pct=10.0
        )
    )
    
    kline_data = create_test_kline_data()
    engine = BacktestEngine(strategy_config, kline_data)
    
    position = Position(
        entry_time=datetime(2024, 1, 1),
        entry_price=50000.0,
        position_size=0.2,
        position_value=10000.0,
        direction="short",
        entry_capital=10000.0
    )
    
    row = pd.Series({
        'timestamp': datetime(2024, 1, 5),
        'close': 45000.0,
        'RSI14': 50
    })
    
    should_exit, reason = engine._check_exit_signal(row, position)
    assert should_exit is True
    assert reason == "take_profit_percentage"


def test_no_exit_conditions_configured():
    """测试未配置平仓条件时返回 False"""
    strategy_config = StrategyConfig(
        name="Test No Exit",
        description="Test",
        timeframe="1d",
        position_size_type="amount",
        position_size_value=10000.0,
        initial_capital=100000.0,
        long_entry_conditions=EntryConditions(
            conditions=[IndicatorCondition("RSI14", ComparisonOperator.LT, 30)],
            logic_operator=LogicOperator.AND
        )
        # 没有配置 long_exit_conditions
    )
    
    kline_data = create_test_kline_data()
    engine = BacktestEngine(strategy_config, kline_data)
    
    position = Position(
        entry_time=datetime(2024, 1, 1),
        entry_price=50000.0,
        position_size=0.2,
        position_value=10000.0,
        direction="long",
        entry_capital=10000.0
    )
    
    row = pd.Series({
        'timestamp': datetime(2024, 1, 5),
        'close': 55000.0,
        'RSI14': 50
    })
    
    should_exit, reason = engine._check_exit_signal(row, position)
    assert should_exit is False
    assert reason == ""
