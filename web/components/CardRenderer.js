/**
 * CardRenderer.js
 * 
 * Renders individual visualization cards with horizontal lines for technical indicators.
 * Manages card lifecycle: render, update, and clear operations.
 * 
 * Requirements: 3.1-3.12, 4.7-4.8, 5.6-5.10, 6.6-6.11
 */

import { SVGVisualizer } from './SVGVisualizer.js';
import { ValueFormatter } from './ValueFormatter.js';

export class CardRenderer {
    /**
     * Create a new CardRenderer instance
     * 
     * @param {string} containerId - DOM element ID where the card will be rendered
     * @param {Object} cardConfig - Card configuration object
     * @param {string} cardConfig.title - Card title
     * @param {Array} cardConfig.indicators - Array of indicator configurations
     * @param {Object} cardConfig.yAxisConfig - Y-axis configuration
     * @param {Object} cardConfig.colorScheme - Color scheme for indicators
     */
    constructor(containerId, cardConfig) {
        this.containerId = containerId;
        this.config = cardConfig;
        this.container = null;
        this.svgVisualizer = null;
        this.currentData = null;
        
        // Timeframe display order
        this.timeframes = ['1m', '1w', '1d', '4h'];
        
        // Timeframe labels for display
        this.timeframeLabels = {
            '1m': '月线',
            '1w': '周线',
            '1d': '日线',
            '4h': '4小时'
        };
        
        // Color palette
        this.colors = {
            positive: '#22c55e',  // green
            negative: '#ef4444',  // red
            neutral: '#8a8fa8',   // gray
            overbought: '#ef4444', // red
            oversold: '#22c55e',  // green
            ema7: '#3b82f6',      // blue
            ema25: '#8b5cf6',     // purple
            ema50: '#06b6d4',     // cyan
            bollUp: '#f87171',    // light red
            bollMd: '#fb923c',    // orange
            bollDn: '#fbbf24',    // yellow
            price: '#22c55e',     // green (default, changes based on trend)
            reference: '#444',    // dark gray for reference lines
            ...cardConfig.colorScheme
        };
    }

    /**
     * Render the card with complete visualization
     * 
     * @param {Object} data - Data object with timeframe keys (1m, 1w, 1d, 4h)
     * 
     * Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8
     */
    render(data) {
        this.currentData = data;
        
        // Get or create container element
        this.container = document.getElementById(this.containerId);
        if (!this.container) {
            console.error(`Container element with id "${this.containerId}" not found`);
            return;
        }
        
        // Clear existing content
        this.container.innerHTML = '';
        
        // Create SVG container (no need for card structure, HTML already has it)
        const svgContainer = document.createElement('div');
        svgContainer.className = 'svg-container';
        
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', '100%');
        svg.setAttribute('height', '400');
        svg.setAttribute('class', 'indicator-card-svg');
        
        svgContainer.appendChild(svg);
        this.container.appendChild(svgContainer);
        
        // Initialize SVG visualizer
        this.svgVisualizer = new SVGVisualizer(svg, {
            width: svg.clientWidth || 800,
            height: 400,
            padding: { top: 30, right: 120, bottom: 30, left: 80 },
            yAxisConfig: this.config.yAxisConfig
        });
        
        // Calculate Y-axis scale from data
        const { min, max } = this._calculateYAxisScale(data);
        
        // Draw Y-axis
        this.svgVisualizer.drawYAxis(min, max, 6);
        
        // Draw reference lines if configured
        this._drawReferenceLines(min, max);
        
        // Draw current price reference line (for EMA card)
        this._drawPriceReferenceLine(data, min, max);
        
        // Draw indicator lines grouped by timeframe
        this._drawIndicatorLines(data, min, max);
    }

    /**
     * Update existing card with new data without full re-render
     * 
     * @param {Object} data - Updated data object with timeframe keys
     * 
     * Requirements: 4.2
     */
    update(data) {
        if (!this.svgVisualizer || !this.container) {
            // If not initialized, do full render
            this.render(data);
            return;
        }
        
        this.currentData = data;
        
        // Clear SVG content
        this.svgVisualizer.clear();
        
        // Recalculate Y-axis scale
        const { min, max } = this._calculateYAxisScale(data);
        
        // Redraw Y-axis
        this.svgVisualizer.drawYAxis(min, max, 6);
        
        // Redraw reference lines
        this._drawReferenceLines(min, max);
        
        // Redraw current price reference line (for EMA card)
        this._drawPriceReferenceLine(data, min, max);
        
        // Redraw indicator lines
        this._drawIndicatorLines(data, min, max);
    }

    /**
     * Clear card content
     * 
     * Requirements: 4.3
     */
    clear() {
        if (this.svgVisualizer) {
            this.svgVisualizer.clear();
        }
        
        if (this.container) {
            this.container.innerHTML = '';
        }
        
        this.currentData = null;
    }

    /**
     * Calculate Y-axis scale from min/max indicator values
     * 
     * @param {Object} data - Data object with timeframe keys
     * @returns {Object} Object with min and max values
     * 
     * Requirements: 4.8
     */
    _calculateYAxisScale(data) {
        const { yAxisConfig } = this.config;
        
        // If fixed scale is configured, use it
        if (yAxisConfig.type === 'fixed') {
            return {
                min: yAxisConfig.min,
                max: yAxisConfig.max
            };
        }
        
        // Auto-calculate from data
        let min = Infinity;
        let max = -Infinity;
        
        // Collect all indicator values
        const values = [];
        
        for (const timeframe of this.timeframes) {
            const timeframeData = data[timeframe];
            if (!timeframeData) continue;
            
            for (const indicator of this.config.indicators) {
                const value = timeframeData[indicator.key];
                if (ValueFormatter.isValidNumber(value)) {
                    values.push(value);
                }
            }
        }
        
        if (values.length === 0) {
            // No valid data, use default range
            return { min: 0, max: 100 };
        }
        
        min = Math.min(...values);
        max = Math.max(...values);
        
        // Add 10% padding to top and bottom
        const range = max - min;
        const padding = range * 0.1;
        
        return {
            min: min - padding,
            max: max + padding
        };
    }

    /**
     * Draw reference lines (e.g., RSI 30/70, MACD 0)
     * 
     * @param {number} min - Y-axis minimum value
     * @param {number} max - Y-axis maximum value
     * 
     * Requirements: 5.4, 6.5
     */
    _drawReferenceLines(min, max) {
        const { referenceLines } = this.config;
        
        if (!referenceLines || referenceLines.length === 0) {
            return;
        }
        
        for (const refLine of referenceLines) {
            const { value, label } = refLine;
            
            // Convert value to normalized Y position (0-1)
            const normalizedY = this._valueToNormalizedY(value, min, max);
            
            // Draw reference line
            this.svgVisualizer.drawReferenceLine(
                normalizedY,
                label,
                this.colors.reference
            );
        }
    }

    /**
     * Draw current price reference line (for EMA card)
     * 
     * @param {Object} data - Data object with timeframe keys
     * @param {number} min - Y-axis minimum value
     * @param {number} max - Y-axis maximum value
     */
    _drawPriceReferenceLine(data, min, max) {
        // Only draw price line for EMA and Bollinger cards
        const hasEMA = this.config.indicators.some(ind => 
            ind.key === 'ema7' || ind.key === 'ema25' || ind.key === 'ema50'
        );
        const hasBollinger = this.config.indicators.some(ind => 
            ind.key === 'boll_up' || ind.key === 'boll_md' || ind.key === 'boll_dn'
        );
        
        if (!hasEMA && !hasBollinger) {
            return;
        }
        
        // Get current price from the most important timeframe (1m - monthly)
        const monthlyData = data['1m'];
        if (!monthlyData || !ValueFormatter.isValidNumber(monthlyData.close)) {
            return;
        }
        
        const currentPrice = monthlyData.close;
        const normalizedY = this._valueToNormalizedY(currentPrice, min, max);
        
        // Format price for display
        const formattedPrice = ValueFormatter.formatPrice(currentPrice);
        
        // Draw price reference line
        this.svgVisualizer.drawPriceReferenceLine(
            normalizedY,
            `当前价格: ${formattedPrice}`,
            '#22c55e'  // green color for price
        );
    }

    /**
     * Draw indicator lines grouped by timeframe with dot visualization
     * 
     * @param {Object} data - Data object with timeframe keys
     * @param {number} min - Y-axis minimum value
     * @param {number} max - Y-axis maximum value
     * 
     * Requirements: 4.8, 5.10, 6.11
     */
    _drawIndicatorLines(data, min, max) {
        // Timeframe visual hierarchy (importance: 1m > 1w > 1d > 4h)
        // X-axis is divided into 4 zones, one per timeframe
        const timeframeStyles = {
            '1m': { 
                xZoneStart: 0.0, 
                xZoneEnd: 0.25, 
                color: '#ef4444',  // red - 月线最重要
                order: 1 
            },
            '1w': { 
                xZoneStart: 0.25, 
                xZoneEnd: 0.5, 
                color: '#f59e0b',  // yellow/amber - 周线
                order: 2 
            },
            '1d': { 
                xZoneStart: 0.5, 
                xZoneEnd: 0.75, 
                color: '#3b82f6',  // blue - 日线
                order: 3 
            },
            '4h': { 
                xZoneStart: 0.75, 
                xZoneEnd: 1.0, 
                color: '#22c55e',  // green - 4小时
                order: 4 
            }
        };
        
        // Indicator-specific dot sizes (for cards like EMA where indicators differ)
        const indicatorSizes = {
            'ema50': 9,  // 长期均线最重要
            'ema25': 7,  // 中期均线
            'ema7': 5,   // 短期均线
            'boll_up': 8,
            'boll_md': 7,
            'boll_dn': 6,
            'rsi14': 8,
            'rsi6': 6,
            'dif': 8,
            'dea': 7,
            'macd': 6
        };
        
        // Draw zone separators
        this.svgVisualizer.drawZoneSeparators();
        
        // Draw zone labels at the bottom
        this.svgVisualizer.drawZoneLabels([
            { label: '月线', xStart: 0.0, xEnd: 0.25 },
            { label: '周线', xStart: 0.25, xEnd: 0.5 },
            { label: '日线', xStart: 0.5, xEnd: 0.75 },
            { label: '4小时', xStart: 0.75, xEnd: 1.0 }
        ]);
        
        // Collect all data points
        const allPoints = [];
        
        for (const timeframe of this.timeframes) {
            const timeframeData = data[timeframe];
            if (!timeframeData) continue;
            
            const timeframeLabel = this.timeframeLabels[timeframe];
            const style = timeframeStyles[timeframe];
            
            // Calculate X position within the zone (evenly distribute indicators)
            const indicatorCount = this.config.indicators.length;
            const zoneWidth = style.xZoneEnd - style.xZoneStart;
            
            this.config.indicators.forEach((indicator, index) => {
                const value = timeframeData[indicator.key];
                
                // Skip null/undefined values
                if (!ValueFormatter.isValidNumber(value)) {
                    return;
                }
                
                // Calculate X position (center of each indicator slot within zone)
                const slotWidth = zoneWidth / indicatorCount;
                const xPos = style.xZoneStart + (index + 0.5) * slotWidth;
                
                // Convert value to normalized Y position
                const yPos = this._valueToNormalizedY(value, min, max);
                
                // Format value for display
                const formattedValue = ValueFormatter.formatIndicator(
                    value,
                    indicator.key
                );
                
                // Use timeframe color (周期决定颜色)
                const dotColor = style.color;
                
                // Use indicator-specific size (指标决定大小)
                const dotSize = indicatorSizes[indicator.key] || 7;
                
                allPoints.push({
                    xPos,
                    yPos,
                    value,
                    formattedValue,
                    timeframe,
                    timeframeLabel,
                    indicatorKey: indicator.key,
                    indicatorLabel: indicator.label,
                    dotSize: dotSize,
                    color: dotColor
                });
            });
        }
        
        // Draw all data points
        for (const point of allPoints) {
            this.svgVisualizer.drawDataPoint(
                point.xPos,
                point.yPos,
                point.dotSize,
                point.color,
                {
                    timeframe: point.timeframeLabel,
                    indicator: point.indicatorLabel,
                    value: point.formattedValue
                }
            );
        }
    }

    /**
     * Get color for indicator based on value and type
     * 
     * @param {string} indicatorKey - Indicator key (e.g., 'ema7', 'rsi14')
     * @param {number} value - Indicator value
     * @param {Object} timeframeData - Complete timeframe data for reference
     * @returns {string} Color hex code
     * 
     * Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10, 3.11, 3.12
     */
    _getIndicatorColor(indicatorKey, value, timeframeData) {
        const closePrice = timeframeData.close;
        
        // EMA color coding: green if price above EMA, red if below
        if (indicatorKey.startsWith('ema')) {
            if (ValueFormatter.isValidNumber(closePrice)) {
                return closePrice > value ? this.colors.positive : this.colors.negative;
            }
            // Default EMA colors if no price reference
            if (indicatorKey === 'ema7') return this.colors.ema7;
            if (indicatorKey === 'ema25') return this.colors.ema25;
            if (indicatorKey === 'ema50') return this.colors.ema50;
            return this.colors.neutral;
        }
        
        // MACD color coding: green if positive, red if negative
        if (indicatorKey === 'macd' || indicatorKey === 'dif' || indicatorKey === 'dea') {
            if (value > 0) return this.colors.positive;
            if (value < 0) return this.colors.negative;
            return this.colors.neutral;
        }
        
        // RSI color coding: red if >70 (overbought), green if <30 (oversold), neutral otherwise
        if (indicatorKey === 'rsi14' || indicatorKey === 'rsi6') {
            if (value > 70) return this.colors.overbought;
            if (value < 30) return this.colors.oversold;
            return this.colors.neutral;
        }
        
        // Bollinger Bands color coding
        if (indicatorKey === 'boll_up') return this.colors.bollUp;
        if (indicatorKey === 'boll_md') return this.colors.bollMd;
        if (indicatorKey === 'boll_dn') return this.colors.bollDn;
        
        // Price color coding (default green, can be customized)
        if (indicatorKey === 'close') {
            return this.colors.price;
        }
        
        // Default neutral color
        return this.colors.neutral;
    }

    /**
     * Convert a value to normalized Y position (0-1)
     * 
     * @param {number} value - Value to convert
     * @param {number} min - Y-axis minimum
     * @param {number} max - Y-axis maximum
     * @returns {number} Normalized Y position (0 = top, 1 = bottom)
     */
    _valueToNormalizedY(value, min, max) {
        if (max === min) {
            return 0.5; // Center if no range
        }
        
        // Invert because SVG Y increases downward
        // Higher values should be at top (lower Y coordinate)
        return 1 - (value - min) / (max - min);
    }

    /**
     * Get current card data
     * 
     * @returns {Object|null} Current data object
     */
    getData() {
        return this.currentData;
    }

    /**
     * Get card configuration
     * 
     * @returns {Object} Card configuration object
     */
    getConfig() {
        return this.config;
    }
}

export default CardRenderer;
