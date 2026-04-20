# 市场分析专家

## 描述

专业的加密货币市场分析系统，基于多时间框架投资框架，提供从宏观趋势到微观入场的完整分析链。

## 何时使用

当用户需要：
- 全面的加密货币市场分析
- 多时间框架趋势判断
- 专业的交易信号生成
- 风险管理和仓位建议
- 市场情绪和资金流向分析

## 核心特性

### 📊 多时间框架分析
- **金字塔式决策流程**: 月线→周线→日线→4小时线
- **趋势一致性分析**: 跨时间框架趋势确认
- **信号共振检测**: 多时间框架信号叠加

### 🔍 专业分析维度
- **技术分析**: 趋势、动量、波动率、成交量
- **支撑阻力分析**: 技术位、心理位、动态位
- **模式识别**: 图表模式、蜡烛图模式
- **市场情绪**: 资金流向、持仓变化、社交媒体情绪

### 🎯 智能决策支持
- **交易信号生成**: 基于多维度分析的明确信号
- **风险管理**: 动态止损止盈计算
- **仓位管理**: 基于风险的资金分配
- **时机选择**: 最佳入场出场时机

### 📈 专业报告输出
- **标准化报告**: 统一格式的专业分析报告
- **可视化图表**: 技术指标图表展示
- **数据驱动**: 基于实时数据的客观分析
- **可操作建议**: 具体的交易计划和风险管理

## 文件结构

```
market-analysis/
├── SKILL.md                    # 本文件
├── QUICK_START.md              # 快速开始指南
├── scripts/
│   ├── market_analyzer.py      # 市场分析器
│   ├── multi_timeframe_analyzer.py  # 多时间框架分析器
│   ├── signal_generator.py     # 信号生成器
│   ├── risk_manager.py         # 风险管理器
│   ├── report_generator.py     # 报告生成器
│   ├── data_fetcher.py         # 数据获取器
│   ├── market_cli.py           # 命令行界面
│   └── setup.sh                # 安装脚本
├── config/
│   ├── default.yaml            # 默认配置
│   ├── frameworks/             # 分析框架配置
│   │   ├── crypto_mtf.yaml     # 加密货币多时间框架
│   │   ├── trend_following.yaml # 趋势跟踪框架
│   │   └── mean_reversion.yaml # 均值回归框架
│   └── reports/                # 报告模板
│       ├── professional.md     # 专业报告模板
│       ├── executive.md        # 执行摘要模板
│       └── technical.md        # 技术分析模板
├── templates/
│   ├── analysis_report.html    # HTML报告模板
│   ├── dashboard.html          # 仪表板模板
│   └── charts/                 # 图表模板
└── examples/
    ├── basic_analysis.py       # 基础分析示例
    ├── full_workflow.py        # 完整工作流程示例
    └── custom_framework.py     # 自定义框架示例
```

## 快速开始

### 安装和设置

```bash
# 1. 进入技能目录
cd /home/francis/.nvm/versions/node/v22.22.2/lib/node_modules/openclaw/skills/market-analysis

# 2. 运行安装脚本
bash scripts/setup.sh

# 3. 安装Python依赖
pip3 install pandas numpy matplotlib plotly ta-lib yfinance ccxt requests
```

### 基本使用

```bash
# 1. 运行基础市场分析
python scripts/market_cli.py analyze --symbol BTCUSDT

# 2. 生成专业报告
python scripts/market_cli.py report --symbol BTCUSDT --timeframes 1d,4h,1h

# 3. 查看交易信号
python scripts/market_cli.py signals --symbol BTCUSDT

# 4. 风险管理分析
python scripts/market_cli.py risk --symbol BTCUSDT --position 0.1
```

## 详细功能

### 1. 市场分析器 (`market_analyzer.py`)

#### 功能特性
- **综合技术分析**: 趋势、动量、波动率、成交量
- **多维度评估**: 技术面、基本面、情绪面
- **市场状态判断**: 趋势、盘整、反转阶段
- **强度评分**: 量化市场强度指标

#### 使用示例
```python
from scripts.market_analyzer import MarketAnalyzer

# 创建分析器
analyzer = MarketAnalyzer(symbol="BTCUSDT")

# 执行全面分析
analysis = analyzer.analyze_comprehensive(
    timeframes=["1d", "4h", "1h"],
    include_sentiment=True,
    include_fundamental=True
)

# 获取分析结果
print(f"市场状态: {analysis.market_state}")
print(f"趋势方向: {analysis.trend_direction}")
print(f"强度评分: {analysis.strength_score}/100")
print(f"风险等级: {analysis.risk_level}")
```

### 2. 多时间框架分析器 (`multi_timeframe_analyzer.py`)

#### 功能特性
- **金字塔式分析**: 月→周→日→4小时
- **趋势一致性**: 跨时间框架趋势确认
- **信号共振**: 多时间框架信号叠加
- **权重分配**: 不同时间框架的重要性权重

#### 使用示例
```python
from scripts.multi_timeframe_analyzer import MultiTimeframeAnalyzer

# 创建多时间框架分析器
mtf_analyzer = MultiTimeframeAnalyzer()

# 加载分析框架
mtf_analyzer.load_framework("crypto_mtf")

# 执行多时间框架分析
mtf_analysis = mtf_analyzer.analyze(
    symbol="BTCUSDT",
    timeframes=["1M", "1w", "1d", "4h"]
)

# 获取决策建议
decision = mtf_analysis.get_decision()
print(f"战略方向: {decision.strategic_direction}")
print(f"战术建议: {decision.tactical_suggestion}")
print(f"执行时机: {decision.execution_timing}")
```

### 3. 信号生成器 (`signal_generator.py`)

#### 信号类型
1. **趋势信号**: 基于趋势分析的入场信号
2. **反转信号**: 基于反转模式的信号
3. **突破信号**: 基于支撑阻力突破的信号
4. **背离信号**: 基于指标背离的信号
5. **确认信号**: 多指标确认的强化信号

#### 使用示例
```python
from scripts.signal_generator import SignalGenerator

# 创建信号生成器
signal_gen = SignalGenerator()

# 生成交易信号
signals = signal_gen.generate_signals(
    symbol="BTCUSDT",
    analysis_data=market_analysis,
    risk_tolerance="medium"
)

# 处理信号
for signal in signals:
    if signal.confidence > 0.7:  # 高置信度信号
        print(f"🚨 交易信号: {signal.type}")
        print(f"   方向: {signal.direction}")
        print(f"   置信度: {signal.confidence:.1%}")
        print(f"   入场价: ${signal.entry_price:,.2f}")
        print(f"   止损: ${signal.stop_loss:,.2f}")
        print(f"   止盈: ${signal.take_profit:,.2f}")
```

### 4. 风险管理器 (`risk_manager.py`)

#### 风险管理功能
- **动态止损**: 基于波动率的止损计算
- **仓位大小**: 基于风险的仓位计算
- **风险暴露**: 总风险控制
- **回撤管理**: 最大回撤限制

#### 使用示例
```python
from scripts.risk_manager import RiskManager

# 创建风险管理器
risk_mgr = RiskManager(
    account_size=10000,  # 账户规模
    max_risk_per_trade=0.02,  # 单笔交易最大风险
    max_drawdown=0.20  # 最大回撤
)

# 计算交易参数
trade_params = risk_mgr.calculate_trade(
    symbol="BTCUSDT",
    entry_price=70000,
    stop_loss=68000,
    confidence=0.75
)

print(f"仓位大小: {trade_params.position_size:.4f} BTC")
print(f"风险金额: ${trade_params.risk_amount:,.2f}")
print(f"风险回报比: {trade_params.risk_reward_ratio:.2f}")
print(f"建议止损: ${trade_params.adjusted_stop_loss:,.2f}")
```

### 5. 报告生成器 (`report_generator.py`)

#### 报告类型
1. **专业分析报告**: 详细的技术分析报告
2. **执行摘要**: 关键信息和决策建议
3. **技术分析报告**: 纯技术指标分析
4. **风险管理报告**: 风险分析和建议
5. **市场展望报告**: 未来市场预测

#### 使用示例
```python
from scripts.report_generator import ReportGenerator

# 创建报告生成器
report_gen = ReportGenerator()

# 生成专业报告
report = report_gen.generate_professional_report(
    symbol="BTCUSDT",
    analysis_data=market_analysis,
    signals=signals,
    risk_assessment=risk_assessment,
    template="professional"
)

# 保存报告
report.save("reports/btc_analysis_20240419.md")
report.export_html("reports/btc_analysis_20240419.html")

# 打印报告摘要
report.print_summary()
```

## 命令行界面

### 命令列表

```bash
# 市场分析
market-analyze analyze --symbol BTCUSDT [--timeframes 1d,4h,1h]
market-analyze analyze-all --symbols BTCUSDT,ETHUSDT,BNBUSDT

# 报告生成
market-analyze report --symbol BTCUSDT --type professional
market-analyze report --symbol BTCUSDT --type executive
market-analyze report --symbol BTCUSDT --type technical

# 信号分析
market-analyze signals --symbol BTCUSDT [--timeframe 4h]
market-analyze signals-history --symbol BTCUSDT --days 7

# 风险管理
market-analyze risk --symbol BTCUSDT --entry 70000 --stop-loss 68000
market-analyze portfolio-risk --symbols BTCUSDT,ETHUSDT

# 数据管理
market-analyze data-fetch --symbol BTCUSDT --timeframe 1d --days 365
market-analyze data-update --symbol BTCUSDT
market-analyze data-quality --symbol BTCUSDT

# 系统管理
market-analyze config show
market-analyze config set --key analysis.timeframes --value "1d,4h,1h"
market-analyze config test
```

### 使用示例

```bash
# 完整工作流程示例
# 1. 获取和分析数据
market-analyze data-fetch --symbol BTCUSDT --timeframe 1d --days 200
market-analyze data-fetch --symbol BTCUSDT --timeframe 4h --days 50

# 2. 执行全面分析
market-analyze analyze --symbol BTCUSDT --timeframes 1d,4h,1h --include-sentiment

# 3. 生成交易信号
market-analyze signals --symbol BTCUSDT --timeframe 4h

# 4. 风险管理计算
market-analyze risk --symbol BTCUSDT --entry 70000 --stop-loss 68000 --account-size 10000

# 5. 生成专业报告
market-analyze report --symbol BTCUSDT --type professional --output reports/btc_analysis.md
```

## 分析框架配置

### 加密货币多时间框架框架 (`config/frameworks/crypto_mtf.yaml`)

```yaml
name: "加密货币多时间框架投资框架"
description: "基于金字塔式决策流程的加密货币分析框架"

timeframes:
  strategic:
    - name: "月线"
      timeframe: "1M"
      weight: 0.30
      indicators: ["EMA25", "MACD", "长期趋势线"]
    
    - name: "周线"
      timeframe: "1w"
      weight: 0.25
      indicators: ["EMA7", "EMA12", "EMA25", "MACD", "成交量"]
  
  tactical:
    - name: "日线"
      timeframe: "1d"
      weight: 0.25
      indicators: ["EMA12", "EMA25", "EMA50", "RSI", "布林带"]
    
    - name: "4小时线"
      timeframe: "4h"
      weight: 0.20
      indicators: ["EMA12", "EMA25", "RSI", "随机指标", "K线形态"]

decision_rules:
  trend_confirmation:
    - "至少3个时间框架趋势一致"
    - "战略层趋势权重最高"
  
  signal_strength:
    - "多时间框架信号共振增加强度"
    - "成交量确认增加可信度"
  
  risk_management:
    - "战略层决定最大风险暴露"
    - "战术层决定具体止损位置"
    - "执行层决定精确入场时机"
```

### 趋势跟踪框架 (`config/frameworks/trend_following.yaml`)

```yaml
name: "趋势跟踪框架"
description: "识别和跟随市场趋势的交易框架"

core_principles:
  - "趋势是你的朋友"
  - "让利润奔跑，快速止损"
  - "只在趋势明确时交易"

entry_signals:
  trend_confirmation:
    - "价格在主要移动平均线之上"
    - "移动平均线多头排列"
    - "动量指标确认趋势"
  
  breakout:
    - "突破关键阻力位"
    - "成交量放大确认"
    - "回测不破前低"

exit_signals:
  trend_reversal:
    - "价格跌破移动平均线"
    - "移动平均线死叉"
    - "动量指标背离"
  
  profit_taking:
    - "达到风险回报比目标"
    - "遇到强阻力位"
    - "趋势动能减弱"
```

## 专业报告模板

### 专业分析报告结构

```
# 📊 BTCUSDT专业分析报告

## 📋 执行摘要
- 市场状态: 上涨趋势
- 关键水平: 支撑$68,000，阻力$75,000
- 交易建议: 逢低做多
- 风险等级: 中等

## 📈 技术分析
### 趋势分析
- 月线: 上涨趋势
- 周线: 上涨趋势
- 日线: 震荡上行
- 4小时: 短期调整

### 关键指标
- RSI: 58 (中性偏多)
- MACD: 金叉向上
- 成交量: 温和放大
- 波动率: 中等

## 🎯 交易计划
### 做多机会
- 入场: $70,000-71,000
- 止损: $68,000
- 止盈: $75,000
- 风险回报比: 1:2.5

### 做空机会
- 入场: $75,000-76,000
- 止损: $78,000
- 止盈: $70,000
- 风险回报比: 1:1.67

## ⚠️ 风险管理
- 最大仓位: 10%
- 单笔风险: 2%
- 总风险暴露: 20%
- 关键风险: 宏观政策变化

## 📅 市场展望
- 短期(1-7天): 震荡上行
- 中期(1-4周): 测试前高
- 长期(1-3月): 趋势延续
```

## 集成示例

### 与交易系统集成

```python
from scripts.market_analyzer import MarketAnalyzer
from scripts.signal_generator import SignalGenerator
from scripts.risk_manager import RiskManager

class TradingSystem:
    def __init__(self):
        self.analyzer = MarketAnalyzer()
        self.signal_gen = SignalGenerator()
        self.risk_mgr = RiskManager(account_size=10000)
    
    def analyze_and_trade(self, symbol):
        # 市场分析
        analysis = self.analyzer.analyze_comprehensive(symbol)
        
        # 信号生成
        signals = self.signal_gen.generate_signals(symbol, analysis)
        
        # 风险管理
        for signal in signals:
            if signal.confidence > 0.7:
                trade_params = self.risk_mgr.calculate_trade(
                    symbol=symbol,
                    entry_price=signal.entry_price,
                    stop_loss=signal.stop_loss,
                    confidence=signal.confidence
                )
                
                # 执行交易
                self.execute_trade(symbol, trade_params)
    
    def execute_trade(self, symbol, trade_params):
        # 这里添加具体的交易执行逻辑
        print(f"执行交易: {symbol}")
        print(f"仓位: {trade_params.position_size}")
        print(f"止损: {trade_params.adjusted_stop_loss}")
        print(f"止盈: {trade_params.take_profit}")
```

### 与监控系统集成

```python
from scripts.market_analyzer import MarketAnalyzer
from btc_monitor.scripts.btc_monitor_core import BTCMonitor

class MarketMonitoringSystem:
    def __init__(self):
        self.analyzer = MarketAnalyzer()
        self.monitor = BTCMonitor()
    
    def update_monitor_points(self, symbol):
        # 分析市场
        analysis = self.analyzer.analyze_comprehensive(symbol)
        
        # 基于分析更新监控点
        support_levels = analysis.support_levels[:3]  # 前3个支撑位
        resistance_levels = analysis.resistance_levels[:3]  # 前3个阻力位
        
