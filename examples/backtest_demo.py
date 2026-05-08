"""
回测系统演示脚本

演示如何使用回测系统的核心数据模型
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.backtest.models import (
    StrategyConfig, EntryConditions, ExitConditions,
    IndicatorCondition, ComparisonOperator, LogicOperator
)
from backend.backtest.logger import get_logger
from backend.backtest.config import config


def main():
    """主函数"""
    # 获取日志记录器
    logger = get_logger("backtest_demo")
    logger.info("=== BTC回测系统演示 ===")
    
    # 1. 创建开仓条件：EMA7 > EMA25 AND RSI14 < 70
    logger.info("\n1. 创建开仓条件")
    entry_conditions = EntryConditions(
        conditions=[
            IndicatorCondition(
                indicator="EMA7",
                operator=ComparisonOperator.GT,
                value=0,  # 将与EMA25比较
                timeframe="1d"
            ),
            IndicatorCondition(
                indicator="RSI14",
                operator=ComparisonOperator.LT,
                value=70,
                timeframe="1d"
            )
        ],
        logic_operator=LogicOperator.AND
    )
    logger.info(f"开仓条件: EMA7 > EMA25 AND RSI14 < 70")
    
    # 2. 创建平仓条件：止盈10%或止损5%
    logger.info("\n2. 创建平仓条件")
    exit_conditions = ExitConditions(
        indicator_conditions=[],
        take_profit_pct=0.10,
        stop_loss_pct=0.05,
        logic_operator=LogicOperator.OR
    )
    logger.info(f"平仓条件: 止盈10% OR 止损5%")
    
    # 3. 创建策略配置
    logger.info("\n3. 创建策略配置")
    strategy = StrategyConfig(
        name="EMA Golden Cross",
        description="EMA7上穿EMA25时做多，止盈10%，止损5%",
        timeframe="1d",
        position_direction="long",
        position_size_type="percentage",
        position_size_value=0.5,  # 50%资金
        entry_conditions=entry_conditions,
        exit_conditions=exit_conditions,
        initial_capital=100000.0
    )
    logger.info(f"策略名称: {strategy.name}")
    logger.info(f"策略描述: {strategy.description}")
    logger.info(f"时间周期: {strategy.timeframe}")
    logger.info(f"持仓方向: {strategy.position_direction}")
    logger.info(f"持仓大小: {strategy.position_size_value * 100}% 资金")
    logger.info(f"初始资金: ${strategy.initial_capital:,.2f}")
    
    # 4. 序列化为JSON
    logger.info("\n4. 序列化策略配置为JSON")
    strategy_json = strategy.to_json()
    logger.info(f"JSON长度: {len(strategy_json)} 字符")
    print("\n策略配置JSON:")
    print(strategy_json)
    
    # 5. 从JSON反序列化
    logger.info("\n5. 从JSON反序列化策略配置")
    loaded_strategy = StrategyConfig.from_json(strategy_json)
    logger.info(f"加载的策略名称: {loaded_strategy.name}")
    logger.info(f"验证: 策略配置相同 = {loaded_strategy.name == strategy.name}")
    
    # 6. 显示配置信息
    logger.info("\n6. 显示系统配置")
    logger.info(f"可用指标: {', '.join(config.get_available_indicators())}")
    logger.info(f"可用时间周期: {', '.join(config.get_available_timeframes())}")
    logger.info(f"默认初始资金: ${config.get('backtest.default_initial_capital', 100000):,.2f}")
    logger.info(f"最大并发回测数: {config.get('backtest.max_concurrent_backtests', 5)}")
    
    logger.info("\n=== 演示完成 ===")


if __name__ == "__main__":
    main()
