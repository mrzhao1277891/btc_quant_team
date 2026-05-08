/**
 * ValueFormatter Unit Tests
 * Run with: node ValueFormatter.test.js
 */

// Simple test framework
class TestRunner {
    constructor() {
        this.tests = [];
        this.passCount = 0;
        this.failCount = 0;
    }

    assertEquals(actual, expected, testName) {
        const passed = actual === expected;
        if (passed) {
            this.passCount++;
            console.log(`✓ ${testName}`);
        } else {
            this.failCount++;
            console.log(`✗ ${testName}`);
            console.log(`  Expected: ${expected}`);
            console.log(`  Got: ${actual}`);
        }
        this.tests.push({ name: testName, passed, expected, actual });
    }

    summary() {
        console.log('\n' + '='.repeat(60));
        console.log('Test Summary');
        console.log('='.repeat(60));
        console.log(`Total: ${this.tests.length} tests`);
        console.log(`Passed: ${this.passCount}`);
        console.log(`Failed: ${this.failCount}`);
        console.log(this.failCount === 0 ? '\n✓ All tests passed!' : '\n✗ Some tests failed');
        return this.failCount === 0;
    }
}

// Mock ValueFormatter for Node.js environment
class ValueFormatter {
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

    static formatPercentage(value, decimals = 1) {
        if (value == null || isNaN(value) || !isFinite(value)) {
            return '—';
        }
        
        return Number(value).toFixed(decimals);
    }

    static formatInteger(value) {
        if (value == null || isNaN(value) || !isFinite(value)) {
            return '—';
        }
        
        return Number(value).toLocaleString('en-US', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        });
    }

    static formatMACD(value) {
        if (value == null || isNaN(value) || !isFinite(value)) {
            return '—';
        }
        
        return Number(value).toFixed(0);
    }

    static formatRSI(value) {
        if (value == null || isNaN(value) || !isFinite(value)) {
            return '—';
        }
        
        return Number(value).toFixed(1);
    }

    static formatEMA(value) {
        return this.formatPrice(value, 2);
    }

    static formatVolume(value) {
        return this.formatInteger(value);
    }

    static formatATR(value) {
        if (value == null || isNaN(value) || !isFinite(value)) {
            return '—';
        }
        
        return Number(value).toFixed(0);
    }

    static getColorClass(value, type, referenceValue = null) {
        if (value == null || isNaN(value) || !isFinite(value)) {
            return 'text-neutral';
        }
        
        switch (type.toLowerCase()) {
            case 'ema':
            case 'ema7':
            case 'ema25':
            case 'ema50':
                if (referenceValue != null) {
                    return referenceValue > value ? 'text-green' : 'text-red';
                }
                return 'text-neutral';
            
            case 'macd':
            case 'dif':
            case 'dea':
                return value > 0 ? 'text-green' : value < 0 ? 'text-red' : 'text-neutral';
            
            case 'rsi':
            case 'rsi14':
            case 'rsi6':
                return value > 70 ? 'text-red' : value < 30 ? 'text-green' : 'text-neutral';
            
            default:
                return 'text-neutral';
        }
    }

    static isValidNumber(value) {
        return value != null && !isNaN(value) && isFinite(value);
    }
}

// Run tests
const runner = new TestRunner();

console.log('Running ValueFormatter Unit Tests...\n');

// Test Suite: formatPrice
console.log('Testing formatPrice...');
runner.assertEquals(ValueFormatter.formatPrice(65432.10), '$65,432.10', 'formatPrice with standard value');
runner.assertEquals(ValueFormatter.formatPrice(1234567.89), '$1,234,567.89', 'formatPrice with large value');
runner.assertEquals(ValueFormatter.formatPrice(0), '$0.00', 'formatPrice with zero');
runner.assertEquals(ValueFormatter.formatPrice(null), '—', 'formatPrice with null');
runner.assertEquals(ValueFormatter.formatPrice(undefined), '—', 'formatPrice with undefined');
runner.assertEquals(ValueFormatter.formatPrice(NaN), '—', 'formatPrice with NaN');
runner.assertEquals(ValueFormatter.formatPrice(Infinity), '—', 'formatPrice with Infinity');

// Test Suite: formatPercentage
console.log('\nTesting formatPercentage...');
runner.assertEquals(ValueFormatter.formatPercentage(65.432), '65.4', 'formatPercentage with standard value');
runner.assertEquals(ValueFormatter.formatPercentage(70.0), '70.0', 'formatPercentage with whole number');
runner.assertEquals(ValueFormatter.formatPercentage(null), '—', 'formatPercentage with null');
runner.assertEquals(ValueFormatter.formatPercentage(undefined), '—', 'formatPercentage with undefined');

// Test Suite: formatInteger
console.log('\nTesting formatInteger...');
runner.assertEquals(ValueFormatter.formatInteger(1234567), '1,234,567', 'formatInteger with large value');
runner.assertEquals(ValueFormatter.formatInteger(0), '0', 'formatInteger with zero');
runner.assertEquals(ValueFormatter.formatInteger(null), '—', 'formatInteger with null');

// Test Suite: formatMACD
console.log('\nTesting formatMACD...');
runner.assertEquals(ValueFormatter.formatMACD(123.45), '123', 'formatMACD with positive value');
runner.assertEquals(ValueFormatter.formatMACD(-50.67), '-51', 'formatMACD with negative value');
runner.assertEquals(ValueFormatter.formatMACD(0), '0', 'formatMACD with zero');
runner.assertEquals(ValueFormatter.formatMACD(null), '—', 'formatMACD with null');

// Test Suite: formatRSI
console.log('\nTesting formatRSI...');
runner.assertEquals(ValueFormatter.formatRSI(65.432), '65.4', 'formatRSI with standard value');
runner.assertEquals(ValueFormatter.formatRSI(70.0), '70.0', 'formatRSI with whole number');
runner.assertEquals(ValueFormatter.formatRSI(null), '—', 'formatRSI with null');

// Test Suite: formatEMA
console.log('\nTesting formatEMA...');
runner.assertEquals(ValueFormatter.formatEMA(65432.10), '$65,432.10', 'formatEMA with standard value');
runner.assertEquals(ValueFormatter.formatEMA(null), '—', 'formatEMA with null');

// Test Suite: formatVolume
console.log('\nTesting formatVolume...');
runner.assertEquals(ValueFormatter.formatVolume(1234567), '1,234,567', 'formatVolume with large value');
runner.assertEquals(ValueFormatter.formatVolume(null), '—', 'formatVolume with null');

// Test Suite: formatATR
console.log('\nTesting formatATR...');
runner.assertEquals(ValueFormatter.formatATR(456.78), '457', 'formatATR with decimal value');
runner.assertEquals(ValueFormatter.formatATR(null), '—', 'formatATR with null');

// Test Suite: getColorClass
console.log('\nTesting getColorClass...');
runner.assertEquals(ValueFormatter.getColorClass(65000, 'ema', 66000), 'text-green', 'getColorClass EMA - price above');
runner.assertEquals(ValueFormatter.getColorClass(67000, 'ema', 66000), 'text-red', 'getColorClass EMA - price below');
runner.assertEquals(ValueFormatter.getColorClass(123.45, 'macd'), 'text-green', 'getColorClass MACD - positive');
runner.assertEquals(ValueFormatter.getColorClass(-50.00, 'macd'), 'text-red', 'getColorClass MACD - negative');
runner.assertEquals(ValueFormatter.getColorClass(75, 'rsi'), 'text-red', 'getColorClass RSI - overbought');
runner.assertEquals(ValueFormatter.getColorClass(25, 'rsi'), 'text-green', 'getColorClass RSI - oversold');
runner.assertEquals(ValueFormatter.getColorClass(50, 'rsi'), 'text-neutral', 'getColorClass RSI - neutral');

// Test Suite: isValidNumber
console.log('\nTesting isValidNumber...');
runner.assertEquals(ValueFormatter.isValidNumber(123), true, 'isValidNumber with valid number');
runner.assertEquals(ValueFormatter.isValidNumber(0), true, 'isValidNumber with zero');
runner.assertEquals(ValueFormatter.isValidNumber(null), false, 'isValidNumber with null');
runner.assertEquals(ValueFormatter.isValidNumber(undefined), false, 'isValidNumber with undefined');
runner.assertEquals(ValueFormatter.isValidNumber(NaN), false, 'isValidNumber with NaN');
runner.assertEquals(ValueFormatter.isValidNumber(Infinity), false, 'isValidNumber with Infinity');

// Print summary
const allPassed = runner.summary();
process.exit(allPassed ? 0 : 1);
