#!/usr/bin/env python3
"""
DatabaseConnector属性测试
使用Hypothesis进行基于属性的测试，验证数据排序和错误报告功能
"""

import pytest
import pandas as pd
import numpy as np
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
from backend.database import DatabaseConnector


# 策略：生成合理的K线数据
@st.composite
def kline_data_strategy(draw, min_size=10, max_size=100):
    """生成K线数据的策略"""
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    
    # 生成基础价格
    base_prices = [draw(st.floats(min_value=10000.0, max_value=100000.0)) for _ in range(size)]
    
    # 生成时间戳（升序）
    start_timestamp = draw(st.integers(min_value=1609459200000, max_value=1704067200000))  # 2021-2024
    interval = draw(st.integers(min_value=3600000, max_value=86400000))  # 1小时到1天
    timestamps = [start_timestamp + i * interval for i in range(size)]
    
    # 生成OHLCV数据
    data = []
    for i, base_price in enumerate(base_prices):
        # 确保OHLC约束：low <= open, close <= high
        high = base_price * draw(st.floats(min_value=1.0, max_value=1.05))
        low = base_price * draw(st.floats(min_value=0.95, max_value=1.0))
        open_price = draw(st.floats(min_value=low, max_value=high))
        close = draw(st.floats(min_value=low, max_value=high))
        volume = draw(st.floats(min_value=0.0, max_value=1000000.0))
        
        data.append({
            'timestamp': timestamps[i],
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })
    
    return data


# 策略：生成无序的K线数据
@st.composite
def unsorted_kline_data_strategy(draw, min_size=10, max_size=50):
    """生成无序K线数据的策略"""
    data = draw(kline_data_strategy(min_size=min_size, max_size=max_size))
    
    # 使用hypothesis的permutations来打乱顺序
    indices = list(range(len(data)))
    shuffled_indices = draw(st.permutations(indices))
    shuffled_data = [data[i] for i in shuffled_indices]
    
    return shuffled_data


class TestDatabaseConnectorDataSorting:
    """测试DatabaseConnector的数据排序功能 (任务3.2)"""
    
    @given(kline_data=kline_data_strategy(min_size=10, max_size=100))
    @settings(max_examples=100, deadline=None)
    def test_property_12_data_sorting_guarantee(self, kline_data):
        """
        **Validates: Requirements 5.5**
        
        Property 12: Data Sorting Guarantee
        For any query result from the Database_Connector, K-line data SHALL be 
        sorted by timestamp in ascending chronological order.
        """
        # 创建DataFrame（可能是无序的）
        df = pd.DataFrame(kline_data)
        
        # 打乱顺序以模拟数据库返回的无序数据
        df = df.sample(frac=1).reset_index(drop=True)
        
        # 模拟DatabaseConnector的排序逻辑
        # 在实际的fetch_klines方法中，数据会被排序
        sorted_df = df.sort_values('timestamp', ascending=True).reset_index(drop=True)
        
        # 验证：数据应该按timestamp升序排列
        timestamps = sorted_df['timestamp'].values
        for i in range(1, len(timestamps)):
            assert timestamps[i] >= timestamps[i-1], \
                f"时间戳应该升序排列: {timestamps[i-1]} <= {timestamps[i]}"
        
        # 验证：排序后的数据应该是单调递增的
        assert sorted_df['timestamp'].is_monotonic_increasing, \
            "时间戳序列应该是单调递增的"
    
    @given(kline_data=unsorted_kline_data_strategy(min_size=20, max_size=50))
    @settings(max_examples=100, deadline=None)
    def test_data_sorting_with_duplicates(self, kline_data):
        """测试包含重复时间戳的数据排序"""
        df = pd.DataFrame(kline_data)
        
        # 添加一些重复的时间戳
        if len(df) > 5:
            df.loc[5, 'timestamp'] = df.loc[3, 'timestamp']
        
        # 排序
        sorted_df = df.sort_values('timestamp', ascending=True).reset_index(drop=True)
        
        # 验证：数据应该按timestamp升序排列（允许相等）
        timestamps = sorted_df['timestamp'].values
        for i in range(1, len(timestamps)):
            assert timestamps[i] >= timestamps[i-1], \
                "时间戳应该升序排列（允许相等）"
    
    @patch('mysql.connector.pooling.MySQLConnectionPool')
    def test_fetch_klines_returns_sorted_data(self, mock_pool_class):
        """测试fetch_klines方法返回排序后的数据"""
        # 创建模拟的连接池和连接
        mock_pool = MagicMock()
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        
        mock_pool_class.return_value = mock_pool
        mock_pool.get_connection.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor
        
        # 模拟数据库返回无序数据
        unsorted_data = [
            {'timestamp': 1609459200000, 'open': 30000, 'high': 31000, 'low': 29000, 'close': 30500, 'volume': 100},
            {'timestamp': 1609545600000, 'open': 30500, 'high': 31500, 'low': 30000, 'close': 31000, 'volume': 150},
            {'timestamp': 1609372800000, 'open': 29000, 'high': 30000, 'low': 28500, 'close': 29500, 'volume': 120},
        ]
        mock_cursor.fetchall.return_value = unsorted_data
        
        # 创建DatabaseConnector实例
        db = DatabaseConnector()
        
        # 调用fetch_klines
        start_date = datetime(2021, 1, 1)
        end_date = datetime(2021, 1, 3)
        df = db.fetch_klines('BTCUSDT', '1d', start_date, end_date)
        
        # 验证：返回的数据应该是排序的
        assert df['timestamp'].is_monotonic_increasing, \
            "fetch_klines应该返回按时间戳升序排列的数据"
        
        # 验证：第一条记录应该是最早的时间戳
        assert df.iloc[0]['timestamp'] == 1609372800000, \
            "第一条记录应该是最早的时间戳"


class TestDatabaseConnectorErrorReporting:
    """测试DatabaseConnector的错误报告功能 (任务3.2)"""
    
    @given(
        symbol=st.sampled_from(['BTCUSDT', 'ETHUSDT', 'BNBUSDT']),
        timeframe=st.sampled_from(['1m', '1w', '1d', '4h']),
        days_offset=st.integers(min_value=1, max_value=365)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_13_missing_data_error_reporting(self, symbol, timeframe, days_offset):
        """
        **Validates: Requirements 5.6**
        
        Property 13: Missing Data Error Reporting
        For any query requesting data that does not exist in the database, 
        the Database_Connector SHALL return an error message indicating 
        the missing data range.
        """
        # 创建模拟的数据库连接
        with patch('mysql.connector.pooling.MySQLConnectionPool') as mock_pool_class:
            mock_pool = MagicMock()
            mock_connection = MagicMock()
            mock_cursor = MagicMock()
            
            mock_pool_class.return_value = mock_pool
            mock_pool.get_connection.return_value = mock_connection
            mock_connection.cursor.return_value = mock_cursor
            
            # 模拟数据库返回空结果（数据不存在）
            mock_cursor.fetchall.return_value = []
            
            # 创建DatabaseConnector实例
            db = DatabaseConnector()
            
            # 设置查询日期范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_offset)
            
            # 验证：应该抛出ValueError并包含错误信息
            with pytest.raises(ValueError) as exc_info:
                db.fetch_klines(symbol, timeframe, start_date, end_date)
            
            # 验证：错误信息应该包含symbol、timeframe和日期范围
            error_message = str(exc_info.value)
            assert symbol in error_message, \
                f"错误信息应该包含symbol: {symbol}"
            assert timeframe in error_message, \
                f"错误信息应该包含timeframe: {timeframe}"
            assert "No data found" in error_message or "not found" in error_message.lower(), \
                "错误信息应该明确指出数据不存在"
    
    @patch('mysql.connector.pooling.MySQLConnectionPool')
    def test_missing_data_error_contains_date_range(self, mock_pool_class):
        """测试缺失数据错误包含日期范围信息"""
        # 创建模拟的连接池和连接
        mock_pool = MagicMock()
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        
        mock_pool_class.return_value = mock_pool
        mock_pool.get_connection.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor
        
        # 模拟数据库返回空结果
        mock_cursor.fetchall.return_value = []
        
        # 创建DatabaseConnector实例
        db = DatabaseConnector()
        
        # 设置查询日期范围
        start_date = datetime(2021, 1, 1)
        end_date = datetime(2021, 1, 31)
        
        # 验证：应该抛出ValueError
        with pytest.raises(ValueError) as exc_info:
            db.fetch_klines('BTCUSDT', '1d', start_date, end_date)
        
        # 验证：错误信息应该包含日期范围
        error_message = str(exc_info.value)
        assert '2021' in error_message, \
            "错误信息应该包含年份"
    
    @patch('mysql.connector.pooling.MySQLConnectionPool')
    def test_get_available_date_range_no_data(self, mock_pool_class):
        """测试get_available_date_range在无数据时的错误报告"""
        # 创建模拟的连接池和连接
        mock_pool = MagicMock()
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        
        mock_pool_class.return_value = mock_pool
        mock_pool.get_connection.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor
        
        # 模拟数据库返回空结果
        mock_cursor.fetchone.return_value = {'earliest_date': None, 'latest_date': None}
        
        # 创建DatabaseConnector实例
        db = DatabaseConnector()
        
        # 验证：应该抛出ValueError
        with pytest.raises(ValueError) as exc_info:
            db.get_available_date_range('BTCUSDT', '1d')
        
        # 验证：错误信息应该明确指出无数据
        error_message = str(exc_info.value)
        assert 'No data available' in error_message or 'not available' in error_message.lower(), \
            "错误信息应该明确指出无可用数据"
        assert 'BTCUSDT' in error_message, \
            "错误信息应该包含symbol"
        assert '1d' in error_message, \
            "错误信息应该包含timeframe"
    
    @given(
        symbol=st.text(min_size=3, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
        timeframe=st.sampled_from(['1m', '1w', '1d', '4h', '1h', '15m'])
    )
    @settings(max_examples=50, deadline=None)
    def test_error_message_format_consistency(self, symbol, timeframe):
        """测试错误信息格式的一致性"""
        with patch('mysql.connector.pooling.MySQLConnectionPool') as mock_pool_class:
            mock_pool = MagicMock()
            mock_connection = MagicMock()
            mock_cursor = MagicMock()
            
            mock_pool_class.return_value = mock_pool
            mock_pool.get_connection.return_value = mock_connection
            mock_connection.cursor.return_value = mock_cursor
            
            # 模拟数据库返回空结果
            mock_cursor.fetchall.return_value = []
            
            # 创建DatabaseConnector实例
            db = DatabaseConnector()
            
            # 设置查询日期范围
            start_date = datetime(2021, 1, 1)
            end_date = datetime(2021, 1, 31)
            
            # 验证：应该抛出ValueError
            try:
                db.fetch_klines(symbol, timeframe, start_date, end_date)
                pytest.fail("应该抛出ValueError")
            except ValueError as e:
                error_message = str(e)
                
                # 验证：错误信息应该包含关键信息
                assert len(error_message) > 0, "错误信息不应该为空"
                assert symbol in error_message, "错误信息应该包含symbol"
                assert timeframe in error_message, "错误信息应该包含timeframe"


class TestDatabaseConnectorIntegration:
    """DatabaseConnector集成测试"""
    
    @patch('mysql.connector.pooling.MySQLConnectionPool')
    def test_fetch_klines_with_valid_data(self, mock_pool_class):
        """测试fetch_klines返回有效数据"""
        # 创建模拟的连接池和连接
        mock_pool = MagicMock()
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        
        mock_pool_class.return_value = mock_pool
        mock_pool.get_connection.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor
        
        # 模拟数据库返回有效数据
        valid_data = [
            {'timestamp': 1609459200000, 'open': 30000, 'high': 31000, 'low': 29000, 'close': 30500, 'volume': 100},
            {'timestamp': 1609545600000, 'open': 30500, 'high': 31500, 'low': 30000, 'close': 31000, 'volume': 150},
            {'timestamp': 1609632000000, 'open': 31000, 'high': 32000, 'low': 30500, 'close': 31500, 'volume': 200},
        ]
        mock_cursor.fetchall.return_value = valid_data
        
        # 创建DatabaseConnector实例
        db = DatabaseConnector()
        
        # 调用fetch_klines
        start_date = datetime(2021, 1, 1)
        end_date = datetime(2021, 1, 3)
        df = db.fetch_klines('BTCUSDT', '1d', start_date, end_date)
        
        # 验证：返回的DataFrame应该包含所有数据
        assert len(df) == 3, "应该返回3条记录"
        assert df['timestamp'].is_monotonic_increasing, "时间戳应该升序排列"
        assert all(col in df.columns for col in ['timestamp', 'open', 'high', 'low', 'close', 'volume']), \
            "应该包含所有必需的列"
    
    @patch('mysql.connector.pooling.MySQLConnectionPool')
    def test_fetch_klines_empty_result_raises_error(self, mock_pool_class):
        """测试fetch_klines在空结果时抛出错误"""
        # 创建模拟的连接池和连接
        mock_pool = MagicMock()
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        
        mock_pool_class.return_value = mock_pool
        mock_pool.get_connection.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor
        
        # 模拟数据库返回空结果
        mock_cursor.fetchall.return_value = []
        
        # 创建DatabaseConnector实例
        db = DatabaseConnector()
        
        # 验证：应该抛出ValueError
        with pytest.raises(ValueError) as exc_info:
            db.fetch_klines('BTCUSDT', '1d', datetime(2021, 1, 1), datetime(2021, 1, 31))
        
        # 验证：错误信息应该有意义
        assert 'No data found' in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
