# 🚀 交易信号专家 - 快速开始指南

## 📋 概述
交易信号专家是一个专业的加密货币交易信号生成和分析系统。本指南将帮助你在5分钟内开始生成、分析和测试交易信号。

## 🎯 核心功能概览

### 📊 信号生成
- **技术信号**: 基于技术指标的买卖信号
- **模式信号**: 图表模式和蜡烛图模式
- **多时间框架信号**: 金字塔式决策信号
- **情绪信号**: 市场情绪反转信号

### 🔍 信号分析
- **强度分析**: 信号置信度和强度评分
- **风险分析**: 止损止盈和风险回报计算
- **验证分析**: 多指标多时间框架验证
- **过滤系统**: 基于规则的信号过滤

### 📈 回溯测试
- **历史回测**: 基于历史数据的信号测试
- **绩效评估**: 全面的绩效指标计算
- **参数优化**: 自动参数优化和扫描
- **策略比较**: 多策略绩效比较

### 🚨 实时监控
- **实时信号**: 基于实时数据的信号生成
- **信号告警**: 重要信号实时告警
- **绩效跟踪**: 信号执行结果跟踪
- **自适应调整**: 市场环境自适应

## 🚀 5分钟快速开始

### 步骤1: 准备环境
```bash
# 1. 进入技能目录
cd /home/francis/btc_quant_team/skills/trading-signal

# 2. 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate

# 3. 安装基础依赖
pip3 install pandas numpy matplotlib ta-lib
```

### 步骤2: 基础配置
```bash
# 1. 创建配置文件目录
mkdir -p config/signals config/filters config/backtest

# 2. 创建基础配置文件
cat > config/default.yaml << 'EOF'
data_sources:
  historical:
    type: "sqlite"
    path: "crypto_analyzer/data/ultra_light.db"
    table: "klines"

signal_generation:
  enabled_types: ["technical", "pattern"]
  timeframes: ["1d", "4h"]
  min_confidence: 0.6
  min_risk_reward: 1.5

backtesting:
  enabled: true
  initial_capital: 10000
  commission: 0.001

monitoring:
  check_interval_seconds: 300
EOF
```

### 步骤3: 运行第一个信号生成
```python
# 创建测试脚本 test_basic_signal.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 创建模拟价格数据
dates = pd.date_range(start='2024-01-01', end='2024-04-19', freq='D')
prices = pd.DataFrame({
    'timestamp': dates,
    'open': np.random.normal(70000, 5000, len(dates)),
    'high': np.random.normal(71000, 5000, len(dates)),
    'low': np.random.normal(69000, 5000, len(dates)),
    'close': np.random.normal(70500, 5000, len(dates)),
    'volume': np.random.normal(1000, 200, len(dates))
})

print("📊 模拟数据创建完成")
print(f"数据点数: {len(prices)}")
print(f"价格范围: ${prices['close'].min():,.0f} - ${prices['close'].max():,.0f}")

# 基础信号生成器
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
    
    def print_signals(self, signals, limit=10):
        """打印信号"""
        print("=" * 70)
        print(f"🚦 交易信号 ({len(signals)} 个)")
        print("=" * 70)
        
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

# 使用示例
generator = BasicSignalGenerator()
signals = generator.generate_all_signals(prices)
generator.print_signals(signals, limit=5)
```

### 步骤4: 基础信号分析
```python
# 创建信号分析器 basic_analyzer.py
class BasicSignalAnalyzer:
    def __init__(self):
        self.analysis_results = {}
    
    def analyze_signals(self, signals, prices):
        """分析信号"""
        results = {
            'total_signals': len(signals),
            'buy_signals': 0,
            'sell_signals': 0,
            'signal_types': {},
            'confidence_stats': {'min': 1.0, 'max': 0.0, 'avg': 0.0},
            'monthly_distribution': {}
        }
        
        if not signals:
            return results
        
        # 统计信号
        confidences = []
        for signal in signals:
            # 统计买卖信号
            if signal['direction'] == 'BUY':
                results['buy_signals'] += 1
            else:
                results['sell_signals'] += 1
            
            # 统计信号类型
            signal_type = signal['type']
            results['signal_types'][signal_type] = results['signal_types'].get(signal_type, 0) + 1
            
            # 统计置信度
            confidence = signal['confidence']
            confidences.append(confidence)
            results['confidence_stats']['min'] = min(results['confidence_stats']['min'], confidence)
            results['confidence_stats']['max'] = max(results['confidence_stats']['max'], confidence)
            
            # 统计月度分布
            month = signal['timestamp'].strftime('%Y-%m')
            results['monthly_distribution'][month] = results['monthly_distribution'].get(month, 0) + 1
        
        # 计算平均置信度
        if confidences:
            results['confidence_stats']['avg'] = sum(confidences) / len(confidences)
        
        return results
    
    def print_analysis(self, analysis):
        """打印分析结果"""
        print("=" * 70)
        print("📊 信号分析结果")
        print("=" * 70)
        
        print(f"总信号数: {analysis['total_signals']}")
        print(f"买入信号: {analysis['buy_signals']}")
        print(f"卖出信号: {analysis['sell_signals']}")
        
        print(f"\n📈 置信度统计:")
        print(f"  最低: {analysis['confidence_stats']['min']:.1%}")
        print(f"  最高: {analysis['confidence_stats']['max']:.1%}")
        print(f"  平均: {analysis['confidence_stats']['avg']:.1%}")
        
        print(f"\n🔧 信号类型分布:")
        for signal_type, count in analysis['signal_types'].items():
            percentage = count / analysis['total_signals'] * 100
            print(f"  {signal_type}: {count} 个 ({percentage:.1f}%)")
        
        print(f"\n📅 月度分布:")
        for month, count in list(analysis['monthly_distribution'].items())[:6]:
            print(f"  {month}: {count} 个")
        
        print("=" * 70)

# 使用示例
analyzer = BasicSignalAnalyzer()
analysis = analyzer.analyze_signals(signals, prices)
analyzer.print_analysis(analysis)
```

## 📖 常用命令

### 信号生成命令
```bash
# 生成技术信号
trading-signal generate --symbol BTCUSDT
trading-signal generate --symbol BTCUSDT --type technical
trading-signal generate --symbol BTCUSDT --type pattern

# 生成多时间框架信号
trading-signal generate-mtf --symbol BTCUSDT
trading-signal generate-mtf --symbol BTCUSDT --timeframes 1d,4h,1h

# 批量生成信号
trading-signal generate-batch --symbols BTCUSDT,ETHUSDT,BNBUSDT
trading-signal generate-batch --symbols BTCUSDT,ETHUSDT --type technical
```

### 信号分析命令
```bash
# 分析信号
trading-signal analyze --symbol BTCUSDT
trading-signal analyze --symbol BTCUSDT --days 90
trading-signal analyze --symbol BTCUSDT --include-confidence

# 信号统计
trading-signal stats --symbol BTCUSDT
trading-signal stats --symbol BTCUSDT --period month
trading-signal stats --symbol BTCUSDT --group-by type

# 信号过滤
trading-signal filter --symbol BTCUSDT --min-confidence 0.7
trading-signal filter --symbol BTCUSDT --min-rr 2.0 --max-risk 0.02
```

### 回溯测试命令
```bash
# 执行回测
trading-signal backtest --symbol BTCUSDT
trading-signal backtest --symbol BTCUSDT --days 365
trading-signal backtest --symbol BTCUSDT --initial-capital 10000

# 回测分析
trading-signal backtest-analysis --symbol BTCUSDT
trading-signal backtest-analysis --symbol BTCUSDT --output results.json

# 参数优化
trading-signal optimize --symbol BTCUSDT
trading-signal optimize --symbol BTCUSDT --parameter ma_period
trading-signal optimize --symbol BTCUSDT --grid-search
```

### 实时监控命令
```bash
# 启动监控
trading-signal monitor-start --symbol BTCUSDT
trading-signal monitor-start --symbols BTCUSDT,ETHUSDT --interval 60

# 监控状态
trading-signal monitor-status
trading-signal monitor-status --symbol BTCUSDT

# 停止监控
trading-signal monitor-stop
trading-signal monitor-stop --symbol BTCUSDT
```

### 报告生成命令
```bash
# 信号报告
trading-signal report --symbol BTCUSDT
trading-signal report --symbol BTCUSDT --type detailed
trading-signal report --symbol BTCUSDT --type executive

# 绩效报告
trading-signal performance-report --symbol BTCUSDT
trading-signal performance-report --symbol BTCUSDT --period 90d

# 监控报告
trading-signal monitoring-report --symbol BTCUSDT
trading-signal monitoring-report --symbol BTCUSDT --period 24h
```

## 🎯 使用示例

### 示例1: 完整的信号工作流
```bash
# 1. 生成信号
trading-signal generate --symbol BTCUSDT --type technical --days 180

# 2. 分析信号
trading-signal analyze --symbol BTCUSDT --include-confidence --include-risk

# 3. 过滤信号
trading-signal filter --symbol BTCUSDT --min-confidence 0.7 --min-rr 2.0

# 4. 执行回测
trading-signal backtest --symbol BTCUSDT --initial-capital 10000

# 5. 生成报告
trading-signal report --symbol BTCUSDT --type comprehensive --output reports/btc_signal_workflow.md
```

### 示例2: 实时信号监控系统
```python
from scripts.signal_monitor import SignalMonitor
from scripts.signal_filter import SignalFilter

class RealTimeSignalSystem:
    def __init__(self):
        self.monitor = SignalMonitor()
        self.filter = SignalFilter()
        self.alert_count = 0
    
    def start_monitoring(self, symbols, check_interval=300):
        """启动实时监控"""
        # 配置监控
        self.monitor.configure(
            symbols=symbols,
            timeframes=["1d", "4h"],
            check_interval_seconds=check_interval,
            alert_threshold=0.75
        )
        
        # 设置回调函数
        self.monitor.set_signal_callback(self.process_signal)
        self.monitor.set_alert_callback(self.send_alert)
        
        # 启动监控
        print("🚀 启动实时信号监控...")
        self.monitor.start()
    
    def process_signal(self, signal):
        """处理信号回调"""
        # 过滤信号
        if self.filter.filter_single_signal(signal, min_confidence=0.7):
            print(f"📊 收到过滤后信号: {signal.type} @ ${signal.entry_price:,.0f}")
            
            # 进一步分析
            risk_reward = signal.calculate_risk_reward()
            if risk_reward >= 2.0:
                print(f"🎯 高价值信号: 风险回报比 {risk_reward:.1f}:1")
                return True
        
        return False
    
    def send_alert(self, signal, alert_type):
        """发送告警回调"""
        self.alert_count += 1
        
        alert_message = f"""
🚨 {alert_type.upper()} 告警 #{self.alert_count}
📊 信号: {signal.type}
💰 价格: ${signal.entry_price:,.0f}
🎯 方向: {signal.direction}
📈 置信度: {signal.confidence:.0%}
⚠️  风险回报比: {signal.risk_reward_ratio:.1f}:1
"""
        
        print(alert_message)
        
        # 这里可以添加发送到Telegram、Email等的逻辑
        # self.send_telegram(alert_message)
        # self.send_email(alert_message)
    
    def stop_monitoring(self):
        """停止监控"""
        print("🛑 停止实时信号监控...")
        self