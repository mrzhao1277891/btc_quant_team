#!/usr/bin/env python3
"""
交易信号Skill测试脚本
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
    print("🧪 交易信号Skill基础测试")
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
    
    print(f"✅ 模拟数据创建完成")
    print(f"   数据点数: {len(data)}")
    print(f"   价格范围: ${data['close'].min():,.0f} - ${data['close'].max():,.0f}")
    
    # 2. 测试基础信号生成
    print("\n🚦 2. 测试基础信号生成...")
    
    class BasicSignalGenerator:
        def __init__(self):
            self.signals = []
        
        def generate_ma_crossover(self, data, short_window=10, long_window=30):
            """生成均线交叉信号"""
            signals = []
            
            # 计算移动平均线
            data['MA_short'] = data['close'].rolling(window=short_window).mean()
            data['MA_long'] = data['close'].rolling(window=long_window).mean()
            
            # 生成交叉信号
            for i in range(1, len(data)):
                prev_short = data['MA_short'].iloc[i-1]
                prev_long = data['MA_long'].iloc[i-1]
                curr_short = data['MA_short'].iloc[i]
                curr_long = data['MA_long'].iloc[i]
                
                # 金叉信号（短期均线上穿长期均线）
                if prev_short <= prev_long and curr_short > curr_long:
                    signal = {
                        'timestamp': data['timestamp'].iloc[i],
                        'type': 'MA_CROSSOVER',
                        'direction': 'BUY',
                        'price': data['close'].iloc[i],
                        'confidence': 0.7,
                        'description': f'MA{short_window}上穿MA{long_window}'
                    }
                    signals.append(signal)
                
                # 死叉信号（短期均线下穿长期均线）
                elif prev_short >= prev_long and curr_short < curr_long:
                    signal = {
                        'timestamp': data['timestamp'].iloc[i],
                        'type': 'MA_CROSSOVER',
                        'direction': 'SELL',
                        'price': data['close'].iloc[i],
                        'confidence': 0.7,
                        'description': f'MA{short_window}下穿MA{long_window}'
                    }
                    signals.append(signal)
            
            return signals
        
        def generate_rsi_signals(self, data, period=14, overbought=70, oversold=30):
            """生成RSI超买超卖信号"""
            signals = []
            
            # 计算RSI
            delta = data['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            data['RSI'] = 100 - (100 / (1 + rs))
            
            # 生成信号
            for i in range(period, len(data)):
                rsi = data['RSI'].iloc[i]
                
                # 超卖信号（RSI < 30）
                if rsi < oversold:
                    signal = {
                        'timestamp': data['timestamp'].iloc[i],
                        'type': 'RSI_OVERSOLD',
                        'direction': 'BUY',
                        'price': data['close'].iloc[i],
                        'confidence': 0.65,
                        'description': f'RSI超卖 ({rsi:.1f})'
                    }
                    signals.append(signal)
                
                # 超买信号（RSI > 70）
                elif rsi > overbought:
                    signal = {
                        'timestamp': data['timestamp'].iloc[i],
                        'type': 'RSI_OVERBOUGHT',
                        'direction': 'SELL',
                        'price': data['close'].iloc[i],
                        'confidence': 0.65,
                        'description': f'RSI超买 ({rsi:.1f})'
                    }
                    signals.append(signal)
            
            return signals
        
        def generate_all_signals(self, data):
            """生成所有信号"""
            ma_signals = self.generate_ma_crossover(data)
            rsi_signals = self.generate_rsi_signals(data)
            
            all_signals = ma_signals + rsi_signals
            all_signals.sort(key=lambda x: x['timestamp'])
            
            return all_signals
        
        def print_signals(self, signals, limit=5):
            """打印信号"""
            print("=" * 60)
            print(f"🚦 交易信号 ({len(signals)} 个)")
            print("=" * 60)
            
            for i, signal in enumerate(signals[:limit]):
                direction_emoji = "🟢" if signal['direction'] == 'BUY' else "🔴"
                print(f"{direction_emoji} 信号 {i+1}:")
                print(f"  时间: {signal['timestamp'].date()}")
                print(f"  类型: {signal['type']}")
                print(f"  方向: {signal['direction']}")
                print(f"  价格: ${signal['price']:,.0f}")
                print(f"  置信度: {signal['confidence']:.0%}")
                print(f"  描述: {signal['description']}")
                print()
            
            if len(signals) > limit:
                print(f"... 还有 {len(signals) - limit} 个信号")
    
    # 执行信号生成
    generator = BasicSignalGenerator()
    signals = generator.generate_all_signals(data)
    generator.print_signals(signals, limit=3)
    
    # 3. 测试信号分析
    print("\n📊 3. 测试信号分析...")
    
    class BasicSignalAnalyzer:
        def analyze_signals(self, signals):
            """分析信号"""
            if not signals:
                return {}
            
            analysis = {
                'total': len(signals),
                'buy': sum(1 for s in signals if s['direction'] == 'BUY'),
                'sell': sum(1 for s in signals if s['direction'] == 'SELL'),
                'types': {},
                'confidence_stats': {
                    'min': min(s['confidence'] for s in signals),
                    'max': max(s['confidence'] for s in signals),
                    'avg': sum(s['confidence'] for s in signals) / len(signals)
                }
            }
            
            # 统计信号类型
            for signal in signals:
                sig_type = signal['type']
                analysis['types'][sig_type] = analysis['types'].get(sig_type, 0) + 1
            
            return analysis
        
        def print_analysis(self, analysis):
            """打印分析结果"""
            print("=" * 60)
            print("📈 信号分析结果")
            print("=" * 60)
            
            print(f"总信号数: {analysis['total']}")
            print(f"买入信号: {analysis['buy']}")
            print(f"卖出信号: {analysis['sell']}")
            
            print(f"\n📊 置信度统计:")
            print(f"  最低: {analysis['confidence_stats']['min']:.1%}")
            print(f"  最高: {analysis['confidence_stats']['max']:.1%}")
            print(f"  平均: {analysis['confidence_stats']['avg']:.1%}")
            
            print(f"\n🔧 信号类型分布:")
            for sig_type, count in analysis['types'].items():
                percentage = count / analysis['total'] * 100
                print(f"  {sig_type}: {count} 个 ({percentage:.1f}%)")
            
            print("=" * 60)
    
    # 执行信号分析
    analyzer = BasicSignalAnalyzer()
    analysis = analyzer.analyze_signals(signals)
    analyzer.print_analysis(analysis)
    
    # 4. 测试配置文件
    print("\n🔧 4. 测试配置文件...")
    config_path = Path(__file__).parent / "config/default.yaml"
    
    if config_path.exists():
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if config and 'signal_generation' in config:
                print(f"✅ 配置文件加载成功")
                sg_config = config['signal_generation']
                print(f"   最小置信度: {sg_config.get('min_confidence', 'N/A')}")
                print(f"   最小风险回报比: {sg_config.get('min_risk_reward', 'N/A')}")
                print(f"   启用信号类型: {', '.join(sg_config.get('enabled_types', []))}")
            else:
                print("❌ 配置文件格式错误")
        except Exception as e:
            print(f"❌ 配置文件加载失败: {e}")
    else:
        print("❌ 配置文件不存在")
    
    # 5. 测试数据结构
    print("\n📁 5. 测试文件结构...")
    required_files = [
        "SKILL.md",
        "QUICK_START.md",
        "config/default.yaml",
        "scripts/signal_generator.py"
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
            print("\n🚀 交易信号Skill基础测试通过！")
            print("\n📋 下一步:")
            print("1. 安装依赖: pip install pandas numpy ta-lib yaml")
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