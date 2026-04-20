#!/usr/bin/env python3
"""
数据质量检查器

功能:
1. 数据完整性检查
2. 数据一致性检查
3. 数据准确性检查
4. 数据及时性检查
5. 综合质量评分

版本: 1.0.0
作者: 数据质量专家
更新日期: 2026-04-19
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging
import yaml
from pathlib import Path
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CheckStatus(Enum):
    """检查状态"""
    PASS = "pass"          # 通过
    WARNING = "warning"    # 警告
    FAIL = "fail"          # 失败
    ERROR = "error"        # 错误

class CheckSeverity(Enum):
    """检查严重性"""
    LOW = "low"           # 低
    MEDIUM = "medium"     # 中
    HIGH = "high"         # 高
    CRITICAL = "critical" # 严重

@dataclass
class QualityIssue:
    """质量问题"""
    id: str
    type: str
    severity: CheckSeverity
    description: str
    location: Optional[str] = None
    value: Optional[Any] = None
    expected: Optional[Any] = None
    timestamp: Optional[datetime] = None
    suggestions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        if self.timestamp:
            data['timestamp'] = self.timestamp.isoformat()
        return data
    
    def print_issue(self):
        """打印问题"""
        severity_emoji = {
            CheckSeverity.LOW: "ℹ️",
            CheckSeverity.MEDIUM: "⚠️",
            CheckSeverity.HIGH: "🚨",
            CheckSeverity.CRITICAL: "🔥"
        }
        
        print(f"{severity_emoji.get(self.severity, '❓')} [{self.severity.value}] {self.type}")
        print(f"  描述: {self.description}")
        
        if self.location:
            print(f"  位置: {self.location}")
        
        if self.value is not None:
            print(f"  实际值: {self.value}")
        
        if self.expected is not None:
            print(f"  期望值: {self.expected}")
        
        if self.timestamp:
            print(f"  时间: {self.timestamp}")
        
        if self.suggestions:
            print(f"  建议:")
            for suggestion in self.suggestions:
                print(f"    • {suggestion}")

@dataclass
class CheckResult:
    """检查结果"""
    check_name: str
    status: CheckStatus
    score: float  # 0-1
    issues: List[QualityIssue] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['status'] = self.status.value
        data['issues'] = [issue.to_dict() for issue in self.issues]
        
        if self.start_time:
            data['start_time'] = self.start_time.isoformat()
        
        if self.end_time:
            data['end_time'] = self.end_time.isoformat()
        
        return data
    
    def print_result(self):
        """打印结果"""
        status_emoji = {
            CheckStatus.PASS: "✅",
            CheckStatus.WARNING: "⚠️",
            CheckStatus.FAIL: "❌",
            CheckStatus.ERROR: "💥"
        }
        
        print(f"{status_emoji.get(self.status, '❓')} {self.check_name}: {self.score:.1%} [{self.status.value}]")
        
        if self.metrics:
            print(f"  指标:")
            for key, value in self.metrics.items():
                print(f"    {key}: {value}")
        
        if self.issues:
            print(f"  发现 {len(self.issues)} 个问题:")
            for issue in self.issues[:3]:  # 只显示前3个
                print(f"    • {issue.type}: {issue.description}")
            
            if len(self.issues) > 3:
                print(f"    ... 还有 {len(self.issues) - 3} 个问题")

@dataclass
class QualityReport:
    """质量报告"""
    symbol: str
    timeframe: str
    overall_score: float
    check_results: Dict[str, CheckResult]
    issues_summary: Dict[str, int]
    timestamp: datetime = field(default_factory=datetime.now)
    data_range: Optional[Tuple[datetime, datetime]] = None
    data_points: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'overall_score': self.overall_score,
            'timestamp': self.timestamp.isoformat(),
            'check_results': {k: v.to_dict() for k, v in self.check_results.items()},
            'issues_summary': self.issues_summary,
            'data_range': [d.isoformat() for d in self.data_range] if self.data_range else None,
            'data_points': self.data_points
        }
    
    def print_summary(self):
        """打印摘要"""
        print("=" * 70)
        print(f"📊 数据质量报告: {self.symbol} ({self.timeframe})")
        print("=" * 70)
        
        # 总体评分
        score_emoji = "✅" if self.overall_score >= 0.9 else "⚠️" if self.overall_score >= 0.7 else "❌"
        print(f"{score_emoji} 总体评分: {self.overall_score:.1%}")
        
        # 数据信息
        if self.data_range:
            start, end = self.data_range
            print(f"📅 数据范围: {start.date()} 到 {end.date()}")
        
        if self.data_points:
            print(f"📈 数据点数: {self.data_points}")
        
        print("-" * 70)
        
        # 检查结果
        print("🔍 检查结果:")
        for check_name, result in self.check_results.items():
            result.print_result()
        
        print("-" * 70)
        
        # 问题摘要
        if self.issues_summary:
            total_issues = sum(self.issues_summary.values())
            if total_issues > 0:
                print(f"🚨 发现问题: {total_issues} 个")
                for issue_type, count in self.issues_summary.items():
                    print(f"  {issue_type}: {count} 个")
            else:
                print("✅ 未发现问题")
        
        print("=" * 70)
    
    def save_report(self, filepath: str):
        """保存报告到文件"""
        report_data = self.to_dict()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"报告已保存到: {filepath}")

class DataQualityChecker:
    """数据质量检查器"""
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        data_source: Optional[Any] = None
    ):
        """
        初始化数据质量检查器
        
        参数:
            config_path: 配置文件路径
            data_source: 数据源（数据库连接等）
        """
        self.config_path = config_path or "config/default.yaml"
        self.data_source = data_source
        self.config = self.load_config()
        
        # 检查配置
        self.checks_enabled = {
            'completeness': self.config.get('quality_checks', {}).get('enable_completeness', True),
            'consistency': self.config.get('quality_checks', {}).get('enable_consistency', True),
            'accuracy': self.config.get('quality_checks', {}).get('enable_accuracy', True),
            'timeliness': self.config.get('quality_checks', {}).get('enable_timeliness', True)
        }
        
        logger.info("数据质量检查器初始化完成")
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置"""
        config_file = Path(self.config_path)
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.error(f"加载配置失败: {e}")
                return {}
        
        # 默认配置
        return {
            'quality_checks': {
                'enable_completeness': True,
                'enable_consistency': True,
                'enable_accuracy': True,
                'enable_timeliness': True
            },
            'thresholds': {
                'completeness': 0.95,
                'consistency': 0.98,
                'accuracy': 0.95,
                'timeliness': 0.90
            }
        }
    
    def check_comprehensive(
        self,
        symbol: str,
        timeframe: str = "1d",
        days: int = 365,
        data: Optional[pd.DataFrame] = None
    ) -> QualityReport:
        """
        执行全面数据质量检查
        
        参数:
            symbol: 交易对符号
            timeframe: 时间框架
            days: 天数
            data: 数据DataFrame（可选）
        
        返回:
            QualityReport: 质量报告
        """
        logger.info(f"开始全面数据质量检查: {symbol} ({timeframe})")
        
        # 获取数据
        if data is None:
            data = self._load_data(symbol, timeframe, days)
        
        if data is None or data.empty:
            logger.error(f"无法加载数据: {symbol}")
            return self._create_error_report(symbol, timeframe, "数据加载失败")
        
        # 记录数据信息
        data_range = (data.index.min(), data.index.max()) if hasattr(data, 'index') else (None, None)
        data_points = len(data)
        
        # 执行各项检查
        check_results = {}
        
        # 完整性检查
        if self.checks_enabled['completeness']:
            completeness_result = self.check_completeness(data)
            check_results['completeness'] = completeness_result
        
        # 一致性检查
        if self.checks_enabled['consistency']:
            consistency_result = self.check_consistency(data)
            check_results['consistency'] = consistency_result
        
        # 准确性检查
        if self.checks_enabled['accuracy']:
            accuracy_result = self.check_accuracy(data)
            check_results['accuracy'] = accuracy_result
        
        # 及时性检查
        if self.checks_enabled['timeliness']:
            timeliness_result = self.check_timeliness(data, timeframe)
            check_results['timeliness'] = timeliness_result
        
        # 计算总体评分
        overall_score = self._calculate_overall_score(check_results)
        
        # 汇总问题
        issues_summary = self._summarize_issues(check_results)
        
        # 创建报告
        report = QualityReport(
            symbol=symbol,
            timeframe=timeframe,
            overall_score=overall_score,
            check_results=check_results,
            issues_summary=issues_summary,
            data_range=data_range,
            data_points=data_points
        )
        
        logger.info(f"数据质量检查完成: {symbol} - 评分: {overall_score:.1%}")
        return report
    
    def check_completeness(self, data: pd.DataFrame) -> CheckResult:
        """检查数据完整性"""
        start_time = datetime.now()
        issues = []
        metrics = {}
        
        try:
            # 1. 检查缺失值
            missing_counts = data.isnull().sum()
            total_cells = data.size
            missing_cells = missing_counts.sum()
            
            completeness_score = 1 - (missing_cells / total_cells)
            
            metrics['total_cells'] = total_cells
            metrics['missing_cells'] = int(missing_cells)
            metrics['completeness_percent'] = completeness_score
            
            # 识别具体缺失的列
            for column, count in missing_counts.items():
                if count > 0:
                    issue = QualityIssue(
                        id=f"missing_{column}",
                        type="missing_data",
                        severity=CheckSeverity.HIGH if count > len(data) * 0.1 else CheckSeverity.MEDIUM,
                        description=f"列 '{column}' 有 {count} 个缺失值",
                        location=column,
                        value=count,
                        expected=0,
                        suggestions=["使用插值填充缺失值", "检查数据源"]
                    )
                    issues.append(issue)
            
            # 2. 检查时间连续性
            if hasattr(data, 'index') and isinstance(data.index, pd.DatetimeIndex):
                time_diff = data.index.to_series().diff()
                expected_interval = self._get_expected_interval(data)
                
                if expected_interval:
                    gaps = time_diff[time_diff > expected_interval * 1.5]
                    gap_count = len(gaps)
                    
                    if gap_count > 0:
                        issue = QualityIssue(
                            id="time_gaps",
                            type="time_gap",
                            severity=CheckSeverity.MEDIUM,
                            description=f"发现 {gap_count} 个时间间隔异常",
                            location="index",
                            value=gap_count,
                            expected=0,
                            suggestions=["检查数据采集过程", "补充缺失时间段数据"]
                        )
                        issues.append(issue)
                    
                    metrics['time_gaps'] = gap_count
            
            # 3. 确定状态
            threshold = self.config.get('thresholds', {}).get('completeness', 0.95)
            if completeness_score >= threshold:
                status = CheckStatus.PASS
            elif completeness_score >= threshold * 0.8:
                status = CheckStatus.WARNING
            else:
                status = CheckStatus.FAIL
            
            result = CheckResult(
                check_name="完整性检查",
                status=status,
                score=completeness_score,
                issues=issues,
                metrics=metrics,
                start_time=start_time,
                end_time=datetime.now()
            )
            
            return result
            
        except Exception as e:
            logger.error(f"完整性检查失败: {e}")
            return self._create_error_result("完整性检查", str(e))
    
    def check_consistency(self, data: pd.DataFrame) -> CheckResult:
        """检查数据一致性"""
        start_time = datetime.now()
        issues = []
        metrics = {}
        
        try:
            # 1. 检查价格逻辑
            price_logic_errors = 0
            price_columns = ['open', 'high', 'low', 'close']
            
            for col in price_columns:
                if col in data.columns:
                    # 检查价格为正数
                    negative_prices = data[data[col] <= 0]
                    if len(negative_prices) > 0:
                        issue = QualityIssue(
                            id=f"negative_{col}",
                            type="negative_price",
                            severity=CheckSeverity.CRITICAL,
                            description=f"列 '{col}' 有 {len(negative_prices)} 个非正价格",
                            location=col,
                            value=len(negative_prices),
                            expected=0,
                            suggestions=["检查数据源", "修正异常价格"]
                        )
                        issues.append(issue)
                        price_logic_errors += len(negative_prices)
            
            # 2. 检查 high >= low, high >= close >= low
            if all(col in data.columns for col in ['high', 'low', 'close']):
                logic_violations = data[
                    (data['high'] < data['low']) |
                    (data['close'] < data['low']) |
                    (data['close'] > data['high'])
                ]
                
                if len(logic_violations) > 0:
                    issue = QualityIssue(
                        id="price_logic",
                        type="price_logic_violation",
                        severity=CheckSeverity.HIGH,
                        description=f"发现 {len(logic_violations)} 个价格逻辑错误",
                        location="price_columns",
                        value=len(logic_violations),
                        expected=0,
                        suggestions=["检查数据源", "修正价格数据"]
                    )
                    issues.append(issue)
                    price_logic_errors += len(logic_violations)
            
            # 3. 检查成交量
            if 'volume' in data.columns:
                negative_volume = data[data['volume'] < 0]
                if len(negative_volume) > 0:
                    issue = QualityIssue(
                        id="negative_volume",
                        type="negative_volume",
                        severity=CheckSeverity.HIGH,
                        description=f"成交量有 {len(negative_volume)} 个负值",
                        location="volume",
                        value=len(negative_volume),
                        expected=0,
                        suggestions=["检查数据源", "修正成交量数据"]
                    )
                    issues.append(issue)
            
            # 4. 计算一致性评分
            total_rows = len(data)
            consistency_score = 1 - (price_logic_errors / total_rows) if total_rows > 0 else 0
            
            metrics['total_rows'] = total_rows
            metrics['logic_errors'] = price_logic_errors
            metrics['consistency_percent'] = consistency_score
            
            # 5. 确定状态
            threshold = self.config.get('thresholds', {}).get('consistency', 0.98)
            if consistency_score >= threshold:
                status = CheckStatus.PASS
            elif consistency