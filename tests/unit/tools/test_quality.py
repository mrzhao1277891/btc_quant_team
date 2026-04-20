#!/usr/bin/env python3
"""
质量工具测试
"""

import pytest
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from tools.quality.checker import (
    DataQualityChecker, QualityReport, QualityDimension, QualityLevel
)

from tools.quality.validator import (
    DataValidator, ValidationReport, ValidationRule, ValidationType, ValidationSeverity
)

from tools.quality.cleaner import (
    DataCleaner, CleaningReport, CleaningRule, CleaningMethod, CleaningStrategy
)

class TestQualityChecker:
    """质量检查器测试类"""
    
    def test_checker_initialization(self):
        """测试检查器初始化"""
        checker = DataQualityChecker()
        assert checker is not None
        assert "completeness_threshold" in checker.config
    
    def test_check_dataframe_basic(self):
        """测试DataFrame基本检查"""
        # 创建测试数据
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=10, freq='H'),
            'open': [70000 + i*10 for i in range(10)],
            'high': [70100 + i*10 for i in range(10)],
            'low': [69900 + i*10 for i in range(10)],
            'close': [70050 + i*10 for i in range(10)],
            'volume': [1000 + i*100 for i in range(10)]
        })
        
        checker = DataQualityChecker()
        report = checker.check_dataframe(df, "测试数据", timeframe="1h")
        
        assert isinstance(report, QualityReport)
        assert report.dataset_name == "测试数据"
        assert 0 <= report.overall_score <= 100
        assert isinstance(report.quality_level, QualityLevel)
        assert len(report.metrics) > 0
    
    def test_check_dataframe_with_missing(self):
        """测试包含缺失数据的检查"""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=10, freq='H'),
            'open': [70000 + i*10 if i != 5 else np.nan for i in range(10)],  # 第5行缺失
            'high': [70100 + i*10 for i in range(10)],
            'low': [69900 + i*10 for i in range(10)],
            'close': [70050 + i*10 for i in range(10)],
            'volume': [1000 + i*100 for i in range(10)]
        })
        
        checker = DataQualityChecker()
        report = checker.check_dataframe(df, "测试缺失数据", timeframe="1h")
        
        # 应该检测到缺失值
        completeness_metrics = [m for m in report.metrics if m.dimension == QualityDimension.COMPLETENESS]
        assert len(completeness_metrics) > 0
        
        # 应该有相关问题
        assert len(report.issues) > 0
    
    def test_check_dataframe_with_outliers(self):
        """测试包含异常值的检查"""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=10, freq='H'),
            'open': [70000 + i*10 for i in range(10)],
            'high': [70100 + i*10 for i in range(9)] + [100000],  # 异常值
            'low': [69900 + i*10 for i in range(10)],
            'close': [70050 + i*10 for i in range(10)],
            'volume': [1000 + i*100 for i in range(10)]
        })
        
        checker = DataQualityChecker()
        report = checker.check_dataframe(df, "测试异常值数据", timeframe="1h")
        
        # 应该检测到异常值
        accuracy_metrics = [m for m in report.metrics if m.dimension == QualityDimension.ACCURACY]
        assert len(accuracy_metrics) > 0
    
    def test_check_database(self, tmp_path):
        """测试数据库检查"""
        # 创建测试数据库
        db_path = tmp_path / "test.db"
        
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        
        # 创建表
        conn.execute("""
            CREATE TABLE klines (
                timestamp INTEGER PRIMARY KEY,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL
            )
        """)
        
        # 插入测试数据
        for i in range(10):
            conn.execute("""
                INSERT INTO klines VALUES (?, ?, ?, ?, ?, ?)
            """, (
                1704067200000 + i * 3600000,  # 时间戳
                70000 + i*10,
                70100 + i*10,
                69900 + i*10,
                70050 + i*10,
                1000 + i*100
            ))
        
        conn.commit()
        conn.close()
        
        # 检查数据库
        checker = DataQualityChecker()
        report = checker.check_database(str(db_path), "klines", timeframe="1h")
        
        assert isinstance(report, QualityReport)
        assert report.dataset_name == "klines"
    
    def test_report_serialization(self):
        """测试报告序列化"""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=5, freq='H'),
            'value': [100, 200, 300, 400, 500]
        })
        
        checker = DataQualityChecker()
        report = checker.check_dataframe(df, "序列化测试")
        
        # 转换为字典
        report_dict = report.to_dict()
        assert isinstance(report_dict, dict)
        assert "dataset_name" in report_dict
        assert "overall_score" in report_dict
        assert "metrics" in report_dict
        
        # 转换为JSON
        report_json = report.to_json()
        assert isinstance(report_json, str)
        assert "dataset_name" in report_json

class TestDataValidator:
    """数据验证器测试类"""
    
    def test_validator_initialization(self):
        """测试验证器初始化"""
        validator = DataValidator()
        assert validator is not None
        assert len(validator._builtin_rules) > 0
    
    def test_validate_dataframe_basic(self):
        """测试DataFrame基本验证"""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=10, freq='H'),
            'open': [70000 + i*10 for i in range(10)],
            'high': [70100 + i*10 for i in range(10)],
            'low': [69900 + i*10 for i in range(10)],
            'close': [70050 + i*10 for i in range(10)],
            'volume': [1000 + i*100 for i in range(10)]
        })
        
        validator = DataValidator()
        validator.add_builtin_rule("kline_required_fields")
        validator.add_builtin_rule("kline_price_positive")
        
        report = validator.validate_dataframe(df, "测试数据")
        
        assert isinstance(report, ValidationReport)
        assert report.dataset_name == "测试数据"
        assert report.total_rules == 2
        assert report.passed_rules >= 0
        assert report.failed_rules >= 0
    
    def test_validate_dataframe_with_errors(self):
        """测试包含错误的数据验证"""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=10, freq='H'),
            'open': [70000 + i*10 for i in range(10)],
            'high': [69900 + i*10 for i in range(10)],  # 错误: high < low
            'low': [70100 + i*10 for i in range(10)],   # 错误: low > high
            'close': [70050 + i*10 for i in range(10)],
            'volume': [1000 + i*100 for i in range(10)]
        })
        
        validator = DataValidator()
        validator.add_builtin_rule("kline_high_low_relation")
        
        report = validator.validate_dataframe(df, "测试错误数据")
        
        # 应该检测到错误
        assert report.failed_rules > 0
    
    def test_custom_validation_rule(self):
        """测试自定义验证规则"""
        # 创建自定义规则
        custom_rule = ValidationRule(
            name="价格范围验证",
            validation_type=ValidationType.RANGE,
            field="close",
            severity=ValidationSeverity.ERROR,
            description="验证收盘价在合理范围内",
            parameters={"min": 60000, "max": 80000}
        )
        
        # 创建测试数据
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=5, freq='H'),
            'close': [59000, 70000, 75000, 81000, 72000]  # 有超出范围的值
        })
        
        validator = DataValidator()
        validator.add_rule(custom_rule)
        
        report = validator.validate_dataframe(df, "测试自定义规则")
        
        # 应该检测到超出范围的值
        assert report.failed_rules > 0
    
    def test_validation_report_print(self):
        """测试验证报告打印"""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=3, freq='H'),
            'value': [100, 200, 300]
        })
        
        validator = DataValidator()
        report = validator.validate_dataframe(df, "打印测试")
        
        # 测试打印功能
        report.print_summary()  # 应该正常执行，不抛出异常

class TestDataCleaner:
    """数据清洗器测试类"""
    
    def test_cleaner_initialization(self):
        """测试清洗器初始化"""
        cleaner = DataCleaner()
        assert cleaner is not None
        assert isinstance(cleaner.strategy, CleaningStrategy)
    
    def test_clean_dataframe_basic(self):
        """测试DataFrame基本清洗"""
        # 创建包含问题的测试数据
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=10, freq='H').tolist() * 2,  # 重复
            'open': [70000 + i*10 for i in range(10)] + [np.nan] * 10,  # 缺失值
            'high': [70100 + i*10 for i in range(20)],
            'low': [69900 + i*10 for i in range(20)],
            'close': [70050 + i*10 for i in range(20)],
            'volume': [1000 + i*100 for i in range(20)]
        })
        
        original_shape = df.shape
        
        cleaner = DataCleaner(strategy=CleaningStrategy.MODERATE)
        cleaner.add_builtin_rule("remove_duplicate_timestamps")
        cleaner.add_builtin_rule("fill_missing_prices_with_interpolation")
        
        cleaned_df, report = cleaner.clean_dataframe(df, "测试清洗")
        
        assert isinstance(cleaned_df, pd.DataFrame)
        assert isinstance(report, CleaningReport)
        assert cleaned_df.shape[0] <= original_shape[0]  # 可能删除了重复行
        assert cleaned_df['open'].isnull().sum() < df['open'].isnull().sum()  # 缺失值减少
    
    def test_clean_dataframe_outliers(self):
        """测试异常值清洗"""
        # 创建包含异常值的测试数据
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=10, freq='H'),
            'close': [70000, 71000, 72000, 100000, 73000, 74000, 75000, 76000, 77000, 78000]  # 异常值100000
        })
        
        cleaner = DataCleaner()
        cleaner.add_builtin_rule("correct_price_outliers_with_iqr")
        
        cleaned_df, report = cleaner.clean_dataframe(df, "测试异常值清洗")
        
        # 检查异常值是否被修正
        close_values = cleaned_df['close'].values
        assert np.max(close_values) < 90000  # 异常值应该被修正
    
    def test_clean_dataframe_negative_prices(self):
        """测试负价格清洗"""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=5, freq='H'),
            'close': [70000, -500, 72000, 73000, 74000]  # 负价格
        })
        
        cleaner = DataCleaner()
        cleaner.add_builtin_rule("ensure_price_positive")
        
        cleaned_df, report = cleaner.clean_dataframe(df, "测试负价格清洗")
        
        # 检查是否还有负价格
        assert (cleaned_df['close'] > 0).all()
    
    def test_clean_dataframe_high_low_swap(self):
        """测试高低价交换清洗"""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=5, freq='H'),
            'high': [69900, 70100, 70200, 70300, 70400],  # high < low
            'low': [70100, 69900, 70000, 70100, 70200]    # low > high
        })
        
        cleaner = DataCleaner()
        cleaner.add_builtin_rule("fix_high_low_relationship")
        
        cleaned_df, report = cleaner.clean_dataframe(df, "测试高低价交换")
        
        # 检查高低价关系是否正确
        assert (cleaned_df['high'] >= cleaned_df['low']).all()
    
    def test_cleaning_report(self):
        """测试清洗报告"""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=3, freq='H'),
            'value': [100, 200, 300]
        })
        
        cleaner = DataCleaner()
        cleaned_df, report = cleaner.clean_dataframe(df, "测试报告")
        
        assert isinstance(report, CleaningReport)
        assert report.original_shape == df.shape
        assert report.cleaned_shape == cleaned_df.shape
        
        # 测试序列化
        report_dict = report.to_dict()
        assert "dataset_name" in report_dict
        assert "original_shape" in report_dict
        
        # 测试打印
        report.print_summary()  # 应该正常执行

class TestQualityIntegration:
    """质量工具集成测试"""
    
    def test_full_quality_pipeline(self):
        """测试完整质量流水线"""
        # 创建包含多种问题的测试数据
        df = pd.DataFrame({
            'timestamp': (pd.date_range('2024-01-01', periods=10, freq='H').tolist() + 
                         pd.date_range('2024-01-01', periods=5, freq='H').tolist()),  # 重复
            'open': [70000 + i*10 if i % 3 != 0 else np.nan for i in range(15)],  # 缺失值
            'high': [69900 + i*10 for i in range(15)],  # 故意设置 high < low
            'low': [70100 + i*10 for i in range(15)],   # 故意设置 low > high
            'close': [70050 + i*10 for i in range(14)] + [-100],  # 负价格
            'volume': [1000 + i*100 for i in range(15)]
        })
        
        print("=" * 60)
        print("测试完整质量流水线")
        print("=" * 60)
        
        # 1. 质量检查
        print("\n1. 📊 质量检查...")
        checker = DataQualityChecker()
        quality_report = checker.check_dataframe(df, "测试流水线", timeframe="1h")
        quality_report.print_summary()
        
        # 2. 数据验证
        print("\n2. 🔍 数据验证...")
        validator = DataValidator()
        validator.add_builtin_rule("kline_required_fields")
        validator.add_builtin_rule("kline_price_positive")
        validator.add_builtin_rule("kline_high_low_relation")
        validation_report = validator.validate_dataframe(df, "测试流水线")
        validation_report.print_summary()
        
        # 3. 数据清洗
        print("\n3. 🧹 数据清洗...")
        cleaner = DataCleaner(strategy=CleaningStrategy.MODERATE)
        cleaner.add_builtin_rule("remove_duplicate_timestamps")
        cleaner.add_builtin_rule("fill_missing_prices_with_interpolation")
        cleaner.add_builtin_rule("ensure_price_positive")
        cleaner.add_builtin_rule("fix_high_low_relationship")
        
        cleaned_df, cleaning_report = cleaner.clean_dataframe(df, "测试流水线")
        cleaning_report.print_summary()
        
        # 4. 重新检查清洗后数据
        print("\n4. ✅ 清洗后质量检查...")
        final_report = checker.check_dataframe(cleaned_df, "清洗后数据", timeframe="1h")
        final_report.print_summary()
        
        # 验证清洗效果
        print("\n5. 📈 清洗效果验证:")
        print(f"   原始数据: {df.shape[0]} 行 × {df.shape[1]} 列")
        print(f"   清洗后数据: {cleaned_df.shape[0]} 行 × {cleaned_df.shape[1]} 列")
        print(f"   删除行数: {df.shape[0