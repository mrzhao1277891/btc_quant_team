#!/usr/bin/env python3
"""
数据验证工具

职责: 验证数据是否符合预期规则和约束

主要功能:
- 模式验证: 验证数据结构和类型
- 业务规则验证: 验证业务逻辑约束
- 范围验证: 验证数值范围
- 关系验证: 验证数据间关系
- 自定义规则验证: 支持用户自定义规则

验证类型:
1. 必需性验证 (Required)
2. 类型验证 (Type)
3. 范围验证 (Range)
4. 模式验证 (Pattern)
5. 唯一性验证 (Unique)
6. 关系验证 (Relationship)
7. 自定义验证 (Custom)

版本: 1.0.0
作者: 量化团队
更新日期: 2026-04-19
"""

import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import numpy as np

class ValidationType(Enum):
    """验证类型"""
    REQUIRED = "required"      # 必需性
    TYPE = "type"             # 类型
    RANGE = "range"           # 范围
    PATTERN = "pattern"       # 模式
    UNIQUE = "unique"         # 唯一性
    RELATIONSHIP = "relationship"  # 关系
    CUSTOM = "custom"         # 自定义

class ValidationSeverity(Enum):
    """验证严重性"""
    CRITICAL = "critical"     # 严重: 必须修复
    ERROR = "error"           # 错误: 应该修复
    WARNING = "warning"       # 警告: 建议修复
    INFO = "info"             # 信息: 仅供参考

@dataclass
class ValidationRule:
    """验证规则"""
    name: str
    validation_type: ValidationType
    field: str
    severity: ValidationSeverity = ValidationSeverity.ERROR
    description: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    custom_validator: Optional[Callable] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "validation_type": self.validation_type.value,
            "field": self.field,
            "severity": self.severity.value,
            "description": self.description,
            "parameters": self.parameters
        }

@dataclass
class ValidationResult:
    """验证结果"""
    rule: ValidationRule
    passed: bool
    message: str
    invalid_values: List[Any] = field(default_factory=list)
    invalid_indices: List[int] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "rule": self.rule.to_dict(),
            "passed": self.passed,
            "message": self.message,
            "invalid_values": self.invalid_values,
            "invalid_indices": self.invalid_indices,
            "timestamp": self.timestamp
        }

@dataclass
class ValidationReport:
    """验证报告"""
    dataset_name: str
    timestamp: str
    total_rules: int
    passed_rules: int
    failed_rules: int
    results: List[ValidationResult]
    summary: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "dataset_name": self.dataset_name,
            "timestamp": self.timestamp,
            "total_rules": self.total_rules,
            "passed_rules": self.passed_rules,
            "failed_rules": self.failed_rules,
            "results": [result.to_dict() for result in self.results],
            "summary": self.summary
        }
    
    def to_json(self, indent: int = 2) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    def print_summary(self):
        """打印摘要"""
        print("=" * 60)
        print(f"🔍 数据验证报告: {self.dataset_name}")
        print("=" * 60)
        print(f"📅 验证时间: {self.timestamp}")
        print(f"📋 验证规则: {self.total_rules} 条")
        print(f"✅ 通过规则: {self.passed_rules} 条")
        print(f"❌ 失败规则: {self.failed_rules} 条")
        print(f"🏆 通过率: {(self.passed_rules/self.total_rules*100):.1f}%")
        print()
        
        # 按严重性统计
        severity_stats = self.summary.get("severity_stats", {})
        if severity_stats:
            print("📊 严重性统计:")
            for severity, count in severity_stats.items():
                print(f"  {severity}: {count} 条")
            print()
        
        # 显示失败的验证
        failed_results = [r for r in self.results if not r.passed]
        if failed_results:
            print("⚠️  失败的验证:")
            for result in failed_results:
                print(f"  ❌ {result.rule.name} ({result.rule.severity.value}):")
                print(f"     字段: {result.rule.field}")
                print(f"     消息: {result.message}")
                if result.invalid_values:
                    print(f"     无效值示例: {result.invalid_values[:3]}")
                print()
        
        print("=" * 60)

class DataValidator:
    """数据验证器"""
    
    def __init__(self, rules: Optional[List[ValidationRule]] = None):
        """
        初始化验证器
        
        参数:
            rules: 验证规则列表
        """
        self.rules = rules or []
        self._builtin_rules = self._create_builtin_rules()
    
    def _create_builtin_rules(self) -> Dict[str, ValidationRule]:
        """创建内置验证规则"""
        return {
            # K线数据验证规则
            "kline_required_fields": ValidationRule(
                name="K线必需字段",
                validation_type=ValidationType.REQUIRED,
                field="all",
                severity=ValidationSeverity.CRITICAL,
                description="验证K线数据必需字段是否存在",
                parameters={
                    "required_fields": ["timestamp", "open", "high", "low", "close", "volume"]
                }
            ),
            
            "kline_price_positive": ValidationRule(
                name="价格正数验证",
                validation_type=ValidationType.RANGE,
                field="close",
                severity=ValidationSeverity.ERROR,
                description="验证价格为正数",
                parameters={"min": 0, "exclusive_min": True}
            ),
            
            "kline_high_low_relation": ValidationRule(
                name="高低价关系验证",
                validation_type=ValidationType.RELATIONSHIP,
                field="all",
                severity=ValidationSeverity.ERROR,
                description="验证最高价 >= 最低价",
                parameters={
                    "condition": "high >= low",
                    "fields": ["high", "low"]
                }
            ),
            
            "kline_open_close_range": ValidationRule(
                name="开盘收盘价范围验证",
                validation_type=ValidationType.RELATIONSHIP,
                field="all",
                severity=ValidationSeverity.WARNING,
                description="验证开盘收盘价在最高最低价范围内",
                parameters={
                    "condition": "(open >= low) and (open <= high) and (close >= low) and (close <= high)",
                    "fields": ["open", "high", "low", "close"]
                }
            ),
            
            "kline_volume_positive": ValidationRule(
                name="成交量正数验证",
                validation_type=ValidationType.RANGE,
                field="volume",
                severity=ValidationSeverity.ERROR,
                description="验证成交量为非负数",
                parameters={"min": 0}
            ),
            
            "kline_timestamp_unique": ValidationRule(
                name="时间戳唯一性验证",
                validation_type=ValidationType.UNIQUE,
                field="timestamp",
                severity=ValidationSeverity.WARNING,
                description="验证时间戳唯一性"
            ),
            
            "kline_price_change_sanity": ValidationRule(
                name="价格变化合理性验证",
                validation_type=ValidationType.CUSTOM,
                field="close",
                severity=ValidationSeverity.WARNING,
                description="验证价格变化在合理范围内",
                parameters={"max_change_percent": 50}  # 单根K线最大变化50%
            ),
            
            # 技术指标验证规则
            "indicator_range_sanity": ValidationRule(
                name="指标范围合理性验证",
                validation_type=ValidationType.RANGE,
                field="all_indicators",
                severity=ValidationSeverity.WARNING,
                description="验证技术指标在合理范围内",
                parameters={
                    "rsi_range": (0, 100),
                    "macd_range": (-1000, 1000),
                    "atr_range": (0, 10000)
                }
            ),
            
            "ema_consistency": ValidationRule(
                name="EMA一致性验证",
                validation_type=ValidationType.RELATIONSHIP,
                field="all",
                severity=ValidationSeverity.INFO,
                description="验证EMA值在价格范围内",
                parameters={
                    "condition": "ema_value between low*0.9 and high*1.1",
                    "fields": ["ema_value", "low", "high"]
                }
            )
        }
    
    def add_rule(self, rule: ValidationRule):
        """添加验证规则"""
        self.rules.append(rule)
    
    def add_rules(self, rules: List[ValidationRule]):
        """批量添加验证规则"""
        self.rules.extend(rules)
    
    def add_builtin_rule(self, rule_name: str):
        """添加内置验证规则"""
        if rule_name in self._builtin_rules:
            self.rules.append(self._builtin_rules[rule_name])
        else:
            raise ValueError(f"未知的内置规则: {rule_name}")
    
    def validate_dataframe(
        self,
        df: pd.DataFrame,
        dataset_name: str,
        rule_names: Optional[List[str]] = None
    ) -> ValidationReport:
        """
        验证DataFrame数据
        
        参数:
            df: 要验证的DataFrame
            dataset_name: 数据集名称
            rule_names: 要使用的规则名称列表 (None表示使用所有规则)
        
        返回:
            ValidationReport: 验证报告
        """
        if df.empty:
            return self._create_empty_report(dataset_name)
        
        # 选择要使用的规则
        rules_to_use = self._select_rules(rule_names)
        
        # 执行验证
        results = []
        for rule in rules_to_use:
            result = self._validate_rule(df, rule)
            results.append(result)
        
        # 生成报告
        return self._create_report(dataset_name, results)
    
    def validate_database(
        self,
        db_path: str,
        table_name: str,
        dataset_name: Optional[str] = None,
        rule_names: Optional[List[str]] = None
    ) -> ValidationReport:
        """
        验证数据库表数据
        
        参数:
            db_path: 数据库路径
            table_name: 表名
            dataset_name: 数据集名称
            rule_names: 规则名称列表
        
        返回:
            ValidationReport: 验证报告
        """
        try:
            import sqlite3
            
            # 连接到数据库
            conn = sqlite3.connect(db_path)
            
            # 读取数据
            query = f"SELECT * FROM {table_name}"
            df = pd.read_sql_query(query, conn)
            
            conn.close()
            
            # 验证数据
            return self.validate_dataframe(
                df=df,
                dataset_name=dataset_name or table_name,
                rule_names=rule_names
            )
            
        except Exception as e:
            return self._create_error_report(
                dataset_name or table_name,
                f"数据库验证失败: {str(e)}"
            )
    
    def _select_rules(self, rule_names: Optional[List[str]] = None) -> List[ValidationRule]:
        """选择要使用的规则"""
        if rule_names is None:
            return self.rules
        
        selected_rules = []
        for rule_name in rule_names:
            # 首先在自定义规则中查找
            for rule in self.rules:
                if rule.name == rule_name:
                    selected_rules.append(rule)
                    break
            else:
                # 在内置规则中查找
                if rule_name in self._builtin_rules:
                    selected_rules.append(self._builtin_rules[rule_name])
        
        return selected_rules
    
    def _validate_rule(self, df: pd.DataFrame, rule: ValidationRule) -> ValidationResult:
        """执行单个规则验证"""
        try:
            if rule.validation_type == ValidationType.REQUIRED:
                return self._validate_required(df, rule)
            elif rule.validation_type == ValidationType.TYPE:
                return self._validate_type(df, rule)
            elif rule.validation_type == ValidationType.RANGE:
                return self._validate_range(df, rule)
            elif rule.validation_type == ValidationType.PATTERN:
                return self._validate_pattern(df, rule)
            elif rule.validation_type == ValidationType.UNIQUE:
                return self._validate_unique(df, rule)
            elif rule.validation_type == ValidationType.RELATIONSHIP:
                return self._validate_relationship(df, rule)
            elif rule.validation_type == ValidationType.CUSTOM:
                return self._validate_custom(df, rule)
            else:
                return ValidationResult(
                    rule=rule,
                    passed=False,
                    message=f"未知的验证类型: {rule.validation_type}"
                )
        except Exception as e:
            return ValidationResult(
                rule=rule,
                passed=False,
                message=f"验证执行失败: {str(e)}"
            )
    
    def _validate_required(self, df: pd.DataFrame, rule: ValidationRule) -> ValidationResult:
        """验证必需字段"""
        if rule.field == "all":
            # 验证所有必需字段
            required_fields = rule.parameters.get("required_fields", [])
            missing_fields = [field for field in required_fields if field not in df.columns]
            
            if missing_fields:
                return ValidationResult(
                    rule=rule,
                    passed=False,
                    message=f"缺少必需字段: {missing_fields}",
                    invalid_values=missing_fields
                )
            else:
                return ValidationResult(
                    rule=rule,
                    passed=True,
                    message="所有必需字段都存在"
                )
        else:
            # 验证单个字段
            if rule.field not in df.columns:
                return ValidationResult(
                    rule=rule,
                    passed=False,
                    message=f"字段 '{rule.field}' 不存在"
                )
            else:
                # 检查字段是否有空值
                null_count = df[rule.field].isnull().sum()
                if null_count > 0:
                    invalid_indices = df[df[rule.field].isnull()].index.tolist()
                    return ValidationResult(
                        rule=rule,
                        passed=False,
                        message=f"字段 '{rule.field}' 包含 {null_count} 个空值",
                        invalid_indices=invalid_indices[:10]  # 只显示前10个
                    )
                else:
                    return ValidationResult(
                        rule=rule,
                        passed=True,
                        message=f"字段 '{rule.field}' 完整无空值"
                    )
    
    def _validate_type(self, df: pd.DataFrame, rule: ValidationRule) -> ValidationResult:
        """验证数据类型"""
        if rule.field not in df.columns:
            return ValidationResult(
                rule=rule,
                passed=False,
                message=f"字段 '{rule.field}' 不存在"
            )
        
        expected_type = rule.parameters.get("type", "any")
        
        # 简化类型检查
        actual_dtype = str(df[rule.field].dtype)
        
        # 类型映射
        type_mapping = {
            "int": ["int64", "int32", "int16", "int8"],
            "float": ["float64", "float32", "float16"],
            "str": ["object", "string"],
            "datetime": ["datetime64[ns]", "datetime64[us]", "datetime64[ms]"],
            "bool": ["bool"]
        }
        
        if expected_type == "any":
            passed = True
            message = f"字段 '{rule.field}' 类型为 {actual_dtype}"
        elif expected_type in type_mapping:
            passed = any(t in actual_dtype for t in type_mapping[expected_type])
            message = f"字段 '{rule.field}' 类型为 {actual_dtype}，预期 {expected_type}"
        else:
            # 直接比较
            passed = actual_dtype == expected_type
            message = f"字段 '{rule.field}' 类型为 {actual_dtype}，预期 {expected_type}"
        
        if not passed:
            # 找出类型不匹配的行
            invalid_indices = []
            invalid_values = []
            
            # 这里简化处理，实际可能需要更复杂的类型检查
            for idx, value in df[rule.field].items():
                if pd.isna(value):
                    continue
                
                # 简单的类型检查
                type_ok = False
                if expected_type == "int":
                    type_ok = isinstance(value, (int, np.integer)) and not isinstance(value, bool)
                elif expected_type == "float":
                    type_ok = isinstance(value, (float, np.floating))
                elif expected_type == "str":
                    type_ok = isinstance(value, str)
                elif expected_type == "datetime":
                    type_ok = isinstance(value, (datetime, pd.Timestamp))
                elif expected_type == "bool":
                    type_ok = isinstance(value, (bool, np.bool_))
                
                if not type_ok:
                    invalid_indices.append(idx)
                    invalid_values.append(value)
            
            return ValidationResult(
                rule=rule,
                passed=False,
                message=message,
                invalid_values=invalid_values[:5],
                invalid_indices=invalid_indices[:10]
            )
        else:
            return ValidationResult(
                rule=rule,
                passed=True,
                message=message
