# BTC数据初始化工具

专门为Steve的`btc_assistant`数据库设计的K线数据初始化工具。

## 🎯 功能特点

### 数据采集配置（完全匹配你的要求）
- **4h周期**: 600条K线数据
- **1d周期**: 600条K线数据  
- **1w周期**: 250条K线数据
- **1M周期**: 60条K线数据

### 技术指标计算
- **移动平均线**: EMA7, EMA25, EMA50, EMA12, MA5, MA10
- **MACD指标**: DIF, DEA, MACD（简化版）
- **RSI指标**: RSI14, RSI6

### 智能处理
- **避免重复**: 自动检查已有数据，避免重复采集
- **错误处理**: 网络异常自动重试，单条失败不影响整体
- **性能优化**: 批量插入，避免API限制

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 运行初始化工具
```bash
# 基本使用（会提示输入密码）
python3 btc_data_initializer.py

# 指定密码
python3 btc_data_initializer.py --password your_password

# 强制重新获取所有数据
python3 btc_data_initializer.py --force

# 只显示数据摘要
python3 btc_data_initializer.py --summary
```

### 3. 高级选项
```bash
# 指定数据库连接
python3 btc_data_initializer.py \
  --host localhost \
  --port 3306 \
  --user root \
  --password your_password \
  --database btc_assistant \
  --symbol BTCUSDT
```

## 📊 数据采集逻辑

### 采集策略
1. **检查已有数据**：如果某个周期已有80%以上数据，则跳过
2. **分批获取**：避免API限制，每个周期间隔1秒
3. **计算指标**：获取原始数据后计算技术指标
4. **批量插入**：使用`ON DUPLICATE KEY UPDATE`避免重复

### 数据验证
- 价格合理性检查（开盘价>0，最高价>=最低价等）
- 时间戳验证
- 数据完整性检查

## 🔧 技术实现

### 核心类：`BTCDataInitializer`
```python
class BTCDataInitializer:
    # 主要方法
    - connect()              # 连接数据库
    - fetch_binance_klines() # 从币安获取数据
    - calculate_indicators() # 计算技术指标
    - insert_klines()        # 插入数据到数据库
    - initialize_data()      # 初始化数据主流程
    - show_data_summary()    # 显示数据摘要
```

### 数据库表结构匹配
工具完全匹配你的表结构：
```sql
CREATE TABLE klines (
    `timestamp` BIGINT NOT NULL,
    `symbol` VARCHAR(20) NOT NULL,
    `timeframe` VARCHAR(5) NOT NULL,
    `open` DECIMAL(20,8) DEFAULT NULL,
    `high` DECIMAL(20,8) DEFAULT NULL,
    `low` DECIMAL(20,8) DEFAULT NULL,
    `close` DECIMAL(20,8) DEFAULT NULL,
    `volume` DECIMAL(20,8) DEFAULT NULL,
    `ema7` DECIMAL(20,8) DEFAULT NULL,
    `ema25` DECIMAL(20,8) DEFAULT NULL,
    `ema50` DECIMAL(20,8) DEFAULT NULL,
    `ema12` DECIMAL(20,8) DEFAULT NULL,
    `ma5` DECIMAL(20,8) DEFAULT NULL,
    `ma10` DECIMAL(20,8) DEFAULT NULL,
    `dif` DECIMAL(20,8) DEFAULT NULL,
    `dea` DECIMAL(20,8) DEFAULT NULL,
    `macd` DECIMAL(20,8) DEFAULT NULL,
    `rsi14` DECIMAL(10,4) DEFAULT NULL,
    `rsi6` DECIMAL(10,4) DEFAULT NULL,
    PRIMARY KEY (`timestamp`, `symbol`, `timeframe`)
)
```

## 📈 使用示例

### 示例1：首次初始化
```bash
python3 btc_data_initializer.py
# 输入MySQL密码后自动开始采集
```

### 示例2：查看当前数据状态
```bash
python3 btc_data_initializer.py --summary
```

### 示例3：强制更新所有数据
```bash
python3 btc_data_initializer.py --force --password your_password
```

## 🎨 输出示例

### 正常执行输出
```
🚀 BTC数据初始化工具
   数据库: btc_assistant
   交易对: BTCUSDT
   强制模式: 否
============================================================

📥 开始获取数据...
   配置:
     - 4h周期: 600条
     - 1d周期: 600条
     - 1w周期: 250条
     - 1M周期: 60条

📡 获取数据: BTCUSDT 4h 数量: 600
✅ 获取到 600 条K线数据
📊 插入完成: 新增 600 条, 更新 0 条, 错误 0 条

📡 获取数据: BTCUSDT 1d 数量: 600
✅ 获取到 600 条K线数据
📊 插入完成: 新增 600 条, 更新 0 条, 错误 0 条

📊 数据摘要:
================================================================================
  4h   | 数量:    600 | 最早: 2026-01-01 00:00:00 | 最新: 2026-04-21 16:00:00
  1d   | 数量:    600 | 最早: 2025-08-01 00:00:00 | 最新: 2026-04-21 00:00:00
  1w   | 数量:    250 | 最早: 2021-01-01 00:00:00 | 最新: 2026-04-21 00:00:00
  1M   | 数量:     60 | 最早: 2021-01-01 00:00:00 | 最新: 2026-04-01 00:00:00

📈 最新数据 (10条):
--------------------------------------------------------------------------------
  4h   | 2026-04-21 16:00:00 | 价格: 70,500.00 | 成交量: 100.50 | EMA7: 70,200.00 | RSI14: 65.32
  1d   | 2026-04-21 00:00:00 | 价格: 70,300.00 | 成交量: 500.20 | EMA7: 69,800.00 | RSI14: 62.15

🎉 操作完成!
```

## ⚠️ 注意事项

1. **API限制**：币安API有每分钟1200次限制，工具已做间隔处理
2. **网络要求**：需要能访问币安API的网络环境
3. **数据库权限**：需要MySQL的INSERT和SELECT权限
4. **数据完整性**：首次运行建议使用`--force`参数确保数据完整

## 🔄 后续维护

### 定期更新
```bash
# 每天运行一次更新
python3 btc_data_initializer.py

# 或添加到cron
0 2 * * * cd /path/to/tools && python3 btc_data_initializer.py --password your_password
```

### 监控数据质量
```sql
-- 检查数据完整性
SELECT timeframe, COUNT(*) as count FROM klines GROUP BY timeframe;

-- 检查最新数据时间
SELECT timeframe, MAX(FROM_UNIXTIME(timestamp/1000)) as latest 
FROM klines 
GROUP BY timeframe;
```

## 🆘 故障排除

### 常见问题
1. **连接失败**：检查MySQL服务是否运行，密码是否正确
2. **网络错误**：检查是否能访问币安API（可能需要代理）
3. **权限不足**：确保数据库用户有INSERT权限
4. **数据重复**：使用`ON DUPLICATE KEY UPDATE`避免重复

### 调试模式
```bash
# 查看详细日志
python3 btc_data_initializer.py 2>&1 | tee init.log
```

## 📄 许可证
MIT License - 自由使用和修改