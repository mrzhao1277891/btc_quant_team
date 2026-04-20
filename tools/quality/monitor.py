#!/usr/bin/env python3
"""
数据质量监控工具

职责: 持续监控数据质量，实时检测问题，发送警报

主要功能:
- 实时质量监控: 持续检查数据质量
- 异常检测: 自动检测数据异常
- 趋势分析: 分析质量变化趋势
- 警报系统: 发送质量警报
- 仪表板: 提供质量可视化

监控维度:
1. 实时监控: 当前数据质量
2. 历史监控: 质量变化趋势
3. 预测监控: 质量预测
4. 对比监控: 与基准对比

版本: 1.0.0
作者: 量化团队
更新日期: 2026-04-19
"""

import time
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import numpy as np
from collections import deque
import warnings

class AlertLevel(Enum):
    """警报级别"""
    INFO = "info"        # 信息: 仅供参考
    WARNING = "warning"  # 警告: 需要注意
    ERROR = "error"      # 错误: 需要处理
    CRITICAL = "critical"  # 严重: 立即处理

class MonitorType(Enum):
    """监控类型"""
    REALTIME = "realtime"    # 实时监控
    HISTORICAL = "historical"  # 历史监控
    PREDICTIVE = "predictive"  # 预测监控
    COMPARATIVE = "comparative"  # 对比监控

@dataclass
class AlertRule:
    """警报规则"""
    name: str
    condition: str
    level: AlertLevel
    message_template: str
    cooldown_seconds: int = 300  # 冷却时间(秒)
    enabled: bool = True
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "condition": self.condition,
            "level": self.level.value,
            "message_template": self.message_template,
            "cooldown_seconds": self.cooldown_seconds,
            "enabled": self.enabled,
            "parameters": self.parameters
        }

@dataclass
class Alert:
    """警报"""
    rule: AlertRule
    timestamp: str
    message: str
    data: Dict[str, Any]
    acknowledged: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "rule": self.rule.to_dict(),
            "timestamp": self.timestamp,
            "message": self.message,
            "data": self.data,
            "acknowledged": self.acknowledged
        }

@dataclass
class MonitorMetric:
    """监控指标"""
    name: str
    value: float
    timestamp: str
    unit: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "value": self.value,
            "timestamp": self.timestamp,
            "unit": self.unit,
            "metadata": self.metadata
        }

@dataclass
class MonitorReport:
    """监控报告"""
    monitor_name: str
    timestamp: str
    duration_seconds: float
    metrics: List[MonitorMetric]
    alerts: List[Alert]
    summary: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "monitor_name": self.monitor_name,
            "timestamp": self.timestamp,
            "duration_seconds": round(self.duration_seconds, 2),
            "metrics": [metric.to_dict() for metric in self.metrics],
            "alerts": [alert.to_dict() for alert in self.alerts],
            "summary": self.summary
        }
    
    def to_json(self, indent: int = 2) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    def print_summary(self):
        """打印摘要"""
        print("=" * 60)
        print(f"📡 数据质量监控报告: {self.monitor_name}")
        print("=" * 60)
        print(f"📅 监控时间: {self.timestamp}")
        print(f"⏱️  监控时长: {self.duration_seconds:.1f} 秒")
        print(f"📊 收集指标: {len(self.metrics)} 个")
        print(f"🚨 触发警报: {len(self.alerts)} 个")
        print()
        
        # 显示关键指标
        key_metrics = [m for m in self.metrics if m.name in ["data_freshness", "completeness_score", "accuracy_score"]]
        if key_metrics:
            print("📈 关键指标:")
            for metric in key_metrics:
                print(f"  {metric.name}: {metric.value:.2f}{metric.unit or ''}")
            print()
        
        # 显示警报
        if self.alerts:
            print("🚨 触发的警报:")
            for alert in self.alerts:
                level_emoji = {
                    "info": "ℹ️",
                    "warning": "⚠️",
                    "error": "❌",
                    "critical": "🔥"
                }.get(alert.rule.level.value, "📢")
                
                print(f"  {level_emoji} [{alert.rule.level.value.upper()}] {alert.message}")
                if alert.rule.name:
                    print(f"     规则: {alert.rule.name}")
            print()
        
        # 显示趋势
        trend = self.summary.get("trend", {})
        if trend:
            print("📈 质量趋势:")
            for key, value in trend.items():
                if isinstance(value, (int, float)):
                    print(f"  {key}: {value:+.2f}")
            print()
        
        print("=" * 60)

class DataQualityMonitor:
    """数据质量监控器"""
    
    def __init__(
        self,
        monitor_name: str,
        check_interval: int = 300,  # 默认5分钟
        alert_rules: Optional[List[AlertRule]] = None,
        history_size: int = 1000
    ):
        """
        初始化监控器
        
        参数:
            monitor_name: 监控器名称
            check_interval: 检查间隔(秒)
            alert_rules: 警报规则列表
            history_size: 历史记录大小
        """
        self.monitor_name = monitor_name
        self.check_interval = check_interval
        self.alert_rules = alert_rules or []
        self.history_size = history_size
        
        # 监控状态
        self.is_running = False
        self.thread = None
        self.last_check_time = None
        
        # 历史数据
        self.metrics_history = deque(maxlen=history_size)
        self.alerts_history = deque(maxlen=history_size)
        self.reports_history = deque(maxlen=100)
        
        # 警报冷却
        self.alert_cooldowns = {}
        
        # 内置警报规则
        self._builtin_rules = self._create_builtin_rules()
    
    def _create_builtin_rules(self) -> Dict[str, AlertRule]:
        """创建内置警报规则"""
        return {
            "data_freshness_critical": AlertRule(
                name="数据新鲜度严重下降",
                condition="data_freshness < 0.5",
                level=AlertLevel.CRITICAL,
                message_template="数据新鲜度严重下降: {value:.1%} (阈值: 50%)",
                cooldown_seconds=600,
                parameters={"threshold": 0.5}
            ),
            
            "data_freshness_warning": AlertRule(
                name="数据新鲜度警告",
                condition="data_freshness < 0.8",
                level=AlertLevel.WARNING,
                message_template="数据新鲜度下降: {value:.1%} (阈值: 80%)",
                cooldown_seconds=300,
                parameters={"threshold": 0.8}
            ),
            
            "completeness_critical": AlertRule(
                name="数据完整性严重问题",
                condition="completeness_score < 0.6",
                level=AlertLevel.CRITICAL,
                message_template="数据完整性严重问题: {value:.1%} (阈值: 60%)",
                cooldown_seconds=600,
                parameters={"threshold": 0.6}
            ),
            
            "completeness_warning": AlertRule(
                name="数据完整性警告",
                condition="completeness_score < 0.85",
                level=AlertLevel.WARNING,
                message_template="数据完整性下降: {value:.1%} (阈值: 85%)",
                cooldown_seconds=300,
                parameters={"threshold": 0.85}
            ),
            
            "accuracy_critical": AlertRule(
                name="数据准确性严重问题",
                condition="accuracy_score < 0.7",
                level=AlertLevel.CRITICAL,
                message_template="数据准确性严重问题: {value:.1%} (阈值: 70%)",
                cooldown_seconds=600,
                parameters={"threshold": 0.7}
            ),
            
            "outlier_detected": AlertRule(
                name="检测到异常值",
                condition="outlier_count > 10",
                level=AlertLevel.WARNING,
                message_template="检测到 {value} 个异常值",
                cooldown_seconds=300,
                parameters={"threshold": 10}
            ),
            
            "missing_data_increase": AlertRule(
                name="缺失数据增加",
                condition="missing_data_increase > 0.1",
                level=AlertLevel.WARNING,
                message_template="缺失数据增加: {value:.1%}",
                cooldown_seconds=300,
                parameters={"threshold": 0.1}
            ),
            
            "data_delay_warning": AlertRule(
                name="数据延迟警告",
                condition="data_delay_minutes > 30",
                level=AlertLevel.WARNING,
                message_template="数据延迟: {value:.0f} 分钟",
                cooldown_seconds=300,
                parameters={"threshold": 30}
            ),
            
            "data_delay_critical": AlertRule(
                name="数据延迟严重",
                condition="data_delay_minutes > 120",
                level=AlertLevel.CRITICAL,
                message_template="数据严重延迟: {value:.0f} 分钟",
                cooldown_seconds=600,
                parameters={"threshold": 120}
            ),
            
            "quality_trend_down": AlertRule(
                name="质量趋势下降",
                condition="quality_trend < -0.1",
                level=AlertLevel.WARNING,
                message_template="质量趋势下降: {value:.2f}",
                cooldown_seconds=600,
                parameters={"threshold": -0.1}
            )
        }
    
    def add_alert_rule(self, rule: AlertRule):
        """添加警报规则"""
        self.alert_rules.append(rule)
    
    def add_alert_rules(self, rules: List[AlertRule]):
        """批量添加警报规则"""
        self.alert_rules.extend(rules)
    
    def add_builtin_rule(self, rule_name: str):
        """添加内置警报规则"""
        if rule_name in self._builtin_rules:
            self.alert_rules.append(self._builtin_rules[rule_name])
        else:
            raise ValueError(f"未知的内置规则: {rule_name}")
    
    def start_monitoring(
        self,
        data_source: Callable[[], pd.DataFrame],
        dataset_name: str,
        check_callback: Optional[Callable] = None
    ):
        """
        开始监控
        
        参数:
            data_source: 数据源函数，返回DataFrame
            dataset_name: 数据集名称
            check_callback: 检查回调函数
        """
        if self.is_running:
            print(f"⚠️  监控器 '{self.monitor_name}' 已经在运行")
            return
        
        self.is_running = True
        self.thread = threading.Thread(
            target=self._monitoring_loop,
            args=(data_source, dataset_name, check_callback),
            daemon=True
        )
        self.thread.start()
        
        print(f"✅ 开始监控: {self.monitor_name} (数据集: {dataset_name})")
        print(f"  检查间隔: {self.check_interval} 秒")
        print(f"  警报规则: {len(self.alert_rules)} 条")
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        
        print(f"🛑 停止监控: {self.monitor_name}")
    
    def _monitoring_loop(
        self,
        data_source: Callable[[], pd.DataFrame],
        dataset_name: str,
        check_callback: Optional[Callable] = None
    ):
        """监控循环"""
        while self.is_running:
            try:
                start_time = time.time()
                
                # 获取数据
                df = data_source()
                
                # 执行检查
                report = self._perform_check(df, dataset_name, start_time)
                
                # 保存报告
                self.reports_history.append(report)
                
                # 调用回调
                if check_callback:
                    check_callback(report)
                
                # 打印摘要
                report.print_summary()
                
                # 更新最后检查时间
                self.last_check_time = datetime.now()
                
                # 等待下一个检查
                elapsed = time.time() - start_time
                sleep_time = max(1, self.check_interval - elapsed)
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
            except Exception as e:
                print(f"❌ 监控检查失败: {e}")
                time.sleep(min(60, self.check_interval))  # 失败后等待
    
    def _perform_check(
        self,
        df: pd.DataFrame,
        dataset_name: str,
        start_time: float
    ) -> MonitorReport:
        """执行检查"""
        metrics = []
        alerts = []
        
        # 1. 计算基本指标
        basic_metrics = self._calculate_basic_metrics(df)
        metrics.extend(basic_metrics)
        
        # 2. 计算质量指标
        quality_metrics = self._calculate_quality_metrics(df)
        metrics.extend(quality_metrics)
        
        # 3. 计算趋势指标
        trend_metrics = self._calculate_trend_metrics(metrics)
        metrics.extend(trend_metrics)
        
        # 4. 检查警报
        current_alerts = self._check_alerts(metrics)
        alerts.extend(current_alerts)
        
        # 5. 保存指标历史
        for metric in metrics:
            self.metrics_history.append(metric)
        
        # 6. 保存警报历史
        for alert in alerts:
            self.alerts_history.append(alert)
        
        # 7. 生成报告
        duration = time.time() - start_time
        
        return MonitorReport(
            monitor_name=self.monitor_name,
            timestamp=datetime.now().isoformat(),
            duration_seconds=duration,
            metrics=metrics,
            alerts=alerts,
            summary=self._generate_summary(metrics, alerts)
        )
    
    def _calculate_basic_metrics(self, df: pd.DataFrame) -> List[MonitorMetric]:
        """计算基本指标"""
        metrics = []
        
        # 数据大小
        metrics.append(MonitorMetric(
            name="row_count",
            value=len(df),
            timestamp=datetime.now().isoformat(),
            unit="rows",
            metadata={"description": "数据行数"}
        ))
        
        metrics.append(MonitorMetric(
            name="column_count",
            value=len(df.columns),
            timestamp=datetime.now().isoformat(),
            unit="columns",
            metadata={"description": "数据列数"}
        ))
        
        # 数据新鲜度 (基于时间戳列)
        time_columns = [col for col in df.columns if 'time' in col.lower() or 'date' in col.lower()]
        if time_columns:
            time_col = time_columns[0]
            if pd.api.types.is_datetime64_any_dtype(df[time_col]):
                latest_time = df[time_col].max()
                if pd.notna(latest_time):
                    if isinstance(latest_time, pd.Timestamp):
                        latest_time = latest_time.to_pydatetime()
                    
                    delay = datetime.now() - latest_time
                    delay_minutes = delay.total_seconds() / 60
                    
                    metrics.append(MonitorMetric(
                        name="data_delay_minutes",
                        value=delay_minutes,
                        timestamp=datetime.now().isoformat(),
                        unit="minutes",
                        metadata={"description": "数据延迟分钟数"}
                    ))
                    
                    # 数据新鲜度分数 (延迟越小分数越高)
                    freshness_score = max(0, 1 - (delay_minutes / (24 * 60)))  # 24小时基准
                    metrics.append(MonitorMetric(
                        name="data_freshness",
                        value=freshness_score,
                        timestamp=datetime.now().isoformat(),
                        unit="score",
                        metadata={"description": "数据新鲜度分数"}
                    ))
        
        return metrics
    
    def _calculate_quality_metrics(self, df: pd.DataFrame) -> List[MonitorMetric]:
        """计算质量指标"""
        metrics = []
        
        # 完整性指标
        total_cells = df.size
        null_cells = df.isnull().sum().sum()
        completeness_ratio = 1 - (null_cells / total_cells) if total_cells > 0 else 0
        
        metrics.append(MonitorMetric(
            name="completeness_score",
            value=completeness_ratio,
            timestamp=datetime.now().isoformat(),
            unit="score",
            metadata={
                "description": "数据完整性分数",
                "null_cells