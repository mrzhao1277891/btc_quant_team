/**
 * dashboard.js
 * 
 * Main application entry point for BTC Multi-Timeframe Dashboard.
 * Initializes all components, defines card configurations, and manages application lifecycle.
 * 
 * Requirements: 1.2, 1.3, 1.4, 5.1, 6.1, 7.1, 8.1, 8.5
 */

// Import component modules
const { DashboardController } = require('./components/DashboardController.js');

// ============================================================================
// Card Configurations
// ============================================================================

/**
 * Price/EMA/Bollinger Card Configuration
 * 
 * Displays current price, moving averages (EMA7, EMA25, EMA50), and Bollinger Bands
 * across all 4 timeframes (1m, 1w, 1d, 4h).
 * 
 * Requirements: 1.2, 4.1, 4.2, 4.3, 4.7, 6.1
 */
const priceCardConfig = {
    containerId: 'price-card',
    title: 'Price & Moving Averages',
    indicators: [
        // Close price
        {
            key: 'close',
            label: 'Price',
            style: 'solid',
            markerShape: 'circle'
        },
        // EMA indicators
        {
            key: 'ema7',
            label: 'EMA7',
            style: 'solid',
            markerShape: null
        },
        {
            key: 'ema25',
            label: 'EMA25',
            style: 'solid',
            markerShape: null
        },
        {
            key: 'ema50',
            label: 'EMA50',
            style: 'solid',
            markerShape: null
        },
        // Bollinger Bands
        {
            key: 'boll_up',
            label: 'BB Upper',
            style: 'dashed',
            markerShape: null
        },
        {
            key: 'boll_md',
            label: 'BB Middle',
            style: 'dashed',
            markerShape: null
        },
        {
            key: 'boll_dn',
            label: 'BB Lower',
            style: 'dashed',
            markerShape: null
        }
    ],
    yAxisConfig: {
        type: 'auto',  // Auto-scale based on price range
        ticks: 6,
        formatter: (value) => `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
    },
    colorScheme: {
        positive: '#22c55e',  // green
        negative: '#ef4444',  // red
        neutral: '#8a8fa8',   // gray
        ema7: '#3b82f6',      // blue
        ema25: '#8b5cf6',     // purple
        ema50: '#06b6d4',     // cyan
        bollUp: '#f87171',    // light red
        bollMd: '#fb923c',    // orange
        bollDn: '#fbbf24',    // yellow
        price: '#22c55e'      // green (default)
    },
    referenceLines: []  // No reference lines for price card
};

/**
 * RSI Card Configuration
 * 
 * Displays RSI14 and RSI6 indicators across all 4 timeframes (1m, 1w, 1d, 4h).
 * Includes reference lines at 30 (oversold) and 70 (overbought).
 * 
 * Requirements: 1.3, 5.1, 5.4, 5.5, 7.1
 */
const rsiCardConfig = {
    containerId: 'rsi-card',
    title: 'RSI Indicators',
    indicators: [
        {
            key: 'rsi14',
            label: 'RSI(14)',
            style: 'solid',
            markerShape: 'circle'
        },
        {
            key: 'rsi6',
            label: 'RSI(6)',
            style: 'solid',
            markerShape: 'triangle'
        }
    ],
    yAxisConfig: {
        type: 'fixed',  // Fixed 0-100 scale for RSI
        min: 0,
        max: 100,
        ticks: 6,
        formatter: (value) => value.toFixed(1)
    },
    colorScheme: {
        positive: '#22c55e',    // green
        negative: '#ef4444',    // red
        neutral: '#8a8fa8',     // gray
        overbought: '#ef4444',  // red (>70)
        oversold: '#22c55e'     // green (<30)
    },
    referenceLines: [
        {
            value: 70,
            label: '70 (Overbought)'
        },
        {
            value: 30,
            label: '30 (Oversold)'
        }
    ]
};

/**
 * MACD Card Configuration
 * 
 * Displays DIF, DEA, and MACD histogram values across all 4 timeframes (1m, 1w, 1d, 4h).
 * Includes reference line at zero level.
 * 
 * Requirements: 1.4, 6.1, 6.5, 8.1
 */
const macdCardConfig = {
    containerId: 'macd-card',
    title: 'MACD Indicators',
    indicators: [
        {
            key: 'dif',
            label: 'DIF',
            style: 'solid',
            markerShape: 'circle'
        },
        {
            key: 'dea',
            label: 'DEA',
            style: 'solid',
            markerShape: 'triangle'
        },
        {
            key: 'macd',
            label: 'MACD',
            style: 'solid',
            markerShape: 'square'
        }
    ],
    yAxisConfig: {
        type: 'auto',  // Auto-scale based on MACD value range
        ticks: 6,
        formatter: (value) => value.toFixed(0)
    },
    colorScheme: {
        positive: '#22c55e',  // green (positive values)
        negative: '#ef4444',  // red (negative values)
        neutral: '#8a8fa8'    // gray (zero)
    },
    referenceLines: [
        {
            value: 0,
            label: 'Zero Line'
        }
    ]
};

// ============================================================================
// Dashboard Configuration
// ============================================================================

/**
 * Main dashboard configuration
 * 
 * Requirements: 7.1, 8.1
 */
const dashboardConfig = {
    apiBaseUrl: 'http://127.0.0.1:8000',  // Backend API base URL
    refreshInterval: 30000,  // 30 seconds auto-refresh
    timeframes: ['1m', '1w', '1d', '4h'],  // Timeframes to display
    cards: [
        priceCardConfig,
        rsiCardConfig,
        macdCardConfig
    ]
};

// ============================================================================
// Application Initialization
// ============================================================================

/**
 * Initialize dashboard application
 * 
 * Requirements: 1.1, 7.1, 8.1, 8.5
 */
async function initializeDashboard() {
    console.log('Initializing BTC Multi-Timeframe Dashboard...');
    
    try {
        // Create DashboardController instance
        const controller = new DashboardController(dashboardConfig);
        
        // Initialize dashboard (fetch initial data and render cards)
        await controller.initialize();
        
        // Start auto-refresh timer (30-second interval)
        controller.startAutoRefresh();
        
        // Wire manual refresh button
        const refreshButton = document.getElementById('refreshButton');
        if (refreshButton) {
            refreshButton.addEventListener('click', async () => {
                console.log('Manual refresh triggered');
                try {
                    await controller.refresh();
                } catch (error) {
                    console.error('Manual refresh failed:', error);
                }
            });
        }
        
        // Store controller instance globally for debugging
        window.dashboardController = controller;
        
        console.log('Dashboard initialized successfully');
    } catch (error) {
        console.error('Failed to initialize dashboard:', error);
        
        // Display error message to user
        const errorElement = document.getElementById('errorMessage');
        if (errorElement) {
            errorElement.textContent = `Failed to initialize dashboard: ${error.message}`;
            errorElement.style.display = 'block';
        }
    }
}

/**
 * Cleanup dashboard on page unload
 */
function cleanupDashboard() {
    console.log('Cleaning up dashboard...');
    
    if (window.dashboardController) {
        window.dashboardController.destroy();
        window.dashboardController = null;
    }
}

// ============================================================================
// Event Listeners
// ============================================================================

// Initialize dashboard when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeDashboard);
} else {
    // DOM is already ready
    initializeDashboard();
}

// Cleanup on page unload
window.addEventListener('beforeunload', cleanupDashboard);

// ============================================================================
// Exports (for testing)
// ============================================================================

if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        priceCardConfig,
        rsiCardConfig,
        macdCardConfig,
        dashboardConfig,
        initializeDashboard,
        cleanupDashboard
    };
}
