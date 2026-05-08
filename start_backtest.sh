#!/bin/bash
# BTC 回测系统启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}   🚀 BTC 回测系统启动脚本${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 检查 Python
echo -e "${YELLOW}[1/5]${NC} 检查 Python 环境..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 未安装${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✅ $PYTHON_VERSION${NC}"
echo ""

# 检查依赖
echo -e "${YELLOW}[2/5]${NC} 检查依赖..."
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  FastAPI 未安装，正在安装...${NC}"
    pip3 install fastapi uvicorn pandas numpy mysql-connector-python pyyaml
fi
echo -e "${GREEN}✅ 依赖已就绪${NC}"
echo ""

# 检查数据库
echo -e "${YELLOW}[3/5]${NC} 检查数据库连接..."
if python3 -c "
import mysql.connector
try:
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='btc_assistant'
    )
    conn.close()
    print('${GREEN}✅ 数据库连接成功${NC}')
except Exception as e:
    print('${RED}❌ 数据库连接失败: ' + str(e) + '${NC}')
    exit(1)
" 2>/dev/null; then
    :
else
    echo -e "${RED}❌ 数据库连接失败${NC}"
    echo -e "${YELLOW}请检查:${NC}"
    echo "  1. MySQL 是否运行: mysql.server status"
    echo "  2. 数据库配置: config/backtest.yaml"
    exit 1
fi
echo ""

# 检查端口
echo -e "${YELLOW}[4/5]${NC} 检查端口 8001..."
if lsof -Pi :8001 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  端口 8001 已被占用${NC}"
    read -p "是否杀死占用进程? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        lsof -ti:8001 | xargs kill -9
        echo -e "${GREEN}✅ 端口已释放${NC}"
    else
        echo -e "${RED}❌ 启动取消${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ 端口可用${NC}"
fi
echo ""

# 启动服务器
echo -e "${YELLOW}[5/5]${NC} 启动 API 服务器..."
cd "$(dirname "$0")"

# 检查 API 文件是否存在
if [ ! -f "backend/backtest/api.py" ]; then
    echo -e "${RED}❌ API 文件不存在: backend/backtest/api.py${NC}"
    echo -e "${YELLOW}提示: 回测系统代码可能还未创建${NC}"
    echo ""
    echo "请先创建以下文件:"
    echo "  - backend/backtest/api.py (FastAPI 应用)"
    echo "  - web/backtest.html (Web UI)"
    echo ""
    exit 1
fi

# 启动服务器
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python3 backend/backtest/api.py &
API_PID=$!

# 等待服务器启动
echo -e "${BLUE}⏳ 等待服务器启动...${NC}"
sleep 3

# 检查服务器是否成功启动
if ps -p $API_PID > /dev/null; then
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}   ✅ 系统启动成功！${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${BLUE}📊 Web UI:${NC}      http://127.0.0.1:8001/backtest.html"
    echo -e "${BLUE}📖 API 文档:${NC}    http://127.0.0.1:8001/docs"
    echo -e "${BLUE}🔧 服务器 PID:${NC}  $API_PID"
    echo ""
    echo -e "${YELLOW}🛑 停止服务:${NC}    kill $API_PID"
    echo -e "${YELLOW}📝 查看日志:${NC}    tail -f logs/backtest.log"
    echo ""
    
    # 尝试打开浏览器
    if command -v open &> /dev/null; then
        echo -e "${BLUE}🌐 正在打开浏览器...${NC}"
        sleep 1
        open http://127.0.0.1:8001/backtest.html 2>/dev/null || true
    fi
    
    # 保存 PID 到文件
    echo $API_PID > .backtest_server.pid
    
    # 等待用户按 Ctrl+C
    echo -e "${YELLOW}按 Ctrl+C 停止服务器${NC}"
    wait $API_PID
else
    echo -e "${RED}❌ 服务器启动失败${NC}"
    echo ""
    echo "请检查:"
    echo "  1. 查看错误日志"
    echo "  2. 确认 backend/backtest/api.py 文件存在"
    echo "  3. 确认所有依赖已安装"
    exit 1
fi
