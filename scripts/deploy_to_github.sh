#!/bin/bash
# 部署BTC量化团队项目到GitHub

echo "🦊 部署BTC量化团队项目到GitHub"
echo "=" * 60

# 检查Git是否安装
if ! command -v git &> /dev/null; then
    echo "❌ Git未安装，请先安装Git"
    echo "   Ubuntu/Debian: sudo apt install git"
    echo "   macOS: brew install git"
    exit 1
fi

# 检查当前目录
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "项目目录: $PROJECT_DIR"

# 检查是否已经是Git仓库
if [ -d "$PROJECT_DIR/.git" ]; then
    echo "✅ 已经是Git仓库"
    
    # 检查远程仓库
    REMOTE_URL=$(git -C "$PROJECT_DIR" remote get-url origin 2>/dev/null || echo "")
    
    if [ -n "$REMOTE_URL" ]; then
        echo "✅ 已配置远程仓库: $REMOTE_URL"
        echo ""
        echo "📦 准备推送更新..."
    else
        echo "❌ 未配置远程仓库"
        echo ""
        read -p "请输入GitHub仓库URL (例如: https://github.com/franciszhao/btc_quant_team.git): " REPO_URL
        
        if [ -z "$REPO_URL" ]; then
            echo "❌ 未提供仓库URL，退出"
            exit 1
        fi
        
        git -C "$PROJECT_DIR" remote add origin "$REPO_URL"
        echo "✅ 已添加远程仓库: $REPO_URL"
    fi
else
    echo "❌ 不是Git仓库，初始化..."
    
    # 初始化Git仓库
    git -C "$PROJECT_DIR" init
    
    # 添加远程仓库
    read -p "请输入GitHub仓库URL (例如: https://github.com/franciszhao/btc_quant_team.git): " REPO_URL
    
    if [ -z "$REPO_URL" ]; then
        echo "❌ 未提供仓库URL，退出"
        exit 1
    fi
    
    git -C "$PROJECT_DIR" remote add origin "$REPO_URL"
    echo "✅ 已初始化Git仓库并添加远程仓库"
fi

# 检查.gitignore
if [ ! -f "$PROJECT_DIR/.gitignore" ]; then
    echo "⚠️  缺少.gitignore文件，创建默认配置..."
    cat > "$PROJECT_DIR/.gitignore" << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Logs
logs/
*.log

# Database
*.db
*.sqlite
*.sqlite3

# Config files with secrets
config/secrets/
config/*.yaml
config/*.json
!config/*.example.yaml
!config/*.example.json

# Temporary files
tmp/
temp/

# OS
.DS_Store
Thumbs.db

# Test coverage
.coverage
htmlcov/
.coverage.*

# Documentation
docs/_build/

# Skills runtime
skills/*/logs/
skills/*/hourly_records/
EOF
    echo "✅ 已创建.gitignore文件"
fi

# 检查是否有未提交的更改
if git -C "$PROJECT_DIR" status --porcelain | grep -q "."; then
    echo "📝 检测到未提交的更改:"
    git -C "$PROJECT_DIR" status --short
    
    read -p "是否提交这些更改？(y/n): " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # 添加所有文件
        git -C "$PROJECT_DIR" add .
        
        # 提交
        COMMIT_MSG="更新项目文件 $(date '+%Y-%m-%d %H:%M:%S')"
        read -p "提交信息 [$COMMIT_MSG]: " USER_COMMIT_MSG
        COMMIT_MSG=${USER_COMMIT_MSG:-$COMMIT_MSG}
        
        git -C "$PROJECT_DIR" commit -m "$COMMIT_MSG"
        echo "✅ 已提交更改"
    else
        echo "⚠️  跳过提交更改"
    fi
else
    echo "✅ 没有未提交的更改"
fi

# 推送代码
echo ""
echo "🚀 准备推送到GitHub..."
read -p "推送到哪个分支？(默认: main): " BRANCH
BRANCH=${BRANCH:-main}

# 检查分支是否存在
if ! git -C "$PROJECT_DIR" show-ref --verify --quiet "refs/heads/$BRANCH"; then
    echo "📝 创建分支: $BRANCH"
    git -C "$PROJECT_DIR" checkout -b "$BRANCH"
else
    git -C "$PROJECT_DIR" checkout "$BRANCH"
fi

# 推送
echo "📤 推送到 origin/$BRANCH..."
if git -C "$PROJECT_DIR" push -u origin "$BRANCH"; then
    echo "✅ 推送成功！"
else
    echo "❌ 推送失败，尝试强制推送？"
    read -p "是否强制推送？(y/n): " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git -C "$PROJECT_DIR" push -u origin "$BRANCH" --force
        echo "✅ 强制推送成功！"
    else
        echo "❌ 推送取消"
        exit 1
    fi
fi

# 显示GitHub链接
REMOTE_URL=$(git -C "$PROJECT_DIR" remote get-url origin)
if [[ $REMOTE_URL == https://github.com/* ]]; then
    REPO_PATH=$(echo "$REMOTE_URL" | sed 's|https://github.com/||' | sed 's|\.git$||')
    GITHUB_URL="https://github.com/$REPO_PATH"
    
    echo ""
    echo "🎉 部署完成！"
    echo "=" * 60
    echo "📊 项目信息:"
    echo "   项目名称: BTC量化团队"
    echo "   GitHub仓库: $GITHUB_URL"
    echo "   分支: $BRANCH"
    echo ""
    echo "🔗 重要链接:"
    echo "   1. 仓库主页: $GITHUB_URL"
    echo "   2. Issues: $GITHUB_URL/issues"
    echo "   3. Actions: $GITHUB_URL/actions"
    echo "   4. Wiki: $GITHUB_URL/wiki"
    echo ""
    echo "📋 下一步:"
    echo "   1. 设置GitHub Pages (可选)"
    echo "   2. 配置CI/CD Secrets"
    echo "   3. 邀请协作者"
    echo "   4. 创建第一个Release"
    echo ""
    echo "🦊 项目已成功部署到GitHub！"
else
    echo ""
    echo "✅ 部署完成！"
    echo "   远程仓库: $REMOTE_URL"
    echo "   分支: $BRANCH"
fi

echo ""
echo "💡 维护建议:"
echo "   1. 定期提交更改: git add . && git commit -m '更新' && git push"
echo "   2. 使用分支开发: git checkout -b feature/xxx"
echo "   3. 创建Pull Request进行代码审查"
echo "   4. 使用GitHub Issues跟踪问题"
echo "   5. 使用GitHub Actions自动化测试和部署"

echo ""
echo "=" * 60
echo "🦊 BTC量化团队项目已部署到GitHub！"