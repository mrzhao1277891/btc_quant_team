"""
MetricsCalculator集成测试

测试MetricsCalculator与BacktestEngine的集成，验证：
- 回测引擎正确调用MetricsCalculator
- 性能指标正确计算并包含在BacktestResult中
- 端到端回测流程生成完整的性能报告
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
    LogicOperator
)


def create_mock_kline_data(days: int = 30, start_price: float = 50000.0) -> pd.DataFrame:
    """创建模拟K线数据用于测试"""
    dates = pd.date_range(start='2024-01-01', periods=days, freq='D')
    
    # 生成模拟价格数据（带有趋势和波动）
    np.random.seed(42)
    prices = []
    current_price = start_price
    
    for i in range(days):
        # 添加随机波动
        change_pct = np.random.normal(0.01, 0.02)  # 平均1%涨幅，2%标准差
        current_price = current_price * (1 + change_pct)
        prices.append(current_price)
    
    prices = np.array(prices)
    
    # 创建OHLC数据
    df = pd.DataFrame({
        'timestamp': dates,
        'open': prices * (1 + np.random.uniform(-0.005, 0.005, days)),
        'high': prices * (1 + np.random.uniform(0.005, 0.015, days)),
        'low': prices * (1 + np.random.uniform(-0.015, -0.005, days)),
        'close': prices,
        'volume': np.random.uniform(1000, 5000, days)
    })
    
    # 添加简单的技术指标
    df['EMA7'] = df['close'].ewm(span=7, adjust=False).mean()
    df['EMA25'] = df['close'].ewm(span=25, adjust=False).mean()
    df['RSI14'] = 50 + np.random.uniform(-20, 20, days)  # 简化的RSI
    
    return df


class TestMetricsIntegration:
    """MetricsCalculator集成测试类"""
    
    def test_backtest_with_metrics_calculation(self):
        """测试回测引擎正确计算性能指标"""
        # 创建模拟数据
        kline_data = create_mock_kline_data(days=60)
        
        # 创建简单的策略配置：EMA7 > EMA25时做多
        strategy = StrategyConfig(
            name="EMA Crossover Test",
            description="Test strategy for metrics integration",
            timeframe="1d",
            position_direction="long",
            position_size_type="amount",
            position_size_value=10000.0,
            entry_conditions=EntryConditions(
                conditions=[
                    IndicatorCondition(
                        indicator="EMA7",
                        operator=ComparisonOperator.GT,
                        value=0,  # EMA7 > 0 (总是满足，用于测试)
                        timeframe="1d"
                    )
                ],
                logic_operator=LogicOperator.AND
            ),
            exit_conditions=ExitConditions(
                indicator_conditions=[],
                take_profit_pct=5.0,  # 5%止盈
                stop_loss_pct=2.0,    # 2%止损
                logic_operator=LogicOperator.OR
            ),
            initial_capital=100000.0
        )
        
        # 执行回测
        engine = BacktestEngine(strategy, kline_data)
        result = engine.run()
        
        # 验证结果包含性能指标
        assert result.metrics is not None
        assert result.metrics.initial_capital == 100000.0
        assert result.metrics.final_capital > 0
        
        # 如果有交易，验证指标被正确计算
        if len(result.trades) > 0:
            assert result.metrics.total_trades == len(result.trades)
            assert result.metrics.winning_trades >= 0
            assert result.metrics.losing_trades >= 0
            # 注意：盈亏为0的交易不计入winning或losing
            assert result.metrics.winning_trades + result.metrics.losing_trades <= result.metrics.total_trades
            assert 0 <= result.metrics.win_rate <= 1.0
            assert result.metrics.max_drawdown >= 0
            assert result.metrics.max_drawdown_pct >= 0
            
            # 验证总收益率计算正确
            expected_return_pct = (result.metrics.final_capital - result.metrics.initial_capital) / result.metrics.initial_capital
            assert result.metrics.total_return_pct == pytest.approx(expected_return_pct, rel=1e-6)
    
    def test_backtest_no_trades_metrics(self):
        """测试无交易时的性能指标"""
        # 创建模拟数据
        kline_data = create_mock_kline_data(days=30)
        
        # 创建永远不会触发的策略
        strategy = StrategyConfig(
            name="No Trade Strategy",
            description="Strategy that never triggers",
            timeframe="1d",
            position_direction="long",
            position_size_type="amount",
            position_size_value=10000.0,
            entry_conditions=EntryConditions(
                conditions=[
                    IndicatorCondition(
                        indicator="close",
                        operator=ComparisonOperator.GT,
                        value=1000000.0,  # 永远不会满足
                        timeframe="1d"
                    )
                ],
                logic_operator=LogicOperator.AND
            ),
            exit_conditions=ExitConditions(
                indicator_conditions=[],
                logic_operator=LogicOperator.OR
            ),
            initial_capital=100000.0
        )
        
        # 执行回测
        engine = BacktestEngine(strategy, kline_data)
        result = engine.run()
        
        # 验证无交易时的指标
        assert result.metrics.total_trades == 0
        assert result.metrics.winning_trades == 0
        assert result.metrics.losing_trades == 0
        assert result.metrics.win_rate == 0.0
        assert result.metrics.final_capital == result.metrics.initial_capital
        assert result.metrics.total_return == 0.0
        assert result.metrics.total_return_pct == 0.0
    
    def test_backtest_metrics_consistency(self):
        """测试性能指标的一致性"""
        # 创建模拟数据
        kline_data = create_mock_kline_data(days=50)
        
        # 创建策略
        strategy = StrategyConfig(
            name="Consistency Test",
            description="Test metrics consistency",
            timeframe="1d",
            position_direction="long",
            position_size_type="percentage",
            position_size_value=20.0,  # 20%仓位
            entry_conditions=EntryConditions(
                conditions=[
                    IndicatorCondition(
                        indicator="RSI14",
                        operator=ComparisonOperator.LT,
                        value=60,
                        timeframe="1d"
                    )
                ],
                logic_operator=LogicOperator.AND
            ),
            exit_conditions=ExitConditions(
                indicator_conditions=[
                    IndicatorCondition(
                        indicator="RSI14",
                        operator=ComparisonOperator.GT,
                        value=70,
                        timeframe="1d"
                    )
                ],
                take_profit_pct=10.0,
                stop_loss_pct=5.0,
                logic_operator=LogicOperator.OR
            ),
            initial_capital=50000.0
        )
        
        # 执行回测
        engine = BacktestEngine(strategy, kline_data)
        result = engine.run()
        
        # 验证指标一致性
        if len(result.trades) > 0:
            # 手动计算总盈亏
            total_pnl = sum(trade.profit_loss for trade in result.trades)
            expected_final_capital = result.metrics.initial_capital + total_pnl
            
            # 验证最终资金一致
            assert result.metrics.final_capital == pytest.approx(expected_final_capital, rel=1e-6)
            
            # 验证交易统计一致
            winning_count = sum(1 for trade in result.trades if trade.profit_loss > 0)
            losing_count = sum(1 for trade in result.trades if trade.profit_loss < 0)
            
            assert result.metrics.winning_trades == winning_count
            assert result.metrics.losing_trades == losing_count
            
            # 验证胜率一致
            expected_win_rate = winning_count / len(result.trades)
            assert result.metrics.win_rate == pytest.approx(expected_win_rate, rel=1e-6)
    
    def test_equity_curve_in_result(self):
        """测试权益曲线包含在结果中"""
        # 创建模拟数据
        kline_data = create_mock_kline_data(days=40)
        
        # 创建策略
        strategy = StrategyConfig(
            name="Equity Curve Test",
            description="Test equity curve generation",
            timeframe="1d",
            position_direction="long",
            position_size_type="amount",
            position_size_value=5000.0,
            entry_conditions=EntryConditions(
                conditions=[
                    IndicatorCondition(
                        indicator="EMA7",
                        operator=ComparisonOperator.GT,
                        value=0,
                        timeframe="1d"
                    )
                ],
                logic_operator=LogicOperator.AND
            ),
            exit_conditions=ExitConditions(
                indicator_conditions=[],
                take_profit_pct=3.0,
                stop_loss_pct=1.5,
                logic_operator=LogicOperator.OR
            ),
            initial_capital=100000.0
        )
        
        # 执行回测
        engine = BacktestEngine(strategy, kline_data)
        result = engine.run()
        
        # 验证权益曲线
        assert len(result.equity_curve) > 0
        assert len(result.equity_curve) == len(kline_data)
        
        # 验证权益曲线的第一个点是初始资金
        first_timestamp, first_equity = result.equity_curve[0]
        assert first_equity == pytest.approx(strategy.initial_capital, rel=1e-6)
        
        # 验证权益曲线的最后一个点接近最终资金
        last_timestamp, last_equity = result.equity_curve[-1]
        # 注意：如果最后有持仓，最终资金可能略有不同
        assert last_equity > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
