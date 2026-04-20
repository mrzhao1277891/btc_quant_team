# 🦊 BTC量化团队工程

[![GitHub License](https://img.shields.io/github/license/franciszhao/btc_quant_team)](https://github.com/franciszhao/btc_quant_team/blob/main/LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![GitHub Issues](https://img.shields.io/github/issues/franciszhao/btc_quant_team)](https://github.com/franciszhao/btc_quant_team/issues)
[![GitHub Stars](https://img.shields.io/github/stars/franciszhao/btc_quant_team)](https://github.com/franciszhao/btc_quant_team/stargazers)

## 🎯 项目概述
专业的加密货币量化分析工程，采用清晰的模块化架构设计。

## 📦 快速链接
- **GitHub仓库**: https://github.com/franciszhao/btc_quant_team
- **文档**: [docs/](docs/) | [GitHub Pages](https://franciszhao.github.io/btc_quant_team/)
- **问题跟踪**: [GitHub Issues](https://github.com/franciszhao/btc_quant_team/issues)
- **讨论区**: [GitHub Discussions](https://github.com/franciszhao/btc_quant_team/discussions)
- **发布版本**: [GitHub Releases](https://github.com/franciszhao/btc_quant_team/releases)

## 🏗️ 架构设计
```
btc_quant_team/                 # 量化总部
├── tools/                      # 专业工具库 (可独立)
├── skills/                     # OpenClaw Skill集 (可分享)
├── services/                   # 后台服务 (可部署)
├── core/                       # 核心业务逻辑 (无依赖)
├── ports/                      # 接口定义 (协议)
├── adapters/                   # 适配器实现 (外部集成)
├── apps/                       # 应用层 (CLI/Web)
├── config/                     # 配置管理
├── docs/                       # 文档中心
├── tests/                      # 测试套件
├── scripts/                    # 运维脚本
└── logs/                       # 日志文件
```

## 🚀 快速开始

### 环境设置
```bash
# 1. 克隆项目
git clone <repository-url>
cd btc_quant_team

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境
cp config/development.yaml.example config/development.yaml
# 编辑配置文件，添加API密钥等
```

### 基本使用
```python
# 使用工具库
from tools.data.fetch import fetch_klines
data = fetch_klines("BTCUSDT", "4h", 500)

# 使用Skill (通过OpenClaw)
openclaw skill run btc-monitor --low 70000 --high 75000
```

## 📊 功能模块

### 工具层 (tools/)
- **数据工具**: 数据获取、存储、同步
- **质量工具**: 完整性、一致性、新鲜度检查
- **指标工具**: 技术指标计算 (EMA, MACD, RSI等)
- **分析工具**: 技术分析、支撑阻力分析
- **风险工具**: 风险计算、仓位管理
- **通用工具**: 时间处理、数学计算、格式化

### Skill层 (skills/)
- **BTC监控Skill**: 价格监控和报警
- **市场分析Skill**: 多时间框架分析
- **数据质量Skill**: 数据质量检查和报告
- **交易信号Skill**: 交易信号生成和验证

### 服务层 (services/)
- **Telegram前端**: 用户交互服务
- **数据更新服务**: 定时数据同步
- **监控服务**: 7x24小时市场监控
- **API网关**: 统一API接口

## 🔧 开发指南

### 代码规范
- 使用类型提示 (Type Hints)
- 遵循PEP 8规范
- 每个函数必须有文档字符串
- 公共API必须有单元测试

### 模块依赖规则
```
tools.data → tools.utils ✅
tools.quality → tools.data ✅
tools.indicators → tools.data ✅
tools.indicators → tools.quality ❌ (禁止跨模块依赖)
```

### 测试要求
```bash
# 运行所有测试
pytest tests/

# 运行单元测试
pytest tests/unit/

# 运行集成测试
pytest tests/integration/

# 生成测试报告
pytest --cov=tools --cov-report=html
```

## 📈 部署指南

### 开发环境
```bash
# 启动开发服务
./scripts/start_dev.sh
```

### 生产环境
```bash
# 使用Docker部署
docker-compose up -d

# 或使用系统服务
sudo systemctl start btc-quant-team
```

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

## 📄 许可证
MIT License - 详见 LICENSE 文件

## 🆘 支持
- 问题报告: GitHub Issues
- 讨论: GitHub Discussions
- 文档: docs/ 目录

## 🚀 GitHub部署

### 一键部署到GitHub
```bash
# 运行部署脚本
chmod +x scripts/deploy_to_github.sh
./scripts/deploy_to_github.sh
```

### 详细部署指南
查看完整部署指南: [GITHUB_SETUP_GUIDE.md](GITHUB_SETUP_GUIDE.md)

### GitHub功能
- ✅ **CI/CD**: 自动测试和部署
- ✅ **代码审查**: Pull Request流程
- ✅ **项目管理**: Issues和Projects
- ✅ **文档站点**: GitHub Pages
- ✅ **社区协作**: Discussions和Wiki
- ✅ **安全扫描**: CodeQL和Dependabot

---

**🦊 由Steve量化助手设计架构** | **版本: 1.0.0** | **更新: 2026-04-19** | **GitHub就绪** 🚀