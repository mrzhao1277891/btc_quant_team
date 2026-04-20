#!/usr/bin/env python3
"""
OpenClaw Skill集成接口
将数据质量专家Skill集成到OpenClaw中，支持聊天触发
"""

import sys
import os
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import threading
import time

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from scripts.chat_trigger import ChatTrigger

class OpenClawDataQualitySkill:
    """OpenClaw数据质量专家Skill"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化OpenClaw Skill
        
        参数:
            config_path: 配置文件路径
        """
        self.config_path = config_path or "config/openclaw.yaml"
        self.config = self._load_config()
        
        # 初始化聊天触发处理器
        self.chat_trigger = ChatTrigger()
        
        # 技能信息
        self.skill_info = {
            'name': '数据质量专家',
            'version': '2.0.0',
            'description': '专业的数据质量管理和监控Skill',
            'author': 'Steve (🦊)',
            'commands': self._get_available_commands()
        }
        
        # 会话状态
        self.sessions = {}  # session_id -> session_data
        
        print(f"✅ OpenClaw数据质量专家Skill初始化完成: {self.skill_info['name']} v{self.skill_info['version']}")
    
    def _load_config(self) -> Dict[str, Any]:
        """加载OpenClaw配置"""
        config_file = Path(self.config_path)
        
        if config_file.exists():
            try:
                import yaml
                with open(config_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                print(f"⚠️  加载OpenClaw配置失败: {e}")
        
        # 默认配置
        return {
            'skill': {
                'name': '数据质量专家',
                'trigger_words': ['数据质量', 'quality', '新鲜度', 'freshness', '更新数据', 'update'],
                'response_format': 'markdown',
                'enable_notifications': True,
                'notification_channels': ['chat']
            },
            'integration': {
                'openclaw_api': None,
                'webhook_url': None,
                'auto_register': True
            },
            'features': {
                'chat_commands': True,
                'scheduled_checks': True,
                'auto_updates': True,
                'reports': True,
                'alerts': True
            }
        }
    
    def _get_available_commands(self) -> List[Dict[str, Any]]:
        """获取可用命令列表"""
        return [
            {
                'command': '检查数据质量',
                'description': '检查指定交易对和时间框架的数据质量',
                'usage': '检查数据质量 [BTC/ETH/BNB] [4h/1d/1w/1M]',
                'examples': [
                    '检查数据质量',
                    '检查BTC数据质量',
                    '检查4小时数据质量'
                ]
            },
            {
                'command': '更新数据',
                'description': '更新过时的数据',
                'usage': '更新数据 [BTC/ETH/BNB] [4h/1d/1w/1M]',
                'examples': [
                    '更新数据',
                    '更新BTC数据',
                    '更新4小时数据'
                ]
            },
            {
                'command': '检查新鲜度',
                'description': '检查数据新鲜度',
                'usage': '检查新鲜度 [BTC/ETH/BNB] [4h/1d/1w/1M]',
                'examples': [
                    '检查新鲜度',
                    '检查BTC新鲜度',
                    '检查4小时新鲜度'
                ]
            },
            {
                'command': '全面检查',
                'description': '执行全面的数据质量检查',
                'usage': '全面检查 [BTC/ETH/BNB] [4h/1d/1w/1M]',
                'examples': [
                    '全面检查',
                    '全面检查BTC',
                    '全面检查所有数据'
                ]
            },
            {
                'command': '数据质量状态',
                'description': '查看数据质量监控状态',
                'usage': '数据质量状态',
                'examples': [
                    '状态',
                    '数据质量状态',
                    '查看状态'
                ]
            },
            {
                'command': '数据质量帮助',
                'description': '查看帮助信息',
                'usage': '帮助',
                'examples': [
                    '帮助',
                    '数据质量帮助',
                    '查看命令'
                ]
            },
            {
                'command': '生成质量报告',
                'description': '生成数据质量报告',
                'usage': '生成报告 [daily/weekly/monthly/summary]',
                'examples': [
                    '生成报告',
                    '生成日报',
                    '生成周报'
                ]
            }
        ]
    
    def handle_message(self, 
                      message: str, 
                      session_id: str = "default",
                      user_id: str = "anonymous",
                      user_name: str = "用户") -> Dict[str, Any]:
        """
        处理OpenClaw消息
        
        参数:
            message: 用户消息
            session_id: 会话ID
            user_id: 用户ID
            user_name: 用户名
        
        返回:
            Dict: 响应结果
        """
        print(f"📨 OpenClaw消息: {session_id} - {user_name}({user_id}): {message}")
        
        # 初始化会话
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                'id': session_id,
                'user_id': user_id,
                'user_name': user_name,
                'created_at': datetime.now().isoformat(),
                'message_count': 0,
                'last_command': None
            }
        
        session = self.sessions[session_id]
        session['message_count'] += 1
        session['last_message'] = message
        session['last_message_time'] = datetime.now().isoformat()
        
        # 检查是否是技能触发词
        if not self._is_skill_triggered(message):
            return {
                'handled': False,
                'message': None,
                'skill': self.skill_info['name']
            }
        
        # 处理消息
        try:
            response = self.chat_trigger.process_message(message, user_id)
            
            if response['success']:
                session['last_command'] = response.get('command')
                
                # 构建完整响应
                full_response = self._format_response(response['message'], user_name)
                
                return {
                    'handled': True,
                    'message': full_response,
                    'skill': self.skill_info['name'],
                    'command': response.get('command'),
                    'task_id': response.get('task_id'),
                    'format': self.config['skill']['response_format']
                }
            else:
                return {
                    'handled': True,
                    'message': f"❌ {response['message']}",
                    'skill': self.skill_info['name'],
                    'error': response.get('error')
                }
                
        except Exception as e:
            print(f"❌ 处理消息失败: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                'handled': True,
                'message': f"❌ 处理命令时发生错误: {str(e)}",
                'skill': self.skill_info['name'],
                'error': str(e)
            }
    
    def _is_skill_triggered(self, message: str) -> bool:
        """检查是否触发技能"""
        message_lower = message.lower()
        
        # 检查触发词
        trigger_words = self.config['skill']['trigger_words']
        for word in trigger_words:
            if word.lower() in message_lower:
                return True
        
        # 检查命令模式
        command_patterns = [
            r'(?i)数据.*质量',
            r'(?i)质量.*检查',
            r'(?i)更新.*数据',
            r'(?i)新鲜.*度',
            r'(?i)全面.*检查',
            r'(?i)生成.*报告'
        ]
        
        for pattern in command_patterns:
            if re.search(pattern, message_lower):
                return True
        
        return False
    
    def _format_response(self, message: str, user_name: str) -> str:
        """格式化响应"""
        response_format = self.config['skill']['response_format']
        
        if response_format == 'markdown':
            # Markdown格式
            formatted = f"""
## 🦊 数据质量专家Skill

👋 {user_name}，您好！

{message}

---
*技能: {self.skill_info['name']} v{self.skill_info['version']}*
*时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
            """
        
        elif response_format == 'html':
            # HTML格式
            formatted = f"""
<div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #e0e0e0; border-radius: 10px; background-color: #f9f9f9;">
    <h2 style="color: #333;">🦊 数据质量专家Skill</h2>
    <p>👋 {user_name}，您好！</p>
    <div style="margin: 20px 0; padding: 15px; background-color: white; border-radius: 5px;">
        {message.replace(chr(10), '<br>')}
    </div>
    <hr style="border: none; border-top: 1px solid #e0e0e0;">
    <p style="font-size: 12px; color: #666;">
        技能: {self.skill_info['name']} v{self.skill_info['version']}<br>
        时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    </p>
</div>
            """
        
        else:
            # 纯文本格式
            formatted = f"""
🦊 数据质量专家Skill

👋 {user_name}，您好！

{message}

---
技能: {self.skill_info['name']} v{self.skill_info['version']}
时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            """
        
        return formatted.strip()
    
    def get_skill_info(self) -> Dict[str, Any]:
        """获取技能信息"""
        return self.skill_info
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息"""
        return self.sessions.get(session_id)
    
    def get_all_sessions(self) -> Dict[str, Dict[str, Any]]:
        """获取所有会话"""
        return self.sessions
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """清理旧会话"""
        now = datetime.now()
        sessions_to_remove = []
        
        for session_id, session in self.sessions.items():
            if 'last_message_time' in session:
                last_time = datetime.fromisoformat(session['last_message_time'])
                age_hours = (now - last_time).total_seconds() / 3600
                
                if age_hours > max_age_hours:
                    sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.sessions[session_id]
        
        if sessions_to_remove:
            print(f"🧹 清理了 {len(sessions_to_remove)} 个旧会话")
    
    def generate_report(self, report_type: str = "summary") -> Dict[str, Any]:
        """生成报告"""
        report_types = {
            'summary': '摘要报告',
            'daily': '日报',
            'weekly': '周报',
            'monthly': '月报'
        }
        
        if report_type not in report_types:
            return {
                'success': False,
                'error': f'不支持的报告类型: {report_type}'
            }
        
        try:
            # 这里可以调用实际的数据质量检查
            report = {
                'type': report_type,
                'name': report_types[report_type],
                'timestamp': datetime.now().isoformat(),
                'skill': self.skill_info['name'],
                'version': self.skill_info['version'],
                'summary': {
                    'sessions': len(self.sessions),
                    'commands_processed': sum(s.get('message_count', 0) for s in self.sessions.values()),
                    'active_users': len(set(s['user_id'] for s in self.sessions.values() if 'user_id' in s))
                },
                'data_quality': {
                    'overall_score': 0.912,  # 示例数据
                    'freshness_score': 0.85,
                    'completeness_score': 1.0,
                    'status': '优秀'
                },
                'recommendations': [
                    '定期检查数据质量',
                    '设置自动更新',
                    '监控技术指标完整性'
                ]
            }
            
            return {
                'success': True,
                'report': report,
                'message': f'✅ {report_types[report_type]}生成成功'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

def test_openclaw_integration():
    """测试OpenClaw集成"""
    print("🧪 测试OpenClaw数据质量专家Skill集成")
    print("=" * 70)
    
    # 创建Skill实例
    skill = OpenClawDataQualitySkill()
    
    print(f"📋 技能信息:")
    print(f"   名称: {skill.skill_info['name']}")
    print(f"   版本: {skill.skill_info['version']}")
    print(f"   描述: {skill.skill_info['description']}")
    print(f"   作者: {skill.skill_info['author']}")
    
    print(f"\n📝 可用命令 ({len(skill.skill_info['commands'])}个):")
    for cmd in skill.skill_info['commands']:
        print(f"   • {cmd['command']}: {cmd['description']}")
    
    # 测试消息处理
    test_cases = [
        {
            'user': 'Francis',
            'message': '帮助',
            'expected': 'handled'
        },
        {
            'user': 'Francis',
            'message': '检查数据质量',
            'expected': 'handled'
        },
        {
            'user': 'Francis',
            'message': '更新数据',
            'expected': 'handled'
        },
        {
            'user': 'Francis',
            'message': '今天天气怎么样',
            'expected': 'not_handled'
        }
    ]
    
    print(f"\n🔍 测试消息处理:")
    print("-" * 40)
    
    for test_case in test_cases:
        user_name = test_case['user']
        message = test_case['message']
        expected = test_case['expected']
        
        print(f"\n📨 测试: {user_name} - \"{message}\"")
        
        response = skill.handle_message(
            message=message,
            session_id="test_session",
            user_id="test_user",
            user_name=user_name
        )
        
        if response['handled']:
            print(f"   ✅ 已处理")
            if response.get('message'):
                # 显示部分响应
                lines = response['message'].split('\n')
                for line in lines[:3]:
                    if line.strip():
                        print(f"      {line}")
                if len(lines) > 3:
                    print(f"      ...")
        else:
            print(f"   ⏭️  未处理 (预期: {expected})")
    
    # 测试报告生成
    print(f"\n📄 测试报告生成:")
    print("-" * 40)
    
    report_result = skill.generate_report("summary")
    if report_result['success']:
        print(f"   ✅ 报告生成成功")
        report = report_result['report']
        print(f"      类型: {report['name']}")
        print(f"      时间: {report['timestamp']}")
        print(f"      会话数: {report['summary']['sessions']}")
        print(f"      数据质量: {report['data_quality']['status']}")
    else:
        print(f"   ❌ 报告生成失败: {report_result['error']}")
    
    # 显示会话信息
    print(f"\n💬 会话信息:")
    print("-" * 40)
    
    sessions = skill.get_all_sessions()
    if sessions:
        for session_id, session in sessions.items():
            print(f"   📱 {session_id}:")
            print(f"      用户: {session.get('user_name', '未知')}")
            print(f"      消息数: {session.get('message_count', 0)}")
            print(f"      最后命令: {session.get('last_command', '无')}")
    else:
        print("   无活跃会话")
    
    print(f"\n" + "=" * 70)
    print("✅ OpenClaw集成测试完成")
    print("=" * 70)
    
    return skill

if __name__ == "__main__":
    # 运行测试
    skill_instance = test_openclaw_integration()
    
    print(f"\n🚀 技能已就绪，可以通过以下方式使用:")
    print(f"   1. 在OpenClaw聊天中发送: \"检查数据质量\"")
    print(f"   2. 在OpenClaw聊天中发送: \"更新数据\"")
    print(f"   3. 在OpenClaw聊天中发送: \"帮助\" 查看所有命令")
    
    print(f"\n📁 相关文件:")
    print(f"   scripts/openclaw_integration.py - OpenClaw集成接口")
    print(f"   scripts/chat_trigger.py - 聊天触发处理器")
    print(f"   scripts/user_trigger.py - 用户触发管理器")
    print(f"   config/openclaw.yaml - OpenClaw配置")
    
    print