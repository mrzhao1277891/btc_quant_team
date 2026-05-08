# Backend 模块

BTC回测系统的后端核心模块。

## 模块结构

```
backend/
├── __init__.py          # 包初始化文件
├── indicators.py        # 技术指标计算模块
└── README.md           # 本文档
```

## 技术指标计算模块 (indicators.py)

### IndicatorCalculator 类

提供各种技术指标的计算方法，所有计算使用 Pandas 进行向量化操作以提高性能。

### 支持的指标

1. **EMA (指数移动平均线)**
   - 公式: `EMA_today = (Price_today * K) + (EMA_yesterday * (1 - K))`
   - 其中 `K = 2 / (N + 1)`

2. **RSI (相对强弱指标)**
   - 公式: `RSI = 100 - (100 / (1 + RS))`
   - 其中 `RS = Average_Gain / Average_Loss`

3. **MACD (移动平均收敛散度)**
   - DIF (快线): `EMA12 - EMA26`
   - DEA (慢线): `EMA9(DIF)`
   - MACD柱状图: `DIF - DEA`

4. **布林带 (Bollinger Bands)**
   - 中轨: `SMA(period)`
   - 上轨: `中轨 + (std_dev * 标准差)`
   - 下轨: `中轨 - (std_dev * 标准差)`

5. **ATR (平均真实波幅)**
   - 公式: `ATR = EMA(period, True_Range)`
   - 其中 `True_Range = max(High - Low, abs(High - Previous_Close), abs(Low - Previous_Close))`

### 使用示例

#### 计算单个指标

```python
import pandas as pd
from backend.indicators import IndicatorCalculator

# 准备价格数据
prices = pd.Series([100, 102, 101, 103, 105, 104, 106, 108, 107, 109])

# 计算 EMA
ema7 = IndicatorCalculator.calculate_ema(prices, period=7)
print(f"EMA(7): {ema7.tolist()}")

# 计算 RSI
rsi14 = IndicatorCalculator.calculate_rsi(prices, period=14)
print(f"RSI(14): {rsi14.tolist()}")

# 计算 MACD
dif, dea, macd = IndicatorCalculator.calculate_macd(prices)
print(f"MACD DIF: {dif.tolist()}")
print(f"MACD DEA: {dea.tolist()}")
print(f"MACD Histogram: {macd.tolist()}")
```

#### 计算所有指标

```python
import pandas as pd
from backend.indicators import IndicatorCalculator

# 准备 OHLCV 数据
df = pd.DataFrame({
    'close': [100, 102, 101, 103, 105, 104, 106, 108, 107, 109],
    'high': [105, 107, 106, 108, 110, 109, 111, 113, 112, 114],
    'low': [95, 97, 96, 98, 100, 99, 101, 103, 102, 104],
    'volume': [1000, 1100, 1050, 1200, 1150, 1080, 1300, 1250, 1180, 1400]
})

# 创建计算器实例
calculator = IndicatorCalculator()

# 计算所有指标
df_with_indicators = calculator.calculate_all_indicators(df)

# 查看结果
print(df_with_indicators.columns.tolist())
# 输出: ['close', 'high', 'low', 'volume', 'EMA7', 'EMA25', 'EMA50', 
#        'RSI14', 'RSI6', 'MACD_DIF', 'MACD_DEA', 'MACD_Histogram',
#        'Bollinger_Upper', 'Bollinger_Middle', 'Bollinger_Lower', 'ATR']
```

### 数据不足处理

当数据不足以计算指标时（例如，只有 5 个数据点但要计算 EMA(20)），指标计算器会：

- **EMA**: 返回 NaN 直到有足够的数据点
- **RSI**: 返回 NaN 直到有足够的数据点（通过 `min_periods` 参数控制）
- **MACD**: 各组件返回 NaN 直到有足够的数据点
- **布林带**: 返回 NaN 直到有足够的数据点
- **ATR**: 返回 NaN 直到有足够的数据点

示例：

```python
import pandas as pd
from backend.indicators import IndicatorCalculator

# 只有 5 个数据点
prices = pd.Series([100, 102, 101, 103, 105])

# 尝试计算 EMA(20)
ema20 = IndicatorCalculator.calculate_ema(prices, period=20)
print(ema20.tolist())  # 输出: [nan, nan, nan, nan, nan]

# 计算 EMA(3) - 有足够数据
ema3 = IndicatorCalculator.calculate_ema(prices, period=3)
print(ema3.tolist())  # 输出: [nan, nan, 101.0, 102.0, 103.5]
```

### 错误处理

指标计算器会对无效输入进行验证：

```python
import pandas as pd
from backend.indicators import IndicatorCalculator

prices = pd.Series([100, 102, 101])

# 无效的周期参数
try:
    ema = IndicatorCalculator.calculate_ema(prices, period=0)
except ValueError as e:
    print(f"错误: {e}")  # 输出: 错误: Period must be positive, got 0

# 缺少必需列
df = pd.DataFrame({'close': [100, 102, 101]})  # 缺少 high, low, volume
calculator = IndicatorCalculator()
try:
    result = calculator.calculate_all_indicators(df)
except ValueError as e:
    print(f"错误: {e}")  # 输出: 错误: DataFrame missing required columns: ['high', 'low', 'volume']
```

## 性能考虑

- 所有指标计算使用 Pandas 的向量化操作，避免 Python 循环
- `calculate_all_indicators` 方法会一次性计算所有指标，避免重复遍历数据
- 对于大型数据集（>10000 行），计算时间应该在秒级

## 测试

运行单元测试：

```bash
pytest tests/test_indicators.py -v
```

## 依赖

- pandas >= 1.5.0
- numpy >= 1.24.0

## 下一步

- [ ] 实现数据库连接器 (DatabaseConnector)
- [ ] 实现回测引擎 (BacktestEngine)
- [ ] 实现性能指标计算器 (MetricsCalculator)
