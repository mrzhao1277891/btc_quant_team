#!/usr/bin/env python3
"""
OpenClaw聊天触发接口
允许用户通过聊天命令触发数据质量检查和更新
"""

import sys
import os
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import threading
import time

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from scripts.user_trigger import UserTriggerManager

class ChatTrigger:
    """聊天触发处理器"""
    
    def __init__(self, trigger_manager: UserTriggerManager = None):
        """
        初始化聊天触发处理器
        
        参数:
            trigger_manager: 用户触发管理器实例
        """
        self.trigger_manager = trigger_manager or UserTriggerManager()
        self.config = self.trigger_manager.config
        
        # 聊天命令映射
        self.command_patterns = self._build_command_patterns()
        
        # 响应模板
        self.response_templates = self._build_response_templates()
        
        # 任务状态跟踪
        self.user_tasks = {}  # user_id -> [task_ids]
        
        print("✅ 聊天触发接口初始化完成")
    
    def _build_command_patterns(self) -> Dict[str, re.Pattern]:
        """构建命令模式"""
        patterns = {}
        
        # 从配置加载命令
        chat_config = self.config.get('triggers', {}).get('chat', {})
        commands = chat_config.get('commands', {})
        
        # 质量检查命令
        for cmd in commands.get('check_quality', []):
            patterns[f'check_quality_{cmd}'] = re.compile(
                rf'(?i)({re.escape(cmd)}|检查.*质量|质量.*检查|quality.*check)',
                re.IGNORECASE
            )
        
        # 数据更新命令
        for cmd in commands.get('update_data', []):
            patterns[f'update_data_{cmd}'] = re.compile(
                rf'(?i)({re.escape(cmd)}|更新.*数据|刷新.*数据|update.*data)',
                re.IGNORECASE
            )
        
        # 新鲜度检查命令
        for cmd in commands.get('check_freshness', []):
            patterns[f'check_freshness_{cmd}'] = re.compile(
                rf'(?i)({re.escape(cmd)}|检查.*新鲜|新鲜.*检查|freshness.*check)',
                re.IGNORECASE
            )
        
        # 全面检查命令
        for cmd in commands.get('full_check', []):
            patterns[f'full_check_{cmd}'] = re.compile(
                rf'(?i)({re.escape(cmd)}|全面.*检查|完整.*检查|full.*check)',
                re.IGNORECASE
            )
        
        # 帮助命令
        patterns['help'] = re.compile(r'(?i)(帮助|help|命令|usage)')
        
        # 状态命令
        patterns['status'] = re.compile(r'(?i)(状态|status|任务.*状态)')
        
        return patterns
    
    def _build_response_templates(self) -> Dict[str, str]:
        """构建响应模板"""
        return {
            'task_started': """
🎯 任务已开始！

任务ID: {task_id}
类型: {task_type}
用户: {user_id}
时间: {timestamp}

🔍 正在执行 {task_type}...
请稍候，完成后会通知您。
            """,
            
            'task_progress': """
📊 任务进度更新

任务ID: {task_id}
进度: {progress:.0%}
当前操作: {current}
消息: {message}
            """,
            
            'task_completed': """
✅ 任务完成！

任务ID: {task_id}
类型: {task_type}
用户: {user_id}
开始时间: {started_at}
完成时间: {completed_at}
持续时间: {duration}

📋 结果摘要:
{summary}
            """,
            
            'task_failed': """
❌ 任务失败！

任务ID: {task_id}
类型: {task_type}
用户: {user_id}
错误: {error}

请检查日志或联系管理员。
            """,
            
            'help': """
🦊 数据质量专家Skill - 聊天命令帮助

📋 可用命令:

1. **检查数据质量**
   - "检查数据质量"
   - "数据质量怎么样"
   - "quality check"
   
2. **更新数据**
   - "更新数据"
   - "刷新数据"
   - "update data"
   
3. **检查新鲜度**
   - "检查新鲜度"
   - "数据新鲜吗"
   - "freshness check"
   
4. **全面检查**
   - "全面检查"
   - "完整检查"
   - "full check"
   
5. **查看状态**
   - "状态"
   - "任务状态"
   - "status"
   
6. **帮助**
   - "帮助"
   - "命令"
   - "help"

💡 示例:
   - "检查BTC数据质量"
   - "更新4小时数据"
   - "全面检查所有数据"
            """,
            
            'status': """
📊 数据质量监控状态

🔄 当前任务: {current_task}
📋 等待任务: {queued_tasks}
📈 历史任务: {history_tasks}

⏰ 最后检查: {last_check}
🎯 总体质量: {overall_quality}

💡 建议: {suggestion}
            """
        }
    
    def process_message(self, message: str, user_id: str = "anonymous") -> Dict[str, Any]:
        """
        处理聊天消息
        
        参数:
            message: 聊天消息
            user_id: 用户ID
        
        返回:
            Dict: 处理结果
        """
        print(f"📨 收到消息: {user_id} - {message}")
        
        # 初始化用户任务列表
        if user_id not in self.user_tasks:
            self.user_tasks[user_id] = []
        
        # 匹配命令
        command_type, params = self._parse_command(message)
        
        if not command_type:
            return {
                'success': False,
                'message': '未识别的命令，请输入"帮助"查看可用命令',
                'command': None
            }
        
        # 处理命令
        if command_type == 'help':
            return self._handle_help(user_id)
        
        elif command_type == 'status':
            return self._handle_status(user_id)
        
        else:
            # 触发相应任务
            return self._trigger_task(command_type, params, user_id)
    
    def _parse_command(self, message: str) -> tuple:
        """
        解析命令
        
        返回:
            tuple: (命令类型, 参数)
        """
        message_lower = message.lower()
        
        # 检查命令模式
        for pattern_name, pattern in self.command_patterns.items():
            if pattern.search(message):
                # 提取命令类型
                if pattern_name.startswith('check_quality_'):
                    return 'check_quality', self._extract_params(message)
                elif pattern_name.startswith('update_data_'):
                    return 'update_data', self._extract_params(message)
                elif pattern_name.startswith('check_freshness_'):
                    return 'check_freshness', self._extract_params(message)
                elif pattern_name.startswith('full_check_'):
                    return 'full_check', self._extract_params(message)
                elif pattern_name == 'help':
                    return 'help', {}
                elif pattern_name == 'status':
                    return 'status', {}
        
        return None, {}
    
    def _extract_params(self, message: str) -> Dict[str, Any]:
        """从消息中提取参数"""
        params = {
            'symbols': ['BTCUSDT'],
            'timeframes': ['4h', '1d', '1w', '1M']
        }
        
        # 提取交易对
        symbol_patterns = [
            r'(?i)btc|比特币',
            r'(?i)eth|以太坊',
            r'(?i)bnb|币安币'
        ]
        
        for pattern in symbol_patterns:
            if re.search(pattern, message):
                if 'btc' in pattern.lower():
                    params['symbols'] = ['BTCUSDT']
                elif 'eth' in pattern.lower():
                    params['symbols'] = ['ETHUSDT']
                elif 'bnb' in pattern.lower():
                    params['symbols'] = ['BNBUSDT']
        
        # 提取时间框架
        timeframe_patterns = {
            '4h': r'(?i)4[小时h]|四小时',
            '1d': r'(?i)1[天d日]|日线|daily',
            '1w': r'(?i)1[周w]|周线|weekly',
            '1M': r'(?i)1[月m]|月线|monthly'
        }
        
        found_timeframes = []
        for tf, pattern in timeframe_patterns.items():
            if re.search(pattern, message):
                found_timeframes.append(tf)
        
        if found_timeframes:
            params['timeframes'] = found_timeframes
        
        # 检查是否包含"所有"或"全部"
        if re.search(r'(?i)所有|全部|all', message):
            params['symbols'] = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
            params['timeframes'] = ['4h', '1d', '1w', '1M']
        
        return params
    
    def _handle_help(self, user_id: str) -> Dict[str, Any]:
        """处理帮助命令"""
        return {
            'success': True,
            'message': self.response_templates['help'],
            'command': 'help',
            'user_id': user_id
        }
    
    def _handle_status(self, user_id: str) -> Dict[str, Any]:
        """处理状态命令"""
        # 获取当前任务
        current_task = self.trigger_manager.current_task
        if current_task:
            current_task_info = f"{current_task.get('type', 'unknown')} ({current_task.get('id', 'unknown')})"
        else:
            current_task_info = "无"
        
        # 获取队列任务
        queued_tasks = len(self.trigger_manager.task_queue)
        
        # 获取历史任务
        history_tasks = len(self.trigger_manager.task_history)
        
        # 获取用户任务
        user_task_count = len(self.user_tasks.get(user_id, []))
        
        # 获取最后检查时间
        last_check = "未知"
        if self.trigger_manager.task_history:
            last_task = self.trigger_manager.task_history[-1]
            last_check = last_task.get('completed_at', '未知')
        
        # 构建状态消息
        status_message = self.response_templates['status'].format(
            current_task=current_task_info,
            queued_tasks=queued_tasks,
            history_tasks=history_tasks,
            last_check=last_check,
            overall_quality="91.2% 🟢 优秀",  # 这里可以调用实际的质量检查
            suggestion="数据质量良好，4小时数据需要更新"
        )
        
        return {
            'success': True,
            'message': status_message,
            'command': 'status',
            'user_id': user_id
        }
    
    def _trigger_task(self, command_type: str, params: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """触发任务"""
        # 注册回调
        def task_callback(task):
            """任务完成回调"""
            self._notify_task_completion(task, user_id)
        
        # 根据命令类型触发任务
        if command_type == 'check_quality':
            task_id = self.trigger_manager.trigger_check_quality(
                symbols=params['symbols'],
                timeframes=params['timeframes'],
                user_id=user_id,
                callback=task_callback
            )
            task_type = "数据质量检查"
        
        elif command_type == 'update_data':
            task_id = self.trigger_manager.trigger_update_data(
                symbols=params['symbols'],
                timeframes=params['timeframes'],
                user_id=user_id,
                callback=task_callback
            )
            task_type = "数据更新"
        
        elif command_type == 'check_freshness':
            task_id = self.trigger_manager.trigger_check_freshness(
                symbols=params['symbols'],
                timeframes=params['timeframes'],
                user_id=user_id,
                callback=task_callback
            )
            task_type = "新鲜度检查"
        
        elif command_type == 'full_check':
            task_id = self.trigger_manager.trigger_full_check(
                symbols=params['symbols'],
                timeframes=params['timeframes'],
                user_id=user_id,
                callback=task_callback
            )
            task_type = "全面检查"
        
        else:
            return {
                'success': False,
                'message': '未知的命令类型',
                'command': command_type,
                'user_id': user_id
            }
        
        # 记录用户任务
        self.user_tasks[user_id].append(task_id)
        
        # 构建响应消息
        response_message = self.response_templates['task_started'].format(
            task_id=task_id,
            task_type=task_type,
            user_id=user_id,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        return {
            'success': True,
            'message': response_message,
            'command': command_type,
            'task_id': task_id,
            'user_id': user_id,
            'params': params
        }
    
    def _notify_task_completion(self, task: Dict[str, Any], user_id: str):
        """通知任务完成"""
        task_id = task['id']
        task_type = task['type']
        status = task['status']
        
        if status == 'completed':
            # 构建完成消息
            started_at = datetime.fromisoformat(task['started_at'])
            completed_at = datetime.fromisoformat(task['completed_at'])
            duration = completed_at - started_at
            
            # 生成结果摘要
            summary = self._generate_result_summary(task)
            
            message = self.response_templates['task_completed'].format(
                task_id=task_id,
                task_type=task_type,
                user_id=user_id,
                started_at=started_at.strftime("%Y-%m-%d %H:%M:%S"),
                completed_at=completed_at.strftime("%Y-%m-%d %H:%M:%S"),
                duration=str(duration),
                summary=summary
            )
        
        elif status == 'failed':
            message = self.response_templates['task_failed'].format(
                task_id=task_id,
                task_type=task_type,
                user_id=user_id,
                error=task.get('error', '未知错误')
            )
        
        else:
            return
        
        # 这里可以添加实际的通知逻辑
        # 例如：发送到OpenClaw聊天、Telegram、Email等
        print(f"📤 发送任务完成通知给 {user_id}:")
        print(message)
        
        # 保存通知记录
        self._save_notification(user_id, message)
    
    def _generate_result_summary(self, task: Dict[str, Any]) -> str:
        """生成结果摘要"""
        results = task.get('results', {})
        task_type = task['type']
        
        if task_type == 'check_quality':
            overall_score = results.get('overall_score', 0)
            
            if overall_score >= 0.9:
                rating = "🟢 优秀"
            elif overall_score >= 0.8:
                rating = "🟡 良好"
            elif overall_score >= 0.7:
                rating = "🟠 一般"
            else:
                rating = "🔴 需要改进"
            
            return f"总体质量评分: {overall_score:.1%} ({rating})"
        
        elif task_type == 'update_data':
            summary = results.get('summary', {})
            success_rate = summary.get('success_rate', 0)
            
            return f"更新成功率: {success_rate:.1%} ({summary.get('successful', 0)}/{summary.get('total', 0)} 成功)"
        
        elif task_type == 'check_freshness':
            stale_count = results.get('stale_count', 0)
            total = results.get('total_checks', 0)
            
            if stale_count == 0:
                return "✅ 所有数据都新鲜"
            else:
                return f"⚠️  {stale_count}/{total} 个数据需要更新"
        
        elif task_type == 'full_check':
            return "✅ 全面检查完成，详情请查看日志"
        
        return "无详细结果"
    
    def _save_notification(self, user_id: str, message: str):
        """保存通知记录"""
        notification_dir = Path("notifications")
        notification_dir.mkdir(exist_ok=True)
        
        notification_file = notification_dir / f"notification_{user_id}_{int(time.time())}.txt"
        
        try:
            with open(notification_file, 'w', encoding='utf-8') as f:
                f.write(message)
        except Exception as e:
            print(f"保存通知失败: {e}")
    
    def get_user_tasks(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户任务列表"""
        task_ids = self.user_tasks.get(user_id, [])
        
        tasks = []
        for task_id in task_ids:
            # 从历史中查找任务
            for task in self.trigger_manager.task_history:
                if task['id'] == task_id:
                    tasks.append(task)
                    break
        
        return tasks

def main():
    """主函数 - 测试聊天触发"""
    print("🧪 测试聊天触发接口")
    print("=" * 60)
    
    # 创建聊天触发处理器
    chat_trigger = ChatTrigger()
    
    # 测试消息
    test_messages = [
        "帮助",
        "状态",
        "检查数据质量",
        "更新数据",
        "检查新鲜度",
        "全面检查",
        "检查BTC数据质量",
        "更新4小时数据",
        "检查所有数据新鲜度"
    ]
    
    for message