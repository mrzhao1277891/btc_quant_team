"""
做空盈亏计算单元测试

测试做空仓位的盈亏计算逻辑，包括：
- 做空盈利场景（价格下跌）
- 做空亏损场景（价格上涨）
- 做空持平场景（价格不变）
- 盈亏计算公式验证
- 盈亏百分比计算验证
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from backend.backtest.engine import BacktestEngine
from backend.backtest.models import (
    StrategyConfig,
    EntryConditions,
    ExitConditions,
    Position
)


class TestShortPositionPnL:
    """测试做空仓位盈亏计算"""
    
    def create_short_strategy(self):
        """创建做空策略配置"""
        strategy = StrategyConfig(
            name="Short Test Strategy",
            description="Test strategy for short positions",
            timeframe="1d",
            position_direction="short",
            position_size_type="amount",
            position_size_value=50000.0,
            entry_conditions=EntryConditions(conditions=[]),
            exit_conditions=ExitConditions(indicator_conditions=[]),
            initial_capital=100000.0
        )
        return strategy
    
    def create_sample_kline_data(self):
        """创建示例K线数据"""
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        base_price = 50000
        prices = base_price + np.cumsum(np.random.randn(100) * 100)
        
        df = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': prices * 1.01,
            'low': prices * 0.99,
            'close': prices,
            'volume': np.random.uniform(100, 1000, 100),
        })
        return df
    
    def test_short_profit_price_drops(self):
        """测试做空盈利场景：价格下跌"""
        strategy = self.create_short_strategy()
        kline_data = self.create_sample_kline_data()
        engine = BacktestEngine(strategy, kline_data)
        
        # 创建做空仓位：开仓价格 50000
        position = Position(
            entry_time=datetime(2024, 1, 1),
            entry_price=50000.0,
            position_size=1.0,  # 1 BTC
            position_value=50000.0,
            direction="short",
            entry_capital=50000.0
        )
        
        # 价格下跌到 45000（做空盈利）
        current_price = 45000.0
        pnl_amount, pnl_pct = engine._calculate_pnl(position, current_price)
        
        # 验证盈亏金额：(entry_price - current_price) * position_size
        expected_pnl = (50000.0 - 45000.0) * 1.0
        assert pnl_amount == expected_pnl, f"Expected PnL: {expected_pnl}, Got: {pnl_amount}"
        assert pnl_amount == 5000.0, "Price drop should result in profit for short position"
        
        # 验证盈亏百分比：pnl_amount / entry_capital * 100
        expected_pnl_pct = (5000.0 / 50000.0) * 100
        assert pnl_pct == expected_pnl_pct, f"Expected PnL%: {expected_pnl_pct}, Got: {pnl_pct}"
        assert pnl_pct == 10.0, "PnL percentage should be 10%"
    
    def test_short_loss_price_rises(self):
        """测试做空亏损场景：价格上涨"""
        strategy = self.create_short_strategy()
        kline_data = self.create_sample_kline_data()
        engine = BacktestEngine(strategy, kline_data)
        
        # 创建做空仓位：开仓价格 50000
        position = Position(
            entry_time=datetime(2024, 1, 1),
            entry_price=50000.0,
            position_size=1.0,  # 1 BTC
            position_value=50000.0,
            direction="short",
            entry_capital=50000.0
        )
        
        # 价格上涨到 55000（做空亏损）
        current_price = 55000.0
        pnl_amount, pnl_pct = engine._calculate_pnl(position, current_price)
        
        # 验证盈亏金额：(entry_price - current_price) * position_size
        expected_pnl = (50000.0 - 55000.0) * 1.0
        assert pnl_amount == expected_pnl, f"Expected PnL: {expected_pnl}, Got: {pnl_amount}"
        assert pnl_amount == -5000.0, "Price rise should result in loss for short position"
        
        # 验证盈亏百分比：pnl_amount / entry_capital * 100
        expected_pnl_pct = (-5000.0 / 50000.0) * 100
        assert pnl_pct == expected_pnl_pct, f"Expected PnL%: {expected_pnl_pct}, Got: {pnl_pct}"
        assert pnl_pct == -10.0, "PnL percentage should be -10%"
    
    def test_short_breakeven_price_unchanged(self):
        """测试做空持平场景：价格不变"""
        strategy = self.create_short_strategy()
        kline_data = self.create_sample_kline_data()
        engine = BacktestEngine(strategy, kline_data)
        
        # 创建做空仓位：开仓价格 50000
        position = Position(
            entry_time=datetime(2024, 1, 1),
            entry_price=50000.0,
            position_size=1.0,  # 1 BTC
            position_value=50000.0,
            direction="short",
            entry_capital=50000.0
        )
        
        # 价格不变，仍为 50000（做空持平）
        current_price = 50000.0
        pnl_amount, pnl_pct = engine._calculate_pnl(position, current_price)
        
        # 验证盈亏金额：(entry_price - current_price) * position_size
        expected_pnl = (50000.0 - 50000.0) * 1.0
        assert pnl_amount == expected_pnl, f"Expected PnL: {expected_pnl}, Got: {pnl_amount}"
        assert pnl_amount == 0.0, "No price change should result in zero PnL"
        
        # 验证盈亏百分比
        assert pnl_pct == 0.0, "PnL percentage should be 0%"
    
    def test_short_pnl_formula_verification(self):
        """验证做空盈亏计算公式：(entry_price - current_price) * position_size"""
        strategy = self.create_short_strategy()
        kline_data = self.create_sample_kline_data()
        engine = BacktestEngine(strategy, kline_data)
        
        # 测试多个不同的价格场景
        test_cases = [
            # (entry_price, position_size, current_price, expected_pnl)
            (50000.0, 1.0, 48000.0, 2000.0),   # 价格下跌 4%
            (50000.0, 1.0, 52000.0, -2000.0),  # 价格上涨 4%
            (50000.0, 2.0, 45000.0, 10000.0),  # 持仓2个BTC，价格下跌10%
            (50000.0, 0.5, 55000.0, -2500.0),  # 持仓0.5个BTC，价格上涨10%
            (60000.0, 1.5, 57000.0, 4500.0),   # 不同开仓价格
        ]
        
        for entry_price, position_size, current_price, expected_pnl in test_cases:
            position = Position(
                entry_time=datetime(2024, 1, 1),
                entry_price=entry_price,
                position_size=position_size,
                position_value=entry_price * position_size,
                direction="short",
                entry_capital=entry_price * position_size
            )
            
            pnl_amount, _ = engine._calculate_pnl(position, current_price)
            
            # 验证公式：(entry_price - current_price) * position_size
            calculated_pnl = (entry_price - current_price) * position_size
            assert pnl_amount == calculated_pnl, \
                f"Formula verification failed: entry={entry_price}, size={position_size}, " \
                f"current={current_price}, expected={calculated_pnl}, got={pnl_amount}"
            assert pnl_amount == expected_pnl, \
                f"Expected PnL: {expected_pnl}, Got: {pnl_amount}"
    
    def test_short_pnl_percentage_calculation(self):
        """验证做空盈亏百分比计算"""
        strategy = self.create_short_strategy()
        kline_data = self.create_sample_kline_data()
        engine = BacktestEngine(strategy, kline_data)
        
        # 测试不同的盈亏百分比场景
        test_cases = [
            # (entry_price, position_size, entry_capital, current_price, expected_pnl_pct)
            (50000.0, 1.0, 50000.0, 45000.0, 10.0),    # 10% 盈利
            (50000.0, 1.0, 50000.0, 55000.0, -10.0),   # 10% 亏损
            (50000.0, 1.0, 50000.0, 47500.0, 5.0),     # 5% 盈利
            (50000.0, 1.0, 50000.0, 52500.0, -5.0),    # 5% 亏损
            (50000.0, 2.0, 100000.0, 45000.0, 10.0),   # 持仓2个BTC，10% 盈利
        ]
        
        for entry_price, position_size, entry_capital, current_price, expected_pnl_pct in test_cases:
            position = Position(
                entry_time=datetime(2024, 1, 1),
                entry_price=entry_price,
                position_size=position_size,
                position_value=entry_price * position_size,
                direction="short",
                entry_capital=entry_capital
            )
            
            pnl_amount, pnl_pct = engine._calculate_pnl(position, current_price)
            
            # 验证百分比公式：pnl_amount / entry_capital * 100
            calculated_pnl_pct = (pnl_amount / entry_capital) * 100
            assert abs(pnl_pct - calculated_pnl_pct) < 0.01, \
                f"Percentage formula verification failed: pnl_amount={pnl_amount}, " \
                f"entry_capital={entry_capital}, expected={calculated_pnl_pct}, got={pnl_pct}"
            assert abs(pnl_pct - expected_pnl_pct) < 0.01, \
                f"Expected PnL%: {expected_pnl_pct}, Got: {pnl_pct}"
    
    def test_short_large_price_movement(self):
        """测试做空在大幅价格波动下的盈亏计算"""
        strategy = self.create_short_strategy()
        kline_data = self.create_sample_kline_data()
        engine = BacktestEngine(strategy, kline_data)
        
        position = Position(
            entry_time=datetime(2024, 1, 1),
            entry_price=50000.0,
            position_size=1.0,
            position_value=50000.0,
            direction="short",
            entry_capital=50000.0
        )
        
        # 价格大幅下跌 50%（做空大幅盈利）
        current_price = 25000.0
        pnl_amount, pnl_pct = engine._calculate_pnl(position, current_price)
        
        expected_pnl = (50000.0 - 25000.0) * 1.0
        assert pnl_amount == expected_pnl
        assert pnl_amount == 25000.0
        assert pnl_pct == 50.0
        
        # 价格大幅上涨 100%（做空大幅亏损）
        current_price = 100000.0
        pnl_amount, pnl_pct = engine._calculate_pnl(position, current_price)
        
        expected_pnl = (50000.0 - 100000.0) * 1.0
        assert pnl_amount == expected_pnl
        assert pnl_amount == -50000.0
        assert pnl_pct == -100.0
    
    def test_short_small_position_size(self):
        """测试做空小仓位的盈亏计算"""
        strategy = self.create_short_strategy()
        kline_data = self.create_sample_kline_data()
        engine = BacktestEngine(strategy, kline_data)
        
        # 小仓位：0.1 BTC
        position = Position(
            entry_time=datetime(2024, 1, 1),
            entry_price=50000.0,
            position_size=0.1,
            position_value=5000.0,
            direction="short",
            entry_capital=5000.0
        )
        
        # 价格下跌 10%
        current_price = 45000.0
        pnl_amount, pnl_pct = engine._calculate_pnl(position, current_price)
        
        expected_pnl = (50000.0 - 45000.0) * 0.1
        assert pnl_amount == expected_pnl
        assert pnl_amount == 500.0
        assert pnl_pct == 10.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
