#!/usr/bin/env python3
"""
核心数据模型单元测试
测试StrategyConfig、Position、TradeRecord等数据模型的验证逻辑和序列化/反序列化
"""

import pytest
from datetime import datetime, timedelta
from backend.backtest.models import (
    IndicatorCondition,
    ComparisonOperator,
    EntryConditions,
    ExitConditions,
    LogicOperator,
    StrategyConfig,
    Position,
    TradeRecord,
    PerformanceMetrics,
    BacktestResult
)


class TestIndicatorCondition:
    """测试IndicatorCondition数据模型"""
    
    def test_to_dict(self):
        """测试序列化为字典"""
        condition = IndicatorCondition(
            indicator="ema7",
            operator=ComparisonOperator.GT,
            value=100.0
        )
        
        result = condition.to_dict()
        
        assert result["indicator"] == "ema7"
        assert result["operator"] == ">"
        assert result["value"] == 100.0
    
    def test_from_dict(self):
        """测试从字典反序列化"""
        data = {
            "indicator": "rsi14",
            "operator": "<",
            "value": 30
        }
        
        condition = IndicatorCondition.from_dict(data)
        
        assert condition.indicator == "rsi14"
        assert condition.operator == ComparisonOperator.LT
        assert condition.value == 30
    
    def test_round_trip_serialization(self):
        """测试序列化和反序列化的往返一致性"""
        original = IndicatorCondition(
            indicator="macd",
            operator=ComparisonOperator.GTE,
            value=0
        )
        
        # 序列化再反序列化
        data = original.to_dict()
        restored = IndicatorCondition.from_dict(data)
        
        assert restored.indicator == original.indicator
        assert restored.operator == original.operator
        assert restored.value == original.value


class TestStrategyConfig:
    """测试StrategyConfig数据模型"""
    
    def test_valid_strategy_config(self):
        """测试有效的策略配置"""
        entry_conditions = EntryConditions(
            conditions=[
                IndicatorCondition("ema7", ComparisonOperator.GT, "ema25"),
                IndicatorCondition("rsi14", ComparisonOperator.LT, 70)
            ],
            logic_operator=LogicOperator.AND
        )
        
        exit_conditions = ExitConditions(
            indicator_conditions=[
                IndicatorCondition("ema7", ComparisonOperator.LT, "ema25")
            ],
            take_profit_pct=0.10,
            stop_loss_pct=0.05,
            logic_operator=LogicOperator.OR
        )
        
        config = StrategyConfig(
            name="Test Strategy",
            description="A test strategy",
            timeframe="1d",
            position_direction="long",
            position_size_type="percentage",
            position_size_value=10.0,
            entry_conditions=entry_conditions,
            exit_conditions=exit_conditions,
            initial_capital=10000.0
        )
        
        assert config.name == "Test Strategy"
        assert config.timeframe == "1d"
        assert config.initial_capital == 10000.0
    
    def test_strategy_config_serialization(self):
        """测试策略配置的序列化"""
        entry_conditions = EntryConditions(
            conditions=[
                IndicatorCondition("close", ComparisonOperator.GT, "boll_up")
            ],
            logic_operator=LogicOperator.AND
        )
        
        exit_conditions = ExitConditions(
            indicator_conditions=[],
            take_profit_pct=0.08,
            stop_loss_pct=0.04,
            logic_operator=LogicOperator.OR
        )
        
        config = StrategyConfig(
            name="Bollinger Breakout",
            description="Price breaks above upper band",
            timeframe="4h",
            position_direction="long",
            position_size_type="amount",
            position_size_value=1000.0,
            entry_conditions=entry_conditions,
            exit_conditions=exit_conditions
        )
        
        # 序列化
        data = config.to_dict()
        
        assert data["name"] == "Bollinger Breakout"
        assert data["timeframe"] == "4h"
        assert data["position_size_value"] == 1000.0
        assert "entry_conditions" in data
        assert "exit_conditions" in data
    
    def test_strategy_config_deserialization(self):
        """测试策略配置的反序列化"""
        data = {
            "name": "RSI Oversold",
            "description": "Buy when RSI < 30",
            "timeframe": "1d",
            "position_direction": "long",
            "position_size_type": "percentage",
            "position_size_value": 15.0,
            "entry_conditions": {
                "conditions": [
                    {"indicator": "rsi14", "operator": "<", "value": 30}
                ],
                "logic_operator": "AND"
            },
            "exit_conditions": {
                "indicator_conditions": [
                    {"indicator": "rsi14", "operator": ">", "value": 70}
                ],
                "take_profit_pct": 0.12,
                "stop_loss_pct": 0.06,
                "logic_operator": "OR"
            },
            "initial_capital": 10000.0
        }
        
        config = StrategyConfig.from_dict(data)
        
        assert config.name == "RSI Oversold"
        assert config.timeframe == "1d"
        assert config.position_size_value == 15.0
        assert len(config.entry_conditions.conditions) == 1
        assert config.exit_conditions.take_profit_pct == 0.12
    
    def test_strategy_config_round_trip(self):
        """测试策略配置的往返序列化"""
        original = StrategyConfig(
            name="Test",
            description="Test strategy",
            timeframe="1h",
            position_direction="short",
            position_size_type="amount",
            position_size_value=500.0,
            entry_conditions=EntryConditions(
                conditions=[IndicatorCondition("rsi14", ComparisonOperator.GT, 70)],
                logic_operator=LogicOperator.AND
            ),
            exit_conditions=ExitConditions(
                indicator_conditions=[],
                take_profit_pct=0.05,
                stop_loss_pct=0.03,
                logic_operator=LogicOperator.OR
            )
        )
        
        # 序列化再反序列化
        data = original.to_dict()
        restored = StrategyConfig.from_dict(data)
        
        assert restored.name == original.name
        assert restored.timeframe == original.timeframe
        assert restored.position_direction == original.position_direction
        assert restored.position_size_value == original.position_size_value
    
    def test_missing_required_fields(self):
        """测试缺失必填字段的情况"""
        with pytest.raises((TypeError, KeyError)):
            # 缺少name字段
            StrategyConfig.from_dict({
                "description": "Test",
                "timeframe": "1d"
            })
    
    def test_invalid_position_direction(self):
        """测试无效的持仓方向"""
        # 注意：由于使用了Literal类型提示，这个测试可能在运行时不会抛出错误
        # 但在类型检查时会被捕获
        data = {
            "name": "Test",
            "description": "Test",
            "timeframe": "1d",
            "position_direction": "invalid",  # 应该是 "long" 或 "short"
            "position_size_type": "amount",
            "position_size_value": 100.0,
            "entry_conditions": {
                "conditions": [],
                "logic_operator": "AND"
            },
            "exit_conditions": {
                "indicator_conditions": [],
                "logic_operator": "OR"
            }
        }
        
        # 在运行时可能不会抛出错误，但这是一个无效配置
        config = StrategyConfig.from_dict(data)
        assert config.position_direction == "invalid"  # 会被创建，但是无效


class TestPosition:
    """测试Position数据模型"""
    
    def test_position_creation(self):
        """测试持仓对象创建"""
        entry_time = datetime(2024, 1, 1, 10, 0, 0)
        position = Position(
            entry_time=entry_time,
            entry_price=50000.0,
            position_size=0.1,
            position_value=5000.0,
            direction="long",
            entry_capital=5000.0
        )
        
        assert position.entry_time == entry_time
        assert position.entry_price == 50000.0
        assert position.position_size == 0.1
        assert position.direction == "long"
    
    def test_position_serialization(self):
        """测试持仓对象序列化"""
        position = Position(
            entry_time=datetime(2024, 1, 1, 10, 0, 0),
            entry_price=50000.0,
            position_size=0.1,
            position_value=5000.0,
            direction="long",
            entry_capital=5000.0
        )
        
        data = position.to_dict()
        
        assert "entry_time" in data
        assert data["entry_price"] == 50000.0
        assert data["position_size"] == 0.1
        assert data["direction"] == "long"


class TestTradeRecord:
    """测试TradeRecord数据模型"""
    
    def test_trade_record_creation(self):
        """测试交易记录创建"""
        entry_time = datetime(2024, 1, 1, 10, 0, 0)
        exit_time = datetime(2024, 1, 2, 10, 0, 0)
        holding_period = exit_time - entry_time
        
        trade = TradeRecord(
            trade_id=1,
            entry_time=entry_time,
            entry_price=50000.0,
            exit_time=exit_time,
            exit_price=51000.0,
            position_size=0.1,
            direction="long",
            profit_loss=100.0,
            profit_loss_pct=0.02,
            holding_period=holding_period,
            exit_reason="take_profit",
            entry_capital=5000.0
        )
        
        assert trade.trade_id == 1
        assert trade.profit_loss == 100.0
        assert trade.profit_loss_pct == 0.02
        assert trade.exit_reason == "take_profit"
    
    def test_trade_record_serialization(self):
        """测试交易记录序列化"""
        entry_time = datetime(2024, 1, 1, 10, 0, 0)
        exit_time = datetime(2024, 1, 2, 10, 0, 0)
        
        trade = TradeRecord(
            trade_id=1,
            entry_time=entry_time,
            entry_price=50000.0,
            exit_time=exit_time,
            exit_price=49000.0,
            position_size=0.1,
            direction="long",
            profit_loss=-100.0,
            profit_loss_pct=-0.02,
            holding_period=timedelta(days=1),
            exit_reason="stop_loss",
            entry_capital=5000.0
        )
        
        data = trade.to_dict()
        
        assert data["trade_id"] == 1
        assert data["profit_loss"] == -100.0
        assert data["exit_reason"] == "stop_loss"
        assert "entry_time" in data
        assert "exit_time" in data
    
    def test_trade_record_round_trip(self):
        """测试交易记录往返序列化"""
        original = TradeRecord(
            trade_id=5,
            entry_time=datetime(2024, 1, 1, 10, 0, 0),
            entry_price=50000.0,
            exit_time=datetime(2024, 1, 2, 10, 0, 0),
            exit_price=51500.0,
            position_size=0.2,
            direction="long",
            profit_loss=300.0,
            profit_loss_pct=0.03,
            holding_period=timedelta(days=1),
            exit_reason="indicator_exit",
            entry_capital=10000.0
        )
        
        # 序列化再反序列化
        data = original.to_dict()
        restored = TradeRecord.from_dict(data)
        
        assert restored.trade_id == original.trade_id
        assert restored.profit_loss == original.profit_loss
        assert restored.exit_reason == original.exit_reason


class TestPerformanceMetrics:
    """测试PerformanceMetrics数据模型"""
    
    def test_performance_metrics_creation(self):
        """测试性能指标创建"""
        metrics = PerformanceMetrics(
            initial_capital=10000.0,
            final_capital=11000.0,
            total_return=1000.0,
            total_return_pct=0.10,
            total_trades=50,
            winning_trades=30,
            losing_trades=20,
            win_rate=0.60,
            avg_profit=50.0,
            avg_loss=-30.0,
            profit_factor=1.67,
            max_drawdown=500.0,
            max_drawdown_pct=0.05,
            sharpe_ratio=1.5,
            longest_win_streak=5,
            longest_loss_streak=3
        )
        
        assert metrics.initial_capital == 10000.0
        assert metrics.final_capital == 11000.0
        assert metrics.win_rate == 0.60
        assert metrics.sharpe_ratio == 1.5
    
    def test_performance_metrics_serialization(self):
        """测试性能指标序列化"""
        metrics = PerformanceMetrics(
            initial_capital=10000.0,
            final_capital=9500.0,
            total_return=-500.0,
            total_return_pct=-0.05,
            total_trades=20,
            winning_trades=8,
            losing_trades=12,
            win_rate=0.40,
            avg_profit=100.0,
            avg_loss=-75.0,
            profit_factor=0.89,
            max_drawdown=800.0,
            max_drawdown_pct=0.08,
            sharpe_ratio=-0.5,
            longest_win_streak=3,
            longest_loss_streak=5
        )
        
        data = metrics.to_dict()
        
        assert data["initial_capital"] == 10000.0
        assert data["final_capital"] == 9500.0
        assert data["win_rate"] == 0.40
        assert data["total_trades"] == 20
    
    def test_performance_metrics_round_trip(self):
        """测试性能指标往返序列化"""
        original = PerformanceMetrics(
            initial_capital=10000.0,
            final_capital=12000.0,
            total_return=2000.0,
            total_return_pct=0.20,
            total_trades=100,
            winning_trades=65,
            losing_trades=35,
            win_rate=0.65,
            avg_profit=60.0,
            avg_loss=-40.0,
            profit_factor=1.95,
            max_drawdown=300.0,
            max_drawdown_pct=0.03,
            sharpe_ratio=2.1,
            longest_win_streak=8,
            longest_loss_streak=4
        )
        
        # 序列化再反序列化
        data = original.to_dict()
        restored = PerformanceMetrics.from_dict(data)
        
        assert restored.initial_capital == original.initial_capital
        assert restored.final_capital == original.final_capital
        assert restored.win_rate == original.win_rate
        assert restored.sharpe_ratio == original.sharpe_ratio


class TestBacktestResult:
    """测试BacktestResult数据模型"""
    
    def test_backtest_result_creation(self):
        """测试回测结果创建"""
        strategy = StrategyConfig(
            name="Test",
            description="Test",
            timeframe="1d",
            position_direction="long",
            position_size_type="amount",
            position_size_value=1000.0,
            entry_conditions=EntryConditions(conditions=[], logic_operator=LogicOperator.AND),
            exit_conditions=ExitConditions(indicator_conditions=[], logic_operator=LogicOperator.OR)
        )
        
        metrics = PerformanceMetrics(
            initial_capital=10000.0,
            final_capital=11000.0,
            total_return=1000.0,
            total_return_pct=0.10,
            total_trades=10,
            winning_trades=6,
            losing_trades=4,
            win_rate=0.60,
            avg_profit=200.0,
            avg_loss=-100.0,
            profit_factor=1.2,
            max_drawdown=200.0,
            max_drawdown_pct=0.02,
            sharpe_ratio=1.0,
            longest_win_streak=3,
            longest_loss_streak=2
        )
        
        result = BacktestResult(
            backtest_id="test_123",
            strategy_config=strategy,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
            trades=[],
            metrics=metrics,
            equity_curve=[],
            data_quality_warnings=[],
            execution_time=1.5
        )
        
        assert result.backtest_id == "test_123"
        assert result.metrics.win_rate == 0.60
        assert result.execution_time == 1.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
