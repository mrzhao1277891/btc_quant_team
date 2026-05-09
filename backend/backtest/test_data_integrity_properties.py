#!/usr/bin/env python3
"""
数据完整性验证的属性测试
使用Hypothesis进行基于属性的测试，验证OHLC数据验证、缺失时间戳检测、无效数据排除和数据质量警告传播功能
"""

import pytest
import pandas as pd
import numpy as np
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime, timedelta
from backend.database import DatabaseConnector


# 自定义策略：生成有效的OHLC数据
@st.composite
def valid_ohlc_data(draw, min_size=10, max_size=100):
    """生成有效的OHLC数据"""
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    base_prices = draw(st.lists(
        st.floats(min_value=100.0, max_value=100000.0, allow_nan=False, allow_infinity=False),
        min_size=size,
        max_size=size
    ))
    
    data = []
    for i, base_price in enumerate(base_prices):
        # 生成满足约束的OHLC数据: low <= open, close <= high
        low = base_price * draw(st.floats(min_value=0.95, max_value=1.0))
        high = base_price * draw(st.floats(min_value=1.0, max_value=1.05))
        open_price = draw(st.floats(min_value=low, max_value=high))
        close_price = draw(st.floats(min_value=low, max_value=high))
        volume = draw(st.floats(min_value=0.0, max_value=1000000.0))
        
        # 生成时间戳（毫秒）
        timestamp = 1609459200000 + i * 86400000  # 从2021-01-01开始，每天一个
        
        data.append({
            'timestamp': timestamp,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close_price,
            'volume': volume
        })
    
    return pd.DataFrame(data)


# 自定义策略：生成无效的OHLC数据（违反约束）
@st.composite
def invalid_ohlc_data(draw, min_size=5, max_size=50):
    """生成违反OHLC约束的数据"""
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    base_prices = draw(st.lists(
        st.floats(min_value=100.0, max_value=100000.0, allow_nan=False, allow_infinity=False),
        min_size=size,
        max_size=size
    ))
    
    data = []
    violation_type = draw(st.sampled_from(['low_gt_open', 'low_gt_close', 'open_gt_high', 'close_gt_high']))
    
    for i, base_price in enumerate(base_prices):
        if i == size // 2:  # 在中间位置插入违规数据
            if violation_type == 'low_gt_open':
                # low > open
                low = base_price * 1.05
                high = base_price * 1.10
                open_price = base_price
                close_price = base_price * 1.02
            elif violation_type == 'low_gt_close':
                # low > close
                low = base_price * 1.05
                high = base_price * 1.10
                open_price = base_price * 1.08
                close_price = base_price
            elif violation_type == 'open_gt_high':
                # open > high
                low = base_price * 0.95
                high = base_price
                open_price = base_price * 1.05
                close_price = base_price * 0.98
            else:  # close_gt_high
                # close > high
                low = base_price * 0.95
                high = base_price
                open_price = base_price * 0.98
                close_price = base_price * 1.05
        else:
            # 生成正常数据
            low = base_price * 0.95
            high = base_price * 1.05
            open_price = base_price
            close_price = base_price * 1.02
        
        volume = draw(st.floats(min_value=0.0, max_value=1000000.0))
        timestamp = 1609459200000 + i * 86400000
        
        data.append({
            'timestamp': timestamp,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close_price,
            'volume': volume
        })
    
    return pd.DataFrame(data)


# 自定义策略：生成带有缺失时间戳的数据
@st.composite
def data_with_missing_timestamps(draw, timeframe='1d', min_size=10, max_size=50):
    """生成带有缺失时间戳的数据"""
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    
    # 时间间隔映射（毫秒）
    interval_map = {
        '1m': 30 * 24 * 60 * 60 * 1000,  # 30天
        '1w': 7 * 24 * 60 * 60 * 1000,    # 7天
        '1d': 24 * 60 * 60 * 1000,        # 1天
        '4h': 4 * 60 * 60 * 1000,         # 4小时
    }
    
    interval = interval_map.get(timeframe, 24 * 60 * 60 * 1000)
    
    data = []
    current_timestamp = 1609459200000  # 2021-01-01
    
    for i in range(size):
        base_price = draw(st.floats(min_value=100.0, max_value=100000.0))
        low = base_price * 0.95
        high = base_price * 1.05
        open_price = base_price
        close_price = base_price * 1.02
        volume = draw(st.floats(min_value=0.0, max_value=1000000.0))
        
        data.append({
            'timestamp': current_timestamp,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close_price,
            'volume': volume
        })
        
        # 随机跳过一些时间戳（创建缺失）
        if i < size - 1 and draw(st.booleans()):
            skip_periods = draw(st.integers(min_value=2, max_value=5))
            current_timestamp += interval * skip_periods
        else:
            current_timestamp += interval
    
    return pd.DataFrame(data)


class TestOHLCDataValidation:
    """测试OHLC数据验证的属性 (任务3.4)"""
    
    @given(df=valid_ohlc_data(min_size=10, max_size=100))
    @settings(max_examples=100, deadline=None)
    def test_property_26_ohlc_data_validation_valid(self, df):
        """
        Property 26: OHLC Data Validation
        验证有效的OHLC数据应该通过验证
        
        **Validates: Requirements 13.3, 13.5**
        """
        db = DatabaseConnector()
        warnings = db.validate_data_integrity(df, '1d')
        
        # 过滤掉时间戳相关的警告，只关注OHLC约束
        ohlc_warnings = [w for w in warnings if 'OHLC violation' in w or 'Negative volume' in w]
        
        # 验证：有效数据不应该有OHLC违规警告
        assert len(ohlc_warnings) == 0, f"有效数据不应该有OHLC违规警告，但发现: {ohlc_warnings}"
    
    @given(df=invalid_ohlc_data(min_size=5, max_size=50))
    @settings(max_examples=100, deadline=None)
    def test_property_26_ohlc_data_validation_invalid(self, df):
        """
        Property 26: OHLC Data Validation
        验证无效的OHLC数据应该被检测出来
        
        **Validates: Requirements 13.3, 13.5**
        """
        db = DatabaseConnector()
        warnings = db.validate_data_integrity(df, '1d')
        
        # 过滤出OHLC违规警告
        ohlc_warnings = [w for w in warnings if 'OHLC violation' in w]
        
        # 验证：无效数据应该产生至少一个OHLC违规警告
        assert len(ohlc_warnings) > 0, "无效OHLC数据应该产生违规警告"
    
    @given(
        size=st.integers(min_value=10, max_value=50),
        base_price=st.floats(min_value=100.0, max_value=10000.0)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_26_ohlc_constraints(self, size, base_price):
        """
        Property 26: OHLC Data Validation
        验证OHLC约束: low <= open, low <= close, open <= high, close <= high, volume >= 0
        
        **Validates: Requirements 13.3, 13.5**
        """
        # 生成满足约束的数据
        data = []
        for i in range(size):
            low = base_price * 0.95
            high = base_price * 1.05
            open_price = base_price
            close_price = base_price * 1.02
            volume = 1000.0
            
            data.append({
                'timestamp': 1609459200000 + i * 86400000,
                'open': open_price,
                'high': high,
                'low': low,
                'close': close_price,
                'volume': volume
            })
        
        df = pd.DataFrame(data)
        db = DatabaseConnector()
        warnings = db.validate_data_integrity(df, '1d')
        
        # 过滤OHLC警告
        ohlc_warnings = [w for w in warnings if 'OHLC violation' in w or 'Negative volume' in w]
        
        # 验证：满足约束的数据不应该有警告
        assert len(ohlc_warnings) == 0, f"满足约束的数据不应该有警告: {ohlc_warnings}"


class TestMissingTimestampDetection:
    """测试缺失时间戳检测的属性 (任务3.4)"""
    
    @given(
        timeframe=st.sampled_from(['1d', '4h', '1w']),
        size=st.integers(min_value=10, max_value=50)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_27_missing_timestamp_detection_continuous(self, timeframe, size):
        """
        Property 27: Missing Timestamp Detection
        验证连续的时间序列不应该产生缺失时间戳警告
        
        **Validates: Requirements 13.1, 13.2**
        """
        # 时间间隔映射（毫秒）
        interval_map = {
            '1m': 30 * 24 * 60 * 60 * 1000,
            '1w': 7 * 24 * 60 * 60 * 1000,
            '1d': 24 * 60 * 60 * 1000,
            '4h': 4 * 60 * 60 * 1000,
        }
        
        interval = interval_map[timeframe]
        
        # 生成连续的时间序列
        data = []
        current_timestamp = 1609459200000
        
        for i in range(size):
            data.append({
                'timestamp': current_timestamp,
                'open': 50000.0,
                'high': 51000.0,
                'low': 49000.0,
                'close': 50500.0,
                'volume': 1000.0
            })
            current_timestamp += interval
        
        df = pd.DataFrame(data)
        db = DatabaseConnector()
        warnings = db.validate_data_integrity(df, timeframe)
        
        # 过滤出时间戳相关的警告
        timestamp_warnings = [w for w in warnings if 'Missing' in w and 'period' in w]
        
        # 验证：连续的时间序列不应该有缺失时间戳警告
        assert len(timestamp_warnings) == 0, f"连续时间序列不应该有缺失警告: {timestamp_warnings}"
    
    @given(df=data_with_missing_timestamps(timeframe='1d', min_size=10, max_size=50))
    @settings(max_examples=100, deadline=None)
    def test_property_27_missing_timestamp_detection_gaps(self, df):
        """
        Property 27: Missing Timestamp Detection
        验证带有缺失时间戳的数据应该被检测出来
        
        **Validates: Requirements 13.1, 13.2**
        """
        db = DatabaseConnector()
        warnings = db.validate_data_integrity(df, '1d')
        
        # 检查是否有缺失时间戳的警告
        # 注意：由于随机生成，可能有也可能没有缺失
        # 我们只验证如果有缺失，应该被检测到
        
        # 手动检查是否真的有缺失
        timestamps = df['timestamp'].values
        interval = 24 * 60 * 60 * 1000  # 1天
        tolerance = interval * 0.1
        
        has_gaps = False
        for i in range(1, len(timestamps)):
            gap = timestamps[i] - timestamps[i-1]
            if gap > interval + tolerance:
                has_gaps = True
                break
        
        if has_gaps:
            # 如果有缺失，应该有警告
            timestamp_warnings = [w for w in warnings if 'Missing' in w and 'period' in w]
            assert len(timestamp_warnings) > 0, "有缺失时间戳时应该产生警告"
    
    @given(
        timeframe=st.sampled_from(['1d', '4h']),
        size=st.integers(min_value=5, max_value=30),
        gap_position=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_27_missing_timestamp_detection_explicit_gap(self, timeframe, size, gap_position):
        """
        Property 27: Missing Timestamp Detection
        验证显式插入的时间戳缺失应该被检测
        
        **Validates: Requirements 13.1, 13.2**
        """
        assume(gap_position < size - 1)
        
        interval_map = {
            '1d': 24 * 60 * 60 * 1000,
            '4h': 4 * 60 * 60 * 1000,
        }
        
        interval = interval_map[timeframe]
        
        # 生成数据，在gap_position处插入缺失
        data = []
        current_timestamp = 1609459200000
        
        for i in range(size):
            data.append({
                'timestamp': current_timestamp,
                'open': 50000.0,
                'high': 51000.0,
                'low': 49000.0,
                'close': 50500.0,
                'volume': 1000.0
            })
            
            if i == gap_position:
                # 跳过3个周期
                current_timestamp += interval * 4
            else:
                current_timestamp += interval
        
        df = pd.DataFrame(data)
        db = DatabaseConnector()
        warnings = db.validate_data_integrity(df, timeframe)
        
        # 应该检测到缺失
        timestamp_warnings = [w for w in warnings if 'Missing' in w and 'period' in w]
        assert len(timestamp_warnings) > 0, "显式的时间戳缺失应该被检测到"


class TestInvalidDataExclusion:
    """测试无效数据排除的属性 (任务3.4)"""
    
    @given(
        size=st.integers(min_value=10, max_value=50),
        violation_index=st.integers(min_value=0, max_value=49)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_28_invalid_data_exclusion(self, size, violation_index):
        """
        Property 28: Invalid Data Exclusion
        验证违反OHLC约束的记录应该被检测并记录错误
        
        **Validates: Requirements 13.4**
        """
        assume(violation_index < size)
        
        # 生成数据，在violation_index处插入违规数据
        data = []
        for i in range(size):
            if i == violation_index:
                # 插入违规数据: low > high
                data.append({
                    'timestamp': 1609459200000 + i * 86400000,
                    'open': 50000.0,
                    'high': 49000.0,  # high < low (违规)
                    'low': 51000.0,
                    'close': 50500.0,
                    'volume': 1000.0
                })
            else:
                # 正常数据
                data.append({
                    'timestamp': 1609459200000 + i * 86400000,
                    'open': 50000.0,
                    'high': 51000.0,
                    'low': 49000.0,
                    'close': 50500.0,
                    'volume': 1000.0
                })
        
        df = pd.DataFrame(data)
        db = DatabaseConnector()
        warnings = db.validate_data_integrity(df, '1d')
        
        # 应该检测到OHLC违规
        ohlc_warnings = [w for w in warnings if 'OHLC violation' in w]
        assert len(ohlc_warnings) > 0, "违规数据应该被检测并记录错误"
    
    @given(
        size=st.integers(min_value=10, max_value=50),
        negative_volume_index=st.integers(min_value=0, max_value=49)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_28_negative_volume_detection(self, size, negative_volume_index):
        """
        Property 28: Invalid Data Exclusion
        验证负成交量应该被检测并记录错误
        
        **Validates: Requirements 13.4**
        """
        assume(negative_volume_index < size)
        
        # 生成数据，在negative_volume_index处插入负成交量
        data = []
        for i in range(size):
            volume = -1000.0 if i == negative_volume_index else 1000.0
            
            data.append({
                'timestamp': 1609459200000 + i * 86400000,
                'open': 50000.0,
                'high': 51000.0,
                'low': 49000.0,
                'close': 50500.0,
                'volume': volume
            })
        
        df = pd.DataFrame(data)
        db = DatabaseConnector()
        warnings = db.validate_data_integrity(df, '1d')
        
        # 应该检测到负成交量
        volume_warnings = [w for w in warnings if 'Negative volume' in w]
        assert len(volume_warnings) > 0, "负成交量应该被检测并记录错误"


class TestDataQualityWarningPropagation:
    """测试数据质量警告传播的属性 (任务3.4)"""
    
    @given(df=invalid_ohlc_data(min_size=5, max_size=30))
    @settings(max_examples=100, deadline=None)
    def test_property_29_data_quality_warning_propagation(self, df):
        """
        Property 29: Data Quality Warning Propagation
        验证数据质量问题应该被包含在警告列表中
        
        **Validates: Requirements 13.6**
        """
        db = DatabaseConnector()
        warnings = db.validate_data_integrity(df, '1d')
        
        # 验证：应该返回警告列表
        assert isinstance(warnings, list), "应该返回警告列表"
        
        # 验证：有数据质量问题时，警告列表不应该为空
        assert len(warnings) > 0, "有数据质量问题时应该返回警告"
        
        # 验证：每个警告都应该是字符串
        for warning in warnings:
            assert isinstance(warning, str), "每个警告都应该是字符串"
    
    @given(df=valid_ohlc_data(min_size=10, max_size=50))
    @settings(max_examples=100, deadline=None)
    def test_property_29_no_warnings_for_valid_data(self, df):
        """
        Property 29: Data Quality Warning Propagation
        验证有效数据不应该产生OHLC相关的警告
        
        **Validates: Requirements 13.6**
        """
        db = DatabaseConnector()
        
        # 生成连续的时间戳以避免时间戳警告
        for i in range(len(df)):
            df.loc[i, 'timestamp'] = 1609459200000 + i * 86400000
        
        warnings = db.validate_data_integrity(df, '1d')
        
        # 过滤OHLC和成交量相关的警告
        data_quality_warnings = [w for w in warnings if 'OHLC violation' in w or 'Negative volume' in w]
        
        # 验证：有效数据不应该有数据质量警告
        assert len(data_quality_warnings) == 0, f"有效数据不应该有数据质量警告: {data_quality_warnings}"
    
    @given(
        size=st.integers(min_value=10, max_value=50)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_29_warning_format(self, size):
        """
        Property 29: Data Quality Warning Propagation
        验证警告信息应该包含有用的描述
        
        **Validates: Requirements 13.6**
        """
        # 生成包含多种问题的数据
        data = []
        for i in range(size):
            if i == size // 3:
                # OHLC违规
                data.append({
                    'timestamp': 1609459200000 + i * 86400000,
                    'open': 50000.0,
                    'high': 49000.0,  # 违规
                    'low': 51000.0,
                    'close': 50500.0,
                    'volume': 1000.0
                })
            elif i == 2 * size // 3:
                # 负成交量
                data.append({
                    'timestamp': 1609459200000 + i * 86400000,
                    'open': 50000.0,
                    'high': 51000.0,
                    'low': 49000.0,
                    'close': 50500.0,
                    'volume': -1000.0  # 违规
                })
            else:
                # 正常数据
                data.append({
                    'timestamp': 1609459200000 + i * 86400000,
                    'open': 50000.0,
                    'high': 51000.0,
                    'low': 49000.0,
                    'close': 50500.0,
                    'volume': 1000.0
                })
        
        df = pd.DataFrame(data)
        db = DatabaseConnector()
        warnings = db.validate_data_integrity(df, '1d')
        
        # 验证：警告应该包含描述性信息
        for warning in warnings:
            # 警告应该是非空字符串
            assert len(warning) > 0, "警告应该是非空字符串"
            # 警告应该包含有用的关键词
            assert any(keyword in warning for keyword in ['OHLC', 'violation', 'volume', 'Missing', 'Negative']), \
                f"警告应该包含描述性关键词: {warning}"


class TestEmptyDataFrame:
    """测试空数据框的边界情况"""
    
    def test_empty_dataframe_validation(self):
        """验证空数据框应该返回警告"""
        df = pd.DataFrame()
        db = DatabaseConnector()
        warnings = db.validate_data_integrity(df, '1d')
        
        # 空数据框应该返回警告
        assert len(warnings) > 0, "空数据框应该返回警告"
        assert any('Empty' in w for w in warnings), "应该包含'Empty'关键词"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
