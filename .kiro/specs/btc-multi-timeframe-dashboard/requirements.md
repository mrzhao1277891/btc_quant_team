# Requirements Document

## Introduction

本需求文档定义了BTC多周期指标仪表盘页面的功能需求。该页面将展示4个时间周期（月线1m、周线1w、日线1d、4小时4h）的技术指标当前值，支持用户同屏对比分析，辅助多时间框架投资决策。

## Glossary

- **Dashboard_Page**: 仪表盘页面，展示多周期技术指标的Web页面
- **Timeframe_Module**: 时间周期模块，展示单个时间周期（1m/1w/1d/4h）的独立可视化模块
- **Indicator**: 技术指标，包括价格、均线、MACD、RSI、布林带、ATR等
- **API_Backend**: 后端API服务，FastAPI提供的数据接口（/api/all, /api/latest, /api/klines）
- **Auto_Refresh**: 自动刷新机制，定时从后端获取最新数据并更新页面

## Requirements

### Requirement 1: 卡片布局

**User Story:** 作为投资者，我想在一个页面上看到不同类型指标的可视化卡片，以便快速对比分析市场状态。

#### Acceptance Criteria

1. THE Dashboard_Page SHALL display exactly 3 visualization cards
2. THE Dashboard_Page SHALL display one card for price and moving average indicators (EMA, Bollinger Bands)
3. THE Dashboard_Page SHALL display one card for RSI indicators
4. THE Dashboard_Page SHALL display one card for MACD indicators
5. WHEN the viewport width is greater than 1200px, THE Dashboard_Page SHALL arrange cards in a 3-column grid
6. WHEN the viewport width is less than 1200px, THE Dashboard_Page SHALL arrange cards in a single column

### Requirement 2: 技术指标当前值显示

**User Story:** 作为投资者，我想看到每个周期各项技术指标的当前值，以便了解当前市场状态。

#### Acceptance Criteria

1. WHEN a card is rendered, THE Dashboard_Page SHALL display the current close price for each timeframe (1m, 1w, 1d, 4h)
2. WHEN the price card is rendered, THE Dashboard_Page SHALL display current values for EMA7, EMA25, EMA50 for each timeframe
3. WHEN the price card is rendered, THE Dashboard_Page SHALL display current values for Bollinger Bands (boll_up, boll_md, boll_dn) for each timeframe
4. WHEN the RSI card is rendered, THE Dashboard_Page SHALL display current values for RSI14 and RSI6 for each timeframe
5. WHEN the MACD card is rendered, THE Dashboard_Page SHALL display current values for DIF, DEA, and MACD柱 for each timeframe
6. WHEN an Indicator value is null or unavailable, THE Dashboard_Page SHALL display "—" as placeholder

### Requirement 3: 指标值颜色编码

**User Story:** 作为投资者，我想通过颜色快速识别指标的多空信号，以便快速判断趋势方向。

#### Acceptance Criteria

1. WHEN the close price is above an EMA value, THE Dashboard_Page SHALL display that EMA value in green color
2. WHEN the close price is below an EMA value, THE Dashboard_Page SHALL display that EMA value in red color
3. WHEN MACD柱 value is positive, THE Dashboard_Page SHALL display it in green color
4. WHEN MACD柱 value is negative, THE Dashboard_Page SHALL display it in red color
5. WHEN DIF value is positive, THE Dashboard_Page SHALL display it in green color
6. WHEN DIF value is negative, THE Dashboard_Page SHALL display it in red color
7. WHEN DEA value is positive, THE Dashboard_Page SHALL display it in green color
8. WHEN DEA value is negative, THE Dashboard_Page SHALL display it in red color
9. WHEN RSI14 is greater than 70, THE Dashboard_Page SHALL display it in red color (overbought)
10. WHEN RSI14 is less than 30, THE Dashboard_Page SHALL display it in green color (oversold)
11. WHEN RSI6 is greater than 70, THE Dashboard_Page SHALL display it in red color (overbought)
12. WHEN RSI6 is less than 30, THE Dashboard_Page SHALL display it in green color (oversold)

### Requirement 4: 价格与均线布林带水平线可视化

**User Story:** 作为投资者，我想通过水平线直观看到当前价格与各技术指标的相对位置，以便快速判断价格所处的技术位置。

#### Acceptance Criteria

1. THE Dashboard_Page SHALL display a single card showing price levels across all 4 timeframes
2. WHEN the price card is rendered, THE Dashboard_Page SHALL display EMA7, EMA25, EMA50 as horizontal lines for each timeframe
3. WHEN the price card is rendered, THE Dashboard_Page SHALL display Bollinger Bands (boll_up, boll_md, boll_dn) as horizontal lines for each timeframe
4. WHEN the price card is rendered, THE Dashboard_Page SHALL display the current close price as a distinct marker/point for each timeframe
5. THE Dashboard_Page SHALL position all horizontal lines proportionally based on their price values
6. THE Dashboard_Page SHALL label each horizontal line with its timeframe and indicator name
7. THE Dashboard_Page SHALL use distinct colors for different indicator types (EMA: blue shades, Bollinger: red shades, Price: green/red)
8. THE Dashboard_Page SHALL group indicators by timeframe within the card for clear comparison

### Requirement 5: RSI指标水平线可视化

**User Story:** 作为投资者，我想通过水平线看到4个周期的RSI指标位置，以便快速判断各周期的超买超卖状态。

#### Acceptance Criteria

1. THE Dashboard_Page SHALL display a single card showing RSI levels across all 4 timeframes
2. WHEN the RSI card is rendered, THE Dashboard_Page SHALL display RSI14 value as a horizontal line for each timeframe (1m, 1w, 1d, 4h)
3. WHEN the RSI card is rendered, THE Dashboard_Page SHALL display RSI6 value as a horizontal line for each timeframe
4. THE Dashboard_Page SHALL display reference lines at RSI levels 30 (oversold) and 70 (overbought)
5. THE Dashboard_Page SHALL position RSI lines on a 0-100 scale
6. WHEN RSI14 is above 70, THE Dashboard_Page SHALL highlight it in red color (overbought)
7. WHEN RSI14 is below 30, THE Dashboard_Page SHALL highlight it in green color (oversold)
8. WHEN RSI14 is between 30 and 70, THE Dashboard_Page SHALL display it in neutral color
9. THE Dashboard_Page SHALL label each RSI line with its timeframe identifier
10. THE Dashboard_Page SHALL group RSI indicators by timeframe within the card for clear comparison

### Requirement 6: MACD指标水平线可视化

**User Story:** 作为投资者，我想通过水平线看到4个周期的MACD指标位置，以便快速判断各周期的动能强弱和趋势方向。

#### Acceptance Criteria

1. THE Dashboard_Page SHALL display a single card showing MACD levels across all 4 timeframes
2. WHEN the MACD card is rendered, THE Dashboard_Page SHALL display DIF value as a horizontal line for each timeframe (1m, 1w, 1d, 4h)
3. WHEN the MACD card is rendered, THE Dashboard_Page SHALL display DEA value as a horizontal line for each timeframe
4. WHEN the MACD card is rendered, THE Dashboard_Page SHALL display MACD柱 value as a horizontal line for each timeframe
5. THE Dashboard_Page SHALL display a reference line at zero level
6. WHEN DIF is positive, THE Dashboard_Page SHALL highlight it in green color
7. WHEN DIF is negative, THE Dashboard_Page SHALL highlight it in red color
8. WHEN MACD柱 is positive, THE Dashboard_Page SHALL highlight it in green color
9. WHEN MACD柱 is negative, THE Dashboard_Page SHALL highlight it in red color
10. THE Dashboard_Page SHALL label each MACD line with its timeframe identifier
11. THE Dashboard_Page SHALL group MACD indicators by timeframe within the card for clear comparison

### Requirement 7: 数据获取与API集成

**User Story:** 作为系统，我需要从后端API获取技术指标数据，以便展示给用户。

#### Acceptance Criteria

1. WHEN the Dashboard_Page loads, THE Dashboard_Page SHALL fetch data from API_Backend endpoint /api/all
2. WHEN the Dashboard_Page loads, THE Dashboard_Page SHALL fetch data from API_Backend endpoint /api/latest
3. WHEN the API_Backend returns data, THE Dashboard_Page SHALL parse the JSON response
4. WHEN the API_Backend returns data, THE Dashboard_Page SHALL extract indicator values for each timeframe (1m, 1w, 1d, 4h)
5. IF the API_Backend request fails, THEN THE Dashboard_Page SHALL display an error message to the user
6. IF the API_Backend request fails, THEN THE Dashboard_Page SHALL include instructions to start the backend service

### Requirement 8: 自动刷新机制

**User Story:** 作为投资者，我想页面能自动刷新数据，以便持续监控市场变化而无需手动刷新。

#### Acceptance Criteria

1. THE Auto_Refresh SHALL fetch new data from API_Backend every 30 seconds
2. WHEN new data is fetched, THE Auto_Refresh SHALL update all Timeframe_Modules with the latest indicator values
3. THE Dashboard_Page SHALL display a visual indicator showing auto-refresh is active
4. THE Dashboard_Page SHALL display the timestamp of the last successful data update
5. THE Dashboard_Page SHALL provide a manual refresh button for immediate data update

### Requirement 9: 实时价格显示

**User Story:** 作为投资者，我想在页面顶部看到BTC的实时价格，以便快速了解当前市场价格。

#### Acceptance Criteria

1. THE Dashboard_Page SHALL fetch real-time BTC price from Binance API endpoint /api/v3/ticker/price
2. THE Dashboard_Page SHALL display the real-time price in the page header
3. WHEN the real-time price increases compared to previous fetch, THE Dashboard_Page SHALL display an upward arrow (↑) and green color
4. WHEN the real-time price decreases compared to previous fetch, THE Dashboard_Page SHALL display a downward arrow (↓) and red color
5. THE Dashboard_Page SHALL update the real-time price every 30 seconds along with Auto_Refresh

### Requirement 10: 数据格式化与显示精度

**User Story:** 作为投资者，我想看到格式化良好的数据，以便快速阅读和理解数值。

#### Acceptance Criteria

1. WHEN displaying price values, THE Dashboard_Page SHALL format them with 2 decimal places and dollar sign prefix
2. WHEN displaying price values greater than 1000, THE Dashboard_Page SHALL include thousand separators (e.g., $65,432.10)
3. WHEN displaying MACD values, THE Dashboard_Page SHALL format them with 0 decimal places
4. WHEN displaying RSI values, THE Dashboard_Page SHALL format them with 1 decimal place
5. WHEN displaying EMA and Bollinger Band values, THE Dashboard_Page SHALL format them as prices with 2 decimal places
6. WHEN displaying volume values, THE Dashboard_Page SHALL format them with thousand separators and 0 decimal places
7. WHEN displaying ATR values, THE Dashboard_Page SHALL format them with 0 decimal places

---

## Notes

### 技术栈说明
- **前端**: HTML + JavaScript
- **后端**: FastAPI (已有 web/api.py)
- **数据库**: MySQL (btc_assistant.klines表)
- **API端点**: /api/all, /api/latest, /api/klines

### 指标体系参考
本需求基于"BTC多时间周期投资框架"文档中定义的技术指标体系，包括：
- 均线系统：EMA7, EMA12, EMA25, EMA50, MA5, MA10
- MACD系统：DIF, DEA, MACD柱
- RSI：RSI14, RSI6
- 布林带：boll_up, boll_md, boll_dn
- 波动率：ATR

### 现有实现参考
项目中已有 web/index.html 实现了类似功能，新页面可以参考其设计模式，但需要按照本需求文档的规格进行独立实现。本版本专注于指标当前值的清晰展示，暂不包含历史趋势图表功能。
