#!/bin/bash
# 设置数据质量Skill每小时自动检查

echo "🦊 设置数据质量Skill每小时自动检查"
echo "=" * 60

# 检查当前目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "脚本目录: $SCRIPT_DIR"

# 备份当前cron
crontab -l > /tmp/cron_data_quality_backup_$(date +%Y%m%d_%H%M%S).txt
echo "✅ cron配置已备份"

# 创建新的cron配置
cat > /tmp/new_cron_data_quality.txt << 'EOF'
# 🦊 数据质量Skill每小时自动检查
# 每小时检查数据质量和新鲜度，如果需要则更新数据到最新时间点
0 * * * * cd /home/francis/btc_quant_team/skills/data-quality && python3 scripts/hourly_data_quality_check.py >> /home/francis/btc_quant_team/skills/data-quality/logs/hourly_cron.log 2>&1

# 📅 每日完整数据质量报告
0 9 * * * cd /home/francis/btc_quant_team/skills/data-quality && python3 scripts/quality_monitor_cli.py report --type daily >> /home/francis/btc_quant_team/skills/data-quality/logs/daily_report.log 2>&1
EOF

# 安装新的cron配置
crontab /tmp/new_cron_data_quality.txt
rm /tmp/new_cron_data_quality.txt

echo "✅ cron配置更新完成"
echo ""
echo "📋 当前cron配置:"
crontab -l
echo ""
echo "📁 相关文件:"
echo "   脚本: $SCRIPT_DIR/scripts/hourly_data_quality_check.py"
echo "   日志: $SCRIPT_DIR/logs/hourly_cron.log"
echo "   配置: $SCRIPT_DIR/config/monitor.yaml"
echo ""
echo "🔄 立即测试每小时检查:"
cd "$SCRIPT_DIR" && python3 scripts/hourly_data_quality_check.py
echo ""
echo "💡 监控建议:"
echo "   1. 查看日志: tail -f $SCRIPT_DIR/logs/hourly_cron.log"
echo "   2. 手动触发: python3 scripts/hourly_data_quality_check.py"
echo "   3. 查看状态: python3 scripts/quality_monitor_cli.py status"
echo ""
echo "🦊 数据质量Skill每小时自动检查已配置完成！"