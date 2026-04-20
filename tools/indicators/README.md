# 📊 技术指标工具库

## 📋 概述
专业的加密货币技术指标计算库，包含趋势、动量、波动率、成交量四大类指标。

## 🏗️ 架构设计
```
indicators/
├── trend.py          # 趋势指标
├── momentum.py       # 动量指标
├── volatility.py     # 波动率指标
├── volume.py         # 成交量指标
└── __init__.py       # 统一导出
```

## 🚀 快速使用

### 导入指标
```python
# 导入所有指标
from tools.indicators import (
    # 趋势指标
    calculate_sma, calculate_ema, calculate_macd,
    calculate_bollinger_bands, identify_trend_direction,
    
    # 动量指标
    calculate_rsi, calculate_stochastic, calculate_cci,
    calculate_momentum, calculate_roc,
    
    # 波动率指标
    calculate_atr, calculate_standard_deviation,
    calculate_historical_volatility,
    
    # 成交量指标
    calculate_volume_ma, calculate_vwap, calculate_obv,
    calculate_mfi
)

# 或按需导入
from tools.indicators.trend import calculate_ema, calculate_macd
from tools.indicators.momentum import calculate_rsi
```

### 基本示例
```python
# 假设有价格数据
prices = [72000, 72100, 71900, 72300, 72500, 72400, 72600, 72800]

# 计算EMA
ema12 = calculate_ema(prices, 12)
ema26 = calculate_ema(prices, 26)

# 计算MACD
macd_data = calculate_macd(prices)
macd_line = macd_data['macd_line']
signal_line = macd_data['signal_line']

# 计算RSI
rsi = calculate_rsi(prices, 14)

# 识别趋势
trend = identify_trend_direction(prices, 10, 30)
print(f"趋势方向: {trend['direction']}, 强度: {trend['strength']:.2f}")
```

## 📈 指标分类

### 1. 趋势指标 (Trend Indicators)
识别市场趋势方向和强度。

| 指标 | 函数 | 参数 | 返回 | 用途 |
|------|------|------|------|------|
| **简单移动平均线** | `calculate_sma()` | prices, period | List[float] | 识别长期趋势 |
| **指数移动平均线** | `calculate_ema()` | prices, period | List[float] | 识别短期趋势 |
| **加权移动平均线** | `calculate_wma()` | prices, period | List[float] | 识别中期趋势 |
| **MACD** | `calculate_macd()` | prices, fast, slow, signal | Dict | 趋势强度和方向 |
| **布林带** | `calculate_bollinger_bands()` | prices, period, std_dev | Dict | 波动率和超买超卖 |
| **抛物线SAR** | `calculate_parabolic_sar()` | highs, lows, accel, max | List[float] | 止损和反转点 |
| **趋势识别** | `identify_trend_direction()` | prices, short, long | Dict | 综合趋势分析 |

### 2. 动量指标 (Momentum Indicators)
衡量价格变化的速度和强度。

| 指标 | 函数 | 参数 | 返回 | 用途 |
|------|------|------|------|------|
| **RSI** | `calculate_rsi()` | prices, period | List[float] | 超买超卖 (0-100) |
| **随机指标** | `calculate_stochastic()` | highs, lows, closes, k, d | Dict | 超买超卖和交叉 |
| **CCI** | `calculate_cci()` | highs, lows, closes, period | List[float] | 趋势强度和反转 |
| **动量指标** | `calculate_momentum()` | prices, period | List[float] | 价格变化速度 |
| **变动率** | `calculate_roc()` | prices, period | List[float] | 价格变化百分比 |
| **威廉指标** | `calculate_williams_r()` | highs, lows, closes, period | List[float] | 超买超卖 (-100-0) |
| **动量信号** | `identify_momentum_signals()` | prices, rsi_period, stoch_period | Dict | 综合动量分析 |

### 3. 波动率指标 (Volatility Indicators)
衡量价格波动的程度。

| 指标 | 函数 | 参数 | 返回 | 用途 |
|------|------|------|------|------|
| **ATR** | `calculate_atr()` | highs, lows, closes, period | List[float] | 真实波动幅度 |
| **标准差** | `calculate_standard_deviation()` | prices, period, use_sample | List[float] | 价格离散程度 |
| **肯特纳通道** | `calculate_keltner_channels()` | highs, lows, closes, ema, atr, mult | Dict | 波动率通道 |
| **唐奇安通道** | `calculate_donchian_channels()` | highs, lows, period | Dict | 突破系统通道 |
| **历史波动率** | `calculate_historical_volatility()` | prices, period, annualize | List[float] | 统计波动率 |
| **波动率比率** | `calculate_volatility_ratio()` | prices, short, long | List[float] | 波动率变化 |
| **波动率状态** | `identify_volatility_regime()` | prices, short, long, threshold | Dict | 波动率分析 |

### 4. 成交量指标 (Volume Indicators)
分析交易活跃度和资金流向。

| 指标 | 函数 | 参数 | 返回 | 用途 |
|------|------|------|------|------|
| **成交量均线** | `calculate_volume_ma()` | volumes, period | List[float] | 成交量趋势 |
| **VWAP** | `calculate_vwap()` | highs, lows, closes, volumes, period | List[float] | 成交量加权均价 |
| **OBV** | `calculate_obv()` | closes, volumes | List[float] | 资金流向 |
| **MFI** | `calculate_mfi()` | highs, lows, closes, volumes, period | List[float] | 资金流量指数 |
| **成交量比率** | `calculate_volume_ratio()` | volumes, short, long | List[float] | 成交量异常 |
| **成交量震荡** | `calculate_volume_oscillator()` | volumes, short, long | List[float] | 成交量变化 |
| **成交量信号** | `identify_volume_signals()` | closes, volumes, price_period, volume_period | Dict | 量价分析 |

## 🔧 使用指南

### 数据准备
```python
# 通常需要以下数据序列
prices = [...]          # 价格 (通常是收盘价)
highs = [...]           # 最高价
lows = [...]            # 最低价
closes = [...]          # 收盘价
volumes = [...]         # 成交量

# 确保数据长度一致
assert len(prices) == len(highs) == len(lows) == len(closes) == len(volumes)
```

### 参数选择
```python
# 常用参数配置
TREND_PARAMS = {
    'sma_period': 20,      # 长期趋势
    'ema_fast': 12,        # 短期趋势
    'ema_slow': 26,        # 长期趋势
    'macd_signal': 9,      # MACD信号线
    'bollinger_period': 20,# 布林带周期
    'bollinger_std': 2.0   # 布林带标准差
}

MOMENTUM_PARAMS = {
    'rsi_period': 14,      # RSI周期
    'stochastic_k': 14,    # 随机%K周期
    'stochastic_d': 3,     # 随机%D周期
    'cci_period': 20       # CCI周期
}

VOLATILITY_PARAMS = {
    'atr_period': 14,      # ATR周期
    'volatility_period': 20 # 波动率周期
}

VOLUME_PARAMS = {
    'volume_ma_period': 20, # 成交量均线周期
    'vwap_period': 20       # VWAP周期
}
```

### 综合分析示例
```python
def comprehensive_analysis(prices, highs, lows, closes, volumes):
    """综合技术分析"""
    
    # 趋势分析
    trend = identify_trend_direction(prices, 10, 30)
    macd_data = calculate_macd(prices)
    bands = calculate_bollinger_bands(prices)
    
    # 动量分析
    rsi = calculate_rsi(prices, 14)
    stoch = calculate_stochastic(highs, lows, closes, 14, 3)
    
    # 波动率分析
    atr = calculate_atr(highs, lows, closes, 14)
    volatility = identify_volatility_regime(prices, 10, 30)
    
    # 成交量分析
    obv = calculate_obv(closes, volumes)
    volume_signals = identify_volume_signals(closes, volumes)
    
    # 生成分析报告
    analysis = {
        'trend': {
            'direction': trend['direction'],
            'strength': trend['strength'],
            'macd_signal': 'bullish' if macd_data['macd_line'][-1] > macd_data['signal_line'][-1] else 'bearish',
            'bollinger_position': 'upper' if closes[-1] > bands['upper'][-1] else 
                                 'lower' if closes[-1] < bands['lower'][-1] else 'middle'
        },
        'momentum': {
            'rsi': rsi[-1],
            'rsi_signal': 'oversold' if rsi[-1] < 30 else 'overbought' if rsi[-1] > 70 else 'neutral',
            'stochastic_k': stoch['k_line'][-1],
            'stochastic_d': stoch['d_line'][-1]
        },
        'volatility': {
            'atr': atr[-1],
            'regime': volatility['regime'],
            'ratio': volatility['volatility_ratio']
        },
        'volume': {
            'obv_trend': 'rising' if obv[-1] > obv[-2] else 'falling',
            'confirmation': volume_signals['confirmation']
        }
    }
    
    return analysis
```

## 🧪 测试

### 运行指标测试
```bash
# 运行所有指标测试
pytest tests/unit/tools/test_indicators.py -v

# 运行特定指标测试
pytest tests/unit/tools/test_indicators.py::TestTrendIndicators -v
pytest tests/unit/tools/test_indicators.py::TestMomentumIndicators -v

# 生成测试报告
pytest tests/unit/tools/test_indicators.py --cov=tools.indicators --cov-report=html
```

### 测试数据生成
```python
def generate_test_data(n=100, trend='up', volatility=1.0):
    """生成测试数据"""
    import random
    
    prices = []
    base = 70000
    
    for i in range(n):
        if trend == 'up':
            price = base + i * 100 + random.uniform(-volatility*100, volatility*100)
        elif trend == 'down':
            price = base - i * 100 + random.uniform(-volatility*100, volatility*100)
        else:  # sideways
            price = base + random.uniform(-volatility*200, volatility*200)
        
        prices.append(price)
    
    # 生成其他价格序列
    highs = [p + random.uniform(0, 200) for p in prices]
    lows = [p - random.uniform(0, 200) for p in prices]
    closes = prices
    volumes = [1000 + random.randint(-200, 200) for _ in range(n)]
    
    return {
        'prices': prices,
        'highs': highs,
        'lows': lows,
        'closes': closes,
        'volumes': volumes
    }
```

## 📊 性能优化

### 批量计算
```python
def batch_calculate_indicators(data, indicators_config):
    """批量计算指标"""
    results = {}
    
    # 趋势指标
    if 'trend' in indicators_config:
        for indicator, params in indicators_config['trend'].items():
            if indicator == 'sma':
                results['sma'] = calculate_sma(data['prices'], **params)
            elif indicator == 'ema':
                results['ema'] = calculate_ema(data['prices'], **params)
            # ... 其他指标
    
    # 动量指标
    if 'momentum' in indicators_config:
        for indicator, params in indicators_config['momentum'].items():
            if indicator == 'rsi':
                results['rsi'] = calculate_rsi(data['prices'], **params)
            # ... 其他指标
    
    return results
```

### 缓存优化
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def cached_calculate_sma(prices_tuple, period):
    """带缓存的SMA计算"""
    prices = list(prices_tuple)
    return calculate_sma(prices, period)

# 使用缓存
prices_tuple = tuple(prices)  # 转换为元组以便哈希
sma = cached_calculate_sma(prices_tuple, 20)
```

## 🔄 集成到分析系统

### 与数据工具集成
```python
from tools.data.fetch import fetch_klines
from tools.indicators import calculate_ema, calculate_rsi, calculate_atr

def analyze_symbol(symbol, timeframe='4h'):
    """分析交易对"""
    # 获取数据
    klines = fetch_klines(symbol, timeframe, 100)
    closes = [k['close'] for k in klines]
    highs = [k['high'] for k in klines]
    lows = [k['low'] for k in klines]
    
    # 计算指标
    ema12 = calculate_ema(closes, 12)
    ema26 = calculate_ema(closes, 26)
    rsi = calculate_rsi(closes, 14)
    atr = calculate_atr(highs, lows, closes, 14)
    
    return {
        'symbol': symbol,
        'timeframe': timeframe,
        'price': closes[-1],
        'ema12': ema12[-1],
        'ema26': ema26[-1],
        'rsi': rsi[-1],
        'atr': atr[-1]
    }
```

### 生成交易信号
```python
def generate_trading_signals(analysis):
    """生成交易信号"""
    signals = []
    
    # 趋势信号
    if analysis['trend']['direction'] == 'up':
        if analysis['trend']['macd_signal'] == 'bullish':
            signals.append('trend_bullish')
    
    # 动量信号
    if analysis['momentum']['rsi_signal'] == 'oversold':
        signals.append('rsi_oversold')
    elif analysis['momentum']['rsi_signal'] == 'overbought':
        signals.append('rsi_overbought')
    
    # 波动率信号
    if analysis['volatility']['regime'] == 'high':
        signals.append('high_volatility')
    
    # 成交量信号
    if analysis['volume']['confirmation'] == 'confirmed':
        signals.append('volume_confirmation')
    
    return signals
```

## 📚 学习资源

### 指标解释
- **移动平均线**: 识别趋势方向，金叉死叉信号
- **MACD**: 趋势强度和动量，柱状图表示加速度
- **RSI**: 超买超卖，背离信号预示反转
- **布林带**: 波动率和价格位置，带宽收缩预示突破
- **ATR**: 真实波动幅度，用于止损和仓位计算

### 交易策略
1. **趋势跟踪**: EMA交叉 + 成交量确认
2. **均值回归**: RSI超买超卖 + 布林带位置
3. **突破交易**: 布林带突破 + 成交量放大
4. **动量交易**: MACD金叉死叉 + RSI确认

## 🔧 开发新指标

### 模板
```python
def calculate_new_indicator(prices, period, **kwargs):
    """
    新指标计算函数
    
    参数:
        prices: 价格序列
        period: 计算周期
        **kwargs: 其他参数
    
    返回:
        指标值序列
    
    示例:
        >>> values = calculate_new_indicator(prices, 14)
    """
    # 参数验证
    if not prices or period <= 0:
        return []
    
    # 计算逻辑
    values = []
    for i in range(len(prices)):
        if i < period - 1:
            values.append(None)
        else:
            # 计算指标值
            window = prices[i - period + 1:i + 1]
            value = calculate_value(window, **kwargs)
            values.append(value)
    
    return values
```

### 添加测试
```python
def test_calculate_new_indicator():
    """测试新指标"""
    prices = [100, 102, 101, 103, 105]
    values = calculate_new_indicator(prices, 3)
    
    assert len(values) == len(prices)
    assert values[0] is None
    assert values[1] is None
    assert values[2] is not None
```

---

**版本**: 1.0.0  
**指标数量**: 28个  
**类别**: 趋势(