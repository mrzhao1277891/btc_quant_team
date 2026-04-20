#!/usr/bin/env python3
"""
数据更新器 - 从API获取最新数据并更新数据库
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import requests
import logging
from typing import Dict, List, Optional, Any, Tuple
import json
from pathlib import Path

class DataUpdater:
    """数据更新器"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        初始化数据更新器
        
        参数:
            db_path: 数据库路径
        """
        self.db_path = db_path or "/home/francis/.openclaw/workspace/crypto_analyzer/data/ultra_light.db"
        
        # Binance API配置
        self.binance_base_url = "https://api.binance.com/api/v3"
        
        # 请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("数据更新器初始化完成")
    
    def check_freshness(self, symbol: str, timeframe: str, threshold_hours: float = 24) -> Tuple[bool, Dict[str, Any]]:
        """
        检查数据新鲜度
        
        参数:
            symbol: 交易对符号
            timeframe: 时间框架
            threshold_hours: 新鲜度阈值（小时）
        
        返回:
            Tuple[是否过时, 详细信息]
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取最新数据时间
            query = f"""
            SELECT MAX(timestamp) as latest_ts, COUNT(*) as count
            FROM klines 
            WHERE symbol = ? AND timeframe = ?
            """
            
            cursor.execute(query, (symbol, timeframe))
            result = cursor.fetchone()
            conn.close()
            
            if not result or result[0] is None:
                # 没有数据
                return True, {
                    'has_data': False,
                    'latest_timestamp': None,
                    'data_count': 0,
                    'is_stale': True,
                    'reason': 'no_data'
                }
            
            latest_ts = result[0]
            data_count = result[1]
            
            latest_time = datetime.fromtimestamp(latest_ts / 1000)
            now = datetime.now()
            age_hours = (now - latest_time).total_seconds() / 3600
            
            is_stale = age_hours > threshold_hours
            
            return is_stale, {
                'has_data': True,
                'latest_timestamp': latest_ts,
                'latest_time': latest_time.isoformat(),
                'data_count': data_count,
                'age_hours': age_hours,
                'threshold_hours': threshold_hours,
                'is_stale': is_stale,
                'reason': 'stale' if is_stale else 'fresh'
            }
            
        except Exception as e:
            self.logger.error(f"检查新鲜度失败: {symbol} ({timeframe}) - {e}")
            return True, {
                'has_data': False,
                'error': str(e),
                'is_stale': True,
                'reason': 'error'
            }
    
    def fetch_klines_from_binance(self, symbol: str, timeframe: str, limit: int = 500) -> Optional[pd.DataFrame]:
        """
        从Binance API获取K线数据
        
        参数:
            symbol: 交易对符号
            timeframe: 时间框架
            limit: 获取的数据条数
        
        返回:
            DataFrame: K线数据
        """
        try:
            # Binance API时间框架映射
            timeframe_map = {
                '1h': '1h',
                '4h': '4h',
                '1d': '1d',
                '1w': '1w',
                '1M': '1M'
            }
            
            binance_timeframe = timeframe_map.get(timeframe)
            if not binance_timeframe:
                self.logger.error(f"不支持的时间框架: {timeframe}")
                return None
            
            # 构建API URL
            url = f"{self.binance_base_url}/klines"
            params = {
                'symbol': symbol.replace('USDT', 'USDT'),  # 确保格式正确
                'interval': binance_timeframe,
                'limit': min(limit, 1000)  # Binance API限制
            }
            
            self.logger.info(f"从Binance获取数据: {symbol} ({timeframe}), 限制: {params['limit']}")
            
            response = requests.get(url, params=params, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if not data:
                self.logger.warning(f"从Binance获取到空数据: {symbol} ({timeframe})")
                return None
            
            # 解析数据
            columns = [
                'open_time', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ]
            
            df = pd.DataFrame(data, columns=columns)
            
            # 转换数据类型
            numeric_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            df['open_time'] = pd.to_numeric(df['open_time'], errors='coerce')
            
            # 重命名列以匹配数据库
            df = df.rename(columns={'open_time': 'timestamp'})
            
            # 添加必要列
            df['symbol'] = symbol
            df['timeframe'] = timeframe
            
            self.logger.info(f"从Binance获取数据成功: {symbol} ({timeframe}) - {len(df)} 条")
            
            return df[['timestamp', 'symbol', 'timeframe', 'open', 'high', 'low', 'close', 'volume']]
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Binance API请求失败: {symbol} ({timeframe}) - {e}")
            return None
        except Exception as e:
            self.logger.error(f"处理Binance数据失败: {symbol} ({timeframe}) - {e}")
            return None
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算技术指标
        
        参数:
            df: 包含价格数据的DataFrame
        
        返回:
            DataFrame: 添加了技术指标的数据
        """
        if df.empty:
            return df
        
        try:
            # 确保数据按时间排序
            df = df.sort_values('timestamp')
            
            # 计算移动平均线
            close_prices = df['close'].values
            
            # EMA计算函数
            def calculate_ema(prices, period):
                if len(prices) < period:
                    return np.full(len(prices), np.nan)
                
                alpha = 2 / (period + 1)
                ema = np.zeros_like(prices, dtype=float)
                ema[0] = prices[0]
                
                for i in range(1, len(prices)):
                    ema[i] = alpha * prices[i] + (1 - alpha) * ema[i-1]
                
                return ema
            
            # 计算各种EMA
            df['ema7'] = calculate_ema(close_prices, 7)
            df['ema12'] = calculate_ema(close_prices, 12)
            df['ema25'] = calculate_ema(close_prices, 25)
            df['ema50'] = calculate_ema(close_prices, 50)
            
            # 计算简单移动平均
            df['ma5'] = df['close'].rolling(window=5, min_periods=1).mean()
            df['ma10'] = df['close'].rolling(window=10, min_periods=1).mean()
            
            # 计算RSI
            def calculate_rsi(prices, period=14):
                if len(prices) < period + 1:
                    return np.full(len(prices), np.nan)
                
                deltas = np.diff(prices)
                seed = deltas[:period]
                up = seed[seed >= 0].sum() / period
                down = -seed[seed < 0].sum() / period
                rs = up / down if down != 0 else 0
                rsi = np.zeros_like(prices)
                rsi[:period] = 100.0 - 100.0 / (1.0 + rs)
                
                for i in range(period, len(prices)):
                    delta = deltas[i - 1]
                    if delta > 0:
                        upval = delta
                        downval = 0.0
                    else:
                        upval = 0.0
                        downval = -delta
                    
                    up = (up * (period - 1) + upval) / period
                    down = (down * (period - 1) + downval) / period
                    rs = up / down if down != 0 else 0
                    rsi[i] = 100.0 - 100.0 / (1.0 + rs)
                
                return rsi
            
            df['rsi14'] = calculate_rsi(close_prices, 14)
            df['rsi6'] = calculate_rsi(close_prices, 6)
            
            # 计算MACD
            def calculate_macd(prices, fast=12, slow=26, signal=9):
                if len(prices) < slow:
                    return np.full(len(prices), np.nan), np.full(len(prices), np.nan), np.full(len(prices), np.nan)
                
                ema_fast = calculate_ema(prices, fast)
                ema_slow = calculate_ema(prices, slow)
                dif = ema_fast - ema_slow
                dea = calculate_ema(dif, signal)
                macd = dif - dea
                
                return dif, dea, macd
            
            df['dif'], df['dea'], df['macd'] = calculate_macd(close_prices)
            
            self.logger.info(f"技术指标计算完成: {len(df)} 条数据")
            
            return df
            
        except Exception as e:
            self.logger.error(f"计算技术指标失败: {e}")
            return df
    
    def update_database(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        更新数据库
        
        参数:
            df: 要插入的数据DataFrame
        
        返回:
            Dict: 更新结果
        """
        if df.empty:
            return {'success': False, 'message': '空数据', 'rows_affected': 0}
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取数据信息
            symbol = df['symbol'].iloc[0] if 'symbol' in df.columns else 'UNKNOWN'
            timeframe = df['timeframe'].iloc[0] if 'timeframe' in df.columns else 'UNKNOWN'
            timestamps = df['timestamp'].tolist()
            
            # 检查哪些数据已经存在
            placeholders = ','.join(['?'] * len(timestamps))
            check_query = f"""
            SELECT timestamp FROM klines 
            WHERE symbol = ? AND timeframe = ? AND timestamp IN ({placeholders})
            """
            
            cursor.execute(check_query, (symbol, timeframe, *timestamps))
            existing_timestamps = {row[0] for row in cursor.fetchall()}
            
            # 过滤掉已存在的数据
            new_data = df[~df['timestamp'].isin(existing_timestamps)]
            
            if new_data.empty:
                conn.close()
                return {
                    'success': True,
                    'message': '所有数据已存在，无需更新',
                    'rows_affected': 0,
                    'existing_count': len(existing_timestamps),
                    'new_count': 0
                }
            
            # 准备插入数据
            rows_inserted = 0
            
            for _, row in new_data.iterrows():
                try:
                    # 构建插入语句
                    columns = ['timestamp', 'symbol', 'timeframe', 'open', 'high', 'low', 'close', 'volume',
                              'ema7', 'ema12', 'ema25', 'ema50', 'dif', 'dea', 'macd', 'rsi14', 'rsi6', 'ma5', 'ma10']
                    
                    placeholders = ','.join(['?'] * len(columns))
                    insert_query = f"INSERT OR REPLACE INTO klines ({','.join(columns)}) VALUES ({placeholders})"
                    
                    # 准备值
                    values = [
                        int(row.get('timestamp', 0)),
                        str(row.get('symbol', '')),
                        str(row.get('timeframe', '')),
                        float(row.get('open', 0)),
                        float(row.get('high', 0)),
                        float(row.get('low', 0)),
                        float(row.get('close', 0)),
                        float(row.get('volume', 0)),
                        float(row.get('ema7', 0)) if pd.notna(row.get('ema7')) else None,
                        float(row.get('ema12', 0)) if pd.notna(row.get('ema12')) else None,
                        float(row.get('ema25', 0)) if pd.notna(row.get('ema25')) else None,
                        float(row.get('ema50', 0)) if pd.notna(row.get('ema50')) else None,
                        float(row.get('dif', 0)) if pd.notna(row.get('dif')) else None,
                        float(row.get('dea', 0)) if pd.notna(row.get('dea')) else None,
                        float(row.get('macd', 0)) if pd.notna(row.get('macd')) else None,
                        float(row.get('rsi14', 0)) if pd.notna(row.get('rsi14')) else None,
                        float(row.get('rsi6', 0)) if pd.notna(row.get('rsi6')) else None,
                        float(row.get('ma5', 0)) if pd.notna(row.get('ma5')) else None,
                        float(row.get('ma10', 0)) if pd.notna(row.get('ma10')) else None
                    ]
                    
                    cursor.execute(insert_query, values)
                    rows_inserted += 1
                    
                except Exception as row_error:
                    self.logger.error(f"插入单行数据失败: {row_error}")
                    continue
            
            conn.commit()
            conn.close()
            
            result = {
                'success': True,
                'message': f'成功插入 {rows_inserted} 条新数据',
                'rows_affected': rows_inserted,
                'existing_count': len(existing_timestamps),
                'new_count': rows_inserted,
                'symbol': symbol,
                'timeframe': timeframe,
                'timestamp_range': {
                    'min': int(new_data['timestamp'].min()) if not new_data.empty else None,
                    'max': int(new_data['timestamp'].max()) if not new_data.empty else None
                }
            }
            
            self.logger.info(f"数据库更新完成: {symbol} ({timeframe}) - 新增 {rows_inserted} 条")
            
            return result
            
        except Exception as e:
            self.logger.error(f"更新数据库失败: {e}")
            return {'success': False, 'message': str(e), 'rows_affected': 0}
    
    def update_data(self, symbol: str, timeframe: str, limit: int = 100) -> Dict[str, Any]:
        """
        更新数据完整流程
        
        参数:
            symbol: 交易对符号
            timeframe: 时间框架
            limit: 获取的数据条数
        
        返回:
            Dict: 更新结果
        """
        self.logger.info(f"开始更新数据: {symbol} ({timeframe})")
        
        start_time = time.time()
        
        try:
            # 1. 从Binance获取数据
            raw_data = self.fetch_klines_from_binance(symbol, timeframe, limit)
            
            if raw_data is None or raw_data.empty:
                return {
                    'success': False,
                    'message': '从API获取数据失败',
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'duration_seconds': time.time() - start_time
                }
            
            # 2. 计算技术指标
            enriched_data = self.calculate_technical_indicators(raw_data)
            
            # 3. 更新数据库
            update_result = self.update_database(enriched_data)
            
            # 4. 添加额外信息
            update_result.update({
                'symbol': symbol,
                'timeframe': timeframe,
                'data_fetched': len(raw_data),
                'duration_seconds': time.time() - start_time,
                'timestamp': datetime.now().isoformat()
            })
            
            self.logger.info(f"数据更新完成: {symbol} ({timeframe}) - 结果: {update_result['success']}")
            
            return update_result
            
        except Exception as e:
            self.logger.error(f"更新数据流程失败: {symbol} ({timeframe}) - {e}")
            return {
                'success': False,
                'message': str(e),
                'symbol': symbol,
                'timeframe': timeframe,
                'duration_seconds': time.time() - start_time
            }
    
    def update_all_stale_data(self, symbols: List[str], timeframes: List[str], 
                             threshold_hours: float = 24) -> Dict[str, Any]:
        """
        更新所有过时数据
        
        参数:
            symbols: 交易对列表
            timeframes: 时间框架列表
            threshold_hours: 新鲜度阈值
        
        返回:
            Dict: 总体更新结果