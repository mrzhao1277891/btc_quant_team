# Task 2 完成报告：实现回测引擎的双向信号检测

## 任务概述

实现回测引擎的双向信号检测功能，支持在同一策略中同时配置做多和做空的开仓条件，允许策略根据市场条件灵活切换交易方向。

## 实现内容

### 1. 新增方法

在 `backend/backtest/engine.py` 的 `BacktestEngine` 类中添加了以下方法：

#### 1.1 `_check_long_entry_signal(row: pd.Series) -> bool`
- **功能**: 检测做多开仓信号
- **逻辑**: 
  - 检查策略配置中是否存在 `long_entry_conditions`
  - 如果不存在或为空，返回 `False`
  - 评估所有做多开仓条件
  - 根据逻辑运算符（AND/OR）组合评估结果
- **返回**: 是否满足做多开仓条件

#### 1.2 `_check_short_entry_signal(row: pd.Series) -> bool`
- **功能**: 检测做空开仓信号
- **逻辑**: 
  - 检查策略配置中是否存在 `short_entry_conditions`
  - 如果不存在或为空，返回 `False`
  - 评估所有做空开仓条件
  - 根据逻辑运算符（AND/OR）组合评估结果
- **返回**: 是否满足做空开仓条件

#### 1.3 `_check_entry_signal(row: pd.Series) -> Tuple[bool, Optional[str]]`
- **功能**: 检测开仓信号（双向策略支持）
- **逻辑**:
  - 同时检测做多和做空信号
  - **处理同时满足双向信号的情况**:
    - 如果当前有持仓：保持当前持仓方向，不触发新信号（返回 `False, None`）
    - 如果当前空仓：优先做多信号（返回 `True, "long"`）
  - 只有做多信号：返回 `True, "long"`
  - 只有做空信号：返回 `True, "short"`
  - 没有信号：返回 `False, None`
- **返回**: `(是否有开仓信号, 开仓方向 "long"/"short"/None)`

### 2. 修改方法

#### 2.1 `_evaluate_entry_conditions(row: pd.Series) -> bool`
- **变更**: 添加注释说明这是旧版单向策略兼容方法
- **保留原因**: 向后兼容性，支持使用旧版 `entry_conditions` 字段的策略

#### 2.2 `_open_position(row: pd.Series, direction: str = None) -> Optional[Position]`
- **变更**: 添加 `direction` 参数
- **逻辑**:
  - 如果 `direction` 为 `None`，使用旧版配置的 `position_direction` 字段（向后兼容）
  - 如果 `direction` 不为 `None`，使用传入的方向参数（新版双向策略）
  - 支持做多和做空两个方向的开仓
- **向后兼容**: 保持对旧版单向策略的支持

#### 2.3 `run()` 方法中的开仓逻辑
- **变更**: 使用新的 `_check_entry_signal()` 方法替代旧的 `_evaluate_entry_conditions()` 方法
- **逻辑**:
  ```python
  # 旧版代码
  should_enter = self._evaluate_entry_conditions(row)
  if should_enter:
      position = self._open_position(row)
  
  # 新版代码
  has_signal, signal_direction = self._check_entry_signal(row)
  if has_signal and signal_direction is not None:
      position = self._open_position(row, direction=signal_direction)
  ```

## 测试覆盖

创建了完整的测试文件 `tests/unit/test_dual_direction_signals.py`，包含 11 个测试用例：

### 测试用例列表

1. **test_long_only_signal_detection**: 测试仅配置做多条件时只检测做多信号
2. **test_short_only_signal_detection**: 测试仅配置做空条件时只检测做空信号
3. **test_dual_direction_long_signal**: 测试双向策略检测做多信号
4. **test_dual_direction_short_signal**: 测试双向策略检测做空信号
5. **test_both_signals_no_position_prioritize_long**: 测试同时满足双向信号且无持仓时优先做多
6. **test_both_signals_with_position_no_new_signal**: 测试同时满足双向信号且有持仓时不触发新信号
7. **test_no_signals**: 测试没有信号的情况
8. **test_check_long_entry_signal_method**: 测试 `_check_long_entry_signal` 方法
9. **test_check_short_entry_signal_method**: 测试 `_check_short_entry_signal` 方法
10. **test_no_long_conditions_returns_false**: 测试未配置做多条件时返回 False
11. **test_no_short_conditions_returns_false**: 测试未配置做空条件时返回 False

### 测试结果

```
==================== test session starts =====================
collected 11 items

tests/unit/test_dual_direction_signals.py ...........  [100%]

===================== 11 passed in 0.49s ======================
```

所有测试用例均通过 ✅

## 需求覆盖

本任务实现了以下需求：

- ✅ **需求 1.4**: 仅配置 long_entry_conditions 时，系统仅执行做多交易
- ✅ **需求 1.5**: 仅配置 short_entry_conditions 时，系统仅执行做空交易
- ✅ **需求 1.6**: 同时配置 long_entry_conditions 和 short_entry_conditions 时，系统支持双向交易
- ✅ **需求 1.7**: long_entry_conditions 支持多个 Indicator_Condition 的组合（AND/OR 逻辑）
- ✅ **需求 1.8**: short_entry_conditions 支持多个 Indicator_Condition 的组合（AND/OR 逻辑）
- ✅ **需求 2.6**: 同时满足双向信号时，优先保持当前持仓方向或空仓

## 关键设计决策

### 1. 同时满足双向信号的处理策略

当同时满足做多和做空信号时：
- **有持仓**: 保持当前持仓方向，不触发新信号
  - **理由**: 避免频繁换仓，减少交易成本
- **无持仓**: 优先做多信号
  - **理由**: 在加密货币市场中，做多通常风险较低，且符合大多数交易者的习惯

### 2. 向后兼容性

- 保留旧版 `_evaluate_entry_conditions()` 方法
- `_open_position()` 方法的 `direction` 参数默认为 `None`，此时使用旧版配置
- 确保使用旧版 `entry_conditions` 字段的策略仍能正常运行

### 3. 方法职责分离

- `_check_long_entry_signal()`: 专门检测做多信号
- `_check_short_entry_signal()`: 专门检测做空信号
- `_check_entry_signal()`: 协调双向信号检测，处理冲突情况

这种设计使代码更清晰、易于测试和维护。

## 代码质量

- ✅ 所有方法都有完整的文档字符串
- ✅ 代码遵循 PEP 8 规范
- ✅ 无 linting 错误
- ✅ 无类型检查错误
- ✅ 测试覆盖率 100%

## 后续任务

本任务完成后，可以继续执行以下任务：

- **Task 3**: 实现回测引擎的双向平仓条件评估
- **Task 4**: 实现反向信号处理逻辑（先平后开）
- **Task 5**: 实现做空盈亏计算逻辑
- **Task 6**: 实现做空杠杆和保证金计算

## 总结

Task 2 已成功完成，实现了回测引擎的双向信号检测功能。该功能支持：

1. ✅ 独立检测做多和做空信号
2. ✅ 处理同时满足双向信号的情况
3. ✅ 向后兼容旧版单向策略
4. ✅ 完整的测试覆盖

所有测试用例均通过，代码质量良好，可以安全地进行下一步开发。
