#!/usr/bin/env python3
"""
BTC监控Skill主脚本

功能: BTC价格监控和报警
输入: 价格阈值、监控间隔、通知方式
输出: 监控状态、价格报警
"""

import sys
import os
import json
import time
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入工具函数
try:
    from tools.data.fetch import fetch_current_price
    from tools.utils.time import get_current_time, format_timestamp
    from tools.utils.formatting import format_price
    from tools.quality.freshness import check_price_freshness
except ImportError as e:
    print(f"❌ 导入工具失败: {e}")
    print("请确保工具层已正确安装")
    sys.exit(1)

# 配置日志
def setup_logging(debug: bool = False):
    """设置日志配置"""
    log_level = logging.DEBUG if debug else logging.INFO
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('btc_monitor.log')
        ]
    )
    
    return logging.getLogger('BTCMonitor')

class BTCMonitor:
    """BTC价格监控器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('BTCMonitor')
        self.running = False
        self.monitor_id = f"monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 监控状态
        self.status = {
            'monitor_id': self.monitor_id,
            'start_time': get_current_time(),
            'checks': 0,
            'alerts': 0,
            'last_check': None,
            'last_price': None,
            'last_alert': None
        }
        
        self.logger.info(f"🚀 BTC监控器初始化完成: {self.monitor_id}")
        self.logger.info(f"配置: 低阈值={config['low']}, 高阈值={config['high']}, 间隔={config['interval']}分钟")
    
    def check_price(self) -> Dict[str, Any]:
        """检查当前价格"""
        try:
            # 获取当前价格
            price_data = fetch_current_price(self.config['symbol'])
            
            if not price_data or 'price' not in price_data:
                self.logger.error("获取价格数据失败")
                return {'error': '价格获取失败'}
            
            price = float(price_data['price'])
            timestamp = price_data.get('timestamp', get_current_time())
            
            # 更新状态
            self.status['last_check'] = timestamp
            self.status['last_price'] = price
            self.status['checks'] += 1
            
            # 检查价格阈值
            alert = self._check_thresholds(price, timestamp)
            
            result = {
                'timestamp': timestamp,
                'price': price,
                'formatted_price': format_price(price),
                'symbol': self.config['symbol'],
                'alert': alert
            }
            
            self.logger.debug(f"价格检查完成: {price} USD")
            
            return result
            
        except Exception as e:
            self.logger.error(f"价格检查失败: {e}")
            return {'error': str(e)}
    
    def _check_thresholds(self, price: float, timestamp: str) -> Optional[Dict[str, Any]]:
        """检查价格是否突破阈值"""
        alert = None
        
        # 检查低阈值
        if price <= self.config['low']:
            alert = {
                'type': 'price_break_low',
                'price': price,
                'threshold': self.config['low'],
                'difference': price - self.config['low'],
                'percentage': ((price - self.config['low']) / self.config['low']) * 100,
                'timestamp': timestamp,
                'message': f"⚠️ BTC跌破低点! 当前: {format_price(price)} (阈值: {format_price(self.config['low'])})"
            }
        
        # 检查高阈值
        elif price >= self.config['high']:
            alert = {
                'type': 'price_break_high',
                'price': price,
                'threshold': self.config['high'],
                'difference': price - self.config['high'],
                'percentage': ((price - self.config['high']) / self.config['high']) * 100,
                'timestamp': timestamp,
                'message': f"⚠️ BTC突破高点! 当前: {format_price(price)} (阈值: {format_price(self.config['high'])})"
            }
        
        if alert:
            self.status['alerts'] += 1
            self.status['last_alert'] = alert
            self.logger.warning(alert['message'])
            
            # 发送通知
            if not self.config.get('silent', False):
                self._send_notification(alert)
        
        return alert
    
    def _send_notification(self, alert: Dict[str, Any]):
        """发送通知"""
        try:
            # 这里可以实现多种通知方式
            # 目前先打印到控制台和日志
            print(f"\n🔔 {alert['message']}")
            
            # TODO: 添加Telegram通知
            # TODO: 添加邮件通知
            # TODO: 添加声音通知
            
            self.logger.info(f"通知已发送: {alert['type']}")
            
        except Exception as e:
            self.logger.error(f"通知发送失败: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取监控状态"""
        status = self.status.copy()
        
        # 计算运行时间
        start_time = datetime.fromisoformat(status['start_time'].replace('Z', '+00:00'))
        uptime = datetime.now() - start_time
        status['uptime'] = str(uptime).split('.')[0]  # 移除微秒
        
        # 计算下次检查时间
        if self.running and self.config.get('interval'):
            interval_minutes = self.config['interval']
            if status['last_check']:
                last_check = datetime.fromisoformat(status['last_check'].replace('Z', '+00:00'))
                next_check = last_check + timedelta(minutes=interval_minutes)
                status['next_check'] = next_check.isoformat()
        
        status['running'] = self.running
        status['config'] = self.config
        
        return status
    
    def run_once(self) -> Dict[str, Any]:
        """运行一次监控检查"""
        self.logger.info("执行单次价格检查...")
        result = self.check_price()
        
        output = {
            'status': 'completed',
            'monitor_id': self.monitor_id,
            'check_result': result,
            'timestamp': get_current_time()
        }
        
        return output
    
    def run_continuous(self):
        """持续运行监控"""
        self.running = True
        interval_minutes = self.config.get('interval', 15)
        
        self.logger.info(f"开始持续监控，间隔{interval_minutes}分钟...")
        
        try:
            while self.running:
                # 执行检查
                result = self.check_price()
                
                # 记录结果
                self.logger.info(f"检查完成: {result.get('formatted_price', 'N/A')}")
                
                # 等待下一次检查
                if self.running:
                    time.sleep(interval_minutes * 60)
        
        except KeyboardInterrupt:
            self.logger.info("收到停止信号，退出监控")
        except Exception as e:
            self.logger.error(f"监控运行出错: {e}")
        finally:
            self.running = False
    
    def stop(self):
        """停止监控"""
        self.running = False
        self.logger.info("监控已停止")

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='BTC价格监控Skill')
    
    # 监控参数
    parser.add_argument('--low', '-l', type=float, default=69000.0,
                       help='低阈值价格 (默认: 69000)')
    parser.add_argument('--high', '-h', type=float, default=73000.0,
                       help='高阈值价格 (默认: 73000)')
    parser.add_argument('--interval', '-i', type=int, default=15,
                       help='监控间隔(分钟) (默认: 15)')
    parser.add_argument('--symbol', '-s', type=str, default='BTCUSDT',
                       help='交易对 (默认: BTCUSDT)')
    
    # 控制参数
    parser.add_argument('--once', action='store_true',
                       help='仅检查一次')
    parser.add_argument('--status', action='store_true',
                       help='查看监控状态')
    parser.add_argument('--stop', action='store_true',
                       help='停止监控')
    parser.add_argument('--restart', action='store_true',
                       help='重启监控')
    
    # 输出参数
    parser.add_argument('--silent', action='store_true',
                       help='静默模式 (不发送通知)')
    parser.add_argument('--debug', action='store_true',
                       help='调试模式')
    parser.add_argument('--output', '-o', type=str,
                       help='输出文件路径')
    
    return parser.parse_args()

def main():
    """主函数"""
    args = parse_args()
    
    # 设置日志
    logger = setup_logging(args.debug)
    
    # 构建配置
    config = {
        'low': args.low,
        'high': args.high,
        'interval': args.interval,
        'symbol': args.symbol,
        'silent': args.silent
    }
    
    # 创建监控器
    monitor = BTCMonitor(config)
    
    # 处理不同命令
    if args.status:
        # 查看状态
        status = monitor.get_status()
        output = {
            'status': 'status_report',
            'data': status,
            'timestamp': get_current_time()
        }
    
    elif args.stop:
        # 停止监控
        monitor.stop()
        output = {
            'status': 'stopped',
            'monitor_id': monitor.monitor_id,
            'message': '监控已停止',
            'timestamp': get_current_time()
        }
    
    elif args.once:
        # 单次检查
        output = monitor.run_once()
    
    else:
        # 持续监控
        if args.restart:
            logger.info("重启监控...")
        
        # 启动持续监控
        try:
            monitor.run_continuous()
            output = {
                'status': 'stopped',
                'monitor_id': monitor.monitor_id,
                'message': '监控已正常结束',
                'timestamp': get_current_time()
            }
        except KeyboardInterrupt:
            output = {
                'status': 'interrupted',
                'monitor_id': monitor.monitor_id,
                'message': '监控被用户中断',
                'timestamp': get_current_time()
            }
    
    # 输出结果
    if args.output:
        # 输出到文件
        with open(args.output, 'w') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        logger.info(f"结果已保存到: {args.output}")
    else:
        # 输出到控制台
        print(json.dumps(output, indent=2, ensure_ascii=False))
    
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        logging.error(f"Skill执行失败: {e}")
        error_output = {
            'status': 'error',
            'error': str(e),
            'timestamp': get_current_time()
        }
        print(json.dumps(error_output, indent=2, ensure_ascii=False))
        sys.exit(1)