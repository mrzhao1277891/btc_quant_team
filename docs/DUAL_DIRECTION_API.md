# 双向交易策略 API 文档

## 概述

本文档详细说明双向交易策略的 API 接口，包括请求参数、响应格式和使用示例。

## 基础信息

- **Base URL**: `http://127.0.0.1:8001`
- **Content-Type**: `application/json`
- **API 版本**: v1.0

## 接口列表

### 1. 运行回测

提交双向交易策略回测任务。

**端点**: `POST /api/backtest`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `strategy_name` | string | 是 | 策略名称 | "双向RSI策略" |
| `timeframe` | string | 是 | 时间周期 | "1d", "4h", "1h" |
| `start_date` | string | 是 | 开始日期 | "2024-01-01" |
| `end_date` | string | 是 | 结束日期 | "2024-12-31" |
| `initial_capital` | float | 是 | 初始资金 | 10000 |
| `position_size` | float | 是 | 持仓大小 | 2000 |
| `leverage` | float | 否 | 杠杆倍数 | 5 (默认1) |
| `long_entry_conditions` | array | 否* | 做多开仓条件 | 见下方 |
| `long_entry_logic` | string | 否 | 做多开仓逻辑 | "AND", "OR" |
| `long_exit_conditions` | array | 否 | 做多平仓条件 | 见下方 |
| `long_exit_logic` | string | 否 | 做多平仓逻辑 | "AND", "OR" |
| `long_take_profit_pct` | float | 否 | 做多止盈百分比 | 10 |
| `long_stop_loss_pct` | float | 否 | 做多止损百分比 | 5 |
| `short_entry_conditions` | array | 否* | 做空开仓条件 | 见下方 |
| `short_entry_logic` | string | 否 | 做空开仓逻辑 | "AND", "OR" |
| `short_exit_conditions` | array | 否 | 做空平仓条件 | 见下方 |
| `short_exit_logic` | string | 否 | 做空平仓逻辑 | "AND", "OR" |
| `short_take_profit_pct` | float | 否 | 做空止盈百分比 | 10 |
| `short_stop_loss_pct` | float | 否 | 做空止损百分比 | 5 |

*注意: `long_entry_conditions` 和 `short_entry_conditions` 至少需要配置一个。

**条件对象结构**:

```json
{
  "indicator": "rsi14",
  "operator": "<",
  "value": 30,
  "timeframe": "1d"
}
```

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `indicator` | string | 是 | 指标名称 | "rsi14", "ema7", "close" |
| `operator` | string | 是 | 比较运算符 | ">", "<", ">=", "<=", "==" |
| `value` | float/string | 是 | 比较值或指标名 | 30, "ema25" |
| `timeframe` | string | 否 | 时间周期 | "1d" |

**可用指标**:

| 指标 | 说明 |
|------|------|
| `ema7`, `ema12`, `ema25`, `ema50` | 指数移动平均线 |
| `rsi6`, `rsi14` | 相对强弱指标 |
| `dif`, `dea`, `macd` | MACD 指标 |
| `boll_up`, `boll_md`, `boll_dn` | 布林带 |
| `atr` | 平均真实波幅 |
| `close` | 收盘价 |
| `volume` | 成交量 |

**请求示例**:

```bash
curl -X POST "http://127.0.0.1:8001/api/backtest" \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_name": "双向RSI策略",
    "timeframe": "1d",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "initial_capital": 10000,
    "position_size": 2000,
    "leverage": 5,
    "long_entry_conditions": [
      {"indicator": "rsi14", "operator": "<", "value": 30},
      {"indicator": "close", "operator": ">", "value": "ema50"}
    ],
    "long_entry_logic": "AND",
    "long_exit_conditions": [
      {"indicator": "rsi14", "operator": ">", "value": 70}
    ],
    "long_exit_logic": "OR",
    "long_take_profit_pct": 10,
    "long_stop_loss_pct": 5,
    "short_entry_conditions": [
      {"indicator": "rsi14", "operator": ">", "value": 70},
      {"indicator": "close", "operator": "<", "value": "ema50"}
    ],
    "short_entry_logic": "AND",
    "short_exit_conditions": [
      {"indicator": "rsi14", "operator": "<", "value": 30}
    ],
    "short_exit_logic": "OR",
    "short_take_profit_pct": 10,
    "short_stop_loss_pct": 5
  }'
```

**响应**:

```json
{
  "backtest_id": "bt_1234567890",
  "status": "queued",
  "message": "回测任务已提交"
}
```

**响应字段**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `backtest_id` | string | 回测任务ID |
| `status` | string | 任务状态: "queued", "running", "completed", "failed" |
| `message` | string | 状态消息 |

---

### 2. 查询回测状态

查询回测任务的执行状态。

**端点**: `GET /api/backtest/{backtest_id}/status`

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `backtest_id` | string | 回测任务ID |

**请求示例**:

```bash
curl "http://127.0.0.1:8001/api/backtest/bt_1234567890/status"
```

**响应**:

```json
{
  "backtest_id": "bt_1234567890",
  "status": "completed",
  "progress": 100,
  "message": "回测完成"
}
```

**响应字段**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `backtest_id` | string | 回测任务ID |
| `status` | string | 任务状态 |
| `progress` | int | 进度百分比 (0-100) |
| `message` | string | 状态消息 |

---

### 3. 获取回测结果

获取已完成回测的详细结果。

**端点**: `GET /api/backtest/{backtest_id}/results`

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `backtest_id` | string | 回测任务ID |

**请求示例**:

```bash
curl "http://127.0.0.1:8001/api/backtest/bt_1234567890/results"
```

**响应**:

```json
{
  "backtest_id": "bt_1234567890",
  "strategy_config": {
    "strategy_name": "双向RSI策略",
    "timeframe": "1d",
    "initial_capital": 10000,
    "position_size": 2000,
    "leverage": 5
  },
  "performance_metrics": {
    "total_return": 1250.50,
    "total_return_pct": 12.51,
    "win_rate": 65.5,
    "max_drawdown": -8.3,
    "max_drawdown_pct": -8.3,
    "sharpe_ratio": 1.85,
    "profit_factor": 2.1,
    "total_trades": 45,
    "winning_trades": 30,
    "losing_trades": 15,
    "avg_win": 150.5,
    "avg_loss": -75.2,
    "largest_win": 450.0,
    "largest_loss": -200.0
  },
  "trades": [
    {
      "trade_id": 1,
      "direction": "long",
      "entry_time": "2024-01-15T00:00:00",
      "entry_price": 45000.0,
      "exit_time": "2024-01-20T00:00:00",
      "exit_price": 47000.0,
      "position_size": 0.044,
      "entry_capital": 2000.0,
      "profit_loss": 200.0,
      "profit_loss_pct": 10.0,
      "exit_reason": "take_profit"
    },
    {
      "trade_id": 2,
      "direction": "short",
      "entry_time": "2024-02-01T00:00:00",
      "entry_price": 48000.0,
      "exit_time": "2024-02-05T00:00:00",
      "exit_price": 46000.0,
      "position_size": 0.042,
      "entry_capital": 2000.0,
      "profit_loss": 200.0,
      "profit_loss_pct": 10.0,
      "exit_reason": "take_profit"
    }
  ],
  "equity_curve": [
    {"timestamp": "2024-01-01T00:00:00", "equity": 10000.0},
    {"timestamp": "2024-01-15T00:00:00", "equity": 10200.0},
    {"timestamp": "2024-02-05T00:00:00", "equity": 10400.0}
  ]
}
```

**响应字段说明**:

#### strategy_config
策略配置信息（与请求参数一致）

#### performance_metrics

| 字段 | 类型 | 说明 |
|------|------|------|
| `total_return` | float | 总收益金额 (USDT) |
| `total_return_pct` | float | 总收益率 (%) |
| `win_rate` | float | 胜率 (%) |
| `max_drawdown` | float | 最大回撤金额 (USDT) |
| `max_drawdown_pct` | float | 最大回撤百分比 (%) |
| `sharpe_ratio` | float | 夏普比率 |
| `profit_factor` | float | 盈亏比 |
| `total_trades` | int | 总交易次数 |
| `winning_trades` | int | 盈利交易次数 |
| `losing_trades` | int | 亏损交易次数 |
| `avg_win` | float | 平均盈利 (USDT) |
| `avg_loss` | float | 平均亏损 (USDT) |
| `largest_win` | float | 最大单笔盈利 (USDT) |
| `largest_loss` | float | 最大单笔亏损 (USDT) |

#### trades

| 字段 | 类型 | 说明 |
|------|------|------|
| `trade_id` | int | 交易ID |
| `direction` | string | 交易方向: "long" 或 "short" |
| `entry_time` | string | 开仓时间 (ISO 8601) |
| `entry_price` | float | 开仓价格 |
| `exit_time` | string | 平仓时间 (ISO 8601) |
| `exit_price` | float | 平仓价格 |
| `position_size` | float | 持仓数量 (BTC) |
| `entry_capital` | float | 开仓资金/保证金 (USDT) |
| `profit_loss` | float | 盈亏金额 (USDT) |
| `profit_loss_pct` | float | 盈亏百分比 (%) |
| `exit_reason` | string | 平仓原因 |

**平仓原因 (exit_reason)**:
- `"take_profit"`: 止盈
- `"stop_loss"`: 止损
- `"exit_signal"`: 平仓信号
- `"reverse_signal"`: 反向信号
- `"end_of_backtest"`: 回测结束

#### equity_curve

| 字段 | 类型 | 说明 |
|------|------|------|
| `timestamp` | string | 时间戳 (ISO 8601) |
| `equity` | float | 账户权益 (USDT) |

---

### 4. 获取策略模板

获取预设的策略模板列表。

**端点**: `GET /api/strategy-templates`

**请求示例**:

```bash
curl "http://127.0.0.1:8001/api/strategy-templates"
```

**响应**:

```json
{
  "templates": [
    {
      "id": "dual_rsi",
      "name": "双向RSI策略",
      "description": "RSI<30做多，RSI>70做空，配合EMA过滤",
      "category": "dual_direction",
      "config": {
        "strategy_name": "双向RSI策略",
        "timeframe": "1d",
        "initial_capital": 10000,
        "position_size": 2000,
        "leverage": 5,
        "long_entry_conditions": [
          {"indicator": "rsi14", "operator": "<", "value": 30},
          {"indicator": "close", "operator": ">", "value": "ema50"}
        ],
        "long_entry_logic": "AND",
        "long_take_profit_pct": 10,
        "long_stop_loss_pct": 5,
        "short_entry_conditions": [
          {"indicator": "rsi14", "operator": ">", "value": 70},
          {"indicator": "close", "operator": "<", "value": "ema50"}
        ],
        "short_entry_logic": "AND",
        "short_take_profit_pct": 10,
        "short_stop_loss_pct": 5
      }
    },
    {
      "id": "dual_ma_crossover",
      "name": "双向均线策略",
      "description": "价格突破EMA25做多，跌破EMA25做空",
      "category": "dual_direction",
      "config": {...}
    },
    {
      "id": "dual_bollinger",
      "name": "双向布林带策略",
      "description": "触及下轨做多，触及上轨做空",
      "category": "dual_direction",
      "config": {...}
    }
  ]
}
```

**响应字段**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 模板ID |
| `name` | string | 模板名称 |
| `description` | string | 模板描述 |
| `category` | string | 模板分类: "dual_direction", "long_only", "short_only" |
| `config` | object | 策略配置对象 |

---

## 错误处理

所有 API 错误响应遵循统一格式：

```json
{
  "error": "错误类型",
  "message": "详细错误信息",
  "details": {
    "field": "具体字段",
    "reason": "错误原因"
  }
}
```

**常见错误码**:

| HTTP 状态码 | 错误类型 | 说明 |
|------------|---------|------|
| 400 | Bad Request | 请求参数错误 |
| 404 | Not Found | 回测任务不存在 |
| 422 | Validation Error | 参数验证失败 |
| 500 | Internal Server Error | 服务器内部错误 |

**错误示例**:

```json
{
  "error": "ValidationError",
  "message": "至少需要配置一个方向的开仓条件",
  "details": {
    "field": "entry_conditions",
    "reason": "long_entry_conditions 和 short_entry_conditions 都为空"
  }
}
```

---

## 使用示例

### Python 示例

```python
import requests
import json

# 配置
BASE_URL = "http://127.0.0.1:8001"

# 1. 提交回测任务
config = {
    "strategy_name": "双向RSI策略",
    "timeframe": "1d",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "initial_capital": 10000,
    "position_size": 2000,
    "leverage": 5,
    "long_entry_conditions": [
        {"indicator": "rsi14", "operator": "<", "value": 30},
        {"indicator": "close", "operator": ">", "value": "ema50"}
    ],
    "long_entry_logic": "AND",
    "long_take_profit_pct": 10,
    "long_stop_loss_pct": 5,
    "short_entry_conditions": [
        {"indicator": "rsi14", "operator": ">", "value": 70},
        {"indicator": "close", "operator": "<", "value": "ema50"}
    ],
    "short_entry_logic": "AND",
    "short_take_profit_pct": 10,
    "short_stop_loss_pct": 5
}

response = requests.post(f"{BASE_URL}/api/backtest", json=config)
result = response.json()
backtest_id = result["backtest_id"]
print(f"回测任务ID: {backtest_id}")

# 2. 查询状态
import time
while True:
    response = requests.get(f"{BASE_URL}/api/backtest/{backtest_id}/status")
    status = response.json()
    print(f"状态: {status['status']}, 进度: {status['progress']}%")
    
    if status['status'] == 'completed':
        break
    elif status['status'] == 'failed':
        print("回测失败")
        exit(1)
    
    time.sleep(2)

# 3. 获取结果
response = requests.get(f"{BASE_URL}/api/backtest/{backtest_id}/results")
results = response.json()

# 打印性能指标
metrics = results['performance_metrics']
print(f"\n=== 回测结果 ===")
print(f"总收益: {metrics['total_return']:.2f} USDT ({metrics['total_return_pct']:.2f}%)")
print(f"胜率: {metrics['win_rate']:.2f}%")
print(f"最大回撤: {metrics['max_drawdown_pct']:.2f}%")
print(f"夏普比率: {metrics['sharpe_ratio']:.2f}")
print(f"总交易次数: {metrics['total_trades']}")

# 打印交易记录
print(f"\n=== 交易记录 ===")
for trade in results['trades'][:5]:  # 显示前5笔交易
    print(f"交易#{trade['trade_id']}: {trade['direction']} | "
          f"盈亏: {trade['profit_loss']:.2f} ({trade['profit_loss_pct']:.2f}%) | "
          f"原因: {trade['exit_reason']}")
```

### JavaScript 示例

```javascript
const BASE_URL = "http://127.0.0.1:8001";

// 1. 提交回测任务
async function runBacktest() {
  const config = {
    strategy_name: "双向RSI策略",
    timeframe: "1d",
    start_date: "2024-01-01",
    end_date: "2024-12-31",
    initial_capital: 10000,
    position_size: 2000,
    leverage: 5,
    long_entry_conditions: [
      { indicator: "rsi14", operator: "<", value: 30 },
      { indicator: "close", operator: ">", value: "ema50" }
    ],
    long_entry_logic: "AND",
    long_take_profit_pct: 10,
    long_stop_loss_pct: 5,
    short_entry_conditions: [
      { indicator: "rsi14", operator: ">", value: 70 },
      { indicator: "close", operator: "<", value: "ema50" }
    ],
    short_entry_logic: "AND",
    short_take_profit_pct: 10,
    short_stop_loss_pct: 5
  };

  const response = await fetch(`${BASE_URL}/api/backtest`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config)
  });

  const result = await response.json();
  const backtestId = result.backtest_id;
  console.log(`回测任务ID: ${backtestId}`);

  // 2. 轮询状态
  while (true) {
    const statusResponse = await fetch(`${BASE_URL}/api/backtest/${backtestId}/status`);
    const status = await statusResponse.json();
    console.log(`状态: ${status.status}, 进度: ${status.progress}%`);

    if (status.status === "completed") {
      break;
    } else if (status.status === "failed") {
      console.error("回测失败");
      return;
    }

    await new Promise(resolve => setTimeout(resolve, 2000));
  }

  // 3. 获取结果
  const resultsResponse = await fetch(`${BASE_URL}/api/backtest/${backtestId}/results`);
  const results = await resultsResponse.json();

  // 显示结果
  const metrics = results.performance_metrics;
  console.log("\n=== 回测结果 ===");
  console.log(`总收益: ${metrics.total_return.toFixed(2)} USDT (${metrics.total_return_pct.toFixed(2)}%)`);
  console.log(`胜率: ${metrics.win_rate.toFixed(2)}%`);
  console.log(`最大回撤: ${metrics.max_drawdown_pct.toFixed(2)}%`);
  console.log(`夏普比率: ${metrics.sharpe_ratio.toFixed(2)}`);
  console.log(`总交易次数: ${metrics.total_trades}`);
}

runBacktest();
```

---

## 向后兼容性

系统完全支持旧版 API 字段，无需修改现有代码：

**旧版请求**（仍然支持）:
```json
{
  "strategy_name": "EMA金叉策略",
  "position_side": "long",
  "entry_conditions": [
    {"indicator": "ema7", "operator": ">", "value": "ema25"}
  ],
  "entry_logic": "AND",
  "exit_conditions": [
    {"indicator": "ema7", "operator": "<", "value": "ema25"}
  ],
  "exit_logic": "OR",
  "take_profit_pct": 10,
  "stop_loss_pct": 5
}
```

系统会自动转换为新版字段：
- `position_side: "long"` → `long_entry_conditions`
- `position_side: "short"` → `short_entry_conditions`
- `entry_conditions` → 对应方向的 `entry_conditions`
- `exit_conditions` → 对应方向的 `exit_conditions`
- `take_profit_pct` → 对应方向的 `take_profit_pct`
- `stop_loss_pct` → 对应方向的 `stop_loss_pct`

---

## 最佳实践

### 1. 参数验证
在提交请求前验证参数：
- 至少配置一个方向的开仓条件
- 日期范围合理（start_date < end_date）
- 持仓大小不超过初始资金
- 杠杆倍数合理（建议1-10倍）

### 2. 错误处理
始终检查响应状态码和错误信息：
```python
response = requests.post(url, json=config)
if response.status_code != 200:
    error = response.json()
    print(f"错误: {error['message']}")
    return
```

### 3. 异步处理
对于长时间运行的回测，使用异步轮询：
```python
import asyncio

async def poll_status(backtest_id):
    while True:
        status = await get_status(backtest_id)
        if status['status'] in ['completed', 'failed']:
            return status
        await asyncio.sleep(2)
```

### 4. 结果缓存
缓存回测结果避免重复请求：
```python
import functools

@functools.lru_cache(maxsize=100)
def get_backtest_results(backtest_id):
    response = requests.get(f"{BASE_URL}/api/backtest/{backtest_id}/results")
    return response.json()
```

---

## 更新日志

### v1.0.0 (2024-12-31)
- ✅ 新增双向交易策略 API
- ✅ 支持独立配置做多和做空条件
- ✅ 支持反向信号处理
- ✅ 支持做空盈亏计算
- ✅ 支持做空杠杆交易
- ✅ 保持向后兼容性

---

## 相关文档

- [双向交易策略完整指南](../DUAL_DIRECTION_TRADING_GUIDE.md)
- [双向交易策略快速参考](../DUAL_DIRECTION_QUICK_REFERENCE.md)
- [回测系统使用指南](../BACKTEST_USAGE_GUIDE.md)
- [需求文档](../.kiro/specs/dual-direction-trading-strategy/requirements.md)

---

**API 文档版本**: v1.0.0 | **更新日期**: 2024-12-31
