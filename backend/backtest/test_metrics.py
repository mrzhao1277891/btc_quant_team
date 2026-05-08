"""
MetricsCalculator单元测试

测试性能指标计算的正确性，包括：
- 总收益率计算
- 胜率计算
- 最大回撤计算
- 夏普比率计算
- 盈亏比计算
- 交易统计
- 连胜连亏统计
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from backend.backtest.metrics import MetricsCalculator
from backend.backtest.models import TradeRecord


def create_trade_record(
    trade_id: int,
    profit_loss: float,
    entry_time: datetime = None,
    exit_time: datetime = None,
    entry_price: float = 50000.0,
    exit_price: float = 51000.0,
    position_size: float = 0.1,
    direction: str = "long",
    entry_capital: float = 5000.0
) -> TradeRecord:
    """创建测试用的交易记录"""
    if entry_time is None:
        entry_time = datetime(2024, 1, 1, 0, 0, 0)
    if exit_time is None:
        exit_time = entry_time + timedelta(days=1)
    
    profit_loss_pct = profit_loss / entry_capital if entry_capital > 0 else 0.0
    
    return TradeRecord(
        trade_id=trade_id,
        entry_time=entry_time,
        entry_price=entry_price,
        exit_time=exit_time,
        exit_price=exit_price,
        position_size=position_size,
        direction=direction,
        profit_loss=profit_loss,
        profit_loss_pct=profit_loss_pct,
        holding_period=exit_time - entry_time,
        exit_reason="test",
        entry_capital=entry_capital
    )


class TestMetricsCalculator:
    """MetricsCalculator测试类"""
    
    def test_calculate_total_return_positive(self):
        """测试正收益的总收益率计算"""
        trades = [
            create_trade_record(1, 1000.0),  # +1000
            create_trade_record(2, 500.0),   # +500
        ]
        calculator = MetricsCalculator(trades, initial_capital=10000.0)
        
        total_return = calculator.calculate_total_return()
        
        # 总收益 = 1500, 初始资金 = 10000
        # 收益率 = 1500 / 10000 = 0.15
        assert total_return == pytest.approx(0.15, rel=1e-6)
    
    def test_calculate_total_return_negative(self):
        """测试负收益的总收益率计算"""
        trades = [
            create_trade_record(1, -500.0),  # -500
            create_trade_record(2, -300.0),  # -300
        ]
        calculator = MetricsCalculator(trades, initial_capital=10000.0)
        
        total_return = calculator.calculate_total_return()
        
        # 总收益 = -800, 初始资金 = 10000
        # 收益率 = -800 / 10000 = -0.08
        assert total_return == pytest.approx(-0.08, rel=1e-6)
    
    def test_calculate_total_return_zero_capital(self):
        """测试初始资金为0的情况"""
        trades = []
        calculator = MetricsCalculator(trades, initial_capital=0.0)
        
        total_return = calculator.calculate_total_return()
        
        assert total_return == 0.0
    
    def test_calculate_win_rate_all_wins(self):
        """测试全部盈利的胜率"""
        trades = [
            create_trade_record(1, 100.0),
            create_trade_record(2, 200.0),
            create_trade_record(3, 150.0),
        ]
        calculator = MetricsCalculator(trades, initial_capital=10000.0)
        
        win_rate = calculator.calculate_win_rate()
        
        # 3个盈利交易 / 3个总交易 = 1.0
        assert win_rate == pytest.approx(1.0, rel=1e-6)
    
    def test_calculate_win_rate_mixed(self):
        """测试混合盈亏的胜率"""
        trades = [
            create_trade_record(1, 100.0),   # 盈利
            create_trade_record(2, -50.0),   # 亏损
            create_trade_record(3, 200.0),   # 盈利
            create_trade_record(4, -30.0),   # 亏损
            create_trade_record(5, 150.0),   # 盈利
        ]
        calculator = MetricsCalculator(trades, initial_capital=10000.0)
        
        win_rate = calculator.calculate_win_rate()
        
        # 3个盈利交易 / 5个总交易 = 0.6
        assert win_rate == pytest.approx(0.6, rel=1e-6)
    
    def test_calculate_win_rate_no_trades(self):
        """测试无交易的胜率"""
        trades = []
        calculator = MetricsCalculator(trades, initial_capital=10000.0)
        
        win_rate = calculator.calculate_win_rate()
        
        assert win_rate == 0.0
    
    def test_calculate_max_drawdown_simple(self):
        """测试简单的最大回撤计算"""
        trades = []
        calculator = MetricsCalculator(trades, initial_capital=10000.0)
        
        # 创建权益曲线：10000 -> 12000 -> 9000 -> 11000
        equity_curve = pd.Series([10000, 12000, 9000, 11000])
        
        max_dd_amount, max_dd_pct = calculator.calculate_max_drawdown(equity_curve)
        
        # 最大回撤发生在12000 -> 9000
        # 回撤金额 = 12000 - 9000 = 3000
        # 回撤百分比 = 3000 / 12000 = 0.25
        assert max_dd_amount == pytest.approx(3000.0, rel=1e-6)
        assert max_dd_pct == pytest.approx(0.25, rel=1e-6)
    
    def test_calculate_max_drawdown_no_drawdown(self):
        """测试无回撤的情况（持续上涨）"""
        trades = []
        calculator = MetricsCalculator(trades, initial_capital=10000.0)
        
        # 创建持续上涨的权益曲线
        equity_curve = pd.Series([10000, 11000, 12000, 13000])
        
        max_dd_amount, max_dd_pct = calculator.calculate_max_drawdown(equity_curve)
        
        # 无回撤
        assert max_dd_amount == pytest.approx(0.0, rel=1e-6)
        assert max_dd_pct == pytest.approx(0.0, rel=1e-6)
    
    def test_calculate_max_drawdown_empty(self):
        """测试空权益曲线"""
        trades = []
        calculator = MetricsCalculator(trades, initial_capital=10000.0)
        
        equity_curve = pd.Series([])
        
        max_dd_amount, max_dd_pct = calculator.calculate_max_drawdown(equity_curve)
        
        assert max_dd_amount == 0.0
        assert max_dd_pct == 0.0
    
    def test_calculate_sharpe_ratio_positive(self):
        """测试正夏普比率"""
        trades = []
        calculator = MetricsCalculator(trades, initial_capital=10000.0)
        
        # 创建收益率序列：平均收益率为正，有一定波动
        returns = pd.Series([0.01, 0.02, -0.005, 0.015, 0.01])
        
        sharpe_ratio = calculator.calculate_sharpe_ratio(returns)
        
        # 手动计算：mean = 0.01, std ≈ 0.00854
        # sharpe = 0.01 / 0.00854 ≈ 1.17
        expected_mean = returns.mean()
        expected_std = returns.std()
        expected_sharpe = expected_mean / expected_std
        
        assert sharpe_ratio == pytest.approx(expected_sharpe, rel=1e-6)
    
    def test_calculate_sharpe_ratio_zero_std(self):
        """测试标准差为0的情况（所有收益率相同）"""
        trades = []
        calculator = MetricsCalculator(trades, initial_capital=10000.0)
        
        # 所有收益率相同
        returns = pd.Series([0.01, 0.01, 0.01, 0.01])
        
        sharpe_ratio = calculator.calculate_sharpe_ratio(returns)
        
        # 标准差为0，应返回0
        assert sharpe_ratio == 0.0
    
    def test_calculate_sharpe_ratio_empty(self):
        """测试空收益率序列"""
        trades = []
        calculator = MetricsCalculator(trades, initial_capital=10000.0)
        
        returns = pd.Series([])
        
        sharpe_ratio = calculator.calculate_sharpe_ratio(returns)
        
        assert sharpe_ratio == 0.0
    
    def test_calculate_profit_factor(self):
        """测试盈亏比计算"""
        trades = [
            create_trade_record(1, 1000.0),  # 盈利
            create_trade_record(2, -500.0),  # 亏损
            create_trade_record(3, 800.0),   # 盈利
            create_trade_record(4, -300.0),  # 亏损
        ]
        calculator = MetricsCalculator(trades, initial_capital=10000.0)
        
        profit_factor = calculator.calculate_profit_factor()
        
        # 总盈利 = 1000 + 800 = 1800
        # 总亏损 = 500 + 300 = 800
        # 盈亏比 = 1800 / 800 = 2.25
        assert profit_factor == pytest.approx(2.25, rel=1e-6)
    
    def test_calculate_profit_factor_no_losses(self):
        """测试无亏损交易的盈亏比"""
        trades = [
            create_trade_record(1, 1000.0),
            create_trade_record(2, 500.0),
        ]
        calculator = MetricsCalculator(trades, initial_capital=10000.0)
        
        profit_factor = calculator.calculate_profit_factor()
        
        # 无亏损，应返回无穷大
        assert profit_factor == float('inf')
    
    def test_calculate_profit_factor_no_profits(self):
        """测试无盈利交易的盈亏比"""
        trades = [
            create_trade_record(1, -500.0),
            create_trade_record(2, -300.0),
        ]
        calculator = MetricsCalculator(trades, initial_capital=10000.0)
        
        profit_factor = calculator.calculate_profit_factor()
        
        # 无盈利，应返回0
        assert profit_factor == 0.0
    
    def test_calculate_trade_statistics(self):
        """测试交易统计计算"""
        trades = [
            create_trade_record(1, 1000.0),  # 盈利
            create_trade_record(2, -500.0),  # 亏损
            create_trade_record(3, 800.0),   # 盈利
            create_trade_record(4, -300.0),  # 亏损
            create_trade_record(5, 600.0),   # 盈利
        ]
        calculator = MetricsCalculator(trades, initial_capital=10000.0)
        
        total, winning, losing, avg_profit, avg_loss = calculator.calculate_trade_statistics()
        
        assert total == 5
        assert winning == 3
        assert losing == 2
        # 平均盈利 = (1000 + 800 + 600) / 3 = 800
        assert avg_profit == pytest.approx(800.0, rel=1e-6)
        # 平均亏损 = (-500 + -300) / 2 = -400
        assert avg_loss == pytest.approx(-400.0, rel=1e-6)
    
    def test_calculate_streaks(self):
        """测试连胜连亏计算"""
        trades = [
            create_trade_record(1, 100.0),   # 盈利
            create_trade_record(2, 200.0),   # 盈利
            create_trade_record(3, 150.0),   # 盈利 - 连胜3
            create_trade_record(4, -50.0),   # 亏损
            create_trade_record(5, 100.0),   # 盈利
            create_trade_record(6, -30.0),   # 亏损
            create_trade_record(7, -40.0),   # 亏损
            create_trade_record(8, -20.0),   # 亏损
            create_trade_record(9, -10.0),   # 亏损 - 连亏4
        ]
        calculator = MetricsCalculator(trades, initial_capital=10000.0)
        
        longest_win, longest_loss = calculator.calculate_streaks()
        
        assert longest_win == 3
        assert longest_loss == 4
    
    def test_calculate_streaks_no_trades(self):
        """测试无交易的连胜连亏"""
        trades = []
        calculator = MetricsCalculator(trades, initial_capital=10000.0)
        
        longest_win, longest_loss = calculator.calculate_streaks()
        
        assert longest_win == 0
        assert longest_loss == 0
    
    def test_calculate_all_metrics(self):
        """测试计算所有指标"""
        trades = [
            create_trade_record(1, 1000.0),
            create_trade_record(2, -500.0),
            create_trade_record(3, 800.0),
        ]
        calculator = MetricsCalculator(trades, initial_capital=10000.0)
        
        # 创建权益曲线和收益率序列
        equity_curve = pd.Series([10000, 11000, 10500, 11300])
        returns = pd.Series([0.1, -0.045, 0.076])
        
        metrics = calculator.calculate_all_metrics(equity_curve, returns)
        
        # 验证所有字段都被正确填充
        assert metrics.initial_capital == 10000.0
        assert metrics.final_capital == 11300.0
        assert metrics.total_return == 1300.0
        assert metrics.total_return_pct == pytest.approx(0.13, rel=1e-6)
        assert metrics.total_trades == 3
        assert metrics.winning_trades == 2
        assert metrics.losing_trades == 1
        assert metrics.win_rate == pytest.approx(2/3, rel=1e-6)
        assert metrics.profit_factor > 0
        assert metrics.sharpe_ratio != 0
        assert metrics.max_drawdown >= 0
        assert metrics.max_drawdown_pct >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
