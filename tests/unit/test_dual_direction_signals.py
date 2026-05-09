"""
测试双向交易策略信号检测

验证 BacktestEngine 支持双向开仓信号检测的功能
"""

import pytest
import pandas as pd
from datetime import datetime
from backend.backtest.models import (
    StrategyConfig,
    EntryConditions,
    ExitConditions,
    IndicatorCondition,
    ComparisonOperator,
    LogicOperator
)
from backend.backtest.engine import BacktestEngine


class TestDualDirectionSignals:
    """测试双向交易策略信号检测"""
    
    def create_test_data(self, rsi_value: float) -> pd.DataFrame:
        """创建测试用的K线数据
        
        Args:
            rsi_value: RSI指标值
            
        Returns:
            包含一行数据的DataFrame
        """
        return pd.DataFrame({
            'timestamp': [datetime(2024, 1, 1, 0, 0, 0)],
            'open': [50000.0],
            'high': [51000.0],
            'low': [49000.0],
            'close': [50500.0],
            'volume': [100.0],
            'RSI14': [rsi_value]
        })
    
    def test_long_only_signal_detection(self):
        """测试仅配置做多条件时只检测做多信号"""
        # 创建仅做多策略
        long_entry = EntryConditions(
            conditions=[
                IndicatorCondition(
                    indicator="RSI14",
                    operator=ComparisonOperator.LT,
                    value=30
                )
            ],
            logic_operator=LogicOperator.AND
        )
        
        strategy = StrategyConfig(
            name="Long Only",
            description="仅做多策略",
            timeframe="1d",
            position_size_type="amount",
            position_size_value=1000.0,
            long_entry_conditions=long_entry
        )
        
        # 创建回测引擎
        kline_data = self.create_test_data(rsi_value=25.0)  # RSI < 30，满足做多条件
        engine = BacktestEngine(strategy, kline_data)
        
        # 测试信号检测
        row = kline_data.iloc[0]
        has_signal, direction = engine._check_entry_signal(row)
        
        assert has_signal is True
        assert direction == "long"
        
        # 测试不满足条件的情况
        kline_data_high_rsi = self.create_test_data(rsi_value=75.0)  # RSI > 70
        row_high_rsi = kline_data_high_rsi.iloc[0]
        has_signal, direction = engine._check_entry_signal(row_high_rsi)
        
        assert has_signal is False
        assert direction is None
    
    def test_short_only_signal_detection(self):
        """测试仅配置做空条件时只检测做空信号"""
        # 创建仅做空策略
        short_entry = EntryConditions(
            conditions=[
                IndicatorCondition(
                    indicator="RSI14",
                    operator=ComparisonOperator.GT,
                    value=70
                )
            ],
            logic_operator=LogicOperator.AND
        )
        
        strategy = StrategyConfig(
            name="Short Only",
            description="仅做空策略",
            timeframe="1d",
            position_size_type="amount",
            position_size_value=1000.0,
            short_entry_conditions=short_entry
        )
        
        # 创建回测引擎
        kline_data = self.create_test_data(rsi_value=75.0)  # RSI > 70，满足做空条件
        engine = BacktestEngine(strategy, kline_data)
        
        # 测试信号检测
        row = kline_data.iloc[0]
        has_signal, direction = engine._check_entry_signal(row)
        
        assert has_signal is True
        assert direction == "short"
        
        # 测试不满足条件的情况
        kline_data_low_rsi = self.create_test_data(rsi_value=25.0)  # RSI < 30
        row_low_rsi = kline_data_low_rsi.iloc[0]
        has_signal, direction = engine._check_entry_signal(row_low_rsi)
        
        assert has_signal is False
        assert direction is None
    
    def test_dual_direction_long_signal(self):
        """测试双向策略检测做多信号"""
        # 创建双向策略
        long_entry = EntryConditions(
            conditions=[
                IndicatorCondition(
                    indicator="RSI14",
                    operator=ComparisonOperator.LT,
                    value=30
                )
            ],
            logic_operator=LogicOperator.AND
        )
        
        short_entry = EntryConditions(
            conditions=[
                IndicatorCondition(
                    indicator="RSI14",
                    operator=ComparisonOperator.GT,
                    value=70
                )
            ],
            logic_operator=LogicOperator.AND
        )
        
        strategy = StrategyConfig(
            name="Dual Direction",
            description="双向策略",
            timeframe="1d",
            position_size_type="amount",
            position_size_value=1000.0,
            long_entry_conditions=long_entry,
            short_entry_conditions=short_entry
        )
        
        # 创建回测引擎
        kline_data = self.create_test_data(rsi_value=25.0)  # RSI < 30，满足做多条件
        engine = BacktestEngine(strategy, kline_data)
        
        # 测试信号检测
        row = kline_data.iloc[0]
        has_signal, direction = engine._check_entry_signal(row)
        
        assert has_signal is True
        assert direction == "long"
    
    def test_dual_direction_short_signal(self):
        """测试双向策略检测做空信号"""
        # 创建双向策略
        long_entry = EntryConditions(
            conditions=[
                IndicatorCondition(
                    indicator="RSI14",
                    operator=ComparisonOperator.LT,
                    value=30
                )
            ],
            logic_operator=LogicOperator.AND
        )
        
        short_entry = EntryConditions(
            conditions=[
                IndicatorCondition(
                    indicator="RSI14",
                    operator=ComparisonOperator.GT,
                    value=70
                )
            ],
            logic_operator=LogicOperator.AND
        )
        
        strategy = StrategyConfig(
            name="Dual Direction",
            description="双向策略",
            timeframe="1d",
            position_size_type="amount",
            position_size_value=1000.0,
            long_entry_conditions=long_entry,
            short_entry_conditions=short_entry
        )
        
        # 创建回测引擎
        kline_data = self.create_test_data(rsi_value=75.0)  # RSI > 70，满足做空条件
        engine = BacktestEngine(strategy, kline_data)
        
        # 测试信号检测
        row = kline_data.iloc[0]
        has_signal, direction = engine._check_entry_signal(row)
        
        assert has_signal is True
        assert direction == "short"
    
    def test_both_signals_no_position_prioritize_long(self):
        """测试同时满足双向信号且无持仓时优先做多"""
        # 创建双向策略，条件设置为总是满足
        long_entry = EntryConditions(
            conditions=[
                IndicatorCondition(
                    indicator="RSI14",
                    operator=ComparisonOperator.GT,
                    value=0  # 总是满足
                )
            ],
            logic_operator=LogicOperator.AND
        )
        
        short_entry = EntryConditions(
            conditions=[
                IndicatorCondition(
                    indicator="RSI14",
                    operator=ComparisonOperator.GT,
                    value=0  # 总是满足
                )
            ],
            logic_operator=LogicOperator.AND
        )
        
        strategy = StrategyConfig(
            name="Both Signals",
            description="同时满足双向信号",
            timeframe="1d",
            position_size_type="amount",
            position_size_value=1000.0,
            long_entry_conditions=long_entry,
            short_entry_conditions=short_entry
        )
        
        # 创建回测引擎
        kline_data = self.create_test_data(rsi_value=50.0)
        engine = BacktestEngine(strategy, kline_data)
        
        # 确保没有持仓
        assert engine.current_position is None
        
        # 测试信号检测
        row = kline_data.iloc[0]
        has_signal, direction = engine._check_entry_signal(row)
        
        # 应该优先做多
        assert has_signal is True
        assert direction == "long"
    
    def test_both_signals_with_position_no_new_signal(self):
        """测试同时满足双向信号且有持仓时不触发新信号"""
        from backend.backtest.models import Position
        
        # 创建双向策略，条件设置为总是满足
        long_entry = EntryConditions(
            conditions=[
                IndicatorCondition(
                    indicator="RSI14",
                    operator=ComparisonOperator.GT,
                    value=0  # 总是满足
                )
            ],
            logic_operator=LogicOperator.AND
        )
        
        short_entry = EntryConditions(
            conditions=[
                IndicatorCondition(
                    indicator="RSI14",
                    operator=ComparisonOperator.GT,
                    value=0  # 总是满足
                )
            ],
            logic_operator=LogicOperator.AND
        )
        
        strategy = StrategyConfig(
            name="Both Signals",
            description="同时满足双向信号",
            timeframe="1d",
            position_size_type="amount",
            position_size_value=1000.0,
            long_entry_conditions=long_entry,
            short_entry_conditions=short_entry
        )
        
        # 创建回测引擎
        kline_data = self.create_test_data(rsi_value=50.0)
        engine = BacktestEngine(strategy, kline_data)
        
        # 手动设置一个持仓
        engine.current_position = Position(
            entry_time=datetime(2024, 1, 1, 0, 0, 0),
            entry_price=50000.0,
            position_size=0.02,
            position_value=1000.0,
            direction="long",
            entry_capital=1000.0
        )
        
        # 测试信号检测
        row = kline_data.iloc[0]
        has_signal, direction = engine._check_entry_signal(row)
        
        # 应该不触发新信号
        assert has_signal is False
        assert direction is None
    
    def test_no_signals(self):
        """测试没有信号的情况"""
        # 创建双向策略
        long_entry = EntryConditions(
            conditions=[
                IndicatorCondition(
                    indicator="RSI14",
                    operator=ComparisonOperator.LT,
                    value=30
                )
            ],
            logic_operator=LogicOperator.AND
        )
        
        short_entry = EntryConditions(
            conditions=[
                IndicatorCondition(
                    indicator="RSI14",
                    operator=ComparisonOperator.GT,
                    value=70
                )
            ],
            logic_operator=LogicOperator.AND
        )
        
        strategy = StrategyConfig(
            name="Dual Direction",
            description="双向策略",
            timeframe="1d",
            position_size_type="amount",
            position_size_value=1000.0,
            long_entry_conditions=long_entry,
            short_entry_conditions=short_entry
        )
        
        # 创建回测引擎，RSI在中间值，不满足任何条件
        kline_data = self.create_test_data(rsi_value=50.0)
        engine = BacktestEngine(strategy, kline_data)
        
        # 测试信号检测
        row = kline_data.iloc[0]
        has_signal, direction = engine._check_entry_signal(row)
        
        assert has_signal is False
        assert direction is None
    
    def test_check_long_entry_signal_method(self):
        """测试 _check_long_entry_signal 方法"""
        long_entry = EntryConditions(
            conditions=[
                IndicatorCondition(
                    indicator="RSI14",
                    operator=ComparisonOperator.LT,
                    value=30
                )
            ],
            logic_operator=LogicOperator.AND
        )
        
        strategy = StrategyConfig(
            name="Long Only",
            description="仅做多策略",
            timeframe="1d",
            position_size_type="amount",
            position_size_value=1000.0,
            long_entry_conditions=long_entry
        )
        
        kline_data = self.create_test_data(rsi_value=25.0)
        engine = BacktestEngine(strategy, kline_data)
        
        row = kline_data.iloc[0]
        result = engine._check_long_entry_signal(row)
        
        assert result is True
    
    def test_check_short_entry_signal_method(self):
        """测试 _check_short_entry_signal 方法"""
        short_entry = EntryConditions(
            conditions=[
                IndicatorCondition(
                    indicator="RSI14",
                    operator=ComparisonOperator.GT,
                    value=70
                )
            ],
            logic_operator=LogicOperator.AND
        )
        
        strategy = StrategyConfig(
            name="Short Only",
            description="仅做空策略",
            timeframe="1d",
            position_size_type="amount",
            position_size_value=1000.0,
            short_entry_conditions=short_entry
        )
        
        kline_data = self.create_test_data(rsi_value=75.0)
        engine = BacktestEngine(strategy, kline_data)
        
        row = kline_data.iloc[0]
        result = engine._check_short_entry_signal(row)
        
        assert result is True
    
    def test_no_long_conditions_returns_false(self):
        """测试未配置做多条件时返回False"""
        strategy = StrategyConfig(
            name="Short Only",
            description="仅做空策略",
            timeframe="1d",
            position_size_type="amount",
            position_size_value=1000.0,
            short_entry_conditions=EntryConditions(
                conditions=[
                    IndicatorCondition(
                        indicator="RSI14",
                        operator=ComparisonOperator.GT,
                        value=70
                    )
                ],
                logic_operator=LogicOperator.AND
            )
        )
        
        kline_data = self.create_test_data(rsi_value=25.0)
        engine = BacktestEngine(strategy, kline_data)
        
        row = kline_data.iloc[0]
        result = engine._check_long_entry_signal(row)
        
        assert result is False
    
    def test_no_short_conditions_returns_false(self):
        """测试未配置做空条件时返回False"""
        strategy = StrategyConfig(
            name="Long Only",
            description="仅做多策略",
            timeframe="1d",
            position_size_type="amount",
            position_size_value=1000.0,
            long_entry_conditions=EntryConditions(
                conditions=[
                    IndicatorCondition(
                        indicator="RSI14",
                        operator=ComparisonOperator.LT,
                        value=30
                    )
                ],
                logic_operator=LogicOperator.AND
            )
        )
        
        kline_data = self.create_test_data(rsi_value=75.0)
        engine = BacktestEngine(strategy, kline_data)
        
        row = kline_data.iloc[0]
        result = engine._check_short_entry_signal(row)
        
        assert result is False
    
    def test_multiple_conditions_and_logic_long(self):
        """测试多个条件使用AND逻辑的做多信号检测"""
        # 创建包含多个条件的做多策略（RSI < 30 AND close > 49000）
        long_entry = EntryConditions(
            conditions=[
                IndicatorCondition(
                    indicator="RSI14",
                    operator=ComparisonOperator.LT,
                    value=30
                ),
                IndicatorCondition(
                    indicator="close",
                    operator=ComparisonOperator.GT,
                    value=49000
                )
            ],
            logic_operator=LogicOperator.AND
        )
        
        strategy = StrategyConfig(
            name="Multi Condition Long",
            description="多条件做多策略",
            timeframe="1d",
            position_size_type="amount",
            position_size_value=1000.0,
            long_entry_conditions=long_entry
        )
        
        # 测试两个条件都满足的情况
        kline_data = self.create_test_data(rsi_value=25.0)  # RSI < 30, close = 50500 > 49000
        engine = BacktestEngine(strategy, kline_data)
        row = kline_data.iloc[0]
        result = engine._check_long_entry_signal(row)
        assert result is True
        
        # 测试只满足一个条件的情况（RSI满足，close不满足）
        kline_data2 = pd.DataFrame({
            'timestamp': [datetime(2024, 1, 1, 0, 0, 0)],
            'open': [48000.0],
            'high': [48500.0],
            'low': [47500.0],
            'close': [48000.0],  # close < 49000，不满足
            'volume': [100.0],
            'RSI14': [25.0]  # RSI < 30，满足
        })
        engine2 = BacktestEngine(strategy, kline_data2)
        row2 = kline_data2.iloc[0]
        result2 = engine2._check_long_entry_signal(row2)
        assert result2 is False
    
    def test_multiple_conditions_or_logic_long(self):
        """测试多个条件使用OR逻辑的做多信号检测"""
        # 创建包含多个条件的做多策略（RSI < 30 OR close < 48000）
        long_entry = EntryConditions(
            conditions=[
                IndicatorCondition(
                    indicator="RSI14",
                    operator=ComparisonOperator.LT,
                    value=30
                ),
                IndicatorCondition(
                    indicator="close",
                    operator=ComparisonOperator.LT,
                    value=48000
                )
            ],
            logic_operator=LogicOperator.OR
        )
        
        strategy = StrategyConfig(
            name="Multi Condition Long OR",
            description="多条件OR做多策略",
            timeframe="1d",
            position_size_type="amount",
            position_size_value=1000.0,
            long_entry_conditions=long_entry
        )
        
        # 测试只满足第一个条件的情况
        kline_data = self.create_test_data(rsi_value=25.0)  # RSI < 30满足，close = 50500不满足
        engine = BacktestEngine(strategy, kline_data)
        row = kline_data.iloc[0]
        result = engine._check_long_entry_signal(row)
        assert result is True
        
        # 测试只满足第二个条件的情况
        kline_data2 = pd.DataFrame({
            'timestamp': [datetime(2024, 1, 1, 0, 0, 0)],
            'open': [47000.0],
            'high': [47500.0],
            'low': [46500.0],
            'close': [47000.0],  # close < 48000，满足
            'volume': [100.0],
            'RSI14': [50.0]  # RSI > 30，不满足
        })
        engine2 = BacktestEngine(strategy, kline_data2)
        row2 = kline_data2.iloc[0]
        result2 = engine2._check_long_entry_signal(row2)
        assert result2 is True
        
        # 测试两个条件都不满足的情况
        kline_data3 = pd.DataFrame({
            'timestamp': [datetime(2024, 1, 1, 0, 0, 0)],
            'open': [50000.0],
            'high': [51000.0],
            'low': [49000.0],
            'close': [50500.0],  # close > 48000，不满足
            'volume': [100.0],
            'RSI14': [50.0]  # RSI > 30，不满足
        })
        engine3 = BacktestEngine(strategy, kline_data3)
        row3 = kline_data3.iloc[0]
        result3 = engine3._check_long_entry_signal(row3)
        assert result3 is False
    
    def test_multiple_conditions_and_logic_short(self):
        """测试多个条件使用AND逻辑的做空信号检测"""
        # 创建包含多个条件的做空策略（RSI > 70 AND close > 51000）
        short_entry = EntryConditions(
            conditions=[
                IndicatorCondition(
                    indicator="RSI14",
                    operator=ComparisonOperator.GT,
                    value=70
                ),
                IndicatorCondition(
                    indicator="close",
                    operator=ComparisonOperator.GT,
                    value=51000
                )
            ],
            logic_operator=LogicOperator.AND
        )
        
        strategy = StrategyConfig(
            name="Multi Condition Short",
            description="多条件做空策略",
            timeframe="1d",
            position_size_type="amount",
            position_size_value=1000.0,
            short_entry_conditions=short_entry
        )
        
        # 测试两个条件都满足的情况
        kline_data = pd.DataFrame({
            'timestamp': [datetime(2024, 1, 1, 0, 0, 0)],
            'open': [51000.0],
            'high': [52000.0],
            'low': [50500.0],
            'close': [51500.0],  # close > 51000，满足
            'volume': [100.0],
            'RSI14': [75.0]  # RSI > 70，满足
        })
        engine = BacktestEngine(strategy, kline_data)
        row = kline_data.iloc[0]
        result = engine._check_short_entry_signal(row)
        assert result is True
        
        # 测试只满足一个条件的情况（RSI满足，close不满足）
        kline_data2 = pd.DataFrame({
            'timestamp': [datetime(2024, 1, 1, 0, 0, 0)],
            'open': [50000.0],
            'high': [50500.0],
            'low': [49500.0],
            'close': [50000.0],  # close < 51000，不满足
            'volume': [100.0],
            'RSI14': [75.0]  # RSI > 70，满足
        })
        engine2 = BacktestEngine(strategy, kline_data2)
        row2 = kline_data2.iloc[0]
        result2 = engine2._check_short_entry_signal(row2)
        assert result2 is False
    
    def test_multiple_conditions_or_logic_short(self):
        """测试多个条件使用OR逻辑的做空信号检测"""
        # 创建包含多个条件的做空策略（RSI > 70 OR close > 52000）
        short_entry = EntryConditions(
            conditions=[
                IndicatorCondition(
                    indicator="RSI14",
                    operator=ComparisonOperator.GT,
                    value=70
                ),
                IndicatorCondition(
                    indicator="close",
                    operator=ComparisonOperator.GT,
                    value=52000
                )
            ],
            logic_operator=LogicOperator.OR
        )
        
        strategy = StrategyConfig(
            name="Multi Condition Short OR",
            description="多条件OR做空策略",
            timeframe="1d",
            position_size_type="amount",
            position_size_value=1000.0,
            short_entry_conditions=short_entry
        )
        
        # 测试只满足第一个条件的情况
        kline_data = pd.DataFrame({
            'timestamp': [datetime(2024, 1, 1, 0, 0, 0)],
            'open': [50000.0],
            'high': [51000.0],
            'low': [49000.0],
            'close': [50500.0],  # close < 52000，不满足
            'volume': [100.0],
            'RSI14': [75.0]  # RSI > 70，满足
        })
        engine = BacktestEngine(strategy, kline_data)
        row = kline_data.iloc[0]
        result = engine._check_short_entry_signal(row)
        assert result is True
        
        # 测试只满足第二个条件的情况
        kline_data2 = pd.DataFrame({
            'timestamp': [datetime(2024, 1, 1, 0, 0, 0)],
            'open': [52000.0],
            'high': [53000.0],
            'low': [51500.0],
            'close': [52500.0],  # close > 52000，满足
            'volume': [100.0],
            'RSI14': [50.0]  # RSI < 70，不满足
        })
        engine2 = BacktestEngine(strategy, kline_data2)
        row2 = kline_data2.iloc[0]
        result2 = engine2._check_short_entry_signal(row2)
        assert result2 is True
        
        # 测试两个条件都不满足的情况
        kline_data3 = pd.DataFrame({
            'timestamp': [datetime(2024, 1, 1, 0, 0, 0)],
            'open': [50000.0],
            'high': [51000.0],
            'low': [49000.0],
            'close': [50500.0],  # close < 52000，不满足
            'volume': [100.0],
            'RSI14': [50.0]  # RSI < 70，不满足
        })
        engine3 = BacktestEngine(strategy, kline_data3)
        row3 = kline_data3.iloc[0]
        result3 = engine3._check_short_entry_signal(row3)
        assert result3 is False
    
    def test_three_conditions_and_logic(self):
        """测试三个条件使用AND逻辑的信号检测"""
        # 创建包含三个条件的做多策略（RSI < 30 AND close > 49000 AND volume > 50）
        long_entry = EntryConditions(
            conditions=[
                IndicatorCondition(
                    indicator="RSI14",
                    operator=ComparisonOperator.LT,
                    value=30
                ),
                IndicatorCondition(
                    indicator="close",
                    operator=ComparisonOperator.GT,
                    value=49000
                ),
                IndicatorCondition(
                    indicator="volume",
                    operator=ComparisonOperator.GT,
                    value=50
                )
            ],
            logic_operator=LogicOperator.AND
        )
        
        strategy = StrategyConfig(
            name="Three Conditions Long",
            description="三条件做多策略",
            timeframe="1d",
            position_size_type="amount",
            position_size_value=1000.0,
            long_entry_conditions=long_entry
        )
        
        # 测试三个条件都满足的情况
        kline_data = self.create_test_data(rsi_value=25.0)  # RSI < 30, close = 50500 > 49000, volume = 100 > 50
        engine = BacktestEngine(strategy, kline_data)
        row = kline_data.iloc[0]
        result = engine._check_long_entry_signal(row)
        assert result is True
        
        # 测试只满足两个条件的情况（volume不满足）
        kline_data2 = pd.DataFrame({
            'timestamp': [datetime(2024, 1, 1, 0, 0, 0)],
            'open': [50000.0],
            'high': [51000.0],
            'low': [49000.0],
            'close': [50500.0],  # close > 49000，满足
            'volume': [30.0],  # volume < 50，不满足
            'RSI14': [25.0]  # RSI < 30，满足
        })
        engine2 = BacktestEngine(strategy, kline_data2)
        row2 = kline_data2.iloc[0]
        result2 = engine2._check_long_entry_signal(row2)
        assert result2 is False
    
    def test_complex_dual_direction_scenario(self):
        """测试复杂的双向策略场景"""
        # 创建复杂的双向策略
        # 做多：RSI < 30 AND close > 49000
        # 做空：RSI > 70 AND close < 52000
        long_entry = EntryConditions(
            conditions=[
                IndicatorCondition(
                    indicator="RSI14",
                    operator=ComparisonOperator.LT,
                    value=30
                ),
                IndicatorCondition(
                    indicator="close",
                    operator=ComparisonOperator.GT,
                    value=49000
                )
            ],
            logic_operator=LogicOperator.AND
        )
        
        short_entry = EntryConditions(
            conditions=[
                IndicatorCondition(
                    indicator="RSI14",
                    operator=ComparisonOperator.GT,
                    value=70
                ),
                IndicatorCondition(
                    indicator="close",
                    operator=ComparisonOperator.LT,
                    value=52000
                )
            ],
            logic_operator=LogicOperator.AND
        )
        
        strategy = StrategyConfig(
            name="Complex Dual Direction",
            description="复杂双向策略",
            timeframe="1d",
            position_size_type="amount",
            position_size_value=1000.0,
            long_entry_conditions=long_entry,
            short_entry_conditions=short_entry
        )
        
        # 测试满足做多条件的情况
        kline_data_long = self.create_test_data(rsi_value=25.0)  # RSI < 30, close = 50500 > 49000
        engine_long = BacktestEngine(strategy, kline_data_long)
        row_long = kline_data_long.iloc[0]
        has_signal, direction = engine_long._check_entry_signal(row_long)
        assert has_signal is True
        assert direction == "long"
        
        # 测试满足做空条件的情况
        kline_data_short = pd.DataFrame({
            'timestamp': [datetime(2024, 1, 1, 0, 0, 0)],
            'open': [51000.0],
            'high': [51500.0],
            'low': [50500.0],
            'close': [51000.0],  # close < 52000，满足
            'volume': [100.0],
            'RSI14': [75.0]  # RSI > 70，满足
        })
        engine_short = BacktestEngine(strategy, kline_data_short)
        row_short = kline_data_short.iloc[0]
        has_signal, direction = engine_short._check_entry_signal(row_short)
        assert has_signal is True
        assert direction == "short"
        
        # 测试两个方向都不满足的情况
        kline_data_none = pd.DataFrame({
            'timestamp': [datetime(2024, 1, 1, 0, 0, 0)],
            'open': [50000.0],
            'high': [51000.0],
            'low': [49000.0],
            'close': [50500.0],  # 不满足任何条件
            'volume': [100.0],
            'RSI14': [50.0]  # RSI在中间，不满足任何条件
        })
        engine_none = BacktestEngine(strategy, kline_data_none)
        row_none = kline_data_none.iloc[0]
        has_signal, direction = engine_none._check_entry_signal(row_none)
        assert has_signal is False
        assert direction is None


class TestReverseSignalProcessing:
    """测试反向信号处理逻辑"""
    
    def create_dual_direction_strategy(self) -> StrategyConfig:
        """创建双向策略配置"""
        long_entry = EntryConditions(
            conditions=[
                IndicatorCondition(
                    indicator="RSI14",
                    operator=ComparisonOperator.LT,
                    value=30
                )
            ],
            logic_operator=LogicOperator.AND
        )
        
        short_entry = EntryConditions(
            conditions=[
                IndicatorCondition(
                    indicator="RSI14",
                    operator=ComparisonOperator.GT,
                    value=70
                )
            ],
            logic_operator=LogicOperator.AND
        )
        
        return StrategyConfig(
            name="Dual Direction RSI",
            description="双向RSI策略",
            timeframe="1d",
            position_size_type="amount",
            position_size_value=1000.0,
            initial_capital=10000.0,
            long_entry_conditions=long_entry,
            short_entry_conditions=short_entry
        )
    
    def test_reverse_signal_long_to_short(self):
        """测试持有多仓时出现做空信号的处理（先平后开）"""
        strategy = self.create_dual_direction_strategy()
        
        # 创建测试数据：第一行RSI=25（做多），第二行RSI=75（做空）
        kline_data = pd.DataFrame({
            'timestamp': [
                datetime(2024, 1, 1, 0, 0, 0),
                datetime(2024, 1, 2, 0, 0, 0)
            ],
            'open': [50000.0, 51000.0],
            'high': [51000.0, 52000.0],
            'low': [49000.0, 50000.0],
            'close': [50500.0, 51500.0],
            'volume': [100.0, 100.0],
            'RSI14': [25.0, 75.0]
        })
        
        engine = BacktestEngine(strategy, kline_data)
        result = engine.run()
        
        # 验证交易记录
        assert len(result.trades) == 2, "应该有2笔交易：平多仓和平空仓"
        
        # 第一笔交易：平多仓（反向信号触发）
        first_trade = result.trades[0]
        assert first_trade.direction == "long", "第一笔交易应该是多仓"
        assert first_trade.exit_reason == "reverse_signal", "平仓原因应该是反向信号"
        assert first_trade.entry_price == 50500.0, "开仓价格应该是50500"
        assert first_trade.exit_price == 51500.0, "平仓价格应该是51500"
        
        # 第二笔交易：平空仓（回测结束）
        second_trade = result.trades[1]
        assert second_trade.direction == "short", "第二笔交易应该是空仓"
        assert second_trade.entry_price == 51500.0, "开仓价格应该是51500"
    
    def test_reverse_signal_short_to_long(self):
        """测试持有空仓时出现做多信号的处理（先平后开）"""
        strategy = self.create_dual_direction_strategy()
        
        # 创建测试数据：第一行RSI=75（做空），第二行RSI=25（做多）
        kline_data = pd.DataFrame({
            'timestamp': [
                datetime(2024, 1, 1, 0, 0, 0),
                datetime(2024, 1, 2, 0, 0, 0)
            ],
            'open': [50000.0, 49000.0],
            'high': [51000.0, 50000.0],
            'low': [49000.0, 48000.0],
            'close': [50500.0, 49500.0],
            'volume': [100.0, 100.0],
            'RSI14': [75.0, 25.0]
        })
        
        engine = BacktestEngine(strategy, kline_data)
        result = engine.run()
        
        # 验证交易记录
        assert len(result.trades) == 2, "应该有2笔交易：平空仓和平多仓"
        
        # 第一笔交易：平空仓（反向信号触发）
        first_trade = result.trades[0]
        assert first_trade.direction == "short", "第一笔交易应该是空仓"
        assert first_trade.exit_reason == "reverse_signal", "平仓原因应该是反向信号"
        assert first_trade.entry_price == 50500.0, "开仓价格应该是50500"
        assert first_trade.exit_price == 49500.0, "平仓价格应该是49500"
        
        # 第二笔交易：平多仓（回测结束）
        second_trade = result.trades[1]
        assert second_trade.direction == "long", "第二笔交易应该是多仓"
        assert second_trade.entry_price == 49500.0, "开仓价格应该是49500"
    
    def test_reverse_signal_insufficient_capital(self):
        """测试平仓后资金不足以开新仓的情况"""
        strategy = self.create_dual_direction_strategy()
        # 设置较小的初始资金和较大的仓位
        strategy.initial_capital = 1000.0
        strategy.position_size_value = 950.0
        
        # 创建测试数据：第一行RSI=25（做多），第二行RSI=75（做空），价格大幅下跌导致亏损
        # 做多从50000跌到45000，亏损约95 USDT，剩余资金约55 USDT，不足以开950的空仓
        kline_data = pd.DataFrame({
            'timestamp': [
                datetime(2024, 1, 1, 0, 0, 0),
                datetime(2024, 1, 2, 0, 0, 0),
                datetime(2024, 1, 3, 0, 0, 0)
            ],
            'open': [50000.0, 45000.0, 45500.0],
            'high': [51000.0, 46000.0, 46000.0],
            'low': [49000.0, 44000.0, 45000.0],
            'close': [50000.0, 45000.0, 45000.0],
            'volume': [100.0, 100.0, 100.0],
            'RSI14': [25.0, 75.0, 50.0]
        })
        
        engine = BacktestEngine(strategy, kline_data)
        result = engine.run()
        
        # 验证交易记录：应该只有1笔交易（平多仓），因为资金不足无法开空仓
        assert len(result.trades) == 1, "应该只有1笔交易：平多仓"
        
        # 验证第一笔交易
        first_trade = result.trades[0]
        assert first_trade.direction == "long", "第一笔交易应该是多仓"
        assert first_trade.exit_reason == "reverse_signal", "平仓原因应该是反向信号"
        
        # 验证最终没有持仓
        assert engine.current_position is None, "最终应该没有持仓"
    
    def test_reverse_signal_with_leverage(self):
        """测试使用杠杆时的反向信号处理"""
        strategy = self.create_dual_direction_strategy()
        strategy.leverage = 5.0  # 5倍杠杆
        strategy.position_size_value = 5000.0  # 5000仓位，需要1000保证金
        
        # 创建测试数据：第一行RSI=25（做多），第二行RSI=75（做空）
        kline_data = pd.DataFrame({
            'timestamp': [
                datetime(2024, 1, 1, 0, 0, 0),
                datetime(2024, 1, 2, 0, 0, 0)
            ],
            'open': [50000.0, 51000.0],
            'high': [51000.0, 52000.0],
            'low': [49000.0, 50000.0],
            'close': [50000.0, 51000.0],
            'volume': [100.0, 100.0],
            'RSI14': [25.0, 75.0]
        })
        
        engine = BacktestEngine(strategy, kline_data)
        result = engine.run()
        
        # 验证交易记录
        assert len(result.trades) == 2, "应该有2笔交易"
        
        # 第一笔交易：平多仓
        first_trade = result.trades[0]
        assert first_trade.direction == "long"
        assert first_trade.exit_reason == "reverse_signal"
        assert first_trade.entry_capital == 1000.0, "保证金应该是1000（5000/5）"
        
        # 第二笔交易：平空仓
        second_trade = result.trades[1]
        assert second_trade.direction == "short"
        assert second_trade.entry_capital == 1000.0, "保证金应该是1000（5000/5）"
    
    def test_reverse_signal_pnl_calculation(self):
        """测试反向信号触发时的盈亏计算"""
        strategy = self.create_dual_direction_strategy()
        
        # 创建测试数据：第一行RSI=25（做多），第二行RSI=75（做空），价格上涨
        kline_data = pd.DataFrame({
            'timestamp': [
                datetime(2024, 1, 1, 0, 0, 0),
                datetime(2024, 1, 2, 0, 0, 0)
            ],
            'open': [50000.0, 51000.0],
            'high': [51000.0, 52000.0],
            'low': [49000.0, 50000.0],
            'close': [50000.0, 52000.0],
            'volume': [100.0, 100.0],
            'RSI14': [25.0, 75.0]
        })
        
        engine = BacktestEngine(strategy, kline_data)
        result = engine.run()
        
        # 验证第一笔交易的盈亏
        first_trade = result.trades[0]
        assert first_trade.direction == "long"
        assert first_trade.exit_reason == "reverse_signal"
        
        # 做多盈利：(52000 - 50000) * position_size
        # position_size = 1000 / 50000 = 0.02 BTC
        # 盈利 = 2000 * 0.02 = 40 USDT
        expected_pnl = (52000.0 - 50000.0) * (1000.0 / 50000.0)
        assert abs(first_trade.profit_loss - expected_pnl) < 0.01, f"盈亏应该约为{expected_pnl}"
        assert first_trade.profit_loss > 0, "做多价格上涨应该盈利"
    
    def test_multiple_reverse_signals(self):
        """测试多次反向信号切换"""
        strategy = self.create_dual_direction_strategy()
        
        # 创建测试数据：多次切换方向
        kline_data = pd.DataFrame({
            'timestamp': [
                datetime(2024, 1, 1, 0, 0, 0),  # RSI=25, 做多
                datetime(2024, 1, 2, 0, 0, 0),  # RSI=75, 做空
                datetime(2024, 1, 3, 0, 0, 0),  # RSI=25, 做多
                datetime(2024, 1, 4, 0, 0, 0),  # RSI=75, 做空
            ],
            'open': [50000.0, 51000.0, 50000.0, 51000.0],
            'high': [51000.0, 52000.0, 51000.0, 52000.0],
            'low': [49000.0, 50000.0, 49000.0, 50000.0],
            'close': [50500.0, 51500.0, 50500.0, 51500.0],
            'volume': [100.0, 100.0, 100.0, 100.0],
            'RSI14': [25.0, 75.0, 25.0, 75.0]
        })
        
        engine = BacktestEngine(strategy, kline_data)
        result = engine.run()
        
        # 验证交易记录：应该有4笔交易
        assert len(result.trades) == 4, "应该有4笔交易"
        
        # 验证每笔交易的方向和平仓原因
        assert result.trades[0].direction == "long"
        assert result.trades[0].exit_reason == "reverse_signal"
        
        assert result.trades[1].direction == "short"
        assert result.trades[1].exit_reason == "reverse_signal"
        
        assert result.trades[2].direction == "long"
        assert result.trades[2].exit_reason == "reverse_signal"
        
        assert result.trades[3].direction == "short"
        assert result.trades[3].exit_reason == "backtest_end"
    
    def test_no_reverse_signal_when_same_direction(self):
        """测试持仓方向与信号方向相同时不触发反向信号"""
        strategy = self.create_dual_direction_strategy()
        
        # 创建测试数据：两行都是做多信号
        kline_data = pd.DataFrame({
            'timestamp': [
                datetime(2024, 1, 1, 0, 0, 0),
                datetime(2024, 1, 2, 0, 0, 0)
            ],
            'open': [50000.0, 50500.0],
            'high': [51000.0, 51500.0],
            'low': [49000.0, 49500.0],
            'close': [50500.0, 51000.0],
            'volume': [100.0, 100.0],
            'RSI14': [25.0, 25.0]  # 两行都是做多信号
        })
        
        engine = BacktestEngine(strategy, kline_data)
        result = engine.run()
        
        # 验证交易记录：应该只有1笔交易（回测结束平仓）
        assert len(result.trades) == 1, "应该只有1笔交易"
        assert result.trades[0].direction == "long"
        assert result.trades[0].exit_reason == "backtest_end", "平仓原因应该是回测结束"
