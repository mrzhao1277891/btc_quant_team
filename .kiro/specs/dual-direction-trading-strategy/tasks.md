# 实现计划：双向交易策略

## 概述

本实现计划将双向交易策略功能分解为离散的编码任务。该功能扩展现有回测系统，支持在同一策略中同时配置做多和做空的开仓条件，允许策略根据市场条件灵活切换交易方向。

**技术栈**: Python 3.8+, FastAPI, Pydantic, vanilla JavaScript

**核心文件**:
- `backend/backtest/models.py` - 数据模型扩展
- `backend/backtest/engine.py` - 回测引擎改造
- `backend/backtest/api.py` - API 接口扩展
- `web/backtest.html` - 前端 UI 改造
- `web/backtest.js` - 前端逻辑改造

## 任务

- [x] 1. 扩展 StrategyConfig 数据模型支持双向条件
  - 在 `backend/backtest/models.py` 的 `StrategyConfig` 类中添加 4 个新字段
  - 添加 `long_entry_conditions: Optional[EntryConditions]` 字段
  - 添加 `short_entry_conditions: Optional[EntryConditions]` 字段
  - 添加 `long_exit_conditions: Optional[ExitConditions]` 字段
  - 添加 `short_exit_conditions: Optional[ExitConditions]` 字段
  - 保留旧版字段 `position_direction`, `entry_conditions`, `exit_conditions` 用于向后兼容
  - 添加 `from_dict()` 方法中的兼容性转换逻辑（旧版字段映射到新版字段）
  - 添加验证逻辑：至少配置一个方向的开仓条件
  - _需求: 1.1, 1.2, 3.1, 3.2, 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 2. 实现回测引擎的双向信号检测
  - 在 `backend/backtest/engine.py` 的 `BacktestEngine` 类中添加 `_check_long_entry_signal()` 方法
  - 在 `backend/backtest/engine.py` 的 `BacktestEngine` 类中添加 `_check_short_entry_signal()` 方法
  - 修改 `_check_entry_signal()` 方法，根据策略配置调用对应的信号检测方法
  - 实现做多信号检测逻辑（评估 `long_entry_conditions`）
  - 实现做空信号检测逻辑（评估 `short_entry_conditions`）
  - 处理同时满足双向信号的情况（保持当前持仓方向或空仓）
  - _需求: 1.4, 1.5, 1.6, 1.7, 1.8, 2.6_

- [x] 3. 实现回测引擎的双向平仓条件评估
  - 在 `backend/backtest/engine.py` 的 `BacktestEngine` 类中添加 `_check_long_exit_signal()` 方法
  - 在 `backend/backtest/engine.py` 的 `BacktestEngine` 类中添加 `_check_short_exit_signal()` 方法
  - 修改 `_check_exit_signal()` 方法，根据当前持仓方向调用对应的平仓检测方法
  - 实现做多平仓条件评估（评估 `long_exit_conditions`）
  - 实现做空平仓条件评估（评估 `short_exit_conditions`）
  - 支持指标条件、止盈百分比、止损百分比的组合评估
  - _需求: 3.3, 3.4, 3.5, 3.6, 3.7, 3.8_

- [x] 4. 实现反向信号处理逻辑（先平后开）
  - 在 `backend/backtest/engine.py` 的 `run()` 方法中添加反向信号检测逻辑
  - 当持有多仓且出现做空信号时，先调用 `_close_position()` 平多仓，再调用 `_open_position()` 开空仓
  - 当持有空仓且出现做多信号时，先调用 `_close_position()` 平空仓，再调用 `_open_position()` 开多仓
  - 在 `_close_position()` 方法中添加 "reverse_signal" 平仓原因
  - 处理平仓后资金不足以开新仓的情况（记录警告，保持空仓）
  - 确保反向信号处理在同一时间步内完成
  - _需求: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 5. 实现做空盈亏计算逻辑
  - 修改 `backend/backtest/engine.py` 的 `_calculate_pnl()` 方法，支持做空盈亏计算
  - 实现做空盈亏公式：`(entry_price - current_price) * position_size`
  - 实现做空盈亏百分比公式：`pnl_amount / entry_capital * 100`
  - 在 `_close_position()` 方法中根据持仓方向选择正确的盈亏计算方式
  - 确保做空盈利时（价格下跌）返回正值，做空亏损时（价格上涨）返回负值
  - 更新 `TradeRecord` 记录正确的 `profit_loss` 和 `profit_loss_pct`
  - _需求: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

- [x] 6. 实现做空杠杆和保证金计算
  - 修改 `backend/backtest/engine.py` 的 `_open_position()` 方法，支持做空保证金计算
  - 实现做空保证金公式：`position_value / leverage`
  - 实现做空持仓数量公式：`position_value / entry_price`
  - 在开空仓前检查保证金是否充足（保证金 <= 可用资金）
  - 在 `_close_position()` 方法中正确返还做空保证金并加上盈亏
  - 确保 `TradeRecord` 记录做空交易的 `entry_capital`（保证金金额）
  - _需求: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

- [x] 7. 扩展 API BacktestRequest 模型支持双向条件
  - 在 `backend/backtest/api.py` 的 `BacktestRequest` 类中添加 4 个可选字段
  - 添加 `long_entry_conditions: Optional[List[IndicatorConditionRequest]]` 字段
  - 添加 `short_entry_conditions: Optional[List[IndicatorConditionRequest]]` 字段
  - 添加 `long_exit_conditions: Optional[List[IndicatorConditionRequest]]` 字段
  - 添加 `short_exit_conditions: Optional[List[IndicatorConditionRequest]]` 字段
  - 添加 `long_entry_logic: Optional[str]` 和 `short_entry_logic: Optional[str]` 字段
  - 添加 `long_exit_logic: Optional[str]` 和 `short_exit_logic: Optional[str]` 字段
  - 添加 `long_take_profit_pct`, `long_stop_loss_pct`, `short_take_profit_pct`, `short_stop_loss_pct` 字段
  - _需求: 8.1, 8.2, 8.3, 8.4_

- [x] 8. 实现 API 请求转换逻辑支持双向策略
  - 修改 `backend/backtest/api.py` 的 `convert_request_to_strategy_config()` 函数
  - 添加双向条件的转换逻辑（将 `long_entry_conditions` 转换为 `EntryConditions` 对象）
  - 添加双向平仓条件的转换逻辑（包含指标条件和止盈止损）
  - 保持对旧版字段的兼容性处理（`position_side`, `entry_conditions`, `exit_conditions`）
  - 添加验证逻辑：至少配置一个方向的开仓条件
  - 在响应中添加策略类型标识（单向或双向）
  - _需求: 8.5, 8.6, 8.7, 8.8_

- [x] 9. 改造前端 UI 移除交易方向单选框
  - 在 `web/backtest.html` 中移除现有的"交易方向"单选框（`<input type="radio" name="positionSide">`）
  - 移除相关的 label 和容器元素
  - 更新表单布局，为新的四个配置区域预留空间
  - _需求: 4.1_

- [x] 10. 添加前端 UI 做多开仓条件配置区域
  - 在 `web/backtest.html` 中添加"做多开仓条件"配置区域
  - 添加标题 `<h3>做多开仓条件</h3>`
  - 添加条件容器 `<div id="longEntryConditions"></div>`
  - 添加"添加条件"按钮 `<button onclick="addLongEntryCondition()">添加做多开仓条件</button>`
  - 添加逻辑运算符选择 `<select id="longEntryLogic"><option>AND</option><option>OR</option></select>`
  - 在 `web/backtest.js` 中实现 `addLongEntryCondition()` 函数
  - 实现条件删除功能
  - _需求: 4.2, 4.7, 4.8_

- [x] 11. 添加前端 UI 做空开仓条件配置区域
  - 在 `web/backtest.html` 中添加"做空开仓条件"配置区域
  - 添加标题 `<h3>做空开仓条件</h3>`
  - 添加条件容器 `<div id="shortEntryConditions"></div>`
  - 添加"添加条件"按钮 `<button onclick="addShortEntryCondition()">添加做空开仓条件</button>`
  - 添加逻辑运算符选择 `<select id="shortEntryLogic"><option>AND</option><option>OR</option></select>`
  - 在 `web/backtest.js` 中实现 `addShortEntryCondition()` 函数
  - 实现条件删除功能
  - _需求: 4.3, 4.7, 4.8_

- [x] 12. 添加前端 UI 做多平仓条件配置区域
  - 在 `web/backtest.html` 中添加"做多平仓条件"配置区域
  - 添加标题 `<h3>做多平仓条件</h3>`
  - 添加条件容器 `<div id="longExitConditions"></div>`
  - 添加"添加条件"按钮 `<button onclick="addLongExitCondition()">添加做多平仓条件</button>`
  - 添加止盈止损输入框 `<input id="longTakeProfitPct">` 和 `<input id="longStopLossPct">`
  - 添加逻辑运算符选择 `<select id="longExitLogic"><option>AND</option><option>OR</option></select>`
  - 在 `web/backtest.js` 中实现 `addLongExitCondition()` 函数
  - _需求: 4.4, 4.7, 4.8_

- [x] 13. 添加前端 UI 做空平仓条件配置区域
  - 在 `web/backtest.html` 中添加"做空平仓条件"配置区域
  - 添加标题 `<h3>做空平仓条件</h3>`
  - 添加条件容器 `<div id="shortExitConditions"></div>`
  - 添加"添加条件"按钮 `<button onclick="addShortExitCondition()">添加做空平仓条件</button>`
  - 添加止盈止损输入框 `<input id="shortTakeProfitPct">` 和 `<input id="shortStopLossPct">`
  - 添加逻辑运算符选择 `<select id="shortExitLogic"><option>AND</option><option>OR</option></select>`
  - 在 `web/backtest.js` 中实现 `addShortExitCondition()` 函数
  - _需求: 4.5, 4.7, 4.8_

- [x] 14. 实现前端表单数据收集逻辑
  - 修改 `web/backtest.js` 的 `collectFormData()` 函数
  - 收集做多开仓条件数据（`long_entry_conditions`, `long_entry_logic`）
  - 收集做空开仓条件数据（`short_entry_conditions`, `short_entry_logic`）
  - 收集做多平仓条件数据（`long_exit_conditions`, `long_exit_logic`, `long_take_profit_pct`, `long_stop_loss_pct`）
  - 收集做空平仓条件数据（`short_exit_conditions`, `short_exit_logic`, `short_take_profit_pct`, `short_stop_loss_pct`）
  - 移除旧版 `position_side` 字段的收集逻辑
  - _需求: 4.2, 4.3, 4.4, 4.5_

- [x] 15. 实现前端表单验证逻辑
  - 修改 `web/backtest.js` 的 `validateForm()` 函数
  - 验证至少配置了一个方向的开仓条件（`long_entry_conditions` 或 `short_entry_conditions` 不为空）
  - 如果两个方向都未配置开仓条件，显示错误提示
  - 验证每个条件的指标、运算符、值都已填写
  - 验证止盈止损百分比为正数
  - _需求: 4.6, 8.8_

- [x] 16. 更新策略模板支持双向策略
  - 修改 `backend/backtest/api.py` 的 `get_strategy_templates()` 函数
  - 添加双向 RSI 策略模板（RSI < 30 做多，RSI > 70 做空）
  - 添加双向布林带策略模板（突破上轨做多，突破下轨做空）
  - 保留现有单向策略模板用于向后兼容
  - 在模板中包含 `long_entry_conditions`, `short_entry_conditions` 等新字段
  - _需求: 1.4, 1.5, 1.6_

- [x] 17. 实现前端模板加载逻辑支持双向策略
  - 修改 `web/backtest.js` 的 `loadTemplate()` 函数
  - 支持加载双向策略模板（填充四个配置区域）
  - 支持加载单向策略模板（仅填充对应方向的配置区域）
  - 清空所有条件容器后再加载新模板
  - 正确设置逻辑运算符和止盈止损值
  - _需求: 4.2, 4.3, 4.4, 4.5_

- [x] 18. 添加单元测试：双向信号检测
  - 创建测试文件 `tests/test_dual_direction_signals.py`
  - 测试仅配置做多条件时只检测做多信号
  - 测试仅配置做空条件时只检测做空信号
  - 测试同时配置双向条件时检测两个方向的信号
  - 测试同时满足双向信号时的处理逻辑
  - _需求: 1.4, 1.5, 1.6, 2.6_

- [x] 19. 添加单元测试：反向信号处理
  - 在 `tests/test_dual_direction_signals.py` 中添加反向信号测试
  - 测试持有多仓时出现做空信号的处理（先平后开）
  - 测试持有空仓时出现做多信号的处理（先平后开）
  - 测试平仓后资金不足以开新仓的情况
  - 验证 `TradeRecord` 记录的平仓原因为 "reverse_signal"
  - _需求: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 20. 添加单元测试：做空盈亏计算
  - 创建测试文件 `tests/test_short_position_pnl.py`
  - 测试做空盈利场景（价格下跌）
  - 测试做空亏损场景（价格上涨）
  - 验证盈亏金额计算公式 `(entry_price - current_price) * position_size`
  - 验证盈亏百分比计算公式 `pnl_amount / entry_capital * 100`
  - 测试杠杆对做空盈亏的影响
  - _需求: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

- [x] 21. 添加单元测试：做空杠杆计算
  - 在 `tests/test_short_position_pnl.py` 中添加杠杆测试
  - 测试做空保证金计算 `position_value / leverage`
  - 测试做空持仓数量计算 `position_value / entry_price`
  - 测试保证金不足时跳过做空信号
  - 测试平仓后正确返还保证金和盈亏
  - _需求: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

- [x] 22. 添加集成测试：双向 RSI 策略完整回测
  - 创建测试文件 `tests/test_dual_direction_integration.py`
  - 配置双向 RSI 策略（RSI < 30 做多，RSI > 70 做空）
  - 运行完整回测流程
  - 验证交易记录包含做多和做空交易
  - 验证盈亏计算正确
  - 验证反向信号触发的平仓和开仓
  - _需求: 1.1-1.8, 2.1-2.6, 3.1-3.8, 5.1-5.6, 6.1-6.6_

- [x] 23. 添加向后兼容性测试
  - 在 `tests/test_dual_direction_integration.py` 中添加兼容性测试
  - 测试旧版单向做多策略配置（使用 `position_direction="long"`）
  - 测试旧版单向做空策略配置（使用 `position_direction="short"`）
  - 验证旧版配置正确转换为新版字段
  - 验证旧版策略的回测结果与新版一致
  - 验证兼容性警告日志输出
  - _需求: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

- [x] 24. 更新文档和示例
  - 更新 `README.md` 添加双向交易策略功能说明
  - 添加双向策略配置示例（JSON 格式）
  - 更新 API 文档说明新增的请求字段
  - 添加前端 UI 使用说明（如何配置双向策略）
  - 添加常见问题解答（FAQ）
  - _需求: 所有需求_

- [x] 25. 最终检查点 - 确保所有测试通过
  - 运行所有单元测试 `pytest tests/`
  - 运行所有集成测试
  - 验证前端 UI 功能正常
  - 验证 API 接口正常响应
  - 验证向后兼容性
  - 确保没有回归问题

## 注意事项

- 所有任务按顺序执行，确保依赖关系正确
- 每个任务完成后运行相关测试验证功能
- 保持代码注释清晰，说明双向逻辑的实现
- 确保向后兼容性，不影响现有单向策略
- 做空盈亏计算需要特别注意符号（价格下跌时盈利为正）
- 反向信号处理必须在同一时间步内完成（先平后开）

## 任务依赖关系

```
任务 1 (数据模型) → 任务 2, 3, 7
任务 2 (双向信号检测) → 任务 4, 18
任务 3 (双向平仓评估) → 任务 4
任务 4 (反向信号处理) → 任务 19, 22
任务 5 (做空盈亏) → 任务 20, 22
任务 6 (做空杠杆) → 任务 21, 22
任务 7 (API 模型) → 任务 8, 14
任务 8 (API 转换) → 任务 22
任务 9 (移除单选框) → 任务 10, 11, 12, 13
任务 10, 11, 12, 13 (UI 配置区域) → 任务 14, 17
任务 14 (表单收集) → 任务 15, 22
任务 15 (表单验证) → 任务 22
任务 16 (策略模板) → 任务 17
任务 17 (模板加载) → 任务 22
任务 18, 19, 20, 21 (单元测试) → 任务 22
任务 22 (集成测试) → 任务 23
任务 23 (兼容性测试) → 任务 24
任务 24 (文档) → 任务 25
```
