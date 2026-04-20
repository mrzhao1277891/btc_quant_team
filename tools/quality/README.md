# 🧪 数据质量工具库

## 📋 概述
专业的加密货币数据质量工具套件，包含检查、验证、清洗、监控四大模块。

## 🏗️ 架构设计
```
quality/
├── checker.py      # 质量检查
├── validator.py    # 数据验证
├── cleaner.py      # 数据清洗
├── monitor.py      # 质量监控
└── __init__.py     # 统一导出
```

## 🚀 快速使用

### 导入工具
```python
# 导入所有质量工具
from tools.quality import (
    # 质量检查
    DataQualityChecker, QualityReport,
    
    # 数据验证
    DataValidator, ValidationReport,
    
    # 数据清洗
    DataCleaner, CleaningReport,
    
    # 质量监控
    DataQualityMonitor, MonitorReport
)

# 或按需导入
from tools.quality.checker import DataQualityChecker
from tools.quality.validator import DataValidator
from tools.quality.cleaner import DataCleaner
from tools.quality.monitor import DataQualityMonitor
```

### 基本示例
```python
import pandas as pd

# 创建示例数据
data = {
    'timestamp': pd.date_range('2024-01-01', periods=100, freq='H'),
    'open': [70000 + i*10 + np.random.randn()*100 for i in range(100)],
    'high': [70100 + i*10 + np.random.randn()*100 for i in range(100)],
    'low': [69900 + i*10 + np.random.randn()*100 for i in range(100)],
    'close': [70050 + i*10 + np.random.randn()*100 for i in range(100)],
    'volume': [1000 + np.random.randn()*100 for _ in range(100)]
}
df = pd.DataFrame(data)

# 1. 质量检查
checker = DataQualityChecker()
report = checker.check_dataframe(df, "BTC示例数据", timeframe="1h")
report.print_summary()

# 2. 数据验证
validator = DataValidator()
validator.add_builtin_rule("kline_required_fields")
validator.add_builtin_rule("kline_price_positive")
report = validator.validate_dataframe(df, "BTC示例数据")
report.print_summary()

# 3. 数据清洗
cleaner = DataCleaner()
cleaner.add_builtin_rule("fill_missing_prices_with_interpolation")
cleaner.add_builtin_rule("remove_duplicate_timestamps")
cleaned_df, report = cleaner.clean_dataframe(df, "BTC示例数据")
report.print_summary()

# 4. 质量监控
def data_source():
    """模拟数据源函数"""
    return df.sample(50)  # 随机采样50行

monitor = DataQualityMonitor("BTC质量监控", check_interval=60)
monitor.add_builtin_rule("data_freshness_warning")
monitor.add_builtin_rule("completeness_warning")
monitor.start_monitoring(data_source, "BTC示例数据")
```

## 📊 工具分类

### 1. 质量检查工具 (Checker)
**职责**: 全面评估数据质量

| 功能 | 类/函数 | 用途 |
|------|---------|------|
| **完整性检查** | `_check_completeness()` | 检查数据缺失、空值 |
| **一致性检查** | `_check_consistency()` | 检查数据类型、格式 |
| **准确性检查** | `_check_accuracy()` | 检查异常值、逻辑错误 |
| **及时性检查** | `_check_timeliness()` | 检查数据新鲜度 |
| **有效性检查** | `_check_validity()` | 检查数据有效性 |
| **综合报告** | `QualityReport` | 生成质量报告 |

**质量维度**:
- **完整性 (Completeness)**: 数据是否完整
- **一致性 (Consistency)**: 数据是否一致  
- **准确性 (Accuracy)**: 数据是否准确
- **及时性 (Timeliness)**: 数据是否及时
- **有效性 (Validity)**: 数据是否有效

**质量等级**:
- 🏆 **优秀 (95-100%)**: 数据质量极好
- ✅ **良好 (85-94%)**: 数据质量良好
- ⚠️ **一般 (70-84%)**: 数据质量一般
- ❌ **较差 (50-69%)**: 数据质量较差
- 🔥 **严重 (<50%)**: 数据质量严重问题

### 2. 数据验证工具 (Validator)
**职责**: 验证数据是否符合规则

| 验证类型 | 说明 | 示例 |
|----------|------|------|
| **必需性验证** | 验证字段是否存在 | 必需字段: timestamp, open, high, low, close, volume |
| **类型验证** | 验证数据类型 | 价格应为float，时间戳应为datetime |
| **范围验证** | 验证数值范围 | 价格 > 0，成交量 >= 0 |
| **模式验证** | 验证数据模式 | 时间戳格式，价格格式 |
| **唯一性验证** | 验证数据唯一性 | 时间戳唯一 |
| **关系验证** | 验证数据间关系 | high >= low, open/close在high/low范围内 |
| **自定义验证** | 用户自定义规则 | 价格变化不超过50% |

**内置验证规则**:
- `kline_required_fields`: K线必需字段验证
- `kline_price_positive`: 价格正数验证
- `kline_high_low_relation`: 高低价关系验证
- `kline_open_close_range`: 开盘收盘价范围验证
- `kline_volume_positive`: 成交量正数验证
- `kline_timestamp_unique`: 时间戳唯一性验证

### 3. 数据清洗工具 (Cleaner)
**职责**: 清洗和修复数据问题

| 清洗方法 | 说明 | 适用场景 |
|----------|------|----------|
| **删除法** | 直接删除问题数据 | 重复数据，严重缺失数据 |
| **填充法** | 使用统计值填充 | 少量缺失值 |
| **插值法** | 使用前后值插值 | 时间序列缺失值 |
| **修正法** | 基于规则修正 | 异常值，逻辑错误 |
| **标记法** | 标记问题但不修改 | 需要保留原始数据 |
| **转换法** | 数据格式转换 | 类型转换，标准化 |

**内置清洗规则**:
- `fill_missing_prices_with_interpolation`: 价格缺失值插值填充
- `remove_duplicate_timestamps`: 删除重复时间戳
- `correct_price_outliers_with_iqr`: 价格异常值IQR修正
- `ensure_price_positive`: 确保价格为正数
- `fix_high_low_relationship`: 修正高低价关系
- `convert_timestamp_to_datetime`: 时间戳转换为日期时间

**清洗策略**:
- 🔥 **激进策略**: 尽可能修复所有问题
- ⚖️ **适中策略**: 平衡修复和保留
- 🛡️ **保守策略**: 尽可能保留原始数据

### 4. 质量监控工具 (Monitor)
**职责**: 持续监控数据质量

| 监控类型 | 说明 | 功能 |
|----------|------|------|
| **实时监控** | 当前数据质量 | 实时检查，即时警报 |
| **历史监控** | 质量变化趋势 | 趋势分析，历史对比 |
| **预测监控** | 质量预测 | 预测未来质量问题 |
| **对比监控** | 与基准对比 | 基准对比，异常检测 |

**警报级别**:
- ℹ️ **信息 (INFO)**: 仅供参考
- ⚠️ **警告 (WARNING)**: 需要注意
- ❌ **错误 (ERROR)**: 需要处理
- 🔥 **严重 (CRITICAL)**: 立即处理

**内置警报规则**:
- `data_freshness_critical`: 数据新鲜度严重下降
- `completeness_warning`: 数据完整性警告
- `accuracy_critical`: 数据准确性严重问题
- `outlier_detected`: 检测到异常值
- `data_delay_warning`: 数据延迟警告

## 🔧 使用指南

### 数据质量检查流程
```python
def quality_check_pipeline(df, dataset_name):
    """数据质量检查流水线"""
    
    # 1. 质量检查
    checker = DataQualityChecker()
    quality_report = checker.check_dataframe(df, dataset_name, timeframe="4h")
    
    # 2. 数据验证
    validator = DataValidator()
    validator.add_builtin_rule("kline_required_fields")
    validator.add_builtin_rule("kline_price_positive")
    validation_report = validator.validate_dataframe(df, dataset_name)
    
    # 3. 根据检查结果决定是否清洗
    if quality_report.overall_score < 80 or validation_report.failed_rules > 0:
        print("⚠️  数据质量不佳，开始清洗...")
        
        # 4. 数据清洗
        cleaner = DataCleaner(strategy=CleaningStrategy.MODERATE)
        cleaner.add_builtin_rule("fill_missing_prices_with_interpolation")
        cleaner.add_builtin_rule("remove_duplicate_timestamps")
        cleaner.add_builtin_rule("correct_price_outliers_with_iqr")
        
        cleaned_df, cleaning_report = cleaner.clean_dataframe(df, dataset_name)
        
        # 5. 重新检查清洗后数据
        final_report = checker.check_dataframe(cleaned_df, f"{dataset_name}_cleaned", timeframe="4h")
        
        return cleaned_df, {
            "quality_report": quality_report,
            "validation_report": validation_report,
            "cleaning_report": cleaning_report,
            "final_report": final_report
        }
    else:
        print("✅ 数据质量良好，无需清洗")
        return df, {
            "quality_report": quality_report,
            "validation_report": validation_report
        }
```

### 数据库质量检查
```python
def check_database_quality(db_path, table_name):
    """检查数据库表质量"""
    
    # 质量检查
    checker = DataQualityChecker()
    report = checker.check_database(db_path, table_name, timeframe="1d")
    
    # 数据验证
    validator = DataValidator()
    validator.add_builtin_rule("kline_required_fields")
    validator.add_builtin_rule("kline_high_low_relation")
    validation_report = validator.validate_database(db_path, table_name)
    
    # 打印报告
    print("📊 数据库质量检查结果:")
    report.print_summary()
    validation_report.print_summary()
    
    return report, validation_report
```

### 实时质量监控
```python
def setup_realtime_monitoring():
    """设置实时质量监控"""
    
    def get_latest_data():
        """获取最新数据"""
        # 这里实现从数据库或API获取最新数据
        import sqlite3
        conn = sqlite3.connect("crypto_data.db")
        df = pd.read_sql_query("SELECT * FROM klines ORDER BY timestamp DESC LIMIT 100", conn)
        conn.close()
        return df
    
    # 创建监控器
    monitor = DataQualityMonitor(
        monitor_name="BTC实时质量监控",
        check_interval=300,  # 5分钟检查一次
        alert_rules=[]
    )
    
    # 添加警报规则
    monitor.add_builtin_rule("data_freshness_warning")
    monitor.add_builtin_rule("completeness_warning")
    monitor.add_builtin_rule("outlier_detected")
    monitor.add_builtin_rule("data_delay_critical")
    
    # 定义警报处理函数
    def handle_alert(alert):
        """处理警报"""
        print(f"🚨 收到警报: {alert.message}")
        
        # 这里可以添加警报处理逻辑，如:
        # - 发送邮件
        # - 发送Slack消息
        # - 记录到日志
        # - 触发自动修复
    
    # 开始监控
    monitor.start_monitoring(
        data_source=get_latest_data,
        dataset_name="BTC实时数据",
        check_callback=lambda report: handle_alerts(report.alerts)
    )
    
    return monitor
```

## 📈 高级功能

### 自定义质量规则
```python
# 自定义验证规则
custom_validation_rule = ValidationRule(
    name="价格变化合理性验证",
    validation_type=ValidationType.CUSTOM,
    field="close",
    severity=ValidationSeverity.WARNING,
    description="验证相邻K线价格变化不超过20%",
    parameters={"max_change": 0.2},
    custom_validator=lambda df, field, params: (
        df[field].pct_change().abs().max() <= params["max_change"]
    )
)

# 自定义清洗规则
custom_cleaning_rule = CleaningRule(
    name="修正异常成交量",
    method=CleaningMethod.CORRECT,
    target_field="volume",
    condition="volume > 1000000",  # 成交量超过100万
    parameters={
        "correction_method": "clip",
        "upper_limit": 1000000
    },
    description="修正异常高的成交量",
    priority=2
)

# 自定义警报规则
custom_alert_rule = AlertRule(
    name="RSI超买超卖警报",
    condition="rsi > 70 or rsi < 30",
    level=AlertLevel.WARNING,
    message_template="RSI {value:.1f} 进入{zone}区域",
    cooldown_seconds=600,
    parameters={"zone": "超买" if rsi > 70 else "超卖"}
)
```

### 质量趋势分析
```python
def analyze_quality_trend(monitor, metric_name, window=24):
    """分析质量趋势"""
    
    # 获取历史指标
    history = list(monitor.metrics_history)
    
    # 过滤指定指标
    metric_history = [m for m in history if m.name == metric_name]
    
    if len(metric_history) < 2:
        return None
    
    # 计算趋势
    values = [m.value for m in metric_history[-window:]]
    timestamps = [m.timestamp for m in metric_history[-window:]]
    
    # 简单线性趋势
    if len(values) >= 2:
        x = range(len(values))
        slope = np.polyfit(x, values, 1)[0]
        
        # 判断趋势
        if slope > 0.01:
            trend = "上升"
        elif slope < -0.01:
            trend = "下降"
        else:
            trend = "平稳"
        
        return {
            "metric": metric_name,
            "trend": trend,
            "slope": slope,
            "current_value": values[-1],
            "average_value": np.mean(values),
            "volatility": np.std(values)
        }
    
    return None
```

### 自动化质量修复
```python
class AutoQualityFixer:
    """自动化质量修复器"""
    
    def __init__(self):
        self.checker = DataQualityChecker()
        self.cleaner = DataCleaner()
        self.validator = DataValidator()
        
        # 配置修复规则
        self._setup_fix_rules()
    
    def _setup_fix_rules(self):
        """设置修复规则"""
        # 根据质量问题类型配置修复规则
        self.fix_mapping = {
            "missing_data": [
                "fill_missing_prices_with_interpolation",
                "fill_missing_volume_with_mean"
            ],
            "outliers": [
                "correct_price_outliers_with_iqr",
                "flag_extreme_price_changes"
            ],
            "duplicates": [
                "remove_duplicate_timestamps"
            ],
            "format_issues": [
                "convert_timestamp_to_datetime",
                "normalize_column_names"
            ],
            "logic_errors": [
                "ensure_price_positive",
                "fix_high_low_relationship"
            ]
        }
    
    def auto_fix(self, df, dataset_name):
        """自动化修复"""
        print(f"🔧 开始自动化修复: {dataset_name}")
        
        # 1. 检查质量问题
        report = self.checker.check_dataframe(df, dataset_name)
        
        # 2. 分析问题类型
        issues = self._analyze_issues(report)
        
        # 3. 应用修复规则
        for issue_type in issues:
            if issue_type in self.fix_mapping:
                for rule_name in self.fix_mapping[issue_type]:
                    self.cleaner.add_builtin_rule(rule_name)
        
        # 4. 执行清洗
        cleaned_df, cleaning_report = self.cleaner.clean_dataframe(df, dataset_name)
        
        # 5. 验证修复结果
        validation_report = self.validator.validate_dataframe(cleaned_df, f"{dataset_name}_fixed")
        
        print(f"✅ 自动化修复完成")
        print(f"   原始问题: {len(issues)} 类")
        print(f"   应用规则: {len(self.cleaner.rules)} 条")
        print(f"   修复后验证: {validation_report.passed_rules}/{validation_report.total_rules} 通过")
        
        return cleaned_df, {
            "quality_report": report,
            "cleaning_report": cleaning_report,
            "validation_report": validation_report
        }
    
    def _analyze_issues(self, report):
        """分析质量问题类型"""
        issues = set()
        
        for metric in report.metrics:
            if not metric.passed:
                # 根据指标名称判断问题类型
                if "completeness" in metric.metric_name.lower():
                    issues.add("missing_data")
                elif "outlier" in metric.metric_name.lower():
                    issues.add("outliers")
                elif "consistency" in metric.metric_name.lower():
                    issues.add("format_issues")
                elif "accuracy" in metric.metric_name.lower():
                    issues.add("logic_errors")
        
        for issue in report.issues:
            if "重复" in issue["description"]:
                issues.add("duplicates")
