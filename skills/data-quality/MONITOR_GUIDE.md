# 📊 数据质量监控系统使用指南

## 🎯 概述

增强版数据质量专家Skill现在具备完整的定时监控和自动更新能力，可以：

1. **定时检查**数据质量和新鲜度
2. **自动更新**过时的数据
3. **智能告警**发现问题及时通知
4. **生成报告**提供详细的质量分析
5. **配置管理**灵活的监控策略

## 🚀 快速开始

### 安装依赖
```bash
cd /home/francis/btc_quant_team/skills/data-quality
pip3 install pandas numpy schedule requests pyyaml
```

### 测试系统
```bash
# 运行增强版测试
python3 test_enhanced_monitor.py

# 测试CLI工具
python3 scripts/quality_monitor_cli.py status
```

### 配置监控
编辑 `config/monitor.yaml` 文件，配置：
- 监控的交易对和时间框架
- 检查间隔和新鲜度阈值
- 告警渠道和通知方式
- 报告生成设置

## 📋 核心功能

### 1. 定时质量监控
```bash
# 启动监控
python3 scripts/quality_monitor_cli.py start

# 查看状态
python3 scripts/quality_monitor_cli.py status

# 停止监控
python3 scripts/quality_monitor_cli.py stop
```

### 2. 手动数据检查
```bash
# 检查单个交易对
python3 scripts/quality_monitor_cli.py check --symbol BTCUSDT --timeframe 1d

# 检查所有配置的交易对
python3 scripts/quality_monitor_cli.py check --all
```

### 3. 数据更新
```bash
# 更新过时数据
python3 scripts/quality_monitor_cli.py update --symbol BTCUSDT --timeframe 4h

# 更新所有过时数据
python3 scripts/quality_monitor_cli.py update --all
```

### 4. 报告生成
```bash
# 生成摘要报告
python3 scripts/quality_monitor_cli.py report --type summary

# 生成日报
python3 scripts/quality_monitor_cli.py report --type daily

# 指定输出文件
python3 scripts/quality_monitor_cli.py report --type summary --output my_report.json
```

### 5. 配置管理
```bash
# 查看当前配置
python3 scripts/quality_monitor_cli.py config --show

# 验证配置
python3 scripts/quality_monitor_cli.py config --validate
```

## ⏰ 定时任务设置

### 使用Cron定时运行
```bash
# 编辑crontab
crontab -e

# 添加以下任务：
# 每4小时运行一次监控
0 */4 * * * cd /home/francis/btc_quant_team/skills/data-quality && python3 scripts/quality_monitor_cli.py check --all >> /home/francis/btc_quant_team/skills/data-quality/logs/cron_check.log 2>&1

# 每天9点生成日报
0 9 * * * cd /home/francis/btc_quant_team/skills/data-quality && python3 scripts/quality_monitor_cli.py report --type daily >> /home/francis/btc_quant_team/skills/data-quality/logs/cron_report.log 2>&1

# 每周一生成周报
0 9 * * 1 cd /home/francis/btc_quant_team/skills/data-quality && python3 scripts/quality_monitor_cli.py report --type weekly >> /home/francis/btc_quant_team/skills/data-quality/logs/cron_weekly.log 2>&1
```

### 使用Systemd服务（可选）
```bash
# 创建服务文件
sudo nano /etc/systemd/system/data-quality-monitor.service

# 内容：
[Unit]
Description=Data Quality Monitor
After=network.target

[Service]
Type=simple
User=francis
WorkingDirectory=/home/francis/btc_quant_team/skills/data-quality
ExecStart=/usr/bin/python3 scripts/quality_monitor_cli.py start
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target

# 启用服务
sudo systemctl enable data-quality-monitor
sudo systemctl start data-quality-monitor
sudo systemctl status data-quality-monitor
```

## 🔧 配置详解

### 监控配置 (monitoring)
```yaml
monitoring:
  enabled: true                    # 监控开关
  check_interval_minutes: 60       # 检查间隔（分钟）
  auto_update: true                # 自动更新过时数据
  alert_on_failure: true           # 失败时告警
  
  symbols:                         # 监控的交易对
    - BTCUSDT
    # - ETHUSDT
    # - BNBUSDT
  
  timeframes:                      # 监控的时间框架
    - 1d
    - 4h
    - 1w
    - 1M
  
  freshness_thresholds:            # 新鲜度阈值（小时）
    1h: 2
    4h: 6
    1d: 24
    1w: 168
    1M: 720
```

### 告警配置 (alerts)
```yaml
alerts:
  enabled: true                    # 告警开关
  channels:                        # 告警渠道
    - log                          # 系统日志
    # - telegram                   # Telegram消息
    # - email                      # 电子邮件
  
  min_severity: warning            # 最小告警严重程度
  
  # Telegram配置
  telegram_bot_token: "YOUR_BOT_TOKEN"
  telegram_chat_id: "YOUR_CHAT_ID"
  
  # Email配置
  email_smtp_server: "smtp.gmail.com"
  email_smtp_port: 587
  email_username: "your_email@gmail.com"
  email_password: "your_password"
  email_from: "your_email@gmail.com"
  email_to: "recipient@example.com"
```

### 报告配置 (reporting)
```yaml
reporting:
  generate_reports: true           # 生成报告
  report_dir: "reports"            # 报告保存目录
  keep_days: 30                    # 报告保留天数
  
  report_types:                    # 报告类型
    - daily                        # 日报
    - weekly                       # 周报
    - monthly                      # 月报
    - on_demand                    # 按需报告
```

## 📊 监控指标

### 质量评分标准
- 🟢 **优秀 (≥90%)**: 数据质量非常好
- 🟡 **良好 (80-89%)**: 数据质量良好，有小问题
- 🟠 **一般 (70-79%)**: 数据质量一般，需要关注
- 🔴 **需要改进 (<70%)**: 数据质量差，需要立即处理

### 新鲜度标准
- ✅ **新鲜**: 数据年龄 ≤ 阈值
- ⚠️ **较旧**: 数据年龄 ≤ 2倍阈值
- ❌ **过时**: 数据年龄 > 2倍阈值

### 检查维度
1. **完整性**: 数据是否完整，有无缺失
2. **一致性**: 数据逻辑是否正确
3. **准确性**: 数据值是否合理
4. **及时性**: 数据是否及时更新
5. **技术指标**: 技术指标是否完整计算

## 🚨 告警系统

### 告警类型
1. **质量告警**: 数据质量评分低于阈值
2. **新鲜度告警**: 数据过时未更新
3. **更新失败告警**: 自动更新失败
4. **系统告警**: 监控系统自身问题

### 告警示例
```
🚨 数据质量警告

交易对: BTCUSDT
时间框架: 4h
质量评分: 75.2%
问题: 数据新鲜度不足，已8.3小时未更新

建议立即检查数据源。
```

## 📈 报告系统

### 报告类型
1. **摘要报告**: 简要的监控状态
2. **日报**: 每日详细报告
3. **周报**: 每周趋势分析
4. **月报**: 月度总结和规划

### 报告内容
- 监控概览和总体状态
- 各交易对质量评分
- 发现的问题和告警
- 数据更新统计
- 趋势分析和预测
- 改进建议

## 🔍 故障排查

### 常见问题

#### 1. 监控无法启动
```bash
# 检查依赖
pip3 list | grep -E "pandas|numpy|schedule|requests|yaml"

# 检查配置文件
python3 scripts/quality_monitor_cli.py config --validate

# 查看日志
tail -f logs/quality_monitor.log
```

#### 2. 数据更新失败
```bash
# 测试API连接
curl -s "https://api.binance.com/api/v3/ping"

# 手动测试数据获取
python3 -c "
from scripts.data_updater import DataUpdater
updater = DataUpdater()
data = updater.fetch_klines_from_binance('BTCUSDT', '1d', 10)
print(f'获取到 {len(data) if data is not None else 0} 条数据')
"

# 检查数据库权限
ls -la /home/francis/.openclaw/workspace/crypto_analyzer/data/ultra_light.db
```

#### 3. 告警不工作
```bash
# 测试告警发送
python3 -c "
from scripts.quality_monitor import QualityMonitor
monitor = QualityMonitor()
monitor.send_alert('测试告警', 'info')
print('告警发送测试完成')
"

# 检查Telegram配置
python3 -c "
import requests
token = 'YOUR_BOT_TOKEN'
chat_id = 'YOUR_CHAT_ID'
url = f'https://api.telegram.org/bot{token}/getMe'
try:
    response = requests.get(url, timeout=10)
    print(f'Telegram连接: {response.status_code}')
except Exception as e:
    print(f'Telegram连接失败: {e}')
"
```

### 日志文件
- `logs/quality_monitor.log`: 主监控日志
- `logs/cron_check.log`: Cron检查日志
- `logs/cron_report.log`: Cron报告日志
- `data_freshness.log`: 数据新鲜度日志（旧系统）

## 🎯 最佳实践

### 日常维护
1. **每日检查**: 查看监控状态和告警
2. **每周审查**: 审查周报，优化配置
3. **每月总结**: 分析趋势，规划改进

### 配置优化
1. **调整阈值**: 根据需求调整质量阈值
2. **优化频率**: 根据数据更新频率调整检查间隔
3. **扩展监控**: 添加更多交易对和时间框架

### 性能优化
1. **缓存策略**: 启用缓存减少API调用
2. **并发控制**: 控制并发检查数量
3. **数据清理**: 定期清理历史数据

## 🔗 集成指南

### 与其他系统集成
```python
# 在Python项目中集成
import sys
sys.path.append('/home/francis/btc_quant_team/skills/data-quality')

from scripts.quality_monitor import QualityMonitor

class MySystem:
    def __init__(self):
        self.monitor = QualityMonitor()
    
    def check_before_trade(self, symbol):
        """交易前检查数据质量"""
        report = self.monitor.check_data_quality(symbol, '1d')
        return report.overall_score >= 0.9
    
    def get_data_quality(self, symbol, timeframe):
        """获取数据质量信息"""
        report = self.monitor.check_data_quality(symbol, timeframe)
        return {
            'score': report.overall_score,
            'freshness': report.check_results.get('timeliness', {}).get('score', 0),
            'status': 'good' if report.overall_score >= 0.9 else 'warning' if report.overall_score >= 0.8 else 'bad'
        }
```

### Web界面集成（可选）
```python
# Flask示例
from flask import Flask, jsonify
from scripts.quality_monitor import QualityMonitor

app = Flask(__name__)
monitor = QualityMonitor()

@app.route('/api/quality/status')
def get_status():
    report = monitor.generate_monitoring_report()
    return jsonify(report)

@app.route('/api/quality/check/<symbol>/<timeframe>')
def check_quality(symbol, timeframe):
    report = monitor.check_data_quality(symbol, timeframe)
    return jsonify(report.to_dict())

if __name__ == '__main__':
    app.run(debug=True)
```

## 📞 支持与反馈

### 获取帮助
```bash
# 查看帮助
python3 scripts/quality_monitor_cli.py --help
python3 scripts/quality_monitor_cli.py check --help

# 查看文档
cat MONITOR_GUIDE.md | less
cat SKILL.md | head -100
```

### 报告问题
1. 查看日志文件获取错误信息
2. 尝试重现问题
3. 提供相关配置和日志
4. 联系开发者或社区

### 功能建议
1. 描述需求场景
2. 说明期望功能
3. 提供使用示例
4. 讨论实现方案

## 🎉 开始使用

### 第一步：基础配置
```bash
cd /home/francis/btc_quant_team/skills/data-quality

# 1. 编辑配置文件
nano config/monitor.yaml

# 2. 测试配置
python3 scripts/quality_monitor_cli.py config --validate

# 3. 测试功能
python3 scripts/quality_monitor_cli.py check --all
python3 scripts/quality_monitor_cli.py status
```

### 第二步：设置定时任务
```bash
# 1. 添加cron任务
crontab -e

# 2. 添加以下内容：
# 每2小时检查一次
0 */2 * * * cd /home/francis/btc_quant_team/skills/data-quality && python3 scripts/quality_monitor_cli.py check --all >> logs/cron.log 2>&1

# 3. 验证cron任务
crontab -l | grep quality
```

### 第三步：监控和优化
```bash
# 1. 查看监控状态
tail -f logs/quality_monitor.log

# 2. 定期查看报告
ls -la reports/

# 3. 根据需求优化配置
# 调整检查频率、阈值、告警等
```

## 📚 学习资源

### 文档
- `SKILL.md`: 完整技能文档
- `QUICK_START.md`: 快速开始指南
- `MONITOR_GUIDE.md`: 本监控指南
- 代码注释和示例

### 示例
- `test_enhanced_monitor.py`: 完整测试示例
- `scripts/` 目录: 所有源代码
- `config/` 目录: 配置示例

### 社区
- OpenClaw社区: https://discord.com/invite/clawd
- GitHub仓库: https://github.com/openclaw/openclaw
- 问题反馈: GitHub Issues

---

**现在你的数据质量专家Skill已经具备完整的定时监控能力！** 🎯

**开始享受自动化的数据质量管理吧！** 🦊🚀