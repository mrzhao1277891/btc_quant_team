# BTC回测系统

基于历史数据的量化交易策略回测平台。

## 目录结构

```
backend/backtest/
├── __init__.py              # 模块初始化
├── models.py                # 核心数据模型
├── logger.py                # 日志系统配置
├── config.py                # 配置管理
├── engine.py                # 回测引擎（待实现）
├── strategy_manager.py      # 策略管理器（待实现）
├── indicator_calculator.py  # 指标计算器（待实现）
├── db_connector.py          # 数据库连接器（待实现）
├── metrics_calculator.py    # 性能指标计算器（待实现）
└── README.md                # 本文件
```

## 核心数据模型

### StrategyConfig
策略配置，包含：
- 策略名称和描述
- 时间周期
- 持仓方向（long/short）
- 持仓大小（金额或百分比）
- 开仓条件（指标条件组合）
- 平仓条件（指标条件和止盈止损）
- 初始资金
- 是否允许多仓位

### Position
持仓信息，包含：
- 开仓时间和价格
- 持仓数量和价值
- 持仓方向
- 开仓资金

### TradeRecord
交易记录，包含：
- 交易ID
- 开仓和平仓时间、价格
- 持仓数量和方向
- 盈亏金额和百分比
- 持仓时长
- 平仓原因

### PerformanceMetrics
性能指标，包含：
- 总收益和收益率
- 交易统计（总数、胜率）
- 平均盈亏
- 盈亏比
- 最大回撤
- 夏普比率
- 连胜连亏记录

### BacktestResult
回测结果，包含：
- 回测ID
- 策略配置
- 开始和结束日期
- 交易记录列表
- 性能指标
- 权益曲线
- 数据质量警告
- 执行时间

## 数据模型序列化

所有数据模型都支持：
- `to_dict()`: 转换为字典
- `from_dict(data)`: 从字典创建
- `to_json()`: 转换为JSON字符串（部分模型）
- `from_json(json_str)`: 从JSON字符串创建（部分模型）

## 日志系统

使用 `logger.py` 配置的日志系统：
- 控制台输出：INFO级别
- 文件输出：DEBUG级别
- 日志文件轮转：10MB，保留5个备份
- 日志目录：`logs/`

使用示例：
```python
from backend.backtest.logger import get_logger

logger = get_logger("backtest")
logger.info("回测开始")
logger.debug("详细调试信息")
logger.error("错误信息")
```

## 配置管理

使用 `config.py` 加载配置：
```python
from backend.backtest.config import config

# 获取数据库配置
db_config = config.get_database_config()

# 获取特定配置项
initial_capital = config.get('backtest.default_initial_capital', 100000.0)

# 获取可用指标
indicators = config.get_available_indicators()
```

配置文件位置：`config/backtest.yaml`

环境变量支持：
- `DB_PASSWORD`: 数据库密码
- `DB_HOST`: 数据库主机
- `DB_PORT`: 数据库端口
- `DB_USER`: 数据库用户
- `DB_NAME`: 数据库名称

## 使用示例

### 创建策略配置

```python
from backend.backtest.models import (
    StrategyConfig, EntryConditions, ExitConditions,
    IndicatorCondition, ComparisonOperator, LogicOperator
)

# 定义开仓条件：EMA7 > EMA25 AND RSI14 < 70
entry_conditions = EntryConditions(
    conditions=[
        IndicatorCondition(
            indicator="EMA7",
            operator=ComparisonOperator.GT,
            value=0,  # 将与EMA25比较
            timeframe="1d"
        ),
        IndicatorCondition(
            indicator="RSI14",
            operator=ComparisonOperator.LT,
            value=70,
            timeframe="1d"
        )
    ],
    logic_operator=LogicOperator.AND
)

# 定义平仓条件：止盈10%或止损5%
exit_conditions = ExitConditions(
    indicator_conditions=[],
    take_profit_pct=0.10,
    stop_loss_pct=0.05,
    logic_operator=LogicOperator.OR
)

# 创建策略配置
strategy = StrategyConfig(
    name="EMA Golden Cross",
    description="EMA7上穿EMA25时做多，止盈10%，止损5%",
    timeframe="1d",
    position_direction="long",
    position_size_type="percentage",
    position_size_value=0.5,  # 50%资金
    entry_conditions=entry_conditions,
    exit_conditions=exit_conditions,
    initial_capital=100000.0
)

# 序列化
strategy_json = strategy.to_json()
print(strategy_json)

# 反序列化
loaded_strategy = StrategyConfig.from_json(strategy_json)
```

## 下一步

待实现的模块：
1. `engine.py` - 回测引擎核心逻辑
2. `indicator_calculator.py` - 技术指标计算
3. `db_connector.py` - 数据库连接和数据读取
4. `metrics_calculator.py` - 性能指标计算
5. `strategy_manager.py` - 策略管理（保存、加载、验证）

## 测试

单元测试位置：`tests/unit/test_backtest_models.py`

运行测试：
```bash
pytest tests/unit/test_backtest_models.py -v
```
