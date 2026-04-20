#!/usr/bin/env python3
"""
数据质量监控CLI工具
"""

import argparse
import sys
import time
from pathlib import Path
from datetime import datetime

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from quality_monitor import QualityMonitor

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="数据质量监控CLI工具")
    
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # start命令 - 启动监控
    start_parser = subparsers.add_parser("start", help="启动数据质量监控")
    start_parser.add_argument("--daemon", action="store_true", help="以守护进程方式运行")
    start_parser.add_argument("--config", help="配置文件路径")
    
    # stop命令 - 停止监控
    stop_parser = subparsers.add_parser("stop", help="停止数据质量监控")
    
    # status命令 - 查看状态
    status_parser = subparsers.add_parser("status", help="查看监控状态")
    
    # check命令 - 执行一次检查
    check_parser = subparsers.add_parser("check", help="执行一次数据质量检查")
    check_parser.add_argument("--symbol", default="BTCUSDT", help="交易对符号")
    check_parser.add_argument("--timeframe", default="1d", help="时间框架")
    check_parser.add_argument("--all", action="store_true", help="检查所有配置的交易对和时间框架")
    
    # update命令 - 更新过时数据
    update_parser = subparsers.add_parser("update", help="更新过时数据")
    update_parser.add_argument("--symbol", help="交易对符号")
    update_parser.add_argument("--timeframe", help="时间框架")
    update_parser.add_argument("--all", action="store_true", help="更新所有过时数据")
    
    # report命令 - 生成报告
    report_parser = subparsers.add_parser("report", help="生成监控报告")
    report_parser.add_argument("--type", choices=["daily", "weekly", "monthly", "summary"], 
                              default="summary", help="报告类型")
    report_parser.add_argument("--output", help="输出文件路径")
    
    # config命令 - 查看配置
    config_parser = subparsers.add_parser("config", help="查看或修改配置")
    config_parser.add_argument("--show", action="store_true", help="显示当前配置")
    config_parser.add_argument("--validate", action="store_true", help="验证配置")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 创建监控器
    monitor = QualityMonitor(args.config if hasattr(args, 'config') else None)
    
    try:
        if args.command == "start":
            start_monitoring(monitor, args.daemon)
            
        elif args.command == "stop":
            stop_monitoring(monitor)
            
        elif args.command == "status":
            show_status(monitor)
            
        elif args.command == "check":
            run_check(monitor, args)
            
        elif args.command == "update":
            run_update(monitor, args)
            
        elif args.command == "report":
            generate_report(monitor, args)
            
        elif args.command == "config":
            handle_config(monitor, args)
            
    except KeyboardInterrupt:
        print("\n⏹️  操作被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 命令执行失败: {e}")
        sys.exit(1)

def start_monitoring(monitor: QualityMonitor, daemon: bool):
    """启动监控"""
    print("🚀 启动数据质量监控...")
    
    if daemon:
        print("🔧 以守护进程方式运行")
        # 这里可以添加守护进程逻辑
        print("⚠️  守护进程模式暂未实现，以后台方式运行")
    
    try:
        # 运行一个监控周期
        print("🔍 执行初始监控周期...")
        monitor.run_monitoring_cycle()
        
        print("✅ 监控启动成功")
        print("\n📋 监控配置:")
        print(f"   检查间隔: {monitor.config['monitoring'].get('check_interval_minutes', 60)} 分钟")
        print(f"   监控交易对: {', '.join(monitor.config['monitoring'].get('symbols', ['BTCUSDT']))}")
        print(f"   时间框架: {', '.join(monitor.config['monitoring'].get('timeframes', ['1d', '4h']))}")
        print(f"   自动更新: {'启用' if monitor.config['monitoring'].get('auto_update', True) else '禁用'}")
        
        if not daemon:
            print("\n⏰ 监控运行中，按 Ctrl+C 停止...")
            try:
                while True:
                    time.sleep(60)  # 每分钟检查一次
            except KeyboardInterrupt:
                print("\n⏹️  停止监控")
                
    except Exception as e:
        print(f"❌ 监控启动失败: {e}")
        sys.exit(1)

def stop_monitoring(monitor: QualityMonitor):
    """停止监控"""
    print("⏹️  停止数据质量监控...")
    
    if monitor.is_running:
        monitor.is_running = False
        if monitor.monitor_thread:
            monitor.monitor_thread.join(timeout=10)
        print("✅ 监控已停止")
    else:
        print("ℹ️  监控未在运行")

def show_status(monitor: QualityMonitor):
    """显示状态"""
    print("📊 数据质量监控状态")
    print("=" * 60)
    
    print(f"运行状态: {'运行中' if monitor.is_running else '已停止'}")
    
    if monitor.last_check_time:
        last_check = monitor.last_check_time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"最后检查: {last_check}")
    else:
        print("最后检查: 从未检查")
    
    print(f"检查历史记录: {len(monitor.check_history)} 条")
    
    if monitor.check_history:
        print("\n📈 最近检查结果:")
        print("-" * 40)
        
        recent_checks = monitor.check_history[-5:]  # 最近5次检查
        for check in reversed(recent_checks):
            symbol = check.get('symbol', 'UNKNOWN')
            timeframe = check.get('timeframe', 'UNKNOWN')
            score = check.get('overall_score', 0)
            status = check.get('status', 'UNKNOWN')
            timestamp = check.get('timestamp', '')
            
            time_str = datetime.fromisoformat(timestamp).strftime("%m-%d %H:%M") if timestamp else "未知时间"
            
            status_icon = "✅" if status == "PASS" else "⚠️ " if status == "WARNING" else "❌"
            
            print(f"{status_icon} {time_str} {symbol}({timeframe}): {score:.1%} [{status}]")
    
    # 生成简要报告
    print("\n📋 简要报告:")
    print("-" * 40)
    
    report = monitor.generate_monitoring_report()
    
    print(f"总体状态: {report.get('overall_status', 'UNKNOWN')}")
    print(f"监控交易对: {len(report.get('symbols_monitored', []))} 个")
    print(f"发现问题: {len(report.get('issues_found', []))} 个")
    
    if report.get('issues_found'):
        print("\n🚨 发现的问题:")
        for issue in report['issues_found'][:3]:  # 显示前3个问题
            print(f"  • {issue.get('issue', '未知问题')}")
        
        if len(report['issues_found']) > 3:
            print(f"  ... 还有 {len(report['issues_found']) - 3} 个问题")
    
    print("=" * 60)

def run_check(monitor: QualityMonitor, args):
    """执行检查"""
    if args.all:
        print("🔍 检查所有配置的交易对和时间框架...")
        
        symbols = monitor.config['monitoring'].get('symbols', ['BTCUSDT'])
        timeframes = monitor.config['monitoring'].get('timeframes', ['1d', '4h'])
        
        all_results = []
        
        for symbol in symbols:
            for timeframe in timeframes:
                print(f"\n📊 检查 {symbol} ({timeframe})...")
                try:
                    report = monitor.check_data_quality(symbol, timeframe)
                    all_results.append({
                        'symbol': symbol,
                        'timeframe': timeframe,
                        'score': report.overall_score
                    })
                    
                    print(f"  质量评分: {report.overall_score:.1%}")
                    
                    # 显示新鲜度
                    freshness_score = report.check_results.get('timeliness', {}).get('score', 0)
                    print(f"  新鲜度: {freshness_score:.1%}")
                    
                except Exception as e:
                    print(f"  ❌ 检查失败: {e}")
        
        if all_results:
            print("\n📋 检查总结:")
            print("-" * 40)
            
            avg_score = sum(r['score'] for r in all_results) / len(all_results)
            print(f"平均质量评分: {avg_score:.1%}")
            
            # 找出评分最低的
            worst = min(all_results, key=lambda x: x['score'])
            print(f"最差质量: {worst['symbol']}({worst['timeframe']}): {worst['score']:.1%}")
            
    else:
        print(f"🔍 检查 {args.symbol} ({args.timeframe})...")
        
        try:
            report = monitor.check_data_quality(args.symbol, args.timeframe)
            
            print(f"✅ 检查完成")
            print(f"质量评分: {report.overall_score:.1%}")
            
            # 显示详细结果
            print("\n📊 详细结果:")
            print("-" * 40)
            
            for check_name, result in report.check_results.items():
                score = result.get('score', 0)
                status = result.get('status', 'UNKNOWN')
                
                status_icon = "✅" if status == "PASS" else "⚠️ " if status == "WARNING" else "❌"
                
                print(f"{status_icon} {check_name}: {score:.1%} [{status}]")
                
                if result.get('issues'):
                    for issue in result['issues'][:2]:
                        print(f"   • {issue.description if hasattr(issue, 'description') else issue}")
            
            print("-" * 40)
            print(f"总体评分: {report.overall_score:.1%}")
            
        except Exception as e:
            print(f"❌ 检查失败: {e}")
            sys.exit(1)

def run_update(monitor: QualityMonitor, args):
    """更新数据"""
    if args.all:
        print("🔄 更新所有过时数据...")
        
        symbols = monitor.config['monitoring'].get('symbols', ['BTCUSDT'])
        timeframes = monitor.config['monitoring'].get('timeframes', ['1d', '4h'])
        
        update_results = []
        
        for symbol in symbols:
            for timeframe in timeframes:
                print(f"\n📥 更新 {symbol} ({timeframe})...")
                
                try:
                    result = monitor.check_and_update_if_stale(symbol, timeframe)
                    update_results.append(result)
                    
                    if result.get('needed_update', False):
                        if result.get('update_success', False):
                            print(f"  ✅ 更新成功")
                        else:
                            print(f"  ❌ 更新失败")
                    else:
                        print(f"  ℹ️  数据新鲜，无需更新")
                        
                except Exception as e:
                    print(f"  ❌ 更新失败: {e}")
        
        # 总结更新结果
        print("\n📋 更新总结:")
        print("-" * 40)
        
        total_updates = sum(1 for r in update_results if r.get('needed_update', False))
        successful_updates = sum(1 for r in update_results if r.get('update_success', False))
        
        print(f"需要更新: {total_updates} 个")
        print(f"成功更新: {successful_updates} 个")
        print(f"失败更新: {total_updates - successful_updates} 个")
        
    else:
        symbol = args.symbol or monitor.config['monitoring'].get('symbols', ['BTCUSDT'])[0]
        timeframe = args.timeframe or monitor.config['monitoring'].get('timeframes', ['1d'])[0]
        
        print(f"🔄 更新 {symbol} ({timeframe})...")
        
        try:
            result = monitor.check_and_update_if_stale(symbol, timeframe)
            
            if result.get('needed_update', False):
                if result.get('update_success', False):
                    print(f"✅ 更新成功")
                    
                    details = result.get('details', {})
                    update_result = details.get('update_result', {})
                    
                    print(f"新增数据: {update_result.get('new_count', 0)} 条")
                    print(f"总数据量: {update_result.get('existing_count', 0) + update_result.get('new_count', 0)} 条")
                    
                else:
                    print(f"❌ 更新失败")
                    error = result.get('error', '未知错误')
                    print(f"错误: {error}")
                    
            else:
                print(f"ℹ️  数据新鲜，无需更新")
                
                freshness_info = result.get('details', {}).get('freshness_check', {})
                if freshness_info:
                    age_hours = freshness_info.get('age_hours', 0)
                    threshold = freshness_info.get('threshold_hours', 24)
                    print(f"数据年龄: {age_hours:.1f}小时 (阈值: {threshold}小时)")
                    
        except Exception as e:
            print(f"❌ 更新失败: {e}")
            sys.exit(1)

def generate_report(monitor: QualityMonitor, args):
    """生成报告"""
    print(f"📄 生成{args.type}报告...")
    
    try:
        report = monitor.generate_monitoring_report()
        
        # 保存报告
        if args.output:
            output_path = Path(args.output)
        else:
            report_dir = Path(monitor.config['reporting']['report_dir'])
            report_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = report_dir / f"quality_report_{args.type}_{timestamp}.json"
        
        monitor.save_report(report)
        
        print(f"✅ 报告已生成: {output_path}")
        
        # 显示报告摘要
        print("\n📋 报告摘要:")
        print("-" * 40)
        print(f"总体状态: {report.get('overall_status', 'UNKNOWN')}")
        print(f"检查次数: {report.get('checks_performed', 0)}")
        print(f"发现问题: {len(report.get('issues_found', []))} 个")
        
        if report.get('recommendations'):
            print(f"\n💡 建议:")
            for rec in report['recommendations'][:3]:
                print(f"  • {rec}")
        
    except Exception as e:
        print(f"❌ 生成报告失败: {e}")
        sys.exit(1)

def handle_config(monitor: QualityMonitor, args):
    """处理配置"""
    if args.show:
        print("🔧 当前监控配置:")
        print("=" * 60)
        
        import yaml
        config_yaml = yaml.dump(monitor.config, default_flow_style=False, allow_unicode=True)
        print(config_yaml)
        
        print("=" * 60)
    
    elif args.validate:
        print("🔍 验证配置...")
        
        # 检查必要配置
        required_sections = ['monitoring', 'alerts', 'reporting']
        missing_sections = [section for section in required_sections if section not in monitor.config]
        
        if missing_sections:
            print(f"❌ 缺少必要配置节: {missing_sections}")
        else:
            print("✅ 配置结构完整")
        
        # 检查监控配置
        monitoring = monitor.config.get('monitoring', {})
        if not monitoring.get('symbols'):
            print("⚠️  未配置监控交易对")
        if not monitoring.get('timeframes'):
            print("⚠️  未配置监控时间框架")
        
        # 检查数据库路径
        db_path = monitor.config.get('database', {}).get('path', '')
        if db_path and Path(db_path).exists():
            print(f"✅ 数据库路径有效: {db_path}")
        else:
            print(f"⚠️  数据库路径可能无效: {db_path}")
        
        print("✅ 配置验证完成")

if __name__ == "__main__":
    main()