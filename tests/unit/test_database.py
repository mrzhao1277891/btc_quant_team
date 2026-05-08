#!/usr/bin/env python3
"""
Unit tests for DatabaseConnector
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from backend.database import DatabaseConnector


class TestDatabaseConnector:
    """Test suite for DatabaseConnector class"""
    
    @pytest.fixture
    def db_connector(self):
        """Create a DatabaseConnector instance for testing"""
        db = DatabaseConnector(
            host='localhost',
            port=3306,
            user='root',
            password='',
            database='btc_assistant'
        )
        yield db
        db.close()
    
    def test_connection_pool_creation(self, db_connector):
        """Test that connection pool is created successfully"""
        assert db_connector.pool is not None
        assert db_connector.config['database'] == 'btc_assistant'
    
    def test_get_available_date_range(self, db_connector):
        """Test getting available date range for a symbol/timeframe"""
        earliest, latest = db_connector.get_available_date_range('BTCUSDT', '1d')
        
        # Verify both dates are returned
        assert earliest is not None
        assert latest is not None
        
        # Verify earliest is before latest
        assert earliest <= latest
        
        # Verify dates are datetime objects
        assert isinstance(earliest, datetime)
        assert isinstance(latest, datetime)
    
    def test_get_available_date_range_invalid_symbol(self, db_connector):
        """Test that invalid symbol raises ValueError"""
        with pytest.raises(ValueError, match="No data available"):
            db_connector.get_available_date_range('INVALID', '1d')
    
    def test_fetch_klines_basic(self, db_connector):
        """Test fetching K-line data"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=10)
        
        df = db_connector.fetch_klines('BTCUSDT', '1d', start_date, end_date)
        
        # Verify DataFrame is returned
        assert isinstance(df, pd.DataFrame)
        
        # Verify DataFrame is not empty
        assert len(df) > 0
        
        # Verify required columns exist
        required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            assert col in df.columns
    
    def test_fetch_klines_sorted_ascending(self, db_connector):
        """Test that K-line data is sorted by timestamp in ascending order"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        df = db_connector.fetch_klines('BTCUSDT', '1d', start_date, end_date)
        
        # Verify data is sorted in ascending order
        assert df['timestamp'].is_monotonic_increasing
        
        # Verify first timestamp is less than last timestamp
        assert df.iloc[0]['timestamp'] < df.iloc[-1]['timestamp']
    
    def test_fetch_klines_ohlc_constraints(self, db_connector):
        """Test that OHLC data satisfies basic constraints"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=10)
        
        df = db_connector.fetch_klines('BTCUSDT', '1d', start_date, end_date)
        
        # Verify OHLC constraints: low <= open, close <= high
        assert (df['low'] <= df['open']).all()
        assert (df['low'] <= df['close']).all()
        assert (df['open'] <= df['high']).all()
        assert (df['close'] <= df['high']).all()
        
        # Verify volume is non-negative
        assert (df['volume'] >= 0).all()
    
    def test_fetch_klines_no_data(self, db_connector):
        """Test that fetching non-existent data raises ValueError"""
        # Use a date range far in the future
        start_date = datetime(2030, 1, 1)
        end_date = datetime(2030, 1, 31)
        
        with pytest.raises(ValueError, match="No data found"):
            db_connector.fetch_klines('BTCUSDT', '1d', start_date, end_date)
    
    def test_fetch_klines_multiple_timeframes(self, db_connector):
        """Test fetching data for different timeframes"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        timeframes = ['1d', '4h', '1w']
        
        for timeframe in timeframes:
            try:
                df = db_connector.fetch_klines('BTCUSDT', timeframe, start_date, end_date)
                assert isinstance(df, pd.DataFrame)
                assert len(df) > 0
            except ValueError:
                # Some timeframes might not have data, which is acceptable
                pass
    
    def test_fetch_klines_date_range_filtering(self, db_connector):
        """Test that date range filtering works correctly"""
        # Get available range first
        earliest, latest = db_connector.get_available_date_range('BTCUSDT', '1d')
        
        # Query a subset of the available range
        mid_date = earliest + (latest - earliest) / 2
        start_date = mid_date - timedelta(days=5)
        end_date = mid_date + timedelta(days=5)
        
        df = db_connector.fetch_klines('BTCUSDT', '1d', start_date, end_date)
        
        # Verify all timestamps are within the requested range
        start_timestamp = int(start_date.timestamp() * 1000)
        end_timestamp = int(end_date.timestamp() * 1000)
        
        assert (df['timestamp'] >= start_timestamp).all()
        assert (df['timestamp'] <= end_timestamp).all()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
