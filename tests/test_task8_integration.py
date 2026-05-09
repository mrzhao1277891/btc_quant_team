#!/usr/bin/env python3
"""
Task 8 集成测试：验证 API 请求转换逻辑支持双向策略
测试 convert_request_to_strategy_config() 函数的完整功能
"""

import pytest
from backend.backtest.api import BacktestRequest, IndicatorConditionRequest, convert_request_to_strategy_config
from backend.backtest.models import StrategyConfig


class TestTask8Integration:
    """Task 8: 实现 API 请求转换逻辑支持双向策略"""
    
    def test_dual_direction_request_to_config(self):
        """测试双向策略请求完整转换流程"""
        # 创建双向策略请求
        request = BacktestRequest(
            strategy_name='双向RSI策略',
            timeframe='1d',
            start_date='2024-01-01',
            end_date='2024-12-31',
            initial_capital=10000.0,
            position_size=2000.0,
            leverage=5.0,
            # 做多开仓条件
            long_entry_conditions=[
                IndicatorConditionRequest(indicator='rsi14', operator='<', value=30),
                IndicatorConditionRequest(indicator='close', operator='>', value='ema50')
            ],
            long_entry_logic='AND',
            # 做空开仓条件
            short_entry_conditions=[
                IndicatorConditionRequest(indicator='rsi14', operator='>', value=70),
                IndicatorConditionRequest(indicator='close', operator='<', value='ema50')
            ],
            short_entry_logic='AND',
            # 做多平仓条件
            long_exit_conditions=[
                IndicatorConditionRequest(indicator='rsi14', operator='>', value=70)
            ],
            long_exit_logic='OR',
            long_take_profit_pct=10.0,
            long_stop_loss_pct=5.0,
            # 做空平仓条件
            short_exit_conditions=[
                IndicatorConditionRequest(indicator='rsi14', operator='<', value=30)
            ],
            short_exit_logic='OR',
            short_take_profit_pct=10.0,
            short_stop_loss_pct=5.0
        )
        
        # 转换为配置字典
        config_dict = convert_request_to_strategy_config(request)
        
        # 验证基本配置
        assert config_dict['name'] == '双向RSI策略'
        assert config_dict['timeframe'] == '1d'
        assert config_dict['initial_capital'] == 10000.0
        assert config_dict['position_size_value'] == 2000.0
        assert config_dict['leverage'] == 5.0
        
        # 验证做多开仓条件
        assert 'long_entry_conditions' in config_dict
        long_entry = config_dict['long_entry_conditions']
        assert len(long_entry['conditions']) == 2
        assert long_entry['logic_operator'] == 'AND'
        assert long_entry['conditions'][0]['indicator'] == 'rsi14'
        assert long_entry['conditions'][0]['operator'] == '<'
        assert long_entry['conditions'][0]['value'] == 30
        assert long_entry['conditions'][1]['indicator'] == 'close'
        assert long_entry['conditions'][1]['operator'] == '>'
        assert long_entry['conditions'][1]['value'] == 'ema50'
        
        # 验证做空开仓条件
        assert 'short_entry_conditions' in config_dict
        short_entry = config_dict['short_entry_conditions']
        assert len(short_entry['conditions']) == 2
        assert short_entry['logic_operator'] == 'AND'
        assert short_entry['conditions'][0]['indicator'] == 'rsi14'
        assert short_entry['conditions'][0]['operator'] == '>'
        assert short_entry['conditions'][0]['value'] == 70
        
        # 验证做多平仓条件
        assert 'long_exit_conditions' in config_dict
        long_exit = config_dict['long_exit_conditions']
        assert len(long_exit['indicator_conditions']) == 1
        assert long_exit['logic_operator'] == 'OR'
        assert long_exit['take_profit_pct'] == 0.10  # 10% 转换为 0.10
        assert long_exit['stop_loss_pct'] == 0.05    # 5% 转换为 0.05
        
        # 验证做空平仓条件
        assert 'short_exit_conditions' in config_dict
        short_exit = config_dict['short_exit_conditions']
        assert len(short_exit['indicator_conditions']) == 1
        assert short_exit['logic_operator'] == 'OR'
        assert short_exit['take_profit_pct'] == 0.10
        assert short_exit['stop_loss_pct'] == 0.05
        
        # 验证可以创建 StrategyConfig 对象
        strategy = StrategyConfig.from_dict(config_dict)
        assert strategy.name == '双向RSI策略'
        assert strategy.long_entry_conditions is not None
        assert strategy.short_entry_conditions is not None
        assert strategy.long_exit_conditions is not None
        assert strategy.short_exit_conditions is not None
    
    def test_only_stop_loss_take_profit_exit(self):
        """测试仅止盈止损的平仓条件（无指标条件）"""
        request = BacktestRequest(
            strategy_name='仅止盈止损策略',
            timeframe='1d',
            start_date='2024-01-01',
            end_date='2024-12-31',
            long_entry_conditions=[
                IndicatorConditionRequest(indicator='close', operator='>', value='ema50')
            ],
            # 仅设置止盈止损，不设置指标平仓条件
            long_take_profit_pct=15.0,
            long_stop_loss_pct=7.5
        )
        
        config_dict = convert_request_to_strategy_config(request)
        
        # 验证平仓条件存在
        assert 'long_exit_conditions' in config_dict
        long_exit = config_dict['long_exit_conditions']
        
        # 验证指标条件为空
        assert long_exit['indicator_conditions'] == []
        
        # 验证止盈止损正确转换
        assert long_exit['take_profit_pct'] == 0.15
        assert long_exit['stop_loss_pct'] == 0.075
    
    def test_backward_compatibility_old_format(self):
        """测试向后兼容性：旧版单向策略格式"""
        request = BacktestRequest(
            strategy_name='旧版做多策略',
            timeframe='1d',
            start_date='2024-01-01',
            end_date='2024-12-31',
            # 使用旧版字段
            position_side='long',
            entry_conditions=[
                IndicatorConditionRequest(indicator='ema7', operator='>', value='ema25')
            ],
            entry_logic='AND',
            exit_conditions=[
                IndicatorConditionRequest(indicator='ema7', operator='<', value='ema25')
            ],
            exit_logic='OR',
            take_profit_pct=10.0,
            stop_loss_pct=5.0
        )
        
        config_dict = convert_request_to_strategy_config(request)
        
        # 验证旧版字段被保留
        assert 'position_direction' in config_dict
        assert config_dict['position_direction'] == 'long'
        assert 'entry_conditions' in config_dict
        assert 'exit_conditions' in config_dict
        
        # 验证旧版开仓条件
        entry = config_dict['entry_conditions']
        assert len(entry['conditions']) == 1
        assert entry['logic_operator'] == 'AND'
        assert entry['conditions'][0]['indicator'] == 'ema7'
        
        # 验证旧版平仓条件
        exit_cond = config_dict['exit_conditions']
        assert len(exit_cond['indicator_conditions']) == 1
        assert exit_cond['logic_operator'] == 'OR'
        assert exit_cond['take_profit_pct'] == 0.10
        assert exit_cond['stop_loss_pct'] == 0.05
        
        # 验证可以创建 StrategyConfig 对象（会自动转换为新版格式）
        strategy = StrategyConfig.from_dict(config_dict)
        assert strategy.name == '旧版做多策略'
        # 旧版配置会被转换为新版格式
        assert strategy.long_entry_conditions is not None or strategy.entry_conditions is not None
    
    def test_percentage_to_decimal_conversion(self):
        """测试百分比到小数的转换"""
        request = BacktestRequest(
            strategy_name='百分比转换测试',
            timeframe='1d',
            start_date='2024-01-01',
            end_date='2024-12-31',
            long_entry_conditions=[
                IndicatorConditionRequest(indicator='close', operator='>', value='ema50')
            ],
            long_take_profit_pct=12.5,   # 12.5%
            long_stop_loss_pct=6.25,     # 6.25%
            short_entry_conditions=[
                IndicatorConditionRequest(indicator='close', operator='<', value='ema50')
            ],
            short_take_profit_pct=8.75,  # 8.75%
            short_stop_loss_pct=4.5      # 4.5%
        )
        
        config_dict = convert_request_to_strategy_config(request)
        
        # 验证做多止盈止损转换
        long_exit = config_dict['long_exit_conditions']
        assert long_exit['take_profit_pct'] == 0.125
        assert long_exit['stop_loss_pct'] == 0.0625
        
        # 验证做空止盈止损转换
        short_exit = config_dict['short_exit_conditions']
        assert short_exit['take_profit_pct'] == 0.0875
        assert short_exit['stop_loss_pct'] == 0.045
    
    def test_logic_operators_handling(self):
        """测试逻辑运算符（AND/OR）的正确处理"""
        request = BacktestRequest(
            strategy_name='逻辑运算符测试',
            timeframe='1d',
            start_date='2024-01-01',
            end_date='2024-12-31',
            long_entry_conditions=[
                IndicatorConditionRequest(indicator='rsi14', operator='<', value=30),
                IndicatorConditionRequest(indicator='close', operator='>', value='ema50')
            ],
            long_entry_logic='AND',  # 所有条件都要满足
            long_exit_conditions=[
                IndicatorConditionRequest(indicator='rsi14', operator='>', value=70),
                IndicatorConditionRequest(indicator='close', operator='<', value='ema50')
            ],
            long_exit_logic='OR',    # 任一条件满足即可
            short_entry_conditions=[
                IndicatorConditionRequest(indicator='rsi14', operator='>', value=70)
            ],
            short_entry_logic='OR',
            short_exit_conditions=[
                IndicatorConditionRequest(indicator='rsi14', operator='<', value=30)
            ],
            short_exit_logic='AND'
        )
        
        config_dict = convert_request_to_strategy_config(request)
        
        # 验证做多逻辑运算符
        assert config_dict['long_entry_conditions']['logic_operator'] == 'AND'
        assert config_dict['long_exit_conditions']['logic_operator'] == 'OR'
        
        # 验证做空逻辑运算符
        assert config_dict['short_entry_conditions']['logic_operator'] == 'OR'
        assert config_dict['short_exit_conditions']['logic_operator'] == 'AND'
    
    def test_new_fields_override_old_fields(self):
        """测试新版字段优先于旧版字段"""
        request = BacktestRequest(
            strategy_name='新旧字段混合',
            timeframe='1d',
            start_date='2024-01-01',
            end_date='2024-12-31',
            # 同时提供新版和旧版字段
            long_entry_conditions=[
                IndicatorConditionRequest(indicator='rsi14', operator='<', value=30)
            ],
            # 旧版字段应该被忽略
            position_side='short',
            entry_conditions=[
                IndicatorConditionRequest(indicator='rsi14', operator='>', value=70)
            ]
        )
        
        config_dict = convert_request_to_strategy_config(request)
        
        # 验证使用新版字段
        assert 'long_entry_conditions' in config_dict
        assert config_dict['long_entry_conditions']['conditions'][0]['value'] == 30
        
        # 验证旧版字段不被使用（因为新版字段存在）
        assert 'position_direction' not in config_dict
        assert 'entry_conditions' not in config_dict


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
