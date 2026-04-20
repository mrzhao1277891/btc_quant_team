#!/usr/bin/env python3
"""
每小时数据质量检查脚本
专门负责每小时检查数据质量和新鲜度，如果需要则拉取和更新数据到最新时间点
"""

import sqlite3
import requests
import time
from datetime import datetime, timedelta
import logging
import sys
import os

print("🦊 每小时数据质量检查启动")
print("=" * 60)

def setup_logging():
    """设置日志"""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, 'hourly_data_quality.log')),
            logging.StreamHandler()
        ]
    )

def check_freshness(symbol='BTCUSDT', timeframe='4h'):
    """检查数据新鲜度"""
    try:
        db_path = '/home/francis/.openclaw/workspace/crypto_analyzer/data/ultra_light.db'
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取最新数据时间戳
        cursor.execute("""
        SELECT MAX(timestamp), COUNT(*)
        FROM klines 
        WHERE symbol=? AND timeframe=?
        """, (symbol, timeframe))
        
        max_ts, count = cursor.fetchone()
        conn.close()
        
        current_time_ms = int(time.time() * 1000)
        
        if max_ts:
            age_ms = current_time_ms - max_ts
            age_hours = age_ms / (1000 * 60 * 60)
            
            # 新鲜度阈值
            thresholds = {'4h': 6, '1d': 24, '1w': 168, '1M': 720}
            threshold = thresholds.get(timeframe, 24)
            
            is_fresh = age_hours <= threshold
            dt = datetime.fromtimestamp(max_ts/1000)
            
            result = {
                'symbol': symbol,
                'timeframe': timeframe,
                'latest_datetime': dt.strftime('%Y-%m-%d %H:%M:%S'),
                'age_hours': age_hours,
                'threshold_hours': threshold,
                'is_fresh': is_fresh,
                'data_count': count,
                'status': 'fresh' if is_fresh else 'stale'
            }
            
            logging.info(f"新鲜度检查: {symbol} ({timeframe}) - {age_hours:.1f}小时 (阈值: {threshold}小时)")
            return result
        else:
            logging.warning(f"无数据: {symbol} ({timeframe})")
            return {
                'symbol': symbol,
                'timeframe': timeframe,
                'status': 'missing'
            }
            
    except Exception as e:
        logging.error(f"新鲜度检查失败: {symbol} ({timeframe}) - {e}")
        return {
            'symbol': symbol,
            'timeframe': timeframe,
            'status': 'error',
            'error': str(e)
        }

def update_data(symbol='BTCUSDT', timeframe='4h'):
    """更新数据到最新时间点"""
    logging.info(f"🔄 开始更新数据: {symbol} ({timeframe})")
    
    result = {
        'symbol': symbol,
        'timeframe': timeframe,
        'timestamp': datetime.now().isoformat(),
        'success': False,
        'updated_count': 0,
        'inserted_count': 0,
        'error': None
    }
    
    try:
        # 映射时间框架到Binance间隔
        interval_map = {'4h': '4h', '1d': '1d', '1w': '1w', '1M': '1M'}
        interval = interval_map.get(timeframe, '4h')
        
        # 获取Binance最新数据
        url = 'https://api.binance.com/api/v3/klines'
        params = {'symbol': symbol, 'interval': interval, 'limit': 5}
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if not data:
            result['error'] = "无数据返回"
            logging.warning(f"Binance无数据返回: {symbol} ({timeframe})")
            return result
        
        logging.info(f"获取到 {len(data)} 条数据: {symbol} ({timeframe})")
        
        # 更新数据库
        db_path = '/home/francis/.openclaw/workspace/crypto_analyzer/data/ultra_light.db'
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        updated = 0
        inserted = 0
        
        for kline in data:
            timestamp = kline[0]
            open_price = float(kline[1])
            high = float(kline[2])
            low = float(kline[3])
            close = float(kline[4])
            volume = float(kline[5])
            
            # 检查是否已存在
            cursor.execute("""
            SELECT 1 FROM klines 
            WHERE symbol=? AND timeframe=? AND timestamp=?
            """, (symbol, timeframe, timestamp))
            
            if cursor.fetchone():
                # 更新现有数据
                cursor.execute("""
                UPDATE klines SET
                    open=?, high=?, low=?, close=?, volume=?
                WHERE symbol=? AND timeframe=? AND timestamp=?
                """, (open_price, high, low, close, volume, symbol, timeframe, timestamp))
                updated += 1
            else:
                # 插入新数据
                cursor.execute("""
                INSERT INTO klines 
                (symbol, timeframe, timestamp, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (symbol, timeframe, timestamp, open_price, high, low, close, volume))
                inserted += 1
        
        conn.commit()
        conn.close()
        
        result['updated_count'] = updated
        result['inserted_count'] = inserted
        result['success'] = True
        
        if inserted > 0 or updated > 0:
            logging.info(f"✅ 数据更新成功: {symbol} ({timeframe}) - 更新: {updated}, 插入: {inserted}")
        else:
            logging.info(f"数据已是最新: {symbol} ({timeframe})")
        
        return result
        
    except requests.exceptions.Timeout:
        error_msg = f"请求超时: {symbol} ({timeframe})"
        result['error'] = error_msg
        logging.error(error_msg)
        return result
        
    except requests.exceptions.ConnectionError:
        error_msg = f"连接错误: {symbol} ({timeframe})"
        result['error'] = error_msg
        logging.error(error_msg)
        return result
        
    except Exception as e:
        error_msg = f"更新失败: {symbol} ({timeframe}) - {e}"
        result['error'] = error_msg
        logging.error(error_msg)
        return result

def check_and_update_if_needed(symbol='BTCUSDT', timeframe='4h'):
    """检查并更新数据（如果需要）"""
    logging.info(f"🔍 检查并更新数据: {symbol} ({timeframe})")
    
    result = {
        'symbol': symbol,
        'timeframe': timeframe,
        'timestamp': datetime.now().isoformat(),
        'checked': True,
        'needed_update': False,
        'update_performed': False,
        'update_success': False
    }
    
    try:
        # 1. 检查数据新鲜度
        freshness_result = check_freshness(symbol, timeframe)
        
        # 2. 判断是否需要更新
        status = freshness_result.get('status', 'unknown')
        age_hours = freshness_result.get('age_hours', 999)
        
        # 新鲜度阈值
        thresholds = {'4h': 6, '1d': 24, '1w': 168, '1M': 720}
        threshold = thresholds.get(timeframe, 24)
        
        if status == 'missing':
            logging.warning(f"数据缺失，需要更新: {symbol} ({timeframe})")
            result['needed_update'] = True
            result['update_reason'] = 'missing_data'
            
        elif status == 'stale':
            logging.warning(f"数据陈旧，需要更新: {symbol} ({timeframe}) - {age_hours:.1f}小时 > {threshold}小时")
            result['needed_update'] = True
            result['update_reason'] = 'stale_data'
            
        elif age_hours > threshold * 0.5:  # 超过阈值一半
            logging.info(f"数据较旧，考虑更新: {symbol} ({timeframe}) - {age_hours:.1f}小时")
            # 对于4小时数据，如果超过3小时（阈值6小时的一半），建议更新
            if timeframe == '4h' and age_hours > 3:
                result['needed_update'] = True
                result['update_reason'] = 'somewhat_old'
            else:
                result['needed_update'] = False
                result['update_reason'] = 'still_acceptable'
                
        else:
            logging.info(f"数据非常新鲜，跳过更新: {symbol} ({timeframe}) - {age_hours:.1f}小时")
            result['needed_update'] = False
            result['update_reason'] = 'very_fresh'
        
        # 3. 如果需要更新，执行更新
        if result['needed_update']:
            update_result = update_data(symbol, timeframe)
            result['update_performed'] = True
            result['update_success'] = update_result.get('success', False)
            
            if result['update_success']:
                logging.info(f"✅ 数据更新完成: {symbol} ({timeframe})")
            else:
                logging.error(f"❌ 数据更新失败: {symbol} ({timeframe})")
        else:
            logging.info(f"✅ 数据状态良好，无需更新: {symbol} ({timeframe})")
        
        return result
        
    except Exception as e:
        error_msg = f"检查更新失败: {symbol} ({timeframe}) - {e}"
        logging.error(error_msg)
        result['error'] = str(e)
        return result

def run_hourly_check():
    """运行每小时检查"""
    logging.info("⏰ 开始每小时数据质量检查")
    start_time = datetime.now()
    
    # 检查的时间框架
    timeframes = ['4h', '1d', '1w', '1M']
    
    all_results = []
    summary = {
        'total_checks': 0,
        'needed_updates': 0,
        'successful_updates': 0,
        'failed_updates': 0,
        'fresh_data': 0,
        'stale_data': 0,
        'missing_data': 0
    }
    
    print(f"\n📊 每小时数据质量检查 - {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    # 对每个时间框架执行检查
    for timeframe in timeframes:
        try:
            summary['total_checks'] += 1
            
            # 执行检查更新
            result = check_and_update_if_needed('BTCUSDT', timeframe)
            all_results.append(result)
            
            # 更新统计
            if result.get('needed_update', False):
                summary['needed_updates'] += 1
                
                if result.get('update_success', False):
                    summary['successful_updates'] += 1
                else:
                    summary['failed_updates'] += 1
            
            # 显示结果
            freshness = check_freshness('BTCUSDT', timeframe)
            status = freshness.get('status', 'unknown')
            
            if status == 'fresh':
                summary['fresh_data'] += 1
                status_icon = '✅'
            elif status == 'stale':
                summary['stale_data'] += 1
                status_icon = '❌'
            elif status == 'missing':
                summary['missing_data'] += 1
                status_icon = '❌'
            else:
                status_icon = '❓'
            
            tf_name = {'4h': '4小时', '1d': '日线', '1w': '周线', '1M': '月线'}[timeframe]
            age_hours = freshness.get('age_hours', 0)
            
            print(f"   {tf_name}: {status_icon} {age_hours:.1f}小时")
            
        except Exception as e:
            logging.error(f"检查失败: BTCUSDT ({timeframe}) - {e}")
            print(f"   {timeframe}: ❌ 检查失败")
    
    # 计算耗时
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # 打印总结
    print(f"\n📋 检查总结:")
    print(f"   总检查项: {summary['total_checks']}")
    print(f"   需要更新: {summary['needed_updates']}")
    print(f"   成功更新: {summary['successful_updates']}")
    print(f"   失败更新: {summary['failed_updates']}")
    print(f"   新鲜数据: {summary['fresh_data']}")
    print(f"   陈旧数据: {summary['stale_data']}")
    print(f"   缺失数据: {summary['missing_data']}")
    print(f"   检查耗时: {duration:.1f}秒")
    
    # 记录到日志
    logging.info(f"✅ 每小时检查完成: 检查{summary['total_checks']}项, 需要更新{summary['needed_updates']}项, 成功{summary['successful_updates']}项")
    
    # 保存检查记录
    try:
        record = {
            'timestamp': start_time.isoformat(),
            'duration_seconds': duration,
            'summary': summary,
            'results': all_results
        }
        
        records_dir = 'hourly_records'
        os.makedirs(records_dir, exist_ok=True)
        
        import json
        record_file = os.path.join(records_dir, f"hourly_check_{start_time.strftime('%Y%m%d_%H%M%S')}.json")
        
        with open(record_file, 'w', encoding='utf-8') as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
        
        logging.info(f"检查记录已保存: {record_file}")
        
    except Exception as e:
        logging.error(f"保存检查记录失败: {e}")
    
    print(f"\n⏰ 每小时检查完成 - {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    return summary

def main():
    """主函数"""
    # 设置日志
    setup_logging()
    
    # 运行检查
    summary = run_hourly_check()
    
    # 返回状态码
    if summary.get('failed_updates', 0) > 0:
        return 1  # 有失败更新
    elif summary.get('stale_data', 0) > 0 or summary.get('missing_data', 0) > 0:
        return 2  # 有陈旧或缺失数据
    else:
        return 0  # 全部正常

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)