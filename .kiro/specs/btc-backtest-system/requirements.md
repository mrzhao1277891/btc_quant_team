# Requirements Document

## Introduction

BTC回测系统是一个基于历史数据的量化交易策略回测平台。该系统允许用户通过Web界面配置技术指标组合策略，设定开仓条件和止盈止损规则，并使用MySQL数据库中的历史K线数据进行回测，最终生成详细的回测报告和可视化图表。系统支持多时间周期（月线、周线、日线、4小时）和多种技术指标（EMA、RSI、MACD、布林带、ATR等），帮助用户验证交易策略的有效性。

## Glossary

- **Backtest_Engine**: 回测引擎，负责执行策略回测逻辑的核心组件
- **Strategy_Config**: 策略配置，包含技术指标条件、开仓规则、止盈止损规则的配置对象
- **Position**: 持仓，表示一个开仓后尚未平仓的交易状态
- **Trade_Record**: 交易记录，包含开仓和平仓信息的完整交易记录
- **Technical_Indicator**: 技术指标，如EMA、RSI、MACD等用于分析市场的计算指标
- **Kline_Data**: K线数据，包含开高低收价格和成交量的时间序列数据
- **Web_UI**: Web用户界面，用户配置策略和查看回测结果的前端界面
- **API_Server**: API服务器，基于FastAPI的后端服务
- **Database_Connector**: 数据库连接器，负责从MySQL读取历史数据的组件
- **Performance_Metrics**: 性能指标，包括总收益、胜率、最大回撤、夏普比率等回测结果指标
- **Stop_Loss**: 止损，当亏损达到设定条件时自动平仓的机制
- **Take_Profit**: 止盈，当盈利达到设定条件时自动平仓的机制
- **Timeframe**: 时间周期，K线的时间粒度（1m/1w/1d/4h）
- **Indicator_Condition**: 指标条件，对技术指标的比较条件（大于、小于、范围）
- **Logic_Operator**: 逻辑运算符，用于组合多个指标条件的AND/OR运算符

## Requirements

### Requirement 1: 策略配置管理

**User Story:** 作为交易者，我希望能够配置技术指标组合策略，以便测试不同的交易逻辑。

#### Acceptance Criteria

1. THE Strategy_Config SHALL support setting indicator conditions with comparison operators (greater than, less than, within range)
2. THE Strategy_Config SHALL support combining multiple indicator conditions using AND/OR logic operators
3. THE Strategy_Config SHALL include the following technical indicators: EMA7, EMA25, EMA50, RSI14, RSI6, MACD_DIF, MACD_DEA, MACD_Histogram, Bollinger_Upper, Bollinger_Middle, Bollinger_Lower, ATR, Price, Volume
4. THE Strategy_Config SHALL support four timeframes: 1m (monthly), 1w (weekly), 1d (daily), 4h (4-hour)
5. WHEN a user creates a strategy configuration, THE Web_UI SHALL validate that all required fields are provided
6. THE Strategy_Config SHALL support specifying position direction (long or short)
7. THE Strategy_Config SHALL support specifying position size as either absolute amount or percentage of capital

### Requirement 2: 开仓条件执行

**User Story:** 作为交易者，我希望系统能够根据配置的指标条件自动识别开仓信号，以便模拟真实交易场景。

#### Acceptance Criteria

1. WHEN indicator conditions are met, THE Backtest_Engine SHALL generate an entry signal
2. THE Backtest_Engine SHALL evaluate indicator conditions using the specified Logic_Operator (AND/OR)
3. WHEN an entry signal is generated AND no position exists, THE Backtest_Engine SHALL create a new Position
4. THE Backtest_Engine SHALL record the entry price, entry time, and position size in the Position object
5. WHEN multiple timeframes are used in conditions, THE Backtest_Engine SHALL align data by timestamp before evaluation
6. THE Backtest_Engine SHALL support both long and short position entry based on Strategy_Config
7. WHEN capital is insufficient for the specified position size, THE Backtest_Engine SHALL skip the entry signal and log a warning

### Requirement 3: 基于技术指标的止盈止损

**User Story:** 作为交易者，我希望能够设定基于技术指标的止盈止损条件，以便实现动态的风险管理。

#### Acceptance Criteria

1. THE Strategy_Config SHALL support defining exit conditions using Technical_Indicator combinations
2. WHILE a Position is open, THE Backtest_Engine SHALL evaluate exit conditions on each time step
3. WHEN exit conditions are met, THE Backtest_Engine SHALL close the Position and create a Trade_Record
4. THE Backtest_Engine SHALL support multiple exit conditions combined with OR logic (any condition triggers exit)
5. THE Trade_Record SHALL include exit price, exit time, exit reason (which indicator condition triggered)
6. WHEN both take profit and stop loss conditions are met simultaneously, THE Backtest_Engine SHALL execute the exit and record both conditions

### Requirement 4: 基于盈亏绝对值的止盈止损

**User Story:** 作为交易者，我希望能够设定固定的盈亏金额或百分比作为止盈止损条件，以便控制每笔交易的风险收益。

#### Acceptance Criteria

1. THE Strategy_Config SHALL support setting take profit as absolute dollar amount
2. THE Strategy_Config SHALL support setting stop loss as absolute dollar amount
3. THE Strategy_Config SHALL support setting take profit as percentage of entry price
4. THE Strategy_Config SHALL support setting stop loss as percentage of entry price
5. WHILE a Position is open, THE Backtest_Engine SHALL calculate current profit/loss on each time step
6. WHEN profit reaches the take profit threshold, THE Backtest_Engine SHALL close the Position with reason "take_profit_amount" or "take_profit_percentage"
7. WHEN loss reaches the stop loss threshold, THE Backtest_Engine SHALL close the Position with reason "stop_loss_amount" or "stop_loss_percentage"
8. THE Backtest_Engine SHALL evaluate absolute value stop conditions before indicator-based stop conditions

### Requirement 5: 历史数据读取

**User Story:** 作为系统，我需要从MySQL数据库读取历史K线数据和技术指标，以便为回测提供数据支持。

#### Acceptance Criteria

1. THE Database_Connector SHALL connect to the btc_assistant.klines table in MySQL
2. WHEN a backtest is initiated, THE Database_Connector SHALL query Kline_Data for the specified timeframe and date range
3. THE Database_Connector SHALL retrieve OHLCV data (open, high, low, close, volume) from the klines table
4. THE Database_Connector SHALL calculate or retrieve technical indicators (EMA7, EMA25, EMA50, RSI14, RSI6, MACD, Bollinger Bands, ATR) for the requested timeframe
5. THE Database_Connector SHALL return data sorted by timestamp in ascending order
6. WHEN requested data is not available in the database, THE Database_Connector SHALL return an error message indicating the missing data range
7. THE Database_Connector SHALL support querying multiple timeframes in a single backtest session

### Requirement 6: 回测执行引擎

**User Story:** 作为系统，我需要一个回测引擎来模拟策略在历史数据上的执行，以便生成交易记录和性能指标。

#### Acceptance Criteria

1. THE Backtest_Engine SHALL iterate through historical Kline_Data in chronological order
2. THE Backtest_Engine SHALL maintain a capital balance that updates with each trade
3. THE Backtest_Engine SHALL track all open positions and evaluate exit conditions on each time step
4. THE Backtest_Engine SHALL record all completed trades in Trade_Record objects
5. THE Backtest_Engine SHALL calculate Performance_Metrics after all historical data is processed
6. THE Backtest_Engine SHALL handle multiple positions if the strategy allows (or enforce single position if configured)
7. WHEN a backtest completes, THE Backtest_Engine SHALL return a backtest result object containing all Trade_Records and Performance_Metrics

### Requirement 7: 性能指标计算

**User Story:** 作为交易者，我希望系统能够计算详细的回测性能指标，以便评估策略的有效性。

#### Acceptance Criteria

1. THE Backtest_Engine SHALL calculate total return as (final_capital - initial_capital) / initial_capital
2. THE Backtest_Engine SHALL calculate win rate as (winning_trades / total_trades)
3. THE Backtest_Engine SHALL calculate maximum drawdown as the largest peak-to-trough decline in capital
4. THE Backtest_Engine SHALL calculate Sharpe ratio using daily returns and risk-free rate of 0
5. THE Backtest_Engine SHALL calculate average profit per trade and average loss per trade
6. THE Backtest_Engine SHALL calculate profit factor as (total_profit / total_loss)
7. THE Backtest_Engine SHALL calculate total number of trades, winning trades, and losing trades
8. THE Performance_Metrics SHALL include the longest winning streak and longest losing streak

### Requirement 8: 交易记录管理

**User Story:** 作为交易者，我希望能够查看每笔交易的详细记录，以便分析策略的具体表现。

#### Acceptance Criteria

1. THE Trade_Record SHALL include entry_time, entry_price, position_size, position_direction (long/short)
2. THE Trade_Record SHALL include exit_time, exit_price, exit_reason
3. THE Trade_Record SHALL include profit_loss as absolute dollar amount
4. THE Trade_Record SHALL include profit_loss_percentage as percentage of entry capital
5. THE Trade_Record SHALL include holding_period as the duration between entry and exit
6. WHEN a backtest completes, THE API_Server SHALL return all Trade_Records in chronological order
7. THE Web_UI SHALL display Trade_Records in a sortable and filterable table

### Requirement 9: Web用户界面 - 策略配置

**User Story:** 作为交易者，我希望通过Web界面配置策略参数，以便方便地创建和修改回测策略。

#### Acceptance Criteria

1. THE Web_UI SHALL provide a form for creating new Strategy_Config objects
2. THE Web_UI SHALL allow users to add multiple indicator conditions with dropdown selectors for indicator, operator, and value input
3. THE Web_UI SHALL allow users to select Logic_Operator (AND/OR) for combining conditions
4. THE Web_UI SHALL provide separate sections for entry conditions and exit conditions
5. THE Web_UI SHALL allow users to select position direction (long/short) via radio buttons
6. THE Web_UI SHALL allow users to input position size as either dollar amount or percentage
7. THE Web_UI SHALL allow users to configure stop loss and take profit using either absolute values or percentages
8. WHEN a user submits the strategy configuration form, THE Web_UI SHALL send the Strategy_Config to the API_Server via HTTP POST
9. THE Web_UI SHALL display validation errors if required fields are missing or invalid

### Requirement 10: Web用户界面 - 回测结果展示

**User Story:** 作为交易者，我希望通过Web界面查看回测结果和可视化图表，以便直观地评估策略表现。

#### Acceptance Criteria

1. THE Web_UI SHALL display Performance_Metrics in a summary card including total return, win rate, max drawdown, Sharpe ratio
2. THE Web_UI SHALL display a table of all Trade_Records with columns for entry time, exit time, direction, profit/loss, holding period
3. THE Web_UI SHALL render an equity curve chart showing capital balance over time
4. THE Web_UI SHALL render a drawdown chart showing drawdown percentage over time
5. THE Web_UI SHALL render a monthly returns heatmap if backtest period spans multiple months
6. THE Web_UI SHALL allow users to export Trade_Records as CSV file
7. THE Web_UI SHALL allow users to export Performance_Metrics as JSON file
8. WHEN no trades were executed in the backtest, THE Web_UI SHALL display a message indicating no trading opportunities were found

### Requirement 11: API服务端点

**User Story:** 作为系统，我需要提供RESTful API端点，以便Web_UI与Backtest_Engine通信。

#### Acceptance Criteria

1. THE API_Server SHALL provide a POST /api/backtest endpoint that accepts Strategy_Config and date range parameters
2. WHEN a backtest request is received, THE API_Server SHALL validate the Strategy_Config
3. WHEN validation passes, THE API_Server SHALL invoke the Backtest_Engine with the provided configuration
4. WHEN the backtest completes, THE API_Server SHALL return a JSON response containing Performance_Metrics and Trade_Records
5. IF an error occurs during backtest, THE API_Server SHALL return an HTTP 400 or 500 error with a descriptive error message
6. THE API_Server SHALL provide a GET /api/indicators endpoint that returns the list of available Technical_Indicators
7. THE API_Server SHALL provide a GET /api/timeframes endpoint that returns the list of available Timeframes
8. THE API_Server SHALL implement CORS headers to allow requests from the Web_UI origin

### Requirement 12: 策略模板和示例

**User Story:** 作为交易者，我希望系统提供预定义的策略模板，以便快速开始回测而无需从零配置。

#### Acceptance Criteria

1. THE API_Server SHALL provide a GET /api/strategy-templates endpoint that returns predefined Strategy_Config templates
2. THE API_Server SHALL include at least two strategy templates: "EMA Golden Cross" and "Bollinger Breakout"
3. THE "EMA Golden Cross" template SHALL configure entry condition as (EMA7 > EMA25 AND RSI14 < 70) on daily timeframe
4. THE "EMA Golden Cross" template SHALL configure take profit at 10% and stop loss at 5%
5. THE "Bollinger Breakout" template SHALL configure entry condition as (Price > Bollinger_Upper AND Volume > 1.5 * Average_Volume)
6. THE "Bollinger Breakout" template SHALL configure exit condition as (Price < Bollinger_Middle)
7. WHEN a user selects a template in Web_UI, THE Web_UI SHALL populate the strategy configuration form with the template values

### Requirement 13: 数据完整性验证

**User Story:** 作为系统，我需要验证历史数据的完整性，以便确保回测结果的准确性。

#### Acceptance Criteria

1. WHEN Kline_Data is loaded, THE Database_Connector SHALL check for missing timestamps in the time series
2. WHEN missing data is detected, THE Database_Connector SHALL log a warning with the missing date range
3. THE Database_Connector SHALL check that OHLC data satisfies the constraint: low <= open, close <= high
4. WHEN invalid OHLC data is detected, THE Database_Connector SHALL exclude the invalid record and log an error
5. THE Database_Connector SHALL verify that volume values are non-negative
6. WHEN data quality issues are found, THE API_Server SHALL include a data_quality_warnings field in the backtest response

### Requirement 14: 回测配置持久化

**User Story:** 作为交易者，我希望能够保存和加载策略配置，以便重复运行相同的回测或修改已有策略。

#### Acceptance Criteria

1. THE API_Server SHALL provide a POST /api/strategies endpoint to save a Strategy_Config with a user-provided name
2. THE API_Server SHALL store saved strategies in a JSON file or database table
3. THE API_Server SHALL provide a GET /api/strategies endpoint that returns all saved Strategy_Config objects
4. THE API_Server SHALL provide a GET /api/strategies/{id} endpoint that returns a specific Strategy_Config by ID
5. THE API_Server SHALL provide a DELETE /api/strategies/{id} endpoint to delete a saved strategy
6. WHEN a strategy is saved, THE API_Server SHALL assign a unique ID and timestamp
7. THE Web_UI SHALL provide a "Load Strategy" dropdown that populates the configuration form with a saved strategy

### Requirement 15: 并发回测支持

**User Story:** 作为交易者，我希望能够同时运行多个回测，以便比较不同策略的表现。

#### Acceptance Criteria

1. THE API_Server SHALL support concurrent backtest requests from multiple clients
2. THE Backtest_Engine SHALL execute each backtest in an isolated context to prevent data interference
3. WHEN multiple backtests are running, THE API_Server SHALL queue requests if resource limits are reached
4. THE API_Server SHALL return a unique backtest_id for each backtest request
5. THE API_Server SHALL provide a GET /api/backtest/{backtest_id}/status endpoint to check backtest progress
6. WHEN a backtest is queued, THE API_Server SHALL return HTTP 202 Accepted with the backtest_id
7. WHEN a backtest completes, THE API_Server SHALL cache results for 1 hour to allow retrieval via GET /api/backtest/{backtest_id}/results

### Requirement 16: 错误处理和日志记录

**User Story:** 作为开发者，我需要系统记录详细的错误日志，以便调试和监控系统运行状态。

#### Acceptance Criteria

1. THE API_Server SHALL log all incoming requests with timestamp, endpoint, and parameters
2. WHEN an error occurs in Backtest_Engine, THE API_Server SHALL log the full stack trace
3. THE API_Server SHALL log warnings when data quality issues are detected
4. THE API_Server SHALL log the start and completion time of each backtest
5. THE API_Server SHALL use structured logging with log levels: DEBUG, INFO, WARNING, ERROR
6. THE API_Server SHALL write logs to both console and a rotating log file
7. WHEN a backtest fails, THE API_Server SHALL return a user-friendly error message in the API response while logging technical details

### Requirement 17: 性能优化

**User Story:** 作为用户，我希望回测能够快速完成，以便高效地测试多个策略。

#### Acceptance Criteria

1. THE Database_Connector SHALL use indexed queries on timestamp and timeframe columns
2. THE Backtest_Engine SHALL precompute technical indicators once per backtest rather than on each evaluation
3. THE Backtest_Engine SHALL use vectorized operations for indicator calculations when possible
4. WHEN a backtest processes more than 10,000 data points, THE Backtest_Engine SHALL provide progress updates every 10%
5. THE API_Server SHALL implement response caching for GET endpoints with a 5-minute TTL
6. THE Backtest_Engine SHALL complete a backtest of 1 year of daily data within 5 seconds on standard hardware
7. THE Web_UI SHALL display a progress indicator during backtest execution

### Requirement 18: 技术指标计算

**User Story:** 作为系统，我需要准确计算技术指标，以便为策略评估提供正确的数据。

#### Acceptance Criteria

1. THE Backtest_Engine SHALL calculate EMA using the formula: EMA_today = (Price_today * K) + (EMA_yesterday * (1 - K)), where K = 2 / (N + 1)
2. THE Backtest_Engine SHALL calculate RSI using the formula: RSI = 100 - (100 / (1 + RS)), where RS = Average_Gain / Average_Loss
3. THE Backtest_Engine SHALL calculate MACD as: DIF = EMA12 - EMA26, DEA = EMA9(DIF), MACD = DIF - DEA
4. THE Backtest_Engine SHALL calculate Bollinger Bands as: Middle = SMA20, Upper = Middle + (2 * StdDev), Lower = Middle - (2 * StdDev)
5. THE Backtest_Engine SHALL calculate ATR using the formula: ATR = EMA14(True_Range), where True_Range = max(High - Low, abs(High - Previous_Close), abs(Low - Previous_Close))
6. WHEN insufficient historical data exists to calculate an indicator, THE Backtest_Engine SHALL skip evaluation until enough data is available
7. THE Backtest_Engine SHALL use the close price for all indicator calculations unless otherwise specified

### Requirement 19: 回测报告生成

**User Story:** 作为交易者，我希望系统能够生成详细的回测报告，以便分享和存档策略测试结果。

#### Acceptance Criteria

1. THE API_Server SHALL provide a GET /api/backtest/{backtest_id}/report endpoint that generates a formatted report
2. THE report SHALL include a summary section with Strategy_Config parameters and Performance_Metrics
3. THE report SHALL include a trades section with all Trade_Records in a formatted table
4. THE report SHALL include a monthly breakdown of returns if applicable
5. THE report SHALL include embedded charts (equity curve, drawdown) as base64-encoded images
6. THE API_Server SHALL support report export in HTML and PDF formats
7. WHEN a report is requested, THE API_Server SHALL generate it within 3 seconds

### Requirement 20: 前端响应式设计

**User Story:** 作为用户，我希望Web界面能够在不同设备上正常显示，以便在手机或平板上查看回测结果。

#### Acceptance Criteria

1. THE Web_UI SHALL use responsive CSS layout that adapts to screen widths from 320px to 1920px
2. THE Web_UI SHALL display strategy configuration form in a single column on mobile devices (width < 768px)
3. THE Web_UI SHALL display Trade_Records table with horizontal scrolling on mobile devices
4. THE Web_UI SHALL render charts with appropriate sizing for the viewport width
5. THE Web_UI SHALL use touch-friendly button sizes (minimum 44x44 pixels) on mobile devices
6. THE Web_UI SHALL test successfully on Chrome, Firefox, Safari, and Edge browsers
7. THE Web_UI SHALL load and render the initial page within 2 seconds on a standard broadband connection
