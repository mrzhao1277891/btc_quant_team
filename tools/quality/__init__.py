"""
数据质量工具包

导出以下质量工具:

质量检查 (checker/):
- DataQualityChecker: 数据质量检查器
- QualityReport: 质量报告
- QualityMetric: 质量指标
- QualityDimension: 质量维度
- QualityLevel: 质量等级

数据验证 (validator/):
- DataValidator: 数据验证器
- ValidationReport: 验证报告
- ValidationRule: 验证规则
- ValidationResult: 验证结果
- ValidationType: 验证类型
- ValidationSeverity: 验证严重性

数据清洗 (cleaner/):
- DataCleaner: 数据清洗器
- CleaningReport: 清洗报告
- CleaningRule: 清洗规则
- CleaningResult: 清洗结果
- CleaningMethod: 清洗方法
- CleaningStrategy: 清洗策略

质量监控 (monitor/):
- DataQualityMonitor: 数据质量监控器
- MonitorReport: 监控报告
- AlertRule: 警报规则
- Alert: 警报
- MonitorMetric: 监控指标
- AlertLevel: 警报级别
- MonitorType: 监控类型

使用示例:
    from tools.quality.checker import DataQualityChecker
    from tools.quality.validator import DataValidator
    from tools.quality.cleaner import DataCleaner
    from tools.quality.monitor import DataQualityMonitor
    
    # 质量检查
    checker = DataQualityChecker()
    report = checker.check_dataframe(df, "BTC数据")
    report.print_summary()
    
    # 数据验证
    validator = DataValidator()
    report = validator.validate_dataframe(df, "BTC数据")
    report.print_summary()
    
    # 数据清洗
    cleaner = DataCleaner()
    cleaned_df, report = cleaner.clean_dataframe(df, "BTC数据")
    report.print_summary()
    
    # 质量监控
    monitor = DataQualityMonitor("BTC质量监控")
    monitor.start_monitoring(data_source_func, "BTC数据")
"""

# 质量检查工具
from .checker import (
    DataQualityChecker,
    QualityReport,
    QualityMetric,
    QualityDimension,
    QualityLevel
)

# 数据验证工具
from .validator import (
    DataValidator,
    ValidationReport,
    ValidationRule,
    ValidationResult,
    ValidationType,
    ValidationSeverity
)

# 数据清洗工具
from .cleaner import (
    DataCleaner,
    CleaningReport,
    CleaningRule,
    CleaningResult,
    CleaningMethod,
    CleaningStrategy
)

# 质量监控工具
from .monitor import (
    DataQualityMonitor,
    MonitorReport,
    AlertRule,
    Alert,
    MonitorMetric,
    AlertLevel,
    MonitorType
)

__all__ = [
    # 质量检查
    'DataQualityChecker',
    'QualityReport',
    'QualityMetric',
    'QualityDimension',
    'QualityLevel',
    
    # 数据验证
    'DataValidator',
    'ValidationReport',
    'ValidationRule',
    'ValidationResult',
    'ValidationType',
    'ValidationSeverity',
    
    # 数据清洗
    'DataCleaner',
    'CleaningReport',
    'CleaningRule',
    'CleaningResult',
    'CleaningMethod',
    'CleaningStrategy',
    
    # 质量监控
    'DataQualityMonitor',
    'MonitorReport',
    'AlertRule',
    'Alert',
    'MonitorMetric',
    'AlertLevel',
    'MonitorType'
]