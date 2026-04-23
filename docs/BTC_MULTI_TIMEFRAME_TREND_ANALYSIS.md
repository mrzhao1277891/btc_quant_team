# BTC 多周期市场趋势判断方法论

> 本文档描述了一套用于判断 BTC 在月线、周线、日线、4小时线四个周期上市场状态（上涨/下跌/震荡）的系统化方法，并给出可直接用于代码实现的量化规则。

---

## 一、核心理念：周期层级与职责分工

多周期分析的本质是"战略-战术"分层决策：

| 周期 | 职责 | 解决的问题 | 更新频率 |
|------|------|-----------|---------|
| 月线 | 定大局（战略方向） | 当前处于牛市、熊市还是大横盘？ | 每月末 |
| 周线 | 定波段（战略执行） | 当前波段方向，何时顺势入场？ | 每周末 |
| 日线 | 定节奏（战术区域） | 当前是顺势还是回调？能否入场？ | 每天 |
| 4小时 | 定入场（战术执行） | 具体在哪里进场？止损设在哪里？ | 盘中 |

**核心原则：大周期方向优先。** 日线和4h只能帮你择时，不能让你逆着月线/周线操作。

---

## 二、三种市场状态定义

| 状态 | 价格结构 | 均线特征 |
|------|---------|---------|
| **上涨** | 波谷依次抬高（HL），波峰依次抬高（HH） | 均线多头排列，向上倾斜 |
| **下跌** | 波峰依次降低（LH），波谷依次降低（LL） | 均线空头排列，向下倾斜 |
| **震荡** | 高低点在同一水平区间内来回 | 均线缠绕走平，价格反复穿越 |

---

## 三、判断方法：三维度综合评分

对每个周期，从以下三个维度独立打分，再综合判断。

### 维度 1：均线排列（权重 40%，满分 ±2）

使用指数移动平均线（EMA），参数：EMA5、EMA10、EMA20，均基于收盘价计算。

> 选用 EMA 而非 SMA 的原因：EMA 对近期价格赋予更高权重，对 BTC 这类波动大的资产反应更灵敏，能比 SMA 提前 1~3 根 K 线捕捉趋势转变。

| 条件 | 得分 |
|------|------|
| EMA5 > EMA10 > EMA20，且 EMA5 向上倾斜（EMA5[-1] > EMA5[-2]） | +2 |
| EMA5 < EMA10 < EMA20，且 EMA5 向下倾斜（EMA5[-1] < EMA5[-2]） | -2 |
| 其他（均线缠绕/走平） | 0 |

### 维度 2：价格与 EMA20 的关系（权重 30%，满分 ±1.5）

| 条件 | 得分 |
|------|------|
| 当前收盘价 > EMA20，且过去 5 根 K 线中至少 4 根收盘价 > EMA20 | +1.5 |
| 当前收盘价 < EMA20，且过去 5 根 K 线中至多 1 根收盘价 > EMA20 | -1.5 |
| 其他 | 0 |

### 维度 3：波峰波谷结构（权重 30%，满分 ±1.5）

**摆动点识别规则（左右各 2 根 K 线）：**
- 波峰：某根 K 线的最高价 > 左边 2 根 K 线的最高价，且 > 右边 2 根 K 线的最高价
- 波谷：某根 K 线的最低价 < 左边 2 根 K 线的最低价，且 < 右边 2 根 K 线的最低价

取最近 3 个波峰和 3 个波谷进行判断：

| 条件 | 得分 |
|------|------|
| 最近 3 个波谷依次抬高（trough[0] < trough[1] < trough[2]），且最近波峰 > 前一波峰 | +1.5 |
| 最近 3 个波峰依次降低（peak[0] > peak[1] > peak[2]），且最近波谷 < 前一波谷 | -1.5 |
| 其他 | 0 |

### 综合判定

```
total_score = ma_score + price_ma_score + structure_score
```

| 总分 | 市场状态 |
|------|---------|
| total_score ≥ +2 | 上涨（up） |
| total_score ≤ -2 | 下跌（down） |
| -2 < total_score < +2 | 震荡（ranging） |

可选置信度：`confidence = abs(total_score) / 5.0`（最大值为 1.0）

---

## 四、各周期参数规格

| 周期 | 最少 K 线数 | 推荐 K 线数 | 均线参数 | 摆动点左右窗口 |
|------|-----------|-----------|---------|-------------|
| 月线 | 20 根 | 20 根 | EMA5 / EMA10 / EMA20 | 左右各 2 根 |
| 周线 | 30 根 | 30 根 | EMA5 / EMA10 / EMA20 | 左右各 2 根 |
| 日线 | 100 根 | 100 根 | EMA10 / EMA20 / EMA50 | 左右各 2 根 |
| 4小时 | 150 根 | 150 根 | EMA20 / EMA50 / EMA100 | 左右各 2 根 |

> **注意：** 日线和 4h 的均线参数相应放大，以过滤更多噪音。

---

## 五、数据不足时的处理

各周期数据量须满足最低要求，若不足则返回 `"insufficient_data"`，不给出判断。

---

## 六、四周期联动决策

### 6.1 各周期独立判断

对月线、周线、日线、4h 分别运行 `detect_trend()`，得到各自的市场状态：

```python
result = {
    "month": detect_trend(month_klines, "month"),   # up / down / ranging
    "week":  detect_trend(week_klines,  "week"),
    "day":   detect_trend(day_klines,   "day"),
    "4h":    detect_trend(h4_klines,    "4h"),
}
```

### 6.2 趋势破坏风险检测（低周期 → 高周期）

低周期的逆向信号可能预示高周期趋势即将被破坏，需要提前预警。判断规则如下：

**月线趋势破坏风险**（参考周线信号）：
| 月线状态 | 周线状态 | 风险等级 | 含义 |
|---------|---------|---------|------|
| 上涨 | 下跌 | 高风险 | 周线已转跌，月线上涨趋势可能被破坏 |
| 上涨 | 震荡 | 中风险 | 月线上涨动能减弱，需观察 |
| 上涨 | 上涨 | 无风险 | 趋势一致，安全 |
| 下跌 | 上涨 | 高风险 | 周线已转涨，月线下跌趋势可能被破坏 |
| 下跌 | 震荡 | 中风险 | 月线下跌动能减弱，需观察 |
| 下跌 | 下跌 | 无风险 | 趋势一致，安全 |

**周线趋势破坏风险**（参考日线信号）：
- 周线上涨 + 日线下跌 → 高风险
- 周线上涨 + 日线震荡 → 中风险
- 周线下跌 + 日线上涨 → 高风险
- 周线下跌 + 日线震荡 → 中风险
- 其他（方向一致） → 无风险

**日线趋势破坏风险**（参考4h信号）：
- 日线上涨 + 4h 下跌 → 高风险
- 日线上涨 + 4h 震荡 → 中风险
- 日线下跌 + 4h 上涨 → 高风险
- 日线下跌 + 4h 震荡 → 中风险
- 其他（方向一致） → 无风险

### 6.3 主方向决策（月线 + 周线）

| 月线状态 | 周线状态 | 主要交易方向 | 操作策略 |
|---------|---------|------------|---------|
| 上涨 | 上涨 | 只做多 | 最强趋势，寻找做多机会 |
| 上涨 | 震荡 | 偏多 | 上涨中的盘整，等待周线方向明确 |
| 上涨 | 下跌 | 观望 | 周线回调，等待企稳，不做空 |
| 下跌 | 下跌 | 只做空 | 最强下跌，寻找做空机会 |
| 下跌 | 震荡 | 偏空 | 下跌中的盘整，等待周线方向明确 |
| 下跌 | 上涨 | 观望 | 周线反弹，等待结束，不做多 |
| 震荡 | 任意 | 观望 | 月线无方向，趋势策略失效，降低仓位 |

### 6.4 综合输出格式

```python
{
    "timeframes": {
        "month": {"trend": "up",      "confidence": 0.9, "details": {...}},
        "week":  {"trend": "ranging", "confidence": 0.4, "details": {...}},
        "day":   {"trend": "down",    "confidence": 0.6, "details": {...}},
        "4h":    {"trend": "down",    "confidence": 0.7, "details": {...}},
    },
    "risk": {
        "month_risk": "中风险",   # 月线趋势破坏风险（参考周线）
        "week_risk":  "高风险",   # 周线趋势破坏风险（参考日线）
        "day_risk":   "无风险",   # 日线趋势破坏风险（参考4h）
    },
    "decision": {
        "direction": "观望",      # 主方向：只做多 / 偏多 / 观望 / 偏空 / 只做空
        "basis": "月线上涨，周线震荡"
    }
}
```

---

## 七、代码实现规范

### 输入格式

```python
klines = [
    {"open": float, "high": float, "low": float, "close": float},
    ...
]
period_type = "month" | "week" | "day" | "4h"
```

### 输出格式

```python
{
    "trend": "up" | "down" | "ranging" | "insufficient_data",
    "confidence": float,  # 0.0 ~ 1.0
    "details": {
        "ma_score": float,          # 均线排列得分
        "price_ma_score": float,    # 价格与EMA20关系得分
        "structure_score": float,   # 波峰波谷结构得分
        "total_score": float        # 综合得分
    }
}
```

### 核心伪代码

```python
def detect_trend(klines: list, period_type: str) -> dict:
    MIN_REQUIRED = {"month": 20, "week": 30, "day": 100, "4h": 150}

    # 数据不足时直接返回
    if len(klines) < MIN_REQUIRED[period_type]:
        return {"trend": "insufficient_data", "confidence": 0.0}

    closes = [k["close"] for k in klines]
    highs  = [k["high"]  for k in klines]
    lows   = [k["low"]   for k in klines]

    # --- 维度1：均线排列 ---
    ema5  = ema(closes, 5)
    ema10 = ema(closes, 10)
    ema20 = ema(closes, 20)

    if ema5[-1] > ema10[-1] > ema20[-1] and ema5[-1] > ema5[-2]:
        ma_score = 2.0
    elif ema5[-1] < ema10[-1] < ema20[-1] and ema5[-1] < ema5[-2]:
        ma_score = -2.0
    else:
        ma_score = 0.0

    # --- 维度2：价格与EMA20关系 ---
    above_count = sum(1 for i in range(-5, 0) if closes[i] > ema20[i])
    if closes[-1] > ema20[-1] and above_count >= 4:
        price_ma_score = 1.5
    elif closes[-1] < ema20[-1] and above_count <= 1:
        price_ma_score = -1.5
    else:
        price_ma_score = 0.0

    # --- 维度3：波峰波谷结构 ---
    peaks, troughs = find_swing_points(highs, lows, left=2, right=2)
    last_peaks   = peaks[-3:]   if len(peaks)   >= 3 else []
    last_troughs = troughs[-3:] if len(troughs) >= 3 else []

    if (len(last_troughs) == 3
            and last_troughs[0] < last_troughs[1] < last_troughs[2]
            and len(last_peaks) >= 2
            and last_peaks[-1] > last_peaks[-2]):
        structure_score = 1.5
    elif (len(last_peaks) == 3
            and last_peaks[0] > last_peaks[1] > last_peaks[2]
            and len(last_troughs) >= 2
            and last_troughs[-1] < last_troughs[-2]):
        structure_score = -1.5
    else:
        structure_score = 0.0

    # --- 综合判定 ---
    total = ma_score + price_ma_score + structure_score
    if total >= 2:
        trend = "up"
    elif total <= -2:
        trend = "down"
    else:
        trend = "ranging"

    return {
        "trend": trend,
        "confidence": min(abs(total) / 5.0, 1.0),
        "details": {
            "ma_score": ma_score,
            "price_ma_score": price_ma_score,
            "structure_score": structure_score,
            "total_score": total
        }
    }
```

---

## 八、关键注意事项

1. **及时性与准确性的权衡**：等月线收盘确认最准确，但滞后；用周线突破关键位（前高/前低、重要均线）作为早期信号，可提前 2~3 周判断，但需接受一定假信号率。

2. **假突破过滤**：突破信号需等待 K 线收盘确认，不以盘中价格为准。

3. **周期矛盾时的处理**：月线与周线方向矛盾时，优先服从月线。周线的逆向运动通常只是回调，不应重仓逆势操作。

4. **震荡市的策略切换**：月线处于震荡时，趋势跟踪策略失效，应降低仓位或切换为高抛低吸策略。

5. **止损纪律**：入场后，止损必须设在对应周期的关键结构位（波谷/波峰）之外，不能因为大周期看涨就忽略止损。

---

*最后更新：基于多周期趋势分析方法论整理*
