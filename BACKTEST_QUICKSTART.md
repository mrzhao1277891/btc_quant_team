# 🚀 BTC 回测系统 - 快速开始

## 一键启动

### 方法 1: 使用 Shell 脚本（推荐）

```bash
./start_backtest.sh
```

### 方法 2: 使用 Python 脚本

```bash
python3 run_backtest_server.py
```

### 方法 3: 手动启动

```bash
python3 -m uvicorn backend.backtest.api:app --host 127.0.0.1 --port 8001 --reload
```

## 访问系统

启动成功后，浏览器会自动打开，或手动访问：

- **Web UI**: http://127.0.0.1:8001/backtest.html
- **API 文档**: http://127.0.0.1:8001/docs

## 停止服务

### 方法 1: 使用停止脚本

```bash
./stop_backtest.sh
```

### 方法 2: 按 Ctrl+C

在运行服务器的终端按 `Ctrl+C`

## 快速测试

### 1. 使用 Web UI

1. 打开 http://127.0.0.1:8001/backtest.html
2. 选择策略模板 "EMA Golden Cross"
3. 设置回测日期范围
4. 点击 "运行回测"
5. 查看结果

### 2. 使用 API

```bash
# 测试 API 是否正常
curl http://127.0.0.1:8001/api/indicators

# 获取数据范围
curl http://127.0.0.1:8001/api/data-range?timeframe=1d

# 运行简单回测
curl -X POST "http://127.0.0.1:8001/api/backtest" \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_name": "测试策略",
    "timeframe": "1d",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "initial_capital": 10000,
    "entry_conditions": [
      {"indicator": "ema7", "operator": ">", "value": "ema25"}
    ],
    "entry_logic": "AND",
    "exit_conditions": [
      {"indicator": "ema7", "operator": "<", "value": "ema25"}
    ],
    "exit_logic": "OR",
    "position_side": "long",
    "position_size": 1000,
    "position_size_type": "fixed"
  }'
```

## 常见问题

### 问题 1: 端口被占用

```bash
# 查看占用端口的进程
lsof -i :8001

# 杀死进程
kill -9 <PID>
```

### 问题 2: 数据库连接失败

```bash
# 检查 MySQL 状态
mysql.server status

# 启动 MySQL
mysql.server start
```

### 问题 3: 模块未找到

```bash
# 安装依赖
pip install -r requirements.txt

# 或安装核心依赖
pip install fastapi uvicorn pandas numpy mysql-connector-python pyyaml
```

## 完整文档

查看完整使用指南：[BACKTEST_USAGE_GUIDE.md](./BACKTEST_USAGE_GUIDE.md)

## 系统架构

```
btc_quant_team/
├── backend/
│   ├── backtest/
│   │   ├── api.py          # FastAPI 应用
│   │   ├── engine.py       # 回测引擎
│   │   ├── metrics.py      # 性能指标
│   │   └── models.py       # 数据模型
│   ├── database.py         # 数据库连接
│   └── indicators.py       # 技术指标
├── web/
│   ├── backtest.html       # Web UI
│   ├── backtest.css        # 样式
│   └── backtest.js         # 前端逻辑
├── config/
│   └── backtest.yaml       # 配置文件
└── logs/
    └── backtest.log        # 日志文件
```

## 下一步

1. ✅ 启动系统
2. ✅ 运行测试回测
3. 📊 创建自己的策略
4. 🔧 优化参数
5. 📈 分析结果

---

**祝你回测顺利！** 🎉
