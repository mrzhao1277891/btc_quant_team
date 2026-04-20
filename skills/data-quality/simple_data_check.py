#!/usr/bin/env python3
"""
简化版数据质量检查
直接使用数据质量专家Skill的核心功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sqlite3
import json

class SimpleDataQualityChecker:
    """简化版数据质量检查器"""
    
    def __init__(self, db_path=None):
        self.db_path = db_path or "/home/francis/.openclaw/workspace/crypto_analyzer/data/ultra_light.db"
        self.results = {}
    
    def load_data(self, symbol="BTCUSDT", timeframe="1d", limit=1000):
        """从数据库加载数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            query = f"""
            SELECT * FROM klines 
            WHERE symbol = ? AND timeframe = ?
            ORDER BY timestamp DESC 
            LIMIT ?
            """
            df = pd.read_sql_query(query, conn, params=(symbol, timeframe, limit))
            conn.close()
            
            # 转换时间戳
            if 'timestamp' in df.columns:
                df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('datetime', inplace=True)
            
            return df
        except Exception as e:
            print(f"❌ 加载数据失败: {e}")
            return None
    
    def check_completeness(self, df):
        """检查完整性"""
        if df is None or df.empty:
            return {"score": 0, "status": "FAIL", "issues": ["数据为空"]}
        
        # 检查缺失值
        key_columns = ['open', 'high', 'low', 'close', 'volume']
        missing_counts = {}
        
        for col in key_columns:
            if col in df.columns:
                missing = df[col].isnull().sum()
                if missing > 0:
                    missing_counts[col] = missing
        
        total_cells = sum(len(df) for col in key_columns if col in df.columns)
        missing_cells = sum(missing_counts.values())
        
        completeness = 1 - (missing_cells / total_cells) if total_cells > 0 else 0
        
        issues = []
        if missing_counts:
            for col, count in missing_counts.items():
                issues.append(f"{col}列有{count}个缺失值")
        
        status = "PASS" if completeness >= 0.95 else "WARNING" if completeness >= 0.80 else "FAIL"
        
        return {
            "score": completeness,
            "status": status,
            "issues": issues,
            "metrics": {
                "total_cells": total_cells,
                "missing_cells": missing_cells,
                "missing_columns": list(missing_counts.keys())
            }
        }
    
    def check_consistency(self, df):
        """检查一致性"""
        if df is None or df.empty:
            return {"score": 0, "status": "FAIL", "issues": ["数据为空"]}
        
        issues = []
        error_count = 0
        
        # 检查价格逻辑
        if all(col in df.columns for col in ['high', 'low', 'close']):
            for idx, row in df.iterrows():
                if row['high'] < row['low']:
                    issues.append(f"行{idx}: high({row['high']}) < low({row['low']})")
                    error_count += 1
                elif row['close'] < row['low']:
                    issues.append(f"行{idx}: close({row['close']}) < low({row['low']})")
                    error_count += 1
                elif row['close'] > row['high']:
                    issues.append(f"行{idx}: close({row['close']}) > high({row['high']})")
                    error_count += 1
        
        # 检查负值
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in df.columns:
                negative = df[df[col] <= 0]
                if len(negative) > 0:
                    issues.append(f"{col}列有{len(negative)}个非正值")
                    error_count += len(negative)
        
        total_checks = len(df) * 3  # 每个数据点检查3个逻辑
        consistency = 1 - (error_count / total_checks) if total_checks > 0 else 0
        
        status = "PASS" if consistency >= 0.98 else "WARNING" if consistency >= 0.90 else "FAIL"
        
        return {
            "score": consistency,
            "status": status,
            "issues": issues[:5],  # 只显示前5个问题
            "metrics": {
                "total_checks": total_checks,
                "errors": error_count
            }
        }
    
    def check_freshness(self, df, timeframe="1d"):
        """检查数据新鲜度"""
        if df is None or df.empty or 'timestamp' not in df.columns:
            return {"score": 0, "status": "FAIL", "issues": ["无法检查新鲜度"]}
        
        # 获取最新数据时间
        latest_timestamp = df['timestamp'].max()
        latest_time = datetime.fromtimestamp(latest_timestamp / 1000)
        now = datetime.now()
        
        age_hours = (now - latest_time).total_seconds() / 3600
        
        # 设置阈值
        thresholds = {
            '1h': 2,    # 2小时
            '4h': 6,    # 6小时
            '1d': 24,   # 24小时
            '1w': 168,  # 7天
            '1M': 720   # 30天
        }
        
        threshold = thresholds.get(timeframe, 24)
        
        if age_hours <= threshold:
            score = 1.0
            status = "PASS"
        elif age_hours <= threshold * 2:
            score = 0.7
            status = "WARNING"
        else:
            score = 0.3
            status = "FAIL"
        
        issues = []
        if status != "PASS":
            issues.append(f"数据已{age_hours:.1f}小时未更新（阈值:{threshold}小时）")
        
        return {
            "score": score,
            "status": status,
            "issues": issues,
            "metrics": {
                "latest_time": latest_time.isoformat(),
                "age_hours": age_hours,
                "threshold_hours": threshold
            }
        }
    
    def check_indicators(self, df):
        """检查技术指标"""
        if df is None or df.empty:
            return {"score": 0, "status": "FAIL", "issues": ["数据为空"]}
        
        indicator_columns = ['ema7', 'ema12', 'ema25', 'ema50', 'rsi14', 'macd']
        available_indicators = []
        missing_indicators = []
        
        for col in indicator_columns:
            if col in df.columns:
                not_null = df[col].notnull().sum()
                if not_null > 0:
                    available_indicators.append(col)
                else:
                    missing_indicators.append(f"{col}（全部为空）")
            else:
                missing_indicators.append(f"{col}（列不存在）")
        
        total_indicators = len(indicator_columns)
        available_count = len(available_indicators)
        score = available_count / total_indicators if total_indicators > 0 else 0
        
        issues = []
        if missing_indicators:
            issues.extend(missing_indicators)
        
        status = "PASS" if score >= 0.8 else "WARNING" if score >= 0.5 else "FAIL"
        
        return {
            "score": score,
            "status": status,
            "issues": issues,
            "metrics": {
                "total_indicators": total_indicators,
                "available_indicators": available_count,
                "available_list": available_indicators
            }
        }
    
    def comprehensive_check(self, symbol="BTCUSDT", timeframe="1d", limit=500):
        """执行全面检查"""
        print(f"🔍 开始数据质量检查: {symbol} ({timeframe})")
        print("=" * 60)
        
        # 加载数据
        df = self.load_data(symbol, timeframe, limit)
        
        if df is None:
            print("❌ 无法加载数据")
            return
        
        print(f"📊 数据加载成功: {len(df)} 行")
        print(f"   时间范围: {df.index.min()} 到 {df.index.max()}")
        
        # 执行各项检查
        checks = {
            "完整性": self.check_completeness(df),
            "一致性": self.check_consistency(df),
            "新鲜度": self.check_freshness(df, timeframe),
            "技术指标": self.check_indicators(df)
        }
        
        # 显示结果
        overall_score = 0
        check_count = 0
        
        print("\n📋 检查结果:")
        print("-" * 60)
        
        for check_name, result in checks.items():
            score = result["score"]
            status = result["status"]
            
            # 状态图标
            if status == "PASS":
                icon = "✅"
            elif status == "WARNING":
                icon = "⚠️ "
            else:
                icon = "❌"
            
            print(f"{icon} {check_name}: {score:.1%} [{status}]")
            
            # 显示问题
            if result.get("issues"):
                for issue in result["issues"][:2]:  # 只显示前2个问题
                    print(f"   • {issue}")
                if len(result["issues"]) > 2:
                    print(f"   ... 还有{len(result['issues']) - 2}个问题")
            
            overall_score += score
            check_count += 1
        
        # 计算总体评分
        if check_count > 0:
            overall_score = overall_score / check_count
        
        print("-" * 60)
        
        # 总体评价
        if overall_score >= 0.9:
            rating = "优秀 🎯"
            color = "🟢"
        elif overall_score >= 0.8:
            rating = "良好 👍"
            color = "🟡"
        elif overall_score >= 0.6:
            rating = "一般 ⚠️"
            color = "🟠"
        else:
            rating = "需要改进 ❌"
            color = "🔴"
        
        print(f"{color} 总体评分: {overall_score:.1%} ({rating})")
        
        # 建议
        print("\n💡 建议:")
        
        if checks["完整性"]["score"] < 0.95:
            print("  • 修复缺失的数据点")
        
        if checks["一致性"]["score"] < 0.98:
            print("  • 检查数据一致性")
        
        if checks["新鲜度"]["score"] < 0.8:
            latest_time = checks["新鲜度"]["metrics"]["latest_time"]
            age = checks["新鲜度"]["metrics"]["age_hours"]
            print(f"  • 更新数据（最新: {latest_time}, 已{age:.1f}小时）")
        
        if checks["技术指标"]["score"] < 0.8:
            print("  • 重新计算技术指标")
        
        print("=" * 60)
        
        # 保存结果
        self.results = {
            "symbol": symbol,
            "timeframe": timeframe,
            "timestamp": datetime.now().isoformat(),
            "overall_score": overall_score,
            "checks": checks,
            "data_info": {
                "rows": len(df),
                "time_range": {
                    "start": df.index.min().isoformat(),
                    "end": df.index.max().isoformat()
                }
            }
        }
        
        return self.results
    
    def save_report(self, filename="data_quality_report.json"):
        """保存报告"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        print(f"📄 报告已保存到: {filename}")

def main():
    """主函数"""
    print("🧪 数据质量专家Skill - 简化版检查")
    print("=" * 60)
    
    # 创建检查器
    checker = SimpleDataQualityChecker()
    
    # 检查各时间框架
    timeframes = ['4h', '1d', '1w', '1M']
    
    all_results = {}
    
    for tf in timeframes:
        print(f"\n📊 检查 {tf} 时间框架:")
        print("-" * 40)
        
        try:
            result = checker.comprehensive_check("BTCUSDT", tf, limit=500)
            if result:
                all_results[tf] = result
        except Exception as e:
            print(f"❌ 检查失败: {e}")
    
    # 生成总结报告
    if all_results:
        print("\n" + "=" * 60)
        print("📋 数据质量总结报告")
        print("=" * 60)
        
        for tf, result in all_results.items():
            score = result["overall_score"]
            if score >= 0.9:
                icon = "✅"
            elif score >= 0.8:
                icon = "⚠️ "
            else:
                icon = "❌"
            
            print(f"{icon} {tf}: {score:.1%}")
        
        # 保存报告
        checker.save_report("data_quality_summary.json")
    
    print("\n✅ 检查完成")

if __name__ == "__main__":
    main()