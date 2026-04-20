# 🛠️ 量化工具库

## 📋 概述
专业的加密货币量化分析工具库，采用模块化设计，每个工具都是独立的纯函数。

## 🏗️ 架构设计
```
tools/
├── data/              # 数据工具
│   ├── fetch.py      # 数据获取
│   ├── storage.py    # 数据存储
│   └── sync.py       # 数据同步
├── quality/          # 质量工具
│   ├── checker.py     # 质量检查
│   ├── validator.py   # 数据验证
│   ├── cleaner.py     # 数据清洗
│   ├── monitor.py     # 质量监控
│   └── __init__.py    # 统一导出
├── indicators/       # 指标工具
│   ├── trend.py     # 趋势指标
│   ├── momentum.py  # 动量指标
│   ├── volatility.py # 波动率指标
│   └── volume.py    # 成交量指标
├── analysis/         # 分析工具
│   ├── technical.py          # 技术分析
│   ├── support_resistance.py # 支撑阻力分析
│   ├── patterns.py           # 模式识别
│   ├── multi_timeframe.py    # 多时间框架分析
│   └── __init__.py           # 统一导出
├── risk/             # 风险工具
│   ├── position.py   # 仓位管理
│   ├── stop_loss.py  # 止损计算
│   └── risk_metrics.py # 风险指标
└── utils/            # 通用工具
    ├── time.py       # 时间处理
    ├── math.py       # 数学计算
    └── formatting.py # 格式化输出
```

## 🚀 快速使用

### 安装
```bash
# 从项目根目录
pip install -e .
```

### 基本示例
```python
# 导入工具
from tools.data.fetch import fetch_klines
from tools.indicators.trend import calculate_ema
from tools.quality import DataQualityChecker
from tools.analysis import TechnicalAnalyzer, SupportResistanceAnalyzer

# 获取数据
data = fetch_klines("BTCUSDT", "4h", 500)

# 1. 质量检查
checker = DataQualityChecker()
quality_report = checker.check_dataframe(data, "BTC数据", timeframe="4h")

# 2. 技术分析
technical_analyzer = TechnicalAnalyzer()
technical_report = technical_analyzer.analyze(data, "BTCUSDT", "4h")
technical_report.print_summary()

# 3. 支撑阻力分析
sr_analyzer = SupportResistanceAnalyzer()
sr_report = sr_analyzer.analyze(data, "BTCUSDT", "4h")
sr_report.print_summary()

# 4. 计算指标
ema7 = calculate_ema(data, 7)
ema25 = calculate_ema(data, 25)

# 5. 生成交易建议
current_price = data['close'].iloc[-1]
trend = technical_report.trend_analysis
momentum = technical_report.momentum_analysis
nearest_support = sr_report.nearest_support
nearest_resistance = sr_report.nearest_resistance

print("💡 交易建议:")
if trend.direction.value in ["strong_up", "moderate_up"] and momentum.rsi_value < 70:
    print("  🟢 考虑买入，趋势向上且未超买")
    if nearest_resistance:
        target_distance = (nearest_resistance.price - current_price) / current_price * 100
        print(f"    目标阻力: ${nearest_resistance.price:,.2f} (+{target_distance:.1f}%)")
elif trend.direction.value in ["strong_down", "moderate_down"] and momentum.rsi_value > 30:
    print("  🔴 考虑卖出，趋势向下且未超卖")
    if nearest_support:
        target_distance = (current_price - nearest_support.price) / current_price * 100
        print(f"    目标支撑: ${nearest_support.price:,.2f} (-{target_distance:.1f}%)")
else:
    print("  ⚪ 建议观望，趋势不明或处于极端区域")
```

## 📊 工具索引

### 数据工具 (data/)
| 工具 | 功能 | 输入 | 输出 |
|------|------|------|------|
| `fetch_klines` | 获取K线数据 | symbol, timeframe, limit | List[Dict] |
| `save_to_db` | 保存到数据库 | data, table_name | bool |
| `load_from_db` | 从数据库加载 | symbol, timeframe | List[Dict] |
| `sync_data` | 同步数据源 | source, target | Dict[stats] |

### 质量工具 (quality/)

#### 1. 质量检查工具 (checker.py)
**功能**: 全面评估数据质量，生成质量报告

| 类/函数 | 功能 | 输入 | 输出 |
|---------|------|------|------|
| `DataQualityChecker` | 质量检查器 | DataFrame, 配置 | QualityReport |
| `QualityReport` | 质量报告 | - | 可序列化的报告对象 |
| `QualityMetric` | 质量指标 | - | 单个质量指标 |
| `QualityDimension` | 质量维度枚举 | - | 完整性/一致性/准确性/及时性/有效性 |
| `QualityLevel` | 质量等级枚举 | - | 优秀/良好/一般/较差/严重 |

**质量维度**:
- **完整性 (Completeness)**: 数据是否完整，缺失值比例
- **一致性 (Consistency)**: 数据类型、格式是否一致
- **准确性 (Accuracy)**: 数据是否准确，异常值检测
- **及时性 (Timeliness)**: 数据是否及时，新鲜度检查
- **有效性 (Validity)**: 数据是否有效，范围验证

#### 2. 数据验证工具 (validator.py)
**功能**: 验证数据是否符合业务规则

| 类/函数 | 功能 | 输入 | 输出 |
|---------|------|------|------|
| `DataValidator` | 数据验证器 | DataFrame, 规则 | ValidationReport |
| `ValidationRule` | 验证规则 | - | 单个验证规则 |
| `ValidationReport` | 验证报告 | - | 验证结果报告 |
| `ValidationType` | 验证类型枚举 | - | 必需性/类型/范围/模式/唯一性/关系/自定义 |
| `ValidationSeverity` | 严重性枚举 | - | 信息/警告/错误/严重 |

**内置验证规则**:
- `kline_required_fields`: K线必需字段验证
- `kline_price_positive`: 价格正数验证
- `kline_high_low_relation`: 高低价关系验证
- `kline_open_close_range`: 开盘收盘价范围验证
- `kline_volume_positive`: 成交量正数验证
- `kline_timestamp_unique`: 时间戳唯一性验证

#### 3. 数据清洗工具 (cleaner.py)
**功能**: 清洗和修复数据问题

| 类/函数 | 功能 | 输入 | 输出 |
|---------|------|------|------|
| `DataCleaner` | 数据清洗器 | DataFrame, 策略 | (DataFrame, CleaningReport) |
| `CleaningRule` | 清洗规则 | - | 单个清洗规则 |
| `CleaningReport` | 清洗报告 | - | 清洗结果报告 |
| `CleaningMethod` | 清洗方法枚举 | - | 删除/填充/插值/修正/标记/转换 |
| `CleaningStrategy` | 清洗策略枚举 | - | 激进/适中/保守 |

**内置清洗规则**:
- `fill_missing_prices_with_interpolation`: 价格缺失值插值填充
- `remove_duplicate_timestamps`: 删除重复时间戳
- `correct_price_outliers_with_iqr`: 价格异常值IQR修正
- `ensure_price_positive`: 确保价格为正数
- `fix_high_low_relationship`: 修正高低价关系
- `convert_timestamp_to_datetime`: 时间戳转换为日期时间

#### 4. 质量监控工具 (monitor.py)
**功能**: 持续监控数据质量，实时警报

| 类/函数 | 功能 | 输入 | 输出 |
|---------|------|------|------|
| `DataQualityMonitor` | 质量监控器 | 数据源, 警报规则 | MonitorReport |
| `AlertRule` | 警报规则 | - | 单个警报规则 |
| `Alert` | 警报对象 | - | 触发的警报 |
| `MonitorReport` | 监控报告 | - | 监控结果报告 |
| `AlertLevel` | 警报级别枚举 | - | 信息/警告/错误/严重 |
| `MonitorType` | 监控类型枚举 | - | 实时/历史/预测/对比 |

**内置警报规则**:
- `data_freshness_critical`: 数据新鲜度严重下降
- `completeness_warning`: 数据完整性警告
- `accuracy_critical`: 数据准确性严重问题
- `outlier_detected`: 检测到异常值
- `data_delay_warning`: 数据延迟警告

#### 5. 基础质量函数
| 函数 | 功能 | 输入 | 输出 |
|------|------|------|------|
| `check_completeness` | 完整性检查 | data, timeframe | float(0-1) |
| `check_consistency` | 一致性检查 | data | Dict[issues] |
| `check_freshness` | 新鲜度检查 | data | Dict[status, age_hours] |
| `detect_anomalies` | 异常检测 | data | List[anomalies] |

### 指标工具 (indicators/)
| 工具 | 功能 | 输入 | 输出 |
|------|------|------|------|
| `calculate_ema` | EMA计算 | data, period | List[float] |
| `calculate_sma` | SMA计算 | data, period | List[float] |
| `calculate_macd` | MACD计算 | data | Dict[dif, dea, hist] |
| `calculate_rsi` | RSI计算 | data, period | List[float] |
| `calculate_bollinger` | 布林带 | data, period, std | Dict[upper, middle, lower] |

### 分析工具 (analysis/)

#### 1. 技术分析工具 (technical.py)
**功能**: 综合技术分析，包括趋势、动量、波动率、成交量分析

| 类/函数 | 功能 | 输入 | 输出 |
|---------|------|------|------|
| `TechnicalAnalyzer` | 技术分析器 | DataFrame, symbol, timeframe | TechnicalAnalysisReport |
| `TechnicalAnalysisReport` | 技术分析报告 | - | 可序列化的报告对象 |
| `TrendAnalysis` | 趋势分析结果 | - | 趋势方向、强度、阶段 |
| `MomentumAnalysis` | 动量分析结果 | - | RSI、随机指标、CCI等 |
| `VolatilityAnalysis` | 波动率分析结果 | - | ATR、布林带、波动率状态 |
| `VolumeAnalysis` | 成交量分析结果 | - | 成交量趋势、OBV、量价确认 |
| `TechnicalSignal` | 技术信号 | - | 信号类型、置信度、原因 |
| `TrendDirection` | 趋势方向枚举 | - | 强势上涨/温和上涨/横盘/温和下跌/强势下跌 |
| `MarketPhase` | 市场阶段枚举 | - | 吸筹/上升/派发/下降/盘整 |
| `SignalType` | 信号类型枚举 | - | 强烈买入/买入/中性/卖出/强烈卖出 |

#### 2. 支撑阻力分析工具 (support_resistance.py)
**功能**: 识别和分析支撑阻力位，包括技术位、心理位、动态位

| 类/函数 | 功能 | 输入 | 输出 |
|---------|------|------|------|
| `SupportResistanceAnalyzer` | 支撑阻力分析器 | DataFrame, symbol, timeframe | SupportResistanceReport |
| `SupportResistanceReport` | 支撑阻力分析报告 | - | 可序列化的报告对象 |
| `SupportResistanceLevel` | 支撑阻力位 | - | 位位价格、类型、强度、置信度 |
| `BreakoutAnalysis` | 突破分析 | - | 突破类型、价格、确认状态 |
| `LevelType` | 位位类型枚举 | - | 支撑/阻力/心理/动态/斐波那契/枢纽点 |
| `StrengthLevel` | 强度等级枚举 | - | 弱/中等/强/非常强 |
| `BreakoutType` | 突破类型枚举 | - | 突破/跌破/假突破/测试中 |

#### 3. 模式识别工具 (patterns.py)
**功能**: 识别技术分析模式，包括反转模式、持续模式、蜡烛图模式

| 类/函数 | 功能 | 输入 | 输出 |
|---------|------|------|------|
| `PatternRecognizer` | 模式识别器 | DataFrame, symbol, timeframe | PatternAnalysisReport |
| `PatternAnalysisReport` | 模式分析报告 | - | 可序列化的报告对象 |
| `Pattern` | 技术模式 | - | 模式类型、名称、方向、状态 |
| `CandlestickPattern` | 蜡烛图模式 | - | 模式名称、方向、置信度 |
| `PatternType` | 模式类型枚举 | - | 反转/持续/蜡烛图/图表/谐波 |
| `PatternDirection` | 模式方向枚举 | - | 看涨/看跌/中性 |
| `PatternStatus` | 模式状态枚举 | - | 形成中/已完成/已确认/已失效 |

#### 4. 多时间框架分析工具 (multi_timeframe.py)
**功能**: 跨多个时间框架进行综合分析，识别趋势一致性、信号确认等

| 类/函数 | 功能 | 输入 | 输出 |
|---------|------|------|------|
| `MultiTimeframeAnalyzer` | 多时间框架分析器 | {timeframe: df}, symbol | MultiTimeframeReport |
| `MultiTimeframeReport` | 多时间框架分析报告 | - | 可序列化的报告对象 |
| `TimeframeAnalysis` | 时间框架分析 | - | 单个时间框架分析结果 |
| `TrendAlignment` | 趋势对齐分析 | - | 趋势对齐状态、分数 |
| `SignalConfirmation` | 信号确认分析 | - | 信号确认分数、时间框架 |
| `SupportResistanceConfluence` | 支撑阻力重合分析 | - | 重合价格、分数、时间框架 |
| `TimeframeHierarchy` | 时间框架层级枚举 | - | 宏观/中级/微观/交易 |
| `AlignmentStatus` | 对齐状态枚举 | - | 强对齐/中等对齐/中性/中等冲突/强冲突 |

#### 5. 基础分析函数
| 函数 | 功能 | 输入 | 输出 |
|------|------|------|------|
| `analyze_trend` | 趋势分析 | data, indicators | Dict[trend, strength] |
| `find_support_resistance` | 支撑阻力 | data | Dict[support, resistance] |
| `identify_patterns` | 形态识别 | data | List[patterns] |

### 风险工具 (risk/)
| 工具 | 功能 | 输入 | 输出 |
|------|------|------|------|
| `calculate_position_size` | 仓位计算 | capital, risk_percent, stop_loss | float |
| `calculate_stop_loss` | 止损计算 | entry_price, risk_percent | float |
| `calculate_risk_reward` | 风险收益比 | entry, stop_loss, take_profit | float |

### 通用工具 (utils/)
| 工具 | 功能 | 输入 | 输出 |
|------|------|------|------|
| `timestamp_to_datetime` | 时间戳转换 | timestamp | datetime |
| `datetime_to_timestamp` | 时间转时间戳 | datetime | int |
| `format_price` | 价格格式化 | price, precision | str |
| `calculate_percentage` | 百分比计算 | old, new | float |

## 🔧 开发指南

### 创建新工具
1. 确定工具所属模块
2. 在对应目录创建 `.py` 文件
3. 编写纯函数，包含完整文档字符串
4. 添加类型提示
5. 编写单元测试
6. 更新本README文档

### 工具函数规范
```python
def tool_function(param1: type, param2: type = default) -> return_type:
    """函数简短描述。
    
    详细描述函数功能、算法、用途等。
    
    Args:
        param1: 参数1描述
        param2: 参数2描述，默认值说明
    
    Returns:
        返回值描述，包括数据结构
    
    Raises:
        ExceptionType: 什么情况下抛出
    
    Examples:
        >>> tool_function(value1, value2)
        expected_output
    
    Notes:
        额外说明、性能考虑、使用限制等
    """
    # 实现代码
    pass
```

### 依赖规则
- 工具函数应该是纯函数（无副作用）
- 避免跨模块直接导入（通过接口）
- 工具模块间依赖关系：
  ```
  data → utils ✅
  quality → data ✅  
  indicators → data ✅
  analysis → indicators ✅
  analysis → quality ❌ (禁止)
  ```

## 🧪 测试
```bash
# 运行工具层测试
pytest tests/unit/tools/

# 测试特定模块
pytest tests/unit/tools/data/

# 生成测试覆盖率报告
pytest --cov=tools --cov-report=html
```

## 📚 文档
```bash
# 生成API文档
pdoc tools --html --output-dir docs/tools

# 查看在线文档
open docs/tools/index.html
```

## 🔄 版本历史
- v1.0.0 (2026-04-19): 初始版本，模块化工具库

---

**🦊 设计: Steve量化助手** | **架构: 六边形架构** | **原则: 单一职责**