#!/usr/bin/env python3
"""
测试杠杆功能
验证合约交易的杠杆计算是否正确
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.backtest.models import StrategyConfig, EntryConditions, ExitConditions, IndicatorCondition, ComparisonOperator
from backend.backtest.engine import BacktestEngine
import pandas as pd
from datetime import datetime


def test_leverage_calculation():
    """测试杠杆计算"""
    print("=" * 60)
    print("测试杠杆功能")
    print("=" * 60)
    print()
    
    # 测试场景：2000本金，5倍杠杆，10000仓位
    initial_capital = 2000.0
    leverage = 5.0
    position_size_value = 10000.0  # 实际仓位
    
    print(f"测试参数：")
    print(f"  初始本金: {initial_capital} USDT")
    print(f"  杠杆倍数: {leverage}x")
    print(f"  目标仓位: {position_size_value} USDT")
    print(f"  预期保证金: {position_size_value / leverage} USDT")
    print()
    
    # 创建简单的策略配置
    strategy = StrategyConfig(
        name="杠杆测试策略",
        description="测试5倍杠杆",
        timeframe="1d",
        position_direction="long",
        position_size_type="amount",  # 固定金额
        position_size_value=position_size_value,  # 10000 USDT仓位
        initial_capital=initial_capital,  # 2000 USDT本金
        leverage=leverage,  # 5倍杠杆
        entry_conditions=EntryConditions(
            conditions=[
                IndicatorCondition(
                    indicator="RSI14",
                    operator=ComparisonOperator.LT,
                    value=50.0
                )
            ]
        ),
        exit_conditions=ExitConditions(
            indicator_conditions=[],
            take_profit_pct=10.0,
            stop_loss_pct=5.0
        )
    )
    
    # 创建测试数据
    test_data = pd.DataFrame([
        {
            'timestamp': datetime(2024, 1, 1),
            'open': 50000.0,
            'high': 51000.0,
            'low': 49000.0,
            'close': 50000.0,
            'volume': 1000.0,
            'RSI14': 30.0,  # 触发开仓条件
            'EMA7': 50000.0,
            'EMA25': 49000.0
        },
        {
            'timestamp': datetime(2024, 1, 2),
            'open': 50000.0,
            'high': 56000.0,  # 价格上涨12%
            'low': 49500.0,
            'close': 55000.0,  # 触发止盈
            'volume': 1200.0,
            'RSI14': 70.0,
            'EMA7': 52000.0,
            'EMA25': 50000.0
        }
    ])
    
    # 运行回测
    engine = BacktestEngine(strategy, test_data)
    result = engine.run()
    
    print("回测结果：")
    print(f"  交易数量: {len(result.trades)}")
    
    if len(result.trades) > 0:
        trade = result.trades[0]
        print()
        print("第一笔交易详情：")
        print(f"  开仓价格: {trade.entry_price:.2f} USDT")
        print(f"  平仓价格: {trade.exit_price:.2f} USDT")
        print(f"  持仓数量: {trade.position_size:.6f} BTC")
        print(f"  使用保证金: {trade.entry_capital:.2f} USDT")
        print(f"  实际仓位价值: {trade.position_size * trade.entry_price:.2f} USDT")
        print(f"  盈亏金额: {trade.profit_loss:.2f} USDT")
        print(f"  盈亏百分比: {trade.profit_loss_pct:.2f}%")
        print(f"  平仓原因: {trade.exit_reason}")
        print()
        
        # 验证计算
        expected_margin = position_size_value / leverage
        expected_position_size = position_size_value / trade.entry_price
        expected_pnl = (trade.exit_price - trade.entry_price) * expected_position_size
        expected_pnl_pct = (expected_pnl / expected_margin) * 100
        
        print("验证结果：")
        print(f"  ✓ 保证金计算: {trade.entry_capital:.2f} == {expected_margin:.2f} ? {abs(trade.entry_capital - expected_margin) < 0.01}")
        print(f"  ✓ 持仓数量计算: {trade.position_size:.6f} == {expected_position_size:.6f} ? {abs(trade.position_size - expected_position_size) < 0.000001}")
        print(f"  ✓ 盈亏金额计算: {trade.profit_loss:.2f} == {expected_pnl:.2f} ? {abs(trade.profit_loss - expected_pnl) < 0.01}")
        print(f"  ✓ 盈亏百分比计算: {trade.profit_loss_pct:.2f}% == {expected_pnl_pct:.2f}% ? {abs(trade.profit_loss_pct - expected_pnl_pct) < 0.01}")
        print()
        
        # 计算实际收益率
        actual_return_on_margin = (trade.profit_loss / trade.entry_capital) * 100
        print(f"实际收益率（基于保证金）: {actual_return_on_margin:.2f}%")
        print(f"价格涨幅: {((trade.exit_price - trade.entry_price) / trade.entry_price) * 100:.2f}%")
        print(f"杠杆放大效果: {actual_return_on_margin / ((trade.exit_price - trade.entry_price) / trade.entry_price * 100):.2f}x")
    
    print()
    print("性能指标：")
    print(f"  初始资金: {result.metrics.initial_capital:.2f} USDT")
    print(f"  最终资金: {result.metrics.final_capital:.2f} USDT")
    print(f"  总收益: {result.metrics.total_return:.2f} USDT")
    print(f"  总收益率: {result.metrics.total_return_pct:.2f}%")
    print(f"  胜率: {result.metrics.win_rate:.2%}")
    print()
    print("=" * 60)


if __name__ == "__main__":
    test_leverage_calculation()
