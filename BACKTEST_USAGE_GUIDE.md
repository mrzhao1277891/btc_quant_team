# BTC 回测系统使用指南

## 📋 目录
1. [系统概述](#系统概述)
2. [环境准备](#环境准备)
3. [启动系统](#启动系统)
4. [使用 Web UI](#使用-web-ui)
5. [使用 API](#使用-api)
6. [策略配置示例](#策略配置示例)
7. [常见问题](#常见问题)

---

## 系统概述

BTC 回测系统是一个完整的量化交易回测平台，包含：

- ✅ **回测引擎**: 支持多种技术指标和策略条件
- ✅ **技术指标**: EMA、RSI、MACD、布林带、ATR
- ✅ **性能分析**: 总收益、胜率、最大回撤、夏普比率等
- ✅ **Web UI**: 可视化策略配置和结果展示
- ✅ **REST API**: 完整的 FastAPI 后端
- ✅ **策略管理**: 保存、加载、模板功能
- ✅ **并发支持**: 多个回测任务并行执行

---

## 环境准备

### 1. 检查 Python 环境

```bash
# 确保 Python 3.8+ 已安装
python3 --version

# 激活虚拟环境（如果有）
source venv/bin/activate  # macOS/Linux
```

### 2. 安装依赖

```bash
# 安装所有依赖
pip install -r requirements.txt

# 或者只安装核心依赖
pip install fastapi uvicorn pandas numpy mysql-connector-python pyyaml
```

### 3. 配置数据库

确保 MySQL 数据库已启动，并且配置正确：

```bash
# 检查数据库配置
cat config/backtest.yaml
```

配置文件示例（`config/backtest.yaml`）：
```yaml
database:
  host: localhost
  port: 3306
  user: root
  password: ""
  database: btc_assistant

backtest:
  initial_capital: 10000
  default_timeframe: "1d"
  max_concurrent_backtests: 10
```

### 4. 验证数据

确保 `klines` 表中有数据：

```sql
-- 检查数据
SELECT COUNT(*) FROM klines WHERE symbol = 'BTCUSDT';

-- 查看可用的时间周期
SELECT DISTINCT timeframe FROM klines;

-- 查看日期范围
SELECT 
    timeframe,
    MIN(FROM_UNIXTIME(timestamp/1000)) as start_date,
    MAX(FROM_UNIXTIME(timestamp/1000)) as end_date,
    COUNT(*) as count
FROM klines 
WHERE symbol = 'BTCUSDT'
GROUP BY timeframe;
```

---

## 启动系统

### 方法 1: 使用启动脚本（推荐）

创建启动脚本 `start_backtest.sh`:

```bash
#!/bin/bash
# 启动 BTC 回测系统

echo "🚀 启动 BTC 回测系统..."

# 检查依赖
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

# 启动 FastAPI 服务器
echo "📡 启动 API 服务器 (http://127.0.0.1:8001)..."
cd /Users/zhaojun/ideaprojects/btc_quant_team
python3 -m uvicorn backend.backtest.api:app --host 127.0.0.1 --port 8001 --reload &

API_PID=$!
echo "✅ API 服务器已启动 (PID: $API_PID)"

# 等待服务器启动
sleep 3

# 打开浏览器
echo "🌐 打开 Web UI..."
open http://127.0.0.1:8001/backtest.html

echo ""
echo "✅ 系统启动完成！"
echo ""
echo "📊 Web UI: http://127.0.0.1:8001/backtest.html"
echo "📖 API 文档: http://127.0.0.1:8001/docs"
echo "🛑 停止服务: kill $API_PID"
echo ""
```

使用：
```bash
chmod +x start_backtest.sh
./start_backtest.sh
```

### 方法 2: 手动启动

```bash
# 进入项目目录
cd /Users/zhaojun/ideaprojects/btc_quant_team

# 启动 FastAPI 服务器
python3 -m uvicorn backend.backtest.api:app --host 127.0.0.1 --port 8001 --reload

# 或者直接运行（如果有 main 函数）
python3 backend/backtest/api.py
```

### 方法 3: 使用 Python 脚本

创建 `run_backtest_server.py`:

```python
#!/usr/bin/env python3
"""启动 BTC 回测系统服务器"""

import uvicorn
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("🚀 启动 BTC 回测系统...")
    print("📊 Web UI: http://127.0.0.1:8001/backtest.html")
    print("📖 API 文档: http://127.0.0.1:8001/docs")
    print("🛑 停止服务: Ctrl+C")
    print()
    
    uvicorn.run(
        "backend.backtest.api:app",
        host="127.0.0.1",
        port=8001,
        reload=True,
        log_level="info"
    )
```

使用：
```bash
python3 run_backtest_server.py
```

---

## 使用 Web UI

### 1. 访问界面

打开浏览器访问：`http://127.0.0.1:8001/backtest.html`

### 2. 配置策略

#### 基本设置
- **策略名称**: 给策略起个名字（如 "EMA金叉策略"）
- **时间周期**: 选择 1m/1w/1d/4h
- **回测日期**: 选择开始和结束日期
- **初始资金**: 设置初始资金（默认 10000 USDT）

#### 开仓条件
点击 "添加开仓条件"，配置入场信号：

**示例 1: EMA 金叉**
```
条件 1: EMA7 > EMA25
条件 2: RSI14 < 70
逻辑: AND（两个条件都满足才开仓）
```

**示例 2: 布林带突破**
```
条件 1: close > boll_up
条件 2: volume > 1.5 * volume_avg
逻辑: AND
```

#### 平仓条件
点击 "添加平仓条件"，配置出场信号：

**示例 1: EMA 死叉**
```
条件 1: EMA7 < EMA25
逻辑: OR（任一条件满足就平仓）
```

**示例 2: RSI 超买**
```
条件 1: RSI14 > 70
逻辑: OR
```

#### 持仓设置
- **方向**: 做多（long）或做空（short）
- **持仓大小**: 
  - 固定金额：如 1000 USDT
  - 百分比：如 10%（使用可用资金的 10%）

#### 止盈止损
- **止盈**: 
  - 绝对金额：如 +100 USDT
  - 百分比：如 +10%
- **止损**: 
  - 绝对金额：如 -50 USDT
  - 百分比：如 -5%

### 3. 运行回测

1. 点击 "运行回测" 按钮
2. 等待回测完成（通常几秒钟）
3. 查看结果

### 4. 查看结果

回测完成后，界面会显示：

#### 性能指标卡片
- **总收益**: 绝对收益和百分比
- **胜率**: 盈利交易占比
- **最大回撤**: 最大峰谷跌幅
- **夏普比率**: 风险调整后收益
- **盈亏因子**: 总盈利/总亏损
- **交易次数**: 总交易、盈利、亏损次数

#### 权益曲线图
显示资金随时间的变化

#### 回撤图
显示回撤百分比随时间的变化

#### 交易记录表格
- 可排序（点击列标题）
- 可筛选（按方向、盈亏）
- 显示每笔交易的详细信息

### 5. 导出结果

- **导出 CSV**: 导出交易记录到 CSV 文件
- **导出 JSON**: 导出性能指标到 JSON 文件
- **生成报告**: 生成完整的 HTML/PDF 报告

### 6. 保存策略

1. 点击 "保存策略" 按钮
2. 输入策略名称
3. 策略会保存到数据库
4. 下次可以从 "加载策略" 下拉菜单中选择

### 7. 使用模板

点击 "策略模板" 下拉菜单，选择预定义模板：

- **EMA Golden Cross**: EMA 金叉策略
- **Bollinger Breakout**: 布林带突破策略

选择后会自动填充表单。

---

## 使用 API

### API 文档

访问 `http://127.0.0.1:8001/docs` 查看完整的 API 文档（Swagger UI）

### 主要端点

#### 1. 运行回测

```bash
POST /api/backtest
```

请求示例：
```bash
curl -X POST "http://127.0.0.1:8001/api/backtest" \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_name": "EMA金叉策略",
    "timeframe": "1d",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "initial_capital": 10000,
    "entry_conditions": [
      {
        "indicator": "ema7",
        "operator": ">",
        "value": "ema25"
      },
      {
        "indicator": "rsi14",
        "operator": "<",
        "value": 70
      }
    ],
    "entry_logic": "AND",
    "exit_conditions": [
      {
        "indicator": "ema7",
        "operator": "<",
        "value": "ema25"
      }
    ],
    "exit_logic": "OR",
    "position_side": "long",
    "position_size": 1000,
    "position_size_type": "fixed",
    "take_profit_pct": 10,
    "stop_loss_pct": 5
  }'
```

响应：
```json
{
  "backtest_id": "bt_1234567890",
  "status": "queued",
  "message": "回测任务已提交"
}
```

#### 2. 查询回测状态

```bash
GET /api/backtest/{backtest_id}/status
```

```bash
curl "http://127.0.0.1:8001/api/backtest/bt_1234567890/status"
```

响应：
```json
{
  "backtest_id": "bt_1234567890",
  "status": "completed",
  "progress": 100
}
```

#### 3. 获取回测结果

```bash
GET /api/backtest/{backtest_id}/results
```

```bash
curl "http://127.0.0.1:8001/api/backtest/bt_1234567890/results"
```

响应：
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
  "trades": [...]
}
```

#### 4. 保存策略

```bash
POST /api/strategies
```

```bash
curl -X POST "http://127.0.0.1:8001/api/strategies" \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_name": "我的策略",
    "strategy_config": {...}
  }'
```

#### 5. 获取所有策略

```bash
GET /api/strategies
```

```bash
curl "http://127.0.0.1:8001/api/strategies"
```

#### 6. 获取策略模板

```bash
GET /api/strategy-templates
```

```bash
curl "http://127.0.0.1:8001/api/strategy-templates"
```

#### 7. 获取可用指标

```bash
GET /api/indicators
```

```bash
curl "http://127.0.0.1:8001/api/indicators"
```

#### 8. 获取数据范围

```bash
GET /api/data-range?timeframe=1d
```

```bash
curl "http://127.0.0.1:8001/api/data-range?timeframe=1d"
```

---

## 策略配置示例

### 示例 1: EMA 金叉策略

```json
{
  "strategy_name": "EMA金叉策略",
  "timeframe": "1d",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "initial_capital": 10000,
  "entry_conditions": [
    {"indicator": "ema7", "operator": ">", "value": "ema25"},
    {"indicator": "rsi14", "operator": "<", "value": 70}
  ],
  "entry_logic": "AND",
  "exit_conditions": [
    {"indicator": "ema7", "operator": "<", "value": "ema25"}
  ],
  "exit_logic": "OR",
  "position_side": "long",
  "position_size": 10,
  "position_size_type": "percent",
  "take_profit_pct": 10,
  "stop_loss_pct": 5
}
```

### 示例 2: 布林带突破策略

```json
{
  "strategy_name": "布林带突破",
  "timeframe": "4h",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "initial_capital": 10000,
  "entry_conditions": [
    {"indicator": "close", "operator": ">", "value": "boll_up"},
    {"indicator": "volume", "operator": ">", "value": 1000000}
  ],
  "entry_logic": "AND",
  "exit_conditions": [
    {"indicator": "close", "operator": "<", "value": "boll_md"}
  ],
  "exit_logic": "OR",
  "position_side": "long",
  "position_size": 1000,
  "position_size_type": "fixed",
  "take_profit_pct": 8,
  "stop_loss_pct": 4
}
```

### 示例 3: RSI 超卖反弹策略

```json
{
  "strategy_name": "RSI超卖反弹",
  "timeframe": "1d",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "initial_capital": 10000,
  "entry_conditions": [
    {"indicator": "rsi14", "operator": "<", "value": 30},
    {"indicator": "close", "operator": ">", "value": "ema50"}
  ],
  "entry_logic": "AND",
  "exit_conditions": [
    {"indicator": "rsi14", "operator": ">", "value": 70}
  ],
  "exit_logic": "OR",
  "position_side": "long",
  "position_size": 15,
  "position_size_type": "percent",
  "take_profit_pct": 12,
  "stop_loss_pct": 6
}
```

### 示例 4: MACD 趋势跟踪策略

```json
{
  "strategy_name": "MACD趋势跟踪",
  "timeframe": "1d",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "initial_capital": 10000,
  "entry_conditions": [
    {"indicator": "dif", "operator": ">", "value": "dea"},
    {"indicator": "macd", "operator": ">", "value": 0}
  ],
  "entry_logic": "AND",
  "exit_conditions": [
    {"indicator": "dif", "operator": "<", "value": "dea"}
  ],
  "exit_logic": "OR",
  "position_side": "long",
  "position_size": 2000,
  "position_size_type": "fixed",
  "take_profit_pct": 15,
  "stop_loss_pct": 7
}
```

---

## 常见问题

### Q1: 服务器启动失败

**问题**: `ModuleNotFoundError: No module named 'backend'`

**解决**:
```bash
# 确保在项目根目录
cd /Users/zhaojun/ideaprojects/btc_quant_team

# 设置 PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 重新启动
python3 -m uvicorn backend.backtest.api:app --host 127.0.0.1 --port 8001
```

### Q2: 数据库连接失败

**问题**: `Can't connect to MySQL server`

**解决**:
```bash
# 检查 MySQL 是否运行
mysql.server status

# 启动 MySQL
mysql.server start

# 检查配置
cat config/backtest.yaml
```

### Q3: 回测没有交易

**可能原因**:
1. 开仓条件太严格，没有触发信号
2. 数据范围内没有满足条件的时机
3. 资金不足（检查 position_size 设置）

**解决**:
- 放宽开仓条件
- 扩大回测日期范围
- 减小持仓大小

### Q4: 如何查看日志

```bash
# 查看回测日志
tail -f logs/backtest.log

# 查看 API 日志
# 日志会直接输出到终端
```

### Q5: 如何停止服务器

```bash
# 方法 1: 在终端按 Ctrl+C

# 方法 2: 查找并杀死进程
ps aux | grep uvicorn
kill <PID>

# 方法 3: 使用 pkill
pkill -f "uvicorn.*backtest"
```

### Q6: 端口被占用

**问题**: `Address already in use`

**解决**:
```bash
# 查找占用端口的进程
lsof -i :8001

# 杀死进程
kill -9 <PID>

# 或者使用其他端口
python3 -m uvicorn backend.backtest.api:app --host 127.0.0.1 --port 8002
```

### Q7: 如何批量回测多个策略

创建 Python 脚本：

```python
import requests
import time

strategies = [
    {...},  # 策略 1
    {...},  # 策略 2
    {...},  # 策略 3
]

results = []
for strategy in strategies:
    # 提交回测
    response = requests.post(
        "http://127.0.0.1:8001/api/backtest",
        json=strategy
    )
    backtest_id = response.json()["backtest_id"]
    
    # 等待完成
    while True:
        status = requests.get(
            f"http://127.0.0.1:8001/api/backtest/{backtest_id}/status"
        ).json()
        
        if status["status"] == "completed":
            break
        time.sleep(1)
    
    # 获取结果
    result = requests.get(
        f"http://127.0.0.1:8001/api/backtest/{backtest_id}/results"
    ).json()
    results.append(result)

# 比较结果
for result in results:
    print(f"{result['strategy_config']['strategy_name']}: "
          f"{result['performance_metrics']['total_return_pct']:.2f}%")
```

---

## 下一步

1. **优化策略**: 根据回测结果调整参数
2. **参数扫描**: 测试不同的参数组合
3. **多周期分析**: 在不同时间周期上测试策略
4. **风险管理**: 添加更复杂的止盈止损逻辑
5. **实盘准备**: 将表现好的策略应用到实盘

---

## 技术支持

- **文档**: 查看 `.kiro/specs/btc-backtest-system/` 目录
- **API 文档**: http://127.0.0.1:8001/docs
- **日志**: `logs/backtest.log`

---

**祝你回测顺利！📈**
