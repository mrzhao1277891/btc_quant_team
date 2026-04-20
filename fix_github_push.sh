#!/bin/bash
# 修复GitHub推送问题

echo "🦊 修复GitHub推送问题"
echo "=" * 60

# 检查当前配置
echo "🔍 检查Git配置:"
echo "   远程仓库: $(git remote get-url origin)"
echo "   用户名: $(git config user.name)"
echo "   邮箱: $(git config user.email)"
echo ""

# 检查网络连接
echo "🌐 检查网络连接..."
if ping -c 1 github.com &> /dev/null; then
    echo "✅ GitHub可访问"
else
    echo "❌ 无法访问GitHub，检查网络"
    exit 1
fi

# 提供解决方案
echo ""
echo "🔧 解决方案 (选择一种):"
echo ""
echo "1. 🔑 使用SSH密钥 (推荐)"
echo "   git remote set-url origin git@github.com:mrzhao1277891/btc_quant_team.git"
echo ""
echo "2. 🔐 使用Personal Access Token (PAT)"
echo "   在GitHub Settings → Developer settings → Personal access tokens"
echo "   生成token，然后使用:"
echo "   git remote set-url origin https://mrzhao1277891:YOUR_TOKEN@github.com/mrzhao1277891/btc_quant_team.git"
echo ""
echo "3. 💻 使用Git Credential Manager"
echo "   git config --global credential.helper store"
echo "   然后重新推送，输入用户名和密码/token"
echo ""
echo "4. 🚀 使用GitHub CLI"
echo "   gh auth login"
echo "   然后重新推送"
echo ""

# 检查SSH密钥
echo "🔑 检查SSH密钥配置..."
if [ -f ~/.ssh/id_rsa.pub ]; then
    echo "✅ 找到SSH公钥: ~/.ssh/id_rsa.pub"
    echo "   密钥指纹: $(ssh-keygen -lf ~/.ssh/id_rsa.pub)"
else
    echo "❌ 未找到SSH密钥"
    echo "   生成SSH密钥: ssh-keygen -t rsa -b 4096 -C \"your_email@example.com\""
fi

# 测试SSH连接
echo ""
echo "🔌 测试SSH连接..."
if ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
    echo "✅ SSH密钥已配置并认证成功"
    USE_SSH=true
else
    echo "❌ SSH认证失败"
    USE_SSH=false
fi

echo ""
echo "🚀 推荐方案:"
if [ "$USE_SSH" = true ]; then
    echo "   使用SSH方式 (已配置)"
    echo "   git remote set-url origin git@github.com:mrzhao1277891/btc_quant_team.git"
else
    echo "   使用Personal Access Token (更简单)"
    echo "   1. 生成PAT: https://github.com/settings/tokens"
    echo "   2. 选择权限: repo (全部)"
    echo "   3. 使用命令:"
    echo "      git remote set-url origin https://mrzhao1277891:YOUR_TOKEN@github.com/mrzhao1277891/btc_quant_team.git"
fi

echo ""
echo "📋 立即修复命令:"
echo "   # 方法1: 使用SSH (如果已配置SSH密钥)"
echo "   git remote set-url origin git@github.com:mrzhao1277891/btc_quant_team.git"
echo ""
echo "   # 方法2: 使用缓存凭据"
echo "   git config --global credential.helper 'cache --timeout=3600'"
echo "   git push -u origin main"
echo ""
echo "   # 方法3: 使用store保存凭据"
echo "   git config --global credential.helper store"
echo "   git push -u origin main"
echo "   # 第一次会提示输入用户名和密码/token，之后会自动保存"

echo ""
echo "💡 提示:"
echo "   - 如果使用密码，需要GitHub Personal Access Token，不是登录密码"
echo "   - Token生成: Settings → Developer settings → Personal access tokens → Generate new token"
echo "   - 选择权限: repo (全部权限)"
echo "   - 复制token，推送时作为密码使用"

echo ""
echo "🦊 选择适合你的方案执行命令即可！"