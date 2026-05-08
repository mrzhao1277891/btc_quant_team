#!/bin/bash
# BTC 回测系统停止脚本

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🛑 停止 BTC 回测系统...${NC}"

# 从 PID 文件读取
if [ -f ".backtest_server.pid" ]; then
    PID=$(cat .backtest_server.pid)
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID
        echo -e "${GREEN}✅ 服务器已停止 (PID: $PID)${NC}"
        rm .backtest_server.pid
    else
        echo -e "${YELLOW}⚠️  服务器未运行 (PID: $PID)${NC}"
        rm .backtest_server.pid
    fi
else
    # 查找并杀死所有相关进程
    PIDS=$(pgrep -f "uvicorn.*backtest")
    if [ -n "$PIDS" ]; then
        echo "$PIDS" | xargs kill
        echo -e "${GREEN}✅ 已停止所有回测服务器进程${NC}"
    else
        echo -e "${YELLOW}⚠️  未找到运行中的回测服务器${NC}"
    fi
fi

# 检查端口
if lsof -Pi :8001 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  端口 8001 仍被占用，强制释放...${NC}"
    lsof -ti:8001 | xargs kill -9
    echo -e "${GREEN}✅ 端口已释放${NC}"
fi

echo -e "${GREEN}✅ 回测系统已完全停止${NC}"
