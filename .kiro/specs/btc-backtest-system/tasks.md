# Implementation Plan: BTC回测系统

## Overview

本实施计划将BTC回测系统的设计转化为可执行的编码任务。系统采用Python FastAPI后端和Vanilla JavaScript前端架构，核心功能包括策略配置管理、回测引擎、技术指标计算、性能指标分析和Web UI展示。实施过程将按照从底层数据模型到上层API和UI的顺序进行，确保每个模块都经过充分测试后再进行集成。

## Tasks

- [x] 1. 建立项目结构和核心数据模型
  - 创建项目目录结构（backend/, web/, tests/, logs/）
  - 定义核心数据模型类（StrategyConfig, Position, TradeRecord, PerformanceMetrics, BacktestResult）
  - 实现数据模型的序列化/反序列化方法（to_dict, from_dict）
  - 配置日志系统（RotatingFileHandler, 控制台和文件输出）
  - 创建requirements.txt和项目配置文件
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.6, 1.7, 16.5, 16.6_

- [ ]* 1.1 为核心数据模型编写单元测试
  - 测试StrategyConfig的验证逻辑
  - 测试数据模型的序列化/反序列化
  - 测试边界条件（缺失字段、无效值）
  - _Requirements: 1.5, 9.9_

- [x] 2. 实现技术指标计算模块
  - [x] 2.1 创建IndicatorCalculator类和基础结构
    - 实现EMA计算方法（使用公式: EMA_today = (Price * K) + (EMA_yesterday * (1-K)), K = 2/(N+1)）
    - 实现RSI计算方法（使用公式: RSI = 100 - (100 / (1 + RS))）
    - 处理数据不足情况（返回NaN）
    - _Requirements: 18.1, 18.2, 18.6, 18.7_

  - [ ]* 2.2 为EMA和RSI编写属性测试
    - **Property 31: EMA Calculation Formula**
    - **Property 32: RSI Calculation Formula**
    - **Property 36: Insufficient Data Handling**
    - **Validates: Requirements 18.1, 18.2, 18.6**

  - [x] 2.3 实现MACD、布林带和ATR计算
    - 实现MACD计算（DIF = EMA12 - EMA26, DEA = EMA9(DIF), MACD = DIF - DEA）
    - 实现布林带计算（Middle = SMA20, Upper = Middle + 2*StdDev, Lower = Middle - 2*StdDev）
    - 实现ATR计算（ATR = EMA14(True_Range)）
    - 实现calculate_all_indicators方法（向量化计算）
    - _Requirements: 18.3, 18.4, 18.5, 17.2_

  - [ ]* 2.4 为MACD、布林带和ATR编写属性测试
    - **Property 33: MACD Calculation Formula**
    - **Property 34: Bollinger Bands Calculation Formula**
    - **Property 35: ATR Calculation Formula**
    - **Validates: Requirements 18.3, 18.4, 18.5**

- [x] 3. 实现数据库连接器
  - [x] 3.1 创建DatabaseConnector类
    - 实现MySQL连接管理（使用连接池）
    - 实现fetch_klines方法（查询指定时间范围和周期的K线数据）
    - 实现数据排序逻辑（按timestamp升序）
    - 实现get_available_date_range方法
    - _Requirements: 5.1, 5.2, 5.3, 5.5, 5.7, 17.1_

  - [ ]* 3.2 为DatabaseConnector编写属性测试
    - **Property 12: Data Sorting Guarantee**
    - **Property 13: Missing Data Error Reporting**
    - **Validates: Requirements 5.5, 5.6**

  - [x] 3.3 实现数据完整性验证
    - 实现validate_data_integrity方法（检查时间序列连续性）
    - 实现OHLC约束验证（low <= open, close <= high）
    - 实现成交量非负验证
    - 记录数据质量警告到日志
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 16.3_

  - [ ]* 3.4 为数据完整性验证编写属性测试
    - **Property 26: OHLC Data Validation**
    - **Property 27: Missing Timestamp Detection**
    - **Property 28: Invalid Data Exclusion**
    - **Property 29: Data Quality Warning Propagation**
    - **Validates: Requirements 13.1, 13.2, 13.3, 13.4, 13.5, 13.6**

- [x] 4. Checkpoint - 验证基础模块
  - 确保所有测试通过，询问用户是否有问题

- [x] 5. 实现回测引擎核心逻辑
  - [x] 5.1 创建BacktestEngine类和初始化
    - 实现__init__方法（接收strategy_config和kline_data）
    - 实现_evaluate_entry_conditions方法（支持AND/OR逻辑运算符）
    - 实现_evaluate_exit_conditions方法（返回是否平仓和平仓原因）
    - _Requirements: 2.1, 2.2, 3.2, 3.4_

  - [ ]* 5.2 为条件评估编写属性测试
    - **Property 2: Entry Signal Generation**
    - **Property 6: Exit Condition Triggering**
    - **Property 7: OR Logic for Exit Conditions**
    - **Validates: Requirements 2.1, 2.2, 3.2, 3.3, 3.4**

  - [x] 5.3 实现开仓和平仓逻辑
    - 实现_open_position方法（创建Position对象，记录entry_time, entry_price, position_size）
    - 实现_close_position方法（创建TradeRecord对象，记录exit信息）
    - 实现_calculate_pnl方法（计算绝对值和百分比盈亏，支持long/short）
    - 处理资金不足情况（跳过开仓信号并记录警告）
    - _Requirements: 2.3, 2.4, 2.7, 4.5, 8.1, 8.2, 8.3, 8.4, 8.5, 16.2_

  - [ ]* 5.4 为开仓平仓逻辑编写属性测试
    - **Property 3: Position Creation on Entry Signal**
    - **Property 4: Capital Insufficiency Handling**
    - **Property 8: Profit/Loss Calculation Accuracy**
    - **Property 16: Trade Record Completeness**
    - **Validates: Requirements 2.3, 2.4, 2.7, 4.5, 8.1-8.5**

  - [x] 5.5 实现止盈止损逻辑
    - 实现绝对金额止盈止损检查（take_profit_amount, stop_loss_amount）
    - 实现百分比止盈止损检查（take_profit_pct, stop_loss_pct）
    - 实现止损条件优先级（绝对值优先于指标条件）
    - 记录正确的exit_reason
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.6, 4.7, 4.8, 3.5_

  - [ ]* 5.6 为止盈止损逻辑编写属性测试
    - **Property 9: Take Profit Triggering**
    - **Property 10: Stop Loss Triggering**
    - **Property 11: Stop Condition Evaluation Priority**
    - **Validates: Requirements 4.6, 4.7, 4.8**

  - [x] 5.7 实现回测主循环
    - 实现run方法（按时间顺序迭代K线数据）
    - 维护资金余额（每笔交易后更新）
    - 跟踪所有开仓持仓并在每个时间步评估平仓条件
    - 支持多时间周期数据对齐
    - 记录所有完成的交易
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 2.5, 16.1, 16.4_

  - [ ]* 5.8 为回测主循环编写属性测试
    - **Property 14: Chronological Iteration**
    - **Property 15: Capital Balance Maintenance**
    - **Property 17: Trade Record Chronological Ordering**
    - **Property 5: Multi-Timeframe Data Alignment**
    - **Validates: Requirements 6.1, 6.2, 6.4, 8.6, 2.5**

- [x] 6. 实现性能指标计算模块
  - [x] 6.1 创建MetricsCalculator类
    - 实现calculate_total_return方法（(final - initial) / initial）
    - 实现calculate_win_rate方法（winning_trades / total_trades）
    - 实现calculate_max_drawdown方法（最大峰谷跌幅）
    - 实现calculate_sharpe_ratio方法（(mean_return - 0) / std_return）
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

  - [ ]* 6.2 为基础性能指标编写属性测试
    - **Property 19: Total Return Calculation**
    - **Property 20: Win Rate Calculation**
    - **Property 21: Maximum Drawdown Calculation**
    - **Property 22: Sharpe Ratio Calculation**
    - **Validates: Requirements 7.1, 7.2, 7.3, 7.4**

  - [x] 6.3 实现高级性能指标
    - 实现calculate_profit_factor方法（total_profit / total_loss）
    - 实现交易统计计算（total_trades, winning_trades, losing_trades）
    - 实现平均盈亏计算（avg_profit, avg_loss）
    - 实现连胜连亏计算（longest_win_streak, longest_loss_streak）
    - 实现calculate_all_metrics方法（返回完整PerformanceMetrics对象）
    - _Requirements: 7.5, 7.6, 7.7, 7.8, 6.5_

  - [ ]* 6.4 为高级性能指标编写属性测试
    - **Property 23: Profit Factor Calculation**
    - **Property 24: Trade Count Accuracy**
    - **Property 25: Winning/Losing Streak Calculation**
    - **Validates: Requirements 7.6, 7.7, 7.8**

- [x] 7. Checkpoint - 验证核心引擎
  - 确保所有测试通过，询问用户是否有问题

- [x] 8. 实现策略管理器
  - [x] 8.1 创建StrategyManager类
    - 实现validate_config方法（验证所有必填字段和有效值）
    - 实现save_strategy方法（保存到JSON文件或数据库，分配唯一ID）
    - 实现load_strategy方法（从存储加载策略配置）
    - 实现list_strategies方法（返回所有已保存策略）
    - 实现delete_strategy方法（删除指定策略）
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 1.5_

  - [ ]* 8.2 为策略管理器编写属性测试
    - **Property 1: Strategy Configuration Validation**
    - **Validates: Requirements 1.5**

  - [x] 8.3 实现策略模板功能
    - 实现get_templates方法（返回预定义模板列表）
    - 创建"EMA Golden Cross"模板（EMA7 > EMA25 AND RSI14 < 70, 止盈10%, 止损5%）
    - 创建"Bollinger Breakout"模板（Price > Bollinger_Upper AND Volume > 1.5*Avg, 出场Price < Bollinger_Middle）
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6_

  - [ ]* 8.4 为策略模板编写单元测试
    - 测试模板加载和字段完整性
    - 测试模板配置的有效性
    - _Requirements: 12.7_

- [x] 9. 实现FastAPI服务器和核心端点
  - [x] 9.1 创建FastAPI应用和中间件
    - 初始化FastAPI应用
    - 配置CORS中间件（允许Web UI跨域请求）
    - 配置请求日志中间件（记录所有请求）
    - 实现全局异常处理器（ValidationError, DataError, Exception）
    - _Requirements: 11.8, 16.1, 16.2, 16.7_

  - [x] 9.2 实现回测相关API端点
    - 实现POST /api/backtest端点（接收策略配置和日期范围，执行回测）
    - 实现GET /api/backtest/{id}/status端点（查询回测状态）
    - 实现GET /api/backtest/{id}/results端点（获取回测结果）
    - 实现结果缓存机制（1小时TTL）
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 15.3, 15.4, 15.5, 15.6, 15.7, 17.5_

  - [ ]* 9.3 为回测API端点编写属性测试
    - **Property 30: API Validation Behavior**
    - **Property 18: Backtest Result Completeness**
    - **Validates: Requirements 11.2, 11.4, 11.5, 6.7**

  - [x] 9.4 实现策略管理API端点
    - 实现POST /api/strategies端点（保存策略）
    - 实现GET /api/strategies端点（列出所有策略）
    - 实现GET /api/strategies/{id}端点（获取特定策略）
    - 实现DELETE /api/strategies/{id}端点（删除策略）
    - 实现GET /api/strategy-templates端点（获取模板）
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5_

  - [x] 9.5 实现元数据API端点
    - 实现GET /api/indicators端点（返回可用指标列表）
    - 实现GET /api/timeframes端点（返回可用时间周期）
    - 实现GET /api/data-range端点（返回数据可用范围）
    - _Requirements: 11.6, 11.7_

  - [ ]* 9.6 为API端点编写集成测试
    - 使用TestClient测试所有端点
    - 测试请求验证和错误响应
    - 测试端到端回测流程
    - _Requirements: 11.1-11.8_

- [x] 10. 实现并发回测支持
  - [x] 10.1 实现回测任务队列和并发管理
    - 实现回测任务队列（使用asyncio.Queue或后台任务）
    - 为每个回测分配唯一backtest_id
    - 实现资源限制检查（队列满时返回HTTP 202）
    - 确保每个回测在隔离上下文中执行
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.6_

  - [ ]* 10.2 为并发回测编写单元测试
    - 测试多个并发请求的处理
    - 测试队列满时的行为
    - 测试回测结果隔离
    - _Requirements: 15.1, 15.2, 15.3_

- [x] 11. Checkpoint - 验证后端API
  - 确保所有测试通过，询问用户是否有问题

- [x] 12. 实现Web UI - 策略配置表单
  - [x] 12.1 创建HTML结构和基础样式
    - 创建backtest.html主页面结构
    - 创建backtest.css样式文件（响应式布局，支持320px-1920px）
    - 实现移动端适配（单列布局，触摸友好按钮）
    - _Requirements: 20.1, 20.2, 20.5_

  - [x] 12.2 实现策略配置表单组件
    - 创建StrategyForm.js组件
    - 实现动态添加/删除指标条件的功能
    - 实现指标、运算符、值的下拉选择器
    - 实现逻辑运算符选择（AND/OR）
    - 实现开仓条件和平仓条件分区
    - 实现持仓方向选择（long/short单选按钮）
    - 实现持仓大小输入（金额或百分比）
    - 实现止盈止损配置（绝对值或百分比）
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7_

  - [x] 12.3 实现表单验证和提交
    - 实现客户端表单验证（必填字段检查）
    - 实现表单提交逻辑（HTTP POST到/api/backtest）
    - 实现验证错误显示
    - 实现加载指示器（回测执行期间）
    - _Requirements: 9.8, 9.9, 17.7_

  - [x] 12.4 实现模板选择器
    - 创建TemplateSelector.js组件
    - 实现从/api/strategy-templates加载模板
    - 实现模板选择后自动填充表单
    - _Requirements: 12.7_

  - [x] 12.5 实现策略保存和加载
    - 实现"保存策略"按钮和对话框
    - 实现"加载策略"下拉菜单
    - 实现从/api/strategies加载已保存策略
    - _Requirements: 14.7_

- [x] 13. 实现Web UI - 回测结果展示
  - [x] 13.1 创建结果展示面板
    - 创建ResultsPanel.js组件
    - 实现性能指标摘要卡片（总收益、胜率、最大回撤、夏普比率）
    - 实现无交易情况的提示信息
    - _Requirements: 10.1, 10.8_

  - [x] 13.2 实现交易记录表格
    - 创建TradeTable.js组件
    - 实现可排序的交易记录表格（按entry_time, exit_time, profit_loss等排序）
    - 实现可过滤的表格（按方向、盈亏筛选）
    - 实现移动端横向滚动
    - _Requirements: 10.2, 20.3_

  - [x] 13.3 实现图表渲染
    - 创建ChartRenderer.js组件（使用Chart.js）
    - 实现权益曲线图（capital over time）
    - 实现回撤图（drawdown percentage over time）
    - 实现月度收益热力图（如果回测跨多月）
    - 实现响应式图表尺寸
    - _Requirements: 10.3, 10.4, 10.5, 20.4_

  - [x] 13.4 实现数据导出功能
    - 实现"导出CSV"按钮（导出交易记录）
    - 实现"导出JSON"按钮（导出性能指标）
    - _Requirements: 10.6, 10.7_

- [x] 14. 实现回测报告生成
  - [x] 14.1 实现报告生成API端点
    - 实现GET /api/backtest/{id}/report端点
    - 生成格式化的HTML报告（包含策略配置、性能指标、交易记录表格）
    - 生成月度收益分解（如果适用）
    - 嵌入base64编码的图表图像
    - 支持HTML和PDF格式导出
    - 确保报告在3秒内生成
    - _Requirements: 19.1, 19.2, 19.3, 19.4, 19.5, 19.6, 19.7_

  - [ ]* 14.2 为报告生成编写单元测试
    - 测试报告内容完整性
    - 测试不同格式的导出
    - 测试生成性能
    - _Requirements: 19.1-19.7_

- [x] 15. Checkpoint - 验证前端功能
  - 确保所有测试通过，询问用户是否有问题

- [x] 16. 性能优化和最终集成
  - [x] 16.1 实现性能优化
    - 优化数据库查询（确保使用timestamp和timeframe索引）
    - 实现技术指标预计算（每次回测只计算一次）
    - 实现向量化操作（使用Pandas/NumPy）
    - 实现进度更新（处理>10000数据点时每10%更新）
    - _Requirements: 17.1, 17.2, 17.3, 17.4_

  - [ ]* 16.2 进行性能测试
    - 测试1年日线数据回测时间（应<5秒）
    - 测试并发10个回测请求
    - 使用EXPLAIN分析数据库查询
    - _Requirements: 17.6_

  - [x] 16.3 实现数据库表创建
    - 创建backtest_strategies表（如果不存在）
    - 创建backtest_results表（如果不存在）
    - 创建必要的索引
    - _Requirements: 14.2_

  - [x] 16.4 最终集成和端到端测试
    - 运行完整的端到端回测流程
    - 测试所有浏览器兼容性（Chrome, Firefox, Safari, Edge）
    - 测试页面加载性能（应<2秒）
    - 修复发现的任何集成问题
    - _Requirements: 20.6, 20.7_

- [x] 17. Final Checkpoint - 完整系统验证
  - 确保所有测试通过，询问用户是否有问题

## Notes

- 任务标记为`*`的为可选测试任务，可以跳过以加快MVP开发
- 每个任务都引用了具体的需求编号，确保可追溯性
- Checkpoint任务确保增量验证，及时发现问题
- 属性测试验证设计文档中定义的通用正确性属性
- 单元测试验证特定示例和边界条件
- 系统使用Python作为实现语言（基于设计文档中的代码示例）
- 所有属性测试必须运行至少100次迭代
- 测试任务作为子任务放置在实现任务之后，以便尽早捕获错误

## Task Dependency Graph

```json
{
  "waves": [
    {
      "id": 0,
      "tasks": ["1"]
    },
    {
      "id": 1,
      "tasks": ["1.1", "2.1", "3.1"]
    },
    {
      "id": 2,
      "tasks": ["2.2", "2.3", "3.2", "3.3"]
    },
    {
      "id": 3,
      "tasks": ["2.4", "3.4"]
    },
    {
      "id": 4,
      "tasks": ["5.1"]
    },
    {
      "id": 5,
      "tasks": ["5.2", "5.3"]
    },
    {
      "id": 6,
      "tasks": ["5.4", "5.5", "6.1"]
    },
    {
      "id": 7,
      "tasks": ["5.6", "5.7", "6.2", "6.3"]
    },
    {
      "id": 8,
      "tasks": ["5.8", "6.4", "8.1"]
    },
    {
      "id": 9,
      "tasks": ["8.2", "8.3"]
    },
    {
      "id": 10,
      "tasks": ["8.4", "9.1"]
    },
    {
      "id": 11,
      "tasks": ["9.2"]
    },
    {
      "id": 12,
      "tasks": ["9.3", "9.4", "9.5", "10.1"]
    },
    {
      "id": 13,
      "tasks": ["9.6", "10.2"]
    },
    {
      "id": 14,
      "tasks": ["12.1"]
    },
    {
      "id": 15,
      "tasks": ["12.2"]
    },
    {
      "id": 16,
      "tasks": ["12.3", "12.4", "12.5", "13.1"]
    },
    {
      "id": 17,
      "tasks": ["13.2", "13.3"]
    },
    {
      "id": 18,
      "tasks": ["13.4", "14.1"]
    },
    {
      "id": 19,
      "tasks": ["14.2"]
    },
    {
      "id": 20,
      "tasks": ["16.1"]
    },
    {
      "id": 21,
      "tasks": ["16.2", "16.3"]
    },
    {
      "id": 22,
      "tasks": ["16.4"]
    }
  ]
}
```
