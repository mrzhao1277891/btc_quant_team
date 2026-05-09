/**
 * DashboardController.js
 * 
 * Main orchestrator for the dashboard application.
 * Manages data fetching, state management, and card rendering.
 * 
 * Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 8.1, 8.2, 8.3, 8.4
 */

import { DataFetcher } from './DataFetcher.js';
import { CardRenderer } from './CardRenderer.js';

export class DashboardController {
    /**
     * Create a new DashboardController instance
     * 
     * @param {Object} config - Configuration object
     * @param {string} config.apiBaseUrl - Base URL for backend API
     * @param {number} config.refreshInterval - Auto-refresh interval in milliseconds (default: 30000)
     * @param {Array<string>} config.timeframes - Timeframes to display (default: ['1m', '1w', '1d', '4h'])
     * @param {Array<Object>} config.cards - Card configurations
     */
    constructor(config) {
        this.config = {
            apiBaseUrl: config.apiBaseUrl || 'http://127.0.0.1:8000',
            refreshInterval: config.refreshInterval || 30000, // 30 seconds
            timeframes: config.timeframes || ['1m', '1w', '1d', '4h'],
            cards: config.cards || []
        };
        
        // Initialize state
        this.state = {
            latestData: {},
            realtimePrice: null,
            lastUpdate: null,
            isLoading: false,
            error: null
        };
        
        // Initialize DataFetcher
        this.dataFetcher = new DataFetcher(this.config.apiBaseUrl);
        
        // Initialize CardRenderer instances
        this.cardRenderers = [];
        
        // Auto-refresh timer
        this.refreshTimer = null;
    }

    /**
     * Initialize dashboard: fetch initial data and render all cards
     * 
     * Requirements: 7.1, 7.2, 7.3, 7.4
     */
    async initialize() {
        console.log('Initializing DashboardController...');
        
        try {
            // Show loading state
            this._setLoadingState(true);
            this._clearError();
            
            // Initialize card renderers
            this._initializeCardRenderers();
            
            // Fetch initial data
            await this.refresh();
            
            console.log('DashboardController initialized successfully');
        } catch (error) {
            console.error('Failed to initialize dashboard:', error);
            this._setError(`Failed to initialize dashboard: ${error.message}`);
            throw error;
        } finally {
            this._setLoadingState(false);
        }
    }

    /**
     * Fetch latest data and update all cards
     * 
     * Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 8.2
     */
    async refresh() {
        try {
            // Show loading state
            this._setLoadingState(true);
            this._clearError();
            
            // Fetch all data in parallel
            const data = await this.dataFetcher.fetchAll();
            
            // Update state
            this.state.latestData = data.latest;
            this.state.realtimePrice = data.realtime;
            this.state.lastUpdate = data.timestamp;
            
            // Update all cards
            this._updateAllCards();
            
            // Update UI elements (realtime price, last update time)
            this._updateUIElements();
            
            console.log('Dashboard refreshed successfully at', new Date(data.timestamp).toLocaleString());
        } catch (error) {
            console.error('Failed to refresh dashboard:', error);
            this._setError(this._formatErrorMessage(error));
            throw error;
        } finally {
            this._setLoadingState(false);
        }
    }

    /**
     * Start auto-refresh with 30-second interval
     * 
     * Requirements: 8.1, 8.3
     */
    startAutoRefresh() {
        // Stop existing timer if any
        this.stopAutoRefresh();
        
        console.log(`Starting auto-refresh with ${this.config.refreshInterval}ms interval`);
        
        // Set up interval timer
        this.refreshTimer = setInterval(async () => {
            try {
                await this.refresh();
            } catch (error) {
                console.error('Auto-refresh failed:', error);
                // Don't stop auto-refresh on error, will retry on next interval
            }
        }, this.config.refreshInterval);
        
        // Update UI to show auto-refresh is active
        this._updateAutoRefreshIndicator(true);
    }

    /**
     * Stop auto-refresh timer
     * 
     * Requirements: 8.1
     */
    stopAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
            console.log('Auto-refresh stopped');
            
            // Update UI to show auto-refresh is inactive
            this._updateAutoRefreshIndicator(false);
        }
    }

    /**
     * Initialize card renderer instances from configuration
     * 
     * @private
     */
    _initializeCardRenderers() {
        this.cardRenderers = [];
        
        for (const cardConfig of this.config.cards) {
            const renderer = new CardRenderer(cardConfig.containerId, cardConfig);
            this.cardRenderers.push(renderer);
        }
        
        console.log(`Initialized ${this.cardRenderers.length} card renderers`);
    }

    /**
     * Update all card renderers with latest data
     * 
     * @private
     */
    _updateAllCards() {
        for (const renderer of this.cardRenderers) {
            try {
                if (renderer.currentData === null) {
                    // First render
                    renderer.render(this.state.latestData, this.state.realtimePrice);
                } else {
                    // Update existing render
                    renderer.update(this.state.latestData, this.state.realtimePrice);
                }
            } catch (error) {
                console.error(`Failed to update card ${renderer.containerId}:`, error);
                // Continue updating other cards
            }
        }
    }

    /**
     * Update UI elements (realtime price, last update time, etc.)
     * 
     * @private
     * Requirements: 8.4
     */
    _updateUIElements() {
        // Update realtime price display
        this._updateRealtimePriceDisplay();
        
        // Update last update timestamp
        this._updateLastUpdateDisplay();
    }

    /**
     * Update realtime price display in header
     * 
     * @private
     * Requirements: 9.2, 9.3, 9.4
     */
    _updateRealtimePriceDisplay() {
        const priceElement = document.getElementById('realtimePrice');
        if (!priceElement || !this.state.realtimePrice) {
            return;
        }
        
        const { price, direction } = this.state.realtimePrice;
        
        // Format price
        const formattedPrice = `$${price.toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        })}`;
        
        // Determine arrow and color based on direction
        let arrow = '';
        let colorClass = '';
        
        if (direction === 'up') {
            arrow = ' ↑';
            colorClass = 'up';
        } else if (direction === 'down') {
            arrow = ' ↓';
            colorClass = 'down';
        } else {
            arrow = '';
            colorClass = 'neutral';
        }
        
        // Update element
        priceElement.textContent = `${formattedPrice}${arrow}`;
        priceElement.className = `realtime-price ${colorClass}`;
    }

    /**
     * Update last update timestamp display
     * 
     * @private
     * Requirements: 8.4
     */
    _updateLastUpdateDisplay() {
        const updateTimeElement = document.getElementById('updateTime');
        if (!updateTimeElement || !this.state.lastUpdate) {
            return;
        }
        
        const timestamp = new Date(this.state.lastUpdate);
        const formattedTime = timestamp.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        });
        
        updateTimeElement.textContent = `更新于 ${formattedTime}`;
    }

    /**
     * Update auto-refresh indicator in UI
     * 
     * @private
     * @param {boolean} isActive - Whether auto-refresh is active
     * Requirements: 8.3
     */
    _updateAutoRefreshIndicator(isActive) {
        const indicatorElement = document.getElementById('autoRefreshIndicator');
        if (!indicatorElement) {
            return;
        }
        
        if (isActive) {
            indicatorElement.textContent = '🔄 自动刷新已启用';
            indicatorElement.className = 'auto-refresh-indicator active';
        } else {
            indicatorElement.textContent = '⏸️ 自动刷新已暂停';
            indicatorElement.className = 'auto-refresh-indicator inactive';
        }
    }

    /**
     * Set loading state
     * 
     * @private
     * @param {boolean} isLoading - Whether dashboard is loading
     */
    _setLoadingState(isLoading) {
        this.state.isLoading = isLoading;
        
        const loadingElement = document.getElementById('loadingIndicator');
        if (loadingElement) {
            loadingElement.style.display = isLoading ? 'block' : 'none';
        }
    }

    /**
     * Set error state and display error message
     * 
     * @private
     * @param {string} errorMessage - Error message to display
     * Requirements: 7.5, 7.6
     */
    _setError(errorMessage) {
        this.state.error = errorMessage;
        
        const errorElement = document.getElementById('errorMessage');
        if (errorElement) {
            errorElement.textContent = errorMessage;
            errorElement.style.display = 'block';
        }
    }

    /**
     * Clear error state
     * 
     * @private
     */
    _clearError() {
        this.state.error = null;
        
        const errorElement = document.getElementById('errorMessage');
        if (errorElement) {
            errorElement.style.display = 'none';
        }
    }

    /**
     * Format error message with troubleshooting instructions
     * 
     * @private
     * @param {Error} error - Error object
     * @returns {string} Formatted error message
     * Requirements: 7.5, 7.6
     */
    _formatErrorMessage(error) {
        let message = error.message;
        
        // Add troubleshooting instructions for common errors
        if (message.includes('Failed to fetch') || message.includes('NetworkError')) {
            message += '\n\n请确保后端服务正在运行：\nuvicorn web.api:app --reload';
        } else if (message.includes('timeout')) {
            message += '\n\n请求超时，请检查网络连接或后端服务状态。';
        } else if (message.includes('HTTP 404')) {
            message += '\n\nAPI端点不存在，请检查后端API配置。';
        } else if (message.includes('HTTP 500')) {
            message += '\n\n后端服务器错误，请查看后端日志。';
        }
        
        return message;
    }

    /**
     * Get current dashboard state
     * 
     * @returns {Object} Current state object
     */
    getState() {
        return { ...this.state };
    }

    /**
     * Get dashboard configuration
     * 
     * @returns {Object} Configuration object
     */
    getConfig() {
        return { ...this.config };
    }

    /**
     * Cleanup resources (stop timers, clear renderers)
     */
    destroy() {
        console.log('Destroying DashboardController...');
        
        // Stop auto-refresh
        this.stopAutoRefresh();
        
        // Clear all card renderers
        for (const renderer of this.cardRenderers) {
            renderer.clear();
        }
        
        this.cardRenderers = [];
        
        console.log('DashboardController destroyed');
    }
}
