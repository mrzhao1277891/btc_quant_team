# 📊 分析工具库

## 📋 概述
专业的加密货币技术分析工具套件，包含技术分析、支撑阻力分析、模式识别和多时间框架分析四大模块。

## 🏗️ 架构设计
```
analysis/
├── technical.py          # 技术分析
├── support_resistance.py # 支撑阻力分析
├── patterns.py          # 模式识别
├── multi_timeframe.py   # 多时间框架分析
└── __init__.py          # 统一导出
```

## 🚀 快速使用

### 导入工具
```python
# 导入所有分析工具
from tools.analysis import (
    # 技术分析
    TechnicalAnalyzer, TechnicalAnalysisReport,
    
    # 支撑阻力分析
    SupportResistanceAnalyzer, SupportResistanceReport,
    
    # 模式识别
    PatternRecognizer, PatternAnalysisReport,
    
    # 多时间框架分析
    MultiTimeframeAnalyzer, MultiTimeframeReport
)

# 或按需导入
from tools.analysis.technical import TechnicalAnalyzer
from tools.analysis.support_resistance import SupportResistanceAnalyzer
from tools.analysis.patterns import PatternRecognizer
from tools.analysis.multi_timeframe import MultiTimeframeAnalyzer
```

### 基本示例
```python
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 创建示例数据
def create_sample_data():
    n = 200
    base_time = datetime(2024, 1, 1)
    
    data = {
        'timestamp': [base_time + timedelta(hours=i) for i in range(n)],
        'open': [70000 + i*10 + np.random.randn()*100 for i in range(n)],
        'high': [70100 + i*10 + np.random.randn()*100 for i in range(n)],
        'low': [69900 + i*10 + np.random.randn()*100 for i in range(n)],
        'close': [70050 + i*10 + np.random.randn()*100 for i in range(n)],
        'volume': [1000 + np.random.randn()*100 for _ in range(n)]
    }
    
    return pd.DataFrame(data)

df = create_sample_data()

# 1. 技术分析
technical_analyzer = TechnicalAnalyzer()
technical_report = technical_analyzer.analyze(df, "BTCUSDT", "4h")
technical_report.print_summary()

# 2. 支撑阻力分析
sr_analyzer = SupportResistanceAnalyzer()
sr_report = sr_analyzer.analyze(df, "BTCUSDT", "4h")
sr_report.print_summary()

# 3. 模式识别
pattern_recognizer = PatternRecognizer()
pattern_report = pattern_recognizer.analyze(df, "BTCUSDT", "4h")
pattern_report.print_summary()

# 4. 多时间框架分析 (需要多个时间框架数据)
# mtf_data = {"1d": df_daily, "4h": df_4h, "1h": df_1h}
# mtf_analyzer = MultiTimeframeAnalyzer()
# mtf_report = mtf_analyzer.analyze(mtf_data, "BTCUSDT")
# mtf_report.print_summary()
```

## 📈 工具分类

### 1. 技术分析工具 (technical.py)
**职责**: 综合技术分析，包括趋势、动量、波动率、成交量分析

#### 核心类:
| 类 | 功能 | 输入 | 输出 |
|----|------|------|------|
| `TechnicalAnalyzer` | 技术分析器 | DataFrame, symbol, timeframe | TechnicalAnalysisReport |
| `TechnicalAnalysisReport` | 技术分析报告 | - | 可序列化的报告对象 |
| `TrendAnalysis` | 趋势分析结果 | - | 趋势方向、强度、阶段 |
| `MomentumAnalysis` | 动量分析结果 | - | RSI、随机指标、CCI等 |
| `VolatilityAnalysis` | 波动率分析结果 | - | ATR、布林带、波动率状态 |
| `VolumeAnalysis` | 成交量分析结果 | - | 成交量趋势、OBV、量价确认 |
| `TechnicalSignal` | 技术信号 | - | 信号类型、置信度、原因 |

#### 分析维度:
- **趋势分析**: 识别趋势方向、强度、市场阶段
- **动量分析**: 分析价格变化的速度和强度
- **波动率分析**: 分析价格波动程度
- **成交量分析**: 分析交易活跃度和资金流向

#### 信号类型:
- 🟢 `STRONG_BUY`: 强烈买入信号
- 🟡 `BUY`: 买入信号
- ⚪ `NEUTRAL`: 中性信号
- 🟠 `SELL`: 卖出信号
- 🔴 `STRONG_SELL`: 强烈卖出信号

### 2. 支撑阻力分析工具 (support_resistance.py)
**职责**: 识别和分析支撑阻力位，包括技术位、心理位、动态位

#### 核心类:
| 类 | 功能 | 输入 | 输出 |
|----|------|------|------|
| `SupportResistanceAnalyzer` | 支撑阻力分析器 | DataFrame, symbol, timeframe | SupportResistanceReport |
| `SupportResistanceReport` | 支撑阻力分析报告 | - | 可序列化的报告对象 |
| `SupportResistanceLevel` | 支撑阻力位 | - | 位位价格、类型、强度、置信度 |
| `BreakoutAnalysis` | 突破分析 | - | 突破类型、价格、确认状态 |

#### 支撑阻力类型:
- **技术位**: 前期高低点、趋势线、形态颈线
- **心理位**: 整数关口、重要价格水平
- **动态位**: 移动平均线、布林带
- **斐波那契位**: 回调位、扩展位
- **枢纽点**: 日内交易枢纽点

#### 强度等级:
- ⚪ `WEAK`: 弱支撑阻力
- 🟡 `MODERATE`: 中等支撑阻力
- 🟠 `STRONG`: 强支撑阻力
- 🔴 `VERY_STRONG`: 非常强支撑阻力

### 3. 模式识别工具 (patterns.py)
**职责**: 识别技术分析模式，包括反转模式、持续模式、蜡烛图模式

#### 核心类:
| 类 | 功能 | 输入 | 输出 |
|----|------|------|------|
| `PatternRecognizer` | 模式识别器 | DataFrame, symbol, timeframe | PatternAnalysisReport |
| `PatternAnalysisReport` | 模式分析报告 | - | 可序列化的报告对象 |
| `Pattern` | 技术模式 | - | 模式类型、名称、方向、状态 |
| `CandlestickPattern` | 蜡烛图模式 | - | 模式名称、方向、置信度 |

#### 模式类型:
- **反转模式**: 头肩顶底、双顶底、三重顶底
- **持续模式**: 三角形、旗形、楔形、矩形
- **蜡烛图模式**: 单根、双根、三根蜡烛模式
- **图表模式**: 基于价格形态
- **谐波模式**: 基于斐波那契比例

#### 模式状态:
- 🔄 `FORMING`: 模式形成中
- ✅ `COMPLETE`: 模式已完成
- 🎯 `CONFIRMED`: 模式已确认
- ❌ `INVALID`: 模式已失效

### 4. 多时间框架分析工具 (multi_timeframe.py)
**职责**: 跨多个时间框架进行综合分析，识别趋势一致性、信号确认等

#### 核心类:
| 类 | 功能 | 输入 | 输出 |
|----|------|------|------|
| `MultiTimeframeAnalyzer` | 多时间框架分析器 | {timeframe: df}, symbol | MultiTimeframeReport |
| `MultiTimeframeReport` | 多时间框架分析报告 | - | 可序列化的报告对象 |
| `TimeframeAnalysis` | 时间框架分析 | - | 单个时间框架分析结果 |
| `TrendAlignment` | 趋势对齐分析 | - | 趋势对齐状态、分数 |
| `SignalConfirmation` | 信号确认分析 | - | 信号确认分数、时间框架 |
| `SupportResistanceConfluence` | 支撑阻力重合分析 | - | 重合价格、分数、时间框架 |

#### 时间框架层级:
- **宏观框架 (1M, 1w)**: 长期趋势，权重最高
- **中级框架 (1d, 4h)**: 中期趋势，权重中等
- **微观框架 (1h, 30m, 15m)**: 短期趋势，权重较低
- **交易框架 (5m, 1m)**: 入场时机，权重最低

#### 对齐状态:
- 🟢 `STRONG_ALIGNMENT`: 强对齐 (所有时间框架趋势一致)
- 🟡 `MODERATE_ALIGNMENT`: 中等对齐 (大部分时间框架趋势一致)
- ⚪ `NEUTRAL`: 中性 (趋势不一致也不冲突)
- 🟠 `MODERATE_CONFLICT`: 中等冲突 (趋势明显不一致)
- 🔴 `STRONG_CONFLICT`: 强冲突 (趋势完全相反)

## 🔧 使用指南

### 完整分析流水线
```python
def complete_analysis_pipeline(df, symbol="BTCUSDT", timeframe="4h"):
    """完整分析流水线"""
    
    print(f"🔍 开始分析: {symbol} ({timeframe})")
    print("=" * 60)
    
    # 1. 技术分析
    print("📊 执行技术分析...")
    technical_analyzer = TechnicalAnalyzer()
    technical_report = technical_analyzer.analyze(df, symbol, timeframe)
    
    # 2. 支撑阻力分析
    print("🎯 执行支撑阻力分析...")
    sr_analyzer = SupportResistanceAnalyzer()
    sr_report = sr_analyzer.analyze(df, symbol, timeframe)
    
    # 3. 模式识别
    print("🔄 执行模式识别...")
    pattern_recognizer = PatternRecognizer()
    pattern_report = pattern_recognizer.analyze(df, symbol, timeframe)
    
    # 4. 生成综合报告
    print("📋 生成综合报告...")
    
    current_price = df['close'].iloc[-1]
    timestamp = datetime.now().isoformat()
    
    # 提取关键信息
    trend = technical_report.trend_analysis
    momentum = technical_report.momentum_analysis
    nearest_support = sr_report.nearest_support
    nearest_resistance = sr_report.nearest_resistance
    active_patterns = pattern_report.active_patterns
    
    # 打印综合摘要
    print("\n" + "=" * 60)
    print(f"📈 综合分析摘要: {symbol} ({timeframe})")
    print("=" * 60)
    print(f"💰 当前价格: ${current_price:,.2f}")
    print(f"📅 分析时间: {timestamp}")
    print()
    
    print(f"📊 趋势分析:")
    print(f"  方向: {trend.direction.value}")
    print(f"  强度: {trend.strength:.1%}")
    print(f"  阶段: {trend.phase.value}")
    print()
    
    print(f"⚡ 动量分析:")
    print(f"  RSI: {momentum.rsi_value:.1f} ({momentum.rsi_signal})")
    print(f"  随机指标: K={momentum.stochastic_k:.1f}, D={momentum.stochastic_d:.1f}")
    print()
    
    if nearest_support:
        support_distance = (current_price - nearest_support.price) / current_price * 100
        print(f"📉 最近支撑: ${nearest_support.price:,.2f} ({support_distance:+.1f}%)")
    
    if nearest_resistance:
        resistance_distance = (nearest_resistance.price - current_price) / current_price * 100
        print(f"📈 最近阻力: ${nearest_resistance.price:,.2f} ({resistance_distance:+.1f}%)")
    print()
    
    if active_patterns:
        print(f"🔄 活跃模式: {len(active_patterns)} 个")
        for pattern in active_patterns[:2]:  # 显示前2个
            direction_emoji = "🟢" if pattern.direction == PatternDirection.BULLISH else "🔴"
            print(f"  {direction_emoji} {pattern.pattern_name} ({pattern.status.value})")
    print()
    
    # 生成交易建议
    print(f"💡 交易建议:")
    signals = technical_report.signals
    if signals:
        for signal in signals:
            if signal.confidence > 0.7:  # 高置信度信号
                emoji = {
                    "strong_buy": "🟢",
                    "buy": "🟡",
                    "sell": "🟠",
                    "strong_sell": "🔴"
                }.get(signal.signal_type.value, "⚪")
                
                print(f"  {emoji} {signal.signal_type.value.upper()} (置信度: {signal.confidence:.1%})")
                for reason in signal.reasons[:2]:
                    print(f"    • {reason}")
    else:
        print("  ⚪ 暂无明确交易信号")
    
    print("=" * 60)
    
    return {
        "technical_report": technical_report,
        "support_resistance_report": sr_report,
        "pattern_report": pattern_report,
        "summary": {
            "current_price": current_price,
            "trend_direction": trend.direction.value,
            "trend_strength": trend.strength,
            "rsi": momentum.rsi_value,
            "nearest_support": nearest_support.price if nearest_support else None,
            "nearest_resistance": nearest_resistance.price if nearest_resistance else None,
            "active_patterns": len(active_patterns)
        }
    }
```

### 多时间框架分析
```python
def multi_timeframe_analysis(symbol="BTCUSDT"):
    """多时间框架分析"""
    
    # 假设有多个时间框架数据
    mtf_data = {
        "1d": get_data_from_db(symbol, "1d", 200),
        "4h": get_data_from_db(symbol, "4h", 200),
        "1h": get_data_from_db(symbol, "1h", 200),
        "15m": get_data_from_db(symbol, "15m", 200)
    }
    
    # 执行多时间框架分析
    mtf_analyzer = MultiTimeframeAnalyzer()
    mtf_report = mtf_analyzer.analyze(mtf_data, symbol)
    
    # 打印报告
    mtf_report.print_summary()
    
    # 根据分析结果生成交易决策
    alignment = mtf_report.trend_alignment
    
    if alignment.status == AlignmentStatus.STRONG_ALIGNMENT:
        print("🎯 趋势强对齐，适合趋势跟踪策略")
        
        # 检查信号确认
        for signal in mtf_report.signal_confirmations:
            if signal.confirmation_score > 0.8:
                print(f"✅ 高确认信号: {signal.signal_type.value}")
                
    elif alignment.status == AlignmentStatus.STRONG_CONFLICT:
        print("⚠️  趋势强冲突，建议观望或采用区间交易策略")
        
    else:
        print("⚪ 趋势中性，需谨慎操作")
    
    return mtf_report
```

### 实时分析监控
```python
class RealTimeAnalyzer:
    """实时分析监控器"""
    
    def __init__(self, symbol="BTCUSDT"):
        self.symbol = symbol
        self.technical_analyzer = TechnicalAnalyzer()
        self.sr_analyzer = SupportResistanceAnalyzer()
        self.pattern_recognizer = PatternRecognizer()
        
        self.analysis_history = []
        self.signal_history = []
    
    def analyze_new_data(self, new_df):
        """分析新数据"""
        current_time = datetime.now()
        
        # 技术分析
        technical_report = self.technical_analyzer.analyze(new_df, self.symbol, "5m")
        
        # 支撑阻力分析
        sr_report = self.sr_analyzer.analyze(new_df, self.symbol, "5m")
        
        # 模式识别
        pattern_report = self.pattern_recognizer.analyze(new_df, self.symbol, "5m")
        
        # 记录分析结果
        analysis_result = {
            "timestamp": current_time.isoformat(),
            "price": new_df['close'].iloc[-1],
            "technical_signals": [s.signal_type.value for s in technical_report.signals],
            "nearest_support": sr_report.nearest_support.price if sr_report.nearest_support else None,
            "nearest_resistance": sr_report.nearest_resistance.price if sr_report.nearest_resistance else None,
            "active_patterns": len(pattern_report.active_patterns)
        }
        
        self.analysis_history.append(analysis_result)
        
        # 检查新信号
        new_signals = []
        for signal in technical_report.signals:
            if signal.confidence > 0.7:  # 高置信度信号
                new_signals.append({
                    "timestamp": current_time.isoformat(),
                    "signal_type": signal.signal_type.value,
                    "confidence": signal.confidence,
                    "price": new_df['close'].iloc[-1],
                    "reasons": signal.reasons
                })
        
        if new_signals:
            self.signal_history.extend(new_signals)
            self._handle_new_signals(new_signals)
        
        return {
            "technical_report": technical_report,
            "support_resistance_report": sr_report,
            "pattern_report": pattern_report,
            "new_signals": new_signals
        }
    
    def _handle_new_signals(self, new_signals):
        """处理新信号"""
        for signal in new_signals:
            print(f"🚨 新信号: {signal['signal_type']} @