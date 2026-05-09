# 双向交易策略快速参考

## 🚀 快速开始

### 1. 启动系统
```bash
python3 -m uvicorn backend.backtest.api:app --host 127.0.0.1 --port 8001 --reload
```

### 2. 访问界面
```
http://127.0.0.1:8001/backtest.html
```

### 3. 选择策略模板
- 双向RSI策略
- 双向均线策略
- 双向布林带策略

---

## 📋 配置字段对照表

### 新版字段（双向策略）

| 字段 | 说明 | 示例 |
|------|------|------|
| `long_entry_conditions` | 做多开仓条件 | `[{"indicator": "rsi14", "operator": "<", "value": 30}]` |
| `long_entry_logic` | 做多开仓逻辑 | `"AND"` 或 `"OR"` |
| `long_exit_conditions` | 做多平仓条件 | `[{"indicator": "rsi14", "operator": ">", "value": 70}]` |
| `long_exit_logic` | 做多平仓逻辑 | `"AND"` 或 `"OR"` |
| `long_take_profit_pct` | 做多止盈百分比 | `10` (表示10%) |
| `long_stop_loss_pct` | 做多止损百分比 | `5` (表示5%) |
| `short_entry_conditions` | 做空开仓条件 | `[{"indicator": "rsi14", "operator": ">", "value": 70}]` |
| `short_entry_logic` | 做空开仓逻辑 | `"AND"` 或 `"OR"` |
| `short_exit_conditions` | 做空平仓条件 | `[{"indicator": "rsi14", "operator": "<", "value": 30}]` |
| `short_exit_logic` | 做空平仓逻辑 | `"AND"` 或 `"OR"` |
| `short_take_profit_pct` | 做空止盈百分比 | `10` (表示10%) |
| `short_stop_loss_pct` | 做空止损百分比 | `5` (表示5%) |

### 旧版字段（单向策略，仍然支持）

| 字段 | 说明 | 映射到新版 |
|------|------|-----------|
| `position_side` | 持仓方向 | `"long"` → `long_entry_conditions`<br>`"short"` → `short_entry_conditions` |
| `entry_conditions` | 开仓条件 | 根据 `position_side` 映射 |
| `exit_conditions` | 平仓条件 | 根据 `position_side` 映射 |
| `take_profit_pct` | 止盈百分比 | 映射到对应方向 |
| `stop_loss_pct` | 止损百分比 | 映射到对应方向 |

---

## 🎯 常用指标

| 指标 | 名称 | 用途 | 常用阈值 |
|------|------|------|----------|
| `rsi14` | RSI(14) | 超买超卖 | 做多: <30, 做空: >70 |
| `rsi6` | RSI(6) | 快速RSI | 做多: <25, 做空: >75 |
| `ema7` | EMA(7) | 短期趋势 | 与其他均线比较 |
| `ema25` | EMA(25) | 中期趋势 | 与其他均线比较 |
| `ema50` | EMA(50) | 长期趋势 | 价格支撑/阻力 |
| `boll_up` | 布林上轨 | 超买区域 | 价格突破做空 |
| `boll_dn` | 布林下轨 | 超卖区域 | 价格突破做多 |
| `boll_md` | 布林中轨 | 均值回归 | 平仓参考 |
| `dif` | MACD DIF | 趋势强度 | 与DEA比较 |
| `dea` | MACD DEA | 信号线 | 与DIF比较 |
| `macd` | MACD柱 | 动量 | 正负转换 |
| `close` | 收盘价 | 价格 | 与均线比较 |
| `volume` | 成交量 | 确认信号 | 放量突破 |

---

## 🔧 运算符

| 运算符 | 说明 | 示例 |
|--------|------|------|
| `>` | 大于 | `{"indicator": "rsi14", "operator": ">", "value": 70}` |
| `<` | 小于 | `{"indicator": "rsi14", "operator": "<", "value": 30}` |
| `>=` | 大于等于 | `{"indicator": "close", "operator": ">=", "value": "ema50"}` |
| `<=` | 小于等于 | `{"indicator": "close", "operator": "<=", "value": "boll_dn"}` |
| `==` | 等于 | `{"indicator": "macd", "operator": "==", "value": 0}` |

---

## 📊 策略模板速查

### 1. 双向RSI策略
```json
{
  "long_entry_conditions": [
    {"indicator": "rsi14", "operator": "<", "value": 30},
    {"indicator": "close", "operator": ">", "value": "ema50"}
  ],
  "long_entry_logic": "AND",
  "short_entry_conditions": [
    {"indicator": "rsi14", "operator": ">", "value": 70},
    {"indicator": "close", "operator": "<", "value": "ema50"}
  ],
  "short_entry_logic": "AND"
}
```

### 2. 双向均线策略
```json
{
  "long_entry_conditions": [
    {"indicator": "ema7", "operator": ">", "value": "ema25"}
  ],
  "short_entry_conditions": [
    {"indicator": "ema7", "operator": "<", "value": "ema25"}
  ]
}
```

### 3. 双向布林带策略
```json
{
  "long_entry_conditions": [
    {"indicator": "close", "operator": "<", "value": "boll_dn"}
  ],
  "short_entry_conditions": [
    {"indicator": "close", "operator": ">", "value": "boll_up"}
  ]
}
```

---

## 💡 最佳实践

### 开仓条件设计
- ✅ 使用多个指标组合，提高信号质量
- ✅ 添加趋势过滤（如价格与均线关系）
- ✅ 考虑成交量确认
- ❌ 避免条件过于复杂
- ❌ 避免相互矛盾的条件

### 平仓条件设计
- ✅ 设置合理的止盈止损
- ✅ 使用反向信号作为平仓条件
- ✅ 考虑时间止损（持仓时长）
- ❌ 避免止损过小（频繁止损）
- ❌ 避免止盈过大（错失利润）

### 参数优化
- ✅ 从简单策略开始
- ✅ 逐步添加过滤条件
- ✅ 在多个时间周期测试
- ✅ 考虑不同市场环境
- ❌ 避免过度拟合历史数据

### 风险管理
- ✅ 合理设置杠杆（建议1-5倍）
- ✅ 控制单笔持仓大小（建议10-20%）
- ✅ 设置最大回撤限制
- ✅ 分散投资，不要全仓一个策略
- ❌ 避免高杠杆（超过10倍）

---

## 🔍 调试技巧

### 1. 检查信号触发
```python
# 查看开仓信号
print(f"做多信号: {long_signal}")
print(f"做空信号: {short_signal}")
```

### 2. 查看交易记录
```python
# 筛选做多交易
long_trades = [t for t in trades if t['direction'] == 'long']

# 筛选做空交易
short_trades = [t for t in trades if t['direction'] == 'short']
```

### 3. 分析平仓原因
```python
# 统计平仓原因
exit_reasons = {}
for trade in trades:
    reason = trade['exit_reason']
    exit_reasons[reason] = exit_reasons.get(reason, 0) + 1
```

### 4. 检查反向信号
```python
# 查找反向信号触发的交易
reverse_trades = [t for t in trades if t['exit_reason'] == 'reverse_signal']
```

---

## 📈 性能指标解读

| 指标 | 说明 | 优秀 | 良好 | 一般 | 较差 |
|------|------|------|------|------|------|
| 总收益率 | 总盈利百分比 | >50% | 20-50% | 5-20% | <5% |
| 胜率 | 盈利交易占比 | >60% | 50-60% | 40-50% | <40% |
| 盈亏比 | 平均盈利/平均亏损 | >2.0 | 1.5-2.0 | 1.0-1.5 | <1.0 |
| 最大回撤 | 最大峰谷跌幅 | <10% | 10-20% | 20-30% | >30% |
| 夏普比率 | 风险调整后收益 | >2.0 | 1.0-2.0 | 0.5-1.0 | <0.5 |
| 交易次数 | 总交易数 | 20-50 | 10-20 | 5-10 | <5 |

---

## 🆘 常见问题速查

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 没有交易 | 条件太严格 | 放宽开仓条件 |
| 交易太多 | 条件太宽松 | 添加过滤条件 |
| 胜率低 | 信号质量差 | 优化指标组合 |
| 回撤大 | 止损不合理 | 调整止损百分比 |
| 盈利小 | 止盈太早 | 调整止盈百分比 |
| 资金不足 | 持仓太大 | 减小持仓大小 |

---

## 📞 获取帮助

- **详细文档**: [DUAL_DIRECTION_TRADING_GUIDE.md](DUAL_DIRECTION_TRADING_GUIDE.md)
- **API 文档**: http://127.0.0.1:8001/docs
- **需求文档**: `.kiro/specs/dual-direction-trading-strategy/requirements.md`

---

**快速参考卡 v1.0** | **更新: 2024-12-31**
