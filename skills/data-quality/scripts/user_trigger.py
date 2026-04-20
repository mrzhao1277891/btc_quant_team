#!/usr/bin/env python3
"""
用户主动触发接口
支持通过多种方式触发数据质量检查和更新
"""

import sys
import os
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import threading
import logging

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from scripts.data_quality_checker import DataQualityChecker
from scripts.data_updater import DataUpdater

class UserTriggerManager:
    """用户触发管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化用户触发管理器
        
        参数:
            config_path: 配置文件路径
        """
        self.config_path = config_path or "config/user_triggers.yaml"
        self.config = self._load_config()
        
        # 初始化组件
        self.quality_checker = DataQualityChecker()
        self.data_updater = DataUpdater()
        
        # 任务队列和状态
        self.task_queue = []
        self.current_task = None
        self.task_history = []
        self.max_history = 100
        
        # 回调函数
        self.callbacks = {
            'on_task_start': [],
            'on_task_progress': [],
            'on_task_complete': [],
            'on_task_error': []
        }
        
        # 设置日志
        self._setup_logging()
        
        # 启动任务处理器
        self.task_processor_thread = threading.Thread(target=self._process_tasks, daemon=True)
        self.task_processor_thread.start()
        
        logging.info("用户触发管理器初始化完成")
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        config_file = Path(self.config_path)
        
        if config_file.exists():
            try:
                import yaml
                with open(config_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logging.error(f"加载触发配置失败: {e}")
        
        # 默认配置
        return {
            'triggers': {
                'chat': {
                    'enabled': True,
                    'commands': {
                        'check_quality': ['检查数据质量', '数据质量怎么样', 'quality check'],
                        'update_data': ['更新数据', '刷新数据', 'update data'],
                        'check_freshness': ['检查新鲜度', '数据新鲜吗', 'freshness check'],
                        'full_check': ['全面检查', '完整检查', 'full check']
                    }
                },
                'cli': {
                    'enabled': True,
                    'commands': ['check', 'update', 'freshness', 'full']
                },
                'api': {
                    'enabled': False,
                    'port': 8080,
                    'endpoints': ['/api/trigger/check', '/api/trigger/update']
                },
                'telegram': {
                    'enabled': False,
                    'bot_token': None,
                    'chat_id': None
                }
            },
            'notifications': {
                'enabled': True,
                'channels': ['log'],
                'format': 'human'  # human, json, markdown
            },
            'tasks': {
                'max_concurrent': 1,
                'timeout_seconds': 300,
                'retry_attempts': 3
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
                logging.FileHandler(log_dir / 'user_triggers.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def register_callback(self, event: str, callback: Callable):
        """
        注册回调函数
        
        参数:
            event: 事件类型 (on_task_start, on_task_progress, on_task_complete, on_task_error)
            callback: 回调函数
        """
        if event in self.callbacks:
            self.callbacks[event].append(callback)
            self.logger.info(f"注册回调: {event}")
    
    def trigger_check_quality(self, 
                             symbols: List[str] = None, 
                             timeframes: List[str] = None,
                             user_id: str = "anonymous",
                             callback: Optional[Callable] = None) -> str:
        """
        触发数据质量检查
        
        参数:
            symbols: 交易对列表
            timeframes: 时间框架列表
            user_id: 用户ID
            callback: 完成回调
        
        返回:
            str: 任务ID
        """
        task_id = f"check_{int(time.time())}_{user_id}"
        
        task = {
            'id': task_id,
            'type': 'check_quality',
            'user_id': user_id,
            'symbols': symbols or ['BTCUSDT'],
            'timeframes': timeframes or ['4h', '1d', '1w', '1M'],
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'callback': callback
        }
        
        self.task_queue.append(task)
        self.logger.info(f"用户 {user_id} 触发质量检查: {task_id}")
        
        return task_id
    
    def trigger_update_data(self,
                           symbols: List[str] = None,
                           timeframes: List[str] = None,
                           user_id: str = "anonymous",
                           callback: Optional[Callable] = None) -> str:
        """
        触发数据更新
        
        参数:
            symbols: 交易对列表
            timeframes: 时间框架列表
            user_id: 用户ID
            callback: 完成回调
        
        返回:
            str: 任务ID
        """
        task_id = f"update_{int(time.time())}_{user_id}"
        
        task = {
            'id': task_id,
            'type': 'update_data',
            'user_id': user_id,
            'symbols': symbols or ['BTCUSDT'],
            'timeframes': timeframes or ['4h', '1d', '1w', '1M'],
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'callback': callback
        }
        
        self.task_queue.append(task)
        self.logger.info(f"用户 {user_id} 触发数据更新: {task_id}")
        
        return task_id
    
    def trigger_check_freshness(self,
                               symbols: List[str] = None,
                               timeframes: List[str] = None,
                               user_id: str = "anonymous",
                               callback: Optional[Callable] = None) -> str:
        """
        触发新鲜度检查
        
        参数:
            symbols: 交易对列表
            timeframes: 时间框架列表
            user_id: 用户ID
            callback: 完成回调
        
        返回:
            str: 任务ID
        """
        task_id = f"freshness_{int(time.time())}_{user_id}"
        
        task = {
            'id': task_id,
            'type': 'check_freshness',
            'user_id': user_id,
            'symbols': symbols or ['BTCUSDT'],
            'timeframes': timeframes or ['4h', '1d', '1w', '1M'],
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'callback': callback
        }
        
        self.task_queue.append(task)
        self.logger.info(f"用户 {user_id} 触发新鲜度检查: {task_id}")
        
        return task_id
    
    def trigger_full_check(self,
                          symbols: List[str] = None,
                          timeframes: List[str] = None,
                          user_id: str = "anonymous",
                          callback: Optional[Callable] = None) -> str:
        """
        触发全面检查（质量+新鲜度+更新）
        
        参数:
            symbols: 交易对列表
            timeframes: 时间框架列表
            user_id: 用户ID
            callback: 完成回调
        
        返回:
            str: 任务ID
        """
        task_id = f"full_{int(time.time())}_{user_id}"
        
        task = {
            'id': task_id,
            'type': 'full_check',
            'user_id': user_id,
            'symbols': symbols or ['BTCUSDT'],
            'timeframes': timeframes or ['4h', '1d', '1w', '1M'],
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'callback': callback
        }
        
        self.task_queue.append(task)
        self.logger.info(f"用户 {user_id} 触发全面检查: {task_id}")
        
        return task_id
    
    def _process_tasks(self):
        """处理任务队列"""
        while True:
            if self.task_queue and self.current_task is None:
                task = self.task_queue.pop(0)
                self.current_task = task
                
                try:
                    self._execute_task(task)
                except Exception as e:
                    self.logger.error(f"任务执行失败 {task['id']}: {e}")
                    task['status'] = 'failed'
                    task['error'] = str(e)
                    task['completed_at'] = datetime.now().isoformat()
                    
                    # 触发错误回调
                    self._trigger_callbacks('on_task_error', task)
                
                finally:
                    self.current_task = None
            
            time.sleep(0.1)  # 避免CPU占用过高
    
    def _execute_task(self, task: Dict[str, Any]):
        """执行任务"""
        task_id = task['id']
        task_type = task['type']
        user_id = task['user_id']
        
        self.logger.info(f"开始执行任务: {task_id} ({task_type})")
        
        # 触发开始回调
        task['status'] = 'running'
        task['started_at'] = datetime.now().isoformat()
        self._trigger_callbacks('on_task_start', task)
        
        results = {}
        
        try:
            if task_type == 'check_quality':
                results = self._execute_quality_check(task)
            
            elif task_type == 'update_data':
                results = self._execute_data_update(task)
            
            elif task_type == 'check_freshness':
                results = self._execute_freshness_check(task)
            
            elif task_type == 'full_check':
                results = self._execute_full_check(task)
            
            # 更新任务状态
            task['status'] = 'completed'
            task['results'] = results
            task['completed_at'] = datetime.now().isoformat()
            
            # 保存到历史
            self.task_history.append(task.copy())
            if len(self.task_history) > self.max_history:
                self.task_history = self.task_history[-self.max_history:]
            
            self.logger.info(f"任务完成: {task_id}")
            
            # 触发完成回调
            self._trigger_callbacks('on_task_complete', task)
            
            # 执行用户回调
            if task.get('callback'):
                try:
                    task['callback'](task)
                except Exception as e:
                    self.logger.error(f"用户回调执行失败: {e}")
        
        except Exception as e:
            self.logger.error(f"任务执行异常 {task_id}: {e}")
            task['status'] = 'failed'
            task['error'] = str(e)
            task['completed_at'] = datetime.now().isoformat()
            
            # 触发错误回调
            self._trigger_callbacks('on_task_error', task)
            
            raise
    
    def _execute_quality_check(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行质量检查"""
        symbols = task['symbols']
        timeframes = task['timeframes']
        
        results = {
            'task_type': 'quality_check',
            'timestamp': datetime.now().isoformat(),
            'symbols': symbols,
            'timeframes': timeframes,
            'checks': {}
        }
        
        total_checks = len(symbols) * len(timeframes)
        completed_checks = 0
        
        for symbol in symbols:
            results['checks'][symbol] = {}
            
            for timeframe in timeframes:
                # 触发进度回调
                completed_checks += 1
                progress = completed_checks / total_checks
                self._trigger_callbacks('on_task_progress', {
                    'task_id': task['id'],
                    'progress': progress,
                    'current': f"{symbol}({timeframe})",
                    'message': f"检查 {symbol}({timeframe})..."
                })
                
                try:
                    # 执行质量检查
                    report = self.quality_checker.check_comprehensive(
                        symbol=symbol,
                        timeframe=timeframe,
                        days=7
                    )
                    
                    results['checks'][symbol][timeframe] = {
                        'overall_score': report.overall_score,
                        'check_results': {
                            name: {
                                'score': result.get('score', 0),
                                'status': result.get('status', 'UNKNOWN')
                            }
                            for name, result in report.check_results.items()
                        },
                        'status': 'success'
                    }
                    
                    self.logger.info(f"质量检查完成: {symbol}({timeframe}) - {report.overall_score:.1%}")
                    
                except Exception as e:
                    self.logger.error(f"质量检查失败 {symbol}({timeframe}): {e}")
                    results['checks'][symbol][timeframe] = {
                        'error': str(e),
                        'status': 'failed'
                    }
        
        # 计算总体评分
        all_scores = []
        for symbol in symbols:
            for timeframe in timeframes:
                check_result = results['checks'][symbol].get(timeframe, {})
                if check_result.get('status') == 'success':
                    all_scores.append(check_result.get('overall_score', 0))
        
        if all_scores:
            results['overall_score'] = sum(all_scores) / len(all_scores)
        else:
            results['overall_score'] = 0
        
        return results
    
    def _execute_data_update(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行数据更新"""
        symbols = task['symbols']
        timeframes = task['timeframes']
        
        results = {
            'task_type': 'data_update',
            'timestamp': datetime.now().isoformat(),
            'symbols': symbols,
            'timeframes': timeframes,
            'updates': {}
        }
        
        total_updates = len(symbols) * len(timeframes)
        completed_updates = 0
        
        for symbol in symbols:
            results['updates'][symbol] = {}
            
            for timeframe in timeframes:
                # 触发进度回调
                completed_updates += 1
                progress = completed_updates / total_updates
                self._trigger_callbacks('on_task_progress', {
                    'task_id': task['id'],
                    'progress': progress,
                    'current': f"{symbol}({timeframe})",
                    'message': f"更新 {symbol}({timeframe})..."
                })
                
                try:
                    # 执行数据更新
                    update_result = self.data_updater.update_data(
                        symbol=symbol,
                        timeframe=timeframe,
                        limit=100
                    )
                    
                    results['updates'][symbol][timeframe] = update_result
                    self.logger.info(f"数据更新完成: {symbol}({timeframe}) - {update_result.get('success', False)}")
                    
                except Exception as e:
                    self.logger.error(f"数据更新失败 {symbol}({timeframe}): {e}")
                    results['updates'][symbol][timeframe] = {
                        'success': False,
                        'error': str(e)
                    }
        
        # 统计更新结果
        successful = 0
        failed = 0
        
        for symbol in symbols:
            for timeframe in timeframes:
                update_result = results['updates'][symbol].get(timeframe, {})
                if update_result.get('success'):
                    successful += 1
                else:
                    failed += 1
        
        results['summary'] = {
            'total': total_updates,
            'successful': successful,
            'failed': failed,
            'success_rate': successful / total_updates if total_updates > 0 else 0
        }
        
        return results
    
    def _execute_freshness_check(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行新鲜度检查"""
        symbols = task['symbols']
        timeframes = task['timeframes']
        
        results = {
            'task_type': 'freshness_check',
            'timestamp': datetime.now().isoformat(),
            'symbols': symbols,
            'timeframes': timeframes,
            'freshness': {}
        }
        
        total_checks = len(symbols) * len(timeframes)
        completed_checks = 0
        
        for symbol in symbols:
            results['freshness'][symbol] = {}
            
            for timeframe in timeframes:
                # 触发进度回调
                completed_checks += 1
                progress = completed_checks / total_checks
                self._trigger_callbacks('on_task_progress', {
                    'task_id': task['id'],
                    'progress': progress,
                    'current': f"{symbol}({timeframe})",
                    'message': f"检查新鲜度 {symbol}({timeframe})..."
                })
                
                try:
                    # 检查新鲜度
                    threshold_hours = {
                        '4h': 6,
                        '1d': 24,
                        '1w': 168,
                        '1M': 720
                    }.get(timeframe, 24)
                    
                    is_stale, freshness_info = self.data_updater.check_freshness(
                        symbol=symbol,
                        timeframe=time