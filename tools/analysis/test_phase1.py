#!/usr/bin/env python3
"""
支撑阻力分析第一阶段功能测试脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.analysis.support_resistance_phase1 import SupportResistanceAnalyzerPhase1

def test_core_functions():
    """测试核心功能"""
    print("🧪 支撑阻力分析第一阶段核心功能测试")
    print("=" * 60)
    
    # 创建分析器
    analyzer = SupportResistanceAnalyzerPhase1(
        host='localhost',
        port=3306,
        user='root',
        password='',
        database='btc_assistant'
    )
    
    # 连接数据库
    if not analyzer.connect():
        print("❌ 数据库连接失败")
        return False
    
    try:
        symbol = 'BTCUSDT'
        
        print(f"\n1. 测试获取当前价格 ({symbol}):")
        current_price = analyzer.get_current_price(symbol)
        if current_price:
            print(f"   ✅ 当前价格: ${current_price:,.2f}")
        else:
            print("   ❌ 获取当前价格失败")
            return False
        
        print(f"\n2. 测试计算ATR (4H):")
        atr = analyzer.calculate_atr('4h', symbol)
        if atr > 0:
            print(f"   ✅ 4H ATR(14): ${atr:,.2f}")
        else:
            print("   ⚠️  ATR计算可能有问题")
        
        print(f"\n3. 测试识别技术位 (4H):")
        technical_levels = analyzer.identify_technical_levels('4h', symbol)
        print(f"   ✅ 识别到 {len(technical_levels['supports'])} 个技术支撑位")
        print(f"   ✅ 识别到 {len(technical_levels['resistances'])} 个技术阻力位")
        
        if technical_levels['supports']:
            support = technical_levels['supports'][0]
            print(f"     示例支撑位: ${support['price']:,.2f} ({support['subtype']})")
        
        print(f"\n4. 测试识别动态位 (4H):")
        dynamic_levels = analyzer.identify_dynamic_levels('4h', symbol)
        print(f"   ✅ 识别到 {len(dynamic_levels['supports'])} 个动态支撑位")
        print(f"   ✅ 识别到 {len(dynamic_levels['resistances'])} 个动态阻力位")
        
        if dynamic_levels['supports']:
            support = dynamic_levels['supports'][0]
            print(f"     示例动态位: ${support['price']:,.2f} ({support['subtype']})")
        
        print(f"\n5. 测试识别心理位:")
        psychological_levels = analyzer.identify_psychological_levels(current_price, symbol)
        print(f"   ✅ 识别到 {len(psychological_levels['supports'])} 个心理支撑位")
        print(f"   ✅ 识别到 {len(psychological_levels['resistances'])} 个心理阻力位")
        
        if psychological_levels['supports']:
            support = psychological_levels['supports'][0]
            print(f"     示例心理位: ${support['price']:,.2f}")
        
        print(f"\n6. 测试摆动点识别算法:")
        # 创建测试价格序列
        test_prices = [100, 105, 103, 108, 107, 110, 109, 112, 111, 115]
        swing_highs, swing_lows = analyzer.find_swing_points(test_prices, window=2, min_amplitude=0.01)
        print(f"   ✅ 识别到 {len(swing_highs)} 个摆动高点")
        print(f"   ✅ 识别到 {len(swing_lows)} 个摆动低点")
        
        print(f"\n7. 测试合并算法:")
        test_levels = [
            {'price': 100.0, 'type': 'technical', 'timeframe': '4h'},
            {'price': 101.0, 'type': 'dynamic', 'timeframe': '4h'},
            {'price': 105.0, 'type': 'psychological', 'timeframe': 'all'},
            {'price': 106.0, 'type': 'technical', 'timeframe': '4h'},
        ]
        merged = analyzer.merge_nearby_levels(test_levels, atr=5.0, atr_multiplier=1.0)
        print(f"   ✅ 将 {len(test_levels)} 个位点合并为 {len(merged)} 个区域")
        
        print(f"\n8. 测试评分计算:")
        test_level = {
            'price': 70000.0,
            'timeframes': ['1M', '1w', '4h'],
            'types': ['technical', 'dynamic', 'psychological'],
            'source_count': 3,
            'sources': [
                {'type': 'technical', 'subtype': 'swing_low'},
                {'type': 'dynamic', 'subtype': 'EMA50'},
                {'type': 'psychological', 'subtype': 'major'}
            ]
        }
        scored = analyzer.calculate_strength_score(test_level, 'support', current_price)
        print(f"   ✅ 综合评分: {scored.get('final_score', 0)}/15")
        print(f"   ✅ 强度等级: {scored.get('strength_level', 'N/A')}")
        
        print(f"\n9. 运行完整分析:")
        analysis_result = analyzer.multi_timeframe_analysis(symbol)
        print(f"   ✅ 分析完成!")
        print(f"   ✅ 找到 {len(analysis_result.get('supports', []))} 个强支撑位")
        print(f"   ✅ 找到 {len(analysis_result.get('resistances', []))} 个强阻力位")
        
        if analysis_result.get('supports'):
            print(f"\n   前3个强支撑位:")
            for i, support in enumerate(analysis_result['supports'][:3], 1):
                print(f"     {i}. ${support['price']:,.2f} - {support['strength_symbol']} "
                      f"(评分: {support['final_score']}/15)")
        
        print(f"\n🎉 所有核心功能测试通过!")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        analyzer.disconnect()

def quick_analysis():
    """快速分析"""
    print("🚀 快速支撑阻力分析")
    print("=" * 60)
    
    analyzer = SupportResistanceAnalyzerPhase1()
    result = analyzer.run_analysis(symbol='BTCUSDT')
    
    if 'error' in result:
        print(f"❌ 分析失败: {result['error']}")
    else:
        print("\n✅ 分析完成!")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='支撑阻力分析测试')
    parser.add_argument('--test', action='store_true', help='运行功能测试')
    parser.add_argument('--analyze', action='store_true', help='运行快速分析')
    
    args = parser.parse_args()
    
    if args.test:
        test_core_functions()
    elif args.analyze:
        quick_analysis()
    else:
        # 默认运行测试
        test_core_functions()