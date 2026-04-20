#!/usr/bin/env python3
"""
数据获取工具测试
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from tools.data.fetch import (
    fetch_klines,
    fetch_current_price,
    clear_cache,
    get_timeframe_seconds
)

class TestDataFetch:
    """数据获取工具测试类"""
    
    def test_get_timeframe_seconds(self):
        """测试时间框架转换"""
        assert get_timeframe_seconds("1m") == 60
        assert get_timeframe_seconds("5m") == 300
        assert get_timeframe_seconds("1h") == 3600
        assert get_timeframe_seconds("4h") == 14400
        assert get_timeframe_seconds("1d") == 86400
        assert get_timeframe_seconds("1w") == 604800
        
        with pytest.raises(ValueError):
            get_timeframe_seconds("invalid")
    
    @patch('tools.data.fetch.requests.get')
    def test_fetch_current_price_success(self, mock_get):
        """测试成功获取当前价格"""
        # 模拟API响应
        mock_response = Mock()
        mock_response.json.return_value = {
            "symbol": "BTCUSDT",
            "price": "72106.85"
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # 调用函数
        result = fetch_current_price("BTCUSDT", use_cache=False)
        
        # 验证结果
        assert result["symbol"] == "BTCUSDT"
        assert result["price"] == 72106.85
        assert "timestamp" in result
        
        # 验证API调用
        mock_get.assert_called_once()
    
    @patch('tools.data.fetch.requests.get')
    def test_fetch_current_price_failure(self, mock_get):
        """测试获取当前价格失败"""
        # 模拟API失败
        mock_get.side_effect = Exception("Network error")
        
        # 应该抛出异常
        with pytest.raises(ConnectionError):
            fetch_current_price("BTCUSDT", use_cache=False)
    
    @patch('tools.data.fetch.requests.get')
    def test_fetch_klines_success(self, mock_get):
        """测试成功获取K线数据"""
        # 模拟API响应
        mock_response = Mock()
        mock_response.json.return_value = [
            [
                1713499200000,  # timestamp
                "72000.0",      # open
                "72500.0",      # high
                "71800.0",      # low
                "72106.85",     # close
                "100.5",        # volume
                1713502800000,  # close_time
                "7250000.0",    # quote_volume
                1000,           # trades
                "50.5",         # taker_buy_base
                "3625000.0"     # taker_buy_quote
            ]
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # 调用函数
        result = fetch_klines("BTCUSDT", "4h", 1, use_cache=False)
        
        # 验证结果
        assert len(result) == 1
        kline = result[0]
        
        assert kline["timestamp"] == 1713499200000
        assert kline["open"] == 72000.0
        assert kline["high"] == 72500.0
        assert kline["low"] == 71800.0
        assert kline["close"] == 72106.85
        assert kline["volume"] == 100.5
        
        # 验证API调用参数
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[1]["params"]["symbol"] == "BTCUSDT"
        assert call_args[1]["params"]["interval"] == "4h"
        assert call_args[1]["params"]["limit"] == 1
    
    def test_fetch_klines_invalid_timeframe(self):
        """测试无效时间框架"""
        with pytest.raises(ValueError):
            fetch_klines("BTCUSDT", "invalid", 10, use_cache=False)
    
    def test_fetch_klines_limit_adjustment(self):
        """测试限制调整"""
        # 应该自动调整超过1500的限制
        with patch('tools.data.fetch.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = []
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            # 调用超过限制
            fetch_klines("BTCUSDT", "4h", 2000, use_cache=False)
            
            # 验证限制被调整
            call_args = mock_get.call_args
            assert call_args[1]["params"]["limit"] == 1500
    
    def test_clear_cache(self):
        """测试缓存清理"""
        # 这个测试可能依赖于实际缓存状态
        # 我们主要测试函数能够正常执行而不崩溃
        try:
            cleared = clear_cache()
            assert isinstance(cleared, int)
        except Exception as e:
            pytest.fail(f"clear_cache failed: {e}")
    
    @patch('tools.data.fetch._get_from_cache')
    @patch('tools.data.fetch._save_to_cache')
    @patch('tools.data.fetch.requests.get')
    def test_cache_usage(self, mock_get, mock_save, mock_get_cache):
        """测试缓存使用"""
        # 模拟缓存命中
        mock_get_cache.return_value = [
            {
                "timestamp": 1713499200000,
                "open": 72000.0,
                "high": 72500.0,
                "low": 71800.0,
                "close": 72106.85,
                "volume": 100.5
            }
        ]
        
        # 调用函数（应该使用缓存）
        result = fetch_klines("BTCUSDT", "4h", 1, use_cache=True)
        
        # 验证使用了缓存
        mock_get_cache.assert_called_once()
        mock_get.assert_not_called()  # 不应该调用API
        mock_save.assert_not_called()  # 不应该保存缓存
        
        # 验证返回了缓存数据
        assert len(result) == 1
        assert result[0]["close"] == 72106.85
    
    @patch('tools.data.fetch._get_from_cache')
    @patch('tools.data.fetch.requests.get')
    def test_cache_miss(self, mock_get, mock_get_cache):
        """测试缓存未命中"""
        # 模拟缓存未命中
        mock_get_cache.return_value = None
        
        # 模拟API响应
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # 调用函数
        fetch_klines("BTCUSDT", "4h", 1, use_cache=True)
        
        # 验证调用了API
        mock_get.assert_called_once()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])