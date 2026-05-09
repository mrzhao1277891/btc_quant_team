# 任务 14 完成总结：实现前端表单数据收集逻辑

## 任务概述

更新 `web/backtest.js` 中的 `collectFormData()` 函数，使其能够收集双向交易策略的所有配置数据，同时保持对旧版单向策略的向后兼容性。

## 实现内容

### 1. 更新 `collectFormData()` 函数

修改了 `web/backtest.js` 中的 `collectFormData()` 函数，实现以下功能：

#### 新增字段收集（双向策略）

1. **做多开仓条件**
   - `long_entry_conditions`: 从 `longEntryConditions` 容器收集条件数组
   - `long_entry_logic`: 从 `longEntryLogic` 下拉框获取逻辑运算符（AND/OR）

2. **做空开仓条件**
   - `short_entry_conditions`: 从 `shortEntryConditions` 容器收集条件数组
   - `short_entry_logic`: 从 `shortEntryLogic` 下拉框获取逻辑运算符（AND/OR）

3. **做多平仓条件**
   - `long_exit_conditions`: 从 `longExitConditions` 容器收集条件数组
   - `long_exit_logic`: 从 `longExitLogic` 下拉框获取逻辑运算符（AND/OR）
   - `long_take_profit_pct`: 从 `longTakeProfitPct` 输入框获取止盈百分比
   - `long_stop_loss_pct`: 从 `longStopLossPct` 输入框获取止损百分比

4. **做空平仓条件**
   - `short_exit_conditions`: 从 `shortExitConditions` 容器收集条件数组
   - `short_exit_logic`: 从 `shortExitLogic` 下拉框获取逻辑运算符（AND/OR）
   - `short_take_profit_pct`: 从 `shortTakeProfitPct` 输入框获取止盈百分比
   - `short_stop_loss_pct`: 从 `shortStopLossPct` 输入框获取止损百分比

#### 向后兼容性

保留了对旧版字段的收集逻辑：

1. **旧版开仓条件**
   - `entry_conditions`: 从 `entryConditions` 容器收集
   - `entry_logic`: 从 `entryLogic` 下拉框获取

2. **旧版平仓条件**
   - `exit_conditions`: 从 `exitConditions` 容器收集
   - `exit_logic`: 从 `exitLogic` 下拉框获取

3. **旧版持仓方向**
   - `position_side`: 从单选框 `input[name="positionSide"]` 获取（如果存在）

4. **旧版止盈止损**
   - `take_profit_pct`: 从 `takeProfitPct` 输入框获取
   - `stop_loss_pct`: 从 `stopLossPct` 输入框获取

### 2. 数据格式处理

- **条件收集**: 使用 `collectConditions()` 函数从各个容器中收集条件数组
- **数值转换**: 使用 `parseFloatOrNull()` 函数处理止盈止损百分比，空值返回 `null`
- **条件判断**: 只有当条件数组长度大于 0 或值不为 `null` 时才添加到数据对象中

### 3. 实现特点

1. **智能收集**: 只收集用户实际配置的字段，避免发送空数据
2. **类型安全**: 正确处理数值类型转换和空值情况
3. **向后兼容**: 同时支持新旧两套字段，不影响现有功能
4. **符合 API 要求**: 数据格式完全符合后端 API 的 `BacktestRequest` 模型

## 测试验证

创建了自动化测试脚本验证功能：

### 测试场景

1. ✅ 基本字段收集（策略名称、时间周期、日期范围等）
2. ✅ 做多开仓条件和逻辑运算符
3. ✅ 做空开仓条件和逻辑运算符
4. ✅ 做多平仓条件、逻辑运算符、止盈止损
5. ✅ 做空平仓条件、逻辑运算符、止盈止损
6. ✅ 杠杆倍数
7. ✅ 旧版字段不会被错误收集

### 测试结果

```
📊 测试结果:
  ✓ 基本字段
  ✓ 做多开仓条件
  ✓ 做多开仓逻辑
  ✓ 做空开仓条件
  ✓ 做空开仓逻辑
  ✓ 做多平仓条件
  ✓ 做多平仓逻辑
  ✓ 做多止盈
  ✓ 做多止损
  ✓ 做空平仓条件
  ✓ 做空平仓逻辑
  ✓ 做空止盈
  ✓ 做空止损
  ✓ 杠杆
  ✓ 旧版字段不存在

✅ 所有测试通过！
```

## 示例数据输出

双向 RSI 策略的数据收集示例：

```json
{
  "strategy_name": "测试策略",
  "timeframe": "1d",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "initial_capital": 10000,
  "position_size": 2000,
  "position_size_type": "fixed",
  "leverage": 5,
  "long_entry_conditions": [
    {
      "indicator": "rsi14",
      "operator": "<",
      "value": 30
    }
  ],
  "long_entry_logic": "AND",
  "short_entry_conditions": [
    {
      "indicator": "rsi14",
      "operator": ">",
      "value": 70
    }
  ],
  "short_entry_logic": "AND",
  "long_exit_conditions": [
    {
      "indicator": "rsi14",
      "operator": ">",
      "value": 70
    }
  ],
  "long_exit_logic": "OR",
  "long_take_profit_pct": 10,
  "long_stop_loss_pct": 5,
  "short_exit_conditions": [
    {
      "indicator": "rsi14",
      "operator": "<",
      "value": 30
    }
  ],
  "short_exit_logic": "OR",
  "short_take_profit_pct": 8,
  "short_stop_loss_pct": 4
}
```

## 文件变更

### 修改的文件

- `web/backtest.js`: 更新 `collectFormData()` 函数

### 变更统计

- 函数重构：1 个
- 新增字段收集：12 个
- 保留旧版字段：6 个
- 代码行数：约 90 行（原 15 行）

## 符合的需求

本任务实现满足以下需求：

- ✅ **需求 4.2**: 收集做多开仓条件配置
- ✅ **需求 4.3**: 收集做空开仓条件配置
- ✅ **需求 4.4**: 收集做多平仓条件配置
- ✅ **需求 4.5**: 收集做空平仓条件配置
- ✅ **需求 7.1-7.5**: 向后兼容性（保留旧版字段收集）
- ✅ **需求 8.1-8.4**: 符合 API 接口要求

## 后续任务

本任务完成后，建议继续执行：

1. **任务 15**: 实现前端表单验证逻辑
   - 验证至少配置了一个方向的开仓条件
   - 验证条件字段的完整性
   - 验证止盈止损百分比为正数

2. **任务 16-17**: 更新策略模板支持双向策略
   - 添加双向策略模板
   - 实现模板加载逻辑

## 注意事项

1. **数据完整性**: 函数会自动过滤空条件和空值，只发送用户实际配置的数据
2. **类型转换**: 所有数值字段都经过正确的类型转换
3. **向后兼容**: 旧版表单仍然可以正常工作，不会影响现有用户
4. **API 对齐**: 数据格式完全符合后端 API 的期望格式

## 总结

任务 14 已成功完成，`collectFormData()` 函数现在能够：

1. ✅ 收集所有双向策略的新字段
2. ✅ 保持对旧版单向策略的向后兼容
3. ✅ 正确处理数据类型和空值
4. ✅ 符合后端 API 的数据格式要求
5. ✅ 通过所有自动化测试验证

前端表单数据收集逻辑已完全就绪，可以支持双向交易策略的配置和提交。
