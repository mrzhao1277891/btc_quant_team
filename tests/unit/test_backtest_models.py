"""
单元测试：核心数据模型

测试回测系统的数据模型序列化/反序列化功能
"""

import pytest
from datetime import datetime, timedelta
from backend.backtest.models import (
    StrategyConfig, EntryConditions, ExitConditions,
    IndicatorCondition, ComparisonOperator, LogicOperator,
    Position, TradeRecord, PerformanceMetrics, BacktestResult
)


class TestIndicatorCondition:
    """测试IndicatorCondition数据模型"""
    
    def test_to_dict_and_from_dict(self):
        """测试序列化和反序列化"""
        condition = IndicatorCondition(
            indicator="EMA7",
            operator=ComparisonOperator.GT,
            value=50000.0,
            timeframe="1d"
        )
        
        # 序列化
        data = condition.to_dict()
        assert data["indicator"] == "EMA7"
        assert data["operator"] == ">"
        assert data["value"] == 50000.0
        assert data["timeframe"] == "1d"
        
        # 反序列化
        loaded = IndicatorCondition.from_dict(data)
        assert loaded.indicator == condition.indicator
        assert loaded.operator == condition.operator
        assert loaded.value == condition.value
        assert loaded.timeframe == condition.timeframe
    
    def test_range_value(self):
        """测试范围值"""
        condition = IndicatorCondition(
            indicator="RSI14",
            operator=ComparisonOperator.RANGE,
            value=(30, 70),
            timeframe="1d"
        )
        
        data = condition.to_dict()
        assert data["value"] == (30, 70)
        
        loaded = IndicatorCondition.from_dict(data)
        assert loaded.value == (30, 70)


class TestEntryConditions:
    """测试EntryConditions数据模型"""
    
    def test_to_dict_and_from_dict(self):
        """测试序列化和反序列化"""
        conditions = EntryConditions(
            conditions=[
                IndicatorCondition("EMA7", ComparisonOperator.GT, 50000.0),
                IndicatorCondition("RSI14", ComparisonOperator.LT, 70)
            ],
            logic_operator=LogicOperator.AND
        )
        
        data = conditions.to_dict()
        assert len(data["conditions"]) == 2
        assert data["logic_operator"] == "AND"
        
        loaded = EntryConditions.from_dict(data)
        assert len(loaded.conditions) == 2
        assert loaded.logic_operator == LogicOperator.AND


class TestExitConditions:
    """测试ExitConditions数据模型"""
    
    def test_to_dict_and_from_dict(self):
        """测试序列化和反序列化"""
        conditions = ExitConditions(
            indicator_conditions=[
                IndicatorCondition("RSI14", ComparisonOperator.GT, 80)
            ],
            take_profit_amount=5000.0,
            stop_loss_amount=2000.0,
            take_profit_pct=0.10,
            stop_loss_pct=0.05,
            logic_operator=LogicOperator.OR
        )
        
        data = conditions.to_dict()
        assert len(data["indicator_conditions"]) == 1
        assert data["take_profit_amount"] == 5000.0
        assert data["stop_loss_amount"] == 2000.0
        assert data["take_profit_pct"] == 0.10
        assert data["stop_loss_pct"] == 0.05
        assert data["logic_operator"] == "OR"
        
        loaded = ExitConditions.from_dict(data)
        assert len(loaded.indicator_conditions) == 1
        assert loaded.take_profit_amount == 5000.0
        assert loaded.stop_loss_amount == 2000.0


class TestStrategyConfig:
    """测试StrategyConfig数据模型"""
    
    def test_to_dict_and_from_dict(self):
        """测试序列化和反序列化"""
        strategy = StrategyConfig(
            name="Test Strategy",
            description="A test strategy",
            timeframe="1d",
            position_direction="long",
            position_size_type="percentage",
            position_size_value=0.5,
            entry_conditions=EntryConditions(
                conditions=[
                    IndicatorCondition("EMA7", ComparisonOperator.GT, 50000.0)
                ],
                logic_operator=LogicOperator.AND
            ),
            exit_conditions=ExitConditions(
                indicator_conditions=[],
                take_profit_pct=0.10,
                stop_loss_pct=0.05
            ),
            initial_capital=100000.0,
            allow_multiple_positions=False
        )
        
        data = strategy.to_dict()
        assert data["name"] == "Test Strategy"
        assert data["timeframe"] == "1d"
        assert data["position_direction"] == "long"
        assert data["initial_capital"] == 100000.0
        
        loaded = StrategyConfig.from_dict(data)
        assert loaded.name == strategy.name
        assert loaded.timeframe == strategy.timeframe
        assert loaded.initial_capital == strategy.initial_capital
    
    def test_to_json_and_from_json(self):
        """测试JSON序列化和反序列化"""
        strategy = StrategyConfig(
            name="JSON Test",
            description="Test JSON serialization",
            timeframe="1d",
            position_direction="long",
            position_size_type="amount",
            position_size_value=50000.0,
            entry_conditions=EntryConditions(
                conditions=[
                    IndicatorCondition("EMA7", ComparisonOperator.GT, 50000.0)
                ]
            ),
            exit_conditions=ExitConditions(
                indicator_conditions=[],
                take_profit_pct=0.10
            )
        )
        
        json_str = strategy.to_json()
        assert isinstance(json_str, str)
        assert "JSON Test" in json_str
        
        loaded = StrategyConfig.from_json(json_str)
        assert loaded.name == strategy.name
        assert loaded.description == strategy.description


class TestPosition:
    """测试Position数据模型"""
    
    def test_to_dict_and_from_dict(self):
        """测试序列化和反序列化"""
        now = datetime.now()
        position = Position(
            entry_time=now,
            entry_price=50000.0,
            position_size=1.0,
            position_value=50000.0,
            direction="long",
            entry_capital=50000.0
        )
        
        data = position.to_dict()
        assert data["entry_price"] == 50000.0
        assert data["position_size"] == 1.0
        assert data["direction"] == "long"
        
        loaded = Position.from_dict(data)
        assert loaded.entry_price == position.entry_price
        assert loaded.position_size == position.position_size
        assert loaded.direction == position.direction


class TestTradeRecord:
    """测试TradeRecord数据模型"""
    
    def test_to_dict_and_from_dict(self):
        """测试序列化和反序列化"""
        entry_time = datetime.now()
        exit_time = entry_time + timedelta(days=5)
        
        trade = TradeRecord(
            trade_id=1,
            entry_time=entry_time,
            entry_price=50000.0,
            exit_time=exit_time,
            exit_price=55000.0,
            position_size=1.0,
            direction="long",
            profit_loss=5000.0,
            profit_loss_pct=0.10,
            holding_period=timedelta(days=5),
            exit_reason="take_profit_pct",
            entry_capital=50000.0
        )
        
        data = trade.to_dict()
        assert data["trade_id"] == 1
        assert data["entry_price"] == 50000.0
        assert data["exit_price"] == 55000.0
        assert data["profit_loss"] == 5000.0
        assert data["exit_reason"] == "take_profit_pct"
        
        loaded = TradeRecord.from_dict(data)
        assert loaded.trade_id == trade.trade_id
        assert loaded.profit_loss == trade.profit_loss
        assert loaded.exit_reason == trade.exit_reason


class TestPerformanceMetrics:
    """测试PerformanceMetrics数据模型"""
    
    def test_to_dict_and_from_dict(self):
        """测试序列化和反序列化"""
        metrics = PerformanceMetrics(
            initial_capital=100000.0,
            final_capital=120000.0,
            total_return=20000.0,
            total_return_pct=0.20,
            total_trades=10,
            winning_trades=7,
            losing_trades=3,
            win_rate=0.70,
            avg_profit=3000.0,
            avg_loss=1000.0,
            profit_factor=2.1,
            max_drawdown=5000.0,
            max_drawdown_pct=0.05,
            sharpe_ratio=1.5,
            longest_win_streak=4,
            longest_loss_streak=2,
            total_fees=0.0
        )
        
        data = metrics.to_dict()
        assert data["initial_capital"] == 100000.0
        assert data["final_capital"] == 120000.0
        assert data["win_rate"] == 0.70
        assert data["sharpe_ratio"] == 1.5
        
        loaded = PerformanceMetrics.from_dict(data)
        assert loaded.initial_capital == metrics.initial_capital
        assert loaded.win_rate == metrics.win_rate
        assert loaded.sharpe_ratio == metrics.sharpe_ratio


class TestBacktestResult:
    """测试BacktestResult数据模型"""
    
    def test_to_dict_and_from_dict(self):
        """测试序列化和反序列化"""
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)
        
        strategy = StrategyConfig(
            name="Test",
            description="Test",
            timeframe="1d",
            position_direction="long",
            position_size_type="amount",
            position_size_value=50000.0,
            entry_conditions=EntryConditions(
                conditions=[
                    IndicatorCondition("EMA7", ComparisonOperator.GT, 50000.0)
                ]
            ),
            exit_conditions=ExitConditions(
                indicator_conditions=[],
                take_profit_pct=0.10
            )
        )
        
        metrics = PerformanceMetrics(
            initial_capital=100000.0,
            final_capital=120000.0,
            total_return=20000.0,
            total_return_pct=0.20,
            total_trades=5,
            winning_trades=3,
            losing_trades=2,
            win_rate=0.60,
            avg_profit=8000.0,
            avg_loss=2000.0,
            profit_factor=2.0,
            max_drawdown=3000.0,
            max_drawdown_pct=0.03,
            sharpe_ratio=1.2,
            longest_win_streak=2,
            longest_loss_streak=1
        )
        
        result = BacktestResult(
            backtest_id="test-123",
            strategy_config=strategy,
            start_date=start_date,
            end_date=end_date,
            trades=[],
            metrics=metrics,
            equity_curve=[(start_date, 100000.0), (end_date, 120000.0)],
            data_quality_warnings=["Warning 1"],
            execution_time=5.5
        )
        
        data = result.to_dict()
        assert data["backtest_id"] == "test-123"
        assert data["execution_time"] == 5.5
        assert len(data["data_quality_warnings"]) == 1
        
        loaded = BacktestResult.from_dict(data)
        assert loaded.backtest_id == result.backtest_id
        assert loaded.execution_time == result.execution_time
    
    def test_to_json_and_from_json(self):
        """测试JSON序列化和反序列化"""
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)
        
        strategy = StrategyConfig(
            name="JSON Test",
            description="Test",
            timeframe="1d",
            position_direction="long",
            position_size_type="amount",
            position_size_value=50000.0,
            entry_conditions=EntryConditions(
                conditions=[
                    IndicatorCondition("EMA7", ComparisonOperator.GT, 50000.0)
                ]
            ),
            exit_conditions=ExitConditions(
                indicator_conditions=[],
                take_profit_pct=0.10
            )
        )
        
        metrics = PerformanceMetrics(
            initial_capital=100000.0,
            final_capital=120000.0,
            total_return=20000.0,
            total_return_pct=0.20,
            total_trades=5,
            winning_trades=3,
            losing_trades=2,
            win_rate=0.60,
            avg_profit=8000.0,
            avg_loss=2000.0,
            profit_factor=2.0,
            max_drawdown=3000.0,
            max_drawdown_pct=0.03,
            sharpe_ratio=1.2,
            longest_win_streak=2,
            longest_loss_streak=1
        )
        
        result = BacktestResult(
            backtest_id="json-test",
            strategy_config=strategy,
            start_date=start_date,
            end_date=end_date,
            trades=[],
            metrics=metrics,
            equity_curve=[(start_date, 100000.0)],
            data_quality_warnings=[],
            execution_time=3.0
        )
        
        json_str = result.to_json()
        assert isinstance(json_str, str)
        assert "json-test" in json_str
        
        loaded = BacktestResult.from_json(json_str)
        assert loaded.backtest_id == result.backtest_id
        assert loaded.execution_time == result.execution_time
