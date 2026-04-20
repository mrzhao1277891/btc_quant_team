# BTC监控Skill

## 🎯 描述
专业的BTC价格监控和报警Skill，支持多阈值监控、实时报警、状态报告。

## 📋 功能特性
- ✅ 多价格阈值监控 (支持高低点)
- ✅ 实时价格获取 (Binance API)
- ✅ 多种通知方式 (Telegram、日志、声音)
- ✅ 状态监控和报告
- ✅ 可配置监控间隔
- ✅ 异常处理和重试机制

## 🚀 何时使用
- 当需要监控BTC价格突破关键位置时
- 当设置价格警报进行交易决策时
- 当需要实时了解市场动态时
- 作为自动化交易系统的一部分

## 📦 安装
```bash
# 方法1: 符号链接 (推荐开发)
ln -s ~/btc_quant_team/skills/btc-monitor ~/.openclaw/skills/

# 方法2: 通过OpenClaw CLI
openclaw skill install ~/btc_quant_team/skills/btc-monitor

# 方法3: 从Skill仓库安装
openclaw skill install btc-monitor
```

## 💻 使用

### 基本用法
```bash
# 启动监控 (默认: 低69000, 高73000, 间隔15分钟)
openclaw skill run btc-monitor

# 自定义阈值
openclaw skill run btc-monitor --low 70000 --high 75000

# 快速监控 (5分钟间隔)
openclaw skill run btc-monitor --low 70000 --high 75000 --interval 5

# 仅监控一次
openclaw skill run btc-monitor --once
```

### 监控管理
```bash
# 查看监控状态
openclaw skill run btc-monitor --status

# 停止监控
openclaw skill run btc-monitor --stop

# 重启监控
openclaw skill run btc-monitor --restart

# 查看监控日志
openclaw skill run btc-monitor --logs
```

### 高级功能
```bash
# 多阈值监控
openclaw skill run btc-monitor --thresholds "69000:73000,70000:74000"

# 自定义通知渠道
openclaw skill run btc-monitor --notify telegram,email,log

# 设置监控时间段
openclaw skill run btc-monitor --start "09:00" --end "18:00"

# 静默模式 (仅日志)
openclaw skill run btc-monitor --silent
```

## ⚙️ 参数说明

### 监控参数
| 参数 | 缩写 | 类型 | 默认值 | 描述 |
|------|------|------|--------|------|
| `--low` | `-l` | float | 69000 | 低阈值价格 |
| `--high` | `-h` | float | 73000 | 高阈值价格 |
| `--interval` | `-i` | int | 15 | 监控间隔(分钟) |
| `--symbol` | `-s` | string | BTCUSDT | 交易对 |
| `--timeframe` | `-t` | string | 1m | 时间框架 |

### 控制参数
| 参数 | 类型 | 描述 |
|------|------|------|
| `--once` | flag | 仅检查一次 |
| `--status` | flag | 查看监控状态 |
| `--stop` | flag | 停止监控 |
| `--restart` | flag | 重启监控 |
| `--logs` | flag | 查看监控日志 |
| `--test` | flag | 测试模式 |

### 通知参数
| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `--notify` | string | telegram | 通知方式 |
| `--telegram-chat` | string | (配置) | Telegram聊天ID |
| `--silent` | flag | false | 静默模式 |

## 📊 输出示例

### 监控启动输出
```json
{
  "status": "started",
  "monitor_id": "monitor_20260419_0845",
  "config": {
    "low": 70000,
    "high": 75000,
    "interval": 5,
    "symbol": "BTCUSDT",
    "start_time": "2026-04-19T08:45:00"
  },
  "message": "BTC监控已启动，间隔5分钟"
}
```

### 价格报警输出
```json
{
  "status": "alert",
  "type": "price_break_high",
  "price": 75123.45,
  "threshold": 75000,
  "difference": 123.45,
  "percentage": 0.16,
  "timestamp": "2026-04-19T09:15:00",
  "message": "⚠️ BTC突破高点! 当前: $75,123.45 (阈值: $75,000)"
}
```

### 状态报告输出
```json
{
  "status": "running",
  "monitor_id": "monitor_20260419_0845",
  "uptime": "2小时15分钟",
  "checks": 27,
  "alerts": 1,
  "last_check": "2026-04-19T10:45:00",
  "last_price": 74890.12,
  "next_check": "2026-04-19T10:50:00"
}
```

## 🔧 配置

### 环境变量
```bash
# Binance API (可选)
export BINANCE_API_KEY="your_api_key"
export BINANCE_API_SECRET="your_api_secret"

# Telegram配置
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"

# 监控配置
export BTC_MONITOR_LOW="69000"
export BTC_MONITOR_HIGH="73000"
export BTC_MONITOR_INTERVAL="15"
```

### 配置文件
创建 `~/.btc_monitor/config.yaml`:
```yaml
monitor:
  default_low: 69000
  default_high: 73000
  default_interval: 15
  max_interval: 60
  min_interval: 1

notifications:
  telegram:
    enabled: true
    bot_token: ${TELEGRAM_BOT_TOKEN}
    chat_id: ${TELEGRAM_CHAT_ID}
  email:
    enabled: false
    smtp_server: smtp.gmail.com
    smtp_port: 587

logging:
  level: INFO
  file: ~/.btc_monitor/monitor.log
  max_size_mb: 10
  backup_count: 5
```

## 🔗 依赖

### Python包
```txt
requests>=2.28.0
pyyaml>=6.0
python-telegram-bot>=20.0
schedule>=1.2.0
```

### 系统依赖
- Python 3.9+
- 网络连接
- 可选的: Telegram Bot配置

### 其他Skill依赖
- `data-quality`: 数据质量检查 (可选)
- `market-analysis`: 市场分析 (可选)

## 🐛 故障排除

### 常见问题
1. **价格获取失败**
   - 检查网络连接
   - 验证Binance API状态
   - 查看错误日志

2. **通知发送失败**
   - 检查Telegram Bot配置
   - 验证聊天ID权限
   - 查看通知日志

3. **监控意外停止**
   - 检查系统资源
   - 查看监控日志
   - 验证配置文件

### 调试模式
```bash
# 启用详细日志
openclaw skill run btc-monitor --debug

# 查看详细日志
tail -f ~/.btc_monitor/monitor.log

# 测试通知
openclaw skill run btc-monitor --test-notify
```

### 获取帮助
```bash
# 查看帮助
openclaw skill run btc-monitor --help

# 查看版本
openclaw skill run btc-monitor --version

# 报告问题
openclaw skill run btc-monitor --report-issue
```

## 📈 性能

### 资源使用
- CPU: < 1% (监控时)
- 内存: ~50MB
- 网络: 每间隔一次API调用

### 监控容量
- 支持同时监控多个交易对
- 支持多个价格阈值
- 可扩展的通知渠道

### 可靠性
- 自动重试机制
- 异常恢复
- 状态持久化

## 🔄 集成

### 与OpenClaw集成
```yaml
# OpenClaw配置示例
skills:
  btc-monitor:
    enabled: true
    schedule: "*/15 * * * *"  # 每15分钟
    params:
      low: 70000
      high: 75000
      notify: telegram
```

### 与Cron集成
```bash
# 每15分钟监控一次
*/15 * * * * cd ~/btc_quant_team && openclaw skill run btc-monitor --once >> monitor.log 2>&1
```

### 与系统服务集成
```systemd
# /etc/systemd/system/btc-monitor.service
[Unit]
Description=BTC价格监控服务
After=network.target

[Service]
Type=simple
User=francis
WorkingDirectory=/home/francis/btc_quant_team
ExecStart=/usr/bin/openclaw skill run btc-monitor
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## 📚 示例

### 示例1: 基本监控
```bash
# 设置69000-73000监控区间，15分钟间隔
openclaw skill run btc-monitor --low 69000 --high 73000 --interval 15
```

### 示例2: 快速监控
```bash
# 快速监控，5分钟间隔，Telegram通知
openclaw skill run btc-monitor --low 70000 --high 75000 --interval 5 --notify telegram
```

### 示例3: 生产部署
```bash
# 使用环境变量配置
export BTC_MONITOR_LOW=69000
export BTC_MONITOR_HIGH=73000
export BTC_MONITOR_INTERVAL=15

# 后台运行
nohup openclaw skill run btc-monitor >> monitor.log 2>&1 &
```

### 示例4: 集成到工作流
```bash
# 监控 + 分析工作流
openclaw skill run btc-monitor --low 70000 --high 75000 --once && \
openclaw skill run market-analysis --symbol BTCUSDT
```

## 📅 版本历史

### v1.0.0 (2026-04-19)
- 初始版本发布
- 基础价格监控功能
- Telegram通知支持
- 状态管理和报告

### v1.1.0 (计划中)
- 多交易对支持
- 更多通知渠道
- 高级分析集成
- 性能优化

## 📞 支持

### 获取帮助
- 查看文档: `openclaw skill run btc-monitor --help`
- 查看日志: `~/.btc_monitor/monitor.log`
- 报告问题: GitHub Issues

### 社区
- OpenClaw社区: https://discord.com/invite/clawd
- Skill仓库: https://clawhub.ai

---

**🦊 Skill设计: Steve量化助手**  
**版本: 1.0.0**  
**更新: 2026-04-19**  
**许可证: MIT**