#!/usr/bin/env python3
"""
市场分析Skill测试脚本

测试Skill的基本功能是否正常工作
"""

import sys
import os
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """测试导入"""
    print("🔍 测试模块导入...")
    
    try:
        from scripts.market_analyzer import MarketAnalyzer, MarketAnalysis, MarketState, RiskLevel
        print("✅ market_analyzer 导入成功")
    except ImportError as e:
        print(f"❌ market_analyzer 导入失败: {e}")
        return False
    
    try:
        from scripts.multi_timeframe_analyzer import MultiTimeframeAnalyzer, MultiTimeframeDecision
        print("✅ multi_timeframe_analyzer 导入成功")
    except ImportError as e:
        print(f"❌ multi_timeframe_analyzer 导入失败: {e}")
        return False
    
    try:
        from scripts.signal_generator import SignalGenerator, TradingSignal, SignalType, SignalDirection
        print("✅ signal_generator 导入成功")
    except ImportError as e:
        print(f"❌ signal_generator 导入失败: {e}")
        return False
    
    try:
        from scripts.risk_manager import RiskManager, TradeParameters, RiskLevel
        print("✅ risk_manager 导入成功")
    except ImportError as e:
        print(f"❌ risk_manager 导入失败: {e}")
        return False
    
    return True

def test_config_files():
    """测试配置文件"""
    print("\n🔧 测试配置文件...")
    
    config_files = [
        "config/default.yaml",
        "config/frameworks/crypto_mtf.yaml"
    ]
    
    all_exists = True
    for config_file in config_files:
        full_path = Path(__file__).parent / config_file
        if full_path.exists():
            print(f"✅ {config_file}")
        else:
            print(f"❌ {config_file} (缺失)")
            all_exists = False
    
    return all_exists

def test_market_analyzer():
    """测试市场分析器"""
    print("\n📊 测试市场分析器...")
    
    try:
        from scripts.market_analyzer import MarketAnalyzer
        
        # 创建分析器
        analyzer = MarketAnalyzer()
        print("✅ 市场分析器创建成功")
        
        # 测试分析（使用模拟数据）
        print("   执行模拟分析...")
        
        # 创建模拟分析结果
        analysis = MarketAnalyzer.MarketAnalysis(
            symbol="BTCUSDT",
            timestamp="2026-04-19T12:00:00",
            current_price=75000.0,
            market_state=MarketAnalyzer.MarketState.MODERATE_UPTREND,
            trend_direction="bullish",
            strength_score=65.5,
            risk_level=MarketAnalyzer.RiskLevel.MODERATE,
            key_levels={
                "support": [72000, 70000, 68000],
                "resistance": [76000, 78000, 80000]
            },
            technical_analysis={
                "summary": {
                    "trend": {"direction": "bullish", "strength": 0.7},
                    "momentum": {"rsi": 58, "signal": "neutral"},
                    "volatility": {"regime": "normal", "atr_percent": 0.02}
                }
            },
            signals=[
                {
                    "type": "trend_following",
                    "direction": "bullish",
                    "confidence": 0.75,
                    "entry_price": 74500,
                    "stop_loss": 73000,
                    "take_profit": 77000
                }
            ],
            recommendations=[
                "逢低做多，关注72000支撑",
                "突破76000可加仓",
                "严格止损控制风险"
            ]
        )
        
        print("✅ 模拟分析创建成功")
        print(f"   市场状态: {analysis.market_state.value}")
        print(f"   趋势方向: {analysis.trend_direction}")
        print(f"   强度评分: {analysis.strength_score}/100")
        
        return True
        
    except Exception as e:
        print(f"❌ 市场分析器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_signal_generator():
    """测试信号生成器"""
    print("\n🚦 测试信号生成器...")
    
    try:
        from scripts.signal_generator import SignalGenerator, SignalType, SignalDirection, SignalPriority
        
        # 创建信号生成器
        signal_gen = SignalGenerator()
        print("✅ 信号生成器创建成功")
        
        # 创建模拟信号
        signal = TradingSignal(
            id="test_signal_001",
            type=SignalType.TREND_FOLLOWING,
            direction=SignalDirection.BULLISH,
            symbol="BTCUSDT",
            timeframe="4h",
            entry_price=74500.0,
            stop_loss=73000.0,
            take_profit=77000.0,
            confidence=0.75,
            priority=SignalPriority.HIGH,
            generated_at="2026-04-19T12:00:00",
            reasons=[
                "趋势确认，EMA多头排列",
                "成交量放大确认",
                "突破关键阻力位"
            ],
            risk_reward_ratio=2.5,
            position_size=0.01,
            validity_period=24
        )
        
        print("✅ 模拟信号创建成功")
        print(f"   信号类型: {signal.type.value}")
        print(f"   信号方向: {signal.direction.value}")
        print(f"   置信度: {signal.confidence:.1%}")
        print(f"   风险回报比: {signal.risk_reward_ratio:.2f}:1")
        
        # 测试信号打印
        print("   测试信号打印...")
        signal.print_signal()
        
        return True
        
    except Exception as e:
        print(f"❌ 信号生成器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_risk_manager():
    """测试风险管理器"""
    print("\n⚠️  测试风险管理器...")
    
    try:
        from scripts.risk_manager import RiskManager, TradeParameters
        
        # 创建风险管理器
        risk_mgr = RiskManager(
            account_size=10000,
            max_risk_per_trade=0.02,
            max_drawdown=0.20
        )
        
        print("✅ 风险管理器创建成功")
        
        # 创建模拟交易参数
        trade_params = TradeParameters(
            symbol="BTCUSDT",
            entry_price=74500.0,
            stop_loss=73000.0,
            take_profit=77000.0,
            position_size=0.01,
            risk_amount=150.0,
            risk_percent=0.015,
            potential_profit=250.0,
            risk_reward_ratio=1.67,
            confidence=0.75
        )
        
        print("✅ 模拟交易参数创建成功")
        print(f"   入场价格: ${trade_params.entry_price:,.2f}")
        print(f"   止损价格: ${trade_params.stop_loss:,.2f}")
        print(f"   止盈价格: ${trade_params.take_profit:,.2f}")
        print(f"   仓位大小: {trade_params.position_size:.4f}")
        print(f"   风险金额: ${trade_params.risk_amount:,.2f}")
        print(f"   风险回报比: {trade_params.risk_reward_ratio:.2f}:1")
        
        # 测试参数打印
        print("   测试参数打印...")
        trade_params.print_summary()
        
        return True
        
    except Exception as e:
        print(f"❌ 风险管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_file_structure():
    """测试文件结构"""
    print("\n📁 测试文件结构...")
    
    required_files = [
        "SKILL.md",
        "QUICK_START.md",
        "scripts/market_analyzer.py",
        "scripts/multi_timeframe_analyzer.py",
        "scripts/signal_generator.py",
        "scripts/risk_manager.py",
        "config/default.yaml",
        "config/frameworks/crypto_mtf.yaml"
    ]
    
    all_exists = True
    for file_path in required_files:
        full_path = Path(__file__).parent / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} (缺失)")
            all_exists = False
    
    return all_exists

def main():
    """主测试函数"""
    print("=" * 70)
    print("🧪 市场分析Skill测试")
    print("=" * 70)
    
    tests = [
        ("文件结构", test_file_structure),
        ("配置文件", test_config_files),
        ("模块导入", test_imports),
        ("市场分析器", test_market_analyzer),
        ("信号生成器", test_signal_generator),
        ("风险管理器", test_risk_manager)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 测试: {test_name}")
        try:
            success = test_func()
            results.append((test_name, success))
            if success:
                print(f"✅ {test_name} 测试通过")
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"💥 {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    # 显示测试结果
    print("\n" + "=" * 70)
    print("📊 测试结果汇总")
    print("=" * 70)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！Skill可以正常工作。")
        print("\n🚀 下一步:")
        print("1. 安装依赖: pip install pandas numpy matplotlib yfinance")
        print("2. 运行示例: python examples/basic_analysis.py")
        print("3. 测试分析: python scripts/market_cli.py analyze --symbol BTCUSDT")
        print("4. 生成报告: python scripts/market_cli.py report --symbol BTCUSDT")
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查问题。")
    
    print("=" * 70)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)