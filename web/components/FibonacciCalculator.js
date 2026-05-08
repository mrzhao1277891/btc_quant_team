/**
 * FibonacciCalculator.js
 * 
 * Calculates Fibonacci retracement and extension levels
 */

export class FibonacciCalculator {
    /**
     * Fibonacci retracement levels (回调位)
     */
    static RETRACEMENT_LEVELS = [
        { ratio: 0, label: '0%' },
        { ratio: 0.236, label: '23.6%' },
        { ratio: 0.382, label: '38.2%' },
        { ratio: 0.5, label: '50%' },
        { ratio: 0.618, label: '61.8%' },
        { ratio: 0.786, label: '78.6%' },
        { ratio: 1, label: '100%' }
    ];

    /**
     * Fibonacci extension levels (扩展位)
     */
    static EXTENSION_LEVELS = [
        { ratio: 0, label: '0%' },
        { ratio: 0.618, label: '61.8%' },
        { ratio: 1, label: '100%' },
        { ratio: 1.272, label: '127.2%' },
        { ratio: 1.618, label: '161.8%' },
        { ratio: 2.618, label: '261.8%' }
    ];

    /**
     * Calculate Fibonacci levels
     * 
     * @param {number} high - High price
     * @param {number} low - Low price
     * @param {string} direction - 'up' (上涨回调) or 'down' (下跌回调)
     * @returns {Array} Array of Fibonacci levels with prices
     */
    static calculate(high, low, direction = 'up') {
        if (!high || !low || high <= low) {
            return [];
        }

        const range = high - low;
        const levels = [];

        if (direction === 'up') {
            // 上涨回调：从高点向下计算
            for (const level of this.RETRACEMENT_LEVELS) {
                const price = high - (range * level.ratio);
                levels.push({
                    ratio: level.ratio,
                    label: level.label,
                    price: price,
                    key: `fib_${level.ratio}`
                });
            }
        } else {
            // 下跌反弹：从低点向上计算
            for (const level of this.RETRACEMENT_LEVELS) {
                const price = low + (range * level.ratio);
                levels.push({
                    ratio: level.ratio,
                    label: level.label,
                    price: price,
                    key: `fib_${level.ratio}`
                });
            }
        }

        return levels;
    }

    /**
     * Get key Fibonacci levels (23.6%, 38.2%, 50%, 61.8%)
     * 
     * @param {number} high - High price
     * @param {number} low - Low price
     * @param {string} direction - 'up' or 'down'
     * @returns {Array} Array of key Fibonacci levels
     */
    static getKeyLevels(high, low, direction = 'up') {
        const allLevels = this.calculate(high, low, direction);
        // Return key levels: 23.6%, 38.2%, 50%, 61.8%
        return allLevels.filter(level => 
            level.ratio === 0.236 || 
            level.ratio === 0.382 || 
            level.ratio === 0.5 || 
            level.ratio === 0.618
        );
    }
}

export default FibonacciCalculator;
