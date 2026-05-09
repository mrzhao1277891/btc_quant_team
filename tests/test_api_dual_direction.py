#!/usr/bin/env python3
"""
测试 API BacktestRequest 模型的双向条件支持
Task 7: 扩展 API BacktestRequest 模型支持双向条件
"""

import pytest
from backend.backtest.api import BacktestRequest, IndicatorConditionRequest, convert_request_to_strategy_config


class TestBacktestRequestDualDirection:
    """测试 BacktestRequest 模型的双向条件字段"""
    
    def test_dual_direction_fields_exist(self):
        """测试双向条件字段是否存在"""
        request = BacktestRequest(
            strategy_name='Test',
            start_date='2024-01-01',
            end_date='2024-12-31',
            long_entry_conditions=[],
            short_entry_conditions=[],
            long_exit_conditions=[],
            short_exit_conditions=[],
            long_entry_logic='AND',
            short_entry_logic='OR',
            long_exit_logic='AND',
            short_exit_logic='OR',
            long_take_profit_pct=10.0,
            long_stop_loss_pct=5.0,
            short_take_profit_pct=8.0,
            short_stop_loss_pct=4.0
        )
        
        assert request.long_entry_conditions == []
        assert request.short_entry_conditions == []
        assert request.long_exit_conditions == []
        assert request.short_exit_conditions == []
        assert request.long_entry_logic == 'AND'
        assert request.short_entry_logic == 'OR'
        assert request.long_exit_logic == 'AND'
        assert request.short_exit_logic == 'OR'
        assert request.long_take_profit_pct == 10.0
        assert request.long_stop_loss_pct == 5.0
        assert request.short_take_profit_pct == 8.0
        assert request.short_stop_loss_pct == 4.0
    
    def test_dual_direction_strategy_conversion(self):
        """测试双向策略的转换"""
        request = BacktestRequest(
            strategy_name='Dual RSI Strategy',
            start_date='2024-01-01',
            end_date='2024-12-31',
            long_entry_conditions=[
                IndicatorConditionRequest(indicator='rsi14', operator='<', value=30)
            ],
            short_entry_conditions=[
                IndicatorConditionRequest(indicator='rsi14', operator='>', value=70)
            ],
            long_take_profit_pct=10.0,
            short_stop_loss_pct=5.0
        )
        
        config = convert_request_to_strategy_config(request)
        
        assert 'long_entry_conditions' in config
        assert 'short_entry_conditions' in config
        assert len(config['long_entry_conditions']['conditions']) == 1
        assert len(config['short_entry_conditions']['conditions']) == 1
        assert config['long_entry_conditions']['conditions'][0]['indicator'] == 'rsi14'
        assert config['short_entry_conditions']['conditions'][0]['indicator'] == 'rsi14'
    
    def test_long_only_strategy(self):
        """测试仅做多策略"""
        request = BacktestRequest(
            strategy_name='Long Only',
            start_date='2024-01-01',
            end_date='2024-12-31',
            long_entry_conditions=[
                IndicatorConditionRequest(indicator='ema7', operator='>', value='ema25')
            ],
            long_take_profit_pct=8.0
        )
        
        config = convert_request_to_strategy_config(request)
        
        assert 'long_entry_conditions' in config
        assert 'short_entry_conditions' not in config
        assert 'long_exit_conditions' in config
    
    def test_short_only_strategy(self):
        """测试仅做空策略"""
        request = BacktestRequest(
            strategy_name='Short Only',
            start_date='2024-01-01',
            end_date='2024-12-31',
            short_entry_conditions=[
                IndicatorConditionRequest(indicator='close', operator='<', value='boll_dn')
            ],
            short_stop_loss_pct=6.0
        )
        
        config = convert_request_to_strategy_config(request)
        
        assert 'long_entry_conditions' not in config
        assert 'short_entry_conditions' in config
        assert 'short_exit_conditions' in config
    
    def test_backward_compatibility_legacy_fields(self):
        """测试向后兼容性 - 旧版字段"""
        request = BacktestRequest(
            strategy_name='Legacy Strategy',
            start_date='2024-01-01',
            end_date='2024-12-31',
            entry_conditions=[
                IndicatorConditionRequest(indicator='rsi14', operator='<', value=30)
            ],
            exit_conditions=[
                IndicatorConditionRequest(indicator='rsi14', operator='>', value=70)
            ],
            position_side='long',
            take_profit_pct=10.0,
            stop_loss_pct=5.0
        )
        
        config = convert_request_to_strategy_config(request)
        
        # 旧版字段应该被保留
        assert 'position_direction' in config
        assert config['position_direction'] == 'long'
        assert 'entry_conditions' in config
        assert 'exit_conditions' in config
        assert len(config['entry_conditions']['conditions']) == 1
        assert len(config['exit_conditions']['indicator_conditions']) == 1
    
    def test_exit_conditions_with_only_stop_loss_take_profit(self):
        """测试仅止盈止损的平仓条件（无指标条件）"""
        request = BacktestRequest(
            strategy_name='TP/SL Only',
            start_date='2024-01-01',
            end_date='2024-12-31',
            long_entry_conditions=[
                IndicatorConditionRequest(indicator='close', operator='>', value='ema50')
            ],
            long_take_profit_pct=15.0,
            long_stop_loss_pct=7.5
        )
        
        config = convert_request_to_strategy_config(request)
        
        assert 'long_exit_conditions' in config
        assert config['long_exit_conditions']['indicator_conditions'] == []
        assert config['long_exit_conditions']['take_profit_pct'] == 0.15
        assert config['long_exit_conditions']['stop_loss_pct'] == 0.075
    
    def test_logic_operators(self):
        """测试逻辑运算符"""
        request = BacktestRequest(
            strategy_name='Logic Test',
            start_date='2024-01-01',
            end_date='2024-12-31',
            long_entry_conditions=[
                IndicatorConditionRequest(indicator='rsi14', operator='<', value=30),
                IndicatorConditionRequest(indicator='close', operator='>', value='ema50')
            ],
            long_entry_logic='AND',
            short_entry_conditions=[
                IndicatorConditionRequest(indicator='rsi14', operator='>', value=70)
            ],
            short_entry_logic='OR'
        )
        
        config = convert_request_to_strategy_config(request)
        
        assert config['long_entry_conditions']['logic_operator'] == 'AND'
        assert config['short_entry_conditions']['logic_operator'] == 'OR'
    
    def test_percentage_conversion(self):
        """测试百分比转换（前端传入的是百分比，需要转换为小数）"""
        request = BacktestRequest(
            strategy_name='Percentage Test',
            start_date='2024-01-01',
            end_date='2024-12-31',
            long_entry_conditions=[
                IndicatorConditionRequest(indicator='close', operator='>', value='ema50')
            ],
            long_take_profit_pct=10.0,  # 10%
            long_stop_loss_pct=5.0,     # 5%
            short_take_profit_pct=8.0,  # 8%
            short_stop_loss_pct=4.0     # 4%
        )
        
        config = convert_request_to_strategy_config(request)
        
        # 应该转换为小数
        assert config['long_exit_conditions']['take_profit_pct'] == 0.10
        assert config['long_exit_conditions']['stop_loss_pct'] == 0.05


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
