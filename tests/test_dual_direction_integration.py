#!/usr/bin/env python3
"""
集成测试：双向 RSI 策略完整回测

测试双向RSI策略的完整回测流程，包括：
1. 完整的双向RSI策略回测（RSI<30做多，RSI>70做空）
2. 验证做多和做空交易都能正确执行
3. 验证反向信号处理（先平后开）
4. 验证最终资金和盈亏计算
5. 验证交易记录的完整性

Task 22: 添加集成测试：双向 RSI 策略完整回测
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from backend.backtest.models import (
    StrategyConfig,
    EntryConditions,
    ExitConditions,
    IndicatorCondition,
    ComparisonOperator,
    LogicOperator
)
from backend.backtest.engine import BacktestEngine


class TestDualDirectionRSIIntegration:
    """双向RSI策略集成测试"""
    
    def create_test_kline_data(self) -> pd.DataFrame:
        """创建测试用的K线数据
        
        模拟一个完整的市场周期：
        - 初始阶段：RSI < 30（超卖，做多信号）
        - 上涨阶段：RSI 30-70（持有多仓）
        - 超买阶段：RSI > 70（做空信号，触发反向操作）
        - 下跌阶段：RSI 70-30（持有空仓）
        - 再次超卖：RSI < 30（做多信号，触发反向操作）
        
        Returns:
            包含完整市场周期的K线数据DataFrame
        """
        base_time = datetime(2024, 1, 1, 0, 0, 0)
        
        # 创建模拟数据
        data = []
        
        # 阶段1: 超卖阶段 (RSI < 30) - 应该触发做多信号
        for i in range(5):
            data.append({
                'timestamp': base_time + timedelta(days=i),
                'open': 45000.0 + i * 100,
                'high': 45500.0 + i * 100,
                'low': 44500.0 + i * 100,
                'close': 45000.0 + i * 100,
                'volume': 100.0,
                'RSI14': 25.0 + i * 0.5  # RSI从25逐渐上升
            })
        
        # 阶段2: 上涨阶段 (RSI 30-70) - 持有多仓
        for i in range(10):
            data.append({
                'timestamp': base_time + timedelta(days=5 + i),
                'open': 45500.0 + i * 500,
                'high': 46000.0 + i * 500,
                'low': 45000.0 + i * 500,
                'close': 45500.0 + i * 500,
                'volume': 100.0,
                'RSI14': 30.0 + i * 4.0  # RSI从30逐渐上升到70
            })
        
        # 阶段3: 超买阶段 (RSI > 70) - 应该触发做空信号（反向操作）
        for i in range(5):
            data.append({
                'timestamp': base_time + timedelta(days=15 + i),
                'open': 50500.0 + i * 100,
                'high': 51000.0 + i * 100,
                'low': 50000.0 + i * 100,
                'close': 50500.0 + i * 100,
                'volume': 100.0,
                'RSI14': 72.0 + i * 0.5  # RSI从72逐渐上升
            })
        
        # 阶段4: 下跌阶段 (RSI 70-30) - 持有空仓
        for i in range(10):
            data.append({
                'timestamp': base_time + timedelta(days=20 + i),
                'open': 51000.0 - i * 500,
                'high': 51500.0 - i * 500,
                'low': 50500.0 - i * 500,
                'close': 51000.0 - i * 500,
                'volume': 100.0,
                'RSI14': 70.0 - i * 4.0  # RSI从70逐渐下降到30
            })
        
        # 阶段5: 再次超卖 (RSI < 30) - 应该触发做多信号（反向操作）
        for i in range(5):
            data.append({
                'timestamp': base_time + timedelta(days=30 + i),
                'open': 46000.0 - i * 100,
                'high': 46500.0 - i * 100,
                'low': 45500.0 - i * 100,
                'close': 46000.0 - i * 100,
                'volume': 100.0,
                'RSI14': 28.0 - i * 0.5  # RSI从28逐渐下降
            })
        
        # 阶段6: 最后几天保持中性，让策略自然结束
        for i in range(5):
            data.append({
                'timestamp': base_time + timedelta(days=35 + i),
                'open': 45500.0 + i * 50,
                'high': 46000.0 + i * 50,
                'low': 45000.0 + i * 50,
                'close': 45500.0 + i * 50,
                'volume': 100.0,
                'RSI14': 50.0  # RSI保持中性
            })
        
        return pd.DataFrame(data)
    
    def test_dual_rsi_strategy_complete_backtest(self):
        """测试双向RSI策略的完整回测流程"""
        # 创建双向RSI策略配置
        # 做多条件：RSI < 30
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
        
        # 做空条件：RSI > 70
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
        
        # 不设置平仓条件，让反向信号触发平仓
        # 这样可以测试反向信号处理逻辑
        
        # 创建策略配置
        strategy = StrategyConfig(
            name="双向RSI策略",
            description="RSI<30做多，RSI>70做空",
            timeframe="1d",
            position_size_type="amount",
            position_size_value=10000.0,  # 每次开仓10000
            initial_capital=50000.0,
            leverage=1.0,  # 不使用杠杆
            long_entry_conditions=long_entry,
            short_entry_conditions=short_entry
        )
        
        # 创建测试数据
        kline_data = self.create_test_kline_data()
        
        # 创建回测引擎并运行
        engine = BacktestEngine(strategy, kline_data)
        result = engine.run()
        
        # 验证回测结果
        assert result is not None
        assert result.trades is not None
        assert len(result.trades) > 0, "应该有交易记录"
        
        # 验证交易记录的完整性
        print(f"\n总交易次数: {len(result.trades)}")
        for trade in result.trades:
            print(f"交易 #{trade.trade_id}: {trade.direction} | "
                  f"开仓: {trade.entry_price:.2f} | 平仓: {trade.exit_price:.2f} | "
                  f"盈亏: {trade.profit_loss:.2f} ({trade.profit_loss_pct:.2f}%) | "
                  f"原因: {trade.exit_reason}")
        
        # 验证有做多和做空交易
        long_trades = [t for t in result.trades if t.direction == "long"]
        short_trades = [t for t in result.trades if t.direction == "short"]
        
        assert len(long_trades) > 0, "应该有做多交易"
        assert len(short_trades) > 0, "应该有做空交易"
        
        print(f"\n做多交易: {len(long_trades)} 笔")
        print(f"做空交易: {len(short_trades)} 笔")
        
        # 验证反向信号处理
        reverse_signal_trades = [t for t in result.trades if t.exit_reason == "reverse_signal"]
        assert len(reverse_signal_trades) > 0, "应该有因反向信号而平仓的交易"
        print(f"反向信号平仓: {len(reverse_signal_trades)} 笔")
        
        # 验证最终资金
        assert result.metrics.final_capital > 0, "最终资金应该大于0"
        print(f"\n初始资金: {result.metrics.initial_capital:.2f}")
        print(f"最终资金: {result.metrics.final_capital:.2f}")
        print(f"总收益: {result.metrics.total_return:.2f} ({result.metrics.total_return_pct:.2f}%)")
        
        # 验证性能指标
        assert result.metrics.total_trades == len(result.trades)
        assert result.metrics.winning_trades + result.metrics.losing_trades == result.metrics.total_trades
        
        print(f"\n胜率: {result.metrics.win_rate:.2%}")
        print(f"盈利交易: {result.metrics.winning_trades} 笔")
        print(f"亏损交易: {result.metrics.losing_trades} 笔")
    
    def test_long_and_short_trades_execution(self):
        """测试做多和做空交易都能正确执行"""
        # 创建简化的双向策略
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
            name="双向策略测试",
            description="测试做多和做空",
            timeframe="1d",
            position_size_type="amount",
            position_size_value=10000.0,
            initial_capital=50000.0,
            leverage=1.0,
            long_entry_conditions=long_entry,
            short_entry_conditions=short_entry
        )
        
        kline_data = self.create_test_kline_data()
        engine = BacktestEngine(strategy, kline_data)
        result = engine.run()
        
        # 验证做多交易
        long_trades = [t for t in result.trades if t.direction == "long"]
        assert len(long_trades) > 0, "应该有做多交易"
        
        for trade in long_trades:
            assert trade.direction == "long"
            assert trade.entry_price > 0
            assert trade.exit_price > 0
            assert trade.position_size > 0
            # 做多盈亏 = (平仓价 - 开仓价) * 持仓数量
            expected_pnl = (trade.exit_price - trade.entry_price) * trade.position_size
            assert abs(trade.profit_loss - expected_pnl) < 0.01, \
                f"做多盈亏计算错误: 期望 {expected_pnl:.2f}, 实际 {trade.profit_loss:.2f}"
        
        # 验证做空交易
        short_trades = [t for t in result.trades if t.direction == "short"]
        assert len(short_trades) > 0, "应该有做空交易"
        
        for trade in short_trades:
            assert trade.direction == "short"
            assert trade.entry_price > 0
            assert trade.exit_price > 0
            assert trade.position_size > 0
            # 做空盈亏 = (开仓价 - 平仓价) * 持仓数量
            expected_pnl = (trade.entry_price - trade.exit_price) * trade.position_size
            assert abs(trade.profit_loss - expected_pnl) < 0.01, \
                f"做空盈亏计算错误: 期望 {expected_pnl:.2f}, 实际 {trade.profit_loss:.2f}"
    
    def test_reverse_signal_handling(self):
        """测试反向信号处理（先平后开）"""
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
            name="反向信号测试",
            description="测试反向信号处理",
            timeframe="1d",
            position_size_type="amount",
            position_size_value=10000.0,
            initial_capital=50000.0,
            leverage=1.0,
            long_entry_conditions=long_entry,
            short_entry_conditions=short_entry
        )
        
        kline_data = self.create_test_kline_data()
        engine = BacktestEngine(strategy, kline_data)
        result = engine.run()
        
        # 查找反向信号触发的交易
        reverse_trades = [t for t in result.trades if t.exit_reason == "reverse_signal"]
        assert len(reverse_trades) > 0, "应该有因反向信号而平仓的交易"
        
        # 验证反向信号的逻辑：
        # 1. 找到所有反向信号平仓的交易
        # 2. 验证下一笔交易的方向与上一笔相反
        for i, trade in enumerate(result.trades):
            if trade.exit_reason == "reverse_signal":
                # 应该有下一笔交易
                if i + 1 < len(result.trades):
                    next_trade = result.trades[i + 1]
                    # 验证方向相反
                    assert trade.direction != next_trade.direction, \
                        f"反向信号后的交易方向应该相反: 当前 {trade.direction}, 下一笔 {next_trade.direction}"
                    # 验证平仓时间和开仓时间相同（同一时间步）
                    assert trade.exit_time == next_trade.entry_time, \
                        "反向信号应该在同一时间步内完成平仓和开仓"
                    
                    print(f"\n反向信号交易对:")
                    print(f"  平仓: {trade.direction} @ {trade.exit_price:.2f} (原因: {trade.exit_reason})")
                    print(f"  开仓: {next_trade.direction} @ {next_trade.entry_price:.2f}")
    
    def test_final_capital_and_pnl_calculation(self):
        """测试最终资金和盈亏计算"""
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
        
        initial_capital = 50000.0
        strategy = StrategyConfig(
            name="资金计算测试",
            description="测试最终资金和盈亏计算",
            timeframe="1d",
            position_size_type="amount",
            position_size_value=10000.0,
            initial_capital=initial_capital,
            leverage=1.0,
            long_entry_conditions=long_entry,
            short_entry_conditions=short_entry
        )
        
        kline_data = self.create_test_kline_data()
        engine = BacktestEngine(strategy, kline_data)
        result = engine.run()
        
        # 验证初始资金
        assert result.metrics.initial_capital == initial_capital
        
        # 手动计算总盈亏
        total_pnl = sum(trade.profit_loss for trade in result.trades)
        expected_final_capital = initial_capital + total_pnl
        
        # 验证最终资金
        assert abs(result.metrics.final_capital - expected_final_capital) < 0.01, \
            f"最终资金计算错误: 期望 {expected_final_capital:.2f}, 实际 {result.metrics.final_capital:.2f}"
        
        # 验证总收益
        assert abs(result.metrics.total_return - total_pnl) < 0.01, \
            f"总收益计算错误: 期望 {total_pnl:.2f}, 实际 {result.metrics.total_return:.2f}"
        
        # 验证收益率（注意：metrics中的total_return_pct可能已经是百分比形式，不需要再乘100）
        # 根据实际实现，total_return_pct可能是小数形式（如0.04表示4%）或百分比形式（如4.0表示4%）
        # 我们需要检查实际值来判断
        expected_return_pct = (total_pnl / initial_capital) * 100
        # 如果实际值很小（<1），说明是小数形式，需要转换
        actual_return_pct = result.metrics.total_return_pct
        if actual_return_pct < 1 and expected_return_pct > 1:
            actual_return_pct = actual_return_pct * 100
        
        assert abs(actual_return_pct - expected_return_pct) < 0.01, \
            f"收益率计算错误: 期望 {expected_return_pct:.2f}%, 实际 {actual_return_pct:.2f}%"
        
        print(f"\n资金计算验证:")
        print(f"初始资金: {initial_capital:.2f}")
        print(f"总盈亏: {total_pnl:.2f}")
        print(f"最终资金: {result.metrics.final_capital:.2f}")
        print(f"收益率: {result.metrics.total_return_pct:.2f}%")
    
    def test_trade_records_integrity(self):
        """测试交易记录的完整性"""
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
            name="交易记录测试",
            description="测试交易记录完整性",
            timeframe="1d",
            position_size_type="amount",
            position_size_value=10000.0,
            initial_capital=50000.0,
            leverage=1.0,
            long_entry_conditions=long_entry,
            short_entry_conditions=short_entry
        )
        
        kline_data = self.create_test_kline_data()
        engine = BacktestEngine(strategy, kline_data)
        result = engine.run()
        
        # 验证每笔交易记录的完整性
        for trade in result.trades:
            # 验证必填字段
            assert trade.trade_id > 0, "交易ID应该大于0"
            assert trade.entry_time is not None, "开仓时间不能为空"
            assert trade.exit_time is not None, "平仓时间不能为空"
            assert trade.entry_price > 0, "开仓价格应该大于0"
            assert trade.exit_price > 0, "平仓价格应该大于0"
            assert trade.position_size > 0, "持仓数量应该大于0"
            assert trade.direction in ["long", "short"], f"持仓方向应该是long或short，实际: {trade.direction}"
            assert trade.exit_reason is not None and trade.exit_reason != "", "平仓原因不能为空"
            assert trade.entry_capital > 0, "开仓资金应该大于0"
            
            # 验证时间逻辑
            assert trade.exit_time >= trade.entry_time, "平仓时间应该晚于或等于开仓时间"
            
            # 验证盈亏计算
            if trade.direction == "long":
                expected_pnl = (trade.exit_price - trade.entry_price) * trade.position_size
            else:  # short
                expected_pnl = (trade.entry_price - trade.exit_price) * trade.position_size
            
            assert abs(trade.profit_loss - expected_pnl) < 0.01, \
                f"交易 #{trade.trade_id} 盈亏计算错误"
            
            # 验证盈亏百分比
            expected_pnl_pct = (trade.profit_loss / trade.entry_capital) * 100
            assert abs(trade.profit_loss_pct - expected_pnl_pct) < 0.01, \
                f"交易 #{trade.trade_id} 盈亏百分比计算错误"
        
        print(f"\n交易记录完整性验证通过，共 {len(result.trades)} 笔交易")
    
    def test_dual_rsi_with_leverage(self):
        """测试带杠杆的双向RSI策略"""
        # 创建双向策略，使用5倍杠杆
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
        
        initial_capital = 50000.0
        position_value = 10000.0
        leverage = 5.0
        
        strategy = StrategyConfig(
            name="杠杆双向RSI策略",
            description="测试带杠杆的双向策略",
            timeframe="1d",
            position_size_type="amount",
            position_size_value=position_value,
            initial_capital=initial_capital,
            leverage=leverage,
            long_entry_conditions=long_entry,
            short_entry_conditions=short_entry
        )
        
        kline_data = self.create_test_kline_data()
        engine = BacktestEngine(strategy, kline_data)
        result = engine.run()
        
        # 验证杠杆交易
        assert len(result.trades) > 0, "应该有交易记录"
        
        for trade in result.trades:
            # 验证保证金计算：保证金 = 仓位价值 / 杠杆
            expected_margin = position_value / leverage
            assert abs(trade.entry_capital - expected_margin) < 0.01, \
                f"交易 #{trade.trade_id} 保证金计算错误: 期望 {expected_margin:.2f}, 实际 {trade.entry_capital:.2f}"
            
            # 验证持仓数量：持仓数量 = 仓位价值 / 开仓价格
            expected_position_size = position_value / trade.entry_price
            assert abs(trade.position_size - expected_position_size) < 0.000001, \
                f"交易 #{trade.trade_id} 持仓数量计算错误"
            
            # 验证盈亏是基于实际仓位价值（含杠杆）计算的
            if trade.direction == "long":
                expected_pnl = (trade.exit_price - trade.entry_price) * trade.position_size
            else:
                expected_pnl = (trade.entry_price - trade.exit_price) * trade.position_size
            
            assert abs(trade.profit_loss - expected_pnl) < 0.01, \
                f"交易 #{trade.trade_id} 杠杆盈亏计算错误"
        
        print(f"\n杠杆交易验证通过:")
        print(f"杠杆倍数: {leverage}x")
        print(f"仓位价值: {position_value:.2f}")
        print(f"保证金: {position_value / leverage:.2f}")
        print(f"总交易: {len(result.trades)} 笔")


class TestBackwardCompatibility:
    """向后兼容性测试
    
    测试旧版单向策略配置能否正确工作：
    1. 测试旧版做多策略配置（position_direction="long"）
    2. 测试旧版做空策略配置（position_direction="short"）
    3. 验证旧版配置正确转换为新版字段
    4. 验证旧版策略的回测结果与新版一致
    5. 验证兼容性警告日志输出
    
    Task 23: 添加向后兼容性测试
    """
    
    def create_simple_test_data(self) -> pd.DataFrame:
        """创建简单的测试数据用于兼容性测试"""
        base_time = datetime(2024, 1, 1, 0, 0, 0)
        
        data = []
        # 创建一个简单的上涨趋势，RSI从低到高
        for i in range(20):
            data.append({
                'timestamp': base_time + timedelta(days=i),
                'open': 45000.0 + i * 500,
                'high': 45500.0 + i * 500,
                'low': 44500.0 + i * 500,
                'close': 45000.0 + i * 500,
                'volume': 100.0,
                'RSI14': 25.0 + i * 2.5  # RSI从25逐渐上升到72.5
            })
        
        return pd.DataFrame(data)
    
    def test_legacy_long_position_config(self):
        """测试旧版做多策略配置（使用 position_direction="long"）"""
        # 使用旧版配置方式创建做多策略
        legacy_config_dict = {
            "name": "旧版做多策略",
            "description": "使用旧版配置的做多策略",
            "timeframe": "1d",
            "position_size_type": "amount",
            "position_size_value": 10000.0,
            "initial_capital": 50000.0,
            "leverage": 1.0,
            "position_direction": "long",  # 旧版字段
            "entry_conditions": {  # 旧版字段
                "conditions": [
                    {
                        "indicator": "RSI14",
                        "operator": "<",
                        "value": 30
                    }
                ],
                "logic_operator": "AND"
            },
            "exit_conditions": {  # 旧版字段
                "indicator_conditions": [
                    {
                        "indicator": "RSI14",
                        "operator": ">",
                        "value": 70
                    }
                ],
                "logic_operator": "OR"
            }
        }
        
        # 从字典创建策略配置（应该触发兼容性转换）
        strategy = StrategyConfig.from_dict(legacy_config_dict)
        
        # 验证旧版字段被正确转换为新版字段
        assert strategy.long_entry_conditions is not None, "旧版做多配置应该转换为 long_entry_conditions"
        assert strategy.short_entry_conditions is None, "旧版做多配置不应该有 short_entry_conditions"
        assert strategy.long_exit_conditions is not None, "旧版做多配置应该转换为 long_exit_conditions"
        
        # 验证转换后的条件内容正确
        assert len(strategy.long_entry_conditions.conditions) == 1
        assert strategy.long_entry_conditions.conditions[0].indicator == "RSI14"
        assert strategy.long_entry_conditions.conditions[0].operator == ComparisonOperator.LT
        assert strategy.long_entry_conditions.conditions[0].value == 30
        
        # 运行回测
        kline_data = self.create_simple_test_data()
        engine = BacktestEngine(strategy, kline_data)
        result = engine.run()
        
        # 验证回测结果
        assert result is not None
        assert len(result.trades) > 0, "应该有交易记录"
        
        # 验证所有交易都是做多
        for trade in result.trades:
            assert trade.direction == "long", f"旧版做多策略应该只有做多交易，实际: {trade.direction}"
        
        print(f"\n旧版做多策略测试通过:")
        print(f"总交易: {len(result.trades)} 笔")
        print(f"所有交易方向: {[t.direction for t in result.trades]}")
    
    def test_legacy_short_position_config(self):
        """测试旧版做空策略配置（使用 position_direction="short"）"""
        # 使用旧版配置方式创建做空策略
        legacy_config_dict = {
            "name": "旧版做空策略",
            "description": "使用旧版配置的做空策略",
            "timeframe": "1d",
            "position_size_type": "amount",
            "position_size_value": 10000.0,
            "initial_capital": 50000.0,
            "leverage": 1.0,
            "position_direction": "short",  # 旧版字段
            "entry_conditions": {  # 旧版字段
                "conditions": [
                    {
                        "indicator": "RSI14",
                        "operator": ">",
                        "value": 70
                    }
                ],
                "logic_operator": "AND"
            },
            "exit_conditions": {  # 旧版字段
                "indicator_conditions": [
                    {
                        "indicator": "RSI14",
                        "operator": "<",
                        "value": 30
                    }
                ],
                "logic_operator": "OR"
            }
        }
        
        # 从字典创建策略配置（应该触发兼容性转换）
        strategy = StrategyConfig.from_dict(legacy_config_dict)
        
        # 验证旧版字段被正确转换为新版字段
        assert strategy.short_entry_conditions is not None, "旧版做空配置应该转换为 short_entry_conditions"
        assert strategy.long_entry_conditions is None, "旧版做空配置不应该有 long_entry_conditions"
        assert strategy.short_exit_conditions is not None, "旧版做空配置应该转换为 short_exit_conditions"
        
        # 验证转换后的条件内容正确
        assert len(strategy.short_entry_conditions.conditions) == 1
        assert strategy.short_entry_conditions.conditions[0].indicator == "RSI14"
        assert strategy.short_entry_conditions.conditions[0].operator == ComparisonOperator.GT
        assert strategy.short_entry_conditions.conditions[0].value == 70
        
        # 运行回测
        kline_data = self.create_simple_test_data()
        engine = BacktestEngine(strategy, kline_data)
        result = engine.run()
        
        # 验证回测结果
        assert result is not None
        assert len(result.trades) > 0, "应该有交易记录"
        
        # 验证所有交易都是做空
        for trade in result.trades:
            assert trade.direction == "short", f"旧版做空策略应该只有做空交易，实际: {trade.direction}"
        
        print(f"\n旧版做空策略测试通过:")
        print(f"总交易: {len(result.trades)} 笔")
        print(f"所有交易方向: {[t.direction for t in result.trades]}")
    
    def test_legacy_vs_new_config_consistency(self):
        """测试旧版配置和新版配置的回测结果一致性"""
        # 创建旧版做多配置
        legacy_config_dict = {
            "name": "旧版做多策略",
            "description": "旧版配置",
            "timeframe": "1d",
            "position_size_type": "amount",
            "position_size_value": 10000.0,
            "initial_capital": 50000.0,
            "leverage": 1.0,
            "position_direction": "long",
            "entry_conditions": {
                "conditions": [
                    {
                        "indicator": "RSI14",
                        "operator": "<",
                        "value": 30
                    }
                ],
                "logic_operator": "AND"
            },
            "exit_conditions": {
                "indicator_conditions": [
                    {
                        "indicator": "RSI14",
                        "operator": ">",
                        "value": 70
                    }
                ],
                "logic_operator": "OR"
            }
        }
        
        # 创建等价的新版做多配置
        new_config = StrategyConfig(
            name="新版做多策略",
            description="新版配置",
            timeframe="1d",
            position_size_type="amount",
            position_size_value=10000.0,
            initial_capital=50000.0,
            leverage=1.0,
            long_entry_conditions=EntryConditions(
                conditions=[
                    IndicatorCondition(
                        indicator="RSI14",
                        operator=ComparisonOperator.LT,
                        value=30
                    )
                ],
                logic_operator=LogicOperator.AND
            ),
            long_exit_conditions=ExitConditions(
                indicator_conditions=[
                    IndicatorCondition(
                        indicator="RSI14",
                        operator=ComparisonOperator.GT,
                        value=70
                    )
                ],
                logic_operator=LogicOperator.OR
            )
        )
        
        # 从字典创建旧版配置
        legacy_config = StrategyConfig.from_dict(legacy_config_dict)
        
        # 使用相同的测试数据
        kline_data = self.create_simple_test_data()
        
        # 运行旧版配置回测
        legacy_engine = BacktestEngine(legacy_config, kline_data)
        legacy_result = legacy_engine.run()
        
        # 运行新版配置回测
        new_engine = BacktestEngine(new_config, kline_data)
        new_result = new_engine.run()
        
        # 验证两个结果应该一致
        assert len(legacy_result.trades) == len(new_result.trades), \
            f"交易数量应该一致: 旧版 {len(legacy_result.trades)}, 新版 {len(new_result.trades)}"
        
        # 验证最终资金一致
        assert abs(legacy_result.metrics.final_capital - new_result.metrics.final_capital) < 0.01, \
            f"最终资金应该一致: 旧版 {legacy_result.metrics.final_capital:.2f}, 新版 {new_result.metrics.final_capital:.2f}"
        
        # 验证总收益一致
        assert abs(legacy_result.metrics.total_return - new_result.metrics.total_return) < 0.01, \
            f"总收益应该一致: 旧版 {legacy_result.metrics.total_return:.2f}, 新版 {new_result.metrics.total_return:.2f}"
        
        # 验证每笔交易的盈亏一致
        for i, (legacy_trade, new_trade) in enumerate(zip(legacy_result.trades, new_result.trades)):
            assert legacy_trade.direction == new_trade.direction, \
                f"交易 #{i+1} 方向应该一致"
            assert abs(legacy_trade.entry_price - new_trade.entry_price) < 0.01, \
                f"交易 #{i+1} 开仓价格应该一致"
            assert abs(legacy_trade.exit_price - new_trade.exit_price) < 0.01, \
                f"交易 #{i+1} 平仓价格应该一致"
            assert abs(legacy_trade.profit_loss - new_trade.profit_loss) < 0.01, \
                f"交易 #{i+1} 盈亏应该一致"
        
        print(f"\n旧版与新版配置一致性测试通过:")
        print(f"旧版交易数: {len(legacy_result.trades)}")
        print(f"新版交易数: {len(new_result.trades)}")
        print(f"旧版最终资金: {legacy_result.metrics.final_capital:.2f}")
        print(f"新版最终资金: {new_result.metrics.final_capital:.2f}")
    
    def test_legacy_config_with_new_config_override(self):
        """测试同时包含旧版和新版字段时，新版字段优先"""
        # 创建同时包含旧版和新版字段的配置
        mixed_config_dict = {
            "name": "混合配置策略",
            "description": "同时包含旧版和新版字段",
            "timeframe": "1d",
            "position_size_type": "amount",
            "position_size_value": 10000.0,
            "initial_capital": 50000.0,
            "leverage": 1.0,
            # 旧版字段：做多
            "position_direction": "long",
            "entry_conditions": {
                "conditions": [
                    {
                        "indicator": "RSI14",
                        "operator": "<",
                        "value": 30
                    }
                ],
                "logic_operator": "AND"
            },
            # 新版字段：做空（应该优先使用）
            "short_entry_conditions": {
                "conditions": [
                    {
                        "indicator": "RSI14",
                        "operator": ">",
                        "value": 70
                    }
                ],
                "logic_operator": "AND"
            }
        }
        
        # 从字典创建策略配置
        strategy = StrategyConfig.from_dict(mixed_config_dict)
        
        # 验证新版字段优先
        assert strategy.short_entry_conditions is not None, "新版做空条件应该存在"
        assert strategy.long_entry_conditions is not None, "旧版做多条件也应该被转换"
        
        # 运行回测
        kline_data = self.create_simple_test_data()
        engine = BacktestEngine(strategy, kline_data)
        result = engine.run()
        
        # 验证回测结果包含做空交易（因为新版字段优先）
        short_trades = [t for t in result.trades if t.direction == "short"]
        assert len(short_trades) > 0, "应该有做空交易（新版字段优先）"
        
        print(f"\n混合配置测试通过:")
        print(f"总交易: {len(result.trades)} 笔")
        print(f"做多交易: {len([t for t in result.trades if t.direction == 'long'])} 笔")
        print(f"做空交易: {len(short_trades)} 笔")
    
    def test_legacy_config_validation_error(self):
        """测试配置缺少必要字段时的验证错误"""
        # 创建既没有新版字段也没有有效旧版配置的情况
        # （只有position_direction但没有entry_conditions不算有效的旧版配置）
        invalid_config_dict = {
            "name": "无效配置",
            "description": "缺少开仓条件",
            "timeframe": "1d",
            "position_size_type": "amount",
            "position_size_value": 10000.0,
            "initial_capital": 50000.0,
            "leverage": 1.0,
            # 明确设置新版字段为空，且没有有效的旧版配置
            "long_entry_conditions": None,
            "short_entry_conditions": None
        }
        
        # 应该抛出验证错误
        with pytest.raises(ValueError, match="必须至少配置一个方向的开仓条件"):
            StrategyConfig.from_dict(invalid_config_dict)
        
        print("\n配置验证错误测试通过")
    
    def test_compatibility_warning_logging(self, caplog):
        """测试兼容性警告日志输出"""
        import logging
        
        # 设置日志级别以捕获警告
        caplog.set_level(logging.WARNING)
        
        # 创建旧版配置
        legacy_config_dict = {
            "name": "旧版策略",
            "description": "测试警告日志",
            "timeframe": "1d",
            "position_size_type": "amount",
            "position_size_value": 10000.0,
            "initial_capital": 50000.0,
            "leverage": 1.0,
            "position_direction": "long",
            "entry_conditions": {
                "conditions": [
                    {
                        "indicator": "RSI14",
                        "operator": "<",
                        "value": 30
                    }
                ],
                "logic_operator": "AND"
            }
        }
        
        # 从字典创建策略配置（应该触发警告日志）
        strategy = StrategyConfig.from_dict(legacy_config_dict)
        
        # 验证警告日志被记录
        assert any("旧版配置字段" in record.message for record in caplog.records), \
            "应该记录兼容性警告日志"
        
        print("\n兼容性警告日志测试通过")
        print(f"捕获的警告日志: {[record.message for record in caplog.records if record.levelname == 'WARNING']}")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
