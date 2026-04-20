#!/usr/bin/env python3
"""
数据质量检查工具

职责: 检查数据质量，包括完整性、一致性、准确性、及时性

主要功能:
- 完整性检查: 数据缺失、空值、重复
- 一致性检查: 数据类型、格式、范围
- 准确性检查: 异常值、逻辑错误
- 及时性检查: 数据新鲜度、延迟

质量维度:
1. 完整性 (Completeness): 数据是否完整
2. 一致性 (Consistency): 数据是否一致
3. 准确性 (Accuracy): 数据是否准确
4. 及时性 (Timeliness): 数据是否及时
5. 有效性 (Validity): 数据是否有效

版本: 1.0.0
作者: 量化团队
更新日期: 2026-04-19
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import json
import sqlite3
from pathlib import Path

class QualityDimension(Enum):
    """数据质量维度"""
    COMPLETENESS = "completeness"  # 完整性
    CONSISTENCY = "consistency"    # 一致性
    ACCURACY = "accuracy"          # 准确性
    TIMELINESS = "timeliness"      # 及时性
    VALIDITY = "validity"          # 有效性

class QualityLevel(Enum):
    """质量等级"""
    EXCELLENT = "excellent"  # 优秀: 95-100%
    GOOD = "good"           # 良好: 85-94%
    FAIR = "fair"           # 一般: 70-84%
    POOR = "poor"           # 较差: 50-69%
    CRITICAL = "critical"   # 严重: <50%

@dataclass
class QualityMetric:
    """质量指标"""
    dimension: QualityDimension
    metric_name: str
    value: float
    threshold: float
    passed: bool
    details: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "dimension": self.dimension.value,
            "metric_name": self.metric_name,
            "value": round(self.value, 4),
            "threshold": self.threshold,
            "passed": self.passed,
            "details": self.details
        }

@dataclass
class QualityReport:
    """质量报告"""
    dataset_name: str
    timestamp: str
    overall_score: float
    quality_level: QualityLevel
    metrics: List[QualityMetric]
    issues: List[Dict[str, Any]]
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "dataset_name": self.dataset_name,
            "timestamp": self.timestamp,
            "overall_score": round(self.overall_score, 2),
            "quality_level": self.quality_level.value,
            "metrics": [metric.to_dict() for metric in self.metrics],
            "issues": self.issues,
            "recommendations": self.recommendations
        }
    
    def to_json(self, indent: int = 2) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    def print_summary(self):
        """打印摘要"""
        print("=" * 60)
        print(f"📊 数据质量报告: {self.dataset_name}")
        print("=" * 60)
        print(f"📅 检查时间: {self.timestamp}")
        print(f"🏆 综合评分: {self.overall_score:.1f}/100 ({self.quality_level.value})")
        print()
        
        # 按维度分组显示
        dimensions = {}
        for metric in self.metrics:
            dim = metric.dimension.value
            if dim not in dimensions:
                dimensions[dim] = []
            dimensions[dim].append(metric)
        
        for dim, metrics in dimensions.items():
            print(f"📈 {dim.upper()}:")
            for metric in metrics:
                status = "✅" if metric.passed else "❌"
                print(f"  {status} {metric.metric_name}: {metric.value:.1%} "
                      f"(阈值: {metric.threshold:.1%})")
            print()
        
        # 显示问题
        if self.issues:
            print("⚠️  发现的问题:")
            for i, issue in enumerate(self.issues, 1):
                print(f"  {i}. {issue['description']}")
                if 'suggestion' in issue:
                    print(f"     建议: {issue['suggestion']}")
            print()
        
        # 显示建议
        if self.recommendations:
            print("💡 改进建议:")
            for i, rec in enumerate(self.recommendations, 1):
                print(f"  {i}. {rec}")
        
        print("=" * 60)

class DataQualityChecker:
    """数据质量检查器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化质量检查器
        
        参数:
            config: 配置字典，包含阈值等设置
        """
        self.config = config or self._default_config()
        
    def _default_config(self) -> Dict[str, Any]:
        """默认配置"""
        return {
            # 完整性阈值
            "completeness_threshold": 0.95,  # 95%完整
            "null_threshold": 0.05,          # 最多5%空值
            
            # 一致性阈值
            "type_consistency_threshold": 0.98,  # 98%类型一致
            "format_consistency_threshold": 0.95, # 95%格式一致
            
            # 准确性阈值
            "outlier_threshold": 0.03,       # 最多3%异常值
            "logic_error_threshold": 0.01,   # 最多1%逻辑错误
            
            # 及时性阈值
            "freshness_threshold_hours": {
                "1m": 0.1,    # 6分钟
                "5m": 0.5,    # 30分钟
                "15m": 1,     # 1小时
                "1h": 4,      # 4小时
                "4h": 6,      # 6小时
                "1d": 24,     # 24小时
                "1w": 168,    # 7天
                "1M": 720     # 30天
            },
            
            # 有效性阈值
            "range_violation_threshold": 0.02,  # 最多2%范围违规
            "pattern_violation_threshold": 0.05 # 最多5%模式违规
        }
    
    def check_dataframe(
        self,
        df: pd.DataFrame,
        dataset_name: str,
        expected_schema: Optional[Dict[str, str]] = None,
        timeframe: Optional[str] = None
    ) -> QualityReport:
        """
        检查DataFrame数据质量
        
        参数:
            df: 要检查的DataFrame
            dataset_name: 数据集名称
            expected_schema: 预期模式 {列名: 数据类型}
            timeframe: 时间框架 (用于及时性检查)
        
        返回:
            QualityReport: 质量报告
        """
        if df.empty:
            return self._create_empty_report(dataset_name)
        
        metrics = []
        issues = []
        
        # 1. 完整性检查
        completeness_metrics, completeness_issues = self._check_completeness(df)
        metrics.extend(completeness_metrics)
        issues.extend(completeness_issues)
        
        # 2. 一致性检查
        consistency_metrics, consistency_issues = self._check_consistency(df, expected_schema)
        metrics.extend(consistency_metrics)
        issues.extend(consistency_issues)
        
        # 3. 准确性检查
        accuracy_metrics, accuracy_issues = self._check_accuracy(df)
        metrics.extend(accuracy_metrics)
        issues.extend(accuracy_issues)
        
        # 4. 及时性检查
        if timeframe:
            timeliness_metrics, timeliness_issues = self._check_timeliness(df, timeframe)
            metrics.extend(timeliness_metrics)
            issues.extend(timeliness_issues)
        
        # 5. 有效性检查
        validity_metrics, validity_issues = self._check_validity(df)
        metrics.extend(validity_metrics)
        issues.extend(validity_issues)
        
        # 计算综合评分
        overall_score = self._calculate_overall_score(metrics)
        quality_level = self._determine_quality_level(overall_score)
        
        # 生成建议
        recommendations = self._generate_recommendations(metrics, issues)
        
        return QualityReport(
            dataset_name=dataset_name,
            timestamp=datetime.now().isoformat(),
            overall_score=overall_score,
            quality_level=quality_level,
            metrics=metrics,
            issues=issues,
            recommendations=recommendations
        )
    
    def check_database(
        self,
        db_path: Union[str, Path],
        table_name: str,
        dataset_name: Optional[str] = None,
        timeframe: Optional[str] = None
    ) -> QualityReport:
        """
        检查数据库表数据质量
        
        参数:
            db_path: 数据库路径
            table_name: 表名
            dataset_name: 数据集名称 (默认使用表名)
            timeframe: 时间框架
        
        返回:
            QualityReport: 质量报告
        """
        if not Path(db_path).exists():
            return self._create_error_report(
                dataset_name or table_name,
                f"数据库文件不存在: {db_path}"
            )
        
        try:
            # 连接到数据库
            conn = sqlite3.connect(str(db_path))
            
            # 读取数据
            query = f"SELECT * FROM {table_name}"
            df = pd.read_sql_query(query, conn)
            
            # 获取表结构
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            schema_info = cursor.fetchall()
            
            # 构建预期模式
            expected_schema = {}
            for col in schema_info:
                col_name, col_type = col[1], col[2]
                expected_schema[col_name] = col_type
            
            conn.close()
            
            # 检查数据质量
            return self.check_dataframe(
                df=df,
                dataset_name=dataset_name or table_name,
                expected_schema=expected_schema,
                timeframe=timeframe
            )
            
        except Exception as e:
            return self._create_error_report(
                dataset_name or table_name,
                f"数据库检查失败: {str(e)}"
            )
    
    def _check_completeness(
        self,
        df: pd.DataFrame
    ) -> Tuple[List[QualityMetric], List[Dict[str, Any]]]:
        """检查完整性"""
        metrics = []
        issues = []
        
        # 1. 总体完整性
        total_cells = df.size
        null_cells = df.isnull().sum().sum()
        completeness_ratio = 1 - (null_cells / total_cells) if total_cells > 0 else 0
        
        metrics.append(QualityMetric(
            dimension=QualityDimension.COMPLETENESS,
            metric_name="总体完整性",
            value=completeness_ratio,
            threshold=self.config["completeness_threshold"],
            passed=completeness_ratio >= self.config["completeness_threshold"],
            details={
                "total_cells": total_cells,
                "null_cells": null_cells,
                "completeness_ratio": completeness_ratio
            }
        ))
        
        if completeness_ratio < self.config["completeness_threshold"]:
            issues.append({
                "dimension": "completeness",
                "description": f"数据完整性不足: {completeness_ratio:.1%} (阈值: {self.config['completeness_threshold']:.1%})",
                "severity": "high"
            })
        
        # 2. 列级完整性
        for column in df.columns:
            null_count = df[column].isnull().sum()
            null_ratio = null_count / len(df)
            
            if null_ratio > self.config["null_threshold"]:
                issues.append({
                    "dimension": "completeness",
                    "description": f"列 '{column}' 空值过多: {null_ratio:.1%}",
                    "suggestion": f"检查数据源或进行插值处理",
                    "severity": "medium"
                })
        
        # 3. 时间连续性 (如果有时序列)
        time_columns = [col for col in df.columns if 'time' in col.lower() or 'date' in col.lower()]
        if time_columns:
            time_col = time_columns[0]
            if pd.api.types.is_datetime64_any_dtype(df[time_col]):
                df_sorted = df.sort_values(time_col)
                time_diffs = df_sorted[time_col].diff().dropna()
                
                if len(time_diffs) > 0:
                    # 检查是否有大的时间间隔
                    max_gap = time_diffs.max()
                    if hasattr(max_gap, 'total_seconds'):
                        max_gap_seconds = max_gap.total_seconds()
                        if max_gap_seconds > 3600 * 24:  # 超过1天
                            issues.append({
                                "dimension": "completeness",
                                "description": f"时间序列存在大间隔: {max_gap}",
                                "suggestion": "检查数据采集是否中断",
                                "severity": "medium"
                            })
        
        return metrics, issues
    
    def _check_consistency(
        self,
        df: pd.DataFrame,
        expected_schema: Optional[Dict[str, str]] = None
    ) -> Tuple[List[QualityMetric], List[Dict[str, Any]]]:
        """检查一致性"""
        metrics = []
        issues = []
        
        # 1. 数据类型一致性
        if expected_schema:
            type_mismatches = []
            for column, expected_type in expected_schema.items():
                if column in df.columns:
                    actual_type = str(df[column].dtype)
                    # 简化类型比较
                    if not self._types_compatible(actual_type, expected_type):
                        type_mismatches.append({
                            "column": column,
                            "expected": expected_type,
                            "actual": actual_type
                        })
            
            type_consistency_ratio = 1 - (len(type_mismatches) / len(expected_schema)) if expected_schema else 1
            
            metrics.append(QualityMetric(
                dimension=QualityDimension.CONSISTENCY,
                metric_name="类型一致性",
                value=type_consistency_ratio,
                threshold=self.config["type_consistency_threshold"],
                passed=type_consistency_ratio >= self.config["type_consistency_threshold"],
                details={
                    "total_columns": len(expected_schema) if expected_schema else 0,
                    "type_mismatches": type_mismatches,
                    "consistency_ratio": type_consistency_ratio
                }
            ))
            
            for mismatch in type_mismatches:
                issues.append({
                    "dimension": "consistency",
                    "description": f"列 '{mismatch['column']}' 类型不匹配: 预期 {mismatch['expected']}, 实际 {mismatch['actual']}",
                    "suggestion": "转换数据类型或检查数据源",
                    "severity": "medium"
                })
        
        # 2. 数值范围一致性 (针对价格数据)
        price_columns = [col for col in df.columns if 'price' in col.lower() or 'close' in col.lower()]
        for col in price_columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                # 检查价格是否为正数
                negative_count = (df[col] <= 0).sum()
                if negative_count > 0:
                    issues.append({
                        "dimension": "consistency",
                        "description": f"列 '{col}' 包含 {negative_count} 个非正数值",
                        "suggestion": "检查数据采集或清洗逻辑",
                        "severity": "high"
                    })
        
        return metrics, issues
    
    def _check_accuracy(
        self,
        df: pd.DataFrame
    ) -> Tuple[List[QualityMetric], List[Dict[str, Any]]]:
        """检查准确性"""
        metrics = []
        issues = []
        
        # 1. 异常值检测
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) > 0:
            outlier_counts = {}
            
            for col in numeric_cols:
                # 使用IQR方法检测异常值
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
                outlier_counts[col] = len(outliers)
                
                if len(outliers) > 0:
                    outlier_ratio = len(outliers) / len(df)
                    if outlier_ratio > self.config["outlier_threshold"]:
                        issues.append({
                            "dimension": "accuracy",
                            "description": f"列 '{col}' 异常值过多: {outlier_ratio:.1%} ({len(outliers)} 个)",
                            "suggestion": "检查数据源或进行异常值处理",
                            "severity": "medium"
                        })
            
            # 计算总体异常值比例
            total_outliers = sum(outlier_counts.values())
            total_values = len(df) * len(numeric_cols)
            outlier_ratio = total_outliers / total_values if total_values > 0 else 0
            
            metrics