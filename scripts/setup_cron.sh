#!/bin/bash
# BTC数据刷新cron配置脚本
# 作者: Steve
# 日期: 2026-04-21

set -e

echo "🚀 BTC数据刷新cron配置脚本"
echo "================================"

# 项目路径
PROJECT_DIR="/Users/zhaojun/ideaprojects/btc_quant_team"
LOG_DIR="$HOME/logs/btc_refresh"
LOG_FILE="$LOG_DIR/refresh.log"

# 检查项目目录
if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ 错误: 项目目录不存在: $PROJECT_DIR"
    exit 1
fi

# 创建日志目录
mkdir -p "$LOG_DIR"
echo "✅ 日志目录: $LOG_DIR"

# 检查Python脚本
if [ ! -f "$PROJECT_DIR/tools/data/refresh_data.py" ]; then
    echo "❌ 错误: 刷新工具不存在: $PROJECT_DIR/tools/data/refresh_data.py"
    exit 1
fi
echo "✅ 刷新工具: $PROJECT_DIR/tools/data/refresh_data.py"

# 生成cron命令
CRON_CMD="0 */2 * * * cd $PROJECT_DIR && python3 tools/data/refresh_data.py --action refresh --password '' >> $LOG_FILE 2>&1"

echo ""
echo "📋 生成的cron命令:"
echo "----------------------------------------"
echo "$CRON_CMD"
echo "----------------------------------------"

# 检查当前cron任务
echo ""
echo "🔍 检查当前cron任务..."
crontab -l 2>/dev/null | grep -q "refresh_data.py" && {
    echo "⚠️  发现已存在的BTC刷新任务，将替换"
    # 移除现有任务
    crontab -l 2>/dev/null | grep -v "refresh_data.py" | crontab -
}

# 添加新任务
(crontab -l 2>/dev/null; echo "# BTC数据刷新 - 每2小时运行一次"; echo "$CRON_CMD") | crontab -

echo ""
echo "✅ cron任务已添加!"
echo ""
echo "📊 任务详情:"
echo "   频率: 每2小时 (0 */2 * * *)"
echo "   命令: python3 tools/data/refresh_data.py --action refresh --password ''"
echo "   日志: $LOG_FILE"
echo "   刷新的周期: 4h, 1d, 1w, 1M"
echo ""
echo "🔧 管理命令:"
echo "   查看cron任务: crontab -l"
echo "   编辑cron任务: crontab -e"
echo "   查看日志: tail -f $LOG_FILE"
echo "   手动运行: cd $PROJECT_DIR && python3 tools/data/refresh_data.py --action refresh --password ''"
echo ""
echo "🎉 配置完成!"