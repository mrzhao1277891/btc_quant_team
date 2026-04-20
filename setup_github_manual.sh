#!/bin/bash
# 手动设置GitHub仓库

echo "🦊 手动设置GitHub仓库"
echo "=" * 60

# 设置Git配置
git config user.name "Francis Zhao"
git config user.email "francis@example.com"

# 添加所有文件
echo "📝 添加文件到Git..."
git add .

# 提交初始版本
echo "💾 提交初始版本..."
git commit -m "初始提交: BTC量化团队项目 v1.0.0

🎯 项目概述:
- 专业的加密货币量化分析工程
- 清晰的模块化架构设计
- 完整的工具链和Skill集
- 自动化数据质量监控
- Telegram Bot集成
- 多时间框架分析系统

📊 功能模块:
- 工具层: 数据、质量、指标、分析工具
- Skill层: BTC监控、市场分析、数据质量、交易信号
- 服务层: Telegram前端、数据更新、监控服务
- 核心层: 业务逻辑、算法实现

🚀 技术特性:
- Python 3.9+ 类型提示
- 严格的模块依赖管理
- 完整的测试套件
- CI/CD自动化
- 详细的文档

🦊 由Steve量化助手设计架构"

echo "✅ 本地Git仓库设置完成"
echo ""
echo "📋 下一步:"
echo "   1. 在GitHub创建新仓库: https://github.com/new"
echo "   2. 仓库名称: btc_quant_team"
echo "   3. 描述: 专业的加密货币量化分析工程"
echo "   4. 选择公开 (Public)"
echo "   5. 不要初始化README、.gitignore或LICENSE"
echo ""
echo "🔗 创建仓库后，运行以下命令:"
echo "   git remote add origin https://github.com/YOUR_USERNAME/btc_quant_team.git"
echo "   git push -u origin main"
echo ""
echo "🎉 然后你的项目就会在GitHub上了！"