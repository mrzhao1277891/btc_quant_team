#!/bin/bash
# 查看BTC数据刷新日志

LOG_DIR="$HOME/logs/btc_refresh"
LOG_FILE="$LOG_DIR/refresh.log"

if [ ! -f "$LOG_FILE" ]; then
    echo "❌ 日志文件不存在: $LOG_FILE"
    echo "请先运行刷新脚本或等待cron任务执行"
    exit 1
fi

echo "📊 BTC数据刷新日志查看器"
echo "================================"
echo "日志文件: $LOG_FILE"
echo "文件大小: $(du -h "$LOG_FILE" | cut -f1)"
echo "最后修改: $(stat -f "%Sm" "$LOG_FILE")"
echo ""

# 显示选项
echo "请选择查看方式:"
echo "1. 查看最新日志 (最后50行)"
echo "2. 查看今天的日志"
echo "3. 查看错误日志"
echo "4. 实时监控日志"
echo "5. 清空日志文件"
echo "6. 查看统计信息"
echo "0. 退出"
echo ""

read -p "请输入选项 [0-6]: " choice

case $choice in
    1)
        echo ""
        echo "📋 最新日志 (最后50行):"
        echo "----------------------------------------"
        tail -50 "$LOG_FILE"
        echo "----------------------------------------"
        ;;
    2)
        echo ""
        echo "📅 今天的日志:"
        echo "----------------------------------------"
        grep "$(date '+%Y-%m-%d')" "$LOG_FILE" || echo "今天还没有日志记录"
        echo "----------------------------------------"
        ;;
    3)
        echo ""
        echo "⚠️  错误日志:"
        echo "----------------------------------------"
        grep -i -E "(错误|失败|error|fail|exception)" "$LOG_FILE" | tail -30 || echo "没有发现错误"
        echo "----------------------------------------"
        ;;
    4)
        echo ""
        echo "👀 实时监控日志 (Ctrl+C退出):"
        echo "----------------------------------------"
        tail -f "$LOG_FILE"
        ;;
    5)
        read -p "⚠️  确定要清空日志文件吗？(y/N): " confirm
        if [[ $confirm == [yY] ]]; then
            > "$LOG_FILE"
            echo "✅ 日志文件已清空"
        else
            echo "❌ 操作取消"
        fi
        ;;
    6)
        echo ""
        echo "📈 日志统计信息:"
        echo "----------------------------------------"
        echo "总行数: $(wc -l < "$LOG_FILE")"
        echo "开始时间: $(head -1 "$LOG_FILE" | cut -d' ' -f2-3 2>/dev/null || echo '未知')"
        echo "结束时间: $(tail -1 "$LOG_FILE" | cut -d' ' -f2-3 2>/dev/null || echo '未知')"
        echo "成功次数: $(grep -c "数据刷新完成" "$LOG_FILE")"
        echo "失败次数: $(grep -c "数据刷新失败" "$LOG_FILE")"
        echo "最近5次执行:"
        grep -E "开始BTC数据刷新|数据刷新完成|数据刷新失败" "$LOG_FILE" | tail -5 | sed 's/^/  /'
        echo "----------------------------------------"
        ;;
    0)
        echo "退出"
        ;;
    *)
        echo "❌ 无效选项"
        ;;
esac