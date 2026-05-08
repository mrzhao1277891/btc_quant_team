#!/usr/bin/env python3
"""
Data Integrity Validation Demo

This script demonstrates the data integrity validation features of the DatabaseConnector.
It shows how to:
1. Validate OHLC constraints
2. Detect missing timestamps in time series
3. Validate volume non-negativity
4. Handle data quality warnings
"""

import sys
import os
import pandas as pd
from datetime import datetime, timedelta

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.database import DatabaseConnector
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def demo_valid_data():
    """Demonstrate validation with valid data."""
    print("\n" + "="*60)
    print("Demo 1: Valid Data")
    print("="*60)
    
    # Create valid K-line data
    day_ms = 24 * 60 * 60 * 1000
    base_timestamp = 1000000000000
    
    data = {
        'timestamp': [base_timestamp + i * day_ms for i in range(5)],
        'open': [100.0, 101.0, 102.0, 103.0, 104.0],
        'high': [105.0, 106.0, 107.0, 108.0, 109.0],
        'low': [95.0, 96.0, 97.0, 98.0, 99.0],
        'close': [103.0, 104.0, 105.0, 106.0, 107.0],
        'volume': [1000.0, 1100.0, 1200.0, 1300.0, 1400.0]
    }
    df = pd.DataFrame(data)
    
    print("\nSample data:")
    print(df.head())
    
    # Create database connector
    try:
        db = DatabaseConnector(
            host='localhost',
            port=3306,
            user='root',
            password='',
            database='btc_assistant'
        )
        
        # Validate data
        warnings = db.validate_data_integrity(df, '1d')
        
        if warnings:
            print(f"\n⚠️ Found {len(warnings)} data quality issues:")
            for warning in warnings:
                print(f"  - {warning}")
        else:
            print("\n✅ All data integrity checks passed!")
        
        db.close()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


def demo_ohlc_violations():
    """Demonstrate detection of OHLC constraint violations."""
    print("\n" + "="*60)
    print("Demo 2: OHLC Constraint Violations")
    print("="*60)
    
    # Create data with OHLC violations
    data = {
        'timestamp': [1000000000000, 1000086400000, 1000172800000],
        'open': [100.0, 106.0, 102.0],    # Row 2: open > high
        'high': [105.0, 105.0, 107.0],
        'low': [101.0, 96.0, 97.0],       # Row 1: low > open
        'close': [103.0, 104.0, 108.0],   # Row 3: close > high
        'volume': [1000.0, 1100.0, 1200.0]
    }
    df = pd.DataFrame(data)
    
    print("\nSample data with violations:")
    print(df)
    
    try:
        db = DatabaseConnector(
            host='localhost',
            port=3306,
            user='root',
            password='',
            database='btc_assistant'
        )
        
        # Validate data
        warnings = db.validate_data_integrity(df, '1d')
        
        print(f"\n⚠️ Found {len(warnings)} OHLC violations:")
        for warning in warnings:
            print(f"  - {warning}")
        
        db.close()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


def demo_missing_timestamps():
    """Demonstrate detection of missing timestamps."""
    print("\n" + "="*60)
    print("Demo 3: Missing Timestamps Detection")
    print("="*60)
    
    # Create data with gaps in time series
    day_ms = 24 * 60 * 60 * 1000
    base_timestamp = 1000000000000
    
    data = {
        'timestamp': [
            base_timestamp,
            base_timestamp + day_ms,
            base_timestamp + 4 * day_ms,  # Gap: missing 2 days
            base_timestamp + 5 * day_ms,
            base_timestamp + 10 * day_ms  # Gap: missing 4 days
        ],
        'open': [100.0, 101.0, 102.0, 103.0, 104.0],
        'high': [105.0, 106.0, 107.0, 108.0, 109.0],
        'low': [95.0, 96.0, 97.0, 98.0, 99.0],
        'close': [103.0, 104.0, 105.0, 106.0, 107.0],
        'volume': [1000.0, 1100.0, 1200.0, 1300.0, 1400.0]
    }
    df = pd.DataFrame(data)
    
    # Convert timestamps to readable format for display
    df_display = df.copy()
    df_display['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    print("\nSample data with gaps:")
    print(df_display)
    
    try:
        db = DatabaseConnector(
            host='localhost',
            port=3306,
            user='root',
            password='',
            database='btc_assistant'
        )
        
        # Validate data
        warnings = db.validate_data_integrity(df, '1d')
        
        print(f"\n⚠️ Found {len(warnings)} time series gaps:")
        for warning in warnings:
            print(f"  - {warning}")
        
        db.close()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


def demo_negative_volume():
    """Demonstrate detection of negative volume."""
    print("\n" + "="*60)
    print("Demo 4: Negative Volume Detection")
    print("="*60)
    
    # Create data with negative volume
    day_ms = 24 * 60 * 60 * 1000
    base_timestamp = 1000000000000
    
    data = {
        'timestamp': [base_timestamp + i * day_ms for i in range(5)],
        'open': [100.0, 101.0, 102.0, 103.0, 104.0],
        'high': [105.0, 106.0, 107.0, 108.0, 109.0],
        'low': [95.0, 96.0, 97.0, 98.0, 99.0],
        'close': [103.0, 104.0, 105.0, 106.0, 107.0],
        'volume': [1000.0, -100.0, 1200.0, -50.0, 1400.0]  # Negative volumes
    }
    df = pd.DataFrame(data)
    
    print("\nSample data with negative volumes:")
    print(df)
    
    try:
        db = DatabaseConnector(
            host='localhost',
            port=3306,
            user='root',
            password='',
            database='btc_assistant'
        )
        
        # Validate data
        warnings = db.validate_data_integrity(df, '1d')
        
        print(f"\n⚠️ Found {len(warnings)} volume violations:")
        for warning in warnings:
            print(f"  - {warning}")
        
        db.close()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


def demo_multiple_issues():
    """Demonstrate detection of multiple data quality issues."""
    print("\n" + "="*60)
    print("Demo 5: Multiple Data Quality Issues")
    print("="*60)
    
    # Create data with multiple issues
    day_ms = 24 * 60 * 60 * 1000
    base_timestamp = 1000000000000
    
    data = {
        'timestamp': [
            base_timestamp,
            base_timestamp + day_ms,
            base_timestamp + 5 * day_ms  # Gap: missing 3 days
        ],
        'open': [100.0, 106.0, 102.0],    # Row 2: open > high
        'high': [105.0, 105.0, 107.0],
        'low': [101.0, 96.0, 97.0],       # Row 1: low > open
        'close': [103.0, 104.0, 105.0],
        'volume': [1000.0, -100.0, 1200.0]  # Row 2: negative volume
    }
    df = pd.DataFrame(data)
    
    print("\nSample data with multiple issues:")
    print(df)
    
    try:
        db = DatabaseConnector(
            host='localhost',
            port=3306,
            user='root',
            password='',
            database='btc_assistant'
        )
        
        # Validate data
        warnings = db.validate_data_integrity(df, '1d')
        
        print(f"\n⚠️ Found {len(warnings)} total data quality issues:")
        for i, warning in enumerate(warnings, 1):
            print(f"  {i}. {warning}")
        
        db.close()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


def main():
    """Run all demos."""
    print("\n" + "="*60)
    print("Data Integrity Validation Demo")
    print("="*60)
    
    demo_valid_data()
    demo_ohlc_violations()
    demo_missing_timestamps()
    demo_negative_volume()
    demo_multiple_issues()
    
    print("\n" + "="*60)
    print("Demo Complete!")
    print("="*60)


if __name__ == "__main__":
    main()
