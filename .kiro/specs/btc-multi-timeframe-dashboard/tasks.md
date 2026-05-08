# Implementation Plan: BTC Multi-Timeframe Dashboard

## Overview

This implementation plan breaks down the BTC Multi-Timeframe Dashboard into discrete coding tasks. The dashboard will display technical indicators across 4 timeframes (1m, 1w, 1d, 4h) using horizontal line visualizations in 3 cards: Price/EMA/Bollinger, RSI, and MACD.

**Technology Stack**: Vanilla JavaScript (ES6), HTML5, CSS3, SVG for visualizations

**Backend Integration**: Existing FastAPI backend at `web/api.py` (no modifications needed)

**File Structure**:
- `web/dashboard.html` - Main HTML page
- `web/dashboard.css` - Styles
- `web/dashboard.js` - Main application logic
- `web/components/` - 5 JavaScript modules

## Tasks

- [x] 1. Set up project structure and core utilities
  - Create `web/dashboard.html` with basic HTML structure (header, 3-card grid container, footer)
  - Create `web/dashboard.css` with CSS variables for color palette and responsive grid layout
  - Create `web/components/` directory for JavaScript modules
  - Create `web/components/ValueFormatter.js` with formatting functions for prices, percentages, and indicators
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7_

- [ ]* 1.1 Write unit tests for ValueFormatter
  - Test price formatting with 2 decimals and thousand separators
  - Test null/undefined value handling (should return "—")
  - Test percentage formatting with 1 decimal
  - Test integer formatting with thousand separators
  - Test MACD formatting (0 decimals)
  - Test RSI formatting (1 decimal)
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 2. Implement data fetching layer
  - [x] 2.1 Create DataFetcher class in `web/components/DataFetcher.js`
    - Implement `fetchLatestValues()` method to call `/api/latest` endpoint
    - Implement `fetchRealtimePrice()` method to call Binance API `/api/v3/ticker/price`
    - Implement `fetchAll()` method to fetch both data sources in parallel using `Promise.all()`
    - Implement retry logic (1 retry with 1-second delay) for network failures
    - Implement 10-second timeout for all requests
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 9.1_

  - [ ]* 2.2 Write integration tests for DataFetcher
    - Test successful fetch from `/api/latest` endpoint
    - Test successful fetch from Binance API
    - Test error handling for connection failures
    - Test timeout behavior
    - Test retry logic
    - _Requirements: 7.5, 7.6_

- [x] 3. Implement SVG visualization engine
  - [x] 3.1 Create SVGVisualizer class in `web/components/SVGVisualizer.js`
    - Implement `drawHorizontalLine(y, label, color, style)` method for indicator lines
    - Implement `drawMarker(y, label, color, shape)` method for price markers
    - Implement `drawReferenceLine(y, label, color)` method for RSI 30/70 and MACD 0 lines
    - Implement `drawYAxis(min, max, ticks)` method for Y-axis with tick marks
    - Implement `clear()` method to remove all SVG elements
    - Use SVG namespaces correctly for element creation
    - _Requirements: 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 5.2, 5.3, 5.4, 5.5, 6.2, 6.3, 6.4, 6.5_

  - [ ]* 3.2 Write unit tests for SVGVisualizer
    - Test horizontal line creation with correct attributes
    - Test marker creation with different shapes (circle, triangle, square)
    - Test reference line creation with dashed style
    - Test Y-axis generation with correct tick positions
    - Test clear() removes all elements
    - _Requirements: 4.2, 4.3, 4.4, 5.2, 6.2_

- [x] 4. Implement card rendering logic
  - [x] 4.1 Create CardRenderer class in `web/components/CardRenderer.js`
    - Implement constructor to accept card configuration (title, indicators, yAxisConfig, colorScheme)
    - Implement `render(data)` method to generate complete card with SVG visualization
    - Implement `update(data)` method to update existing card without full re-render
    - Implement `clear()` method to clear card content
    - Implement color coding logic for EMA (green if price above, red if below)
    - Implement color coding logic for MACD (green if positive, red if negative)
    - Implement color coding logic for RSI (red if >70, green if <30, neutral otherwise)
    - Calculate Y-axis scale automatically from min/max indicator values
    - Group indicators by timeframe for clear visual separation
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10, 3.11, 3.12, 4.7, 4.8, 5.6, 5.7, 5.8, 6.6, 6.7, 6.8, 6.9_

  - [ ]* 4.2 Write unit tests for color coding logic
    - Test EMA color based on price position (above/below)
    - Test RSI color based on overbought/oversold thresholds
    - Test MACD color based on positive/negative values
    - Test null value handling (should display "—")
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10, 3.11, 3.12_

- [x] 5. Implement dashboard controller
  - [x] 5.1 Create DashboardController class in `web/components/DashboardController.js`
    - Implement constructor to initialize DataFetcher and CardRenderer instances
    - Implement `initialize()` method to fetch initial data and render all 3 cards
    - Implement `refresh()` method to fetch latest data and update all cards
    - Implement `startAutoRefresh()` method to set up 30-second interval timer
    - Implement `stopAutoRefresh()` method to clear interval timer
    - Implement state management for latestData, realtimePrice, lastUpdate, isLoading, error
    - Implement error handling to display user-friendly error messages
    - Implement loading state display during data fetches
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 8.1, 8.2, 8.3, 8.4_

  - [ ]* 5.2 Write integration tests for DashboardController
    - Test initialization flow (fetch data, render cards)
    - Test refresh flow (fetch latest, update cards)
    - Test auto-refresh timer (verify 30-second interval)
    - Test error handling (backend not running)
    - Test loading state transitions
    - _Requirements: 7.5, 7.6, 8.1, 8.2_

- [ ] 6. Create Price/EMA/Bollinger card configuration and rendering
  - [x] 6.1 Define card configuration for Price/EMA/Bollinger card in `web/dashboard.js`
    - Configure indicators: close, ema7, ema25, ema50, boll_up, boll_md, boll_dn
    - Configure Y-axis as auto-scaling based on price range
    - Configure color scheme: Price (green/red), EMA (blue shades), Bollinger (red shades)
    - Configure line styles: solid for EMA, dashed for Bollinger bands
    - _Requirements: 1.2, 4.1, 4.2, 4.3, 4.7_

  - [~] 6.2 Implement Price card rendering in CardRenderer
    - Render horizontal lines for EMA7, EMA25, EMA50 for each timeframe
    - Render horizontal lines for Bollinger Bands (boll_up, boll_md, boll_dn) for each timeframe
    - Render price markers (circles) for current close price for each timeframe
    - Position lines proportionally based on price values
    - Label each line with timeframe and indicator name
    - Group indicators by timeframe (1m, 1w, 1d, 4h)
    - _Requirements: 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8_

- [ ] 7. Create RSI card configuration and rendering
  - [x] 7.1 Define card configuration for RSI card in `web/dashboard.js`
    - Configure indicators: rsi14, rsi6
    - Configure Y-axis as fixed 0-100 scale
    - Configure reference lines at 30 (oversold) and 70 (overbought)
    - Configure color scheme: Green (<30), Red (>70), Neutral (30-70)
    - _Requirements: 1.3, 5.1, 5.4, 5.5_

  - [~] 7.2 Implement RSI card rendering in CardRenderer
    - Render horizontal lines for RSI14 and RSI6 for each timeframe
    - Render reference lines at RSI 30 and 70 with dashed style
    - Position RSI lines on 0-100 scale
    - Apply color coding: red if >70, green if <30, neutral otherwise
    - Label each line with timeframe identifier
    - Group indicators by timeframe (1m, 1w, 1d, 4h)
    - _Requirements: 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 5.10_

- [ ] 8. Create MACD card configuration and rendering
  - [x] 8.1 Define card configuration for MACD card in `web/dashboard.js`
    - Configure indicators: dif, dea, macd
    - Configure Y-axis as auto-scaling based on MACD value range
    - Configure reference line at zero level
    - Configure color scheme: Green (positive), Red (negative)
    - _Requirements: 1.4, 6.1, 6.5_

  - [~] 8.2 Implement MACD card rendering in CardRenderer
    - Render horizontal lines for DIF, DEA, MACD柱 for each timeframe
    - Render reference line at zero level with dashed style
    - Apply color coding: green if positive, red if negative
    - Label each line with timeframe identifier
    - Group indicators by timeframe (1m, 1w, 1d, 4h)
    - _Requirements: 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 6.10, 6.11_

- [ ] 9. Implement realtime price display in header
  - [~] 9.1 Create realtime price display element in `web/dashboard.html` header
    - Add price display with large font size
    - Add direction arrow indicator (↑/↓)
    - Add timestamp display for last update
    - _Requirements: 9.2, 9.3, 9.4_

  - [~] 9.2 Implement realtime price update logic in DashboardController
    - Fetch BTC price from Binance API every 30 seconds
    - Compare with previous price to determine direction (up/down)
    - Update price display with green color and ↑ arrow if price increased
    - Update price display with red color and ↓ arrow if price decreased
    - Update timestamp display
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ] 10. Implement responsive layout and styling
  - [~] 10.1 Implement responsive grid layout in `web/dashboard.css`
    - Desktop (>1200px): 3-column grid for cards
    - Tablet/Mobile (<1200px): 1-column stack for cards
    - Use CSS Grid for layout
    - _Requirements: 1.5, 1.6_

  - [~] 10.2 Implement card styling in `web/dashboard.css`
    - Dark theme background (#0f1117)
    - Card background (#1a1d28)
    - Border color (#2a2d3a)
    - Text color (#e4e6f0)
    - Padding and spacing for readability
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

  - [~] 10.3 Implement SVG responsive behavior
    - SVG width: 100% of card width
    - SVG height: fixed 400px
    - Debounce window resize events (300ms delay)
    - Re-render cards on window resize
    - _Requirements: 4.1, 5.1, 6.1_

- [ ] 11. Implement auto-refresh and manual refresh
  - [~] 11.1 Implement auto-refresh timer in DashboardController
    - Start 30-second interval timer on page load
    - Fetch latest data from `/api/latest` and Binance API
    - Update all 3 cards with new data
    - Update timestamp display
    - _Requirements: 8.1, 8.2, 8.4_

  - [~] 11.2 Add manual refresh button in `web/dashboard.html` header
    - Add refresh button with icon
    - Wire button click to DashboardController.refresh() method
    - Show loading indicator during refresh
    - Update timestamp after successful refresh
    - _Requirements: 8.5_

  - [~] 11.3 Add visual indicator for auto-refresh status
    - Display "Auto-refresh: ON" indicator in header
    - Display last update timestamp in human-readable format
    - Update timestamp on each successful refresh
    - _Requirements: 8.3, 8.4_

- [ ] 12. Implement error handling and loading states
  - [~] 12.1 Create error message component in `web/dashboard.html`
    - Add error message container with icon, title, details, and retry button
    - Style error message with warning colors
    - Hide by default, show when error occurs
    - _Requirements: 7.5, 7.6_

  - [~] 12.2 Implement error handling in DashboardController
    - Catch network errors and display user-friendly message
    - Include troubleshooting steps (e.g., "Start backend: uvicorn web.api:app --reload")
    - Provide retry button to attempt fetch again
    - Log detailed error to console for debugging
    - _Requirements: 7.5, 7.6_

  - [~] 12.3 Implement loading state display
    - Show loading spinner during initial data fetch
    - Show loading indicator during manual refresh
    - Disable refresh button during loading
    - Hide loading state after data is loaded or error occurs
    - _Requirements: 7.1, 7.2, 8.1_

- [ ] 13. Wire all components together in main application
  - [x] 13.1 Create main application entry point in `web/dashboard.js`
    - Import all component modules (DashboardController, DataFetcher, CardRenderer, SVGVisualizer, ValueFormatter)
    - Initialize DashboardController with configuration (API base URL, refresh interval, timeframes)
    - Call DashboardController.initialize() on page load
    - Start auto-refresh timer
    - Wire manual refresh button to DashboardController.refresh()
    - _Requirements: 1.1, 7.1, 8.1, 8.5_

  - [~] 13.2 Add accessibility features
    - Add ARIA labels to SVG elements for screen readers
    - Ensure refresh button is keyboard accessible (tab navigation)
    - Add visible focus indicators for interactive elements
    - Ensure color contrast meets WCAG AA standards (4.5:1 ratio)
    - _Requirements: 1.1, 8.5_

- [ ]* 14. End-to-end testing
  - Test dashboard loads and displays all 3 cards correctly
  - Test realtime price displays in header with direction arrow
  - Test auto-refresh updates data every 30 seconds
  - Test manual refresh button updates data immediately
  - Test error message displays when backend is not running
  - Test responsive layout on desktop (>1200px) and mobile (<1200px)
  - Test color coding for EMA, RSI, and MACD indicators
  - Test null value handling (displays "—")
  - Test number formatting (decimals, thousand separators)
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 2.6, 3.1-3.12, 7.5, 8.1, 8.5, 9.2, 9.3, 9.4, 10.1-10.7_

- [~] 15. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- The implementation uses vanilla JavaScript (ES6) with no framework dependencies
- SVG is used for horizontal line visualizations due to precise positioning and styling capabilities
- The existing FastAPI backend (`web/api.py`) is used as-is with no modifications
- Auto-refresh interval is 30 seconds to balance real-time updates with API load
- Color palette follows dark theme design: bg (#0f1117), card (#1a1d28), green (#22c55e), red (#ef4444)
- Responsive breakpoint: 1200px (3-column grid above, 1-column stack below)
- Browser compatibility: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+ (no polyfills needed)

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "2.1", "3.1"] },
    { "id": 1, "tasks": ["2.2", "3.2", "4.1"] },
    { "id": 2, "tasks": ["4.2", "5.1", "6.1", "7.1", "8.1"] },
    { "id": 3, "tasks": ["5.2", "6.2", "7.2", "8.2", "9.1"] },
    { "id": 4, "tasks": ["9.2", "10.1", "10.2", "10.3"] },
    { "id": 5, "tasks": ["11.1", "11.2", "11.3", "12.1"] },
    { "id": 6, "tasks": ["12.2", "12.3", "13.1"] },
    { "id": 7, "tasks": ["13.2", "14"] }
  ]
}
```
