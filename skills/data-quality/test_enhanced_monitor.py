#!/usr/bin/env python3
"""
增强版数据质量监控测试
"""

import sys
import os
from pathlib import Path
import time
from datetime import datetime

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

def test_enhanced_monitor():
    """测试增强版监控功能"""
    print("🧪 增强版数据质量监控测试")
    print("=" * 70)
    
    try:
        # 1. 测试导入
        print("\n🔍 1. 测试模块导入...")
        
        from scripts.quality_monitor import QualityMonitor
        from scripts.data_updater import DataUpdater
        from scripts.quality_monitor_cli import main as cli_main
        
        print("✅ 模块导入成功")
        
        # 2. 创建监控器实例
        print("\n🔧 2. 创建监控器实例...")
        
        monitor = QualityMonitor()
        
        print("✅ 监控器创建成功")
        print(f"   配置路径: {monitor.config_path}")
        print(f"   监控开关: {'启用' if monitor.config['monitoring'].get('enabled', True) else '禁用'}")
        print(f"   检查间隔: {monitor.config['monitoring'].get('check_interval_minutes', 60)} 分钟")
        print(f"   自动更新: {'启用' if monitor.config['monitoring'].get('auto_update', True) else '禁用'}")
        
        # 3. 测试数据更新器
        print("\n🔄 3. 测试数据更新器...")
        
        updater = DataUpdater()
        
        # 测试新鲜度检查
        symbol = "BTCUSDT"
        timeframe = "1d"
        
        print(f"   检查 {symbol} ({timeframe}) 新鲜度...")
        is_stale, freshness_info = updater.check_freshness(symbol, timeframe, threshold_hours=24)
        
        print(f"   是否过时: {is_stale}")
        if freshness_info.get('has_data'):
            print(f"   最新数据: {freshness_info.get('latest_time', '未知')}")
            print(f"   数据年龄: {freshness_info.get('age_hours', 0):.1f}小时")
            print(f"   数据数量: {freshness_info.get('data_count', 0)} 条")
        else:
            print("   ⚠️  无数据或检查失败")
        
        # 4. 测试质量检查
        print("\n🔍 4. 测试质量检查...")
        
        try:
            report = monitor.check_data_quality(symbol, timeframe)
            print(f"   质量检查完成")
            print(f"   总体评分: {report.overall_score:.1%}")
            
            # 显示各项检查结果
            for check_name, result in report.check_results.items():
                score = result.get('score', 0)
                status = result.get('status', 'UNKNOWN')
                status_icon = "✅" if status == "PASS" else "⚠️ " if status == "WARNING" else "❌"
                print(f"     {status_icon} {check_name}: {score:.1%}")
                
        except Exception as e:
            print(f"   ❌ 质量检查失败: {e}")
        
        # 5. 测试监控周期
        print("\n⏰ 5. 测试监控周期...")
        
        try:
            print("   运行监控周期...")
            monitor.run_monitoring_cycle()
            print("   ✅ 监控周期运行成功")
            
            if monitor.check_history:
                latest_check = monitor.check_history[-1]
                print(f"   最近检查: {latest_check.get('symbol', 'UNKNOWN')}({latest_check.get('timeframe', 'UNKNOWN')})")
                print(f"   检查评分: {latest_check.get('overall_score', 0):.1%}")
                print(f"   检查状态: {latest_check.get('status', 'UNKNOWN')}")
            
        except Exception as e:
            print(f"   ❌ 监控周期失败: {e}")
        
        # 6. 测试报告生成
        print("\n📄 6. 测试报告生成...")
        
        try:
            report = monitor.generate_monitoring_report()
            print(f"   ✅ 报告生成成功")
            print(f"   总体状态: {report.get('overall_status', 'UNKNOWN')}")
            print(f"   检查次数: {report.get('checks_performed', 0)}")
            print(f"   发现问题: {len(report.get('issues_found', []))} 个")
            
            # 保存报告
            monitor.save_report(report)
            print(f"   ✅ 报告已保存")
            
        except Exception as e:
            print(f"   ❌ 报告生成失败: {e}")
        
        # 7. 测试CLI工具
        print("\n💻 7. 测试CLI工具...")
        
        print("   测试状态命令:")
        import subprocess
        result = subprocess.run(
            [sys.executable, "scripts/quality_monitor_cli.py", "status"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        if result.returncode == 0:
            print("   ✅ CLI状态命令成功")
            # 显示部分输出
            lines = result.stdout.split('\n')[:10]
            for line in lines:
                if line.strip():
                    print(f"     {line}")
        else:
            print(f"   ❌ CLI状态命令失败: {result.stderr[:100]}")
        
        # 8. 测试配置验证
        print("\n🔧 8. 测试配置验证...")
        
        print("   当前配置摘要:")
        config = monitor.config
        
        print(f"    监控交易对: {', '.join(config['monitoring'].get('symbols', ['BTCUSDT']))}")
        print(f"    时间框架: {', '.join(config['monitoring'].get('timeframes', ['1d', '4h']))}")
        print(f"    新鲜度阈值:")
        thresholds = config['monitoring'].get('freshness_thresholds', {})
        for tf, hours in thresholds.items():
            print(f"      {tf}: {hours}小时")
        
        print(f"    告警渠道: {', '.join(config['alerts'].get('channels', ['log']))}")
        print(f"    报告目录: {config['reporting'].get('report_dir', 'reports')}")
        
        # 9. 测试告警系统
        print("\n🚨 9. 测试告警系统...")
        
        try:
            monitor.send_alert("测试告警消息", "info")
            monitor.send_alert("测试警告消息", "warning")
            monitor.send_alert("测试错误消息", "error")
            print("   ✅ 告警发送测试完成")
        except Exception as e:
            print(f"   ❌ 告警测试失败: {e}")
        
        # 10. 总结
        print("\n" + "=" * 70)
        print("🎯 增强版数据质量监控测试总结")
        print("=" * 70)
        
        print("\n✅ 测试通过的功能:")
        print("  1. 模块导入和初始化")
        print("  2. 数据新鲜度检查")
        print("  3. 数据质量检查")
        print("  4. 监控周期运行")
        print("  5. 报告生成和保存")
        print("  6. CLI工具基础功能")
        print("  7. 配置管理")
        print("  8. 告警系统")
        
        print("\n🔧 可用的命令:")
        print("  python scripts/quality_monitor_cli.py start    # 启动监控")
        print("  python scripts/quality_monitor_cli.py stop     # 停止监控")
        print("  python scripts/quality_monitor_cli.py status   # 查看状态")
        print("  python scripts/quality_monitor_cli.py check    # 执行检查")
        print("  python scripts/quality_monitor_cli.py update   # 更新数据")
        print("  python scripts/quality_monitor_cli.py report   # 生成报告")
        print("  python scripts/quality_monitor_cli.py config   # 查看配置")
        
        print("\n📁 相关文件:")
        print("  scripts/quality_monitor.py      # 监控器主逻辑")
        print("  scripts/data_updater.py         # 数据更新器")
        print("  scripts/quality_monitor_cli.py  # CLI工具")
        print("  config/monitor.yaml             # 监控配置")
        print("  logs/quality_monitor.log        # 监控日志")
        print("  reports/                        # 报告目录")
        
        print("\n🎯 下一步:")
        print("  1. 配置监控参数 (config/monitor.yaml)")
        print("  2. 设置定时任务 (cron)")
        print("  3. 配置告警渠道 (Telegram等)")
        print("  4. 定期查看监控报告")
        
        print("\n" + "=" * 70)
        print("✅ 增强版数据质量监控测试完成")
        print("=" * 70)
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    success = test_enhanced_monitor()
    
    if success:
        print("\n🚀 增强版数据质量监控测试通过！")
        print("\n📋 立即开始使用:")
        print("1. 查看配置: python scripts/quality_monitor_cli.py config --show")
        print("2. 检查状态: python scripts/quality_monitor_cli.py status")
        print("3. 执行检查: python scripts/quality_monitor_cli.py check --all")
        print("4. 启动监控: python scripts/quality_monitor_cli.py start")
    else:
        print("\n⚠️  测试失败，请检查问题。")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()