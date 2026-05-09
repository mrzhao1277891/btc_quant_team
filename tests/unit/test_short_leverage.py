"""
测试做空仓位的杠杆和保证金计算

验证 BacktestEngine 正确计算做空仓位的杠杆、保证金和资金占用
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
    LogicOperator,
    Position
)
from backend.backtest.engine import BacktestEngine


class TestShortLeverage:
    """测试做空仓位的杠杆和保证金计算"""
    
    def create_test_data(self, close_price: float = 50000.0) -> pd.DataFrame:
        """创建测试用的K线数据
        
        Args:
            close_price: 收盘价格
            
        Returns:
            包含一行数据的DataFrame
        """
        return pd.DataFrame({
            'timestamp': [datetime(2024, 1, 1, 0, 0, 0)],
            'open': [close_price - 500],
            'high': [close_price + 500],
            'low': [close_price - 1000],
            'close': [close_price],
            'volume': [100.0],
            'RSI14': [75.0]  # 触发做空信号
        })
    
    def create_short_strategy(self, leverage: float, position_size_value: float, 
                             initial_capital: float = 10000.0) -> StrategyConfig:
        """创建做空策略配置
        
        Args:
            leverage: 杠杆倍数
            position_size_value: 仓位大小（金额）
            initial_capital: 初始资金
            
        Returns:
            策略配置对象
        """
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
            name="Short Leverage Test",
            description="做空杠杆测试策略",
            timeframe="1d",
            position_size_type="amount",
            position_size_value=position_size_value,
            initial_capital=initial_capital,
            leverage=leverage,
            short_entry_conditions=short_entry
        )
    
    def test_short_margin_calculation_1x_leverage(self):
        """测试1倍杠杆下的做空保证金计算"""
        # 配置：1倍杠杆，2000元仓位
        strategy = self.create_short_strategy(leverage=1.0, position_size_value=2000.0)
        kline_data = self.create_test_data(close_price=50000.0)
        engine = BacktestEngine(strategy, kline_data)
        
        # 开仓
        row = kline_data.iloc[0]
        position = engine._open_position(row, direction="short")
        
        # 验证保证金计算：position_value / leverage = 2000 / 1 = 2000
        assert position is not None
        assert position.entry_capital == 2000.0
        assert position.position_value == 2000.0
        assert position.direction == "short"
        
        # 验证持仓数量：position_value / entry_price = 2000 / 50000 = 0.04
        assert abs(position.position_size - 0.04) < 1e-6
        
        # 验证资金占用：初始资金 - 保证金 = 10000 - 2000 = 8000
        assert engine.capital == 8000.0
    
    def test_short_margin_calculation_5x_leverage(self):
        """测试5倍杠杆下的做空保证金计算"""
        # 配置：5倍杠杆，2000元仓位
        strategy = self.create_short_strategy(leverage=5.0, position_size_value=2000.0)
        kline_data = self.create_test_data(close_price=50000.0)
        engine = BacktestEngine(strategy, kline_data)
        
        # 开仓
        row = kline_data.iloc[0]
        position = engine._open_position(row, direction="short")
        
        # 验证保证金计算：position_value / leverage = 2000 / 5 = 400
        assert position is not None
        assert position.entry_capital == 400.0
        assert position.position_value == 2000.0
        assert position.direction == "short"
        
        # 验证持仓数量：position_value / entry_price = 2000 / 50000 = 0.04
        assert abs(position.position_size - 0.04) < 1e-6
        
        # 验证资金占用：初始资金 - 保证金 = 10000 - 400 = 9600
        assert engine.capital == 9600.0
    
    def test_short_margin_calculation_10x_leverage(self):
        """测试10倍杠杆下的做空保证金计算"""
        # 配置：10倍杠杆，5000元仓位
        strategy = self.create_short_strategy(leverage=10.0, position_size_value=5000.0)
        kline_data = self.create_test_data(close_price=50000.0)
        engine = BacktestEngine(strategy, kline_data)
        
        # 开仓
        row = kline_data.iloc[0]
        position = engine._open_position(row, direction="short")
        
        # 验证保证金计算：position_value / leverage = 5000 / 10 = 500
        assert position is not None
        assert position.entry_capital == 500.0
        assert position.position_value == 5000.0
        assert position.direction == "short"
        
        # 验证持仓数量：position_value / entry_price = 5000 / 50000 = 0.1
        assert abs(position.position_size - 0.1) < 1e-6
        
        # 验证资金占用：初始资金 - 保证金 = 10000 - 500 = 9500
        assert engine.capital == 9500.0
    
    def test_short_margin_calculation_20x_leverage(self):
        """测试20倍杠杆下的做空保证金计算"""
        # 配置：20倍杠杆，10000元仓位
        strategy = self.create_short_strategy(leverage=20.0, position_size_value=10000.0)
        kline_data = self.create_test_data(close_price=50000.0)
        engine = BacktestEngine(strategy, kline_data)
        
        # 开仓
        row = kline_data.iloc[0]
        position = engine._open_position(row, direction="short")
        
        # 验证保证金计算：position_value / leverage = 10000 / 20 = 500
        assert position is not None
        assert position.entry_capital == 500.0
        assert position.position_value == 10000.0
        assert position.direction == "short"
        
        # 验证持仓数量：position_value / entry_price = 10000 / 50000 = 0.2
        assert abs(position.position_size - 0.2) < 1e-6
        
        # 验证资金占用：初始资金 - 保证金 = 10000 - 500 = 9500
        assert engine.capital == 9500.0
    
    def test_short_position_value_calculation(self):
        """测试做空仓位价值计算"""
        # 配置：5倍杠杆，3000元仓位
        strategy = self.create_short_strategy(leverage=5.0, position_size_value=3000.0)
        kline_data = self.create_test_data(close_price=60000.0)
        engine = BacktestEngine(strategy, kline_data)
        
        # 开仓
        row = kline_data.iloc[0]
        position = engine._open_position(row, direction="short")
        
        # 验证仓位价值 = position_size_value = 3000
        assert position is not None
        assert position.position_value == 3000.0
        
        # 验证持仓数量 = position_value / entry_price = 3000 / 60000 = 0.05
        assert abs(position.position_size - 0.05) < 1e-6
        
        # 验证保证金 = position_value / leverage = 3000 / 5 = 600
        assert position.entry_capital == 600.0
    
    def test_short_insufficient_margin(self):
        """测试保证金不足时跳过做空信号"""
        # 配置：5倍杠杆，60000元仓位，但初始资金只有10000
        # 需要保证金 = 60000 / 5 = 12000 > 10000（可用资金）
        strategy = self.create_short_strategy(
            leverage=5.0, 
            position_size_value=60000.0,
            initial_capital=10000.0
        )
        kline_data = self.create_test_data(close_price=50000.0)
        engine = BacktestEngine(strategy, kline_data)
        
        # 尝试开仓
        row = kline_data.iloc[0]
        position = engine._open_position(row, direction="short")
        
        # 验证开仓失败（返回None）
        assert position is None
        
        # 验证资金未被扣除
        assert engine.capital == 10000.0
    
    def test_short_margin_return_on_close(self):
        """测试平仓后正确返还保证金"""
        # 配置：5倍杠杆，2000元仓位
        strategy = self.create_short_strategy(leverage=5.0, position_size_value=2000.0)
        kline_data = self.create_test_data(close_price=50000.0)
        engine = BacktestEngine(strategy, kline_data)
        
        # 开仓
        row = kline_data.iloc[0]
        position = engine._open_position(row, direction="short")
        
        # 验证开仓后资金
        assert engine.capital == 9600.0  # 10000 - 400
        
        # 平仓（价格不变，盈亏为0）
        trade = engine._close_position(position, row, "test_close")
        
        # 验证平仓后资金：返还保证金 + 盈亏 = 400 + 0 = 400
        # 总资金 = 9600 + 400 = 10000
        assert engine.capital == 10000.0
        assert trade.profit_loss == 0.0
    
    def test_short_margin_return_with_profit(self):
        """测试平仓盈利后正确返还保证金和盈利"""
        # 配置：5倍杠杆，2000元仓位
        strategy = self.create_short_strategy(leverage=5.0, position_size_value=2000.0)
        
        # 开仓价格 50000
        kline_data_entry = self.create_test_data(close_price=50000.0)
        engine = BacktestEngine(strategy, kline_data_entry)
        
        row_entry = kline_data_entry.iloc[0]
        position = engine._open_position(row_entry, direction="short")
        
        # 验证开仓后资金
        assert engine.capital == 9600.0  # 10000 - 400
        
        # 平仓价格 48000（价格下跌，做空盈利）
        kline_data_exit = self.create_test_data(close_price=48000.0)
        row_exit = kline_data_exit.iloc[0]
        
        # 计算预期盈利：(entry_price - exit_price) * position_size
        # = (50000 - 48000) * 0.04 = 2000 * 0.04 = 80
        expected_pnl = (50000.0 - 48000.0) * 0.04
        
        trade = engine._close_position(position, row_exit, "test_close")
        
        # 验证盈利计算
        assert abs(trade.profit_loss - expected_pnl) < 1e-6
        
        # 验证平仓后资金：返还保证金 + 盈利 = 400 + 80 = 480
        # 总资金 = 9600 + 480 = 10080
        assert abs(engine.capital - 10080.0) < 1e-6
    
    def test_short_margin_return_with_loss(self):
        """测试平仓亏损后正确返还保证金和扣除亏损"""
        # 配置：5倍杠杆，2000元仓位
        strategy = self.create_short_strategy(leverage=5.0, position_size_value=2000.0)
        
        # 开仓价格 50000
        kline_data_entry = self.create_test_data(close_price=50000.0)
        engine = BacktestEngine(strategy, kline_data_entry)
        
        row_entry = kline_data_entry.iloc[0]
        position = engine._open_position(row_entry, direction="short")
        
        # 验证开仓后资金
        assert engine.capital == 9600.0  # 10000 - 400
        
        # 平仓价格 52000（价格上涨，做空亏损）
        kline_data_exit = self.create_test_data(close_price=52000.0)
        row_exit = kline_data_exit.iloc[0]
        
        # 计算预期亏损：(entry_price - exit_price) * position_size
        # = (50000 - 52000) * 0.04 = -2000 * 0.04 = -80
        expected_pnl = (50000.0 - 52000.0) * 0.04
        
        trade = engine._close_position(position, row_exit, "test_close")
        
        # 验证亏损计算
        assert abs(trade.profit_loss - expected_pnl) < 1e-6
        
        # 验证平仓后资金：返还保证金 + 亏损 = 400 + (-80) = 320
        # 总资金 = 9600 + 320 = 9920
        assert abs(engine.capital - 9920.0) < 1e-6
    
    def test_short_position_size_calculation_different_prices(self):
        """测试不同价格下的做空持仓数量计算"""
        # 测试价格 30000
        strategy1 = self.create_short_strategy(leverage=5.0, position_size_value=3000.0)
        kline_data1 = self.create_test_data(close_price=30000.0)
        engine1 = BacktestEngine(strategy1, kline_data1)
        position1 = engine1._open_position(kline_data1.iloc[0], direction="short")
        
        # 持仓数量 = 3000 / 30000 = 0.1
        assert abs(position1.position_size - 0.1) < 1e-6
        
        # 测试价格 60000
        strategy2 = self.create_short_strategy(leverage=5.0, position_size_value=3000.0)
        kline_data2 = self.create_test_data(close_price=60000.0)
        engine2 = BacktestEngine(strategy2, kline_data2)
        position2 = engine2._open_position(kline_data2.iloc[0], direction="short")
        
        # 持仓数量 = 3000 / 60000 = 0.05
        assert abs(position2.position_size - 0.05) < 1e-6
        
        # 测试价格 100000
        strategy3 = self.create_short_strategy(leverage=5.0, position_size_value=5000.0)
        kline_data3 = self.create_test_data(close_price=100000.0)
        engine3 = BacktestEngine(strategy3, kline_data3)
        position3 = engine3._open_position(kline_data3.iloc[0], direction="short")
        
        # 持仓数量 = 5000 / 100000 = 0.05
        assert abs(position3.position_size - 0.05) < 1e-6
    
    def test_short_leverage_formula_verification(self):
        """验证做空杠杆公式：保证金 = 仓位价值 / 杠杆"""
        test_cases = [
            # (leverage, position_value, expected_margin)
            (1.0, 1000.0, 1000.0),
            (2.0, 1000.0, 500.0),
            (5.0, 2500.0, 500.0),
            (10.0, 5000.0, 500.0),
            (20.0, 10000.0, 500.0),
            (3.0, 6000.0, 2000.0),
            (4.0, 8000.0, 2000.0),
        ]
        
        for leverage, position_value, expected_margin in test_cases:
            strategy = self.create_short_strategy(
                leverage=leverage, 
                position_size_value=position_value,
                initial_capital=20000.0  # 确保资金充足
            )
            kline_data = self.create_test_data(close_price=50000.0)
            engine = BacktestEngine(strategy, kline_data)
            
            position = engine._open_position(kline_data.iloc[0], direction="short")
            
            # 验证保证金计算
            assert position is not None, f"Failed for leverage={leverage}, position_value={position_value}"
            assert abs(position.entry_capital - expected_margin) < 1e-6, \
                f"Margin mismatch for leverage={leverage}, position_value={position_value}: " \
                f"expected {expected_margin}, got {position.entry_capital}"
    
    def test_short_trade_record_entry_capital(self):
        """验证交易记录正确记录做空交易的保证金"""
        # 配置：10倍杠杆，5000元仓位
        strategy = self.create_short_strategy(leverage=10.0, position_size_value=5000.0)
        kline_data = self.create_test_data(close_price=50000.0)
        engine = BacktestEngine(strategy, kline_data)
        
        # 开仓
        row = kline_data.iloc[0]
        position = engine._open_position(row, direction="short")
        
        # 平仓
        trade = engine._close_position(position, row, "test_close")
        
        # 验证交易记录中的 entry_capital（保证金）
        # 保证金 = 5000 / 10 = 500
        assert trade.entry_capital == 500.0
        assert trade.direction == "short"
    
    def test_short_multiple_leverage_scenarios(self):
        """测试多种杠杆场景下的资金占用"""
        scenarios = [
            # (leverage, position_value, initial_capital, should_succeed)
            (1.0, 5000.0, 10000.0, True),   # 需要5000保证金，有10000，成功
            (5.0, 5000.0, 10000.0, True),   # 需要1000保证金，有10000，成功
            (10.0, 5000.0, 10000.0, True),  # 需要500保证金，有10000，成功
            (5.0, 60000.0, 10000.0, False), # 需要12000保证金，只有10000，失败
            (10.0, 120000.0, 10000.0, False), # 需要12000保证金，只有10000，失败
        ]
        
        for leverage, position_value, initial_capital, should_succeed in scenarios:
            strategy = self.create_short_strategy(
                leverage=leverage,
                position_size_value=position_value,
                initial_capital=initial_capital
            )
            kline_data = self.create_test_data(close_price=50000.0)
            engine = BacktestEngine(strategy, kline_data)
            
            position = engine._open_position(kline_data.iloc[0], direction="short")
            
            if should_succeed:
                assert position is not None, \
                    f"Expected success for leverage={leverage}, position_value={position_value}, " \
                    f"initial_capital={initial_capital}"
                expected_margin = position_value / leverage
                assert abs(position.entry_capital - expected_margin) < 1e-6
                assert abs(engine.capital - (initial_capital - expected_margin)) < 1e-6
            else:
                assert position is None, \
                    f"Expected failure for leverage={leverage}, position_value={position_value}, " \
                    f"initial_capital={initial_capital}"
                assert engine.capital == initial_capital  # 资金未被扣除
    
    def test_short_high_leverage_profit_amplification(self):
        """测试高杠杆下做空盈利的放大效果"""
        # 配置：10倍杠杆，10000元仓位
        strategy = self.create_short_strategy(leverage=10.0, position_size_value=10000.0)
        
        # 开仓价格 50000
        kline_data_entry = self.create_test_data(close_price=50000.0)
        engine = BacktestEngine(strategy, kline_data_entry)
        
        row_entry = kline_data_entry.iloc[0]
        position = engine._open_position(row_entry, direction="short")
        
        # 保证金 = 10000 / 10 = 1000
        assert position.entry_capital == 1000.0
        
        # 平仓价格 45000（价格下跌10%）
        kline_data_exit = self.create_test_data(close_price=45000.0)
        row_exit = kline_data_exit.iloc[0]
        
        # 持仓数量 = 10000 / 50000 = 0.2
        # 盈利 = (50000 - 45000) * 0.2 = 5000 * 0.2 = 1000
        expected_pnl = (50000.0 - 45000.0) * 0.2
        
        trade = engine._close_position(position, row_exit, "test_close")
        
        # 验证盈利
        assert abs(trade.profit_loss - expected_pnl) < 1e-6
        
        # 验证盈利百分比（相对于保证金）
        # pnl_pct = 1000 / 1000 * 100 = 100%
        expected_pnl_pct = (expected_pnl / position.entry_capital) * 100
        assert abs(trade.profit_loss_pct - expected_pnl_pct) < 1e-6
    
    def test_short_high_leverage_loss_amplification(self):
        """测试高杠杆下做空亏损的放大效果"""
        # 配置：10倍杠杆，10000元仓位
        strategy = self.create_short_strategy(leverage=10.0, position_size_value=10000.0)
        
        # 开仓价格 50000
        kline_data_entry = self.create_test_data(close_price=50000.0)
        engine = BacktestEngine(strategy, kline_data_entry)
        
        row_entry = kline_data_entry.iloc[0]
        position = engine._open_position(row_entry, direction="short")
        
        # 保证金 = 10000 / 10 = 1000
        assert position.entry_capital == 1000.0
        
        # 平仓价格 55000（价格上涨10%）
        kline_data_exit = self.create_test_data(close_price=55000.0)
        row_exit = kline_data_exit.iloc[0]
        
        # 持仓数量 = 10000 / 50000 = 0.2
        # 亏损 = (50000 - 55000) * 0.2 = -5000 * 0.2 = -1000
        expected_pnl = (50000.0 - 55000.0) * 0.2
        
        trade = engine._close_position(position, row_exit, "test_close")
        
        # 验证亏损
        assert abs(trade.profit_loss - expected_pnl) < 1e-6
        
        # 验证亏损百分比（相对于保证金）
        # pnl_pct = -1000 / 1000 * 100 = -100%
        expected_pnl_pct = (expected_pnl / position.entry_capital) * 100
        assert abs(trade.profit_loss_pct - expected_pnl_pct) < 1e-6
