/**
 * Unit tests for DashboardController class
 * Tests initialization, data fetching, state management, auto-refresh, and error handling
 * 
 * Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 8.1, 8.2, 8.3, 8.4
 */

// Mock fetch globally
global.fetch = jest.fn();

// Import DashboardController
const { DashboardController } = require('./DashboardController.js');

// Mock DataFetcher
jest.mock('./DataFetcher.js', () => {
  return jest.fn().mockImplementation(() => ({
    fetchAll: jest.fn(),
    fetchLatestValues: jest.fn(),
    fetchRealtimePrice: jest.fn()
  }));
});

// Mock CardRenderer
jest.mock('./CardRenderer.js', () => ({
  CardRenderer: jest.fn().mockImplementation(() => ({
    render: jest.fn(),
    update: jest.fn(),
    clear: jest.fn(),
    currentData: null,
    containerId: 'test-card'
  }))
}));

const DataFetcher = require('./DataFetcher.js');
const { CardRenderer } = require('./CardRenderer.js');

describe('DashboardController', () => {
  let controller;
  let mockDataFetcher;
  
  const mockConfig = {
    apiBaseUrl: 'http://127.0.0.1:8000',
    refreshInterval: 30000,
    timeframes: ['1m', '1w', '1d', '4h'],
    cards: [
      {
        containerId: 'price-card',
        title: 'Price & Moving Averages',
        indicators: [
          { key: 'close', label: 'Price', color: '#22c55e' },
          { key: 'ema7', label: 'EMA7', color: '#3b82f6' }
        ],
        yAxisConfig: { type: 'auto' },
        colorScheme: {}
      }
    ]
  };

  const mockLatestData = {
    '1m': { close: 65432.10, ema7: 65500.00, rsi14: 65.4 },
    '1w': { close: 64000.00, ema7: 64500.00, rsi14: 55.2 },
    '1d': { close: 65500.00, ema7: 66000.00, rsi14: 70.1 },
    '4h': { close: 65200.00, ema7: 65700.00, rsi14: 62.3 }
  };

  const mockRealtimePrice = {
    price: 65432.10,
    timestamp: Date.now(),
    direction: 'up'
  };

  beforeEach(() => {
    // Clear all mocks
    jest.clearAllMocks();
    jest.useFakeTimers();
    
    // Setup DOM elements
    document.body.innerHTML = `
      <div id="price-card"></div>
      <div id="realtimePrice"></div>
      <div id="updateTime"></div>
      <div id="autoRefreshIndicator"></div>
      <div id="loadingIndicator"></div>
      <div id="errorMessage"></div>
    `;
    
    // Create controller instance
    controller = new DashboardController(mockConfig);
    
    // Get the mock instance created by the constructor
    mockDataFetcher = controller.dataFetcher;
    mockDataFetcher.fetchAll.mockResolvedValue({
      latest: mockLatestData,
      realtime: mockRealtimePrice,
      timestamp: Date.now()
    });
    mockDataFetcher.fetchLatestValues.mockResolvedValue(mockLatestData);
    mockDataFetcher.fetchRealtimePrice.mockResolvedValue(mockRealtimePrice);
  });

  afterEach(() => {
    jest.useRealTimers();
    if (controller) {
      controller.destroy();
    }
  });

  describe('constructor', () => {
    test('initializes with correct configuration', () => {
      expect(controller.config.apiBaseUrl).toBe('http://127.0.0.1:8000');
      expect(controller.config.refreshInterval).toBe(30000);
      expect(controller.config.timeframes).toEqual(['1m', '1w', '1d', '4h']);
      expect(controller.config.cards).toHaveLength(1);
    });

    test('initializes with default configuration', () => {
      const defaultController = new DashboardController({});
      expect(defaultController.config.apiBaseUrl).toBe('http://127.0.0.1:8000');
      expect(defaultController.config.refreshInterval).toBe(30000);
      expect(defaultController.config.timeframes).toEqual(['1m', '1w', '1d', '4h']);
    });

    test('initializes state with correct defaults', () => {
      expect(controller.state.latestData).toEqual({});
      expect(controller.state.realtimePrice).toBeNull();
      expect(controller.state.lastUpdate).toBeNull();
      expect(controller.state.isLoading).toBe(false);
      expect(controller.state.error).toBeNull();
    });

    test('initializes with null refreshTimer', () => {
      expect(controller.refreshTimer).toBeNull();
    });
  });

  describe('initialize', () => {
    test('fetches initial data and renders cards', async () => {
      await controller.initialize();

      expect(mockDataFetcher.fetchAll).toHaveBeenCalledTimes(1);
      expect(controller.cardRenderers).toHaveLength(1);
    });

    test('updates state with fetched data', async () => {
      await controller.initialize();

      expect(controller.state.latestData).toEqual(mockLatestData);
      expect(controller.state.realtimePrice).toEqual(mockRealtimePrice);
      expect(controller.state.lastUpdate).toBeGreaterThan(0);
    });

    test('sets loading state during initialization', async () => {
      const loadingElement = document.getElementById('loadingIndicator');
      
      const initPromise = controller.initialize();
      
      // Should be loading
      expect(controller.state.isLoading).toBe(true);
      expect(loadingElement.style.display).toBe('block');
      
      await initPromise;
      
      // Should not be loading after completion
      expect(controller.state.isLoading).toBe(false);
      expect(loadingElement.style.display).toBe('none');
    });

    test('handles initialization error', async () => {
      mockDataFetcher.fetchAll.mockRejectedValueOnce(new Error('Network error'));

      await expect(controller.initialize()).rejects.toThrow('Network error');
      expect(controller.state.error).toContain('Network error');
    });

    test('clears loading state on error', async () => {
      mockDataFetcher.fetchAll.mockRejectedValueOnce(new Error('Network error'));

      try {
        await controller.initialize();
      } catch (error) {
        // Expected error
      }

      expect(controller.state.isLoading).toBe(false);
    });
  });

  describe('refresh', () => {
    test('fetches latest data from DataFetcher', async () => {
      await controller.refresh();

      expect(mockDataFetcher.fetchAll).toHaveBeenCalledTimes(1);
    });

    test('updates state with new data', async () => {
      const newData = {
        latest: { '1m': { close: 66000.00 } },
        realtime: { price: 66000.00, timestamp: Date.now() },
        timestamp: Date.now()
      };
      mockDataFetcher.fetchAll.mockResolvedValueOnce(newData);

      await controller.refresh();

      expect(controller.state.latestData).toEqual(newData.latest);
      expect(controller.state.realtimePrice).toEqual(newData.realtime);
      expect(controller.state.lastUpdate).toBe(newData.timestamp);
    });

    test('updates all card renderers', async () => {
      // First initialize to create renderers
      await controller.initialize();
      
      const renderer = controller.cardRenderers[0];
      const renderSpy = jest.spyOn(renderer, 'render');
      const updateSpy = jest.spyOn(renderer, 'update');
      
      // Set currentData to simulate existing render
      renderer.currentData = mockLatestData;

      // Now refresh
      await controller.refresh();

      expect(updateSpy).toHaveBeenCalledWith(mockLatestData);
    });

    test('renders cards on first refresh if not initialized', async () => {
      const renderer = controller.cardRenderers[0] || { render: jest.fn(), update: jest.fn(), currentData: null };
      
      await controller.refresh();

      // Should have created renderers during refresh
      expect(controller.cardRenderers.length).toBeGreaterThan(0);
    });

    test('updates UI elements after refresh', async () => {
      await controller.refresh();

      const priceElement = document.getElementById('realtimePrice');
      const updateTimeElement = document.getElementById('updateTime');

      expect(priceElement.textContent).toContain('$65,432.10');
      expect(updateTimeElement.textContent).toContain('更新于');
    });

    test('handles refresh error', async () => {
      mockDataFetcher.fetchAll.mockRejectedValueOnce(new Error('API error'));

      await expect(controller.refresh()).rejects.toThrow('API error');
      expect(controller.state.error).toContain('API error');
    });

    test('displays error message in UI on refresh failure', async () => {
      mockDataFetcher.fetchAll.mockRejectedValueOnce(new Error('Failed to fetch'));

      try {
        await controller.refresh();
      } catch (error) {
        // Expected error
      }

      const errorElement = document.getElementById('errorMessage');
      expect(errorElement.style.display).toBe('block');
      expect(errorElement.textContent).toContain('Failed to fetch');
    });
  });

  describe('startAutoRefresh', () => {
    test('sets up interval timer with correct interval', () => {
      controller.startAutoRefresh();

      expect(controller.refreshTimer).not.toBeNull();
    });

    test('calls refresh on interval', async () => {
      const refreshSpy = jest.spyOn(controller, 'refresh');
      
      controller.startAutoRefresh();

      // Fast-forward 30 seconds
      await jest.advanceTimersByTimeAsync(30000);

      expect(refreshSpy).toHaveBeenCalledTimes(1);

      // Fast-forward another 30 seconds
      await jest.advanceTimersByTimeAsync(30000);

      expect(refreshSpy).toHaveBeenCalledTimes(2);
    });

    test('updates auto-refresh indicator to active', () => {
      controller.startAutoRefresh();

      const indicator = document.getElementById('autoRefreshIndicator');
      expect(indicator.textContent).toContain('自动刷新已启用');
      expect(indicator.className).toContain('active');
    });

    test('stops existing timer before starting new one', () => {
      controller.startAutoRefresh();
      const firstTimer = controller.refreshTimer;

      controller.startAutoRefresh();
      const secondTimer = controller.refreshTimer;

      expect(firstTimer).not.toBe(secondTimer);
    });

    test('continues auto-refresh even if refresh fails', async () => {
      const refreshSpy = jest.spyOn(controller, 'refresh');
      refreshSpy.mockRejectedValueOnce(new Error('Network error'));

      controller.startAutoRefresh();

      // First refresh fails
      await jest.advanceTimersByTimeAsync(30000);
      expect(refreshSpy).toHaveBeenCalledTimes(1);

      // Should still call refresh again after next interval
      refreshSpy.mockResolvedValueOnce();
      await jest.advanceTimersByTimeAsync(30000);
      expect(refreshSpy).toHaveBeenCalledTimes(2);
    });
  });

  describe('stopAutoRefresh', () => {
    test('clears interval timer', () => {
      controller.startAutoRefresh();
      expect(controller.refreshTimer).not.toBeNull();

      controller.stopAutoRefresh();
      expect(controller.refreshTimer).toBeNull();
    });

    test('updates auto-refresh indicator to inactive', () => {
      controller.startAutoRefresh();
      controller.stopAutoRefresh();

      const indicator = document.getElementById('autoRefreshIndicator');
      expect(indicator.textContent).toContain('自动刷新已暂停');
      expect(indicator.className).toContain('inactive');
    });

    test('does nothing if timer is not running', () => {
      expect(() => controller.stopAutoRefresh()).not.toThrow();
    });

    test('stops calling refresh after stopped', async () => {
      const refreshSpy = jest.spyOn(controller, 'refresh');
      
      controller.startAutoRefresh();
      await jest.advanceTimersByTimeAsync(30000);
      expect(refreshSpy).toHaveBeenCalledTimes(1);

      controller.stopAutoRefresh();
      await jest.advanceTimersByTimeAsync(30000);
      
      // Should not call refresh again
      expect(refreshSpy).toHaveBeenCalledTimes(1);
    });
  });

  describe('error handling', () => {
    test('formats network error with troubleshooting instructions', async () => {
      mockDataFetcher.fetchAll.mockRejectedValueOnce(new Error('Failed to fetch'));

      try {
        await controller.refresh();
      } catch (error) {
        // Expected error
      }

      expect(controller.state.error).toContain('请确保后端服务正在运行');
      expect(controller.state.error).toContain('uvicorn web.api:app --reload');
    });

    test('formats timeout error with troubleshooting instructions', async () => {
      mockDataFetcher.fetchAll.mockRejectedValueOnce(new Error('Request timeout'));

      try {
        await controller.refresh();
      } catch (error) {
        // Expected error
      }

      expect(controller.state.error).toContain('请求超时');
    });

    test('formats HTTP 404 error with troubleshooting instructions', async () => {
      mockDataFetcher.fetchAll.mockRejectedValueOnce(new Error('HTTP 404: Not Found'));

      try {
        await controller.refresh();
      } catch (error) {
        // Expected error
      }

      expect(controller.state.error).toContain('API端点不存在');
    });

    test('formats HTTP 500 error with troubleshooting instructions', async () => {
      mockDataFetcher.fetchAll.mockRejectedValueOnce(new Error('HTTP 500: Internal Server Error'));

      try {
        await controller.refresh();
      } catch (error) {
        // Expected error
      }

      expect(controller.state.error).toContain('后端服务器错误');
    });
  });

  describe('UI updates', () => {
    test('updates realtime price display with up arrow', async () => {
      mockDataFetcher.fetchAll.mockResolvedValueOnce({
        latest: mockLatestData,
        realtime: { price: 65432.10, timestamp: Date.now(), direction: 'up' },
        timestamp: Date.now()
      });

      await controller.refresh();

      const priceElement = document.getElementById('realtimePrice');
      expect(priceElement.textContent).toContain('$65,432.10');
      expect(priceElement.textContent).toContain('↑');
      expect(priceElement.className).toContain('price-up');
    });

    test('updates realtime price display with down arrow', async () => {
      mockDataFetcher.fetchAll.mockResolvedValueOnce({
        latest: mockLatestData,
        realtime: { price: 64000.00, timestamp: Date.now(), direction: 'down' },
        timestamp: Date.now()
      });

      await controller.refresh();

      const priceElement = document.getElementById('realtimePrice');
      expect(priceElement.textContent).toContain('$64,000.00');
      expect(priceElement.textContent).toContain('↓');
      expect(priceElement.className).toContain('price-down');
    });

    test('updates last update timestamp', async () => {
      await controller.refresh();

      const updateTimeElement = document.getElementById('updateTime');
      expect(updateTimeElement.textContent).toMatch(/更新于 \d{4}\/\d{2}\/\d{2}/);
    });

    test('handles missing UI elements gracefully', async () => {
      document.body.innerHTML = ''; // Remove all elements

      expect(() => controller.refresh()).not.toThrow();
    });
  });

  describe('state management', () => {
    test('getState returns copy of current state', () => {
      controller.state.latestData = mockLatestData;
      const state = controller.getState();

      expect(state.latestData).toEqual(mockLatestData);
      
      // Verify it's a copy, not reference
      state.latestData = {};
      expect(controller.state.latestData).toEqual(mockLatestData);
    });

    test('getConfig returns copy of configuration', () => {
      const config = controller.getConfig();

      expect(config.apiBaseUrl).toBe('http://127.0.0.1:8000');
      
      // Verify it's a copy, not reference
      config.apiBaseUrl = 'http://different.url';
      expect(controller.config.apiBaseUrl).toBe('http://127.0.0.1:8000');
    });
  });

  describe('destroy', () => {
    test('stops auto-refresh timer', () => {
      controller.startAutoRefresh();
      controller.destroy();

      expect(controller.refreshTimer).toBeNull();
    });

    test('clears all card renderers', async () => {
      await controller.initialize();
      const renderer = controller.cardRenderers[0];
      const clearSpy = jest.spyOn(renderer, 'clear');
      
      controller.destroy();

      expect(clearSpy).toHaveBeenCalled();
      expect(controller.cardRenderers).toHaveLength(0);
    });

    test('can be called multiple times safely', () => {
      controller.destroy();
      expect(() => controller.destroy()).not.toThrow();
    });
  });

  describe('card renderer integration', () => {
    test('initializes card renderers from config', async () => {
      await controller.initialize();

      expect(controller.cardRenderers).toHaveLength(1);
    });

    test('handles multiple cards', async () => {
      const multiCardConfig = {
        ...mockConfig,
        cards: [
          { containerId: 'card1', title: 'Card 1', indicators: [], yAxisConfig: {}, colorScheme: {} },
          { containerId: 'card2', title: 'Card 2', indicators: [], yAxisConfig: {}, colorScheme: {} }
        ]
      };

      const multiController = new DashboardController(multiCardConfig);
      
      // Mock the data fetcher for this controller too
      multiController.dataFetcher.fetchAll = jest.fn().mockResolvedValue({
        latest: mockLatestData,
        realtime: mockRealtimePrice,
        timestamp: Date.now()
      });
      
      await multiController.initialize();

      expect(multiController.cardRenderers).toHaveLength(2);
      multiController.destroy();
    });
  });
});
