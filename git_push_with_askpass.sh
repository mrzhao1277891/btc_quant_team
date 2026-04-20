#!/bin/bash
# 使用GIT_ASKPASS环境变量推送

echo "🔑 使用GIT_ASKPASS推送"
echo "=" * 60

# 创建简单的askpass脚本
ASKPASS_SCRIPT="/tmp/git_askpass_$$.sh"

cat > "$ASKPASS_SCRIPT" << 'EOF'
#!/bin/bash
# 简单的askpass脚本
if [ "$1" = "Username for 'https://github.com':" ]; then
    echo "mrzhao1277891"
elif [ "$1" = "Password for 'https://mrzhao1277891@github.com':" ]; then
    echo "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"
else
    echo ""
fi
EOF

chmod +x "$ASKPASS_SCRIPT"

# 设置环境变量
export GIT_ASKPASS="$ASKPASS_SCRIPT"

echo "📋 Askpass脚本已创建: $ASKPASS_SCRIPT"
echo "📋 内容:"
cat "$ASKPASS_SCRIPT"

echo ""
echo "🚀 尝试推送..."
cd /home/francis/btc_quant_team

# 先重置远程URL为普通URL
git remote set-url origin https://github.com/mrzhao1277891/btc_quant_team.git

# 尝试推送
timeout 30 git push -u origin main

# 清理
rm -f "$ASKPASS_SCRIPT"
unset GIT_ASKPASS

echo ""
echo "💡 如果还是失败，可能Token需要特定配置。"