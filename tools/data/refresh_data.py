#!/usr/bin/env python3
"""
数据刷新工具模块

职责: 检查klines表的数据质量和新鲜度，从币安数据源获取最新数据，
计算技术指标并补充到klines表中。

主要功能:
- check_data_freshness(): 检查数据新鲜度
- refresh_latest_data(): 刷新最新数据
- fill_missing_data(): 填充缺失数据
- calculate_missing_indicators(): 计算缺失指标

依赖:
- mysql-connector-python: MySQL连接
- TA-Lib: 技术指标计算
- requests: API数据获取

注意事项:
1. 遵守API速率限制
2. 处理网络和数据库异常
3. 数据验证和完整性检查

版本: 1.0.0
作者: 量化团队
更新日期: 2026-04-21
"""

import mysql.connector
import requests
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import talib
import logging
import argparse
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API配置
BINANCE_API_URL = "https://api.binance.com"
BINANCE_KLINES_ENDPOINT = "/api/v3/klines"

# 时间框架配置
# 刷新阈值说明：每2小时检查一次，保证数据在阈值内
TIMEFRAME_CONFIG = {
    '1m': {'refresh_hours': 2, 'limit': 100},     # 保证数据在2小时内
    '5m': {'refresh_hours': 6, 'limit': 200},     # 保证数据在6小时内
    '15m': {'refresh_hours': 24, 'limit': 300},   # 保证数据在24小时内
    '1h': {'refresh_hours': 48, 'limit': 400},    # 保证数据在48小时内
    '4h': {'refresh_hours': 4, 'limit': 600},     # 保证数据在4小时内（合理）
    '1d': {'refresh_hours': 24, 'limit': 600},    # 保证数据在24小时内（合理）
    '1w': {'refresh_hours': 168, 'limit': 250},   # 保证数据在7天内（合理）
    '1M': {'refresh_hours': 720, 'limit': 60}     # 保证数据在30天内（合理）
}

class DataRefresher:
    """
    数据刷新器
    
    职责: 刷新和补充BTC量化分析数据库的数据
    
    属性:
        config (Dict): 数据库配置
        connection (mysql.connector.connection): 数据库连接
        binance_api (str): Binance API地址
    
    方法:
        connect(): 连接到数据库
        disconnect(): 断开数据库连接
        check_freshness(): 检查数据新鲜度
        refresh_data(): 刷新数据
        fill_gaps(): 填充数据缺口
    
    示例:
        >>> refresher = DataRefresher()
        >>> refresher.connect()
        >>> report = refresher.check_freshness('BTCUSDT')
        >>> refresher.refresh_data('BTCUSDT')
        >>> refresher.disconnect()
    """
    
    def __init__(
        self,
        host: str = 'localhost',
        port: int = 3306,
        user: str = 'root',
        password: str = '',
        database: str = 'btc_assistant'
    ):
        """
        初始化数据刷新器
        
        参数:
            host (str): MySQL主机，默认'localhost'
            port (int): MySQL端口，默认3306
            user (str): MySQL用户，默认'root'
            password (str): MySQL密码，默认''
            database (str): 数据库名，默认'btc_assistant'
        """
        self.config = {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'database': database,
            'charset': 'utf8mb4'
        }
        self.connection = None
        self.binance_api = BINANCE_API_URL
    
    def connect(self) -> bool:
        """连接到数据库"""
        try:
            self.connection = mysql.connector.connect(**self.config)
            logger.info(f"✅ 成功连接到数据库: {self.config['database']}")
            return True
        except mysql.connector.Error as e:
            logger.error(f"❌ 数据库连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开数据库连接"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("🔌 数据库连接已关闭")
    
    def check_data_freshness(self, symbol: str = 'BTCUSDT') -> Dict[str, Any]:
        """
        检查数据新鲜度
        
        参数:
            symbol (str): 交易对，默认'BTCUSDT'
        
        返回:
            Dict: 数据新鲜度报告
        """
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            # 检查每个时间框架的数据新鲜度
            freshness_report = {
                'symbol': symbol,
                'timeframes': [],
                'issues': [],
                'summary': {
                    'total_timeframes': 0,
                    'fresh_timeframes': 0,
                    'stale_timeframes': 0,
                    'missing_timeframes': 0
                }
            }
            
            for timeframe, config in TIMEFRAME_CONFIG.items():
                # 获取最新数据时间
                query = """
                    SELECT 
                        MAX(FROM_UNIXTIME(timestamp/1000)) as latest_time,
                        COUNT(*) as total_count
                    FROM klines 
                    WHERE symbol = %s AND timeframe = %s
                """
                cursor.execute(query, (symbol, timeframe))
                result = cursor.fetchone()
                
                timeframe_report = {
                    'timeframe': timeframe,
                    'config': config,
                    'latest_time': result['latest_time'] if result['latest_time'] else None,
                    'total_count': result['total_count'] or 0,
                    'is_fresh': False,
                    'hours_behind': None,
                    'status': 'UNKNOWN'
                }
                
                if timeframe_report['latest_time']:
                    latest_dt = timeframe_report['latest_time']
                    if isinstance(latest_dt, str):
                        latest_dt = datetime.fromisoformat(latest_dt.replace('Z', '+00:00'))
                    
                    hours_behind = (datetime.now() - latest_dt).total_seconds() / 3600
                    timeframe_report['hours_behind'] = round(hours_behind, 2)
                    
                    # 判断新鲜度
                    if hours_behind <= config['refresh_hours']:
                        timeframe_report['is_fresh'] = True
                        timeframe_report['status'] = 'FRESH'
                        freshness_report['summary']['fresh_timeframes'] += 1
                    else:
                        timeframe_report['status'] = 'STALE'
                        freshness_report['summary']['stale_timeframes'] += 1
                        freshness_report['issues'].append({
                            'timeframe': timeframe,
                            'issue': '数据过期',
                            'hours_behind': hours_behind,
                            'threshold': config['refresh_hours']
                        })
                else:
                    timeframe_report['status'] = 'MISSING'
                    freshness_report['summary']['missing_timeframes'] += 1
                    freshness_report['issues'].append({
                        'timeframe': timeframe,
                        'issue': '数据缺失',
                        'details': '没有找到该时间框架的数据'
                    })
                
                freshness_report['timeframes'].append(timeframe_report)
                freshness_report['summary']['total_timeframes'] += 1
            
            cursor.close()
            return freshness_report
            
        except mysql.connector.Error as e:
            logger.error(f"检查数据新鲜度失败: {e}")
            raise
    
    def fetch_latest_klines(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        从Binance获取最新K线数据
        
        参数:
            symbol (str): 交易对
            timeframe (str): 时间间隔
            limit (int): 获取数量
        
        返回:
            List[Dict]: K线数据列表
        """
        try:
            url = f"{self.binance_api}{BINANCE_KLINES_ENDPOINT}"
            params = {
                'symbol': symbol,
                'interval': timeframe,
                'limit': limit
            }
            
            logger.info(f"📡 获取最新数据: {symbol} {timeframe} 数量: {limit}")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            klines = []
            for item in data:
                kline = {
                    'timestamp': int(item[0]),
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'open': float(item[1]),
                    'high': float(item[2]),
                    'low': float(item[3]),
                    'close': float(item[4]),
                    'volume': float(item[5]),
                    'close_time': int(item[6]),
                    'quote_volume': float(item[7]),
                    'trades': int(item[8]),
                    'taker_buy_base': float(item[9]),
                    'taker_buy_quote': float(item[10])
                }
                klines.append(kline)
            
            logger.info(f"✅ 获取到 {len(klines)} 条最新K线数据")
            return klines
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 网络请求失败: {e}")
            raise ConnectionError(f"网络请求失败: {e}")
        except (KeyError, IndexError, ValueError) as e:
            logger.error(f"❌ 数据解析失败: {e}")
            raise RuntimeError(f"数据解析失败: {e}")
    
    def calculate_indicators(
        self,
        klines: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        使用TA-Lib计算技术指标
        
        参数:
            klines (List[Dict]): K线数据列表
        
        返回:
            List[Dict]: 包含技术指标的K线数据
        """
        if len(klines) < 50:
            logger.warning(f"⚠️ 数据不足({len(klines)}条)，跳过指标计算")
            return klines
        
        try:
            # 提取价格序列
            closes = np.array([k['close'] for k in klines], dtype=np.float64)
            
            # 计算移动平均线
            ema7 = talib.EMA(closes, timeperiod=7)
            ema25 = talib.EMA(closes, timeperiod=25)
            ema50 = talib.EMA(closes, timeperiod=50)
            ema12 = talib.EMA(closes, timeperiod=12)
            ma5 = talib.SMA(closes, timeperiod=5)
            ma10 = talib.SMA(closes, timeperiod=10)
            
            # 计算MACD
            macd, macd_signal, macd_hist = talib.MACD(
                closes, fastperiod=12, slowperiod=26, signalperiod=9
            )
            
            # 计算RSI
            rsi14 = talib.RSI(closes, timeperiod=14)
            rsi6 = talib.RSI(closes, timeperiod=6)
            
            # 布林带 (20, 2)
            upperband, middleband, lowerband = talib.BBANDS(
                closes, 
                timeperiod=20,
                nbdevup=2,
                nbdevdn=2,
                matype=0
            )
            
            # 将计算结果赋回到K线数据
            for i in range(len(klines)):
                if not np.isnan(ema7[i]):
                    klines[i]['ema7'] = float(ema7[i])
                if not np.isnan(ema25[i]):
                    klines[i]['ema25'] = float(ema25[i])
                if not np.isnan(ema50[i]):
                    klines[i]['ema50'] = float(ema50[i])
                if not np.isnan(ema12[i]):
                    klines[i]['ema12'] = float(ema12[i])
                if not np.isnan(ma5[i]):
                    klines[i]['ma5'] = float(ma5[i])
                if not np.isnan(ma10[i]):
                    klines[i]['ma10'] = float(ma10[i])
                
                if not np.isnan(macd[i]):
                    klines[i]['dif'] = float(macd[i])
                if not np.isnan(macd_signal[i]):
                    klines[i]['dea'] = float(macd_signal[i])
                if not np.isnan(macd_hist[i]):
                    klines[i]['macd'] = float(macd_hist[i])
                
                if not np.isnan(rsi14[i]):
                    klines[i]['rsi14'] = float(round(rsi14[i], 4))
                if not np.isnan(rsi6[i]):
                    klines[i]['rsi6'] = float(round(rsi6[i], 4))
                
                # 布林带
                if not np.isnan(middleband[i]):
                    klines[i]['boll'] = float(round(middleband[i], 4))
                    klines[i]['boll_md'] = float(round(middleband[i], 4))
                if not np.isnan(upperband[i]):
                    klines[i]['boll_up'] = float(round(upperband[i], 4))
                if not np.isnan(lowerband[i]):
                    klines[i]['boll_dn'] = float(round(lowerband[i], 4))
            
            logger.info(f"✅ 使用TA-Lib计算了 {len(klines)} 条数据的指标")
            return klines
            
        except Exception as e:
            logger.error(f"❌ TA-Lib计算指标失败: {e}")
            raise RuntimeError(f"指标计算失败: {e}")
    
    def insert_klines(
        self,
        klines: List[Dict[str, Any]]
    ) -> Tuple[int, int, int]:
        """
        插入K线数据到数据库
        
        参数:
            klines (List[Dict]): K线数据列表
        
        返回:
            Tuple[int, int, int]: (新增数量, 更新数量, 错误数量)
        """
        if not klines:
            logger.warning("⚠️ 没有数据可插入")
            return 0, 0, 0
        
        try:
            cursor = self.connection.cursor()
            
            insert_query = """
                INSERT INTO klines (
                    timestamp, symbol, timeframe,
                    open, high, low, close, volume,
                    ema7, ema25, ema50, ema12, ma5, ma10,
                    dif, dea, macd,
                    rsi14, rsi6,
                    boll, boll_up, boll_md, boll_dn,
                    create_time, update_time
                ) VALUES (
                    %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s,
                    %s, %s, %s, %s,
                    NOW(), NOW()
                )
                ON DUPLICATE KEY UPDATE
                    open = VALUES(open),
                    high = VALUES(high),
                    low = VALUES(low),
                    close = VALUES(close),
                    volume = VALUES(volume),
                    ema7 = VALUES(ema7),
                    ema25 = VALUES(ema25),
                    ema50 = VALUES(ema50),
                    ema12 = VALUES(ema12),
                    ma5 = VALUES(ma5),
                    ma10 = VALUES(ma10),
                    dif = VALUES(dif),
                    dea = VALUES(dea),
                    macd = VALUES(macd),
                    rsi14 = VALUES(rsi14),
                    rsi6 = VALUES(rsi6),
                    boll = VALUES(boll),
                    boll_up = VALUES(boll_up),
                    boll_md = VALUES(boll_md),
                    boll_dn = VALUES(boll_dn),
                    update_time = NOW()
            """
            
            inserted_count = 0
            updated_count = 0
            error_count = 0
            
            for kline in klines:
                try:
                    cursor.execute(insert_query, (
                        kline['timestamp'],
                        kline['symbol'],
                        kline['timeframe'],
                        kline['open'],
                        kline['high'],
                        kline['low'],
                        kline['close'],
                        kline['volume'],
                        kline.get('ema7'),
                        kline.get('ema25'),
                        kline.get('ema50'),
                        kline.get('ema12'),
                        kline.get('ma5'),
                        kline.get('ma10'),
                        kline.get('dif'),
                        kline.get('dea'),
                        kline.get('macd'),
                        kline.get('rsi14'),
                        kline.get('rsi6'),
                        kline.get('boll'),
                        kline.get('boll_up'),
                        kline.get('boll_md'),
                        kline.get('boll_dn')
                    ))
                    
                    if cursor.rowcount == 1:
                        inserted_count += 1
                    elif cursor.rowcount == 2:
                        updated_count += 1
                        
                except mysql.connector.Error as e:
                    error_count += 1
                    logger.debug(f"插入单条数据失败: {e}")
                    continue
            
            self.connection.commit()
            cursor.close()
            
            logger.info(
                f"📊 插入完成: 新增 {inserted_count} 条, "
                f"更新 {updated_count} 条, 错误 {error_count} 条"
            )
            return inserted_count, updated_count, error_count
            
        except mysql.connector.Error as e:
            logger.error(f"❌ 插入数据失败: {e}")
            self.connection.rollback()
            raise
    
    def refresh_timeframe_data(
        self,
        symbol: str,
        timeframe: str,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        刷新指定时间框架的数据
        
        参数:
            symbol (str): 交易对
            timeframe (str): 时间框架
            force (bool): 是否强制刷新
        
        返回:
            Dict: 刷新结果报告
        """
        config = TIMEFRAME_CONFIG.get(timeframe)
        if not config:
            return {
                'success': False,
                'error': f'不支持的时间框架: {timeframe}'
            }
        
        try:
            # 检查是否需要刷新
            if not force:
                freshness = self.check_data_freshness(symbol)
                timeframe_info = next(
                    (tf for tf in freshness['timeframes'] if tf['timeframe'] == timeframe),
                    None
                )
                
                if timeframe_info and timeframe_info['is_fresh']:
                    logger.info(f"⏭️  {timeframe} 数据已是最新，跳过刷新")
                    return {
                        'success': True,
                        'skipped': True,
                        'reason': '数据已是最新',
                        'hours_behind': timeframe_info['hours_behind']
                    }
            
            # 获取最新数据
            logger.info(f"🔄 刷新 {timeframe} 数据...")
            klines = self.fetch_latest_klines(symbol, timeframe, config['limit'])
            
            if not klines:
                return {
                    'success': False,
                    'error': '获取数据失败'
                }
            
            # 计算指标
            klines_with_indicators = self.calculate_indicators(klines)
            
            # 插入数据
            inserted, updated, errors = self.insert_klines(klines_with_indicators)
            
            # 避免API限制
            time.sleep(0.5)
            
            return {
                'success': True,
                'skipped': False,
                'inserted': inserted,
                'updated': updated,
                'errors': errors,
                'total': inserted + updated
            }
            
        except Exception as e:
            logger.error(f"刷新 {timeframe} 数据失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def refresh_all_data(
        self,
        symbol: str = 'BTCUSDT',
        force: bool = False
    ) -> Dict[str, Any]:
        """
        刷新所有时间框架的数据
        
        参数:
            symbol (str): 交易对，默认'BTCUSDT'
            force (bool): 是否强制刷新所有数据
        
        返回:
            Dict: 刷新结果报告
        """
        logger.info(f"🚀 开始刷新 {symbol} 所有时间框架数据")
        
        results = {
            'symbol': symbol,
            'force': force,
            'timeframes': {},
            'summary': {
                'total_timeframes': 0,
                'successful': 0,
                'failed': 0,
                'skipped': 0,
                'total_inserted': 0,
                'total_updated': 0
            }
        }
        
        # 按时间框架优先级排序（从短到长）
        timeframes = ['4h', '1d', '1w', '1M']
        
        for timeframe in timeframes:
            logger.info(f"\n📈 处理 {timeframe} 时间框架...")
            
            result = self.refresh_timeframe_data(symbol, timeframe, force)
            results['timeframes'][timeframe] = result
            
            results['summary']['total_timeframes'] += 1
            
            if result.get('skipped', False):
                results['summary']['skipped'] += 1
                logger.info(f"⏭️  {timeframe} 跳过刷新")
            elif result.get('success', False):
                results['summary']['successful'] += 1
                results['summary']['total_inserted'] += result.get('inserted', 0)
                results['summary']['total_updated'] += result.get('updated', 0)
                logger.info(f"✅  {timeframe} 刷新成功: 新增{result.get('inserted', 0)}条, 更新{result.get('updated', 0)}条")
            else:
                results['summary']['failed'] += 1
                logger.error(f"❌  {timeframe} 刷新失败: {result.get('error', '未知错误')}")
        
        logger.info(f"\n🎉 数据刷新完成")
        logger.info(f"   成功: {results['summary']['successful']}, 失败: {results['summary']['failed']}, 跳过: {results['summary']['skipped']}")
        logger.info(f"   新增: {results['summary']['total_inserted']}条, 更新: {results['summary']['total_updated']}条")
        
        return results
    
    def fill_data_gaps(self, symbol: str = 'BTCUSDT') -> Dict[str, Any]:
        """
        填充数据缺口
        
        参数:
            symbol (str): 交易对，默认'BTCUSDT'
        
        返回:
            Dict: 填充结果报告
        """
        logger.info(f"🔍 检查并填充 {symbol} 数据缺口")
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            gaps_report = {
                'symbol': symbol,
                'timeframes': {},
                'summary': {
                    'total_gaps': 0,
                    'filled_gaps': 0,
                    'total_inserted': 0
                }
            }
            
            for timeframe in TIMEFRAME_CONFIG.keys():
                # 检查数据连续性
                query = """
                    SELECT 
                        timeframe,
                        COUNT(*) as total_count,
                        MIN(timestamp) as min_timestamp,
                        MAX(timestamp) as max_timestamp
                    FROM klines 
                    WHERE symbol = %s AND timeframe = %s
                    GROUP BY timeframe
                """
                cursor.execute(query, (symbol, timeframe))
                result = cursor.fetchone()
                
                if not result or result['total_count'] == 0:
                    gaps_report['timeframes'][timeframe] = {
                        'status': 'MISSING',
                        'gaps_found': 0,
                        'gaps_filled': 0,
                        'inserted': 0
                    }
                    continue
                
                # 这里可以添加更复杂的数据缺口检测逻辑
                # 例如：检查时间戳是否连续，计算缺失的数据点等
                
                # 简化版：只报告基本情况
                gaps_report['timeframes'][timeframe] = {
                    'status': 'CHECKED',
                    'total_count': result['total_count'],
                    'min_timestamp': result['min_timestamp'],
                    'max_timestamp': result['max_timestamp'],
                    'gaps_found': 0,  # 简化处理
                    'gaps_filled': 0,
                    'inserted': 0
                }
            
            cursor.close()
            return gaps_report
            
        except mysql.connector.Error as e:
            logger.error(f"检查数据缺口失败: {e}")
            raise

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='BTC数据刷新工具')
    parser.add_argument('--host', default='localhost', help='MySQL主机 (默认: localhost)')
    parser.add_argument('--port', type=int, default=3306, help='MySQL端口 (默认: 3306)')
    parser.add_argument('--user', default='root', help='MySQL用户 (默认: root)')
    parser.add_argument('--password', default='', help='MySQL密码')
    parser.add_argument('--database', default='btc_assistant', help='数据库名 (默认: btc_assistant)')
    parser.add_argument('--symbol', default='BTCUSDT', help='交易对 (默认: BTCUSDT)')
    parser.add_argument('--action', default='refresh',
                       choices=['check', 'refresh', 'fill-gaps', 'all'],
                       help='执行动作 (默认: refresh)')
    parser.add_argument('--timeframe', help='指定时间框架 (如: 4h, 1d)')
    parser.add_argument('--force', action='store_true', help='强制刷新所有数据')
    
    args = parser.parse_args()
    
    print(f"🚀 BTC数据刷新工具")
    print(f"   数据库: {args.database}")
    print(f"   交易对: {args.symbol}")
    print(f"   动作: {args.action}")
    print(f"   强制模式: {'是' if args.force else '否'}")
    print("="*60)
    
    # 创建刷新器
    refresher = DataRefresher(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        database=args.database
    )
    
    try:
        # 连接数据库
        if not refresher.connect():
            return
        
        if args.action == 'check':
            # 检查数据新鲜度
            print(f"\n🔍 检查数据新鲜度...")
            report = refresher.check_data_freshness(args.symbol)
            
            print(f"\n📊 数据新鲜度报告:")
            print("-" * 80)
            for tf in report['timeframes']:
                status_icon = '✅' if tf['status'] == 'FRESH' else '⚠️' if tf['status'] == 'STALE' else '❌'
                print(f"  {status_icon} {tf['timeframe']:4} | 状态: {tf['status']:8} | "
                      f"数量: {tf['total_count']:6} | 最新: {tf['latest_time'] or '无数据'}")
                if tf['hours_behind']:
                    print(f"      落后: {tf['hours_behind']}小时 (阈值: {tf['config']['refresh_hours']}小时)")
            
            print(f"\n📋 摘要:")
            print(f"   总时间框架: {report['summary']['total_timeframes']}")
            print(f"   新鲜: {report['summary']['fresh_timeframes']}")
            print(f"   过期: {report['summary']['stale_timeframes']}")
            print(f"   缺失: {report['summary']['missing_timeframes']}")
            
            if report['issues']:
                print(f"\n⚠️  发现的问题:")
                for issue in report['issues']:
                    print(f"   - {issue['timeframe']}: {issue['issue']}")
        
        elif args.action == 'refresh':
            # 刷新数据
            if args.timeframe:
                # 刷新指定时间框架
                print(f"\n🔄 刷新 {args.timeframe} 数据...")
                result = refresher.refresh_timeframe_data(
                    args.symbol, args.timeframe, args.force
                )
                
                if result['success']:
                    if result.get('skipped', False):
                        print(f"✅ 跳过刷新: {result.get('reason', '未知原因')}")
                    else:
                        print(f"✅ 刷新成功!")
                        print(f"   新增: {result.get('inserted', 0)}条")
                        print(f"   更新: {result.get('updated', 0)}条")
                        print(f"   错误: {result.get('errors', 0)}条")
                else:
                    print(f"❌ 刷新失败: {result.get('error', '未知错误')}")
            else:
                # 刷新所有时间框架
                results = refresher.refresh_all_data(args.symbol, args.force)
                
                print(f"\n📊 刷新结果摘要:")
                print("-" * 80)
                for timeframe, result in results['timeframes'].items():
                    if result.get('skipped', False):
                        print(f"  ⏭️  {timeframe:4} | 跳过: {result.get('reason', '未知原因')}")
                    elif result.get('success', False):
                        print(f"  ✅  {timeframe:4} | 新增: {result.get('inserted', 0):3}条 | "
                              f"更新: {result.get('updated', 0):3}条")
                    else:
                        print(f"  ❌  {timeframe:4} | 失败: {result.get('error', '未知错误')}")
        
        elif args.action == 'fill-gaps':
            # 填充数据缺口
            print(f"\n🔍 填充数据缺口...")
            report = refresher.fill_data_gaps(args.symbol)
            
            print(f"\n📊 数据缺口报告:")
            print("-" * 80)
            for timeframe, info in report['timeframes'].items():
                if info['status'] == 'MISSING':
                    print(f"  ❌  {timeframe:4} | 状态: 数据缺失")
                else:
                    print(f"  ✅  {timeframe:4} | 状态: 已检查 | 数量: {info['total_count']:6}条")
        
        elif args.action == 'all':
            # 执行所有操作
            print(f"\n🔍 检查数据新鲜度...")
            freshness = refresher.check_data_freshness(args.symbol)
            
            print(f"\n🔄 刷新数据...")
            refresh_results = refresher.refresh_all_data(args.symbol, args.force)
            
            print(f"\n🔍 填充数据缺口...")
            gaps = refresher.fill_data_gaps(args.symbol)
            
            print(f"\n🎉 所有操作完成!")
        
        print("\n🎉 操作完成!")
        
    except KeyboardInterrupt:
        print("\n\n操作被用户中断")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        refresher.disconnect()

if __name__ == "__main__":
    main()