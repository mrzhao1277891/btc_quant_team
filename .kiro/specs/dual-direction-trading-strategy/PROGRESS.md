# 双向交易策略实现进度

## ✅ 已完成的任务

### 任务 1: 扩展 StrategyConfig 数据模型支持双向条件 ✅
**状态**: 完成
**文件**: `backend/backtest/models.py`

**实现内容**:
- ✅ 添加了 4 个新字段：
  - `long_entry_conditions: Optional[EntryConditions]`
  - `short_entry_conditions: Optional[EntryConditions]`
  - `long_exit_conditions: Optional[ExitConditions]`
  - `short_exit_conditions: Optional[ExitConditions]`
- ✅ 保留旧版字段用于向后兼容
- ✅ 实现了 `from_dict()` 方法中的兼容性转换逻辑
- ✅ 添加了验证逻辑：至少配置一个方向的开仓条件
- ✅ 创建了 9 个单元测试，全部通过

### 任务 2: 实现回测引擎的双向信号检测 ✅
**状态**: 完成
**文件**: `backend/backtest/engine.py`

**实现内容**:
- ✅ 添加了 `_check_long_entry_signal()` 方法
- ✅ 添加了 `_check_short_entry_signal()` 方法
- ✅ 实现了 `_check_entry_signal()` 方法（返回信号和方向）
- ✅ 修改了 `_open_position()` 方法支持 direction 参数
- ✅ 更新了 `run()` 方法使用新的信号检测逻辑
- ✅ 处理同时满足双向信号的情况（有持仓时保持方向，无持仓时优先做多）
- ✅ 创建了 11 个单元测试，全部通过

## 🔄 部分完成的任务

### 任务 3: 实现回测引擎的双向平仓条件评估 🔄
**状态**: 部分完成（代码已存在但需要验证）
**文件**: `backend/backtest/engine.py`

**已实现**:
- ✅ `_check_long_exit_signal()` 方法已存在
- ✅ `_check_short_exit_signal()` 方法已存在
- ✅ `_check_exit_signal()` 方法已更新

**需要验证**:
- ⚠️ 确认方法正确调用对应方向的平仓条件
- ⚠️ 确认支持指标条件、止盈止损的组合评估

### 任务 4: 实现反向信号处理逻辑（先平后开） ⏳
**状态**: 待实现
**文件**: `backend/backtest/engine.py`

**需要实现**:
- ❌ 在 `run()` 方法中添加反向信号检测逻辑
- ❌ 持有多仓时出现做空信号 → 先平多仓再开空仓
- ❌ 持有空仓时出现做多信号 → 先平空仓再开多仓
- ❌ 平仓原因记录为 "reverse_signal"
- ❌ 处理平仓后资金不足的情况

**实现方案**:
```python
# 在 run() 方法的持仓评估部分添加：
if self.current_position is not None:
    # 1. 先检查平仓条件
    should_exit, exit_reason = self._check_exit_signal(row, self.current_position)
    
    if should_exit:
        trade = self._close_position(self.current_position, row, exit_reason)
        self.trades.append(trade)
        self.current_position = None
    else:
        # 2. 检查反向信号
        has_signal, signal_direction = self._check_entry_signal(row)
        
        if has_signal and signal_direction is not None:
            # 如果信号方向与当前持仓方向相反
            if signal_direction != self.current_position.direction:
                # 先平仓
                trade = self._close_position(self.current_position, row, "reverse_signal")
                self.trades.append(trade)
                self.current_position = None
                
                # 再开新仓
                position = self._open_position(row, direction=signal_direction)
                if position is not None:
                    self.current_position = position
```

### 任务 5: 实现做空盈亏计算逻辑 ✅
**状态**: 已完成（代码已存在）
**文件**: `backend/backtest/engine.py`

**已实现**:
- ✅ `_calculate_pnl()` 方法已支持做空盈亏计算
- ✅ 做空公式：`(entry_price - current_price) * position_size`
- ✅ 盈亏百分比：`pnl_amount / entry_capital * 100`

### 任务 6: 实现做空杠杆和保证金计算 ✅
**状态**: 已完成（代码已存在）
**文件**: `backend/backtest/engine.py`

**已实现**:
- ✅ `_open_position()` 方法已支持做空杠杆计算
- ✅ 保证金公式：`position_value / leverage`
- ✅ 持仓数量：`position_value / entry_price`
- ✅ 资金检查和返还逻辑

## ⏳ 待完成的任务

### 任务 7: 扩展 API BacktestRequest 模型支持双向条件
**文件**: `backend/backtest/api.py`

**需要添加的字段**:
```python
class BacktestRequest(BaseModel):
    # ... 现有字段 ...
    
    # 新增双向条件字段
    long_entry_conditions: Optional[List[IndicatorConditionRequest]] = None
    short_entry_conditions: Optional[List[IndicatorConditionRequest]] = None
    long_exit_conditions: Optional[List[IndicatorConditionRequest]] = None
    short_exit_conditions: Optional[List[IndicatorConditionRequest]] = None
    
    long_entry_logic: Optional[str] = "AND"
    short_entry_logic: Optional[str] = "AND"
    long_exit_logic: Optional[str] = "OR"
    short_exit_logic: Optional[str] = "OR"
    
    long_take_profit_pct: Optional[float] = None
    long_stop_loss_pct: Optional[float] = None
    short_take_profit_pct: Optional[float] = None
    short_stop_loss_pct: Optional[float] = None
```

### 任务 8: 实现 API 请求转换逻辑支持双向策略
**文件**: `backend/backtest/api.py`

**需要修改**: `convert_request_to_strategy_config()` 函数
- 添加双向条件的转换逻辑
- 保持对旧版字段的兼容性
- 添加验证逻辑

### 任务 9-17: 前端 UI 改造
**文件**: `web/backtest.html`, `web/backtest.js`

**需要实现**:
- 移除"交易方向"单选框
- 添加 4 个配置区域（做多/做空 × 开仓/平仓）
- 实现表单数据收集和验证
- 更新策略模板

## 📊 总体进度

- **已完成**: 2/25 任务 (8%)
- **部分完成**: 4/25 任务 (16%)
- **待完成**: 19/25 任务 (76%)

## 🎯 下一步行动

### 立即需要完成（核心功能）:
1. **任务 4**: 添加反向信号处理逻辑（约 20 行代码）
2. **任务 7**: 扩展 API 模型（约 15 行代码）
3. **任务 8**: 修改 API 转换逻辑（约 50 行代码）

### 然后完成（前端功能）:
4. **任务 9-13**: UI 改造（约 200 行代码）
5. **任务 14-15**: 表单逻辑（约 100 行代码）
6. **任务 16-17**: 策略模板（约 50 行代码）

### 最后完成（测试和文档）:
7. **任务 18-23**: 测试用例
8. **任务 24**: 文档更新
9. **任务 25**: 最终检查

## 💡 快速完成方案

如果需要快速完成基本功能，可以按以下顺序：

1. **完成任务 4**（反向信号处理）- 这是核心逻辑
2. **完成任务 7-8**（API 扩展）- 连接前后端
3. **简化前端**（只添加基本的双向配置，不做完整 UI 改造）
4. **手动测试**（跳过自动化测试，直接运行回测验证）

这样可以在 1-2 小时内完成一个可用的 MVP 版本。

## 📝 注意事项

1. 所有代码修改都需要保持向后兼容性
2. 做空盈亏计算需要特别注意符号（价格下跌时盈利为正）
3. 反向信号处理必须在同一时间步内完成（先平后开）
4. 前端 UI 需要清晰区分做多和做空配置区域
