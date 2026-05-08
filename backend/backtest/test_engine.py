"""
回测引擎单元测试

测试BacktestEngine类的核心功能：
- 条件评估（开仓和平仓）
- 持仓管理（开仓、平仓、盈亏计算）
"""

import pytest
import pandas as pd
import numpy as np
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


class TestBacktestEngine:
    """测试BacktestEngine类"""
    
    def create_sample_kline_data(self, num_rows=100):
        """创建示例K线数据"""
        dates = pd.date_range(start='2024-01-01', periods=num_rows, freq='D')
        
        # 生成模拟价格数据（上涨趋势）
        base_price = 50000
        prices = base_price + np.cumsum(np.random.randn(num_rows) * 100)
        
        df = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': prices * 1.01,
            'low': prices * 0.99,
            'close': prices,
            'volume': np.random.uniform(100, 1000, num_rows),
            'EMA7': prices * 0.98,
            'EMA25': prices * 0.97,
            'RSI14': np.random.uniform(30, 70, num_rows),
        })
        
        return df
    
    def create_simple_strategy(self):
        """创建简单的测试策略"""
        entry_conditions = EntryConditions(
            conditions=[
                IndicatorCondition(
                    indicator="RSI14",
                    operator=ComparisonOperator.LT,
                    value=40.0
                )
            ],
            logic_operator=LogicOperator.AND
        )
        
        exit_conditions = ExitConditions(
            indicator_conditions=[
                IndicatorCondition(
                    indicator="RSI14",
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
            description="Simple test strategy",
            timeframe="1d",
            position_direction="long",
            position_size_type="percentage",
            position_size_value=50.0,  # 50% of capital
            entry_conditions=entry_conditions,
            exit_conditions=exit_conditions,
            initial_capital=100000.0
        )
        
        return strategy
    
    def test_engine_initialization(self):
        """测试引擎初始化"""
        strategy = self.create_simple_strategy()
        kline_data = self.create_sample_kline_data()
        
        engine = BacktestEngine(strategy, kline_data)
        
        assert engine.strategy_config == strategy
        assert len(engine.kline_data) == 100
        assert engine.capital == 100000.0
        assert engine.current_position is None
        assert len(engine.trades) == 0
    
    def test_evaluate_condition_gt(self):
        """测试大于条件评估"""
        strategy = self.create_simple_strategy()
        kline_data = self.create_sample_kline_data()
        engine = BacktestEngine(strategy, kline_data)
        
        condition = IndicatorCondition(
            indicator="RSI14",
            operator=ComparisonOperator.GT,
            value=50.0
        )
        
        # 创建测试行
        row = pd.Series({'RSI14': 60.0})
        assert engine._evaluate_condition(condition, row) == True
        
        row = pd.Series({'RSI14': 40.0})
        assert engine._evaluate_condition(condition, row) == False
    
    def test_evaluate_condition_lt(self):
        """测试小于条件评估"""
        strategy = self.create_simple_strategy()
        kline_data = self.create_sample_kline_data()
        engine = BacktestEngine(strategy, kline_data)
        
        condition = IndicatorCondition(
            indicator="RSI14",
            operator=ComparisonOperator.LT,
            value=50.0
        )
        
        row = pd.Series({'RSI14': 40.0})
        assert engine._evaluate_condition(condition, row) == True
        
        row = pd.Series({'RSI14': 60.0})
        assert engine._evaluate_condition(condition, row) == False
    
    def test_evaluate_condition_range(self):
        """测试范围条件评估"""
        strategy = self.create_simple_strategy()
        kline_data = self.create_sample_kline_data()
        engine = BacktestEngine(strategy, kline_data)
        
        condition = IndicatorCondition(
            indicator="RSI14",
            operator=ComparisonOperator.RANGE,
            value=(40.0, 60.0)
        )
        
        row = pd.Series({'RSI14': 50.0})
        assert engine._evaluate_condition(condition, row) == True
        
        row = pd.Series({'RSI14': 70.0})
        assert engine._evaluate_condition(condition, row) == False
    
    def test_evaluate_condition_missing_indicator(self):
        """测试缺失指标的条件评估"""
        strategy = self.create_simple_strategy()
        kline_data = self.create_sample_kline_data()
        engine = BacktestEngine(strategy, kline_data)
        
        condition = IndicatorCondition(
            indicator="NonExistent",
            operator=ComparisonOperator.GT,
            value=50.0
        )
        
        row = pd.Series({'RSI14': 60.0})
        assert engine._evaluate_condition(condition, row) == False
    
    def test_evaluate_entry_conditions_and(self):
        """测试AND逻辑的开仓条件"""
        entry_conditions = EntryConditions(
            conditions=[
                IndicatorCondition("RSI14", ComparisonOperator.LT, 40.0),
                IndicatorCondition("EMA7", ComparisonOperator.GT, 50000.0)
            ],
            logic_operator=LogicOperator.AND
        )
        
        strategy = StrategyConfig(
            name="Test",
            description="Test",
            timeframe="1d",
            position_direction="long",
            position_size_type="amount",
            position_size_value=10000.0,
            entry_conditions=entry_conditions,
            exit_conditions=ExitConditions(indicator_conditions=[])
        )
        
        kline_data = self.create_sample_kline_data()
        engine = BacktestEngine(strategy, kline_data)
        
        # 两个条件都满足
        row = pd.Series({'RSI14': 35.0, 'EMA7': 51000.0})
        assert engine._evaluate_entry_conditions(row) == True
        
        # 只有一个条件满足
        row = pd.Series({'RSI14': 35.0, 'EMA7': 49000.0})
        assert engine._evaluate_entry_conditions(row) == False
    
    def test_evaluate_entry_conditions_or(self):
        """测试OR逻辑的开仓条件"""
        entry_conditions = EntryConditions(
            conditions=[
                IndicatorCondition("RSI14", ComparisonOperator.LT, 40.0),
                IndicatorCondition("EMA7", ComparisonOperator.GT, 50000.0)
            ],
            logic_operator=LogicOperator.OR
        )
        
        strategy = StrategyConfig(
            name="Test",
            description="Test",
            timeframe="1d",
            position_direction="long",
            position_size_type="amount",
            position_size_value=10000.0,
            entry_conditions=entry_conditions,
            exit_conditions=ExitConditions(indicator_conditions=[])
        )
        
        kline_data = self.create_sample_kline_data()
        engine = BacktestEngine(strategy, kline_data)
        
        # 只有一个条件满足
        row = pd.Series({'RSI14': 35.0, 'EMA7': 49000.0})
        assert engine._evaluate_entry_conditions(row) == True
        
        # 两个条件都不满足
        row = pd.Series({'RSI14': 45.0, 'EMA7': 49000.0})
        assert engine._evaluate_entry_conditions(row) == False
    
    def test_calculate_pnl_long(self):
        """测试做多盈亏计算"""
        strategy = self.create_simple_strategy()
        kline_data = self.create_sample_kline_data()
        engine = BacktestEngine(strategy, kline_data)
        
        position = Position(
            entry_time=datetime.now(),
            entry_price=50000.0,
            position_size=1.0,  # 1 BTC
            position_value=50000.0,
            direction="long",
            entry_capital=50000.0
        )
        
        # 价格上涨
        pnl_amount, pnl_pct = engine._calculate_pnl(position, 55000.0)
        assert pnl_amount == 5000.0
        assert pnl_pct == 10.0
        
        # 价格下跌
        pnl_amount, pnl_pct = engine._calculate_pnl(position, 45000.0)
        assert pnl_amount == -5000.0
        assert pnl_pct == -10.0
    
    def test_calculate_pnl_short(self):
        """测试做空盈亏计算"""
        strategy = StrategyConfig(
            name="Test",
            description="Test",
            timeframe="1d",
            position_direction="short",
            position_size_type="amount",
            position_size_value=50000.0,
            entry_conditions=EntryConditions(conditions=[]),
            exit_conditions=ExitConditions(indicator_conditions=[])
        )
        
        kline_data = self.create_sample_kline_data()
        engine = BacktestEngine(strategy, kline_data)
        
        position = Position(
            entry_time=datetime.now(),
            entry_price=50000.0,
            position_size=1.0,
            position_value=50000.0,
            direction="short",
            entry_capital=50000.0
        )
        
        # 价格下跌（做空盈利）
        pnl_amount, pnl_pct = engine._calculate_pnl(position, 45000.0)
        assert pnl_amount == 5000.0
        assert pnl_pct == 10.0
        
        # 价格上涨（做空亏损）
        pnl_amount, pnl_pct = engine._calculate_pnl(position, 55000.0)
        assert pnl_amount == -5000.0
        assert pnl_pct == -10.0
    
    def test_evaluate_exit_conditions_stop_loss_amount(self):
        """测试绝对值止损"""
        strategy = self.create_simple_strategy()
        strategy.exit_conditions.stop_loss_amount = 2000.0
        
        kline_data = self.create_sample_kline_data()
        engine = BacktestEngine(strategy, kline_data)
        
        position = Position(
            entry_time=datetime.now(),
            entry_price=50000.0,
            position_size=1.0,
            position_value=50000.0,
            direction="long",
            entry_capital=50000.0
        )
        
        # 亏损达到止损线
        row = pd.Series({'close': 48000.0, 'RSI14': 50.0})
        should_exit, reason = engine._evaluate_exit_conditions(row, position)
        assert should_exit == True
        assert reason == "stop_loss_amount"
    
    def test_evaluate_exit_conditions_take_profit_pct(self):
        """测试百分比止盈"""
        strategy = self.create_simple_strategy()
        strategy.exit_conditions.take_profit_pct = 10.0
        
        kline_data = self.create_sample_kline_data()
        engine = BacktestEngine(strategy, kline_data)
        
        position = Position(
            entry_time=datetime.now(),
            entry_price=50000.0,
            position_size=1.0,
            position_value=50000.0,
            direction="long",
            entry_capital=50000.0
        )
        
        # 盈利达到止盈线
        row = pd.Series({'close': 55000.0, 'RSI14': 50.0})
        should_exit, reason = engine._evaluate_exit_conditions(row, position)
        assert should_exit == True
        assert reason == "take_profit_percentage"
    
    def test_open_position_success(self):
        """测试成功开仓"""
        strategy = self.create_simple_strategy()
        kline_data = self.create_sample_kline_data()
        engine = BacktestEngine(strategy, kline_data)
        
        row = pd.Series({
            'timestamp': datetime.now(),
            'close': 50000.0
        })
        
        position = engine._open_position(row)
        
        assert position is not None
        assert position.entry_price == 50000.0
        assert position.direction == "long"
        assert position.entry_capital == 50000.0  # 50% of 100000
        assert position.position_size == 1.0  # 50000 / 50000
        assert engine.capital == 50000.0  # 100000 - 50000
    
    def test_open_position_insufficient_capital(self):
        """测试资金不足时开仓"""
        strategy = self.create_simple_strategy()
        strategy.position_size_value = 150.0  # 150% of capital
        
        kline_data = self.create_sample_kline_data()
        engine = BacktestEngine(strategy, kline_data)
        
        row = pd.Series({
            'timestamp': datetime.now(),
            'close': 50000.0
        })
        
        position = engine._open_position(row)
        
        assert position is None
        assert engine.capital == 100000.0  # 资金未变化
    
    def test_close_position(self):
        """测试平仓"""
        strategy = self.create_simple_strategy()
        kline_data = self.create_sample_kline_data()
        engine = BacktestEngine(strategy, kline_data)
        
        position = Position(
            entry_time=datetime(2024, 1, 1),
            entry_price=50000.0,
            position_size=1.0,
            position_value=50000.0,
            direction="long",
            entry_capital=50000.0
        )
        
        engine.capital = 50000.0  # 模拟开仓后的资金
        
        row = pd.Series({
            'timestamp': datetime(2024, 1, 10),
            'close': 55000.0
        })
        
        trade = engine._close_position(position, row, "take_profit")
        
        assert trade.trade_id == 1
        assert trade.entry_price == 50000.0
        assert trade.exit_price == 55000.0
        assert trade.profit_loss == 5000.0
        assert trade.profit_loss_pct == 10.0
        assert trade.exit_reason == "take_profit"
        assert engine.capital == 105000.0  # 50000 + 50000 + 5000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
