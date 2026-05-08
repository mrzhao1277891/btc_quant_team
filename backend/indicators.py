"""
技术指标计算模块

该模块提供各种技术指标的计算方法，包括EMA、RSI、MACD、布林带和ATR。
所有计算使用Pandas进行向量化操作以提高性能。
"""

import pandas as pd
import numpy as np
from typing import Tuple


class IndicatorCalculator:
    """技术指标计算器类
    
    提供静态方法计算各种技术指标。所有方法都使用向量化操作，
    并正确处理数据不足的情况（返回NaN）。
    """
    
    @staticmethod
    def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
        """计算指数移动平均线（EMA）
        
        使用公式: EMA_today = (Price_today * K) + (EMA_yesterday * (1 - K))
        其中 K = 2 / (N + 1)
        
        Args:
            prices: 价格序列（通常是收盘价）
            period: EMA周期（例如：7, 25, 50）
            
        Returns:
            pd.Series: EMA值序列。当数据不足时，前面的值为NaN
            
        Examples:
            >>> prices = pd.Series([100, 102, 101, 103, 105])
            >>> ema = IndicatorCalculator.calculate_ema(prices, period=3)
        """
        if len(prices) == 0:
            return pd.Series(dtype=float)
        
        if period <= 0:
            raise ValueError(f"Period must be positive, got {period}")
        
        # 使用Pandas的ewm方法计算EMA
        # span参数对应于N，adjust=False使用递归公式
        # min_periods确保至少有period个数据点才开始计算
        ema = prices.ewm(span=period, adjust=False, min_periods=period).mean()
        
        return ema
    
    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """计算相对强弱指标（RSI）
        
        使用公式: RSI = 100 - (100 / (1 + RS))
        其中 RS = Average_Gain / Average_Loss
        
        Average_Gain 和 Average_Loss 使用指数移动平均计算。
        
        Args:
            prices: 价格序列（通常是收盘价）
            period: RSI周期（默认14）
            
        Returns:
            pd.Series: RSI值序列（0-100之间）。当数据不足时，前面的值为NaN
            
        Examples:
            >>> prices = pd.Series([44, 44.34, 44.09, 43.61, 44.33, 44.83])
            >>> rsi = IndicatorCalculator.calculate_rsi(prices, period=5)
        """
        if len(prices) == 0:
            return pd.Series(dtype=float)
        
        if period <= 0:
            raise ValueError(f"Period must be positive, got {period}")
        
        # 计算价格变化
        delta = prices.diff()
        
        # 分离涨跌
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        
        # 计算平均涨跌（使用EMA）
        # 第一个平均值使用简单平均，之后使用指数移动平均
        avg_gain = gain.ewm(span=period, adjust=False, min_periods=period).mean()
        avg_loss = loss.ewm(span=period, adjust=False, min_periods=period).mean()
        
        # 计算RS和RSI
        # 避免除以零：当avg_loss为0时，RSI为100
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        # 处理特殊情况：当avg_loss为0时（没有下跌），RSI应该是100
        rsi = rsi.fillna(100)
        
        return rsi
    
    @staticmethod
    def calculate_macd(prices: pd.Series, 
                      fast_period: int = 12, 
                      slow_period: int = 26, 
                      signal_period: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """计算MACD指标
        
        MACD (Moving Average Convergence Divergence) 包含三个组件：
        - DIF (快线): EMA12 - EMA26
        - DEA (慢线/信号线): EMA9(DIF)
        - MACD柱状图: DIF - DEA
        
        Args:
            prices: 价格序列（通常是收盘价）
            fast_period: 快速EMA周期（默认12）
            slow_period: 慢速EMA周期（默认26）
            signal_period: 信号线EMA周期（默认9）
            
        Returns:
            Tuple[pd.Series, pd.Series, pd.Series]: (DIF, DEA, MACD柱状图)
            
        Examples:
            >>> prices = pd.Series([...])
            >>> dif, dea, macd = IndicatorCalculator.calculate_macd(prices)
        """
        if len(prices) == 0:
            empty = pd.Series(dtype=float)
            return empty, empty, empty
        
        # 计算快速和慢速EMA
        ema_fast = IndicatorCalculator.calculate_ema(prices, fast_period)
        ema_slow = IndicatorCalculator.calculate_ema(prices, slow_period)
        
        # 计算DIF（快线）
        dif = ema_fast - ema_slow
        
        # 计算DEA（信号线）
        dea = IndicatorCalculator.calculate_ema(dif, signal_period)
        
        # 计算MACD柱状图
        macd_histogram = dif - dea
        
        return dif, dea, macd_histogram
    
    @staticmethod
    def calculate_bollinger_bands(prices: pd.Series, 
                                  period: int = 20, 
                                  std_dev: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """计算布林带
        
        布林带包含三条线：
        - 中轨: SMA(period)
        - 上轨: 中轨 + (std_dev * 标准差)
        - 下轨: 中轨 - (std_dev * 标准差)
        
        Args:
            prices: 价格序列（通常是收盘价）
            period: 移动平均周期（默认20）
            std_dev: 标准差倍数（默认2.0）
            
        Returns:
            Tuple[pd.Series, pd.Series, pd.Series]: (上轨, 中轨, 下轨)
            
        Examples:
            >>> prices = pd.Series([...])
            >>> upper, middle, lower = IndicatorCalculator.calculate_bollinger_bands(prices)
        """
        if len(prices) == 0:
            empty = pd.Series(dtype=float)
            return empty, empty, empty
        
        if period <= 0:
            raise ValueError(f"Period must be positive, got {period}")
        
        # 计算中轨（简单移动平均）
        middle = prices.rolling(window=period, min_periods=period).mean()
        
        # 计算标准差
        std = prices.rolling(window=period, min_periods=period).std()
        
        # 计算上轨和下轨
        upper = middle + (std_dev * std)
        lower = middle - (std_dev * std)
        
        return upper, middle, lower
    
    @staticmethod
    def calculate_atr(high: pd.Series, 
                     low: pd.Series, 
                     close: pd.Series, 
                     period: int = 14) -> pd.Series:
        """计算平均真实波幅（ATR）
        
        ATR = EMA(period, True_Range)
        其中 True_Range = max(High - Low, abs(High - Previous_Close), abs(Low - Previous_Close))
        
        Args:
            high: 最高价序列
            low: 最低价序列
            close: 收盘价序列
            period: ATR周期（默认14）
            
        Returns:
            pd.Series: ATR值序列。当数据不足时，前面的值为NaN
            
        Examples:
            >>> high = pd.Series([...])
            >>> low = pd.Series([...])
            >>> close = pd.Series([...])
            >>> atr = IndicatorCalculator.calculate_atr(high, low, close)
        """
        if len(high) == 0 or len(low) == 0 or len(close) == 0:
            return pd.Series(dtype=float)
        
        if period <= 0:
            raise ValueError(f"Period must be positive, got {period}")
        
        # 计算True Range的三个组成部分
        tr1 = high - low  # 当日最高最低价差
        tr2 = (high - close.shift(1)).abs()  # 当日最高价与前日收盘价差的绝对值
        tr3 = (low - close.shift(1)).abs()   # 当日最低价与前日收盘价差的绝对值
        
        # True Range是三者中的最大值
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # 计算ATR（True Range的EMA）
        atr = IndicatorCalculator.calculate_ema(true_range, period)
        
        return atr
    
    def calculate_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算所有技术指标并添加到DataFrame
        
        该方法会向输入的DataFrame添加以下列：
        - EMA7, EMA25, EMA50
        - RSI14, RSI6
        - MACD_DIF, MACD_DEA, MACD_Histogram
        - Bollinger_Upper, Bollinger_Middle, Bollinger_Lower
        - ATR
        
        Args:
            df: 包含OHLCV数据的DataFrame，必须包含列：
                'close', 'high', 'low', 'volume'
                
        Returns:
            pd.DataFrame: 添加了所有指标列的DataFrame（原地修改）
            
        Raises:
            ValueError: 如果DataFrame缺少必需的列
            
        Examples:
            >>> df = pd.DataFrame({
            ...     'close': [...],
            ...     'high': [...],
            ...     'low': [...],
            ...     'volume': [...]
            ... })
            >>> calculator = IndicatorCalculator()
            >>> df = calculator.calculate_all_indicators(df)
        """
        # 验证必需的列
        required_columns = ['close', 'high', 'low', 'volume']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"DataFrame missing required columns: {missing_columns}")
        
        # 创建副本以避免修改原始数据
        result_df = df.copy()
        
        # 计算EMA
        result_df['EMA7'] = self.calculate_ema(df['close'], 7)
        result_df['EMA25'] = self.calculate_ema(df['close'], 25)
        result_df['EMA50'] = self.calculate_ema(df['close'], 50)
        
        # 计算RSI
        result_df['RSI14'] = self.calculate_rsi(df['close'], 14)
        result_df['RSI6'] = self.calculate_rsi(df['close'], 6)
        
        # 计算MACD
        dif, dea, macd = self.calculate_macd(df['close'])
        result_df['MACD_DIF'] = dif
        result_df['MACD_DEA'] = dea
        result_df['MACD_Histogram'] = macd
        
        # 计算布林带
        upper, middle, lower = self.calculate_bollinger_bands(df['close'])
        result_df['Bollinger_Upper'] = upper
        result_df['Bollinger_Middle'] = middle
        result_df['Bollinger_Lower'] = lower
        
        # 计算ATR
        result_df['ATR'] = self.calculate_atr(df['high'], df['low'], df['close'])
        
        return result_df
