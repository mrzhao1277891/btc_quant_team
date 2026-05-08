#!/usr/bin/env python3
"""
调试回测系统 - 检查数据和指标
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.database import DatabaseConnector
from backend.indicators import IndicatorCalculator

def main():
    print("=" * 60)
    print("🔍 调试回测系统")
    print("=" * 60)
    print()
    
    # 1. 连接数据库
    print("1️⃣ 连接数据库...")
    try:
        db = DatabaseConnector()
        print("✅ 数据库连接成功")
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return
    
    # 2. 获取数据
    print("\n2️⃣ 获取最近30天的数据...")
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        klines_df = db.fetch_klines(
            symbol="BTCUSDT",
            timeframe="1d",
            start_date=start_date,
            end_date=end_date
        )
        
        print(f"✅ 获取到 {len(klines_df)} 条数据")
        print(f"   日期范围: {start_date.date()} 到 {end_date.date()}")
        print(f"   列名: {list(klines_df.columns)}")
        print()
        print("前3行数据:")
        print(klines_df.head(3))
    except Exception as e:
        print(f"❌ 获取数据失败: {e}")
        return
    
    # 3. 计算指标
    print("\n3️⃣ 计算技术指标...")
    try:
        calculator = IndicatorCalculator()
        klines_with_indicators = calculator.calculate_all_indicators(klines_df)
        
        print(f"✅ 指标计算完成")
        print(f"   新增列: {[col for col in klines_with_indicators.columns if col not in klines_df.columns]}")
        print()
        print("最后3行数据（包含指标）:")
        print(klines_with_indicators.tail(3))
    except Exception as e:
        print(f"❌ 指标计算失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 4. 检查指标值
    print("\n4️⃣ 检查指标值...")
    last_row = klines_with_indicators.iloc[-1]
    
    print(f"最新数据（{last_row.get('timestamp', 'N/A')}）:")
    print(f"  收盘价: {last_row.get('close', 'N/A')}")
    print(f"  EMA7: {last_row.get('EMA7', 'N/A')}")
    print(f"  EMA25: {last_row.get('EMA25', 'N/A')}")
    print(f"  EMA50: {last_row.get('EMA50', 'N/A')}")
    print(f"  RSI14: {last_row.get('RSI14', 'N/A')}")
    print(f"  RSI6: {last_row.get('RSI6', 'N/A')}")
    print(f"  MACD_DIF: {last_row.get('MACD_DIF', 'N/A')}")
    print(f"  MACD_DEA: {last_row.get('MACD_DEA', 'N/A')}")
    
    # 5. 检查 NaN 值
    print("\n5️⃣ 检查 NaN 值...")
    nan_counts = klines_with_indicators.isna().sum()
    print("每列的 NaN 数量:")
    for col, count in nan_counts.items():
        if count > 0:
            print(f"  {col}: {count} ({count/len(klines_with_indicators)*100:.1f}%)")
    
    # 6. 测试条件评估
    print("\n6️⃣ 测试 EMA 金叉条件...")
    ema7_gt_ema25 = klines_with_indicators['EMA7'] > klines_with_indicators['EMA25']
    rsi14_lt_70 = klines_with_indicators['RSI14'] < 70
    
    both_conditions = ema7_gt_ema25 & rsi14_lt_70
    
    print(f"  EMA7 > EMA25: {ema7_gt_ema25.sum()} 次")
    print(f"  RSI14 < 70: {rsi14_lt_70.sum()} 次")
    print(f"  两个条件都满足: {both_conditions.sum()} 次")
    
    if both_conditions.sum() > 0:
        print("\n  满足条件的日期:")
        matching_dates = klines_with_indicators[both_conditions]['timestamp']
        for date in matching_dates.head(5):
            print(f"    - {date}")
    
    print("\n" + "=" * 60)
    print("✅ 调试完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
