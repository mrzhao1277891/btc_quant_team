#!/usr/bin/env python3
"""
Database Connector for BTC Backtest System
Handles MySQL connection and K-line data retrieval
"""

import mysql.connector
from mysql.connector import pooling
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import logging

# Configure logging
logger = logging.getLogger(__name__)


class DatabaseConnector:
    """
    Database connector for fetching historical K-line data from MySQL.
    
    This class manages MySQL connections using connection pooling and provides
    methods to query K-line data for backtesting purposes.
    
    Attributes:
        config (Dict): Database configuration parameters
        pool (mysql.connector.pooling.MySQLConnectionPool): Connection pool
    """
    
    def __init__(self, host='localhost', port=3306, user='root', 
                 password='', database='btc_assistant', pool_size=5):
        """
        Initialize database connector with connection pooling.
        
        Args:
            host (str): MySQL host address
            port (int): MySQL port number
            user (str): MySQL username
            password (str): MySQL password
            database (str): Database name
            pool_size (int): Connection pool size
        """
        self.config = {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'database': database,
            'charset': 'utf8mb4',
            'pool_name': 'backtest_pool',
            'pool_size': pool_size
        }
        
        # Create connection pool
        try:
            self.pool = pooling.MySQLConnectionPool(**self.config)
            logger.info(f"✅ Database connection pool created: {database}")
        except mysql.connector.Error as e:
            logger.error(f"❌ Failed to create connection pool: {e}")
            raise
    
    def fetch_klines(self, symbol: str, timeframe: str, 
                     start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Query K-line data for specified time range and timeframe.
        
        This method retrieves OHLCV data from the klines table and returns it
        sorted by timestamp in ascending order.
        
        Args:
            symbol (str): Trading symbol (e.g., 'BTCUSDT')
            timeframe (str): Timeframe (e.g., '1m', '1w', '1d', '4h')
            start_date (datetime): Start date for data query
            end_date (datetime): End date for data query
        
        Returns:
            pd.DataFrame: K-line data with columns:
                - timestamp: Unix timestamp in milliseconds
                - open: Opening price
                - high: Highest price
                - low: Lowest price
                - close: Closing price
                - volume: Trading volume
        
        Raises:
            ValueError: If requested data does not exist
            mysql.connector.Error: If database query fails
        """
        connection = None
        cursor = None
        
        try:
            # Get connection from pool
            connection = self.pool.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            # Convert datetime to timestamp (milliseconds)
            start_timestamp = int(start_date.timestamp() * 1000)
            end_timestamp = int(end_date.timestamp() * 1000)
            
            # Query to fetch K-line data with technical indicators
            query = """
                SELECT 
                    timestamp,
                    open,
                    high,
                    low,
                    close,
                    volume,
                    ema7,
                    ema25,
                    ema50,
                    ema12,
                    ma5,
                    ma10,
                    dif,
                    dea,
                    macd,
                    rsi14,
                    rsi6,
                    boll_up,
                    boll_md,
                    boll_dn,
                    atr
                FROM klines
                WHERE symbol = %s
                    AND timeframe = %s
                    AND timestamp >= %s
                    AND timestamp <= %s
                ORDER BY timestamp ASC
            """
            
            cursor.execute(query, (symbol, timeframe, start_timestamp, end_timestamp))
            results = cursor.fetchall()
            
            if not results:
                error_msg = (
                    f"No data found for {symbol} {timeframe} "
                    f"between {start_date} and {end_date}"
                )
                logger.warning(error_msg)
                raise ValueError(error_msg)
            
            # Convert to DataFrame
            df = pd.DataFrame(results)
            
            # Ensure timestamp is sorted in ascending order
            df = df.sort_values('timestamp', ascending=True).reset_index(drop=True)
            
            logger.info(
                f"✅ Fetched {len(df)} K-lines for {symbol} {timeframe} "
                f"from {start_date} to {end_date}"
            )
            
            return df
            
        except mysql.connector.Error as e:
            logger.error(f"❌ Database query failed: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
    def get_available_date_range(self, symbol: str, timeframe: str) -> Tuple[datetime, datetime]:
        """
        Get the available date range for a symbol and timeframe.
        
        Args:
            symbol (str): Trading symbol (e.g., 'BTCUSDT')
            timeframe (str): Timeframe (e.g., '1m', '1w', '1d', '4h')
        
        Returns:
            Tuple[datetime, datetime]: (earliest_date, latest_date)
        
        Raises:
            ValueError: If no data exists for the symbol/timeframe
            mysql.connector.Error: If database query fails
        """
        connection = None
        cursor = None
        
        try:
            # Get connection from pool
            connection = self.pool.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            # Query to get min and max timestamps
            query = """
                SELECT 
                    FROM_UNIXTIME(MIN(timestamp)/1000) as earliest_date,
                    FROM_UNIXTIME(MAX(timestamp)/1000) as latest_date
                FROM klines
                WHERE symbol = %s
                    AND timeframe = %s
            """
            
            cursor.execute(query, (symbol, timeframe))
            result = cursor.fetchone()
            
            if not result or result['earliest_date'] is None:
                error_msg = f"No data available for {symbol} {timeframe}"
                logger.warning(error_msg)
                raise ValueError(error_msg)
            
            earliest_date = result['earliest_date']
            latest_date = result['latest_date']
            
            logger.info(
                f"✅ Available date range for {symbol} {timeframe}: "
                f"{earliest_date} to {latest_date}"
            )
            
            return (earliest_date, latest_date)
            
        except mysql.connector.Error as e:
            logger.error(f"❌ Failed to get date range: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
    def validate_data_integrity(self, df: pd.DataFrame, timeframe: str) -> List[str]:
        """
        Validate data integrity of K-line data.
        
        This method performs the following checks:
        1. Time series continuity (missing timestamps)
        2. OHLC constraints (low <= open, close <= high)
        3. Volume non-negativity
        
        Args:
            df (pd.DataFrame): K-line data with columns: timestamp, open, high, low, close, volume
            timeframe (str): Timeframe (e.g., '1m', '1w', '1d', '4h') for gap detection
        
        Returns:
            List[str]: List of data quality warnings (empty if no issues found)
        """
        warnings = []
        
        if df.empty:
            logger.warning("⚠️ Empty dataframe provided for validation")
            return ["Empty dataframe"]
        
        # 1. Check time series continuity (missing timestamps)
        missing_timestamps = self._check_missing_timestamps(df, timeframe)
        if missing_timestamps:
            warnings.extend(missing_timestamps)
        
        # 2. Validate OHLC constraints
        ohlc_violations = self._validate_ohlc_constraints(df)
        if ohlc_violations:
            warnings.extend(ohlc_violations)
        
        # 3. Validate volume non-negativity
        volume_violations = self._validate_volume(df)
        if volume_violations:
            warnings.extend(volume_violations)
        
        # Log summary
        if warnings:
            logger.warning(f"⚠️ Data quality issues found: {len(warnings)} warnings")
            for warning in warnings:
                logger.warning(f"  - {warning}")
        else:
            logger.info("✅ Data integrity validation passed")
        
        return warnings
    
    def _check_missing_timestamps(self, df: pd.DataFrame, timeframe: str) -> List[str]:
        """
        Check for missing timestamps in the time series.
        
        Args:
            df (pd.DataFrame): K-line data with timestamp column
            timeframe (str): Timeframe for calculating expected interval
        
        Returns:
            List[str]: List of warnings about missing timestamps
        """
        warnings = []
        
        # Define expected intervals in milliseconds for each timeframe
        interval_map = {
            '1m': 30 * 24 * 60 * 60 * 1000,  # 30 days in milliseconds (monthly)
            '1w': 7 * 24 * 60 * 60 * 1000,    # 7 days in milliseconds (weekly)
            '1d': 24 * 60 * 60 * 1000,        # 1 day in milliseconds (daily)
            '4h': 4 * 60 * 60 * 1000,         # 4 hours in milliseconds
        }
        
        expected_interval = interval_map.get(timeframe)
        if not expected_interval:
            logger.warning(f"⚠️ Unknown timeframe: {timeframe}, skipping continuity check")
            return warnings
        
        # Check for gaps in the time series
        timestamps = df['timestamp'].values
        for i in range(1, len(timestamps)):
            gap = timestamps[i] - timestamps[i-1]
            
            # Allow some tolerance (e.g., 10% deviation)
            tolerance = expected_interval * 0.1
            if gap > expected_interval + tolerance:
                # Calculate how many periods are missing
                missing_periods = int((gap - expected_interval) / expected_interval)
                start_time = pd.to_datetime(timestamps[i-1], unit='ms')
                end_time = pd.to_datetime(timestamps[i], unit='ms')
                
                warning = (
                    f"Missing {missing_periods} period(s) in time series: "
                    f"gap between {start_time} and {end_time}"
                )
                warnings.append(warning)
                logger.warning(f"⚠️ {warning}")
        
        return warnings
    
    def _validate_ohlc_constraints(self, df: pd.DataFrame) -> List[str]:
        """
        Validate OHLC constraints: low <= open, close <= high.
        
        Args:
            df (pd.DataFrame): K-line data with open, high, low, close columns
        
        Returns:
            List[str]: List of warnings about OHLC violations
        """
        warnings = []
        
        # Check: low <= open
        low_open_violations = df[df['low'] > df['open']]
        if not low_open_violations.empty:
            for idx, row in low_open_violations.iterrows():
                timestamp = pd.to_datetime(row['timestamp'], unit='ms')
                warning = (
                    f"OHLC violation at {timestamp}: "
                    f"low ({row['low']}) > open ({row['open']})"
                )
                warnings.append(warning)
                logger.error(f"❌ {warning}")
        
        # Check: low <= close
        low_close_violations = df[df['low'] > df['close']]
        if not low_close_violations.empty:
            for idx, row in low_close_violations.iterrows():
                timestamp = pd.to_datetime(row['timestamp'], unit='ms')
                warning = (
                    f"OHLC violation at {timestamp}: "
                    f"low ({row['low']}) > close ({row['close']})"
                )
                warnings.append(warning)
                logger.error(f"❌ {warning}")
        
        # Check: open <= high
        open_high_violations = df[df['open'] > df['high']]
        if not open_high_violations.empty:
            for idx, row in open_high_violations.iterrows():
                timestamp = pd.to_datetime(row['timestamp'], unit='ms')
                warning = (
                    f"OHLC violation at {timestamp}: "
                    f"open ({row['open']}) > high ({row['high']})"
                )
                warnings.append(warning)
                logger.error(f"❌ {warning}")
        
        # Check: close <= high
        close_high_violations = df[df['close'] > df['high']]
        if not close_high_violations.empty:
            for idx, row in close_high_violations.iterrows():
                timestamp = pd.to_datetime(row['timestamp'], unit='ms')
                warning = (
                    f"OHLC violation at {timestamp}: "
                    f"close ({row['close']}) > high ({row['high']})"
                )
                warnings.append(warning)
                logger.error(f"❌ {warning}")
        
        return warnings
    
    def _validate_volume(self, df: pd.DataFrame) -> List[str]:
        """
        Validate that volume values are non-negative.
        
        Args:
            df (pd.DataFrame): K-line data with volume column
        
        Returns:
            List[str]: List of warnings about negative volume
        """
        warnings = []
        
        # Check for negative volume
        negative_volume = df[df['volume'] < 0]
        if not negative_volume.empty:
            for idx, row in negative_volume.iterrows():
                timestamp = pd.to_datetime(row['timestamp'], unit='ms')
                warning = (
                    f"Negative volume at {timestamp}: "
                    f"volume = {row['volume']}"
                )
                warnings.append(warning)
                logger.error(f"❌ {warning}")
        
        return warnings
    
    def close(self):
        """
        Close the connection pool.
        
        Note: This should only be called when shutting down the application.
        Individual connections are automatically returned to the pool.
        """
        # Connection pools don't have a direct close method
        # Connections are automatically managed
        logger.info("Database connector closed")


# Example usage
if __name__ == "__main__":
    # Configure logging for example
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create database connector
    db = DatabaseConnector(
        host='localhost',
        port=3306,
        user='root',
        password='',
        database='btc_assistant'
    )
    
    try:
        # Get available date range
        symbol = 'BTCUSDT'
        timeframe = '1d'
        
        earliest, latest = db.get_available_date_range(symbol, timeframe)
        print(f"\nAvailable data range:")
        print(f"  Earliest: {earliest}")
        print(f"  Latest: {latest}")
        
        # Fetch recent data
        from datetime import timedelta
        end_date = latest
        start_date = end_date - timedelta(days=30)
        
        df = db.fetch_klines(symbol, timeframe, start_date, end_date)
        print(f"\nFetched {len(df)} K-lines")
        print(f"\nFirst 5 rows:")
        print(df.head())
        print(f"\nLast 5 rows:")
        print(df.tail())
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()
