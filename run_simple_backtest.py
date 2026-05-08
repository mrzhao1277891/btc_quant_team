#!/usr/bin/env python3
"""
简单回测运行脚本
直接使用回测引擎运行策略，无需 Web UI
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.backtest.models import StrategyConfig
from backend.backtest.engine import BacktestEngine
from backend.database import DatabaseConnector
from backend.indicators import IndicatorCalculator
from backend.backtest.logger import get_logger

logger = get_logger("simple_backtest")


def run_backtest():
    """运行简单的回测示例"""
    
    print("=" * 60)
    print("🚀 BTC 回测系统 - 简单示例")
    print("=" * 60)
    print()
    
    # 1. 配置策略
    print("📋 配置策略...")
    strategy_config = {
        "name": "EMA金叉策略",
        "description": "EMA7上穿EMA25时做多",
        "timeframe": "1d",
        "position_direction": "long",
        "position_size_type": "percentage",
        "position_size_value": 0.1,  # 10% 资金
        "initial_capital": 10000.0,
        "entry_conditions": {
            "conditions": [
                {
                    "indicator": "ema7",
                    "operator": ">",
                    "value": "ema25",
                    "timeframe": "1d"
                },
                {
                    "indicator": "rsi14",
                    "operator": "<",
                    "value": 70,
                    "timeframe": "1d"
                }
            ],
            "logic_operator": "AND"
        },
        "exit_conditions": {
            "indicator_conditions": [
                {
                    "indicator": "ema7",
                    "operator": "<",
                    "value": "ema25",
                    "timeframe": "1d"
                }
            ],
            "take_profit_pct": 0.10,  # 10% 止盈
            "stop_loss_pct": 0.05,    # 5% 止损
            "logic_operator": "OR"
        }
    }
    
    print(f"✅ 策略名称: {strategy_config['name']}")
    print(f"✅ 时间周期: {strategy_config['timeframe']}")
    print(f"✅ 初始资金: ${strategy_config['initial_capital']:,.2f}")
    print()
    
    # 2. 连接数据库获取数据
    print("📊 获取历史数据...")
    try:
        db = DatabaseConnector()
        
        # 获取最近 120 天的数据
        end_date = datetime.now()
        start_date = end_date - timedelta(days=120)
        
        klines = db.fetch_klines(
            symbol="BTCUSDT",
            timeframe="1d",
            start_time=int(start_date.timestamp() * 1000),
            end_time=int(end_date.timestamp() * 1000)
        )
        
        if not klines:
            print("❌ 没有获取到数据")
            return
        
        print(f"✅ 获取到 {len(klines)} 条K线数据")
        print(f"✅ 日期范围: {start_date.date()} 到 {end_date.date()}")
        print()
        
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        print("\n请检查:")
        print("  1. MySQL 是否运行: mysql.server status")
        print("  2. 数据库配置: config/backtest.yaml")
        return
    
    # 3. 计算技术指标
    print("📈 计算技术指标...")
    try:
        calculator = IndicatorCalculator()
        klines_with_indicators = calculator.calculate_all_indicators(klines)
        print(f"✅ 已计算 EMA、RSI、MACD、布林带、ATR")
        print()
    except Exception as e:
        print(f"❌ 指标计算失败: {e}")
        return
    
    # 4. 创建策略对象
    print("⚙️  初始化回测引擎...")
    try:
        strategy = StrategyConfig.from_dict(strategy_config)
        engine = BacktestEngine(strategy, klines_with_indicators)
        print("✅ 回测引擎已就绪")
        print()
    except Exception as e:
        print(f"❌ 引擎初始化失败: {e}")
        return
    
    # 5. 运行回测
    print("🔄 运行回测...")
    print("-" * 60)
    try:
        result = engine.run()
        print("-" * 60)
        print("✅ 回测完成！")
        print()
    except Exception as e:
        print(f"❌ 回测失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 6. 显示结果
    print("=" * 60)
    print("📊 回测结果")
    print("=" * 60)
    print()
    
    metrics = result.performance_metrics
    
    print("💰 收益指标:")
    print(f"  初始资金:     ${result.initial_capital:,.2f}")
    print(f"  最终资金:     ${result.final_capital:,.2f}")
    print(f"  总收益:       ${metrics.total_return:,.2f}")
    print(f"  收益率:       {metrics.total_return_pct:.2f}%")
    print()
    
    print("📈 交易统计:")
    print(f"  总交易次数:   {metrics.total_trades}")
    print(f"  盈利次数:     {metrics.winning_trades}")
    print(f"  亏损次数:     {metrics.losing_trades}")
    print(f"  胜率:         {metrics.win_rate:.2f}%")
    print()
    
    print("📉 风险指标:")
    print(f"  最大回撤:     {metrics.max_drawdown:.2f}%")
    print(f"  夏普比率:     {metrics.sharpe_ratio:.2f}")
    print(f"  盈亏因子:     {metrics.profit_factor:.2f}")
    print()
    
    if metrics.avg_profit > 0:
        print("💵 盈亏分析:")
        print(f"  平均盈利:     ${metrics.avg_profit:,.2f}")
        print(f"  平均亏损:     ${metrics.avg_loss:,.2f}")
        print(f"  最长连胜:     {metrics.longest_win_streak} 次")
        print(f"  最长连亏:     {metrics.longest_loss_streak} 次")
        print()
    
    # 7. 显示交易记录
    if result.trades:
        print("=" * 60)
        print("📝 交易记录（最近 5 笔）")
        print("=" * 60)
        print()
        
        for i, trade in enumerate(result.trades[-5:], 1):
            print(f"交易 #{len(result.trades) - 5 + i}:")
            print(f"  开仓时间:     {trade.entry_time}")
            print(f"  开仓价格:     ${trade.entry_price:,.2f}")
            print(f"  平仓时间:     {trade.exit_time}")
            print(f"  平仓价格:     ${trade.exit_price:,.2f}")
            print(f"  持仓方向:     {trade.position_side}")
            print(f"  持仓大小:     {trade.position_size:.4f} BTC")
            print(f"  盈亏:         ${trade.profit_loss:,.2f} ({trade.profit_loss_pct:.2f}%)")
            print(f"  平仓原因:     {trade.exit_reason}")
            print()
    else:
        print("⚠️  没有产生任何交易")
        print("提示: 可能需要调整策略条件或扩大回测日期范围")
        print()
    
    print("=" * 60)
    print("✅ 回测完成！")
    print("=" * 60)


if __name__ == "__main__":
    try:
        run_backtest()
    except KeyboardInterrupt:
        print("\n\n⚠️  回测已取消")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
