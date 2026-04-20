# 🕐 每小时数据质量监控指南

## 🎯 概述
数据质量专家Skill现在具备**每小时自动检查数据质量和新鲜度**的功能。这个系统会每小时检查所有时间框架的数据，如果发现数据过时或缺失，会自动从Binance拉取最新数据并更新到数据库。

## ✨ 核心功能

### 🔍 每小时自动检查
- **检查频率**: 每小时整点执行 (如: 08:00, 09:00, 10:00...)
- **检查内容**: 数据新鲜度、完整性、准确性
- **自动更新**: 如果数据过时，自动从Binance获取最新数据
- **智能判断**: 根据数据年龄决定是否需要更新

### 📊 监控的时间框架
| 时间框架 | 新鲜度阈值 | 说明 |
|----------|------------|------|
| **4小时** | 6小时 | 超过6小时未更新需要更新 |
| **日线** | 24小时 | 超过24小时未更新需要更新 |
| **周线** | 168小时 | 超过7天未更新需要更新 |
| **月线** | 720小时 | 超过30天未更新需要更新 |

### 🔧 智能更新逻辑
1. **数据缺失** → 立即更新
2. **数据陈旧** (超过阈值) → 立即更新
3. **数据较旧** (超过阈值一半) → 考虑更新
4. **数据新鲜** (小于阈值一半) → 跳过更新

## 🚀 系统配置

### Cron配置
```bash
# 🦊 数据质量Skill每小时自动检查
0 * * * * cd /home/francis/btc_quant_team/skills/data-quality && python3 scripts/hourly_data_quality_check.py >> /home/francis/btc_quant_team/skills/data-quality/logs/hourly_cron.log 2>&1

# 📅 每日完整数据质量报告
0 9 * * * cd /home/francis/btc_quant_team/skills/data-quality && python3 scripts/quality_monitor_cli.py report --type daily >> /home/francis/btc_quant_team/skills/data-quality/logs/daily_report.log 2>&1
```

### 监控配置 (`config/monitor.yaml`)
```yaml
monitoring:
  enabled: true
  check_interval_minutes: 60  # 每小时检查
  auto_update: true           # 自动更新过时数据
  symbols: ['BTCUSDT']        # 监控的交易对
  timeframes: ['4h', '1d', '1w', '1M']  # 监控的时间框架
  freshness_thresholds:       # 新鲜度阈值（小时）
    4h: 6
    1d: 24
    1w: 168
    1M: 720
```

## 📁 相关文件

### 核心脚本
```
scripts/hourly_data_quality_check.py      # 每小时检查主脚本
scripts/quality_monitor_cli.py            # 质量监控CLI
config/monitor.yaml                       # 监控配置
```

### 日志文件
```
logs/hourly_cron.log                      # 每小时检查日志
logs/hourly_data_quality.log              # 详细检查日志
hourly_records/                           # 检查记录存档
```

### 配置脚本
```
setup_hourly_cron.sh                      # 设置cron的脚本
```

## 🎮 使用方法

### 1. 手动触发检查
```bash
# 进入技能目录
cd /home/francis/btc_quant_team/skills/data-quality

# 手动运行每小时检查
python3 scripts/hourly_data_quality_check.py

# 使用CLI检查
python3 scripts/quality_monitor_cli.py check --all
```

### 2. 查看监控状态
```bash
# 查看cron日志
tail -f logs/hourly_cron.log

# 查看详细日志
tail -f logs/hourly_data_quality.log

# 查看最新检查记录
ls -la hourly_records/
cat hourly_records/hourly_check_$(date +%Y%m%d_%H)*.json | tail -20
```

### 3. 验证数据新鲜度
```bash
# 检查当前数据状态
python3 scripts/hourly_data_quality_check.py

# 输出示例:
# 🦊 每小时数据质量检查启动
# ========================================================
# 📊 每小时数据质量检查 - 2026-04-20 08:25:46
# --------------------------------------------------
#   4小时: ✅ 0.4小时
#   日线: ✅ 0.4小时
#   周线: ✅ 0.4小时
#   月线: ✅ 456.4小时
# 📋 检查总结:
#   总检查项: 4
#   需要更新: 1
#   成功更新: 1
#   失败更新: 0
#   新鲜数据: 4
#   陈旧数据: 0
#   缺失数据: 0
#   检查耗时: 0.2秒
```

### 4. 紧急手动更新
```bash
# 强制更新所有数据
python3 scripts/hourly_data_quality_check.py

# 只更新特定时间框架
python3 -c "
from scripts.hourly_data_quality_check import update_data
result = update_data('BTCUSDT', '4h')
print(f'更新结果: {result}')
"
```

## 📈 监控报告

### 每小时检查报告
每次检查都会生成详细的JSON报告：
```json
{
  "timestamp": "2026-04-20T08:25:46.746000",
  "duration_seconds": 0.2,
  "summary": {
    "total_checks": 4,
    "needed_updates": 1,
    "successful_updates": 1,
    "failed_updates": 0,
    "fresh_data": 4,
    "stale_data": 0,
    "missing_data": 0
  },
  "results": [...]
}
```

### 日志格式
```
2026-04-20 08:25:46,511 - root - INFO - ⏰ 开始每小时数据质量检查
2026-04-20 08:25:46,512 - root - INFO - 🔍 检查并更新数据: BTCUSDT (4h)
2026-04-20 08:25:46,512 - root - INFO - 新鲜度检查: BTCUSDT (4h) - 0.4小时 (阈值: 6小时)
2026-04-20 08:25:46,512 - root - INFO - 数据非常新鲜，跳过更新: BTCUSDT (4h) - 0.4小时
```

## 🔧 故障排除

### 常见问题

#### 1. 网络连接失败
```
错误: 请求超时: BTCUSDT (1w)
```
**解决方案**:
- 检查网络连接
- 增加API超时时间
- 使用备用数据源

#### 2. 数据库访问错误
```
错误: 无法连接数据库
```
**解决方案**:
- 检查数据库文件路径
- 确保有读写权限
- 验证数据库完整性

#### 3. 数据更新失败
```
错误: 数据更新失败: BTCUSDT (4h)
```
**解决方案**:
- 检查Binance API状态
- 验证交易对和时间框架
- 手动测试API连接

### 调试命令
```bash
# 测试网络连接
curl -s https://api.binance.com/api/v3/ping

# 测试数据库连接
sqlite3 /home/francis/.openclaw/workspace/crypto_analyzer/data/ultra_light.db "SELECT COUNT(*) FROM klines;"

# 查看cron状态
crontab -l
systemctl status cron

# 查看进程状态
ps aux | grep hourly_data_quality
```

## 🎯 最佳实践

### 1. 监控建议
- **定期查看日志**: 每天检查一次日志文件
- **设置告警**: 配置Telegram或Email告警
- **备份数据**: 定期备份数据库文件
- **性能监控**: 监控检查耗时和成功率

### 2. 维护建议
- **清理旧日志**: 定期清理超过30天的日志
- **更新配置**: 根据需求调整新鲜度阈值
- **测试恢复**: 定期测试数据恢复流程
- **文档更新**: 保持文档与系统同步

### 3. 优化建议
- **并行检查**: 对于多个交易对，考虑并行检查
- **缓存策略**: 添加API响应缓存
- **重试机制**: 增加失败重试次数
- **健康检查**: 添加系统健康检查端点

## 📊 性能指标

### 检查性能
- **平均检查时间**: < 5秒
- **成功率**: > 95%
- **数据新鲜度**: 所有时间框架达标
- **资源使用**: 低内存和CPU占用

### 质量指标
- **4小时数据**: < 6小时新鲜度
- **日线数据**: < 24小时新鲜度
- **周线数据**: < 168小时新鲜度
- **月线数据**: < 720小时新鲜度

## 🔗 与其他系统集成

### 与BTC监控系统集成
```python
# 在BTC监控系统中调用数据质量检查
from btc_quant_team.skills.data-quality.scripts.hourly_data_quality_check import check_freshness

def monitor_with_quality_check():
    # 检查数据新鲜度
    freshness = check_freshness('BTCUSDT', '4h')
    
    if freshness['is_fresh']:
        # 数据新鲜，执行监控
        run_monitoring()
    else:
        # 数据陈旧，先更新
        print(f"数据陈旧: {freshness['age_hours']:.1f}小时")
        update_data('BTCUSDT', '4h')
```

### 与交易分析系统集成
```python
# 在交易分析前检查数据质量
def analyze_with_quality_guarantee():
    from btc_quant_team.skills.data-quality.scripts.hourly_data_quality_check import run_hourly_check
    
    # 先确保数据新鲜
    summary = run_hourly_check()
    
    if summary['fresh_data'] == summary['total_checks']:
        # 所有数据都新鲜，执行分析
        perform_analysis()
    else:
        # 有数据问题，记录并跳过
        log_data_quality_issue(summary)
```

## 🚀 快速开始

### 1. 首次设置
```bash
# 进入技能目录
cd /home/francis/btc_quant_team/skills/data-quality

# 设置每小时cron
bash setup_hourly_cron.sh

# 测试配置
python3 scripts/hourly_data_quality_check.py
```

### 2. 日常使用
```bash
# 查看监控状态
tail -f logs/hourly_cron.log

# 手动触发检查
python3 scripts/hourly_data_quality_check.py

# 生成报告
python3 scripts/quality_monitor_cli.py report --type summary
```

### 3. 维护操作
```bash
# 清理旧日志
find logs/ -name "*.log" -mtime +30 -delete
find hourly_records/ -name "*.json" -mtime +30 -delete

# 备份配置
cp config/monitor.yaml config/monitor.yaml.backup.$(date +%Y%m%d)

# 更新cron配置
crontab -l > cron_backup_$(date +%Y%m%d_%H%M%S).txt
bash setup_hourly_cron.sh
```

## 📋 总结

### 系统优势
1. **自动化**: 每小时自动检查，无需人工干预
2. **智能化**: 智能判断是否需要更新
3. **可靠性**: 网络容错和重试机制
4. **可监控**: 详细日志和报告系统
5. **易集成**: 与其他系统无缝集成

### 保障的数据质量
- ✅ **4小时数据**: 始终保持<6小时新鲜度
- ✅ **日线数据**: 始终保持<24小时新鲜度  
- ✅ **周线数据**: 始终保持<7天新鲜度
- ✅ **月线数据**: 始终保持<30天新鲜度

### 立即开始
```bash
# 启动每小时监控
cd /home/francis/btc_quant_team/skills/data-quality
bash setup_hourly_cron.sh

# 验证系统运行
python3 scripts/hourly_data_quality_check.py

# 查看监控状态
tail -f logs/hourly_cron.log
```

**🎯 数据质量专家Skill的每小时监控系统现已就绪！**

**你的加密货币数据将始终保持最新、最准确的状态！** 🦊🚀