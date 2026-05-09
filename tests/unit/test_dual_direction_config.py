"""
测试双向交易策略配置

验证 StrategyConfig 支持双向开仓和平仓条件的功能
"""

import pytest
from backend.backtest.models import (
    StrategyConfig,
    EntryConditions,
    ExitConditions,
    IndicatorCondition,
    ComparisonOperator,
    LogicOperator
)


class TestDualDirectionConfig:
    """测试双向交易策略配置"""
    
    def test_long_only_strategy(self):
        """测试仅配置做多条件的策略"""
        long_entry = EntryConditions(
            conditions=[
                IndicatorCondition(
                    indicator="rsi14",
                    operator=ComparisonOperator.LT,
                    value=30
                )
            ],
            logic_operator=LogicOperator.AND
        )
        
        long_exit = ExitConditions(
            indicator_conditions=[
                IndicatorCondition(
                    indicator="rsi14",
                    operator=ComparisonOperator.GT,
                    value=70
                )
            ],
            take_profit_pct=10.0,
            stop_loss_pct=5.0
        )
        
        strategy = StrategyConfig(
            name="Long Only RSI",
            description="仅做多的RSI策略",
            timeframe="1d",
            position_size_type="amount",
            position_size_value=1000.0,
            long_entry_conditions=long_entry,
            long_exit_conditions=long_exit
        )
        
        assert strategy.long_entry_conditions is not None
        assert strategy.short_entry_conditions is None
        assert strategy.long_exit_conditions is not None
        assert strategy.short_exit_conditions is None
    
    def test_short_only_strategy(self):
        """测试仅配置做空条件的策略"""
        short_entry = EntryConditions(
            conditions=[
                IndicatorCondition(
                    indicator="rsi14",
                    operator=ComparisonOperator.GT,
                    value=70
                )
            ],
            logic_operator=LogicOperator.AND
        )
        
        short_exit = ExitConditions(
            indicator_conditions=[
                IndicatorCondition(
                    indicator="rsi14",
                    operator=ComparisonOperator.LT,
                    value=30
                )
            ],
            take_profit_pct=10.0,
            stop_loss_pct=5.0
        )
        
        strategy = StrategyConfig(
            name="Short Only RSI",
            description="仅做空的RSI策略",
            timeframe="1d",
            position_size_type="amount",
            position_size_value=1000.0,
            short_entry_conditions=short_entry,
            short_exit_conditions=short_exit
        )
        
        assert strategy.long_entry_conditions is None
        assert strategy.short_entry_conditions is not None
        assert strategy.long_exit_conditions is None
        assert strategy.short_exit_conditions is not None
    
    def test_dual_direction_strategy(self):
        """测试同时配置做多和做空条件的策略"""
        long_entry = EntryConditions(
            conditions=[
                IndicatorCondition(
                    indicator="rsi14",
                    operator=ComparisonOperator.LT,
                    value=30
                )
            ],
            logic_operator=LogicOperator.AND
        )
        
        short_entry = EntryConditions(
            conditions=[
                IndicatorCondition(
                    indicator="rsi14",
                    operator=ComparisonOperator.GT,
                    value=70
                )
            ],
            logic_operator=LogicOperator.AND
        )
        
        long_exit = ExitConditions(
            indicator_conditions=[
                IndicatorCondition(
                    indicator="rsi14",
                    operator=ComparisonOperator.GT,
                    value=70
                )
            ],
            take_profit_pct=10.0,
            stop_loss_pct=5.0
        )
        
        short_exit = ExitConditions(
            indicator_conditions=[
                IndicatorCondition(
                    indicator="rsi14",
                    operator=ComparisonOperator.LT,
                    value=30
                )
            ],
            take_profit_pct=10.0,
            stop_loss_pct=5.0
        )
        
        strategy = StrategyConfig(
            name="Dual Direction RSI",
            description="双向RSI策略",
            timeframe="1d",
            position_size_type="amount",
            position_size_value=1000.0,
            long_entry_conditions=long_entry,
            short_entry_conditions=short_entry,
            long_exit_conditions=long_exit,
            short_exit_conditions=short_exit
        )
        
        assert strategy.long_entry_conditions is not None
        assert strategy.short_entry_conditions is not None
        assert strategy.long_exit_conditions is not None
        assert strategy.short_exit_conditions is not None
    
    def test_no_entry_conditions_raises_error(self):
        """测试配置了新版字段但未提供任何开仓条件时抛出错误"""
        data = {
            "name": "Invalid Strategy",
            "description": "没有开仓条件",
            "timeframe": "1d",
            "position_size_type": "amount",
            "position_size_value": 1000.0,
            "long_entry_conditions": None,  # 明确设置为 None
            "short_entry_conditions": None  # 明确设置为 None
        }
        
        with pytest.raises(ValueError, match="必须至少配置一个方向的开仓条件"):
            StrategyConfig.from_dict(data)
    
    def test_backward_compatibility_long(self):
        """测试向后兼容：旧版做多配置转换为新版"""
        data = {
            "name": "Old Long Strategy",
            "description": "旧版做多策略",
            "timeframe": "1d",
            "position_direction": "long",
            "position_size_type": "amount",
            "position_size_value": 1000.0,
            "entry_conditions": {
                "conditions": [
                    {
                        "indicator": "rsi14",
                        "operator": "<",
                        "value": 30
                    }
                ],
                "logic_operator": "AND"
            },
            "exit_conditions": {
                "indicator_conditions": [
                    {
                        "indicator": "rsi14",
                        "operator": ">",
                        "value": 70
                    }
                ],
                "take_profit_pct": 10.0,
                "stop_loss_pct": 5.0,
                "logic_operator": "OR"
            }
        }
        
        strategy = StrategyConfig.from_dict(data)
        
        # 验证旧版字段被保留
        assert strategy.position_direction == "long"
        assert strategy.entry_conditions is not None
        assert strategy.exit_conditions is not None
        
        # 验证转换为新版字段
        assert strategy.long_entry_conditions is not None
        assert strategy.long_exit_conditions is not None
        assert strategy.short_entry_conditions is None
        assert strategy.short_exit_conditions is None
        
        # 验证条件内容正确
        assert len(strategy.long_entry_conditions.conditions) == 1
        assert strategy.long_entry_conditions.conditions[0].indicator == "rsi14"
        assert strategy.long_entry_conditions.conditions[0].value == 30
    
    def test_backward_compatibility_short(self):
        """测试向后兼容：旧版做空配置转换为新版"""
        data = {
            "name": "Old Short Strategy",
            "description": "旧版做空策略",
            "timeframe": "1d",
            "position_direction": "short",
            "position_size_type": "amount",
            "position_size_value": 1000.0,
            "entry_conditions": {
                "conditions": [
                    {
                        "indicator": "rsi14",
                        "operator": ">",
                        "value": 70
                    }
                ],
                "logic_operator": "AND"
            },
            "exit_conditions": {
                "indicator_conditions": [
                    {
                        "indicator": "rsi14",
                        "operator": "<",
                        "value": 30
                    }
                ],
                "take_profit_pct": 10.0,
                "stop_loss_pct": 5.0,
                "logic_operator": "OR"
            }
        }
        
        strategy = StrategyConfig.from_dict(data)
        
        # 验证旧版字段被保留
        assert strategy.position_direction == "short"
        assert strategy.entry_conditions is not None
        assert strategy.exit_conditions is not None
        
        # 验证转换为新版字段
        assert strategy.long_entry_conditions is None
        assert strategy.long_exit_conditions is None
        assert strategy.short_entry_conditions is not None
        assert strategy.short_exit_conditions is not None
        
        # 验证条件内容正确
        assert len(strategy.short_entry_conditions.conditions) == 1
        assert strategy.short_entry_conditions.conditions[0].indicator == "rsi14"
        assert strategy.short_entry_conditions.conditions[0].value == 70
    
    def test_new_config_overrides_old_config(self):
        """测试新版字段优先于旧版字段"""
        data = {
            "name": "Mixed Config Strategy",
            "description": "同时包含新旧配置",
            "timeframe": "1d",
            "position_direction": "long",  # 旧版：做多
            "position_size_type": "amount",
            "position_size_value": 1000.0,
            "entry_conditions": {
                "conditions": [
                    {
                        "indicator": "rsi14",
                        "operator": "<",
                        "value": 30
                    }
                ],
                "logic_operator": "AND"
            },
            "exit_conditions": {
                "indicator_conditions": [],
                "logic_operator": "OR"
            },
            # 新版：同时配置做多和做空
            "long_entry_conditions": {
                "conditions": [
                    {
                        "indicator": "rsi14",
                        "operator": "<",
                        "value": 25  # 不同的值
                    }
                ],
                "logic_operator": "AND"
            },
            "short_entry_conditions": {
                "conditions": [
                    {
                        "indicator": "rsi14",
                        "operator": ">",
                        "value": 75
                    }
                ],
                "logic_operator": "AND"
            }
        }
        
        strategy = StrategyConfig.from_dict(data)
        
        # 验证新版字段优先
        assert strategy.long_entry_conditions is not None
        assert strategy.short_entry_conditions is not None
        assert strategy.long_entry_conditions.conditions[0].value == 25  # 使用新版的值
        assert strategy.short_entry_conditions.conditions[0].value == 75
    
    def test_to_dict_includes_all_fields(self):
        """测试 to_dict() 包含所有新旧字段"""
        long_entry = EntryConditions(
            conditions=[
                IndicatorCondition(
                    indicator="rsi14",
                    operator=ComparisonOperator.LT,
                    value=30
                )
            ],
            logic_operator=LogicOperator.AND
        )
        
        short_entry = EntryConditions(
            conditions=[
                IndicatorCondition(
                    indicator="rsi14",
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
        
        data = strategy.to_dict()
        
        assert "long_entry_conditions" in data
        assert "short_entry_conditions" in data
        assert data["long_entry_conditions"] is not None
        assert data["short_entry_conditions"] is not None
        assert "name" in data
        assert "timeframe" in data
    
    def test_round_trip_serialization(self):
        """测试双向策略的序列化和反序列化往返"""
        long_entry = EntryConditions(
            conditions=[
                IndicatorCondition(
                    indicator="rsi14",
                    operator=ComparisonOperator.LT,
                    value=30
                )
            ],
            logic_operator=LogicOperator.AND
        )
        
        short_entry = EntryConditions(
            conditions=[
                IndicatorCondition(
                    indicator="rsi14",
                    operator=ComparisonOperator.GT,
                    value=70
                )
            ],
            logic_operator=LogicOperator.AND
        )
        
        original = StrategyConfig(
            name="Round Trip Test",
            description="测试往返序列化",
            timeframe="1d",
            position_size_type="amount",
            position_size_value=1000.0,
            leverage=5.0,
            long_entry_conditions=long_entry,
            short_entry_conditions=short_entry
        )
        
        # 序列化
        data = original.to_dict()
        
        # 反序列化
        restored = StrategyConfig.from_dict(data)
        
        # 验证
        assert restored.name == original.name
        assert restored.description == original.description
        assert restored.leverage == original.leverage
        assert restored.long_entry_conditions is not None
        assert restored.short_entry_conditions is not None
        assert len(restored.long_entry_conditions.conditions) == 1
        assert len(restored.short_entry_conditions.conditions) == 1
        assert restored.long_entry_conditions.conditions[0].value == 30
        assert restored.short_entry_conditions.conditions[0].value == 70
