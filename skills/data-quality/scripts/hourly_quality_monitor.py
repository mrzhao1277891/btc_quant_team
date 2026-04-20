#!/usr/bin/env python3
"""
每小时数据质量监控器
专门负责每小时检查数据质量和新鲜度，如果需要则拉取和更新数据到最新时间点
"""

import time
import schedule
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import yaml
from pathlib import Path
import sqlite3
import requests
import sys
import os

# 添加父目录到路径以便导入
sys.path.append(str(Path(__file__).parent.parent))

class HourlyQualityMonitor:
    """每小时数据质量监控器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化每小时质量监控器
        
        参数:
            config_path: 配置文件路径
        """
        self.config_path = config_path or "config/monitor.yaml"
        self.config = self._load_config()
        
        # 监控状态
        self.is_running = False
        self.monitor_thread = None
        self.last_check_time = None
        self.check_history = []
        
        # 设置日志
        self._setup_logging()
        
        logging.info("🦊 每小时数据质量监控器初始化完成")
    
    def _load_config(self) -> Dict[str, Any]:
        """加载监控配置"""
        config_file = Path(self.config_path)
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logging.error(f"加载监控配置失败: {e}")
        
        # 默认配置
        return {
            'monitoring': {
                'enabled': True,
                'check_interval_minutes': 60,  # 每小时检查
                'auto_update': True,           # 自动更新过时数据
                'alert_on_failure': True,      # 失败时告警
                'symbols': ['BTCUSDT'],        # 监控的交易对
                'timeframes': ['4h', '1d', '1w', '1M'],  # 监控的时间框架
                'freshness_thresholds': {      # 新鲜度阈值（小时）
                    '4h': 6,    # 4小时线：超过6小时未更新需要更新
                    '1d': 24,   # 日线：超过24小时未更新需要更新
                    '1w': 168,  # 周线：超过7天未更新需要更新
                    '1M': 720   # 月线：超过30天未更新需要更新
                }
            },
            'database': {
                'path': '/home/francis/.openclaw/workspace/crypto_analyzer/data/ultra_light.db'
            },
            'api': {
                'binance': {
                    'base_url': 'https://api.binance.com/api/v3',
                    'timeout_seconds': 30,
                    'retry_attempts': 3
                }
            },
            'alerts': {
                'enabled': True,
                'channels': ['log'],
                'min_severity': 'warning'
            }
        }
    
    def _setup_logging(self):
        """设置日志"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'hourly_quality_monitor.log'),
                logging.StreamHandler()
            ]
        )
    
    def check_data_freshness(self, symbol: str, timeframe: str) -> Dict[str, Any]:
        """
        检查数据新鲜度
        
        参数:
            symbol: 交易对符号
            timeframe: 时间框架
        
        返回:
            Dict: 新鲜度检查结果
        """
        try:
            db_path = self.config['database']['path']
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
                
                # 获取阈值
                thresholds = self.config['monitoring']['freshness_thresholds']
                threshold = thresholds.get(timeframe, 24)
                
                is_fresh = age_hours <= threshold
                is_very_fresh = age_hours <= threshold * 0.5  # 一半阈值内算非常新鲜
                
                dt = datetime.fromtimestamp(max_ts/1000)
                
                result = {
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'latest_timestamp': max_ts,
                    'latest_datetime': dt.strftime('%Y-%m-%d %H:%M:%S'),
                    'age_hours': age_hours,
                    'threshold_hours': threshold,
                    'is_fresh': is_fresh,
                    'is_very_fresh': is_very_fresh,
                    'data_count': count,
                    'status': 'fresh' if is_fresh else 'stale',
                    'status_icon': '✅' if is_fresh else '❌'
                }
                
                logging.info(f"新鲜度检查: {symbol} ({timeframe}) - {age_hours:.1f}小时 (阈值: {threshold}小时)")
                return result
            else:
                logging.warning(f"无数据: {symbol} ({timeframe})")
                return {
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'status': 'missing',
                    'status_icon': '❌'
                }
                
        except Exception as e:
            logging.error(f"新鲜度检查失败: {symbol} ({timeframe}) - {e}")
            return {
                'symbol': symbol,
                'timeframe': timeframe,
                'status': 'error',
                'error': str(e),
                'status_icon': '❌'
            }
    
    def update_data_to_latest(self, symbol: str, timeframe: str) -> Dict[str, Any]:
        """
        更新数据到最新时间点
        
        参数:
            symbol: 交易对符号
            timeframe: 时间框架
        
        返回:
            Dict: 更新结果
        """
        logging.info(f"🔄 开始更新数据: {symbol} ({timeframe})")
        
        result = {
            'symbol': symbol,
            'timeframe': timeframe,
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'updated_count': 0,
            'inserted_count': 0,
            'error': None,
            'details': {}
        }
        
        try:
            # 1. 获取Binance最新数据
            binance_config = self.config['api']['binance']
            base_url = binance_config['base_url']
            
            # 映射时间框架到Binance间隔
            interval_map = {
                '4h': '4h',
                '1d': '1d',
                '1w': '1w',
                '1M': '1M'
            }
            
            interval = interval_map.get(timeframe, '4h')
            
            # 获取最新5条数据（确保覆盖可能的缺失）
            url = f"{base_url}/klines"
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': 5
            }
            
            response = requests.get(url, params=params, timeout=binance_config['timeout_seconds'])
            response.raise_for_status()
            
            data = response.json()
            
            if not data:
                result['error'] = "无数据返回"
                logging.warning(f"Binance无数据返回: {symbol} ({timeframe})")
                return result
            
            logging.info(f"获取到 {len(data)} 条数据: {symbol} ({timeframe})")
            
            # 2. 更新数据库
            db_path = self.config['database']['path']
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
            
            # 3. 验证更新结果
            if inserted > 0 or updated > 0:
                # 重新检查新鲜度
                freshness_result = self.check_data_freshness(symbol, timeframe)
                result['details']['after_update'] = freshness_result
                
                logging.info(f"✅ 数据更新成功: {symbol} ({timeframe}) - 更新: {updated}, 插入: {inserted}")
                
                # 发送成功通知
                if self.config['alerts']['enabled']:
                    self.send_alert(
                        f"✅ 数据更新成功: {symbol} ({timeframe})\n"
                        f"更新: {updated}条, 插入: {inserted}条\n"
                        f"最新数据: {freshness_result.get('latest_datetime', 'N/A')}",
                        'info'
                    )
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
            
            # 发送失败告警
            if self.config['alerts']['enabled']:
                self.send_alert(f"❌ 数据更新失败: {symbol} ({timeframe})\n错误: {str(e)}", 'error')
            
            return result
    
    def check_and_update_if_needed(self, symbol: str, timeframe: str) -> Dict[str, Any]:
        """
        检查并更新数据（如果需要）
        
        参数:
            symbol: 交易对符号
            timeframe: 时间框架
        
        返回:
            Dict: 检查更新结果
        """
        logging.info(f"🔍 检查并更新数据: {symbol} ({timeframe})")
        
        result = {
            'symbol': symbol,
            'timeframe': timeframe,
            'timestamp': datetime.now().isoformat(),
            'checked': True,
            'needed_update': False,
            'update_performed': False,
            'update_success': False,
            'details': {}
        }
        
        try:
            # 1. 检查数据新鲜度
            freshness_result = self.check_data_freshness(symbol, timeframe)
            result['details']['freshness_check'] = freshness_result
            
            # 2. 判断是否需要更新
            status = freshness_result.get('status', 'unknown')
            age_hours = freshness_result.get('age_hours', 999)
            
            # 获取阈值
            thresholds = self.config['monitoring']['freshness_thresholds']
            threshold = thresholds.get(timeframe, 24)
            
            # 判断逻辑：
            # - 如果数据缺失 → 需要更新
            # - 如果数据陈旧（超过阈值） → 需要更新
            # - 如果数据较旧（超过阈值一半）但未到阈值 → 考虑更新
            # - 如果数据非常新鲜（小于阈值一半） → 跳过更新
            
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
                update_result = self.update_data_to_latest(symbol, timeframe)
                result['update_performed'] = True
                result['update_success'] = update_result.get('success', False)
                result['details']['update_result'] = update_result
                
                if result['update_success']:
                    logging.info(f"✅ 数据更新完成: {symbol} ({timeframe})")
                else:
                    logging.error(f"❌ 数据更新失败: {symbol} ({timeframe})")
            else:
                logging.info(f"✅ 数据状态良好，无需更新: {symbol} ({timeframe})")
            
            # 记录检查历史
            self.check_history.append({
                'timestamp': result['timestamp'],
                'symbol': symbol,
                'timeframe': timeframe,
                'needed_update': result['needed_update'],
                'update_performed': result['update_performed'],
                'update_success': result.get('update_success', False),
                'age_hours': age_hours,
                'threshold': threshold
            })
            
            # 保持历史记录大小
            if len(self.check_history) > 1000:
                self.check_history = self.check_history[-1000:]
            
            return result
            
        except Exception as e:
            error_msg = f"检查更新失败: {symbol} ({timeframe}) - {e}"
            logging.error(error_msg)
            result['error'] = str(e)
            return result
    
    def run_hourly_check(self):
        """运行每小时检查"""
        logging.info("⏰ 开始每小时数据质量检查")
        self.last_check_time = datetime.now()
        
        monitoring_config = self.config['monitoring']
        
        if not monitoring_config.get('enabled', True):
            logging.info("监控已禁用")
            return
        
        symbols = monitoring_config.get('symbols', ['BTCUSDT'])
        timeframes = monitoring_config.get('timeframes', ['4h', '1d', '1w', '1M'])
        
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
        
        # 对每个交易对和时间框架执行检查
        for symbol in symbols:
            for timeframe in timeframes:
                try:
                    summary['total_checks'] += 1
                    
                    # 执行检查更新
                    result = self.check_and_update_if_needed(symbol, timeframe)
                    all_results.append(result)
                    
                    # 更新统计
                    if result.get('needed_update', False):
                        summary['needed_updates'] += 1
                        
                        if result.get('update_success', False):
                            summary['successful_updates'] += 1
                        else:
                            summary['failed_updates'] += 1
                    
                    # 更新状态统计
                    freshness = result['details'].get('freshness_check', {})
                    status = freshness.get('status', 'unknown')
                    
                    if status == 'fresh':
                        summary['fresh_data'] += 1
                    elif status == 'stale':
                        summary['stale_data'] += 1
                    elif status == 'missing':
                        summary['missing_data'] += 1
                    
                except Exception as e:
                    logging.error(f"检查失败: {symbol} ({timeframe}) - {e}")
        
        # 生成总结报告
        self._generate_hourly_report(summary, all_results)
        
        logging.info(f"✅ 每小时检查完成: 检查{summary['total_checks']}项, 需要更新{