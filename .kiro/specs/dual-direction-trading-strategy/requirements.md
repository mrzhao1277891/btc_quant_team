# 需求文档：双向交易策略

## 简介

本文档定义了双向交易策略功能的需求。该功能扩展现有回测系统，支持在同一策略中同时配置做多和做空的开仓条件，允许策略根据市场条件灵活切换交易方向。当前系统仅支持单向交易（要么只做多，要么只做空），新功能将使策略能够在不同市场条件下自动选择最优交易方向。

## 术语表

- **Backtest_System**: 回测系统，执行策略回测并生成性能报告的核心系统
- **Strategy_Config**: 策略配置对象，包含开仓条件、平仓条件、持仓设置等所有策略参数
- **Long_Position**: 做多仓位，预期价格上涨时盈利的持仓
- **Short_Position**: 做空仓位，预期价格下跌时盈利的持仓
- **Entry_Condition**: 开仓条件，基于技术指标的触发条件，满足时开仓
- **Exit_Condition**: 平仓条件，基于技术指标或止盈止损的触发条件，满足时平仓
- **Position_Direction**: 持仓方向，可以是做多（long）或做空（short）
- **Backtest_Engine**: 回测引擎，负责执行策略逻辑、管理持仓和记录交易的核心组件
- **Trade_Record**: 交易记录，包含开仓时间、平仓时间、盈亏等信息的单笔交易数据
- **UI_Config_Panel**: 前端配置面板，用户配置策略参数的界面组件
- **Indicator_Condition**: 指标条件，包含指标名称、比较运算符和目标值的条件对象
- **Leverage**: 杠杆倍数，放大交易仓位的倍数，用于计算实际仓位价值

## 需求

### 需求 1: 双向开仓条件配置

**用户故事:** 作为量化交易员，我希望能够分别配置做多和做空的开仓条件，以便策略能够根据不同市场条件自动选择交易方向。

#### 验收标准

1. THE Strategy_Config SHALL 包含独立的 long_entry_conditions 字段用于存储做多开仓条件
2. THE Strategy_Config SHALL 包含独立的 short_entry_conditions 字段用于存储做空开仓条件
3. WHEN long_entry_conditions 和 short_entry_conditions 都为空时，THE Backtest_System SHALL 返回配置错误
4. WHEN 仅配置 long_entry_conditions 时，THE Backtest_System SHALL 仅执行做多交易
5. WHEN 仅配置 short_entry_conditions 时，THE Backtest_System SHALL 仅执行做空交易
6. WHEN 同时配置 long_entry_conditions 和 short_entry_conditions 时，THE Backtest_System SHALL 支持双向交易
7. THE long_entry_conditions SHALL 支持多个 Indicator_Condition 的组合（AND/OR 逻辑）
8. THE short_entry_conditions SHALL 支持多个 Indicator_Condition 的组合（AND/OR 逻辑）

### 需求 2: 单边持仓规则

**用户故事:** 作为量化交易员，我希望系统确保同一时间只持有一个方向的仓位，以便避免对冲风险和简化持仓管理。

#### 验收标准

1. THE Backtest_Engine SHALL 在任意时刻最多持有一个 Long_Position 或一个 Short_Position
2. WHEN 持有 Long_Position 且 short_entry_conditions 满足时，THE Backtest_Engine SHALL 先平掉 Long_Position 再开 Short_Position
3. WHEN 持有 Short_Position 且 long_entry_conditions 满足时，THE Backtest_Engine SHALL 先平掉 Short_Position 再开 Long_Position
4. WHEN 平掉当前仓位后资金不足以开新仓时，THE Backtest_Engine SHALL 记录警告并保持空仓状态
5. THE Trade_Record SHALL 记录因反向信号触发的平仓原因为 "reverse_signal"
6. WHEN 同时满足 long_entry_conditions 和 short_entry_conditions 时，THE Backtest_Engine SHALL 优先保持当前持仓方向

### 需求 3: 双向平仓条件配置

**用户故事:** 作为量化交易员，我希望能够为做多和做空分别配置平仓条件，以便针对不同方向的仓位使用不同的退出策略。

#### 验收标准

1. THE Strategy_Config SHALL 包含独立的 long_exit_conditions 字段用于存储做多平仓条件
2. THE Strategy_Config SHALL 包含独立的 short_exit_conditions 字段用于存储做空平仓条件
3. WHEN 持有 Long_Position 时，THE Backtest_Engine SHALL 仅评估 long_exit_conditions
4. WHEN 持有 Short_Position 时，THE Backtest_Engine SHALL 仅评估 short_exit_conditions
5. THE long_exit_conditions SHALL 支持指标条件、止盈百分比、止损百分比的组合
6. THE short_exit_conditions SHALL 支持指标条件、止盈百分比、止损百分比的组合
7. WHEN long_exit_conditions 为空时，THE Backtest_Engine SHALL 仅依赖反向信号或回测结束来平多仓
8. WHEN short_exit_conditions 为空时，THE Backtest_Engine SHALL 仅依赖反向信号或回测结束来平空仓

### 需求 4: 前端 UI 双向配置支持

**用户故事:** 作为量化交易员，我希望在前端界面中能够直观地配置双向交易策略，以便快速创建和测试双向策略。

#### 验收标准

1. THE UI_Config_Panel SHALL 移除现有的单选"交易方向"控件（做多/做空单选框）
2. THE UI_Config_Panel SHALL 添加"做多开仓条件"配置区域，支持添加多个 Indicator_Condition
3. THE UI_Config_Panel SHALL 添加"做空开仓条件"配置区域，支持添加多个 Indicator_Condition
4. THE UI_Config_Panel SHALL 添加"做多平仓条件"配置区域，支持配置指标条件和止盈止损
5. THE UI_Config_Panel SHALL 添加"做空平仓条件"配置区域，支持配置指标条件和止盈止损
6. WHEN 用户未配置任何开仓条件时，THE UI_Config_Panel SHALL 在提交前显示验证错误
7. THE UI_Config_Panel SHALL 为每个条件区域提供"添加条件"和"删除条件"按钮
8. THE UI_Config_Panel SHALL 支持为做多和做空分别设置逻辑运算符（AND/OR）

### 需求 5: 做空盈亏计算

**用户故事:** 作为量化交易员，我希望系统能够正确计算做空交易的盈亏，以便准确评估做空策略的表现。

#### 验收标准

1. WHEN 持有 Short_Position 且当前价格低于开仓价格时，THE Backtest_Engine SHALL 计算正盈利
2. WHEN 持有 Short_Position 且当前价格高于开仓价格时，THE Backtest_Engine SHALL 计算负盈利（亏损）
3. THE Backtest_Engine SHALL 使用公式 `(entry_price - current_price) * position_size` 计算做空盈亏金额
4. THE Backtest_Engine SHALL 使用公式 `pnl_amount / entry_capital * 100` 计算做空盈亏百分比
5. WHEN 平仓 Short_Position 时，THE Trade_Record SHALL 记录正确的 profit_loss 和 profit_loss_pct
6. THE Backtest_Engine SHALL 在平仓后正确更新账户资金（返还保证金 + 盈亏）

### 需求 6: 做空杠杆支持

**用户故事:** 作为量化交易员，我希望做空交易也能使用杠杆，以便放大做空策略的收益。

#### 验收标准

1. WHEN 开 Short_Position 时，THE Backtest_Engine SHALL 使用 Strategy_Config 中的 Leverage 计算保证金
2. THE Backtest_Engine SHALL 使用公式 `position_value / leverage` 计算做空所需保证金
3. WHEN 做空保证金大于可用资金时，THE Backtest_Engine SHALL 跳过做空信号并记录警告
4. THE Backtest_Engine SHALL 使用公式 `position_value / entry_price` 计算做空持仓数量
5. WHEN 平仓 Short_Position 时，THE Backtest_Engine SHALL 返还保证金并加上盈亏金额
6. THE Trade_Record SHALL 记录做空交易使用的 entry_capital（保证金金额）

### 需求 7: 向后兼容性

**用户故事:** 作为系统维护者，我希望新功能能够兼容现有的单向策略配置，以便不影响已有策略的运行。

#### 验收标准

1. WHEN Strategy_Config 包含旧版 position_direction 字段（值为 "long"）时，THE Backtest_System SHALL 将其转换为 long_entry_conditions
2. WHEN Strategy_Config 包含旧版 position_direction 字段（值为 "short"）时，THE Backtest_System SHALL 将其转换为 short_entry_conditions
3. WHEN Strategy_Config 同时包含旧版和新版字段时，THE Backtest_System SHALL 优先使用新版字段
4. THE Backtest_System SHALL 继续支持旧版 entry_conditions 字段，并根据 position_direction 映射到对应方向
5. THE Backtest_System SHALL 继续支持旧版 exit_conditions 字段，并复制到 long_exit_conditions 和 short_exit_conditions
6. WHEN 使用旧版配置时，THE Backtest_System SHALL 在日志中记录兼容性警告

### 需求 8: API 接口扩展

**用户故事:** 作为前端开发者，我希望 API 接口能够支持双向策略配置，以便前端能够提交和接收双向策略数据。

#### 验收标准

1. THE BacktestRequest SHALL 添加可选的 long_entry_conditions 字段（List[IndicatorConditionRequest]）
2. THE BacktestRequest SHALL 添加可选的 short_entry_conditions 字段（List[IndicatorConditionRequest]）
3. THE BacktestRequest SHALL 添加可选的 long_exit_conditions 字段（List[IndicatorConditionRequest]）
4. THE BacktestRequest SHALL 添加可选的 short_exit_conditions 字段（List[IndicatorConditionRequest]）
5. WHEN 接收到包含双向条件的请求时，THE API SHALL 正确转换为 Strategy_Config 对象
6. WHEN 接收到仅包含旧版字段的请求时，THE API SHALL 继续支持并正确处理
7. THE API SHALL 在响应中返回使用的策略类型（单向或双向）
8. THE API SHALL 验证至少配置了一个方向的开仓条件

## 示例策略配置

### 双向 RSI 策略示例

```json
{
  "strategy_name": "双向RSI策略",
  "timeframe": "1d",
  "initial_capital": 10000,
  "position_size": 2000,
  "leverage": 5,
  "long_entry_conditions": [
    {"indicator": "rsi14", "operator": "<", "value": 30},
    {"indicator": "close", "operator": ">", "value": "ema50"}
  ],
  "long_entry_logic": "AND",
  "long_exit_conditions": [
    {"indicator": "rsi14", "operator": ">", "value": 70}
  ],
  "long_exit_logic": "OR",
  "long_take_profit_pct": 10,
  "long_stop_loss_pct": 5,
  "short_entry_conditions": [
    {"indicator": "rsi14", "operator": ">", "value": 70},
    {"indicator": "close", "operator": "<", "value": "ema50"}
  ],
  "short_entry_logic": "AND",
  "short_exit_conditions": [
    {"indicator": "rsi14", "operator": "<", "value": 30}
  ],
  "short_exit_logic": "OR",
  "short_take_profit_pct": 10,
  "short_stop_loss_pct": 5
}
```

## 数据模型变更

### Strategy_Config 扩展字段

- `long_entry_conditions: Optional[EntryConditions]` - 做多开仓条件
- `short_entry_conditions: Optional[EntryConditions]` - 做空开仓条件
- `long_exit_conditions: Optional[ExitConditions]` - 做多平仓条件
- `short_exit_conditions: Optional[ExitConditions]` - 做空平仓条件

### 保留字段（向后兼容）

- `position_direction: Optional[Literal["long", "short"]]` - 旧版持仓方向（已弃用）
- `entry_conditions: Optional[EntryConditions]` - 旧版开仓条件（已弃用）
- `exit_conditions: Optional[ExitConditions]` - 旧版平仓条件（已弃用）

## 技术约束

1. 使用现有的 `BacktestEngine`、`StrategyConfig`、`TradeRecord` 模型作为基础
2. 保持现有 API 接口的向后兼容性
3. 前端使用 vanilla JavaScript，不引入新框架或库
4. 做空交易的盈亏计算必须考虑杠杆效应
5. 反向信号触发的平仓必须在同一时间步内完成（先平后开）
6. 所有数值计算使用 Python float 类型，避免 Decimal 类型问题

## 非功能性需求

1. **性能**: 双向策略的回测执行时间不应超过单向策略的 1.5 倍
2. **可用性**: UI 配置界面应清晰区分做多和做空配置区域
3. **可维护性**: 代码应保持清晰的注释，说明双向逻辑的实现
4. **测试性**: 所有核心逻辑应有单元测试覆盖，包括边界情况

## 验收测试场景

### 场景 1: 纯做多策略（向后兼容）
- 配置: 仅设置 long_entry_conditions
- 预期: 系统仅执行做多交易，行为与旧版一致

### 场景 2: 纯做空策略（向后兼容）
- 配置: 仅设置 short_entry_conditions
- 预期: 系统仅执行做空交易，行为与旧版一致

### 场景 3: 双向 RSI 策略
- 配置: RSI < 30 做多，RSI > 70 做空
- 预期: 系统根据 RSI 值自动切换交易方向

### 场景 4: 反向信号平仓
- 场景: 持有多仓时出现做空信号
- 预期: 先平多仓，再开空仓，记录平仓原因为 "reverse_signal"

### 场景 5: 做空盈亏计算
- 场景: 以 50000 价格开空仓，以 48000 价格平仓
- 预期: 盈利 = (50000 - 48000) × 持仓数量

### 场景 6: 杠杆做空
- 场景: 2000 本金，5 倍杠杆做空
- 预期: 实际仓位 10000，保证金 2000，盈亏按 10000 仓位计算
