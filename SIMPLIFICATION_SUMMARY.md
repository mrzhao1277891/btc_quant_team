# 系统简化总结

## 修改内容

根据用户反馈，系统已简化，移除了杠杆和持仓类型选择功能。

### 修改前的问题
1. **类型选择混乱**：前端发送"fixed"/"percent"，但后端期望"amount"/"percentage"
2. **杠杆功能复杂**：对于简单回测场景，杠杆功能增加了理解难度
3. **固定金额不工作**：由于类型值不匹配，选择固定金额时没有交易

### 修改后的简化
1. ✅ **移除类型选择**：持仓大小固定为"固定金额(USDT)"
2. ✅ **移除杠杆功能**：固定为1倍（现货交易）
3. ✅ **统一参数**：后端统一使用"amount"类型

## 修改的文件

### 1. `web/backtest.html`
**修改前：**
```html
<div class="form-row">
    <div class="form-group">
        <label>持仓大小</label>
        <input type="number" id="positionSize" value="10">
    </div>
    <div class="form-group">
        <label>类型</label>
        <select id="positionSizeType">
            <option value="percent">百分比 (%)</option>
            <option value="fixed">固定金额 (USDT)</option>
        </select>
    </div>
</div>
<div class="form-group">
    <label>杠杆倍数</label>
    <input type="number" id="leverage" value="1">
</div>
```

**修改后：**
```html
<div class="form-group">
    <label>持仓大小 (USDT)</label>
    <input type="number" id="positionSize" value="1000" min="1" step="1">
    <small class="form-hint">💡 每次开仓时使用的固定金额（USDT）</small>
</div>
```

### 2. `web/backtest.js`
**修改前：**
```javascript
position_size: parseFloat(document.getElementById('positionSize').value),
position_size_type: document.getElementById('positionSizeType').value,
leverage: parseFloat(document.getElementById('leverage').value) || 1.0,
```

**修改后：**
```javascript
position_size: parseFloat(document.getElementById('positionSize').value),
position_size_type: "fixed",  // 固定为固定金额类型
leverage: 1.0,  // 固定为1倍（现货）
```

### 3. `backend/backtest/api.py`
**修改前：**
```python
"position_size_type": request.position_size_type,
"position_size_value": request.position_size if request.position_size_type == "fixed" else request.position_size / 100,
"leverage": request.leverage,
```

**修改后：**
```python
"position_size_type": "amount",  # 固定使用amount类型
"position_size_value": request.position_size,  # 直接使用固定金额
"leverage": 1.0,  # 固定为1倍（现货）
```

### 4. 策略模板更新
所有模板的`position_size`改为固定金额（USDT），移除`position_size_type`字段：
- EMA金叉：1000 USDT
- 布林带突破：1000 USDT
- RSI超卖反弹：1500 USDT

## 使用说明

### 简化后的参数

现在只需要设置3个核心参数：

1. **初始资金**：你账户的总资金（例如：10000 USDT）
2. **持仓大小**：每次开仓使用的固定金额（例如：1000 USDT）
3. **持仓方向**：做多或做空

### 示例配置

```
初始资金：10000 USDT
持仓大小：1000 USDT
持仓方向：做多
```

**含义：**
- 你有 10000 USDT 本金
- 每次开仓用 1000 USDT
- 最多可以开 10 次仓位（如果不考虑盈亏）
- 不使用杠杆（现货交易）

### 计算逻辑

```
开仓时：
- 扣除资金：1000 USDT
- 剩余资金：10000 - 1000 = 9000 USDT
- 持仓数量：1000 / BTC价格

平仓时：
- 返还资金：1000 + 盈亏
- 盈亏 = (平仓价 - 开仓价) × 持仓数量
```

## 优势

1. ✅ **简单直观**：不需要理解杠杆和百分比的概念
2. ✅ **固定风险**：每次交易的风险是固定的
3. ✅ **易于计算**：直接用USDT金额，容易理解
4. ✅ **避免混淆**：消除了类型选择带来的困惑

## 测试验证

修改后的系统已经过测试，确保：
- ✅ 固定金额正常工作
- ✅ 交易记录正确显示
- ✅ 盈亏计算准确
- ✅ 模板加载正常

## 注意事项

1. **资金不足时会跳过交易**
   - 如果剩余资金 < 持仓大小，系统会跳过这次开仓信号
   - 建议：持仓大小设置为初始资金的 10-20%

2. **建议配置**
   - 初始资金 10000 USDT → 持仓大小 1000-2000 USDT
   - 初始资金 5000 USDT → 持仓大小 500-1000 USDT
   - 初始资金 2000 USDT → 持仓大小 200-400 USDT

3. **如果需要杠杆功能**
   - 杠杆功能的代码仍然保留在系统中
   - 如果将来需要，可以轻松恢复
   - 相关代码在 `models.py` 和 `engine.py` 中
