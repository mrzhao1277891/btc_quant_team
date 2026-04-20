#!/usr/bin/env python3
"""
数据清洗工具

职责: 清洗和预处理数据，修复质量问题

主要功能:
- 缺失值处理: 填充、插值、删除
- 异常值处理: 检测、修正、删除
- 重复值处理: 检测、删除
- 格式标准化: 数据类型转换、格式统一
- 数据转换: 规范化、标准化、编码
- 特征工程: 创建衍生特征

清洗策略:
1. 删除法: 直接删除问题数据
2. 填充法: 使用统计值填充
3. 插值法: 使用前后值插值
4. 修正法: 基于规则修正
5. 标记法: 标记问题但不修改

版本: 1.0.0
作者: 量化团队
更新日期: 2026-04-19
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import warnings

class CleaningMethod(Enum):
    """清洗方法"""
    DELETE = "delete"          # 删除
    FILL = "fill"             # 填充
    INTERPOLATE = "interpolate"  # 插值
    CORRECT = "correct"       # 修正
    FLAG = "flag"             # 标记
    TRANSFORM = "transform"   # 转换

class CleaningStrategy(Enum):
    """清洗策略"""
    AGGRESSIVE = "aggressive"  # 激进: 尽可能修复
    MODERATE = "moderate"     # 适中: 平衡修复和保留
    CONSERVATIVE = "conservative"  # 保守: 尽可能保留原始数据

@dataclass
class CleaningRule:
    """清洗规则"""
    name: str
    method: CleaningMethod
    target_field: str
    condition: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    description: Optional[str] = None
    priority: int = 1  # 优先级，数字越小优先级越高
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "method": self.method.value,
            "target_field": self.target_field,
            "condition": self.condition,
            "parameters": self.parameters,
            "description": self.description,
            "priority": self.priority
        }

@dataclass
class CleaningResult:
    """清洗结果"""
    rule: CleaningRule
    applied: bool
    affected_rows: int
    details: Dict[str, Any]
    message: str
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "rule": self.rule.to_dict(),
            "applied": self.applied,
            "affected_rows": self.affected_rows,
            "details": self.details,
            "message": self.message
        }

@dataclass
class CleaningReport:
    """清洗报告"""
    dataset_name: str
    timestamp: str
    original_shape: Tuple[int, int]
    cleaned_shape: Tuple[int, int]
    removed_rows: int
    modified_cells: int
    results: List[CleaningResult]
    summary: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "dataset_name": self.dataset_name,
            "timestamp": self.timestamp,
            "original_shape": self.original_shape,
            "cleaned_shape": self.cleaned_shape,
            "removed_rows": self.removed_rows,
            "modified_cells": self.modified_cells,
            "results": [result.to_dict() for result in self.results],
            "summary": self.summary
        }
    
    def to_json(self, indent: int = 2) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    def print_summary(self):
        """打印摘要"""
        print("=" * 60)
        print(f"🧹 数据清洗报告: {self.dataset_name}")
        print("=" * 60)
        print(f"📅 清洗时间: {self.timestamp}")
        print(f"📊 原始数据: {self.original_shape[0]} 行 × {self.original_shape[1]} 列")
        print(f"📊 清洗后数据: {self.cleaned_shape[0]} 行 × {self.cleaned_shape[1]} 列")
        print(f"🗑️  删除行数: {self.removed_rows}")
        print(f"✏️  修改单元格: {self.modified_cells}")
        print()
        
        # 显示清洗规则应用情况
        applied_rules = [r for r in self.results if r.applied]
        if applied_rules:
            print("🔧 应用的清洗规则:")
            for result in applied_rules:
                print(f"  ✅ {result.rule.name}: {result.message}")
                if result.affected_rows > 0:
                    print(f"     影响行数: {result.affected_rows}")
            print()
        
        # 显示未应用的规则
        skipped_rules = [r for r in self.results if not r.applied]
        if skipped_rules:
            print("⏭️  跳过的清洗规则:")
            for result in skipped_rules:
                print(f"  ⏭️  {result.rule.name}: {result.message}")
            print()
        
        # 显示清洗效果
        if self.original_shape[0] > 0:
            retention_rate = self.cleaned_shape[0] / self.original_shape[0] * 100
            print(f"📈 数据保留率: {retention_rate:.1f}%")
        
        print("=" * 60)

class DataCleaner:
    """数据清洗器"""
    
    def __init__(
        self,
        strategy: CleaningStrategy = CleaningStrategy.MODERATE,
        rules: Optional[List[CleaningRule]] = None
    ):
        """
        初始化清洗器
        
        参数:
            strategy: 清洗策略
            rules: 清洗规则列表
        """
        self.strategy = strategy
        self.rules = rules or []
        self._builtin_rules = self._create_builtin_rules()
        self._cleaning_log = []
    
    def _create_builtin_rules(self) -> Dict[str, CleaningRule]:
        """创建内置清洗规则"""
        return {
            # 缺失值处理规则
            "fill_missing_prices_with_interpolation": CleaningRule(
                name="价格缺失值插值填充",
                method=CleaningMethod.INTERPOLATE,
                target_field="price_columns",
                condition="isnull()",
                parameters={
                    "method": "linear",
                    "limit_direction": "both"
                },
                description="使用线性插值填充价格缺失值",
                priority=1
            ),
            
            "fill_missing_volume_with_mean": CleaningRule(
                name="成交量缺失值均值填充",
                method=CleaningMethod.FILL,
                target_field="volume",
                condition="isnull()",
                parameters={
                    "value": "mean",
                    "inplace": True
                },
                description="使用均值填充成交量缺失值",
                priority=2
            ),
            
            "remove_rows_with_many_missing": CleaningRule(
                name="删除多列缺失的行",
                method=CleaningMethod.DELETE,
                target_field="all",
                condition="missing_ratio > 0.5",
                parameters={
                    "threshold": 0.5,
                    "subset": None
                },
                description="删除缺失值超过50%的行",
                priority=3
            ),
            
            # 异常值处理规则
            "correct_price_outliers_with_iqr": CleaningRule(
                name="价格异常值IQR修正",
                method=CleaningMethod.CORRECT,
                target_field="price_columns",
                condition="is_outlier_iqr",
                parameters={
                    "method": "clip",
                    "multiplier": 1.5
                },
                description="使用IQR方法修正价格异常值",
                priority=2
            ),
            
            "flag_extreme_price_changes": CleaningRule(
                name="标记极端价格变化",
                method=CleaningMethod.FLAG,
                target_field="close",
                condition="price_change > 0.5",
                parameters={
                    "threshold": 0.5,  # 50%变化
                    "flag_column": "extreme_change"
                },
                description="标记价格变化超过50%的K线",
                priority=3
            ),
            
            # 重复值处理规则
            "remove_duplicate_timestamps": CleaningRule(
                name="删除重复时间戳",
                method=CleaningMethod.DELETE,
                target_field="timestamp",
                condition="duplicated()",
                parameters={
                    "keep": "first",
                    "subset": ["timestamp"]
                },
                description="删除重复的时间戳记录",
                priority=1
            ),
            
            # 格式标准化规则
            "convert_timestamp_to_datetime": CleaningRule(
                name="时间戳转换为日期时间",
                method=CleaningMethod.TRANSFORM,
                target_field="timestamp",
                condition=None,
                parameters={
                    "unit": "ms",
                    "format": None
                },
                description="将毫秒时间戳转换为datetime格式",
                priority=1
            ),
            
            "ensure_price_positive": CleaningRule(
                name="确保价格为正数",
                method=CleaningMethod.CORRECT,
                target_field="price_columns",
                condition="price <= 0",
                parameters={
                    "correction": "abs",
                    "minimum": 0.01
                },
                description="修正非正价格",
                priority=1
            ),
            
            "fix_high_low_relationship": CleaningRule(
                name="修正高低价关系",
                method=CleaningMethod.CORRECT,
                target_field="all",
                condition="high < low",
                parameters={
                    "swap_fields": ["high", "low"]
                },
                description="修正最高价低于最低价的情况",
                priority=1
            ),
            
            "normalize_column_names": CleaningRule(
                name="标准化列名",
                method=CleaningMethod.TRANSFORM,
                target_field="columns",
                condition=None,
                parameters={
                    "lowercase": True,
                    "replace_spaces": "_",
                    "remove_special": True
                },
                description="标准化列名格式",
                priority=4
            )
        }
    
    def add_rule(self, rule: CleaningRule):
        """添加清洗规则"""
        self.rules.append(rule)
    
    def add_rules(self, rules: List[CleaningRule]):
        """批量添加清洗规则"""
        self.rules.extend(rules)
    
    def add_builtin_rule(self, rule_name: str):
        """添加内置清洗规则"""
        if rule_name in self._builtin_rules:
            self.rules.append(self._builtin_rules[rule_name])
        else:
            raise ValueError(f"未知的内置规则: {rule_name}")
    
    def clean_dataframe(
        self,
        df: pd.DataFrame,
        dataset_name: str,
        rule_names: Optional[List[str]] = None,
        inplace: bool = False
    ) -> Tuple[pd.DataFrame, CleaningReport]:
        """
        清洗DataFrame数据
        
        参数:
            df: 要清洗的DataFrame
            dataset_name: 数据集名称
            rule_names: 要使用的规则名称列表
            inplace: 是否原地修改
        
        返回:
            Tuple[清洗后的DataFrame, 清洗报告]
        """
        if not inplace:
            df = df.copy()
        
        original_shape = df.shape
        original_df = df.copy()
        
        # 选择要使用的规则
        rules_to_use = self._select_rules(rule_names)
        
        # 按优先级排序
        rules_to_use.sort(key=lambda x: x.priority)
        
        # 执行清洗
        results = []
        total_modified_cells = 0
        
        for rule in rules_to_use:
            result = self._apply_cleaning_rule(df, rule)
            results.append(result)
            
            if result.applied:
                total_modified_cells += result.affected_rows
        
        # 计算清洗效果
        cleaned_shape = df.shape
        removed_rows = original_shape[0] - cleaned_shape[0]
        
        # 生成报告
        report = self._create_report(
            dataset_name=dataset_name,
            original_shape=original_shape,
            cleaned_shape=cleaned_shape,
            removed_rows=removed_rows,
            modified_cells=total_modified_cells,
            results=results
        )
        
        return df, report
    
    def clean_database(
        self,
        db_path: str,
        table_name: str,
        dataset_name: Optional[str] = None,
        rule_names: Optional[List[str]] = None,
        create_backup: bool = True
    ) -> Tuple[pd.DataFrame, CleaningReport]:
        """
        清洗数据库表数据
        
        参数:
            db_path: 数据库路径
            table_name: 表名
            dataset_name: 数据集名称
            rule_names: 规则名称列表
            create_backup: 是否创建备份
        
        返回:
            Tuple[清洗后的DataFrame, 清洗报告]
        """
        try:
            import sqlite3
            
            # 连接到数据库
            conn = sqlite3.connect(db_path)
            
            # 创建备份
            if create_backup:
                backup_table = f"{table_name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                conn.execute(f"CREATE TABLE {backup_table} AS SELECT * FROM {table_name}")
                conn.commit()
            
            # 读取数据
            query = f"SELECT * FROM {table_name}"
            df = pd.read_sql_query(query, conn)
            
            # 清洗数据
            cleaned_df, report = self.clean_dataframe(
                df=df,
                dataset_name=dataset_name or table_name,
                rule_names=rule_names,
                inplace=False
            )
            
            # 写回数据库
            cleaned_df.to_sql(table_name, conn, if_exists='replace', index=False)
            conn.commit()
            conn.close()
            
            return cleaned_df, report
            
        except Exception as e:
            raise RuntimeError(f"数据库清洗失败: {str(e)}")
    
    def _select_rules(self, rule_names: Optional[List[str]] = None) -> List[CleaningRule]:
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
    
    def _apply_cleaning_rule(self, df: pd.DataFrame, rule: CleaningRule) -> CleaningResult:
        """应用单个清洗规则"""
        try:
            if rule.method == CleaningMethod.DELETE:
                return self._apply_delete(df, rule)
            elif rule.method == CleaningMethod.FILL:
                return self._apply_fill(df, rule)
            elif rule.method == CleaningMethod.INTERPOLATE:
                return self._apply_interpolate(df, rule)
            elif rule.method == CleaningMethod.CORRECT:
                return self._apply_correct(df, rule)
            elif rule.method == CleaningMethod.FLAG:
                return self._apply_flag(df, rule)
            elif rule.method == CleaningMethod.TRANSFORM:
                return self._apply_transform(df, rule)
            else:
                return CleaningResult(
                    rule=rule,
                    applied=False,
                    affected_rows=0,
                    details={},
                    message=f"未知的清洗方法: {rule.method}"
                )
        except Exception as e:
            return CleaningResult(
                rule=rule,
                applied=False,
                affected_rows=0,
                details={"error": str(e)},
                message=f"清洗规则执行失败: {str(e)}"
            )
    
    def _apply_delete(self, df: pd.DataFrame, rule: CleaningRule) -> CleaningResult:
        """应用删除规则"""
        original_len = len(df)
        
        if rule.target_field == "all":
            # 删除整行
            if rule.condition == "missing_ratio > 0.5":
                threshold = rule.parameters.get("threshold", 0.5)
                subset = rule.parameters.get("subset")
                
                if subset:
                    missing_ratio = df[subset].isnull().sum(axis=1) / len(subset)
                else:
                    missing_ratio = df.isnull().sum(axis=1) / df.shape[1]
                
                rows_to_delete = missing_ratio > threshold
                df.drop(df[rows_to_delete].index, inplace=True)
                
                affected = rows_to_delete.sum()
                message = f"删除缺失值超过{threshold:.0%}的行: {affected} 行"
                
            elif rule.condition == "duplicated()":
                subset = rule.parameters.get("subset")
                keep = rule.parameters.get("keep", "first")
                
                duplicates = df.duplicated(subset=subset, keep=keep)
                df.drop(df[duplicates].index, inplace=True)
                
                affected = duplicates.sum()
                message = f"删除重复行: {affected} 行"
                
            else:
                # 通用条件删除
                if rule.condition:
                    rows_to_delete = df.eval(rule.condition)
                    df.drop(df[rows_to_delete].index, inplace=True)
                    affected = rows_to_delete.sum()
                    message = f"根据条件删除行: {affected} 行"
                else:
                    affected = 0
                    message = "无删除条件，跳过"
        
        else:
            # 删除特定字段
            if rule.condition:
                mask = df[rule.target_field].apply(
                    lambda x: eval(rule.condition, {"x": x, "isnull": pd