# 🚀 数据质量专家 - 快速开始指南

## 📋 概述
数据质量专家是一个专业的加密货币数据质量管理和监控系统。本指南将帮助你在5分钟内开始使用。

## 🎯 核心功能概览

### 🔍 数据质量检查
- **完整性**: 检测缺失数据
- **一致性**: 验证数据格式
- **准确性**: 检测异常值
- **及时性**: 监控数据更新

### 🚨 异常检测
- **统计异常**: Z-Score, IQR检测
- **模式异常**: 聚类分析
- **时间序列异常**: 季节性分解
- **相关性异常**: 多资产关联

### 🔧 数据修复
- **缺失值填充**: 智能插值
- **异常值修正**: 合理修正
- **格式标准化**: 统一格式
- **数据验证**: 修复验证

### 📈 质量监控
- **实时监控**: 实时质量检查
- **定期报告**: 自动报告生成
- **告警系统**: 异常告警
- **趋势分析**: 质量趋势跟踪

## 🚀 5分钟快速开始

### 步骤1: 准备环境
```bash
# 1. 进入技能目录
cd /home/francis/btc_quant_team/skills/data-quality

# 2. 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate

# 3. 安装基础依赖
pip3 install pandas numpy matplotlib scipy
```

### 步骤2: 基础配置
```bash
# 1. 创建配置文件目录
mkdir -p config/checks config/thresholds

# 2. 创建基础配置文件
cat > config/default.yaml << 'EOF'
data_sources:
  primary:
    type: "sqlite"
    path: "crypto_analyzer/data/ultra_light.db"
    table: "klines"

quality_checks:
  enable_completeness: true
  enable_consistency: true
  enable_accuracy: true
  enable_timeliness: true

anomaly_detection:
  sensitivity: 0.95

monitoring:
  check_interval_minutes: 60
EOF
```

### 步骤3: 运行第一个检查
```python
# 创建测试脚本 test_basic.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 创建模拟数据
dates = pd.date_range(start='2024-01-01', end='2024-04-19', freq='D')
data = pd.DataFrame({
    'timestamp': dates,
    'open': np.random.normal(70000, 5000, len(dates)),
    'high': np.random.normal(71000, 5000, len(dates)),
    'low': np.random.normal(69000, 5000, len(dates)),
    'close': np.random.normal(70500, 5000, len(dates)),
    'volume': np.random.normal(1000, 200, len(dates))
})

# 添加一些异常
data.loc[50, 'close'] = 100000  # 价格异常
data.loc[100, 'volume'] = 0     # 成交量异常
data = data.drop([30, 31])      # 缺失数据

print("📊 模拟数据创建完成")
print(f"数据形状: {data.shape}")
print(f"时间范围: {data['timestamp'].min()} 到 {data['timestamp'].max()}")
print(f"缺失值数量: {data.isnull().sum().sum()}")
```

### 步骤4: 基础质量检查
```python
# 创建基础检查器 basic_checker.py
class BasicDataQualityChecker:
    def __init__(self):
        self.results = {}
    
    def check_completeness(self, data):
        """检查数据完整性"""
        total_rows = len(data)
        missing_rows = data.isnull().any(axis=1).sum()
        completeness = 1 - (missing_rows / total_rows)
        
        return {
            'total_rows': total_rows,
            'missing_rows': missing_rows,
            'completeness_score': completeness,
            'status': 'PASS' if completeness > 0.95 else 'FAIL'
        }
    
    def check_consistency(self, data):
        """检查数据一致性"""
        # 检查价格逻辑: high >= low, high >= close >= low
        price_logic_errors = 0
        for _, row in data.iterrows():
            if row['high'] < row['low'] or row['close'] < row['low'] or row['close'] > row['high']:
                price_logic_errors += 1
        
        consistency = 1 - (price_logic_errors / len(data))
        
        return {
            'price_logic_errors': price_logic_errors,
            'consistency_score': consistency,
            'status': 'PASS' if consistency > 0.98 else 'FAIL'
        }
    
    def check_accuracy(self, data):
        """检查数据准确性"""
        # 使用Z-Score检测异常值
        from scipy import stats
        z_scores = np.abs(stats.zscore(data['close'].dropna()))
        anomalies = np.sum(z_scores > 3)
        
        accuracy = 1 - (anomalies / len(data))
        
        return {
            'anomalies_detected': int(anomalies),
            'accuracy_score': accuracy,
            'status': 'PASS' if accuracy > 0.95 else 'FAIL'
        }
    
    def check_all(self, data):
        """执行所有检查"""
        self.results['completeness'] = self.check_completeness(data)
        self.results['consistency'] = self.check_consistency(data)
        self.results['accuracy'] = self.check_accuracy(data)
        
        # 计算总体评分
        scores = [r['completeness_score'] for r in self.results.values() if 'completeness_score' in r]
        overall_score = np.mean(scores) if scores else 0
        
        self.results['overall'] = {
            'score': overall_score,
            'status': 'PASS' if overall_score > 0.90 else 'FAIL'
        }
        
        return self.results
    
    def print_summary(self):
        """打印检查结果摘要"""
        print("=" * 60)
        print("📊 数据质量检查结果")
        print("=" * 60)
        
        for check_name, result in self.results.items():
            if check_name == 'overall':
                continue
                
            score = result.get('score', result.get('completeness_score', 0))
            status = result.get('status', 'UNKNOWN')
            
            print(f"{check_name.upper():15} {score:.1%} [{status}]")
            
            # 显示详细信息
            for key, value in result.items():
                if key not in ['score', 'completeness_score', 'status']:
                    print(f"  {key}: {value}")
        
        print("-" * 60)
        overall = self.results.get('overall', {})
        print(f"总体评分: {overall.get('score', 0):.1%} [{overall.get('status', 'UNKNOWN')}]")
        print("=" * 60)

# 使用示例
checker = BasicDataQualityChecker()
results = checker.check_all(data)
checker.print_summary()
```

## 📖 常用命令

### 数据质量检查命令
```bash
# 基础检查
data-quality check --symbol BTCUSDT
data-quality check --symbol BTCUSDT --timeframe 1d
data-quality check --symbol BTCUSDT --timeframe 1d --days 365

# 全面检查
data-quality check-comprehensive --symbol BTCUSDT
data-quality check-comprehensive --symbol BTCUSDT --include-anomaly

# 批量检查
data-quality check-batch --symbols BTCUSDT,ETHUSDT,BNBUSDT
data-quality check-batch --symbols BTCUSDT,ETHUSDT --timeframes 1d,4h
```

### 异常检测命令
```bash
# 异常检测
data-quality detect-anomalies --symbol BTCUSDT
data-quality detect-anomalies --symbol BTCUSDT --method statistical
data-quality detect-anomalies --symbol BTCUSDT --method timeseries

# 异常分析
data-quality analyze-anomalies --symbol BTCUSDT
data-quality analyze-anomalies --symbol BTCUSDT --output anomalies.json

# 异常报告
data-quality anomaly-report --symbol BTCUSDT
data-quality anomaly-report --symbol BTCUSDT --detailed
```

### 数据修复命令
```bash
# 数据修复
data-quality repair --symbol BTCUSDT
data-quality repair --symbol BTCUSDT --fix-missing
data-quality repair --symbol BTCUSDT --fix-anomalies

# 修复验证
data-quality validate-repair --symbol BTCUSDT
data-quality validate-repair --symbol BTCUSDT --compare-original

# 修复报告
data-quality repair-report --symbol BTCUSDT
data-quality repair-report --symbol BTCUSDT --include-before-after
```

### 质量监控命令
```bash
# 启动监控
data-quality monitor-start --symbol BTCUSDT
data-quality monitor-start --symbols BTCUSDT,ETHUSDT --interval 30

# 监控状态
data-quality monitor-status
data-quality monitor-status --symbol BTCUSDT

# 停止监控
data-quality monitor-stop
data-quality monitor-stop --symbol BTCUSDT
```

### 报告生成命令
```bash
# 质量报告
data-quality report --symbol BTCUSDT
data-quality report --symbol BTCUSDT --type detailed
data-quality report --symbol BTCUSDT --type executive

# 趋势报告
data-quality trend-report --symbol BTCUSDT
data-quality trend-report --symbol BTCUSDT --period 90d

# 批量报告
data-quality batch-report --symbols BTCUSDT,ETHUSDT
data-quality batch-report --symbols BTCUSDT,ETHUSDT --output-dir reports/
```

## 🎯 使用示例

### 示例1: 每日数据质量工作流
```bash
# 1. 检查数据质量
data-quality check --symbol BTCUSDT --timeframe 1d --days 30

# 2. 检测异常
data-quality detect-anomalies --symbol BTCUSDT --method statistical

# 3. 修复数据（如果需要）
data-quality repair --symbol BTCUSDT --fix-missing --fix-anomalies

# 4. 生成报告
data-quality report --symbol BTCUSDT --type daily --output reports/btc_daily_quality.md
```

### 示例2: 实时质量监控
```python
from scripts.quality_monitor import QualityMonitor

# 创建监控器
monitor = QualityMonitor()

# 配置监控
monitor.configure(
    symbols=["BTCUSDT", "ETHUSDT"],
    timeframes=["1d", "4h"],
    check_interval_minutes=30,
    alert_threshold=0.90
)

# 启动监控
monitor.start()

# 获取当前状态
status = monitor.get_status()
print(f"监控状态: {status.state}")
print(f"检查次数: {status.checks_completed}")
print(f"发现问题: {status.issues_found}")

# 停止监控
monitor.stop()
```

### 示例3: 完整的数据修复流程
```python
from scripts.data_quality_checker import DataQualityChecker
from scripts.anomaly_detector import AnomalyDetector
from scripts.data_repair_tool import DataRepairTool
from scripts.report_generator import ReportGenerator

def complete_data_repair_workflow(symbol, timeframe="1d", days=365):
    """完整的数据修复工作流"""
    
    # 1. 创建工具实例
    checker = DataQualityChecker()
    detector = AnomalyDetector()
    repair_tool = DataRepairTool()
    report_gen = ReportGenerator()
    
    print(f"🔍 开始数据修复工作流: {symbol}")
    
    # 2. 检查数据质量
    print("步骤1: 检查数据质量...")
    quality_results = checker.check_comprehensive(symbol, timeframe, days)
    
    if quality_results.overall_score > 0.95:
        print(f"✅ 数据质量良好 ({quality_results.overall_score:.1%})，无需修复")
        return quality_results
    
    print(f"⚠️  数据质量需要改善 ({quality_results.overall_score:.1%})")
    
    # 3. 检测异常
    print("步骤2: 检测异常...")
    anomalies = detector.detect_anomalies(symbol, timeframe, days)
    
    if anomalies:
        print(f"🚨 检测到 {len(anomalies)} 个异常")
    
    # 4. 执行修复
    print("步骤3: 执行数据修复...")
    repaired_data = repair_tool.repair_data(
        symbol=symbol,
        timeframe=timeframe,
        days=days,
        fix_missing=True,
        fix_anomalies=True,
        anomalies=anomalies
    )
    
    # 5. 验证修复
    print("步骤4: 验证修复结果...")
    validation = repair_tool.validate_repair(repaired_data)
    
    if validation.passed:
        print("✅ 修复验证通过")
    else:
        print("❌ 修复验证失败")
    
    # 6. 生成报告
    print("步骤5: 生成修复报告...")
    report = report_gen.generate_repair_report(
        symbol=symbol,
        original_quality=quality_results,
        anomalies=anomalies,
        repaired_data=repaired_data,
        validation=validation
    )
    
    report.save(f"reports/{symbol}_repair_report.md")
    print(f"📄 报告已保存: reports/{symbol}_repair_report.md")
    
    return {
        'original_quality': quality_results,
        'anomalies': anomalies,
        'repaired_data': repaired_data,
        'validation': validation,
        'report': report
    }

# 使用示例
results = complete_data_repair_workflow("BTCUSDT", "1d", 90)
```

### 示例4: 集成到交易系统
```python
from scripts.data_quality_checker import DataQualityChecker
from trading_system import TradingSystem

class QualityAwareTradingSystem:
    """数据质量感知的交易系统"""
    
    def __init__(self, min_quality_score=0.90):
        self.trading_system = TradingSystem()
        self.quality_checker = DataQualityChecker()
        self.min_quality_score = min_quality_score
        self.quality_cache = {}
    
    def check_data_quality(self, symbol, timeframe="1d", days=30):
        """检查数据质量"""
        if symbol in self.quality_cache:
            # 使用缓存
            cached = self.quality_cache[symbol]
            if cached['timestamp'] > datetime.now() - timedelta(hours=1):
                return cached['quality']
        
        # 执行质量检查
        quality = self.quality_checker.check_comprehensive(symbol, timeframe, days)
        
        # 更新缓存
        self.quality_cache[symbol] = {
            'quality': quality,
            'timestamp': datetime.now()
        }
        
        return quality
    
    def execute_trade(self, symbol, signal):
        """执行交易（带质量检查）"""
        # 检查数据质量
        quality = self.check_data_quality(symbol)
        
        if quality.overall_score < self.min_quality_score:
            print(f"⏸️  跳过交易: 数据质量不足 ({quality.overall_score:.1%} < {self.min_quality_score:.1%})")
            
            # 记录质量警告
            self.log_quality_warning(symbol, quality)
            return None
        
        # 数据质量可接受，执行交易
        print(f"✅ 数据质量可接受 ({quality.overall_score:.1%})，执行交易")
        result = self.trading_system.execute(signal)
        
        return result
    
    def log_quality_warning(self, symbol, quality):
        """记录质量警告"""
        warning = {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'quality_score': quality.overall_score,
            'min_required': self.min_quality_score,
            'details': quality.get_details()
        }
        
        # 保存到日志
        with open('quality_warnings.log', 'a') as f:
            f.write(json.dumps(warning) + '\n')
        
        # 发送告警（可选）
        self.send_quality_alert(warning)

# 使用示例
trading_system = QualityAwareTradingSystem(min_quality_score=0.85)

# 假设有一个交易信号
signal = {
    'symbol': 'BTCUSDT',
    'action': 'BUY',
    'price': 70000,
    'quantity': 0.1
}

# 执行交易（会自动检查数据质量）
result = trading_system.execute_trade('BTCUSDT', signal)
```

## 🔧 配置说明

### 主要配置文件
```
config/
├── default.yaml              # 主配置文件
├── checks/                   # 检查配置
│   ├── completeness.yaml    # 完整性检查
│   ├── consistency.yaml     # 一致性检查
│   ├── accuracy.yaml        # 准确性检查
│   └── timeliness.yaml      # 及时性检查
└── thresholds/              # 阈值配置
    ├── anomaly.yaml         # 异常阈值
    ├── quality.yaml         # 质量阈值
    └── alert.yaml           # 告警阈值
```

### 自定义检查配置
```yaml
# config/checks/custom.yaml
custom_checks:
  # 价格合理性检查
  price_sanity:
    enabled: true
    rules:
      - name: "price_positive"
        condition: "price > 0"
        severity: "critical"
      
      - name: "price_change_limit"
        condition: "abs(price_change) < 0.5"  # 单日涨跌幅不超过50%
        severity: "high"
  
  # 成交量检查
  volume_sanity:
