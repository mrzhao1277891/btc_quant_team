/**
 * ValueFormatter.js
 * 
 * Utility module for formatting numeric values for display.
 * Handles prices, percentages, integers, and various indicator types.
 * 
 * Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7
 */

export class ValueFormatter {
    /**
     * Format a value as a price with dollar sign, thousand separators, and 2 decimal places.
     * 
     * @param {number|null|undefined} value - The price value to format
     * @param {number} decimals - Number of decimal places (default: 2)
     * @returns {string} Formatted price string (e.g., "$65,432.10") or "—" for null/undefined
     * 
     * Requirements: 10.1, 10.2
     */
    static formatPrice(value, decimals = 2) {
        if (value == null || isNaN(value) || !isFinite(value)) {
            return '—';
        }
        
        const formatted = Number(value).toLocaleString('en-US', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        });
        
        return `$${formatted}`;
    }

    /**
     * Format a value as a percentage with specified decimal places.
     * 
     * @param {number|null|undefined} value - The percentage value to format
     * @param {number} decimals - Number of decimal places (default: 1)
     * @returns {string} Formatted percentage string (e.g., "65.4") or "—" for null/undefined
     * 
     * Requirements: 10.4
     */
    static formatPercentage(value, decimals = 1) {
        if (value == null || isNaN(value) || !isFinite(value)) {
            return '—';
        }
        
        return Number(value).toFixed(decimals);
    }

    /**
     * Format a value as an integer with thousand separators and no decimal places.
     * 
     * @param {number|null|undefined} value - The integer value to format
     * @returns {string} Formatted integer string (e.g., "1,234,567") or "—" for null/undefined
     * 
     * Requirements: 10.6
     */
    static formatInteger(value) {
        if (value == null || isNaN(value) || !isFinite(value)) {
            return '—';
        }
        
        return Number(value).toLocaleString('en-US', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        });
    }

    /**
     * Format a MACD value (DIF, DEA, or MACD histogram) with 0 decimal places.
     * 
     * @param {number|null|undefined} value - The MACD value to format
     * @returns {string} Formatted MACD string (e.g., "123") or "—" for null/undefined
     * 
     * Requirements: 10.3
     */
    static formatMACD(value) {
        if (value == null || isNaN(value) || !isFinite(value)) {
            return '—';
        }
        
        return Number(value).toFixed(0);
    }

    /**
     * Format an RSI value with 1 decimal place.
     * 
     * @param {number|null|undefined} value - The RSI value to format
     * @returns {string} Formatted RSI string (e.g., "65.4") or "—" for null/undefined
     * 
     * Requirements: 10.4
     */
    static formatRSI(value) {
        if (value == null || isNaN(value) || !isFinite(value)) {
            return '—';
        }
        
        return Number(value).toFixed(1);
    }

    /**
     * Format an EMA or Bollinger Band value as a price with 2 decimal places.
     * 
     * @param {number|null|undefined} value - The EMA/Bollinger value to format
     * @returns {string} Formatted price string (e.g., "$65,432.10") or "—" for null/undefined
     * 
     * Requirements: 10.5
     */
    static formatEMA(value) {
        return this.formatPrice(value, 2);
    }

    /**
     * Format a volume value with thousand separators and 0 decimal places.
     * 
     * @param {number|null|undefined} value - The volume value to format
     * @returns {string} Formatted volume string (e.g., "1,234,567") or "—" for null/undefined
     * 
     * Requirements: 10.6
     */
    static formatVolume(value) {
        return this.formatInteger(value);
    }

    /**
     * Format an ATR value with 0 decimal places.
     * 
     * @param {number|null|undefined} value - The ATR value to format
     * @returns {string} Formatted ATR string (e.g., "456") or "—" for null/undefined
     * 
     * Requirements: 10.7
     */
    static formatATR(value) {
        if (value == null || isNaN(value) || !isFinite(value)) {
            return '—';
        }
        
        return Number(value).toFixed(0);
    }

    /**
     * Format a value based on indicator type.
     * 
     * @param {number|null|undefined} value - The value to format
     * @param {string} type - The indicator type ('price', 'rsi', 'macd', 'ema', 'volume', 'atr', 'percentage')
     * @returns {string} Formatted string based on type
     */
    static formatIndicator(value, type) {
        switch (type.toLowerCase()) {
            case 'price':
            case 'close':
                return this.formatPrice(value);
            
            case 'rsi':
            case 'rsi14':
            case 'rsi6':
                return this.formatRSI(value);
            
            case 'macd':
            case 'dif':
            case 'dea':
                return this.formatMACD(value);
            
            case 'ema':
            case 'ema7':
            case 'ema25':
            case 'ema50':
            case 'bollinger':
            case 'boll_up':
            case 'boll_md':
            case 'boll_dn':
                return this.formatEMA(value);
            
            case 'volume':
                return this.formatVolume(value);
            
            case 'atr':
                return this.formatATR(value);
            
            case 'percentage':
                return this.formatPercentage(value);
            
            default:
                // Default to 2 decimal places
                return value != null && !isNaN(value) && isFinite(value) 
                    ? Number(value).toFixed(2) 
                    : '—';
        }
    }

    /**
     * Format a timestamp as a readable date/time string.
     * 
     * @param {number|string|Date} timestamp - The timestamp to format
     * @returns {string} Formatted timestamp string (e.g., "2024-01-20 14:30:00")
     */
    static formatTimestamp(timestamp) {
        if (!timestamp) {
            return '—';
        }
        
        try {
            const date = new Date(timestamp);
            if (isNaN(date.getTime())) {
                return '—';
            }
            
            return date.toLocaleString('zh-CN', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: false
            });
        } catch (error) {
            console.error('Error formatting timestamp:', error);
            return '—';
        }
    }

    /**
     * Get color class based on indicator value and type.
     * 
     * @param {number|null|undefined} value - The indicator value
     * @param {string} type - The indicator type
     * @param {number|null} referenceValue - Optional reference value for comparison (e.g., close price for EMA)
     * @returns {string} CSS class name ('text-green', 'text-red', 'text-neutral')
     */
    static getColorClass(value, type, referenceValue = null) {
        if (value == null || isNaN(value) || !isFinite(value)) {
            return 'text-neutral';
        }
        
        switch (type.toLowerCase()) {
            case 'ema':
            case 'ema7':
            case 'ema25':
            case 'ema50':
                // Green if price is above EMA, red if below
                if (referenceValue != null) {
                    return referenceValue > value ? 'text-green' : 'text-red';
                }
                return 'text-neutral';
            
            case 'macd':
            case 'dif':
            case 'dea':
                // Green if positive, red if negative
                return value > 0 ? 'text-green' : value < 0 ? 'text-red' : 'text-neutral';
            
            case 'rsi':
            case 'rsi14':
            case 'rsi6':
                // Red if overbought (>70), green if oversold (<30), neutral otherwise
                return value > 70 ? 'text-red' : value < 30 ? 'text-green' : 'text-neutral';
            
            case 'boll_up':
                // Red if price is above upper band (overbought)
                if (referenceValue != null) {
                    return referenceValue > value ? 'text-red' : 'text-neutral';
                }
                return 'text-neutral';
            
            case 'boll_dn':
                // Green if price is below lower band (oversold)
                if (referenceValue != null) {
                    return referenceValue < value ? 'text-green' : 'text-neutral';
                }
                return 'text-neutral';
            
            default:
                return 'text-neutral';
        }
    }

    /**
     * Validate if a value is a valid number.
     * 
     * @param {any} value - The value to validate
     * @returns {boolean} True if value is a valid finite number
     */
    static isValidNumber(value) {
        return value != null && !isNaN(value) && isFinite(value);
    }
}

// Export as default for convenience
export default ValueFormatter;
