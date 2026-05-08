/**
 * Unit tests for DataFetcher class
 * Tests network requests, retry logic, timeout handling, and data aggregation
 */

// Mock fetch globally
global.fetch = jest.fn();

// Import DataFetcher
const DataFetcher = require('./DataFetcher.js');

describe('DataFetcher', () => {
  let fetcher;
  const mockApiBaseUrl = 'http://127.0.0.1:8000';

  beforeEach(() => {
    fetcher = new DataFetcher(mockApiBaseUrl);
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  describe('constructor', () => {
    test('initializes with correct configuration', () => {
      expect(fetcher.apiBaseUrl).toBe(mockApiBaseUrl);
      expect(fetcher.binanceApiUrl).toBe('https://api.binance.com');
      expect(fetcher.requestTimeout).toBe(10000);
      expect(fetcher.retryDelay).toBe(1000);
      expect(fetcher.maxRetries).toBe(1);
    });
  });

  describe('fetchLatestValues', () => {
    test('fetches latest values successfully', async () => {
      const mockData = {
        '1m': { close: 65432.10, ema7: 65500.00, rsi14: 65.4 },
        '1w': { close: 64000.00, ema7: 64500.00, rsi14: 55.2 },
        '1d': { close: 65500.00, ema7: 66000.00, rsi14: 70.1 },
        '4h': { close: 65200.00, ema7: 65700.00, rsi14: 62.3 },
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      });

      const result = await fetcher.fetchLatestValues();

      expect(global.fetch).toHaveBeenCalledWith(
        `${mockApiBaseUrl}/api/latest`,
        expect.objectContaining({
          headers: { 'Accept': 'application/json' },
        })
      );
      expect(result).toEqual(mockData);
    });

    test('throws error when API returns non-ok response', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
      });

      // Use real timers for this test
      jest.useRealTimers();
      await expect(fetcher.fetchLatestValues()).rejects.toThrow(
        'Failed to fetch latest values: HTTP 500: Internal Server Error'
      );
      jest.useFakeTimers();
    });

    test('retries once on network failure', async () => {
      const mockData = { '1m': { close: 65432.10 } };

      // First call fails, second succeeds
      global.fetch
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockData,
        });

      const resultPromise = fetcher.fetchLatestValues();

      // Fast-forward through retry delay
      await jest.advanceTimersByTimeAsync(1000);

      const result = await resultPromise;

      expect(global.fetch).toHaveBeenCalledTimes(2);
      expect(result).toEqual(mockData);
    });

    test('throws error after retry exhausted', async () => {
      global.fetch
        .mockRejectedValueOnce(new Error('Network error'))
        .mockRejectedValueOnce(new Error('Network error'));

      // Use real timers for this test
      jest.useRealTimers();
      await expect(fetcher.fetchLatestValues()).rejects.toThrow(
        'Failed to fetch latest values: Network error'
      );
      expect(global.fetch).toHaveBeenCalledTimes(2);
      jest.useFakeTimers();
    });
  });

  describe('fetchRealtimePrice', () => {
    test('fetches realtime price from Binance successfully', async () => {
      const mockBinanceResponse = {
        symbol: 'BTCUSDT',
        price: '65432.10',
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockBinanceResponse,
      });

      const result = await fetcher.fetchRealtimePrice();

      expect(global.fetch).toHaveBeenCalledWith(
        'https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT',
        expect.objectContaining({
          headers: { 'Accept': 'application/json' },
        })
      );
      expect(result.price).toBe(65432.10);
      expect(result.timestamp).toBeGreaterThan(0);
    });

    test('parses price as float', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ symbol: 'BTCUSDT', price: '65432.10' }),
      });

      const result = await fetcher.fetchRealtimePrice();

      expect(typeof result.price).toBe('number');
      expect(result.price).toBe(65432.10);
    });

    test('throws error when Binance API fails', async () => {
      global.fetch
        .mockRejectedValueOnce(new Error('Binance API error'))
        .mockRejectedValueOnce(new Error('Binance API error'));

      // Use real timers for this test
      jest.useRealTimers();
      await expect(fetcher.fetchRealtimePrice()).rejects.toThrow(
        'Failed to fetch realtime price'
      );
      jest.useFakeTimers();
    });
  });

  describe('fetchAll', () => {
    test('fetches all data sources in parallel', async () => {
      const mockLatestData = {
        '1m': { close: 65432.10, ema7: 65500.00 },
        '1w': { close: 64000.00, ema7: 64500.00 },
      };
      const mockBinanceResponse = {
        symbol: 'BTCUSDT',
        price: '65432.10',
      };

      global.fetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockLatestData,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockBinanceResponse,
        });

      const result = await fetcher.fetchAll();

      expect(global.fetch).toHaveBeenCalledTimes(2);
      expect(result.latest).toEqual(mockLatestData);
      expect(result.realtime.price).toBe(65432.10);
      expect(result.timestamp).toBeGreaterThan(0);
    });

    test('throws error if any data source fails', async () => {
      global.fetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ '1m': { close: 65432.10 } }),
        })
        .mockRejectedValueOnce(new Error('Binance API error'))
        .mockRejectedValueOnce(new Error('Binance API error'));

      // Use real timers for this test
      jest.useRealTimers();
      await expect(fetcher.fetchAll()).rejects.toThrow();
      jest.useFakeTimers();
    });
  });

  describe('fetchAllTimeframes', () => {
    test('fetches historical data with default limit', async () => {
      const mockData = {
        '1m': [{ time: '2024-01-20T14:30:00', close: 65432.10 }],
        '1w': [{ time: '2024-01-20T00:00:00', close: 64000.00 }],
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      });

      const result = await fetcher.fetchAllTimeframes();

      expect(global.fetch).toHaveBeenCalledWith(
        `${mockApiBaseUrl}/api/all?limit=60`,
        expect.any(Object)
      );
      expect(result).toEqual(mockData);
    });

    test('fetches historical data with custom limit', async () => {
      const mockData = { '1m': [] };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      });

      await fetcher.fetchAllTimeframes(120);

      expect(global.fetch).toHaveBeenCalledWith(
        `${mockApiBaseUrl}/api/all?limit=120`,
        expect.any(Object)
      );
    });
  });

  describe('timeout handling', () => {
    test('aborts request after 10 seconds', async () => {
      // Use real timers for this test
      jest.useRealTimers();
      
      // Mock a fetch that takes longer than timeout
      global.fetch.mockImplementationOnce(() => 
        new Promise(resolve => setTimeout(resolve, 15000))
      );

      await expect(fetcher.fetchLatestValues()).rejects.toThrow();
      
      jest.useFakeTimers();
    }, 15000); // Increase test timeout
  });

  describe('retry logic', () => {
    test('waits 1 second between retries', async () => {
      global.fetch
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ '1m': { close: 65432.10 } }),
        });

      const resultPromise = fetcher.fetchLatestValues();

      // Should not resolve immediately
      await Promise.resolve();
      expect(global.fetch).toHaveBeenCalledTimes(1);

      // Fast-forward 1 second
      await jest.advanceTimersByTimeAsync(1000);

      await resultPromise;

      expect(global.fetch).toHaveBeenCalledTimes(2);
    });
  });
});
