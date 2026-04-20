# 📦 OpenClaw Skill集

## 📋 概述
标准化的OpenClaw Skill集合，每个Skill都是完整的工作流解决方案。

## 🏗️ Skill架构
```
skills/
├── btc-monitor/          # BTC监控Skill
│   ├── SKILL.md         # Skill文档
│   ├── scripts/         # 执行脚本
│   ├── references/      # 参考资料
│   └── examples/        # 使用示例
├── market-analysis/      # 市场分析Skill
├── data-quality/         # 数据质量Skill
└── trading-signal/       # 交易信号Skill
```

## 🚀 快速使用

### 安装Skill到OpenClaw
```bash
# 方法1: 符号链接 (开发)
ln -s ~/btc_quant_team/skills/btc-monitor ~/.openclaw/skills/

# 方法2: 复制 (生产)
cp -r ~/btc_quant_team/skills/btc-monitor ~/.openclaw/skills/

# 方法3: 通过OpenClaw CLI
openclaw skill install ~/btc_quant_team/skills/btc-monitor
```

### 使用Skill
```bash
# 查看可用Skill
openclaw skill list

# 运行BTC监控Skill
openclaw skill run btc-monitor --low 70000 --high 75000 --interval 5

# 查看Skill帮助
openclaw skill help btc-monitor
```

## 📊 Skill目录

### 1. BTC监控Skill (`btc-monitor/`)
**功能**: BTC价格监控和报警
**触发**: 用户说"监控BTC"或定时任务
**输入**: 价格阈值、监控间隔、通知方式
**输出**: 监控状态、价格报警

**使用示例**:
```bash
# 设置监控
openclaw skill run btc-monitor --low 69000 --high 73000

# 查看状态
openclaw skill run btc-monitor --action status

# 停止监控
openclaw skill run btc-monitor --action stop
```

### 2. 市场分析Skill (`market-analysis/`)
**功能**: 多时间框架市场分析
**触发**: 用户说"分析市场"或每日定时
**输入**: 交易对、时间框架、分析深度
**输出**: 分析报告、交易建议

**使用示例**:
```bash
# 快速分析
openclaw skill run market-analysis --symbol BTCUSDT

# 深度分析
openclaw skill run market-analysis --symbol BTCUSDT --timeframes 4h,1d,1w --depth detailed

# 生成报告
openclaw skill run market-analysis --symbol BTCUSDT --output report.md
```

### 3. 数据质量Skill (`data-quality/`)
**功能**: 数据质量检查和修复
**触发**: 用户说"检查数据"或定时检查
**输入**: 数据源、检查项目、修复选项
**输出**: 质量报告、修复结果

**使用示例**:
```bash
# 检查数据质量
openclaw skill run data-quality --check completeness,freshness,consistency

# 自动修复问题
openclaw skill run data-quality --check all --auto-fix

# 生成质量报告
openclaw skill run data-quality --report --output quality_report.json
```

### 4. 交易信号Skill (`trading-signal/`)
**功能**: 交易信号生成和验证
**触发**: 价格变动或技术指标信号
**输入**: 策略参数、风险偏好、资金规模
**输出**: 交易信号、风险分析、执行建议

**使用示例**:
```bash
# 检查当前信号
openclaw skill run trading-signal --check

# 回测策略
openclaw skill run trading-signal --backtest --days 30

# 模拟交易
openclaw skill run trading-signal --simulate --capital 10000
```

## 🔧 开发新Skill

### Skill标准结构
```
skill-name/
├── SKILL.md          # Skill文档 (必须)
├── scripts/          # 执行脚本目录
│   └── main.py      # 主执行脚本
├── references/       # 参考资料
│   └── README.md    # 参考文档
├── examples/         # 使用示例
│   └── basic_usage.md
└── tests/           # 测试文件 (可选)
    └── test_skill.py
```

### SKILL.md 模板
```markdown
# Skill名称

## 描述
简要描述Skill的功能和用途。

## 何时使用
- 场景1: 当用户想要...
- 场景2: 当需要自动...
- 场景3: 定时任务...

## 安装
```bash
openclaw skill install path/to/skill
```

## 使用
### 基本用法
```bash
openclaw skill run skill-name --param value
```

### 参数说明
| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `--symbol` | string | BTCUSDT | 交易对 |
| `--action` | string | monitor | 执行动作 |

### 示例
```bash
# 示例1
openclaw skill run skill-name --low 70000 --high 75000

# 示例2
openclaw skill run skill-name --action status
```

## 输出
描述Skill的输出格式和内容。

## 依赖
- Python包: requests, pandas
- 系统工具: cron, systemd
- 其他Skill: data-quality

## 配置
描述需要的配置文件和环境变量。

## 故障排除
常见问题和解决方案。

## 版本历史
- v1.0.0: 初始版本
```

### 创建新Skill步骤
1. 创建Skill目录: `mkdir -p skills/new-skill/{scripts,references,examples}`
2. 编写SKILL.md文档
3. 创建主脚本: `scripts/main.py`
4. 添加参考资料和示例
5. 测试Skill: `openclaw skill run new-skill --test`
6. 发布到Skill仓库

## 🔗 与工具层集成

### Skill调用工具示例
```python
# skills/btc-monitor/scripts/main.py
import sys
import json
from pathlib import Path

# 添加工具路径
sys.path.append(str(Path(__file__).parent.parent.parent / 'tools'))

from tools.data.fetch import fetch_klines
from tools.analysis.technical import analyze_trend

def main():
    # 解析参数
    args = parse_args()
    
    # 调用工具函数
    data = fetch_klines(args.symbol, args.timeframe)
    analysis = analyze_trend(data)
    
    # 生成输出
    output = {
        'status': 'success',
        'data': analysis,
        'timestamp': get_current_time()
    }
    
    print(json.dumps(output, indent=2))

if __name__ == '__main__':
    main()
```

## 🧪 测试Skill
```bash
# 测试单个Skill
cd skills/btc-monitor
python scripts/main.py --test

# 集成测试
openclaw skill run btc-monitor --test-mode

# 通过OpenClaw测试
openclaw skill test btc-monitor
```

## 📚 文档生成
```bash
# 生成Skill文档索引
python scripts/generate_skill_index.py

# 查看所有Skill文档
open docs/skills/index.html
```

## 🔄 发布流程
1. 开发完成并测试
2. 更新版本号
3. 生成文档
4. 打包Skill: `tar -czf btc-monitor-v1.0.0.tar.gz btc-monitor/`
5. 发布到Skill仓库
6. 更新Skill索引

---

**🦊 设计: Steve量化助手** | **标准: OpenClaw Skill规范** | **目标: 可复用工作流**