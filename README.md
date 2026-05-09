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

### 回测系统 (backend/backtest/)

#### 🎯 核心功能
- **双向交易策略**: 支持做多和做空的灵活切换 🆕
- **技术指标**: EMA、RSI、MACD、布林带、ATR
- **性能分析**: 总收益、胜率、最大回撤、夏普比率
- **Web UI**: 可视化策略配置和结果展示
- **REST API**: 完整的 FastAPI 后端
- **杠杆支持**: 做多和做空均支持杠杆交易

#### 🚀 双向交易策略 (新功能)

双向交易策略是回测系统的重要升级，允许在同一策略中同时配置做多和做空条件，根据市场情况自动切换交易方向。

**主要特性**:
- ✅ **独立配置**: 为做多和做空分别配置开仓/平仓条件
- ✅ **智能切换**: 根据市场信号自动在多空之间切换
- ✅ **反向处理**: 持有多仓时出现空信号自动先平后开
- ✅ **精确计算**: 正确计算做空盈亏和杠杆效果
- ✅ **向后兼容**: 完全兼容现有单向策略配置

**快速开始**:
```bash
# 1. 启动回测服务
python3 -m uvicorn backend.backtest.api:app --host 127.0.0.1 --port 8001 --reload

# 2. 访问 Web UI
open http://127.0.0.1:8001/backtest.html

# 3. 选择双向策略模板（如"双向RSI策略"）
# 4. 运行回测查看结果
```

**配置示例** (双向RSI策略):
```json
{
  "strategy_name": "双向RSI策略",
  "timeframe": "1d",
  "initial_capital": 10000,
  "position_size": 2000,
  "leverage": 5,
  
  "long_entry_conditions": [
    {"indicator": "rsi14", "operator": "<", "value": 30},
    {"indicator": "close", "operator": ">", "value": "ema50"}
  ],
  "long_entry_logic": "AND",
  "long_take_profit_pct": 10,
  "long_stop_loss_pct": 5,
  
  "short_entry_conditions": [
    {"indicator": "rsi14", "operator": ">", "value": 70},
    {"indicator": "close", "operator": "<", "value": "ema50"}
  ],
  "short_entry_logic": "AND",
  "short_take_profit_pct": 10,
  "short_stop_loss_pct": 5
}
```

**API 使用**:
```bash
# 提交双向策略回测
curl -X POST "http://127.0.0.1:8001/api/backtest" \
  -H "Content-Type: application/json" \
  -d @dual_strategy_config.json

# 查询回测结果
curl "http://127.0.0.1:8001/api/backtest/{backtest_id}/results"
```

**前端 UI 使用**:

Web UI 提供了直观的可视化配置界面，分为四个主要配置区域：

1. **做多开仓条件区域**
   - 点击"添加做多开仓条件"按钮
   - 选择指标（如 rsi14）
   - 选择运算符（如 <）
   - 输入阈值（如 30）
   - 选择逻辑运算符（AND/OR）

2. **做空开仓条件区域**
   - 点击"添加做空开仓条件"按钮
   - 配置方式同做多开仓条件
   - 可以配置完全不同的指标组合

3. **做多平仓条件区域**
   - 添加指标平仓条件（可选）
   - 设置止盈百分比（如 10%）
   - 设置止损百分比（如 5%）

4. **做空平仓条件区域**
   - 配置方式同做多平仓条件
   - 可以为做空设置不同的止盈止损

**UI 操作技巧**:
- 使用"策略模板"快速加载预设策略
- 点击条件右侧的"删除"按钮移除条件
- 留空平仓条件则仅依赖止盈止损和反向信号
- 配置完成后点击"运行回测"查看结果

📖 **详细文档**:
- [双向交易策略完整指南](DUAL_DIRECTION_TRADING_GUIDE.md) - 详细功能说明、配置参数、策略示例
- [双向交易策略快速参考](DUAL_DIRECTION_QUICK_REFERENCE.md) - 快速查询表、常用指标、调试技巧
- [回测系统使用指南](BACKTEST_USAGE_GUIDE.md) - 回测系统基础使用

**常见问题**:

<details>
<summary>Q: 如何配置纯做多或纯做空策略？</summary>

只需配置一个方向的开仓条件即可。例如纯做多：
```json
{
  "long_entry_conditions": [...],
  "long_exit_conditions": [...]
}
```
</details>

<details>
<summary>Q: 做空盈亏如何计算？</summary>

做空盈亏公式：`(开仓价格 - 平仓价格) × 持仓数量`

示例：以50000开空仓，以48000平仓，盈利 = (50000 - 48000) × 持仓数量
</details>

<details>
<summary>Q: 反向信号如何处理？</summary>

当持有多仓时出现做空信号（或持有空仓时出现做多信号），系统会：
1. 先平掉当前仓位
2. 再开新方向的仓位
3. 平仓原因记录为 "reverse_signal"
</details>

<details>
<summary>Q: 旧版单向策略配置还能用吗？</summary>

完全可以！系统会自动转换旧版配置（`position_side`, `entry_conditions`等）到新版字段，无需修改现有策略。
</details>

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

## ❓ 常见问题解答 (FAQ)

### 回测系统相关

<details>
<summary><strong>Q1: 如何启动回测系统？</strong></summary>

```bash
# 启动后端服务
python3 -m uvicorn backend.backtest.api:app --host 127.0.0.1 --port 8001 --reload

# 访问 Web UI
open http://127.0.0.1:8001/backtest.html
```
</details>

<details>
<summary><strong>Q2: 支持哪些技术指标？</strong></summary>

当前支持的指标：
- **趋势指标**: EMA7, EMA12, EMA25, EMA50
- **动量指标**: RSI6, RSI14, MACD (DIF, DEA, MACD)
- **波动率指标**: 布林带 (上轨、中轨、下轨), ATR
- **价格指标**: 收盘价 (close)
- **成交量**: volume
</details>

<details>
<summary><strong>Q3: 如何配置杠杆交易？</strong></summary>

在策略配置中设置 `leverage` 字段：
```json
{
  "leverage": 5,  // 5倍杠杆
  "position_size": 2000  // 本金2000，实际仓位10000
}
```

注意：
- 杠杆会放大收益和风险
- 建议杠杆倍数：1-5倍（保守），5-10倍（激进）
- 保证金 = 持仓价值 / 杠杆倍数
</details>

### 双向交易策略相关

<details>
<summary><strong>Q4: 什么是双向交易策略？</strong></summary>

双向交易策略允许在同一策略中同时配置做多和做空条件，系统会根据市场信号自动选择交易方向。

**优势**：
- 在震荡市场中高抛低吸
- 在趋势市场中跟随趋势
- 提高资金利用率
- 捕捉更多交易机会
</details>

<details>
<summary><strong>Q5: 如何配置双向策略？</strong></summary>

分别配置做多和做空的开仓/平仓条件：

```json
{
  "long_entry_conditions": [
    {"indicator": "rsi14", "operator": "<", "value": 30}
  ],
  "long_take_profit_pct": 10,
  "long_stop_loss_pct": 5,
  
  "short_entry_conditions": [
    {"indicator": "rsi14", "operator": ">", "value": 70}
  ],
  "short_take_profit_pct": 10,
  "short_stop_loss_pct": 5
}
```

详见：[双向交易策略指南](DUAL_DIRECTION_TRADING_GUIDE.md)
</details>

<details>
<summary><strong>Q6: 可以只配置做多或只配置做空吗？</strong></summary>

可以！只需配置一个方向的条件即可：

**纯做多**：
```json
{
  "long_entry_conditions": [...],
  "long_exit_conditions": [...]
}
```

**纯做空**：
```json
{
  "short_entry_conditions": [...],
  "short_exit_conditions": [...]
}
```
</details>

<details>
<summary><strong>Q7: 同时满足做多和做空信号会怎样？</strong></summary>

系统会优先保持当前持仓方向：
- 如果持有多仓，继续持有多仓
- 如果持有空仓，继续持有空仓
- 如果空仓，不会开仓（避免冲突）
</details>

<details>
<summary><strong>Q8: 什么是反向信号处理？</strong></summary>

当持有多仓时出现做空信号（或持有空仓时出现做多信号），系统会：
1. **先平仓**：平掉当前持仓
2. **再开仓**：开新方向的仓位
3. **记录原因**：平仓原因标记为 "reverse_signal"

这确保了策略能够灵活切换方向。
</details>

<details>
<summary><strong>Q9: 做空盈亏如何计算？</strong></summary>

做空盈亏计算公式：
```
盈亏金额 = (开仓价格 - 平仓价格) × 持仓数量
盈亏百分比 = 盈亏金额 / 开仓资金 × 100
```

**示例**：
- 开空仓价格：50000 USDT
- 平空仓价格：48000 USDT
- 持仓数量：0.2 BTC
- 盈利：(50000 - 48000) × 0.2 = 400 USDT

注意：价格下跌时盈利为正，价格上涨时盈利为负。
</details>

<details>
<summary><strong>Q10: 旧版策略配置还能用吗？</strong></summary>

完全可以！系统提供向后兼容性：

**旧版配置**（仍然支持）：
```json
{
  "position_side": "long",
  "entry_conditions": [...],
  "exit_conditions": [...],
  "take_profit_pct": 10,
  "stop_loss_pct": 5
}
```

系统会自动转换为新版字段，无需修改现有策略。
</details>

### 策略优化相关

<details>
<summary><strong>Q11: 如何提高策略胜率？</strong></summary>

**建议**：
1. **添加过滤条件**：使用多个指标组合，提高信号质量
2. **趋势过滤**：在趋势方向上交易（如价格在均线上方做多）
3. **成交量确认**：放量突破更可靠
4. **避免震荡区间**：在明确趋势中交易
5. **优化参数**：测试不同的指标参数组合

示例（添加趋势过滤）：
```json
{
  "long_entry_conditions": [
    {"indicator": "rsi14", "operator": "<", "value": 30},
    {"indicator": "close", "operator": ">", "value": "ema50"}  // 趋势过滤
  ],
  "long_entry_logic": "AND"
}
```
</details>

<details>
<summary><strong>Q12: 如何设置合理的止盈止损？</strong></summary>

**一般原则**：
- **盈亏比**: 止盈应大于止损（建议 2:1 或 3:1）
- **市场波动**: 根据 ATR 调整止损距离
- **时间周期**: 长周期使用更大的止盈止损

**推荐设置**：
- **保守型**: 止盈 5-8%, 止损 2-3%
- **平衡型**: 止盈 10-15%, 止损 5-7%
- **激进型**: 止盈 20-30%, 止损 10-15%

```json
{
  "long_take_profit_pct": 10,  // 10% 止盈
  "long_stop_loss_pct": 5      // 5% 止损（盈亏比 2:1）
}
```
</details>

<details>
<summary><strong>Q13: 如何避免过度拟合？</strong></summary>

**防止过度拟合的方法**：
1. **简单策略优先**：从简单策略开始，逐步优化
2. **样本外测试**：在不同时间段测试策略
3. **多市场验证**：在不同市场环境下测试
4. **避免过多参数**：参数越多，过拟合风险越大
5. **前向测试**：使用最新数据验证策略

**测试流程**：
```
训练期：2023-01-01 至 2023-12-31（优化参数）
验证期：2024-01-01 至 2024-06-30（验证效果）
测试期：2024-07-01 至 2024-12-31（最终测试）
```
</details>

<details>
<summary><strong>Q14: 如何分析回测结果？</strong></summary>

**关键指标**：
- **总收益率**: 整体盈利能力
- **胜率**: 盈利交易占比（建议 >50%）
- **盈亏比**: 平均盈利/平均亏损（建议 >1.5）
- **最大回撤**: 风险控制能力（建议 <20%）
- **夏普比率**: 风险调整后收益（建议 >1.0）
- **交易次数**: 样本量是否充足（建议 >20）

**分析步骤**：
1. 查看总体性能指标
2. 分析交易记录（盈利/亏损分布）
3. 检查最大回撤发生时间
4. 统计平仓原因（止盈/止损/信号）
5. 对比做多和做空表现
</details>

### 技术问题

<details>
<summary><strong>Q15: 如何查看 API 文档？</strong></summary>

启动服务后访问：
```
http://127.0.0.1:8001/docs
```

提供完整的 API 接口文档和在线测试功能。
</details>

<details>
<summary><strong>Q16: 如何查看日志？</strong></summary>

日志文件位置：
```
logs/backtest.log
```

查看实时日志：
```bash
tail -f logs/backtest.log
```
</details>

<details>
<summary><strong>Q17: 遇到错误如何调试？</strong></summary>

**调试步骤**：
1. 查看浏览器控制台（F12）
2. 查看后端日志 `logs/backtest.log`
3. 检查配置是否正确（JSON 格式）
4. 验证指标名称和运算符
5. 确认日期范围和数据可用性

**常见错误**：
- `配置错误`: 检查 JSON 格式和必填字段
- `数据不足`: 扩大日期范围或更换时间周期
- `指标不存在`: 检查指标名称拼写
- `资金不足`: 减小持仓大小或杠杆倍数
</details>

<details>
<summary><strong>Q18: 如何贡献代码？</strong></summary>

欢迎贡献！请遵循以下步骤：
1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

详见：[CONTRIBUTING.md](CONTRIBUTING.md)
</details>

---

**💡 提示**: 如果以上 FAQ 没有解决你的问题，请查看详细文档或在 GitHub Issues 中提问。

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