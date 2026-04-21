#!/usr/bin/env python3
"""
BTC数据初始化工具 - 专业版
使用TA-Lib计算所有技术指标
"""

import mysql.connector
import requests
import time
import json
from datetime import datetime, timedelta
import logging
import sys
import argparse
from typing import Dict, List, Optional, Tuple
import numpy as np
import talib

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BTCDataInitializerTA:
    """BTC数据初始化器 - 使用TA-Lib"""
    
    def __init__(self, host='localhost', port=3306, user='root', password='', database='btc_assistant'):
        self.config = {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'database': database,
            'charset': 'utf8mb4'
        }
        self.connection = None
        self.binance_api = "https://api.binance.com"
        
        # 数据采集配置
        self.data_config = {
            '4h': {'limit': 600, 'interval': '4h'},
            '1d': {'limit': 600, 'interval': '1d'},
            '1w': {'limit': 250, 'interval': '1w'},
            '1M': {'limit': 60, 'interval': '1M'}
        }
        
        # 支持的交易对
        self.symbols = ['BTCUSDT']
    
    def connect(self):
        """连接到数据库"""
        try:
            self.connection = mysql.connector.connect(**self.config)
            logger.info(f"✅ 成功连接到数据库: {self.config['database']}")
            return True
        except Exception as e:
            logger.error(f"❌ 连接失败: {e}")
            return False
    
    def fetch_binance_klines(self, symbol: str, interval: str, limit: int) -> List[Dict]:
        """从币安获取K线数据"""
        try:
            url = f"{self.binance_api}/api/v3/klines"
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            
            logger.info(f"📡 获取数据: {symbol} {interval} 数量: {limit}")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            klines = []
            for item in data:
                kline = {
                    'timestamp': int(item[0]),  # 开盘时间戳
                    'symbol': symbol,
                    'timeframe': interval,
                    'open': float(item[1]),
                    'high': float(item[2]),
                    'low': float(item[3]),
                    'close': float(item[4]),
                    'volume': float(item[5]),
                    'close_time': int(item[6]),  # 收盘时间戳
                    'quote_volume': float(item[7]),
                    'trades': int(item[8]),
                    'taker_buy_base': float(item[9]),
                    'taker_buy_quote': float(item[10])
                }
                klines.append(kline)
            
            logger.info(f"✅ 获取到 {len(klines)} 条K线数据")
            return klines
            
        except Exception as e:
            logger.error(f"❌ 获取数据失败: {e}")
            return []
    
    def calculate_indicators_with_talib(self, klines: List[Dict]) -> List[Dict]:
        """使用TA-Lib计算技术指标"""
        if len(klines) < 50:  # 需要足够数据计算指标
            logger.warning(f"⚠️  数据不足({len(klines)}条)，跳过指标计算")
            return klines
        
        # 提取价格序列
        closes = np.array([k['close'] for k in klines], dtype=np.float64)
        opens = np.array([k['open'] for k in klines], dtype=np.float64)
        highs = np.array([k['high'] for k in klines], dtype=np.float64)
        lows = np.array([k['low'] for k in klines], dtype=np.float64)
        volumes = np.array([k['volume'] for k in klines], dtype=np.float64)
        
        # 计算移动平均线
        try:
            # EMA
            ema7 = talib.EMA(closes, timeperiod=7)
            ema25 = talib.EMA(closes, timeperiod=25)
            ema50 = talib.EMA(closes, timeperiod=50)
            ema12 = talib.EMA(closes, timeperiod=12)
            
            # MA (简单移动平均)
            ma5 = talib.SMA(closes, timeperiod=5)
            ma10 = talib.SMA(closes, timeperiod=10)
            
            # MACD
            macd, macd_signal, macd_hist = talib.MACD(closes, fastperiod=12, slowperiod=26, signalperiod=9)
            
            # RSI
            rsi14 = talib.RSI(closes, timeperiod=14)
            rsi6 = talib.RSI(closes, timeperiod=6)
            
            # 布林带 (20, 2) - 使用TA-Lib的BBANDS函数
            # 返回: upperband, middleband, lowerband
            upperband, middleband, lowerband = talib.BBANDS(
                closes, 
                timeperiod=20,
                nbdevup=2,      # 上轨标准差倍数
                nbdevdn=2,      # 下轨标准差倍数
                matype=0        # 0=SMA, 1=EMA, 2=WMA, 3=DEMA, 4=TEMA, 5=TRIMA, 6=KAMA, 7=MAMA, 8=T3
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
                
                # MACD: DIF = macd, DEA = macd_signal, MACD = macd_hist
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
                    klines[i]['boll_md'] = float(round(middleband[i], 4))  # 中轨，与boll相同
                if not np.isnan(upperband[i]):
                    klines[i]['boll_up'] = float(round(upperband[i], 4))
                if not np.isnan(lowerband[i]):
                    klines[i]['boll_dn'] = float(round(lowerband[i], 4))
            
            logger.info(f"✅ 使用TA-Lib计算了 {len(klines)} 条数据的指标")
            
            # 调试：打印最后一条数据的指标值
            last = klines[-1]
            logger.info(f"🔍 最后一条指标样本: DIF={last.get('dif')}, DEA={last.get('dea')}, "
                        f"MACD={last.get('macd')}, BOLL={last.get('boll')}, "
                        f"BOLL_UP={last.get('boll_up')}, BOLL_DN={last.get('boll_dn')}")
            
        except Exception as e:
            logger.error(f"❌ TA-Lib计算指标失败: {e}")
            import traceback
            traceback.print_exc()
        
        return klines
    
    def insert_klines(self, klines: List[Dict]):
        """插入K线数据到数据库"""
        if not klines:
            logger.warning("⚠️ 没有数据可插入")
            return
        
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
                        
                except Exception as e:
                    error_count += 1
                    logger.debug(f"插入单条数据失败: {e}")
                    continue
            
            self.connection.commit()
            cursor.close()
            
            logger.info(f"📊 插入完成: 新增 {inserted_count} 条, 更新 {updated_count} 条, 错误 {error_count} 条")
            return inserted_count + updated_count
            
        except Exception as e:
            logger.error(f"❌ 插入数据失败: {e}")
            self.connection.rollback()
            return 0
    
    def initialize_data(self, symbol='BTCUSDT', force=False):
        """初始化数据"""
        logger.info(f"🚀 开始初始化 {symbol} 数据 (使用TA-Lib)")
        
        total_inserted = 0
        
        for timeframe, config in self.data_config.items():
            logger.info(f"\n📈 处理 {timeframe} 周期数据...")
            
            # 检查是否已有数据
            if not force:
                existing_count = self.check_existing_data(symbol, timeframe)
                if existing_count >= config['limit'] * 0.8:  # 已有80%数据
                    logger.info(f"⏭️  {timeframe} 周期已有 {existing_count} 条数据，跳过")
                    continue
            
            # 获取数据
            klines = self.fetch_binance_klines(symbol, config['interval'], config['limit'])
            if not klines:
                logger.warning(f"⚠️  获取 {timeframe} 数据失败，跳过")
                continue
            
            # 使用TA-Lib计算指标
            klines_with_indicators = self.calculate_indicators_with_talib(klines)
            
            # 插入数据
            inserted = self.insert_klines(klines_with_indicators)
            total_inserted += inserted
            
            # 避免API限制
            time.sleep(1)
        
        logger.info(f"\n🎉 数据初始化完成，共处理 {total_inserted} 条数据")
        return total_inserted
    
    def check_existing_data(self, symbol: str, timeframe: str) -> int:
        """检查已有数据量"""
        try:
            cursor = self.connection.cursor()
            query = "SELECT COUNT(*) FROM klines WHERE symbol = %s AND timeframe = %s"
            cursor.execute(query, (symbol, timeframe))
            count = cursor.fetchone()[0]
            cursor.close()
            return count
        except Exception as e:
            logger.warning(f"检查已有数据失败: {e}")
            return 0
    
    def show_data_summary(self):
        """显示数据摘要"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            # 按时间框架统计
            query = """
                SELECT 
                    timeframe,
                    COUNT(*) as count,
                    MIN(FROM_UNIXTIME(timestamp/1000)) as earliest,
                    MAX(FROM_UNIXTIME(timestamp/1000)) as latest,
                    MIN(create_time) as first_create,
                    MAX(update_time) as last_update
                FROM klines 
                WHERE symbol = 'BTCUSDT'
                GROUP BY timeframe
                ORDER BY FIELD(timeframe, '1M', '1w', '1d', '4h')
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            print("\n📊 数据摘要:")
            print("="*80)
            for row in results:
                print(f"  {row['timeframe']:4} | 数量: {row['count']:6} | "
                      f"最早: {row['earliest']} | 最新: {row['latest']}")
                print(f"      创建: {row['first_create']} | 更新: {row['last_update']}")
            
            # 显示最新数据（包含MACD）
            cursor.execute("""
                SELECT 
                    timeframe,
                    FROM_UNIXTIME(timestamp/1000) as time,
                    close,
                    volume,
                    ema7,
                    ema25,
                    dif,
                    dea,
                    macd,
                    rsi14
                FROM klines 
                WHERE symbol = 'BTCUSDT'
                ORDER BY timestamp DESC
                LIMIT 10
            """)
            
            latest = cursor.fetchall()
            print(f"\n📈 最新数据 (10条，包含MACD):")
            print("-"*100)
            for row in latest:
                print(f"  {row['timeframe']:4} | {row['time']} | "
                      f"价格: {row['close']:,.2f} | 成交量: {row['volume']:.2f} | "
                      f"EMA7: {row['ema7'] or 'N/A':,.2f} | DIF: {row['dif'] or 'N/A':,.4f} | "
                      f"RSI14: {row['rsi14'] or 'N/A'}")
            
            cursor.close()
            
        except Exception as e:
            logger.error(f"显示数据摘要失败: {e}")
    
    def close(self):
        """关闭连接"""
        if self.connection:
            self.connection.close()
            logger.info("🔌 数据库连接已关闭")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='BTC数据初始化工具 - TA-Lib专业版')
    parser.add_argument('--host', default='localhost', help='MySQL主机 (默认: localhost)')
    parser.add_argument('--port', type=int, default=3306, help='MySQL端口 (默认: 3306)')
    parser.add_argument('--user', default='root', help='MySQL用户 (默认: root)')
    parser.add_argument('--password', default='', help='MySQL密码')
    parser.add_argument('--database', default='btc_assistant', help='数据库名 (默认: btc_assistant)')
    parser.add_argument('--symbol', default='BTCUSDT', help='交易对 (默认: BTCUSDT)')
    parser.add_argument('--force', action='store_true', help='强制重新获取所有数据')
    parser.add_argument('--summary', action='store_true', help='只显示数据摘要')
    
    args = parser.parse_args()
    
    print(f"🚀 BTC数据初始化工具 - TA-Lib专业版")
    print(f"   数据库: {args.database}")
    print(f"   交易对: {args.symbol}")
    print(f"   强制模式: {'是' if args.force else '否'}")
    print("="*60)
    
    # 如果密码为空，使用空字符串
    if args.password is None:
        args.password = ""
    
    # 创建初始化器
    initializer = BTCDataInitializerTA(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        database=args.database
    )
    
    try:
        # 连接数据库
        if not initializer.connect():
            return
        
        if args.summary:
            # 只显示摘要
            initializer.show_data_summary()
        else:
            # 初始化数据
            print(f"\n📥 开始获取数据 (使用TA-Lib计算指标)...")
            print(f"   配置:")
            print(f"     - 4h周期: 600条")
            print(f"     - 1d周期: 600条") 
            print(f"     - 1w周期: 250条")
            print(f"     - 1M周期: 60条")
            print()
            
            total = initializer.initialize_data(args.symbol, args.force)
            
            if total > 0:
                print(f"\n✅ 数据初始化完成，共处理 {total} 条数据")
            
            # 显示摘要
            initializer.show_data_summary()
        
        print("\n🎉 操作完成!")
        
    except KeyboardInterrupt:
        print("\n\n操作被用户中断")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        initializer.close()

if __name__ == "__main__":
    main()