#!/bin/bash
# BTC数据刷新脚本
# 手动运行或由cron调用

set -e

echo "🚀 BTC数据刷新脚本"
echo "========================"
date
echo ""

# 配置
PROJECT_DIR="/Users/zhaojun/ideaprojects/btc_quant_team"
LOG_DIR="$HOME/logs/btc_refresh"
LOG_FILE="$LOG_DIR/refresh.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# 创建日志目录
mkdir -p "$LOG_DIR"

# 记录开始时间
echo "[$TIMESTAMP] 开始BTC数据刷新" >> "$LOG_FILE"
echo "开始时间: $TIMESTAMP"

# 切换到项目目录
cd "$PROJECT_DIR" || {
    echo "❌ 错误: 无法切换到项目目录: $PROJECT_DIR"
    echo "[$TIMESTAMP] 错误: 无法切换到项目目录" >> "$LOG_FILE"
    exit 1
}

echo "项目目录: $PROJECT_DIR"
echo "日志文件: $LOG_FILE"
echo ""

# 运行刷新工具
echo "🔄 运行数据刷新工具..."
python3 tools/data/refresh_data.py --action refresh --password "" 2>&1 | tee -a "$LOG_FILE"

# 检查执行结果
EXIT_CODE=${PIPESTATUS[0]}
END_TIME=$(date '+%Y-%m-%d %H:%M:%S')

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ 数据刷新完成"
    echo "[$END_TIME] 数据刷新完成 (退出码: $EXIT_CODE)" >> "$LOG_FILE"
else
    echo "❌ 数据刷新失败 (退出码: $EXIT_CODE)"
    echo "[$END_TIME] 数据刷新失败 (退出码: $EXIT_CODE)" >> "$LOG_FILE"
fi

echo "结束时间: $END_TIME"
echo ""

# 显示最新日志
echo "📋 最新日志内容:"
echo "----------------------------------------"
tail -10 "$LOG_FILE" | sed 's/^/  /'
echo "----------------------------------------"

exit $EXIT_CODE