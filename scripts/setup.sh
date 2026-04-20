#!/bin/bash
# BTC量化团队 - 环境设置脚本

set -e  # 遇到错误退出

echo "🚀 BTC量化团队环境设置脚本"
echo "================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "命令 '$1' 未找到，请先安装"
        return 1
    fi
    return 0
}

# 主函数
main() {
    log_info "开始设置BTC量化团队环境..."
    
    # 1. 检查Python
    log_info "1. 检查Python环境..."
    check_command python3 || exit 1
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    log_success "Python版本: $PYTHON_VERSION"
    
    # 2. 检查pip
    log_info "2. 检查pip..."
    check_command pip3 || {
        log_warning "pip3未找到，尝试安装..."
        sudo apt-get update && sudo apt-get install -y python3-pip
    }
    PIP_VERSION=$(pip3 --version | cut -d' ' -f2)
    log_success "pip版本: $PIP_VERSION"
    
    # 3. 创建虚拟环境
    log_info "3. 创建Python虚拟环境..."
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        log_success "虚拟环境创建成功"
    else
        log_warning "虚拟环境已存在，跳过创建"
    fi
    
    # 4. 激活虚拟环境
    log_info "4. 激活虚拟环境..."
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        log_success "虚拟环境已激活"
    else
        log_error "虚拟环境激活文件未找到"
        exit 1
    fi
    
    # 5. 升级pip
    log_info "5. 升级pip..."
    pip install --upgrade pip
    log_success "pip升级完成"
    
    # 6. 安装依赖
    log_info "6. 安装项目依赖..."
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        log_success "依赖安装完成"
    else
        log_error "requirements.txt 未找到"
        exit 1
    fi
    
    # 7. 安装开发依赖
    log_info "7. 安装开发依赖..."
    if [ -f "pyproject.toml" ]; then
        pip install -e ".[dev]"
        log_success "开发依赖安装完成"
    else
        log_warning "pyproject.toml 未找到，跳过开发依赖安装"
    fi
    
    # 8. 创建配置目录
    log_info "8. 创建配置目录..."
    mkdir -p ~/.btc_quant
    log_success "配置目录创建完成: ~/.btc_quant"
    
    # 9. 复制配置文件
    log_info "9. 设置配置文件..."
    if [ -f "config/development.yaml" ]; then
        if [ ! -f ~/.btc_quant/config.yaml ]; then
            cp config/development.yaml ~/.btc_quant/config.yaml
            log_success "配置文件已复制"
        else
            log_warning "配置文件已存在，跳过复制"
        fi
    else
        log_warning "开发配置文件未找到，跳过复制"
    fi
    
    # 10. 设置环境变量
    log_info "10. 设置环境变量..."
    ENV_FILE=".env"
    if [ ! -f "$ENV_FILE" ]; then
        cat > "$ENV_FILE" << EOF
# BTC量化团队环境变量
# 复制此文件为 .env.local 并填写实际值

# Binance API (可选)
# export BINANCE_API_KEY="your_api_key_here"
# export BINANCE_API_SECRET="your_api_secret_here"

# Telegram Bot (可选)
# export TELEGRAM_BOT_TOKEN="your_bot_token_here"
# export TELEGRAM_CHAT_ID="your_chat_id_here"

# 数据库路径
export BTC_QUANT_DB_PATH="~/.btc_quant/main.db"

# 日志级别
export LOG_LEVEL="INFO"

# 开发模式
export BTC_QUANT_ENV="development"
EOF
        log_success "环境变量模板已创建: $ENV_FILE"
        log_warning "请编辑 $ENV_FILE 填写实际配置"
    else
        log_warning "环境变量文件已存在，跳过创建"
    fi
    
    # 11. 初始化Git (如果未初始化)
    log_info "11. 初始化Git仓库..."
    if [ ! -d ".git" ]; then
        git init
        log_success "Git仓库初始化完成"
    else
        log_warning "Git仓库已存在，跳过初始化"
    fi
    
    # 12. 设置Git钩子
    log_info "12. 设置Git钩子..."
    if command -v pre-commit &> /dev/null; then
        pre-commit install
        log_success "Git钩子设置完成"
    else
        log_warning "pre-commit未安装，跳过Git钩子设置"
    fi
    
    # 13. 运行测试
    log_info "13. 运行基础测试..."
    if command -v pytest &> /dev/null; then
        if pytest tests/unit/tools/ -v --tb=short; then
            log_success "基础测试通过"
        else
            log_warning "部分测试失败，请检查"
        fi
    else
        log_warning "pytest未安装，跳过测试"
    fi
    
    # 14. 创建快捷脚本
    log_info "14. 创建快捷脚本..."
    cat > btc-quant << 'EOF'
#!/bin/bash
# BTC量化团队快捷命令

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

source venv/bin/activate 2>/dev/null || echo "警告: 虚拟环境未找到"

case "$1" in
    "monitor")
        python -m skills.btc-monitor.scripts.main "${@:2}"
        ;;
    "analyze")
        python -m tools.analysis.technical "${@:2}"
        ;;
    "data")
        python -m tools.data.fetch "${@:2}"
        ;;
    "test")
        pytest "${@:2}"
        ;;
    "shell")
        python -c "from tools.data.fetch import fetch_current_price; print(fetch_current_price())"
        ;;
    "help"|"")
        echo "BTC量化团队快捷命令:"
        echo "  btc-quant monitor   启动BTC监控"
        echo "  btc-quant analyze   运行技术分析"
        echo "  btc-quant data      获取数据"
        echo "  btc-quant test      运行测试"
        echo "  btc-quant shell     进入Python shell"
        echo "  btc-quant help      显示帮助"
        ;;
    *)
        echo "未知命令: $1"
        echo "使用 'btc-quant help' 查看可用命令"
        ;;
esac
EOF
    
    chmod +x btc-quant
    log_success "快捷脚本创建完成: ./btc-quant"
    
    # 15. 完成提示
    echo ""
    echo "🎉 ${GREEN}BTC量化团队环境设置完成！${NC}"
    echo "================================"
    echo ""
    echo "下一步操作:"
    echo "1. ${YELLOW}编辑环境变量${NC}:"
    echo "   cp .env .env.local"
    echo "   nano .env.local  # 填写实际配置"
    echo ""
    echo "2. ${YELLOW}测试数据获取${NC}:"
    echo "   ./btc-quant data"
    echo ""
    echo "3. ${YELLOW}启动BTC监控${NC}:"
    echo "   ./btc-quant monitor --low 70000 --high 75000"
    echo ""
    echo "4. ${YELLOW}运行完整测试${NC}:"
    echo "   ./btc-quant test"
    echo ""
    echo "5. ${YELLOW}安装OpenClaw Skill${NC}:"
    echo "   ln -s \$(pwd)/skills/btc-monitor ~/.openclaw/skills/"
    echo ""
    echo "常用命令:"
    echo "  source venv/bin/activate  # 激活虚拟环境"
    echo "  ./btc-quant help          # 查看所有命令"
    echo "  pytest tests/ -v          # 运行所有测试"
    echo ""
    echo "🦊 祝你量化交易顺利！"
}

# 运行主函数
main "$@"