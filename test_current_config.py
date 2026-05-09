#!/usr/bin/env python3
"""
测试当前配置是否正确
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.backtest.models import StrategyConfig, EntryConditions, ExitConditions, IndicatorCondition, ComparisonOperator
from backend.backtest.engine import BacktestEngine
import pandas as pd
from datetime import datetime

# 模拟前端发送的配置
config_dict = {
    "name": "测试策略",
    "description": "测试",
    "timeframe": "1d",
    "position_direction": "long",
    "position_size_type": "amount",
    "position_size_value": 10000.0,  # 持仓大小 10000
    "initial_capital": 2000.0,  # 初始资金 2000
    "leverage": 5.0,  # 杠杆 5倍
    "entry_conditions": {
        "conditions": [
            {
                "indicator": "RSI14",
                "operator": "<",
                "value": 50.0
            }
        ],
        "logic_operator": "AND"
    },
    "exit_conditions": {
        "indicator_conditions": [],
        "take_profit_pct": 0.1,
        "stop_loss_pct": 0.05,
        "logic_operator": "OR"
    }
}

print("=" * 60)
print("测试配置")
print("=" * 60)
print(f"初始资金: {config_dict['initial_capital']}")
print(f"持仓大小: {config_dict['position_size_value']}")
print(f"杠杆倍数: {config_dict['leverage']}")
print(f"预期保证金: {config_dict['position_size_value'] / config_dict['leverage']}")
print()

# 创建策略配置
strategy = StrategyConfig.from_dict(config_dict)

print("策略配置对象:")
print(f"  position_size_type: {strategy.position_size_type}")
print(f"  position_size_value: {strategy.position_size_value}")
print(f"  initial_capital: {strategy.initial_capital}")
print(f"  leverage: {strategy.leverage}")
print()

# 创建测试数据
test_data = pd.DataFrame([
    {
        'timestamp': datetime(2024, 1, 1),
        'open': 50000.0,
        'high': 51000.0,
        'low': 49000.0,
        'close': 50000.0,
        'volume': 1000.0,
        'RSI14': 30.0,
        'EMA7': 50000.0,
        'EMA25': 49000.0
    },
    {
        'timestamp': datetime(2024, 1, 2),
        'open': 50000.0,
        'high': 56000.0,
        'low': 49500.0,
        'close': 55000.0,
        'volume': 1200.0,
        'RSI14': 70.0,
        'EMA7': 52000.0,
        'EMA25': 50000.0
    }
])

# 运行回测
engine = BacktestEngine(strategy, test_data)
result = engine.run()

print("回测结果:")
print(f"  交易数量: {len(result.trades)}")
print(f"  最终资金: {result.metrics.final_capital}")

if len(result.trades) > 0:
    print("\n✅ 成功！有交易记录")
    trade = result.trades[0]
    print(f"  使用保证金: {trade.entry_capital}")
    print(f"  持仓数量: {trade.position_size}")
    print(f"  盈亏: {trade.profit_loss}")
else:
    print("\n❌ 失败！没有交易记录")
    print("请检查日志文件查看详细错误信息")

print("=" * 60)
