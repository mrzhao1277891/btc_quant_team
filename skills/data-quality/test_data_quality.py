#!/usr/bin/env python3
"""
数据质量Skill测试脚本
"""

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

def test_basic_functionality():
    """测试基础功能"""
    print("🧪 数据质量Skill基础测试")
    print("=" * 70)
    
    # 1. 创建模拟数据
    print("\n📊 1. 创建模拟数据...")
    dates = pd.date_range(start='2024-01-01', end='2024-04-19', freq='D')
    data = pd.DataFrame({
        'timestamp': dates,
        'open': np.random.normal(70000, 5000, len(dates)),
        'high': np.random.normal(71000, 5000, len(dates)),
        'low': np.random.normal(69000, 5000, len(dates)),
        'close': np.random.normal(70500, 5000, len(dates)),
        'volume': np.random.normal(1000, 200, len(dates))
    })
    
    # 添加一些数据质量问题
    data.loc[50, 'close'] = 100000  # 价格异常
    data.loc[100, 'volume'] = 0     # 成交量异常
    data = data.drop([30, 31])      # 缺失数据
    data.loc[150, 'high'] = 65000   # 价格逻辑错误 (high < low)
    data.loc[150, 'low'] = 68000
    
    print(f"✅ 模拟数据创建完成")
    print(f"   数据形状: {data.shape}")
    print(f"   时间范围: {data['timestamp'].min()} 到 {data['timestamp'].max()}")
    print(f"   缺失值数量: {data.isnull().sum().sum()}")
    
    # 2. 测试基础检查器
    print("\n🔍 2. 测试基础检查器...")
    
    class BasicDataQualityChecker:
        def __init__(self):
            self.results = {}
        
        def check_completeness(self, data):
            """检查数据完整性"""
            total_rows = len(data)
            missing_rows = data.isnull().any(axis=1).sum()
            completeness = 1 - (missing_rows / total_rows)
            
            return {
                'total_rows': total_rows,
                'missing_rows': missing_rows,
                'completeness_score': completeness,
                'status': 'PASS' if completeness > 0.95 else 'FAIL'
            }
        
        def check_consistency(self, data):
            """检查数据一致性"""
            # 检查价格逻辑: high >= low, high >= close >= low
            price_logic_errors = 0
            for _, row in data.iterrows():
                if row['high'] < row['low'] or row['close'] < row['low'] or row['close'] > row['high']:
                    price_logic_errors += 1
            
            consistency = 1 - (price_logic_errors / len(data))
            
            return {
                'price_logic_errors': price_logic_errors,
                'consistency_score': consistency,
                'status': 'PASS' if consistency > 0.98 else 'FAIL'
            }
        
        def check_accuracy(self, data):
            """检查数据准确性"""
            # 使用Z-Score检测异常值
            from scipy import stats
            z_scores = np.abs(stats.zscore(data['close'].dropna()))
            anomalies = np.sum(z_scores > 3)
            
            accuracy = 1 - (anomalies / len(data))
            
            return {
                'anomalies_detected': int(anomalies),
                'accuracy_score': accuracy,
                'status': 'PASS' if accuracy > 0.95 else 'FAIL'
            }
        
        def check_all(self, data):
            """执行所有检查"""
            self.results['completeness'] = self.check_completeness(data)
            self.results['consistency'] = self.check_consistency(data)
            self.results['accuracy'] = self.check_accuracy(data)
            
            # 计算总体评分
            scores = [
                self.results['completeness']['completeness_score'],
                self.results['consistency']['consistency_score'],
                self.results['accuracy']['accuracy_score']
            ]
            overall_score = np.mean(scores)
            
            self.results['overall'] = {
                'score': overall_score,
                'status': 'PASS' if overall_score > 0.90 else 'FAIL'
            }
            
            return self.results
        
        def print_summary(self):
            """打印检查结果摘要"""
            print("=" * 60)
            print("📊 数据质量检查结果")
            print("=" * 60)
            
            for check_name, result in self.results.items():
                if check_name == 'overall':
                    continue
                    
                score_key = f"{check_name}_score"
                score = result.get(score_key, 0)
                status = result.get('status', 'UNKNOWN')
                
                print(f"{check_name.upper():15} {score:.1%} [{status}]")
                
                # 显示详细信息
                for key, value in result.items():
                    if key not in [score_key, 'status']:
                        print(f"  {key}: {value}")
            
            print("-" * 60)
            overall = self.results.get('overall', {})
            print(f"总体评分: {overall.get('score', 0):.1%} [{overall.get('status', 'UNKNOWN')}]")
            print("=" * 60)
    
    # 执行检查
    checker = BasicDataQualityChecker()
    results = checker.check_all(data)
    checker.print_summary()
    
    # 3. 测试配置文件
    print("\n🔧 3. 测试配置文件...")
    config_path = Path(__file__).parent / "config/default.yaml"
    
    if config_path.exists():
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if config and 'quality_checks' in config:
                print(f"✅ 配置文件加载成功")
                checks = config['quality_checks']
                print(f"   完整性检查: {'启用' if checks.get('enable_completeness') else '禁用'}")
                print(f"   一致性检查: {'启用' if checks.get('enable_consistency') else '禁用'}")
                print(f"   准确性检查: {'启用' if checks.get('enable_accuracy') else '禁用'}")
                print(f"   及时性检查: {'启用' if checks.get('enable_timeliness') else '禁用'}")
            else:
                print("❌ 配置文件格式错误")
        except Exception as e:
            print(f"❌ 配置文件加载失败: {e}")
    else:
        print("❌ 配置文件不存在")
    
    # 4. 测试数据结构
    print("\n📁 4. 测试文件结构...")
    required_files = [
        "SKILL.md",
        "QUICK_START.md",
        "config/default.yaml",
        "scripts/data_quality_checker.py"
    ]
    
    all_exists = True
    for file_path in required_files:
        full_path = Path(__file__).parent / file_path
        if full_path.exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} (缺失)")
            all_exists = False
    
    if all_exists:
        print("✅ 文件结构完整")
    else:
        print("❌ 文件结构不完整")
    
    print("\n" + "=" * 70)
    print("🎯 测试完成")
    print("=" * 70)
    
    return True

def main():
    """主测试函数"""
    try:
        success = test_basic_functionality()
        if success:
            print("\n🚀 数据质量Skill基础测试通过！")
            print("\n📋 下一步:")
            print("1. 安装依赖: pip install pandas numpy scipy yaml")
            print("2. 查看文档: 阅读 SKILL.md 和 QUICK_START.md")
            print("3. 运行示例: 创建 examples/ 目录中的示例")
            print("4. 集成使用: 参考集成示例")
        else:
            print("\n⚠️  测试失败，请检查问题。")
        
        return success
        
    except Exception as e:
        print(f"\n💥 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)