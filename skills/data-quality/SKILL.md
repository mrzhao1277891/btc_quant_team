# 📊 数据质量专家 Skill

## 🎯 概述
数据质量专家是一个专业的加密货币数据质量管理和监控系统。它提供全面的数据质量检查、异常检测、数据修复和监控报告功能，确保你的交易和分析基于可靠、准确、完整的数据。

## ✨ 核心功能

### 🔍 数据质量检查
- **完整性检查**: 检测缺失数据点、时间间隔
- **一致性检查**: 验证数据格式、类型、范围
- **准确性检查**: 对比多个数据源，检测异常值
- **及时性检查**: 监控数据更新频率和延迟

### 🚨 异常检测
- **统计异常**: 基于统计分布的异常检测
- **模式异常**: 检测异常的价格模式
- **时间序列异常**: 检测时间序列中的异常点
- **相关性异常**: 检测相关资产间的异常关系

### 🔧 数据修复
- **缺失值填充**: 智能填充缺失的数据点
- **异常值修正**: 修正或标记异常数据
- **格式标准化**: 统一数据格式和单位
- **数据验证**: 验证修复后的数据质量

### 📈 质量监控
- **实时监控**: 实时数据质量监控
- **定期报告**: 定期生成质量报告
- **告警系统**: 数据质量异常告警
- **趋势分析**: 数据质量趋势分析

### 📊 报告生成
- **质量报告**: 详细的数据质量分析报告
- **异常报告**: 异常检测结果报告
- **修复报告**: 数据修复操作报告
- **趋势报告**: 数据质量趋势报告

## 📁 文件结构

```
data-quality/
├── 📘 SKILL.md                    # 本文件
├── 🚀 QUICK_START.md              # 快速开始指南
├── 📁 config/                     # 配置文件
│   ├── default.yaml              # 主配置文件
│   ├── checks/                   # 检查配置
│   │   ├── completeness.yaml     # 完整性检查配置
│   │   ├── consistency.yaml      # 一致性检查配置
│   │   ├── accuracy.yaml         # 准确性检查配置
│   │   └── timeliness.yaml       # 及时性检查配置
│   └── thresholds/               # 阈值配置
│       ├── anomaly.yaml          # 异常检测阈值
│       ├── quality.yaml          # 质量评分阈值
│       └── alert.yaml            # 告警阈值
├── 📁 scripts/                    # 核心脚本
│   ├── data_quality_checker.py   # 数据质量检查器
│   ├── anomaly_detector.py       # 异常检测器
│   ├── data_repair_tool.py       # 数据修复工具
│   ├── quality_monitor.py        # 质量监控器
│   ├── report_generator.py       # 报告生成器
│   └── data_quality_cli.py       # 命令行接口
├── 📁 examples/                   # 使用示例
│   ├── basic_check.py            # 基础检查示例
│   ├── anomaly_detection.py      # 异常检测示例
│   ├── data_repair.py            # 数据修复示例
│   └── quality_report.py         # 质量报告示例
├── 📁 tests/                      # 测试文件
│   ├── test_checker.py           # 检查器测试
│   ├── test_anomaly.py           # 异常检测测试
│   └── test_repair.py            # 修复工具测试
└── 📁 references/                 # 参考文档
    ├── DATA_QUALITY_METRICS.md   # 数据质量指标
    ├── ANOMALY_DETECTION.md      # 异常检测方法
    └── BEST_PRACTICES.md         # 最佳实践
```

## 🔧 安装和配置

### 系统要求
- Python 3.8+
- pandas, numpy, scipy, matplotlib
- 数据库连接 (SQLite, PostgreSQL, MySQL)

### 安装步骤
```bash
# 1. 进入技能目录
cd /home/francis/btc_quant_team/skills/data-quality

# 2. 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate

# 3. 安装依赖
pip3 install pandas numpy scipy matplotlib seaborn sqlalchemy
```

### 基础配置
```yaml
# config/default.yaml
data_sources:
  primary:
    type: "sqlite"
    path: "crypto_analyzer/data/ultra_light.db"
    table: "klines"
  
  secondary:
    type: "binance_api"
    api_key: "${BINANCE_API_KEY}"
    api_secret: "${BINANCE_API_SECRET}"

quality_checks:
  enable_completeness: true
  enable_consistency: true
  enable_accuracy: true
  enable_timeliness: true

anomaly_detection:
  methods:
    - "statistical"
    - "pattern"
    - "timeseries"
    - "correlation"
  sensitivity: 0.95

monitoring:
  check_interval_minutes: 60
  alert_channels:
    - "telegram"
    - "email"
    - "log"
```

## 🚀 快速开始

### 基础数据质量检查
```python
from scripts.data_quality_checker import DataQualityChecker

# 创建检查器
checker = DataQualityChecker()

# 执行全面检查
results = checker.check_comprehensive(
    symbol="BTCUSDT",
    timeframe="1d",
    days=365
)

# 打印结果
results.print_summary()
```

### 异常检测
```python
from scripts.anomaly_detector import AnomalyDetector

# 创建检测器
detector = AnomalyDetector()

# 检测异常
anomalies = detector.detect_anomalies(
    symbol="BTCUSDT",
    timeframe="1d",
    days=90
)

# 分析异常
for anomaly in anomalies:
    print(f"异常类型: {anomaly.type}")
    print(f"异常时间: {anomaly.timestamp}")
    print(f"异常值: {anomaly.value}")
    print(f"置信度: {anomaly.confidence}")
```

### 数据修复
```python
from scripts.data_repair_tool import DataRepairTool

# 创建修复工具
repair_tool = DataRepairTool()

# 修复数据
repaired_data = repair_tool.repair_data(
    symbol="BTCUSDT",
    timeframe="1d",
    days=365,
    fix_missing=True,
    fix_anomalies=True,
    validate=True
)

# 验证修复结果
validation = repair_tool.validate_repair(repaired_data)
validation.print_report()
```

### 质量监控
```python
from scripts.quality_monitor import QualityMonitor

# 创建监控器
monitor = QualityMonitor()

# 启动监控
monitor.start_monitoring(
    symbols=["BTCUSDT", "ETHUSDT", "BNBUSDT"],
    timeframes=["1d", "4h", "1h"],
    check_interval_minutes=60
)

# 获取监控状态
status = monitor.get_status()
status.print_summary()
```

### 生成报告
```python
from scripts.report_generator import ReportGenerator

# 创建报告生成器
report_gen = ReportGenerator()

# 生成质量报告
report = report_gen.generate_quality_report(
    symbol="BTCUSDT",
    timeframe="1d",
    days=30,
    report_type="detailed"
)

# 保存报告
report.save("reports/btc_quality_report.md")
report.print_summary()
```

## 📊 数据质量指标

### 完整性指标
- **数据点完整性**: 预期数据点 vs 实际数据点
- **时间间隔完整性**: 连续时间间隔检查
- **字段完整性**: 所有必需字段存在
- **范围完整性**: 数据在预期范围内

### 一致性指标
- **格式一致性**: 数据格式统一
- **类型一致性**: 数据类型正确
- **单位一致性**: 计量单位统一
- **命名一致性**: 字段命名规范

### 准确性指标
- **源一致性**: 多数据源对比
- **逻辑一致性**: 数据逻辑关系
- **统计准确性**: 统计特性合理
- **业务准确性**: 符合业务规则

### 及时性指标
- **更新频率**: 数据更新及时性
- **延迟时间**: 数据采集延迟
- **新鲜度**: 数据时效性
- **同步性**: 多源数据同步

## 🚨 异常检测方法

### 统计方法
- **Z-Score检测**: 基于标准差的异常检测
- **IQR检测**: 基于四分位距的异常检测
- **Grubbs检测**: 基于极值的异常检测
- **ESD检测**: 极端学生化偏差检测

### 时间序列方法
- **季节性分解**: 检测季节性异常
- **移动平均**: 基于移动平均的异常
- **指数平滑**: 基于指数平滑的异常
- **ARIMA模型**: 基于预测模型的异常

### 机器学习方法
- **孤立森林**: 基于隔离的异常检测
- **局部异常因子**: 基于密度的异常检测
- **一类SVM**: 基于支持向量的异常检测
- **自动编码器**: 基于重构误差的异常检测

### 模式方法
- **聚类分析**: 基于聚类的异常检测
- **关联规则**: 基于关联的异常检测
- **序列模式**: 基于序列的异常检测
- **图分析**: 基于图结构的异常检测

## 🔧 数据修复策略

### 缺失值处理
- **前向填充**: 使用前一个值填充
- **后向填充**: 使用后一个值填充
- **线性插值**: 线性插值填充
- **样条插值**: 样条插值填充
- **均值填充**: 使用均值填充
- **中位数填充**: 使用中位数填充
- **模型预测**: 使用模型预测填充

### 异常值处理
- **删除**: 删除异常值
- **修正**: 修正为合理值
- **标记**: 标记异常值
- **转换**: 数据转换处理
- **分段**: 分段处理异常

### 格式标准化
- **时间格式**: 统一时间格式
- **数值格式**: 统一数值格式
- **文本格式**: 统一文本格式
- **单位转换**: 统一计量单位

### 数据验证
- **范围验证**: 验证数据范围
- **逻辑验证**: 验证逻辑关系
- **一致性验证**: 验证数据一致性
- **完整性验证**: 验证数据完整性

## 📈 质量监控系统

### 实时监控
```python
# 实时数据质量监控
monitor = QualityMonitor()
monitor.start_realtime_monitoring(
    symbols=["BTCUSDT"],
    timeframes=["1d", "4h"],
    callback=quality_alert_callback
)
```

### 定期检查
```bash
# 使用cron定期检查
0 */6 * * * cd /path/to/data-quality && python scripts/data_quality_cli.py check --symbol BTCUSDT --timeframe 1d
```

### 告警系统
```python
# 配置告警
alerts = AlertSystem()
alerts.add_alert_rule(
    name="completeness_below_95",
    condition=lambda r: r.completeness_score < 0.95,
    severity="high",
    channels=["telegram", "email"]
)
```

### 趋势分析
```python
# 质量趋势分析
trend_analyzer = QualityTrendAnalyzer()
trends = trend_analyzer.analyze_trends(
    symbol="BTCUSDT",
    timeframe="1d",
    period="90d"
)
trends.plot_trends()
```

## 📊 报告系统

### 质量报告
```
# 📊 BTCUSDT数据质量报告

## 📋 执行摘要
- 总体质量评分: 92.5/100
- 数据完整性: 98.2%
- 数据一致性: 95.8%
- 数据准确性: 90.3%
- 数据及时性: 85.7%

## 🔍 详细分析
### 完整性分析
- 总数据点: 365
- 缺失数据点: 7 (1.9%)
- 时间间隔异常: 2 (0.5%)

### 异常检测
- 检测到异常: 15个
- 主要异常类型: 价格异常 (8个)
- 异常时间分布: 集中在2024-03月

## 🚨 问题列表
1. 2024-03-15: 价格异常 (+25%)
2. 2024-03-20: 成交量缺失
3. 2024-04-01: 时间间隔异常

## 🔧 修复建议
1. 修复缺失的成交量数据
2. 验证异常价格点
3. 调整数据采集频率
```

### 异常报告
```python
# 生成异常报告
anomaly_report = report_gen.generate_anomaly_report(
    symbol="BTCUSDT",
    timeframe="1d",
    days=30,
    include_details=True
)
```

### 趋势报告
```python
# 生成趋势报告
trend_report = report_gen.generate_trend_report(
    symbol="BTCUSDT",
    timeframe="1d",
    period="180d",
    include_forecast=True
)
```

## 🔗 与其他系统集成

### 与市场分析系统集成
```python
from skills.market-analysis.scripts.market_analyzer import MarketAnalyzer
from scripts.data_quality_checker import DataQualityChecker

class IntegratedSystem:
    def __init__(self):
        self.analyzer = MarketAnalyzer()
        self.checker = DataQualityChecker()
    
    def analyze_with_quality_check(self, symbol):
        # 检查数据质量
        quality = self.checker.check_comprehensive(symbol)
        
        if quality.overall_score > 0.9:
            # 高质量数据，执行分析
            analysis = self.analyzer.analyze_comprehensive(symbol)
            return analysis
        else:
            # 数据质量不足，先修复
            print(f"数据质量不足: {quality.overall_score}")
            return None
```

### 与交易系统集成
```python
from scripts.quality_monitor import QualityMonitor
from trading_system import TradingSystem

class QualityAwareTradingSystem:
    def __init__(self):
        self.trading_system = TradingSystem()
        self.quality_monitor = QualityMonitor()
    
    def execute_trade(self, symbol, signal):
        # 检查数据质量
        quality = self.quality_monitor.get_current_quality(symbol)
        
        if quality.is_acceptable():
            # 数据质量可接受，执行交易
            self.trading_system.execute(signal)
        else:
            # 数据质量不足，跳过交易
            print(f"跳过交易: 数据质量不足 ({quality.score})")
```

### 与监控系统集成
```python
from scripts.data_quality_checker import DataQualityChecker
from btc_monitor.scripts.btc_monitor_core import BTCMonitor

class QualityMonitoringSystem:
    def __init__(self):
        self.monitor = BTCMonitor()
        self.checker = DataQualityChecker()
    
    def monitor_with_quality(self):
        # 定期检查数据质量
        quality_results = self.checker.check_all_symbols()
        
        # 基于质量结果调整监控
        for result in quality_results:
            if result.score < 0.8:
                # 数据质量差，增加监控频率
                self.monitor.increase_frequency(result.symbol)
            else:
                # 数据质量好，正常监控
                self.monitor.normal_frequency(result.symbol)
```

## 🎯 使用场景

### 场景1: 每日数据质量检查
```bash
# 每日检查所有主要币种的数据质量
data-quality check-all --symbols BTCUSDT,ETHUSDT,BNBUSDT --timeframes 1d,4h

# 生成每日质量报告
data-quality report --symbol BTCUSDT --type daily --output reports/daily_quality.md
```

### 场景2: 实时异常监控
```python
# 实时监控数据异常
monitor = QualityMonitor()
monitor.start_realtime_monitoring(
    symbols=["BTCUSDT", "ETHUSDT"],
    anomaly_types=["price", "volume", "spread"],
    alert_threshold=0.95
)
```

### 场景3: 数据修复工作流
```python
# 完整的数据修复工作流
checker = DataQualityChecker()
repair_tool = DataRepairTool()

# 1. 检查数据质量
results = checker.check_comprehensive("BTCUSDT")

# 2. 识别问题
issues = results.get_issues()

# 3. 执行修复
if issues:
    repaired = repair_tool.repair_data("BTCUSDT", fix_issues=issues)
    
    # 4. 验证修复
    validation = repair_tool.validate_repair(repaired)
    
    # 5. 生成报告
    report = ReportGenerator().generate_repair_report(validation)
```

### 场景4: 质量趋势分析
```python
# 分析数据质量趋势
trend_analyzer = QualityTrendAnalyzer()

# 获取历史质量数据
history = trend_analyzer.get_quality_history("BTCUSDT", "90d")

# 分析趋势
trends = trend_analyzer.analyze_trends(history)

# 预测未来质量
forecast = trend_analyzer.forecast_quality(trends, "30d")

# 生成趋势报告
report = trend_analyzer.generate_trend_report(trends, forecast)
```

## 🔧 配置详解

### 检查配置
```yaml
# config/checks/completeness.yaml
completeness:
  # 完整性检查配置
  check_missing_points: true


## 🕐 每小时自动监控功能 (v3.0新增)

### 🎯 概述
数据质量专家Skill v3.0新增**每小时自动监控**功能，系统会每小时检查所有时间框架的数据质量和新鲜度，如果需要则自动从Binance拉取最新数据并更新到数据库。

### ✨ 核心功能

#### 1. 每小时自动检查
- **检查频率**: 每小时整点执行 (如: 08:00, 09:00, 10:00...)
- **检查内容**: 数据新鲜度、完整性、准确性
- **自动更新**: 如果数据过时，自动从Binance获取最新数据
- **智能判断**: 根据数据年龄决定是否需要更新

#### 2. 监控的时间框架
| 时间框架 | 新鲜度阈值 | 说明 |
|----------|------------|------|
| **4小时** | 6小时 | 超过6小时未更新需要更新 |
| **日线** | 24小时 | 超过24小时未更新需要更新 |
| **周线** | 168小时 | 超过7天未更新需要更新 |
| **月线** | 720小时 | 超过30天未更新需要更新 |

#### 3. 智能更新逻辑
1. **数据缺失** → 立即更新
2. **数据陈旧** (超过阈值) → 立即更新
3. **数据较旧** (超过阈值一半) → 考虑更新
4. **数据新鲜** (小于阈值一半) → 跳过更新

#### 4. 系统配置
```bash
# 🦊 数据质量Skill每小时自动检查
0 * * * * cd /home/francis/btc_quant_team/skills/data-quality && python3 scripts/hourly_data_quality_check.py >> /home/francis/btc_quant_team/skills/data-quality/logs/hourly_cron.log 2>&1
```

#### 5. 立即使用
```bash
# 进入技能目录
cd /home/francis/btc_quant_team/skills/data-quality

# 设置每小时cron
bash setup_hourly_cron.sh

# 手动测试
python3 scripts/hourly_data_quality_check.py

# 查看监控日志
tail -f logs/hourly_cron.log
```

### 📁 新增文件
```
scripts/hourly_data_quality_check.py      # 每小时检查主脚本
HOURLY_MONITOR_GUIDE.md                   # 每小时监控指南
setup_hourly_cron.sh                      # 设置cron的脚本
logs/hourly_cron.log                      # 每小时检查日志
hourly_records/                           # 检查记录存档
```

### 🚀 详细指南
查看完整指南: [HOURLY_MONITOR_GUIDE.md](HOURLY_MONITOR_GUIDE.md)

---

## 🎮 用户主动触发功能 (v2.0新增)

### 🎯 概述
数据质量专家Skill v2.0新增**用户主动触发**功能，支持通过多种方式即时触发数据质量检查和更新。

### ✨ 新增功能

#### 1. OpenClaw聊天触发
直接在OpenClaw聊天中发送命令：
```
检查数据质量          # 检查所有数据质量
更新数据              # 更新所有过时数据
检查新鲜度            # 检查数据新鲜度
全面检查              # 执行全面检查
数据质量状态          # 查看监控状态
数据质量帮助          # 查看帮助信息
生成质量报告          # 生成质量报告
```

#### 2. CLI命令触发
```bash
# 进入Skill目录
cd /home/francis/btc_quant_team/skills/data-quality

# 检查数据质量
python3 scripts/quality_monitor_cli.py check --all

# 更新数据
python3 scripts/quality_monitor_cli.py update --all

# 生成报告
python3 scripts/quality_monitor_cli.py report --type summary

# 查看状态
python3 scripts/quality_monitor_cli.py status
```

#### 3. Python API触发
```python
from scripts.user_trigger import UserTriggerManager

# 创建触发管理器
trigger_manager = UserTriggerManager()

# 触发质量检查
task_id = trigger_manager.trigger_check_quality(
    symbols=['BTCUSDT'],
    timeframes=['4h', '1d', '1w', '1M'],
    user_id='francis',
    callback=lambda task: print(f"任务完成: {task['id']}")
)

print(f"任务已触发: {task_id}")
```

#### 4. 聊天命令示例
```
# 基本命令
检查数据质量          # 检查所有数据质量
更新数据              # 更新所有过时数据
检查新鲜度            # 检查数据新鲜度
全面检查              # 执行全面检查

# 带参数命令
检查BTC数据质量       # 只检查BTC
更新4小时数据         # 只更新4小时数据
检查所有数据新鲜度    # 检查所有数据新鲜度

# 状态和帮助
数据质量状态          # 查看监控状态
数据质量帮助          # 查看帮助信息
生成日报              # 生成每日质量报告
```

### 📁 新增文件
```
scripts/user_trigger.py          # 用户触发管理器
scripts/chat_trigger.py          # 聊天触发处理器
scripts/openclaw_integration.py  # OpenClaw集成接口
config/openclaw.yaml            # OpenClaw配置
config/monitor.yaml             # 监控配置
MONITOR_GUIDE.md                # 监控使用指南
```

### 🔧 配置OpenClaw集成
编辑 `config/openclaw.yaml`:
```yaml
skill:
  name: "数据质量专家"
  trigger_words:
    - "数据质量"
    - "quality"
    - "新鲜度"
    - "更新数据"
  response_format: "markdown"

commands:
  check_quality:
    enabled: true
    aliases: ["检查质量", "质量检查"]
  update_data:
    enabled: true
    aliases: ["更新", "刷新"]
```

### 🚀 立即使用
```bash
# 测试OpenClaw集成
cd /home/francis/btc_quant_team/skills/data-quality
python3 scripts/openclaw_integration.py

# 测试聊天触发
python3 -c "
from scripts.chat_trigger import ChatTrigger
chat = ChatTrigger()
result = chat.process_message('检查数据质量', 'francis')
print(result['message'])
"
```

---

**🎯 数据质量专家Skill v2.0现已就绪！**

**新增用户主动触发功能，支持：**
- ✅ OpenClaw聊天触发
- ✅ CLI命令触发  
- ✅ Python API触发
- ✅ 实时状态反馈

**开始享受即时、主动的数据质量管理吧！** 🚀🦊
