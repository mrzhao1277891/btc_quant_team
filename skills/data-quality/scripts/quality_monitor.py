#!/usr/bin/env python3
"""
数据质量监控器 - 增强版
功能：定时检查数据质量和新鲜度，自动更新过时数据
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

from .data_quality_checker import DataQualityChecker, QualityReport
from .data_updater import DataUpdater  # 稍后创建

class QualityMonitor:
    """数据质量监控器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化质量监控器
        
        参数:
            config_path: 配置文件路径
        """
        self.config_path = config_path or "config/monitor.yaml"
        self.config = self._load_config()
        
        # 初始化组件
        self.quality_checker = DataQualityChecker()
        self.data_updater = DataUpdater()
        
        # 监控状态
        self.is_running = False
        self.monitor_thread = None
        self.last_check_time = None
        self.check_history = []
        
        # 设置日志
        self._setup_logging()
        
        logging.info("数据质量监控器初始化完成")
    
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
                'check_interval_minutes': 60,  # 检查间隔（分钟）
                'auto_update': True,           # 自动更新过时数据
                'alert_on_failure': True,      # 失败时告警
                'symbols': ['BTCUSDT'],        # 监控的交易对
                'timeframes': ['1d', '4h', '1w', '1M'],  # 监控的时间框架
                'freshness_thresholds': {      # 新鲜度阈值（小时）
                    '1h': 2,
                    '4h': 6,
                    '1d': 24,
                    '1w': 168,
                    '1M': 720
                }
            },
            'alerts': {
                'enabled': True,
                'channels': ['log'],  # log, telegram, email
                'telegram_bot_token': None,
                'telegram_chat_id': None,
                'min_severity': 'warning'  # info, warning, error, critical
            },
            'reporting': {
                'generate_reports': True,
                'report_dir': 'reports',
                'keep_days': 30
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
                logging.FileHandler(log_dir / 'quality_monitor.log'),
                logging.StreamHandler()
            ]
        )
    
    def check_data_quality(self, symbol: str, timeframe: str) -> QualityReport:
        """
        检查数据质量
        
        参数:
            symbol: 交易对符号
            timeframe: 时间框架
        
        返回:
            QualityReport: 质量报告
        """
        logging.info(f"检查数据质量: {symbol} ({timeframe})")
        
        try:
            # 执行质量检查
            report = self.quality_checker.check_comprehensive(
                symbol=symbol,
                timeframe=timeframe,
                days=7  # 检查最近7天数据
            )
            
            # 记录检查历史
            check_record = {
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol,
                'timeframe': timeframe,
                'overall_score': report.overall_score,
                'freshness_score': report.check_results.get('timeliness', {}).get('score', 0),
                'status': 'PASS' if report.overall_score >= 0.9 else 'WARNING' if report.overall_score >= 0.7 else 'FAIL'
            }
            
            self.check_history.append(check_record)
            
            # 保持历史记录大小
            if len(self.check_history) > 1000:
                self.check_history = self.check_history[-1000:]
            
            logging.info(f"质量检查完成: {symbol} ({timeframe}) - 评分: {report.overall_score:.1%}")
            
            return report
            
        except Exception as e:
            logging.error(f"质量检查失败: {symbol} ({timeframe}) - {e}")
            raise
    
    def check_and_update_if_stale(self, symbol: str, timeframe: str) -> Dict[str, Any]:
        """
        检查并更新过时数据
        
        参数:
            symbol: 交易对符号
            timeframe: 时间框架
        
        返回:
            Dict: 更新结果
        """
        logging.info(f"检查并更新过时数据: {symbol} ({timeframe})")
        
        result = {
            'symbol': symbol,
            'timeframe': timeframe,
            'timestamp': datetime.now().isoformat(),
            'checked': True,
            'needed_update': False,
            'update_success': False,
            'details': {}
        }
        
        try:
            # 1. 检查数据新鲜度
            freshness_threshold = self.config['monitoring']['freshness_thresholds'].get(
                timeframe, 
                24  # 默认24小时
            )
            
            is_stale, freshness_info = self.data_updater.check_freshness(
                symbol=symbol,
                timeframe=timeframe,
                threshold_hours=freshness_threshold
            )
            
            result['details']['freshness_check'] = freshness_info
            
            if not is_stale:
                # 数据新鲜，无需更新
                logging.info(f"数据新鲜: {symbol} ({timeframe})")
                result['needed_update'] = False
                return result
            
            # 2. 数据过时，执行更新
            logging.warning(f"数据过时，开始更新: {symbol} ({timeframe})")
            result['needed_update'] = True
            
            update_result = self.data_updater.update_data(
                symbol=symbol,
                timeframe=timeframe,
                limit=100  # 更新最近100条数据
            )
            
            result['details']['update_result'] = update_result
            result['update_success'] = update_result.get('success', False)
            
            if result['update_success']:
                logging.info(f"数据更新成功: {symbol} ({timeframe})")
            else:
                logging.error(f"数据更新失败: {symbol} ({timeframe})")
            
            return result
            
        except Exception as e:
            logging.error(f"检查更新失败: {symbol} ({timeframe}) - {e}")
            result['error'] = str(e)
            return result
    
    def send_alert(self, message: str, severity: str = 'warning'):
        """
        发送告警
        
        参数:
            message: 告警消息
            severity: 严重程度 (info, warning, error, critical)
        """
        if not self.config['alerts']['enabled']:
            return
        
        # 检查严重程度阈值
        severity_levels = {'info': 0, 'warning': 1, 'error': 2, 'critical': 3}
        min_severity = self.config['alerts'].get('min_severity', 'warning')
        
        if severity_levels.get(severity, 0) < severity_levels.get(min_severity, 1):
            return
        
        # 添加时间戳
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_message = f"[{timestamp}] [{severity.upper()}] {message}"
        
        # 发送到配置的渠道
        channels = self.config['alerts'].get('channels', ['log'])
        
        for channel in channels:
            try:
                if channel == 'log':
                    if severity == 'error' or severity == 'critical':
                        logging.error(full_message)
                    elif severity == 'warning':
                        logging.warning(full_message)
                    else:
                        logging.info(full_message)
                
                elif channel == 'telegram':
                    self._send_telegram_alert(full_message)
                
                elif channel == 'email':
                    self._send_email_alert(full_message)
                    
            except Exception as e:
                logging.error(f"发送告警到 {channel} 失败: {e}")
    
    def _send_telegram_alert(self, message: str):
        """发送Telegram告警"""
        bot_token = self.config['alerts'].get('telegram_bot_token')
        chat_id = self.config['alerts'].get('telegram_chat_id')
        
        if not bot_token or not chat_id:
            logging.warning("Telegram告警配置不完整")
            return
        
        try:
            import requests
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
        except Exception as e:
            logging.error(f"发送Telegram告警失败: {e}")
    
    def _send_email_alert(self, message: str):
        """发送Email告警"""
        # 这里可以添加Email发送逻辑
        pass
    
    def generate_monitoring_report(self) -> Dict[str, Any]:
        """
        生成监控报告
        
        返回:
            Dict: 监控报告
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'monitoring_duration': None,
            'checks_performed': len(self.check_history),
            'overall_status': 'UNKNOWN',
            'symbols_monitored': self.config['monitoring'].get('symbols', []),
            'check_summary': {},
            'issues_found': [],
            'recommendations': []
        }
        
        if self.last_check_time:
            report['monitoring_duration'] = str(datetime.now() - self.last_check_time)
        
        # 分析检查历史
        if self.check_history:
            # 按交易对和时间框架分组
            summary = {}
            
            for check in self.check_history[-100:]:  # 最近100次检查
                key = f"{check['symbol']}_{check['timeframe']}"
                
                if key not in summary:
                    summary[key] = {
                        'symbol': check['symbol'],
                        'timeframe': check['timeframe'],
                        'checks': 0,
                        'scores': [],
                        'last_status': 'UNKNOWN',
                        'last_check': check['timestamp']
                    }
                
                summary[key]['checks'] += 1
                summary[key]['scores'].append(check['overall_score'])
                summary[key]['last_status'] = check['status']
                summary[key]['last_check'] = max(
                    summary[key]['last_check'], 
                    check['timestamp']
                )
            
            # 计算统计信息
            for key, data in summary.items():
                scores = data['scores']
                if scores:
                    data['avg_score'] = sum(scores) / len(scores)
                    data['min_score'] = min(scores)
                    data['max_score'] = max(scores)
                    data['trend'] = 'stable' if len(scores) < 2 else (
                        'improving' if scores[-1] > scores[0] else 'declining'
                    )
                else:
                    data['avg_score'] = 0
                    data['min_score'] = 0
                    data['max_score'] = 0
                    data['trend'] = 'unknown'
                
                del data['scores']
            
            report['check_summary'] = summary
            
            # 识别问题
            for key, data in summary.items():
                if data['avg_score'] < 0.8:
                    report['issues_found'].append({
                        'symbol': data['symbol'],
                        'timeframe': data['timeframe'],
                        'issue': f"平均质量评分低: {data['avg_score']:.1%}",
                        'severity': 'warning' if data['avg_score'] >= 0.6 else 'error'
                    })
                
                if data['last_status'] == 'FAIL':
                    report['issues_found'].append({
                        'symbol': data['symbol'],
                        'timeframe': data['timeframe'],
                        'issue': f"最近检查失败",
                        'severity': 'error'
                    })
            
            # 生成建议
            if report['issues_found']:
                report['recommendations'].append("检查并修复发现的数据质量问题")
            
            if any(data['trend'] == 'declining' for data in summary.values()):
                report['recommendations'].append("关注数据质量下降趋势")
            
            # 确定总体状态
            if any(issue['severity'] == 'error' for issue in report['issues_found']):
                report['overall_status'] = 'FAIL'
            elif any(issue['severity'] == 'warning' for issue in report['issues_found']):
                report['overall_status'] = 'WARNING'
            else:
                report['overall_status'] = 'PASS'
        
        return report
    
    def save_report(self, report: Dict[str, Any]):
        """保存报告到文件"""
        if not self.config['reporting']['generate_reports']:
            return
        
        report_dir = Path(self.config['reporting']['report_dir'])
        report_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"quality_monitor_report_{timestamp}.json"
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            logging.info(f"监控报告已保存: {report_file}")
            
            # 清理旧报告
            self._cleanup_old_reports()
            
        except Exception as e:
            logging.error(f"保存监控报告失败: {e}")
    
    def _cleanup_old_reports(self):
        """清理旧报告"""
        keep_days = self.config['reporting'].get('keep_days', 30)
        report_dir = Path(self.config['reporting']['report_dir'])
        
        if not report_dir.exists():
            return
        
        cutoff_time = datetime.now() - timedelta(days=keep_days)
        
        for report_file in report_dir.glob("quality_monitor_report_*.json"):
            try:
                # 从文件名解析时间
                filename = report_file.stem
                time_str = filename.replace("quality_monitor_report_", "")
                file_time = datetime.strptime(time_str, "%Y%m%d_%H%M%S")
                
                if file_time < cutoff_time:
                    report_file.unlink()
                    logging.info(f"删除旧报告: {report_file}")
                    
            except Exception as e:
                logging.error(f"处理报告文件失败 {report_file}: {e}")
    
    def run_monitoring_cycle(self):
        """运行一个监控周期"""
        logging.info("开始监控周期")
        self.last_check_time = datetime.now()
        
        monitoring_config = self.config['monitoring']
        
        if not monitoring_config.get('enabled', True):
            logging.info("监控已禁用")
            return
        
        symbols = monitoring_config.get('symbols', ['BTCUSDT'])
        timeframes = monitoring_config.get('timeframes', ['1d', '4h', '1w', '1M'])
        auto_update = monitoring_config.get('auto_update', True)
        
        all_results = []
        issues_found = []
        
        # 对每个交易对和时间框架执行检查
        for symbol in symbols:
            for timeframe in timeframes:
                try:
                    # 1. 检查数据质量
                    quality_report = self.check_data_quality(symbol, timeframe)
                    
                    # 2. 检查是否需要更新
                    if auto_update:
                        update_result = self.check_and_update_if_stale(symbol, timeframe)
                        all_results.append(update_result)
                        
                        if update_result.get('needed_update', False):
                            if update_result.get('update_success', False):
                                logging.info(f"数据更新成功: {symbol} ({timeframe})")
                            else:
                                error_msg = f"数据更新失败: {symbol} ({timeframe})"
                                logging.error(error_msg)
                                self.send_alert(error_msg, 'error')
                                issues_found.append(error_msg)
                    
                    # 3. 检查质量评分，发送告警
                    if quality_report.overall_score < 0.8:
                        warning_msg = f"数据质量低: {symbol} ({timeframe}) - 评分: {quality_report.overall_score:.1%}"
                        logging.warning(warning_msg)
                        self.send_alert(warning_msg, 'warning')
                        issues_found.append(warning