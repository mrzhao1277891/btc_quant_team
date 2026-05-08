/**
 * CardRenderer.test.js
 * 
 * Unit tests for CardRenderer class
 */

import { CardRenderer } from './CardRenderer.js';
import { ValueFormatter } from './ValueFormatter.js';

// Mock DOM environment
const setupDOM = () => {
    // Create container element
    const container = document.createElement('div');
    container.id = 'test-card-container';
    document.body.appendChild(container);
    return container;
};

const cleanupDOM = () => {
    const container = document.getElementById('test-card-container');
    if (container) {
        container.remove();
    }
};

// Mock data for testing
const mockData = {
    '1m': {
        close: 65000,
        ema7: 65500,
        ema25: 65000,
        ema50: 64500,
        rsi14: 65.4,
        rsi6: 70.2,
        dif: 123,
        dea: 100,
        macd: 23,
        boll_up: 66000,
        boll_md: 65000,
        boll_dn: 64000
    },
    '1w': {
        close: 64000,
        ema7: 64500,
        ema25: 64000,
        ema50: 63500,
        rsi14: 55.0,
        rsi6: 60.0,
        dif: -50,
        dea: -30,
        macd: -20,
        boll_up: 65000,
        boll_md: 64000,
        boll_dn: 63000
    },
    '1d': {
        close: 65500,
        ema7: 66000,
        ema25: 65500,
        ema50: 65000,
        rsi14: 75.0,
        rsi6: 80.0,
        dif: 200,
        dea: 180,
        macd: 20,
        boll_up: 67000,
        boll_md: 65500,
        boll_dn: 64000
    },
    '4h': {
        close: 65200,
        ema7: 65700,
        ema25: 65200,
        ema50: 64700,
        rsi14: 25.0,
        rsi6: 20.0,
        dif: 50,
        dea: 40,
        macd: 10,
        boll_up: 66200,
        boll_md: 65200,
        boll_dn: 64200
    }
};

// Test configurations
const priceCardConfig = {
    title: 'Price & Moving Averages',
    indicators: [
        { key: 'close', label: 'Price', style: 'solid', markerShape: 'circle' },
        { key: 'ema7', label: 'EMA7', style: 'solid' },
        { key: 'ema25', label: 'EMA25', style: 'dashed' },
        { key: 'ema50', label: 'EMA50', style: 'dotted' },
        { key: 'boll_up', label: 'BB Upper', style: 'dashed' },
        { key: 'boll_md', label: 'BB Mid', style: 'solid' },
        { key: 'boll_dn', label: 'BB Lower', style: 'dashed' }
    ],
    yAxisConfig: {
        type: 'auto'
    },
    colorScheme: {}
};

const rsiCardConfig = {
    title: 'RSI Indicators',
    indicators: [
        { key: 'rsi14', label: 'RSI(14)', style: 'solid', markerShape: 'circle' },
        { key: 'rsi6', label: 'RSI(6)', style: 'dashed', markerShape: 'square' }
    ],
    yAxisConfig: {
        type: 'fixed',
        min: 0,
        max: 100
    },
    referenceLines: [
        { value: 70, label: '70 (Overbought)' },
        { value: 30, label: '30 (Oversold)' }
    ],
    colorScheme: {}
};

const macdCardConfig = {
    title: 'MACD Indicators',
    indicators: [
        { key: 'dif', label: 'DIF', style: 'solid' },
        { key: 'dea', label: 'DEA', style: 'dashed' },
        { key: 'macd', label: 'MACD', style: 'solid', markerShape: 'triangle' }
    ],
    yAxisConfig: {
        type: 'auto'
    },
    referenceLines: [
        { value: 0, label: 'Zero Line' }
    ],
    colorScheme: {}
};

describe('CardRenderer', () => {
    let container;

    beforeEach(() => {
        container = setupDOM();
    });

    afterEach(() => {
        cleanupDOM();
    });

    describe('Constructor', () => {
        test('should create CardRenderer instance with valid config', () => {
            const renderer = new CardRenderer('test-card-container', priceCardConfig);
            
            expect(renderer).toBeDefined();
            expect(renderer.containerId).toBe('test-card-container');
            expect(renderer.config).toEqual(priceCardConfig);
            expect(renderer.timeframes).toEqual(['1m', '1w', '1d', '4h']);
        });

        test('should initialize with default color scheme', () => {
            const renderer = new CardRenderer('test-card-container', priceCardConfig);
            
            expect(renderer.colors).toBeDefined();
            expect(renderer.colors.positive).toBe('#22c55e');
            expect(renderer.colors.negative).toBe('#ef4444');
            expect(renderer.colors.neutral).toBe('#8a8fa8');
        });
    });

    describe('render()', () => {
        test('should render card with SVG element', () => {
            const renderer = new CardRenderer('test-card-container', priceCardConfig);
            renderer.render(mockData);
            
            const cardElement = container.querySelector('.indicator-card');
            expect(cardElement).toBeTruthy();
            
            const svg = container.querySelector('svg');
            expect(svg).toBeTruthy();
            expect(svg.getAttribute('height')).toBe('400');
        });

        test('should render card title', () => {
            const renderer = new CardRenderer('test-card-container', priceCardConfig);
            renderer.render(mockData);
            
            const title = container.querySelector('.card-title');
            expect(title).toBeTruthy();
            expect(title.textContent).toBe('Price & Moving Averages');
        });

        test('should handle missing container gracefully', () => {
            const renderer = new CardRenderer('non-existent-container', priceCardConfig);
            
            // Should not throw error
            expect(() => renderer.render(mockData)).not.toThrow();
        });

        test('should store current data after render', () => {
            const renderer = new CardRenderer('test-card-container', priceCardConfig);
            renderer.render(mockData);
            
            expect(renderer.getData()).toEqual(mockData);
        });
    });

    describe('update()', () => {
        test('should update existing card with new data', () => {
            const renderer = new CardRenderer('test-card-container', priceCardConfig);
            renderer.render(mockData);
            
            const updatedData = {
                ...mockData,
                '1m': { ...mockData['1m'], close: 66000 }
            };
            
            renderer.update(updatedData);
            
            expect(renderer.getData()).toEqual(updatedData);
        });

        test('should perform full render if not initialized', () => {
            const renderer = new CardRenderer('test-card-container', priceCardConfig);
            
            // Call update without render first
            renderer.update(mockData);
            
            const cardElement = container.querySelector('.indicator-card');
            expect(cardElement).toBeTruthy();
        });
    });

    describe('clear()', () => {
        test('should clear card content', () => {
            const renderer = new CardRenderer('test-card-container', priceCardConfig);
            renderer.render(mockData);
            
            renderer.clear();
            
            expect(container.innerHTML).toBe('');
            expect(renderer.getData()).toBeNull();
        });

        test('should handle clear on uninitialized card', () => {
            const renderer = new CardRenderer('test-card-container', priceCardConfig);
            
            // Should not throw error
            expect(() => renderer.clear()).not.toThrow();
        });
    });

    describe('_calculateYAxisScale()', () => {
        test('should return fixed scale when configured', () => {
            const renderer = new CardRenderer('test-card-container', rsiCardConfig);
            const { min, max } = renderer._calculateYAxisScale(mockData);
            
            expect(min).toBe(0);
            expect(max).toBe(100);
        });

        test('should auto-calculate scale from data', () => {
            const renderer = new CardRenderer('test-card-container', priceCardConfig);
            const { min, max } = renderer._calculateYAxisScale(mockData);
            
            // Should include all indicator values with 10% padding
            expect(min).toBeLessThan(63000); // Lowest value in mock data
            expect(max).toBeGreaterThan(67000); // Highest value in mock data
        });

        test('should handle empty data gracefully', () => {
            const renderer = new CardRenderer('test-card-container', priceCardConfig);
            const { min, max } = renderer._calculateYAxisScale({});
            
            expect(min).toBe(0);
            expect(max).toBe(100);
        });

        test('should handle null indicator values', () => {
            const renderer = new CardRenderer('test-card-container', priceCardConfig);
            const dataWithNulls = {
                '1m': { close: 65000, ema7: null, ema25: undefined, ema50: 64500 }
            };
            
            const { min, max } = renderer._calculateYAxisScale(dataWithNulls);
            
            // Should only use valid values
            expect(min).toBeLessThan(64500);
            expect(max).toBeGreaterThan(65000);
        });
    });

    describe('_getIndicatorColor()', () => {
        test('should return green for EMA when price is above', () => {
            const renderer = new CardRenderer('test-card-container', priceCardConfig);
            const timeframeData = { close: 65000, ema7: 64500 };
            
            const color = renderer._getIndicatorColor('ema7', 64500, timeframeData);
            
            expect(color).toBe(renderer.colors.positive); // green
        });

        test('should return red for EMA when price is below', () => {
            const renderer = new CardRenderer('test-card-container', priceCardConfig);
            const timeframeData = { close: 65000, ema7: 65500 };
            
            const color = renderer._getIndicatorColor('ema7', 65500, timeframeData);
            
            expect(color).toBe(renderer.colors.negative); // red
        });

        test('should return green for positive MACD', () => {
            const renderer = new CardRenderer('test-card-container', macdCardConfig);
            const timeframeData = { dif: 123 };
            
            const color = renderer._getIndicatorColor('dif', 123, timeframeData);
            
            expect(color).toBe(renderer.colors.positive); // green
        });

        test('should return red for negative MACD', () => {
            const renderer = new CardRenderer('test-card-container', macdCardConfig);
            const timeframeData = { dif: -50 };
            
            const color = renderer._getIndicatorColor('dif', -50, timeframeData);
            
            expect(color).toBe(renderer.colors.negative); // red
        });

        test('should return red for overbought RSI (>70)', () => {
            const renderer = new CardRenderer('test-card-container', rsiCardConfig);
            const timeframeData = { rsi14: 75 };
            
            const color = renderer._getIndicatorColor('rsi14', 75, timeframeData);
            
            expect(color).toBe(renderer.colors.overbought); // red
        });

        test('should return green for oversold RSI (<30)', () => {
            const renderer = new CardRenderer('test-card-container', rsiCardConfig);
            const timeframeData = { rsi14: 25 };
            
            const color = renderer._getIndicatorColor('rsi14', 25, timeframeData);
            
            expect(color).toBe(renderer.colors.oversold); // green
        });

        test('should return neutral for RSI between 30-70', () => {
            const renderer = new CardRenderer('test-card-container', rsiCardConfig);
            const timeframeData = { rsi14: 50 };
            
            const color = renderer._getIndicatorColor('rsi14', 50, timeframeData);
            
            expect(color).toBe(renderer.colors.neutral); // gray
        });
    });

    describe('_valueToNormalizedY()', () => {
        test('should convert value to normalized Y position', () => {
            const renderer = new CardRenderer('test-card-container', priceCardConfig);
            
            // Value at max should be at top (0)
            expect(renderer._valueToNormalizedY(100, 0, 100)).toBe(0);
            
            // Value at min should be at bottom (1)
            expect(renderer._valueToNormalizedY(0, 0, 100)).toBe(1);
            
            // Value at middle should be at center (0.5)
            expect(renderer._valueToNormalizedY(50, 0, 100)).toBe(0.5);
        });

        test('should handle equal min and max', () => {
            const renderer = new CardRenderer('test-card-container', priceCardConfig);
            
            // Should return center position
            expect(renderer._valueToNormalizedY(50, 50, 50)).toBe(0.5);
        });
    });

    describe('Integration Tests', () => {
        test('should render price card with all indicators', () => {
            const renderer = new CardRenderer('test-card-container', priceCardConfig);
            renderer.render(mockData);
            
            const svg = container.querySelector('svg');
            expect(svg).toBeTruthy();
            
            // Should have Y-axis
            const yAxis = svg.querySelector('.y-axis');
            expect(yAxis).toBeTruthy();
            
            // Should have horizontal lines
            const lines = svg.querySelectorAll('.horizontal-line');
            expect(lines.length).toBeGreaterThan(0);
        });

        test('should render RSI card with reference lines', () => {
            const renderer = new CardRenderer('test-card-container', rsiCardConfig);
            renderer.render(mockData);
            
            const svg = container.querySelector('svg');
            expect(svg).toBeTruthy();
            
            // Should have reference lines (70 and 30)
            const refLines = svg.querySelectorAll('.reference-line');
            expect(refLines.length).toBe(2);
        });

        test('should render MACD card with zero line', () => {
            const renderer = new CardRenderer('test-card-container', macdCardConfig);
            renderer.render(mockData);
            
            const svg = container.querySelector('svg');
            expect(svg).toBeTruthy();
            
            // Should have reference line at zero
            const refLines = svg.querySelectorAll('.reference-line');
            expect(refLines.length).toBe(1);
        });

        test('should handle data updates correctly', () => {
            const renderer = new CardRenderer('test-card-container', priceCardConfig);
            renderer.render(mockData);
            
            const initialData = renderer.getData();
            expect(initialData['1m'].close).toBe(65000);
            
            const updatedData = {
                ...mockData,
                '1m': { ...mockData['1m'], close: 66000 }
            };
            
            renderer.update(updatedData);
            
            const newData = renderer.getData();
            expect(newData['1m'].close).toBe(66000);
        });
    });
});
