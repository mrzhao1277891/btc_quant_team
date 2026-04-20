#!/usr/bin/env python3
"""
质量工具演示脚本

展示如何使用质量工具检查、验证、清洗和监控BTC数据
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tools.quality.checker import DataQualityChecker
from tools.quality.validator import DataValidator
from tools.quality.cleaner import DataCleaner, CleaningStrategy
from tools.quality.monitor import DataQualityMonitor

def create_sample_data(include_problems=True):
    """
    创建示例BTC数据
    
    参数:
        include_problems: 是否包含数据质量问题
    """
    # 基础数据
    n = 100
    base_time = datetime(2024, 1, 1)
    
    data = {
        'timestamp': [base_time + timedelta(hours=i) for i in range(n)],
        'open': [70000 + i*10 + np.random.randn()*100 for i in range(n)],
        'high': [70100 + i*10 + np.random.randn()*100 for i in range(n)],
        'low': [69900 + i*10 + np.random.randn()*100 for i in range(n)],
        'close': [70050 + i*10 + np.random.randn()*100 for i in range(n)],
        'volume': [1000 + np.random.randn()*100 for _ in range(n)]
    }
    
    df = pd.DataFrame(data)
    
    if include_problems:
        print("⚠️  添加数据质量问题...")
        
        # 1. 添加缺失值
        df.loc[10:15, 'open'] = np.nan
        df.loc[20:25, 'volume'] = np.nan
        
        # 2. 添加重复数据
        duplicate_rows = df.iloc[30:35].copy()
        duplicate_rows['timestamp'] = duplicate_rows['timestamp'] + timedelta(seconds=1)
        df = pd.concat([df, duplicate_rows], ignore_index=True)
        
        # 3. 添加异常值
        df.loc[40, 'close'] = 100000  # 极端高价
        df.loc[45, 'close'] = 50000   # 极端低价
        df.loc[50, 'volume'] = 1000000  # 异常高成交量
        
        # 4. 添加逻辑错误
        df.loc[60, 'high'] = 69000  # high < low
        df.loc[60, 'low'] = 71000   # low > high
        
        # 5. 添加负价格
        df.loc[70, 'close'] = -100
        
        # 6. 添加格式问题 (字符串时间戳)
        df.loc[80, 'timestamp'] = '2024-01-01 00:00:00'
    
    return df

def demo_quality_checker():
    """演示质量检查工具"""
    print("=" * 60)
    print("🧪 演示: 数据质量检查工具")
    print("=" * 60)
    
    # 创建测试数据
    df = create_sample_data(include_problems=True)
    print(f"📊 测试数据: {df.shape[0]} 行 × {df.shape[1]} 列")
    
    # 创建质量检查器
    checker = DataQualityChecker()
    
    # 检查数据质量
    print("\n📈 执行质量检查...")
    report = checker.check_dataframe(df, "BTC示例数据", timeframe="1h")
    
    # 打印报告
    report.print_summary()
    
    # 显示详细指标
    print("\n📋 详细质量指标:")
    for metric in report.metrics:
        status = "✅" if metric.passed else "❌"
        print(f"  {status} {metric.metric_name}: {metric.value:.1%}")
    
    return report

def demo_data_validator():
    """演示数据验证工具"""
    print("\n" + "=" * 60)
    print("🔍 演示: 数据验证工具")
    print("=" * 60)
    
    # 创建测试数据
    df = create_sample_data(include_problems=True)
    
    # 创建数据验证器
    validator = DataValidator()
    
    # 添加内置验证规则
    print("📋 添加验证规则:")
    rules_to_add = [
        "kline_required_fields",
        "kline_price_positive",
        "kline_high_low_relation",
        "kline_open_close_range",
        "kline_volume_positive",
        "kline_timestamp_unique"
    ]
    
    for rule_name in rules_to_add:
        validator.add_builtin_rule(rule_name)
        print(f"  ✅ {rule_name}")
    
    # 执行验证
    print("\n🔍 执行数据验证...")
    report = validator.validate_dataframe(df, "BTC示例数据")
    
    # 打印报告
    report.print_summary()
    
    return report

def demo_data_cleaner():
    """演示数据清洗工具"""
    print("\n" + "=" * 60)
    print("🧹 演示: 数据清洗工具")
    print("=" * 60)
    
    # 创建测试数据
    df = create_sample_data(include_problems=True)
    original_shape = df.shape
    print(f"📊 原始数据: {original_shape[0]} 行 × {original_shape[1]} 列")
    
    # 显示原始数据问题
    print("\n⚠️  原始数据问题:")
    print(f"  缺失值: {df.isnull().sum().sum()} 个")
    print(f"  重复行: {df.duplicated(subset=['timestamp']).sum()} 行")
    print(f"  负价格: {(df['close'] <= 0).sum()} 个")
    print(f"  高低价错误: {(df['high'] < df['low']).sum()} 行")
    
    # 创建数据清洗器
    cleaner = DataCleaner(strategy=CleaningStrategy.MODERATE)
    
    # 添加内置清洗规则
    print("\n📋 添加清洗规则:")
    rules_to_add = [
        "remove_duplicate_timestamps",
        "fill_missing_prices_with_interpolation",
        "fill_missing_volume_with_mean",
        "correct_price_outliers_with_iqr",
        "ensure_price_positive",
        "fix_high_low_relationship",
        "convert_timestamp_to_datetime"
    ]
    
    for rule_name in rules_to_add:
        cleaner.add_builtin_rule(rule_name)
        print(f"  ✅ {rule_name}")
    
    # 执行清洗
    print("\n🧹 执行数据清洗...")
    cleaned_df, report = cleaner.clean_dataframe(df, "BTC示例数据")
    
    # 打印报告
    report.print_summary()
    
    # 显示清洗效果
    print("\n📈 清洗效果对比:")
    print(f"  原始数据: {original_shape[0]} 行")
    print(f"  清洗后数据: {cleaned_df.shape[0]} 行")
    print(f"  删除行数: {original_shape[0] - cleaned_df.shape[0]}")
    
    print(f"\n  原始缺失值: {df.isnull().sum().sum()} 个")
    print(f"  清洗后缺失值: {cleaned_df.isnull().sum().sum()} 个")
    
    print(f"\n  原始负价格: {(df['close'] <= 0).sum()} 个")
    print(f"  清洗后负价格: {(cleaned_df['close'] <= 0).sum()} 个")
    
    print(f"\n  原始高低价错误: {(df['high'] < df['low']).sum()} 行")
    print(f"  清洗后高低价错误: {(cleaned_df['high'] < cleaned_df['low']).sum()} 行")
    
    return cleaned_df, report

def demo_quality_monitor():
    """演示质量监控工具"""
    print("\n" + "=" * 60)
    print("📡 演示: 数据质量监控工具")
    print("=" * 60)
    
    # 创建模拟数据源
    data_history = []
    
    def create_monitoring_data():
        """创建监控数据"""
        # 模拟实时数据，每次略有不同
        base_df = create_sample_data(include_problems=False)
        
        # 添加一些随机问题
        problem_df = base_df.copy()
        
        # 随机添加缺失值
        if np.random.random() < 0.3:
            n_missing = np.random.randint(1, 5)
            rows = np.random.choice(len(problem_df), n_missing, replace=False)
            cols = np.random.choice(['open', 'close', 'volume'], n_missing, replace=True)
            for row, col in zip(rows, cols):
                problem_df.loc[row, col] = np.nan
        
        # 随机添加延迟
        if np.random.random() < 0.2:
            delay_hours = np.random.randint(1, 6)
            problem_df['timestamp'] = problem_df['timestamp'] - timedelta(hours=delay_hours)
        
        data_history.append({
            'timestamp': datetime.now(),
            'data': problem_df,
            'missing_count': problem_df.isnull().sum().sum(),
            'delay_hours': delay_hours if 'delay_hours' in locals() else 0
        })
        
        return problem_df
    
    # 创建质量监控器
    monitor = DataQualityMonitor(
        monitor_name="BTC质量监控演示",
        check_interval=10,  # 10秒检查一次 (演示用)
        alert_rules=[]
    )
    
    # 添加内置警报规则
    print("📋 添加警报规则:")
    rules_to_add = [
        "data_freshness_warning",
        "data_freshness_critical",
        "completeness_warning",
        "completeness_critical",
        "outlier_detected",
        "data_delay_warning",
        "data_delay_critical"
    ]
    
    for rule_name in rules_to_add:
        monitor.add_builtin_rule(rule_name)
        print(f"  ✅ {rule_name}")
    
    # 定义警报处理函数
    def handle_alerts(alerts):
        """处理警报"""
        if alerts:
            print(f"\n🚨 收到 {len(alerts)} 个警报:")
            for alert in alerts:
                level = alert.rule.level.value.upper()
                print(f"  [{level}] {alert.message}")
    
    # 开始监控 (运行几次检查)
    print("\n📡 开始质量监控 (运行5次检查)...")
    
    # 手动运行几次检查来演示
    for i in range(5):
        print(f"\n--- 检查 #{i+1} ---")
        
        # 获取数据
        df = create_monitoring_data()
        
        # 手动执行检查
        start_time = datetime.now()
        
        # 这里简化，实际应该使用monitor的内部方法
        print(f"📊 数据: {df.shape[0]} 行 × {df.shape[1]} 列")
        print(f"⏰ 数据延迟: {data_history[-1]['delay_hours']} 小时")
        print(f"❓ 缺失值: {data_history[-1]['missing_count']} 个")
        
        # 模拟警报
        if data_history[-1]['delay_hours'] > 2:
            print("🚨 [CRITICAL] 数据严重延迟")
        elif data_history[-1]['delay_hours'] > 0.5:
            print("⚠️  [WARNING] 数据延迟")
        
        if data_history[-1]['missing_count'] > 10:
            print("🚨 [CRITICAL] 缺失数据过多")
        elif data_history[-1]['missing_count'] > 5:
            print("⚠️  [WARNING] 缺失数据")
        
        # 等待一下
        import time
        time.sleep(2)
    
    print("\n✅ 监控演示完成")
    print(f"📊 监控历史: {len(data_history)} 次检查")
    
    return monitor

def demo_quality_pipeline():
    """演示完整质量流水线"""
    print("\n" + "=" * 60)
    print("🚀 演示: 完整质量流水线")
    print("=" * 60)
    
    # 1. 创建有问题的数据
    print("\n1. 📊 创建测试数据...")
    df = create_sample_data(include_problems=True)
    print(f"   数据大小: {df.shape[0]} 行 × {df.shape[1]} 列")
    
    # 2. 质量检查
    print("\n2. 📈 执行质量检查...")
    checker = DataQualityChecker()
    quality_report = checker.check_dataframe(df, "流水线测试", timeframe="1h")
    
    print(f"   综合评分: {quality_report.overall_score:.1f}/100")
    print(f"   质量等级: {quality_report.quality_level.value}")
    print(f"   发现问题: {len(quality_report.issues)} 个")
    
    # 3. 数据验证
    print("\n3. 🔍 执行数据验证...")
    validator = DataValidator()
    validator.add_builtin_rule("kline_required_fields")
    validator.add_builtin_rule("kline_price_positive")
    validator.add_builtin_rule("kline_high_low_relation")
    
    validation_report = validator.validate_dataframe(df, "流水线测试")
    
    print(f"   验证规则: {validation_report.total_rules} 条")
    print(f"   通过规则: {validation_report.passed_rules} 条")
    print(f"   失败规则: {validation_report.failed_rules} 条")
    
    # 4. 决定是否清洗
    need_cleaning = quality_report.overall_score < 80 or validation_report.failed_rules > 0
    
    if need_cleaning:
        print("\n4. 🧹 数据需要清洗，执行清洗...")
        
        cleaner = DataCleaner(strategy=CleaningStrategy.MODERATE)
        cleaner.add_builtin_rule("remove_duplicate_timestamps")
        cleaner.add_builtin_rule("fill_missing_prices_with_interpolation")
        cleaner.add_builtin_rule("ensure_price_positive")
        cleaner.add_builtin_rule("fix_high_low_relationship")
        
        cleaned_df, cleaning_report = cleaner.clean_dataframe(df, "流水线测试")
        
        print(f"   原始数据: {df.shape[0]} 行")
        print(f"   清洗后数据: {cleaned_df.shape[0]} 行")
        print(f"   删除行数: {df.shape[0] - cleaned_df.shape[0]}")
        print(f"   修改单元格: {cleaning_report.modified_cells} 个")
        
        # 5. 验证清洗效果
        print("\n5. ✅ 验证清洗效果...")
        final_report = checker.check_dataframe(cleaned_df, "清洗后数据", timeframe="1h")
        
        print(f"   原始评分: {quality_report.overall_score:.1f}/100")
        print(f"   清洗后评分: {final_report.overall_score:.1f}/100")
        print(f"   质量提升: {final_report.overall_score - quality_report.overall_score:+.1f} 分")
        
        if final_report.overall_score > quality_report.overall_score:
            print("   🎉 清洗成功，数据质量提升！")
        else:
            print("   ⚠️  清洗效果有限")
        
        return cleaned_df, {
            "quality_report": quality_report,
            "validation_report": validation_report,
            "cleaning_report": cleaning_report,
            "final_report": final_report
        }
    else:
        print("\n4. ✅ 数据质量良好，无需清洗")
        return df, {
            "quality_report": quality_report,
            "validation_report": validation_report
        }

def main():
    """主函数"""
    print("🎯 BTC数据质量工具演示")
    print("=" * 60)
    
    try:
        # 演示各个工具
        print("\n选择演示模式:")
        print("1. 📊 质量检查工具")
        print("2. 🔍 数据验证工具")
        print("3. 🧹 数据清洗工具")
        print("4. 📡 质量监控工具")
        print("5. 🚀 完整质量流水线")
        print("6. 🔄 全部演示")
        
        choice = input("\n请输入选择 (1-6): ").strip()
        
        if choice == "1":
            demo_quality_checker()
        elif choice == "2":
            demo_data_validator()
        elif choice == "3":
            demo_data_cleaner()
        elif choice == "4":
            demo_quality_monitor()
        elif choice == "5":
            demo_quality_pipeline()
        elif choice == "6":
            demo_quality_checker()
            demo_data_validator()
            demo_data_cleaner()
            demo_quality_monitor()
            demo_quality_pipeline()
        else:
            print("❌ 无效选择")
        
        print("\n" + "=" * 60)
        print("✅ 演示完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()