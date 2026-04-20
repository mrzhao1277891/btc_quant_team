#!/bin/bash
# 设置Git凭据

echo "🔐 设置Git凭据"
echo "=" * 60

# 创建凭据文件
CREDENTIALS_FILE="$HOME/.git-credentials"

# 添加GitHub凭据
echo "https://mrzhao1277891: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@github.com" > "$CREDENTIALS_FILE"

# 设置权限
chmod 600 "$CREDENTIALS_FILE"

echo "✅ 凭据文件已创建: $CREDENTIALS_FILE"
echo "📋 内容:"
cat "$CREDENTIALS_FILE"

# 配置Git使用凭据存储
git config --global credential.helper store

echo ""
echo "🚀 现在尝试推送..."
cd /home/francis/btc_quant_team
git push -u origin main