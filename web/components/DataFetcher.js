/**
 * DataFetcher - Handles all HTTP requests and data aggregation for the dashboard
 * 
 * Responsibilities:
 * - Fetch data from backend API endpoints (/api/latest, /api/all)
 * - Fetch real-time price from Binance API
 * - Implement retry logic for network failures
 * - Implement timeout for all requests
 * - Aggregate data from multiple sources
 */

export class DataFetcher {
  /**
   * @param {string} apiBaseUrl - Base URL for the backend API (e.g., 'http://127.0.0.1:8000')
   */
  constructor(apiBaseUrl) {
    this.apiBaseUrl = apiBaseUrl;
    this.binanceApiUrl = 'https://api.binance.com';
    this.requestTimeout = 10000; // 10 seconds
    this.retryDelay = 1000; // 1 second
    this.maxRetries = 1; // 1 retry
  }

  /**
   * Fetch with timeout support
   * @private
   * @param {string} url - URL to fetch
   * @param {number} timeout - Timeout in milliseconds
   * @returns {Promise<Response>}
   */
  async _fetchWithTimeout(url, timeout) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const response = await fetch(url, {
        signal: controller.signal,
        headers: {
          'Accept': 'application/json',
        },
      });
      clearTimeout(timeoutId);
      return response;
    } catch (error) {
      clearTimeout(timeoutId);
      if (error.name === 'AbortError') {
        throw new Error(`Request timeout after ${timeout}ms`);
      }
      throw error;
    }
  }

  /**
   * Fetch with retry logic
   * @private
   * @param {string} url - URL to fetch
   * @param {number} retries - Number of retries remaining
   * @returns {Promise<any>} - Parsed JSON response
   */
  async _fetchWithRetry(url, retries = this.maxRetries) {
    try {
      const response = await this._fetchWithTimeout(url, this.requestTimeout);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      if (retries > 0) {
        console.warn(`Fetch failed for ${url}, retrying... (${retries} attempts left)`, error.message);
        await this._sleep(this.retryDelay);
        return this._fetchWithRetry(url, retries - 1);
      }
      throw error;
    }
  }

  /**
   * Sleep utility for retry delay
   * @private
   * @param {number} ms - Milliseconds to sleep
   * @returns {Promise<void>}
   */
  _sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Fetch latest indicator values for all timeframes from backend
   * GET /api/latest
   * 
   * @returns {Promise<Object>} - Latest values for all timeframes
   * @example
   * {
   *   '1m': { close: 65432.10, ema7: 65500.00, rsi14: 65.4, ... },
   *   '1w': { ... },
   *   '1d': { ... },
   *   '4h': { ... }
   * }
   */
  async fetchLatestValues() {
    const url = `${this.apiBaseUrl}/api/latest`;
    try {
      const data = await this._fetchWithRetry(url);
      return data;
    } catch (error) {
      console.error('Failed to fetch latest values:', error);
      throw new Error(`Failed to fetch latest values: ${error.message}`);
    }
  }

  /**
   * Fetch real-time BTC price from Binance API
   * GET /api/v3/ticker/price?symbol=BTCUSDT
   * 
   * @returns {Promise<Object>} - Real-time price data
   * @example
   * {
   *   price: 65432.10,
   *   timestamp: 1705756800000
   * }
   */
  async fetchRealtimePrice() {
    const url = `${this.binanceApiUrl}/api/v3/ticker/price?symbol=BTCUSDT`;
    try {
      const data = await this._fetchWithRetry(url);
      return {
        price: parseFloat(data.price),
        timestamp: Date.now(),
      };
    } catch (error) {
      console.error('Failed to fetch realtime price from Binance:', error);
      throw new Error(`Failed to fetch realtime price: ${error.message}`);
    }
  }

  /**
   * Fetch all data sources in parallel using Promise.all()
   * Combines latest values from backend and real-time price from Binance
   * 
   * @returns {Promise<Object>} - Aggregated data from all sources
   * @example
   * {
   *   latest: { '1m': {...}, '1w': {...}, '1d': {...}, '4h': {...} },
   *   realtime: { price: 65432.10, timestamp: 1705756800000 },
   *   timestamp: 1705756800000
   * }
   */
  async fetchAll() {
    try {
      const [latest, realtime] = await Promise.all([
        this.fetchLatestValues(),
        this.fetchRealtimePrice(),
      ]);

      return {
        latest,
        realtime,
        timestamp: Date.now(),
      };
    } catch (error) {
      console.error('Failed to fetch all data:', error);
      throw error;
    }
  }

  /**
   * Fetch historical data for all timeframes from backend
   * GET /api/all?limit={limit}
   * 
   * @param {number} limit - Number of historical records to fetch (default: 60)
   * @returns {Promise<Object>} - Historical data for all timeframes
   * @example
   * {
   *   '1m': [{ time: '2024-01-20T14:30:00', close: 65432.10, ... }, ...],
   *   '1w': [...],
   *   '1d': [...],
   *   '4h': [...]
   * }
   */
  async fetchAllTimeframes(limit = 60) {
    const url = `${this.apiBaseUrl}/api/all?limit=${limit}`;
    try {
      const data = await this._fetchWithRetry(url);
      return data;
    } catch (error) {
      console.error('Failed to fetch all timeframes:', error);
      throw new Error(`Failed to fetch all timeframes: ${error.message}`);
    }
  }
}
