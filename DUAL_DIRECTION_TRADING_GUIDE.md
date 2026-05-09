# 双向交易策略使用指南

## 📋 目录
1. [功能概述](#功能概述)
2. [核心特性](#核心特性)
3. [快速开始](#快速开始)
4. [配置说明](#配置说明)
5. [策略示例](#策略示例)
6. [API 使用](#api-使用)
7. [迁移指南](#迁移指南)
8. [常见问题](#常见问题)

---

## 功能概述

双向交易策略功能扩展了现有回测系统，支持在同一策略中同时配置做多和做空的开仓条件。策略可以根据市场条件自动选择最优交易方向，实现更灵活的交易策略。

### 主要优势

- ✅ **灵活切换方向**: 根据市场条件自动在做多和做空之间切换
- ✅ **独立条件配置**: 为做多和做空分别配置开仓和平仓条件
- ✅ **单边持仓规则**: 确保同一时间只持有一个方向的仓位
- ✅ **杠杆支持**: 做多和做空均支持杠杆交易
- ✅ **向后兼容**: 完全兼容现有的单向策略配置
- ✅ **反向信号处理**: 自动处理反向信号触发的平仓和开仓

### 适用场景

1. **震荡市场**: 在区间震荡中高抛低吸
2. **趋势跟踪**: 跟随趋势方向，上涨做多，下跌做空
3. **均值回归**: 价格偏离均值时反向操作
4. **技术指标组合**: 利用多个指标的组合信号

---

## 核心特性

### 1. 双向开仓条件

可以分别为做多和做空配置独立的开仓条件：

- **做多开仓条件** (`long_entry_conditions`): 满足时开多仓
- **做空开仓条件** (`short_entry_conditions`): 满足时开空仓

每个方向的条件支持：
- 多个指标条件组合
- AND/OR 逻辑运算符
- 灵活的比较运算符（>、<、>=、<=、==）

### 2. 双向平仓条件

为做多和做空分别配置平仓条件：

- **做多平仓条件** (`long_exit_conditions`): 持有多仓时评估
- **做空平仓条件** (`short_exit_conditions`): 持有空仓时评估

平仓条件包括：
- 指标条件（如 RSI 超买/超卖）
- 止盈百分比
- 止损百分比

### 3. 单边持仓规则

系统确保同一时间只持有一个方向的仓位：

- 持有多仓时出现做空信号 → 先平多仓，再开空仓
- 持有空仓时出现做多信号 → 先平空仓，再开多仓
- 平仓原因记录为 `"reverse_signal"`

### 4. 做空盈亏计算

正确计算做空交易的盈亏：

- **盈利公式**: `(开仓价格 - 当前价格) × 持仓数量`
- **盈亏百分比**: `盈亏金额 / 开仓资金 × 100`
- 价格下跌时盈利为正，价格上涨时盈利为负

### 5. 杠杆支持

做多和做空均支持杠杆交易：

- **保证金计算**: `持仓价值 / 杠杆倍数`
- **持仓数量**: `持仓价值 / 开仓价格`
- 平仓时返还保证金并加上盈亏

---

## 快速开始

### 方法 1: 使用 Web UI

1. **启动系统**
   ```bash
   python3 -m uvicorn backend.backtest.api:app --host 127.0.0.1 --port 8001 --reload
   ```

2. **访问界面**
   
   打开浏览器访问: `http://127.0.0.1:8001/backtest.html`

3. **配置双向策略**

   - 在"做多开仓条件"区域添加做多信号
   - 在"做空开仓条件"区域添加做空信号
   - 分别配置做多和做空的平仓条件
   - 设置止盈止损百分比

4. **运行回测**
   
   点击"运行回测"按钮，查看结果

### 方法 2: 使用策略模板

1. 点击"策略模板"下拉菜单
2. 选择双向策略模板：
   - **双向RSI策略**: RSI<30做多，RSI>70做空
   - **双向均线策略**: 价格突破均线做多，跌破做空
   - **双向布林带策略**: 触及下轨做多，触及上轨做空
3. 模板会自动填充所有配置
4. 根据需要调整参数
5. 运行回测

---

## 配置说明

### 基本配置结构

```json
{
  "strategy_name": "策略名称",
  "timeframe": "1d",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "initial_capital": 10000,
  "position_size": 2000,
  "leverage": 5,
  
  "long_entry_conditions": [...],
  "long_entry_logic": "AND",
  "long_exit_conditions": [...],
  "long_exit_logic": "OR",
  "long_take_profit_pct": 10,
  "long_stop_loss_pct": 5,
  
  "short_entry_conditions": [...],
  "short_entry_logic": "AND",
  "short_exit_conditions": [...],
  "short_exit_logic": "OR",
  "short_take_profit_pct": 10,
  "short_stop_loss_pct": 5
}
```

### 参数说明

#### 基本参数

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `strategy_name` | string | 策略名称 | 必填 |
| `timeframe` | string | 时间周期 (1m/1w/1d/4h) | "1d" |
| `start_date` | string | 回测开始日期 (YYYY-MM-DD) | 必填 |
| `end_date` | string | 回测结束日期 (YYYY-MM-DD) | 必填 |
| `initial_capital` | float | 初始资金 (USDT) | 10000 |
| `position_size` | float | 持仓大小 (USDT) | 1000 |
| `leverage` | float | 杠杆倍数 | 1.0 |

#### 做多条件参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `long_entry_conditions` | array | 做多开仓条件列表 |
| `long_entry_logic` | string | 做多开仓逻辑 ("AND"/"OR") |
| `long_exit_conditions` | array | 做多平仓条件列表 |
| `long_exit_logic` | string | 做多平仓逻辑 ("AND"/"OR") |
| `long_take_profit_pct` | float | 做多止盈百分比 |
| `long_stop_loss_pct` | float | 做多止损百分比 |

#### 做空条件参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `short_entry_conditions` | array | 做空开仓条件列表 |
| `short_entry_logic` | string | 做空开仓逻辑 ("AND"/"OR") |
| `short_exit_conditions` | array | 做空平仓条件列表 |
| `short_exit_logic` | string | 做空平仓逻辑 ("AND"/"OR") |
| `short_take_profit_pct` | float | 做空止盈百分比 |
| `short_stop_loss_pct` | float | 做空止损百分比 |

### 条件对象结构

```json
{
  "indicator": "rsi14",
  "operator": "<",
  "value": 30,
  "timeframe": "1d"
}
```

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `indicator` | string | 指标名称 | "rsi14", "ema7", "close" |
| `operator` | string | 比较运算符 | ">", "<", ">=", "<=", "==" |
| `value` | float/string | 比较值或指标名 | 30, "ema25" |
| `timeframe` | string | 时间周期（可选） | "1d" |

### 可用指标

| 指标 | 说明 | 类型 |
|------|------|------|
| `ema7`, `ema12`, `ema25`, `ema50` | 指数移动平均线 | 趋势 |
| `rsi6`, `rsi14` | 相对强弱指标 | 动量 |
| `dif`, `dea`, `macd` | MACD 指标 | 动量 |
| `boll_up`, `boll_md`, `boll_dn` | 布林带 | 波动率 |
| `atr` | 平均真实波幅 | 波动率 |
| `close` | 收盘价 | 价格 |
| `volume` | 成交量 | 成交量 |

---

## 策略示例

### 示例 1: 双向 RSI 策略

**策略逻辑**:
- 做多: RSI < 30 且价格在 EMA50 上方
- 做空: RSI > 70 且价格在 EMA50 下方
- 止盈: 10%
- 止损: 5%

```json
{
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
}
```

### 示例 2: 双向均线策略

**策略逻辑**:
- 做多: 价格突破 EMA25 且 EMA7 > EMA25
- 做空: 价格跌破 EMA25 且 EMA7 < EMA25
- 止盈: 8%
- 止损: 4%

```json
{
  "strategy_name": "双向均线策略",
  "timeframe": "4h",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "initial_capital": 10000,
  "position_size": 1500,
  "leverage": 3,
  
  "long_entry_conditions": [
    {"indicator": "close", "operator": ">", "value": "ema25"},
    {"indicator": "ema7", "operator": ">", "value": "ema25"}
  ],
  "long_entry_logic": "AND",
  "long_exit_conditions": [
    {"indicator": "close", "operator": "<", "value": "ema25"}
  ],
  "long_exit_logic": "OR",
  "long_take_profit_pct": 8,
  "long_stop_loss_pct": 4,
  
  "short_entry_conditions": [
    {"indicator": "close", "operator": "<", "value": "ema25"},
    {"indicator": "ema7", "operator": "<", "value": "ema25"}
  ],
  "short_entry_logic": "AND",
  "short_exit_conditions": [
    {"indicator": "close", "operator": ">", "value": "ema25"}
  ],
  "short_exit_logic": "OR",
  "short_take_profit_pct": 8,
  "short_stop_loss_pct": 4
}
```

### 示例 3: 双向布林带策略

**策略逻辑**:
- 做多: 价格触及布林下轨且 RSI < 40
- 做空: 价格触及布林上轨且 RSI > 60
- 平仓: 价格回到布林中轨

```json
{
  "strategy_name": "双向布林带策略",
  "timeframe": "1d",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "initial_capital": 10000,
  "position_size": 2500,
  "leverage": 4,
  
  "long_entry_conditions": [
    {"indicator": "close", "operator": "<", "value": "boll_dn"},
    {"indicator": "rsi14", "operator": "<", "value": 40}
  ],
  "long_entry_logic": "AND",
  "long_exit_conditions": [
    {"indicator": "close", "operator": ">", "value": "boll_md"}
  ],
  "long_exit_logic": "OR",
  "long_take_profit_pct": 12,
  "long_stop_loss_pct": 6,
  
  "short_entry_conditions": [
    {"indicator": "close", "operator": ">", "value": "boll_up"},
    {"indicator": "rsi14", "operator": ">", "value": 60}
  ],
  "short_entry_logic": "AND",
  "short_exit_conditions": [
    {"indicator": "close", "operator": "<", "value": "boll_md"}
  ],
  "short_exit_logic": "OR",
  "short_take_profit_pct": 12,
  "short_stop_loss_pct": 6
}
```

### 示例 4: 纯做多策略（向后兼容）

**策略逻辑**:
- 仅配置做多条件
- 系统只执行做多交易

```json
{
  "strategy_name": "纯做多EMA策略",
  "timeframe": "1d",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "initial_capital": 10000,
  "position_size": 1000,
  "leverage": 2,
  
  "long_entry_conditions": [
    {"indicator": "ema7", "operator": ">", "value": "ema25"},
    {"indicator": "rsi14", "operator": "<", "value": 70}
  ],
  "long_entry_logic": "AND",
  "long_exit_conditions": [
    {"indicator": "ema7", "operator": "<", "value": "ema25"}
  ],
  "long_exit_logic": "OR",
  "long_take_profit_pct": 10,
  "long_stop_loss_pct": 5
}
```

---

## API 使用

### 1. 运行双向策略回测

**端点**: `POST /api/backtest`

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

### 2. 查询回测状态

**端点**: `GET /api/backtest/{backtest_id}/status`

```bash
curl "http://127.0.0.1:8001/api/backtest/bt_1234567890/status"
```

**响应**:

```json
{
  "backtest_id": "bt_1234567890",
  "status": "completed",
  "progress": 100
}
```

### 3. 获取回测结果

**端点**: `GET /api/backtest/{backtest_id}/results`

```bash
curl "http://127.0.0.1:8001/api/backtest/bt_1234567890/results"
```

**响应**:

```json
{
  "backtest_id": "bt_1234567890",
  "strategy_config": {...},
  "performance_metrics": {
    "total_return": 1250.50,
    "total_return_pct": 12.51,
    "win_rate": 65.5,
    "max_drawdown": -8.3,
    "sharpe_ratio": 1.85,
    "profit_factor": 2.1,
    "total_trades": 45,
    "winning_trades": 30,
    "losing_trades": 15
  },
  "trades": [
    {
      "trade_id": 1,
      "direction": "long",
      "entry_time": "2024-01-15T00:00:00",
      "entry_price": 45000,
      "exit_time": "2024-01-20T00:00:00",
      "exit_price": 47000,
      "profit_loss": 200,
      "profit_loss_pct": 10.0,
      "exit_reason": "take_profit"
    },
    {
      "trade_id": 2,
      "direction": "short",
      "entry_time": "2024-02-01T00:00:00",
      "entry_price": 48000,
      "exit_time": "2024-02-05T00:00:00",
      "exit_price": 46000,
      "profit_loss": 200,
      "profit_loss_pct": 10.0,
      "exit_reason": "take_profit"
    }
  ]
}
```

### 4. 获取策略模板

**端点**: `GET /api/strategy-templates`

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
      "config": {...}
    },
    {
      "id": "dual_ma_crossover",
      "name": "双向均线策略",
      "description": "价格突破EMA25做多，跌破EMA25做空",
      "config": {...}
    }
  ]
}
```

---

## 迁移指南

### 从单向策略迁移到双向策略

如果你有现有的单向策略配置，可以轻松迁移到双向策略：

#### 旧版配置（单向做多）

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

#### 新版配置（双向）

```json
{
  "strategy_name": "双向EMA策略",
  "long_entry_conditions": [
    {"indicator": "ema7", "operator": ">", "value": "ema25"}
  ],
  "long_entry_logic": "AND",
  "long_exit_conditions": [
    {"indicator": "ema7", "operator": "<", "value": "ema25"}
  ],
  "long_exit_logic": "OR",
  "long_take_profit_pct": 10,
  "long_stop_loss_pct": 5,
  
  "short_entry_conditions": [
    {"indicator": "ema7", "operator": "<", "value": "ema25"}
  ],
  "short_entry_logic": "AND",
  "short_exit_conditions": [
    {"indicator": "ema7", "operator": ">", "value": "ema25"}
  ],
  "short_exit_logic": "OR",
  "short_take_profit_pct": 10,
  "short_stop_loss_pct": 5
}
```

### 向后兼容性

系统完全支持旧版配置，无需修改现有策略：

- 旧版字段 `position_side` 会自动映射到对应的新版字段
- 旧版 `entry_conditions` 会根据 `position_side` 映射到 `long_entry_conditions` 或 `short_entry_conditions`
- 旧版 `exit_conditions` 会复制到对应方向的平仓条件
- 系统会在日志中记录兼容性警告，建议迁移到新版字段

---

## 常见问题

### Q1: 如何配置纯做多或纯做空策略？

**答**: 只需配置一个方向的开仓条件即可。

**纯做多**:
```json
{
  "long_entry_conditions": [...],
  "long_exit_conditions": [...]
}
```

**纯做空**:
```json
{
  "short_entry_conditions": [...],
  "short_exit_conditions": [...]
}
```

### Q2: 同时满足做多和做空信号时会怎样？

**答**: 系统会优先保持当前持仓方向。如果当前空仓，则不会开仓。

### Q3: 反向信号如何处理？

**答**: 当持有多仓时出现做空信号（或持有空仓时出现做多信号），系统会：
1. 先平掉当前仓位
2. 再开新方向的仓位
3. 平仓原因记录为 `"reverse_signal"`

### Q4: 做空盈亏如何计算？

**答**: 
- **盈亏金额** = (开仓价格 - 平仓价格) × 持仓数量
- **盈亏百分比** = 盈亏金额 / 开仓资金 × 100
- 价格下跌时盈利为正，价格上涨时盈利为负

**示例**:
- 开空仓: 50000 USDT
- 平空仓: 48000 USDT
- 盈利: (50000 - 48000) × 持仓数量 = 正值

### Q5: 杠杆如何影响做空交易？

**答**:
- **保证金** = 持仓价值 / 杠杆倍数
- **实际仓位** = 保证金 × 杠杆倍数
- **盈亏** = 按实际仓位计算

**示例**:
- 本金: 2000 USDT
- 杠杆: 5倍
- 实际仓位: 10000 USDT
- 保证金: 2000 USDT
- 盈亏: 按 10000 USDT 仓位计算

### Q6: 如何设置不同的止盈止损？

**答**: 为做多和做空分别设置：

```json
{
  "long_take_profit_pct": 10,
  "long_stop_loss_pct": 5,
  "short_take_profit_pct": 8,
  "short_stop_loss_pct": 4
}
```

### Q7: 可以只设置止盈止损，不设置指标条件吗？

**答**: 可以。平仓条件的指标条件是可选的：

```json
{
  "long_exit_conditions": [],
  "long_take_profit_pct": 10,
  "long_stop_loss_pct": 5
}
```

### Q8: 如何查看交易记录中的做多和做空交易？

**答**: 每笔交易记录都包含 `direction` 字段：
- `"long"`: 做多交易
- `"short"`: 做空交易

可以在 Web UI 的交易记录表格中按方向筛选。

### Q9: 旧版策略配置还能用吗？

**答**: 完全可以。系统会自动转换旧版配置到新版字段，无需修改现有策略。

### Q10: 如何优化双向策略？

**建议**:
1. **测试不同参数**: 调整 RSI 阈值、均线周期等
2. **添加过滤条件**: 使用多个指标组合，提高信号质量
3. **调整止盈止损**: 根据市场波动率调整止盈止损比例
4. **多周期测试**: 在不同时间周期上测试策略表现
5. **风险管理**: 合理设置杠杆和持仓大小

---

## 技术支持

- **API 文档**: http://127.0.0.1:8001/docs
- **需求文档**: `.kiro/specs/dual-direction-trading-strategy/requirements.md`
- **任务文档**: `.kiro/specs/dual-direction-trading-strategy/tasks.md`
- **日志文件**: `logs/backtest.log`

---

## 更新日志

### v1.0.0 (2024-12-31)
- ✅ 实现双向开仓条件配置
- ✅ 实现双向平仓条件配置
- ✅ 实现单边持仓规则
- ✅ 实现做空盈亏计算
- ✅ 实现做空杠杆支持
- ✅ 实现反向信号处理
- ✅ 实现向后兼容性
- ✅ 扩展 API 接口
- ✅ 更新前端 UI
- ✅ 添加策略模板

---

**祝你交易顺利！📈📉**
