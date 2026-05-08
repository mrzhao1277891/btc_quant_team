#!/usr/bin/env python3
"""
Unit tests for data integrity validation in DatabaseConnector.
Tests OHLC constraints, time series continuity, and volume validation.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.database import DatabaseConnector


class TestDataIntegrityValidation:
    """Test suite for data integrity validation methods."""
    
    @pytest.fixture
    def db_connector(self):
        """Create a DatabaseConnector instance for testing."""
        # Note: We don't need actual DB connection for validation tests
        # We'll test the validation methods directly
        try:
            db = DatabaseConnector(
                host='localhost',
                port=3306,
                user='root',
                password='',
                database='btc_assistant'
            )
            return db
        except Exception as e:
            pytest.skip(f"Database connection not available: {e}")
    
    def test_validate_empty_dataframe(self, db_connector):
        """Test validation with empty dataframe."""
        df = pd.DataFrame()
        warnings = db_connector.validate_data_integrity(df, '1d')
        
        assert len(warnings) == 1
        assert "Empty dataframe" in warnings[0]
    
    def test_validate_valid_data(self, db_connector):
        """Test validation with valid OHLC data."""
        # Create valid data
        data = {
            'timestamp': [1000000000000, 1000086400000, 1000172800000],  # 1 day intervals
            'open': [100.0, 101.0, 102.0],
            'high': [105.0, 106.0, 107.0],
            'low': [95.0, 96.0, 97.0],
            'close': [103.0, 104.0, 105.0],
            'volume': [1000.0, 1100.0, 1200.0]
        }
        df = pd.DataFrame(data)
        
        warnings = db_connector.validate_data_integrity(df, '1d')
        
        assert len(warnings) == 0, f"Expected no warnings, got: {warnings}"
    
    def test_detect_low_greater_than_open(self, db_connector):
        """Test detection of low > open violation."""
        data = {
            'timestamp': [1000000000000],
            'open': [100.0],
            'high': [105.0],
            'low': [101.0],  # Invalid: low > open
            'close': [103.0],
            'volume': [1000.0]
        }
        df = pd.DataFrame(data)
        
        warnings = db_connector.validate_data_integrity(df, '1d')
        
        assert len(warnings) > 0
        assert any('low' in w.lower() and 'open' in w.lower() for w in warnings)
    
    def test_detect_low_greater_than_close(self, db_connector):
        """Test detection of low > close violation."""
        data = {
            'timestamp': [1000000000000],
            'open': [100.0],
            'high': [105.0],
            'low': [104.0],  # Invalid: low > close
            'close': [103.0],
            'volume': [1000.0]
        }
        df = pd.DataFrame(data)
        
        warnings = db_connector.validate_data_integrity(df, '1d')
        
        assert len(warnings) > 0
        assert any('low' in w.lower() and 'close' in w.lower() for w in warnings)
    
    def test_detect_open_greater_than_high(self, db_connector):
        """Test detection of open > high violation."""
        data = {
            'timestamp': [1000000000000],
            'open': [106.0],  # Invalid: open > high
            'high': [105.0],
            'low': [95.0],
            'close': [103.0],
            'volume': [1000.0]
        }
        df = pd.DataFrame(data)
        
        warnings = db_connector.validate_data_integrity(df, '1d')
        
        assert len(warnings) > 0
        assert any('open' in w.lower() and 'high' in w.lower() for w in warnings)
    
    def test_detect_close_greater_than_high(self, db_connector):
        """Test detection of close > high violation."""
        data = {
            'timestamp': [1000000000000],
            'open': [100.0],
            'high': [105.0],
            'low': [95.0],
            'close': [106.0],  # Invalid: close > high
            'volume': [1000.0]
        }
        df = pd.DataFrame(data)
        
        warnings = db_connector.validate_data_integrity(df, '1d')
        
        assert len(warnings) > 0
        assert any('close' in w.lower() and 'high' in w.lower() for w in warnings)
    
    def test_detect_negative_volume(self, db_connector):
        """Test detection of negative volume."""
        data = {
            'timestamp': [1000000000000],
            'open': [100.0],
            'high': [105.0],
            'low': [95.0],
            'close': [103.0],
            'volume': [-100.0]  # Invalid: negative volume
        }
        df = pd.DataFrame(data)
        
        warnings = db_connector.validate_data_integrity(df, '1d')
        
        assert len(warnings) > 0
        assert any('negative volume' in w.lower() for w in warnings)
    
    def test_detect_missing_timestamps_daily(self, db_connector):
        """Test detection of missing timestamps in daily data."""
        # Create data with a gap (missing 2 days)
        day_ms = 24 * 60 * 60 * 1000
        data = {
            'timestamp': [
                1000000000000,
                1000000000000 + day_ms,
                1000000000000 + 4 * day_ms  # Gap: missing days 2 and 3
            ],
            'open': [100.0, 101.0, 102.0],
            'high': [105.0, 106.0, 107.0],
            'low': [95.0, 96.0, 97.0],
            'close': [103.0, 104.0, 105.0],
            'volume': [1000.0, 1100.0, 1200.0]
        }
        df = pd.DataFrame(data)
        
        warnings = db_connector.validate_data_integrity(df, '1d')
        
        assert len(warnings) > 0
        assert any('missing' in w.lower() and 'period' in w.lower() for w in warnings)
    
    def test_detect_missing_timestamps_4h(self, db_connector):
        """Test detection of missing timestamps in 4-hour data."""
        # Create data with a gap (missing 2 periods)
        hour_4_ms = 4 * 60 * 60 * 1000
        data = {
            'timestamp': [
                1000000000000,
                1000000000000 + hour_4_ms,
                1000000000000 + 4 * hour_4_ms  # Gap: missing 2 periods
            ],
            'open': [100.0, 101.0, 102.0],
            'high': [105.0, 106.0, 107.0],
            'low': [95.0, 96.0, 97.0],
            'close': [103.0, 104.0, 105.0],
            'volume': [1000.0, 1100.0, 1200.0]
        }
        df = pd.DataFrame(data)
        
        warnings = db_connector.validate_data_integrity(df, '4h')
        
        assert len(warnings) > 0
        assert any('missing' in w.lower() and 'period' in w.lower() for w in warnings)
    
    def test_multiple_violations(self, db_connector):
        """Test detection of multiple violations in the same dataset."""
        data = {
            'timestamp': [1000000000000, 1000086400000],
            'open': [100.0, 106.0],  # Second row: open > high
            'high': [105.0, 105.0],
            'low': [101.0, 95.0],    # First row: low > open
            'close': [103.0, 103.0],
            'volume': [1000.0, -100.0]  # Second row: negative volume
        }
        df = pd.DataFrame(data)
        
        warnings = db_connector.validate_data_integrity(df, '1d')
        
        # Should detect at least 3 violations
        assert len(warnings) >= 3
    
    def test_boundary_values(self, db_connector):
        """Test with boundary values (equal values)."""
        # All OHLC values equal - should be valid
        data = {
            'timestamp': [1000000000000],
            'open': [100.0],
            'high': [100.0],
            'low': [100.0],
            'close': [100.0],
            'volume': [0.0]  # Zero volume is valid
        }
        df = pd.DataFrame(data)
        
        warnings = db_connector.validate_data_integrity(df, '1d')
        
        assert len(warnings) == 0, f"Expected no warnings for boundary values, got: {warnings}"
    
    def test_unknown_timeframe(self, db_connector):
        """Test with unknown timeframe (should skip continuity check)."""
        data = {
            'timestamp': [1000000000000, 2000000000000],  # Large gap
            'open': [100.0, 101.0],
            'high': [105.0, 106.0],
            'low': [95.0, 96.0],
            'close': [103.0, 104.0],
            'volume': [1000.0, 1100.0]
        }
        df = pd.DataFrame(data)
        
        # Use unknown timeframe
        warnings = db_connector.validate_data_integrity(df, '15m')
        
        # Should not detect missing timestamps (unknown timeframe)
        # But should still validate OHLC and volume
        assert all('missing' not in w.lower() for w in warnings)


class TestOHLCConstraints:
    """Focused tests for OHLC constraint validation."""
    
    @pytest.fixture
    def db_connector(self):
        """Create a DatabaseConnector instance for testing."""
        try:
            db = DatabaseConnector(
                host='localhost',
                port=3306,
                user='root',
                password='',
                database='btc_assistant'
            )
            return db
        except Exception as e:
            pytest.skip(f"Database connection not available: {e}")
    
    def test_valid_ohlc_constraints(self, db_connector):
        """Test that valid OHLC data passes all constraints."""
        data = {
            'timestamp': [1000000000000],
            'open': [100.0],
            'high': [110.0],
            'low': [90.0],
            'close': [105.0],
            'volume': [1000.0]
        }
        df = pd.DataFrame(data)
        
        warnings = db_connector._validate_ohlc_constraints(df)
        
        assert len(warnings) == 0
    
    def test_all_ohlc_violations(self, db_connector):
        """Test data that violates all OHLC constraints."""
        data = {
            'timestamp': [1000000000000],
            'open': [120.0],  # open > high
            'high': [100.0],
            'low': [110.0],   # low > open, low > close
            'close': [105.0], # close > high
            'volume': [1000.0]
        }
        df = pd.DataFrame(data)
        
        warnings = db_connector._validate_ohlc_constraints(df)
        
        # Should detect multiple violations
        assert len(warnings) >= 3


class TestVolumeValidation:
    """Focused tests for volume validation."""
    
    @pytest.fixture
    def db_connector(self):
        """Create a DatabaseConnector instance for testing."""
        try:
            db = DatabaseConnector(
                host='localhost',
                port=3306,
                user='root',
                password='',
                database='btc_assistant'
            )
            return db
        except Exception as e:
            pytest.skip(f"Database connection not available: {e}")
    
    def test_valid_volume(self, db_connector):
        """Test that non-negative volumes pass validation."""
        data = {
            'timestamp': [1000000000000, 1000086400000, 1000172800000],
            'open': [100.0, 101.0, 102.0],
            'high': [105.0, 106.0, 107.0],
            'low': [95.0, 96.0, 97.0],
            'close': [103.0, 104.0, 105.0],
            'volume': [0.0, 1000.0, 999999.99]  # All valid
        }
        df = pd.DataFrame(data)
        
        warnings = db_connector._validate_volume(df)
        
        assert len(warnings) == 0
    
    def test_negative_volume(self, db_connector):
        """Test detection of negative volume."""
        data = {
            'timestamp': [1000000000000, 1000086400000],
            'open': [100.0, 101.0],
            'high': [105.0, 106.0],
            'low': [95.0, 96.0],
            'close': [103.0, 104.0],
            'volume': [1000.0, -0.01]  # Second row has negative volume
        }
        df = pd.DataFrame(data)
        
        warnings = db_connector._validate_volume(df)
        
        assert len(warnings) == 1
        assert 'negative volume' in warnings[0].lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
