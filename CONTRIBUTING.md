# 贡献指南

感谢你考虑为BTC量化团队项目做出贡献！本指南将帮助你了解如何参与贡献。

## 🎯 贡献方式

### 1. 报告Bug
如果你发现了bug，请：
1. 搜索[现有issue](https://github.com/franciszhao/btc_quant_team/issues)确认是否已报告
2. 使用[bug报告模板](.github/ISSUE_TEMPLATE/bug_report.md)创建新issue
3. 提供详细的重现步骤和环境信息

### 2. 请求新功能
如果你有功能建议，请：
1. 搜索[现有issue](https://github.com/franciszhao/btc_quant_team/issues)确认是否已提出
2. 使用[功能请求模板](.github/ISSUE_TEMPLATE/feature_request.md)创建新issue
3. 详细描述使用场景和预期效果

### 3. 提交代码
如果你想贡献代码，请：
1. Fork项目仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

## 🏗️ 开发环境设置

### 1. 克隆项目
```bash
git clone https://github.com/franciszhao/btc_quant_team.git
cd btc_quant_team
```

### 2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 开发依赖
```

### 4. 安装预提交钩子
```bash
pre-commit install
```

## 📝 代码规范

### 1. 代码风格
- 遵循[PEP 8](https://www.python.org/dev/peps/pep-0008/)规范
- 使用[Black](https://github.com/psf/black)自动格式化
- 使用[isort](https://github.com/PyCQA/isort)排序导入
- 行长度限制为120个字符

### 2. 类型提示
- 所有公共API必须使用类型提示
- 使用Python 3.9+的类型提示语法
- 复杂类型使用`typing`模块

### 3. 文档字符串
- 所有公共函数必须有文档字符串
- 使用Google风格文档字符串
- 包含参数、返回值和异常说明

### 4. 提交消息
- 使用[约定式提交](https://www.conventionalcommits.org/)
- 格式：`<type>(<scope>): <description>`
- 类型：feat, fix, docs, style, refactor, test, chore

## 🧪 测试要求

### 1. 测试覆盖率
- 核心功能测试覆盖率不低于80%
- 公共API必须有单元测试
- 集成测试覆盖主要工作流

### 2. 运行测试
```bash
# 运行所有测试
pytest

# 运行特定模块测试
pytest tests/unit/tools/

# 运行测试并生成覆盖率报告
pytest --cov=tools --cov-report=html

# 运行性能测试
pytest tests/performance/ -v
```

### 3. 测试编写指南
- 测试函数名以`test_`开头
- 使用描述性的测试名称
- 每个测试只测试一个功能
- 使用fixture管理测试数据

## 🔧 项目结构

### 模块依赖规则
```
tools/
├── data/          # 数据层 (无依赖)
├── utils/         # 工具层 (可依赖data)
├── quality/       # 质量层 (可依赖data, utils)
├── indicators/    # 指标层 (可依赖data, utils)
└── analysis/      # 分析层 (可依赖所有下层)
```

### 禁止的依赖
- 禁止循环依赖
- 禁止跨模块直接依赖
- 禁止工具层依赖业务层

## 📦 发布流程

### 1. 版本管理
- 使用[语义化版本](https://semver.org/)
- 主版本号：不兼容的API修改
- 次版本号：向下兼容的功能新增
- 修订号：向下兼容的问题修正

### 2. 发布步骤
1. 更新CHANGELOG.md
2. 更新版本号
3. 运行完整测试套件
4. 创建发布标签
5. 生成发布说明

### 3. 版本号更新
```bash
# 更新pyproject.toml中的版本号
version = "1.0.0"

# 创建发布标签
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

## 🤝 社区准则

### 1. 行为准则
- 尊重所有贡献者
- 建设性讨论
- 包容不同观点
- 专业沟通

### 2. 沟通渠道
- **问题讨论**: GitHub Issues
- **功能建议**: GitHub Discussions
- **代码审查**: Pull Requests
- **即时沟通**: [可选：Discord/Slack]

### 3. 获取帮助
- 查看[文档](docs/)
- 搜索[现有issue](https://github.com/franciszhao/btc_quant_team/issues)
- 在[Discussions](https://github.com/franciszhao/btc_quant_team/discussions)提问

## 📄 许可证

本项目采用MIT许可证。贡献者同意其贡献将在同一许可证下发布。

## 🙏 致谢

感谢所有为项目做出贡献的人！你的每一份贡献都让项目变得更好。

---

**🦊 由Steve量化助手维护** | **最后更新: 2026-04-19**