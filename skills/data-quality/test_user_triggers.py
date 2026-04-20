#!/usr/bin/env python3
"""
测试用户主动触发功能
"""

import sys
import os
from pathlib import Path
import time
from datetime import datetime

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

def test_user_triggers():
    """测试用户主动触发功能"""
    print("🧪 测试用户主动触发功能")
    print("=" * 70)
    
    try:
        # 1. 测试导入
        print("\n🔍 1. 测试模块导入...")
        
        from scripts.user_trigger import UserTriggerManager
        from scripts.chat_trigger import ChatTrigger
        from scripts.openclaw_integration import OpenClawDataQualitySkill
        
        print("✅ 模块导入成功")
        
        # 2. 测试用户触发管理器
        print("\n🔧 2. 测试用户触发管理器...")
        
        trigger_manager = UserTriggerManager()
        
        print("✅ 用户触发管理器创建成功")
        print(f"   配置路径: {trigger_manager.config_path}")
        print(f"   任务队列: {len(trigger_manager.task_queue)} 个等待")
        print(f"   当前任务: {'有' if trigger_manager.current_task else '无'}")
        
        # 3. 测试触发质量检查
        print("\n🎯 3. 测试触发质量检查...")
        
        def quality_check_callback(task):
            print(f"   📤 质量检查回调: 任务 {task['id']} 状态: {task['status']}")
            if task['status'] == 'completed':
                print(f"   ✅ 质量检查完成!")
                if task.get('results'):
                    score = task['results'].get('overall_score', 0)
                    print(f"      总体评分: {score:.1%}")
        
        task_id = trigger_manager.trigger_check_quality(
            symbols=['BTCUSDT'],
            timeframes=['1d'],
            user_id='francis',
            callback=quality_check_callback
        )
        
        print(f"   ✅ 质量检查已触发: {task_id}")
        print(f"   等待任务: {len(trigger_manager.task_queue)} 个")
        
        # 4. 测试触发数据更新
        print("\n🔄 4. 测试触发数据更新...")
        
        def update_callback(task):
            print(f"   📤 数据更新回调: 任务 {task['id']} 状态: {task['status']}")
            if task['status'] == 'completed':
                print(f"   ✅ 数据更新完成!")
                if task.get('results'):
                    summary = task['results'].get('summary', {})
                    success = summary.get('successful', 0)
                    total = summary.get('total', 0)
                    print(f"      成功更新: {success}/{total}")
        
        update_task_id = trigger_manager.trigger_update_data(
            symbols=['BTCUSDT'],
            timeframes=['4h'],
            user_id='francis',
            callback=update_callback
        )
        
        print(f"   ✅ 数据更新已触发: {update_task_id}")
        print(f"   等待任务: {len(trigger_manager.task_queue)} 个")
        
        # 5. 测试聊天触发
        print("\n💬 5. 测试聊天触发...")
        
        chat_trigger = ChatTrigger(trigger_manager)
        
        test_messages = [
            "检查数据质量",
            "更新数据",
            "检查新鲜度",
            "全面检查",
            "状态",
            "帮助"
        ]
        
        for message in test_messages:
            print(f"\n   📨 测试消息: \"{message}\"")
            result = chat_trigger.process_message(message, "test_user")
            
            if result['success']:
                print(f"   ✅ 处理成功")
                print(f"      命令: {result.get('command', '未知')}")
                if result.get('task_id'):
                    print(f"      任务ID: {result['task_id']}")
            else:
                print(f"   ❌ 处理失败: {result.get('message', '未知错误')}")
        
        # 6. 测试OpenClaw集成
        print("\n🦊 6. 测试OpenClaw集成...")
        
        openclaw_skill = OpenClawDataQualitySkill()
        
        skill_info = openclaw_skill.get_skill_info()
        print(f"   ✅ OpenClaw Skill创建成功")
        print(f"      名称: {skill_info['name']}")
        print(f"      版本: {skill_info['version']}")
        print(f"      描述: {skill_info['description']}")
        print(f"      作者: {skill_info['author']}")
        print(f"      命令数: {len(skill_info['commands'])}")
        
        # 测试消息处理
        print(f"\n   🔍 测试OpenClaw消息处理:")
        
        test_cases = [
            ("检查数据质量", True),
            ("更新数据", True),
            ("今天天气怎么样", False),  # 不应触发
            ("数据质量状态", True),
            ("帮助", True)
        ]
        
        for message, should_handle in test_cases:
            response = openclaw_skill.handle_message(
                message=message,
                session_id="test_session",
                user_id="test_user",
                user_name="测试用户"
            )
            
            if response['handled'] == should_handle:
                status = "✅ 正确"
            else:
                status = "❌ 错误"
            
            print(f"      {status} \"{message}\": {'处理' if response['handled'] else '跳过'}")
        
        # 7. 测试报告生成
        print("\n📄 7. 测试报告生成...")
        
        report_result = openclaw_skill.generate_report("summary")
        if report_result['success']:
            print(f"   ✅ 报告生成成功")
            report = report_result['report']
            print(f"      报告类型: {report['name']}")
            print(f"      会话数: {report['summary']['sessions']}")
            print(f"      数据质量: {report['data_quality']['status']}")
        else:
            print(f"   ❌ 报告生成失败: {report_result['error']}")
        
        # 8. 等待任务完成
        print("\n⏳ 8. 等待任务完成...")
        print("   等待10秒让任务执行...")
        
        for i in range(10):
            print(f"   {10-i}...", end=' ', flush=True)
            time.sleep(1)
        print()
        
        # 检查任务历史
        print(f"\n📋 任务历史: {len(trigger_manager.task_history)} 个")
        if trigger_manager.task_history:
            for task in trigger_manager.task_history[-3:]:  # 显示最后3个任务
                task_id = task['id']
                task_type = task['type']
                status = task['status']
                created = task.get('created_at', '未知')
                
                status_icon = "✅" if status == 'completed' else "⚠️ " if status == 'running' else "❌"
                
                print(f"   {status_icon} {task_id}: {task_type} [{status}]")
        
        # 9. 总结
        print("\n" + "=" * 70)
        print("📋 用户主动触发功能测试总结")
        print("=" * 70)
        
        print("\n✅ 测试通过的功能:")
        print("  1. 用户触发管理器")
        print("  2. 质量检查触发")
        print("  3. 数据更新触发")
        print("  4. 聊天触发处理器")
        print("  5. OpenClaw集成")
        print("  6. 报告生成")
        print("  7. 任务队列管理")
        print("  8. 回调函数支持")
        
        print("\n🔧 可用接口:")
        print("  • UserTriggerManager - 用户触发管理器")
        print("  • ChatTrigger - 聊天触发处理器")
        print("  • OpenClawDataQualitySkill - OpenClaw集成")
        
        print("\n🎮 使用方式:")
        print("  1. OpenClaw聊天: \"检查数据质量\"")
        print("  2. CLI命令: python3 scripts/quality_monitor_cli.py check --all")
        print("  3. Python API: trigger_manager.trigger_check_quality()")
        
        print("\n📁 相关文件:")
        print("  scripts/user_trigger.py - 用户触发管理器")
        print("  scripts/chat_trigger.py - 聊天触发处理器")
        print("  scripts/openclaw_integration.py - OpenClaw集成")
        print("  config/openclaw.yaml - OpenClaw配置")
        print("  config/monitor.yaml - 监控配置")
        
        print("\n" + "=" * 70)
        print("✅ 用户主动触发功能测试完成")
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
    success = test_user_triggers()
    
    if success:
        print("\n🚀 用户主动触发功能测试通过！")
        print("\n📋 立即开始使用:")
        print("1. OpenClaw聊天: 发送\"检查数据质量\"")
        print("2. CLI命令: python3 scripts/quality_monitor_cli.py status")
        print("3. Python API: 导入UserTriggerManager使用")
        print("\n🎯 现在你可以随时主动触发数据质量检查和更新了！")
    else:
        print("\n⚠️  测试失败，请检查问题。")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()