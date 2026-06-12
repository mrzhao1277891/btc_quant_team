#!/usr/bin/env python3
"""
BTC/SOL 价格预警工具

功能：每5分钟检查价格，突破阈值时语音通知（macOS say命令）
支持：多币种、上限/下限、触发冷却（避免重复播报）

用法：
  python3 tools/monitor/price_alert.py --high 80000 --low 70000
  python3 tools/monitor/price_alert.py --symbol SOLUSDT --high 200 --low 150
  python3 tools/monitor/price_alert.py --config tools/monitor/alert_config.json
"""

import requests
import time
import os
import json
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

BINANCE_API = "https://api.binance.com/api/v3/ticker/price"

# 触发后冷却时间（秒），避免同一阈值反复播报
COOLDOWN_SECONDS = 30


def get_price(symbol: str) -> float:
    """从币安获取实时价格"""
    try:
        resp = requests.get(BINANCE_API, params={'symbol': symbol}, timeout=10)
        resp.raise_for_status()
        return float(resp.json()['price'])
    except Exception as e:
        logger.error(f"获取{symbol}价格失败: {e}")
        return None


def speak(text: str):
    """macOS语音播报"""
    logger.info(f"🔊 语音播报: {text}")
    os.system(f'say "{text}"')


def check_alerts(symbol: str, price: float, high: float, low: float, cooldowns: dict) -> dict:
    """
    检查价格是否突破阈值
    
    Args:
        symbol: 交易对
        price: 当前价格
        high: 上限阈值（None表示不设）
        low: 下限阈值（None表示不设）
        cooldowns: 冷却记录 {'high': last_trigger_time, 'low': last_trigger_time}
    
    Returns:
        更新后的cooldowns
    """
    now = datetime.now()
    coin_name = symbol.replace('USDT', '')
    
    # 检查上限
    if high is not None and price >= high:
        last_high = cooldowns.get('high')
        if last_high is None or now - last_high > timedelta(seconds=COOLDOWN_SECONDS):
            speak(f"注意，{coin_name}价格突破{int(high)}，当前{int(price)}")
            cooldowns['high'] = now
            logger.warning(f"⚠️  {symbol} 突破上限! 价格:{price:.2f} >= 阈值:{high}")
    
    # 检查下限
    if low is not None and price <= low:
        last_low = cooldowns.get('low')
        if last_low is None or now - last_low > timedelta(seconds=COOLDOWN_SECONDS):
            speak(f"注意，{coin_name}价格跌破{int(low)}，当前{int(price)}")
            cooldowns['low'] = now
            logger.warning(f"⚠️  {symbol} 跌破下限! 价格:{price:.2f} <= 阈值:{low}")
    
    return cooldowns


def load_config(config_path: str) -> list:
    """
    从配置文件加载预警规则
    
    配置格式:
    [
        {"symbol": "BTCUSDT", "high": 80000, "low": 70000},
        {"symbol": "SOLUSDT", "high": 200, "low": 150}
    ]
    """
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
        return []


def main():
    parser = argparse.ArgumentParser(description='BTC/SOL 价格预警工具')
    parser.add_argument('--symbol', default='BTCUSDT', help='交易对 (默认: BTCUSDT)')
    parser.add_argument('--high', type=float, default=None, help='价格上限阈值')
    parser.add_argument('--low', type=float, default=None, help='价格下限阈值')
    parser.add_argument('--interval', type=int, default=300, help='检查间隔秒数 (默认: 300)')
    parser.add_argument('--cooldown', type=int, default=30, help='触发冷却秒数 (默认: 30)')
    parser.add_argument('--config', type=str, default=None, help='配置文件路径 (JSON)')
    
    args = parser.parse_args()
    
    global COOLDOWN_SECONDS
    COOLDOWN_SECONDS = args.cooldown
    
    # 构建预警规则
    alerts = []
    if args.config:
        alerts = load_config(args.config)
    else:
        if args.high is None and args.low is None:
            print("❌ 请至少设置 --high 或 --low 阈值，或使用 --config 配置文件")
            return
        alerts = [{"symbol": args.symbol, "high": args.high, "low": args.low}]
    
    if not alerts:
        print("❌ 没有有效的预警规则")
        return
    
    # 初始化冷却记录
    cooldowns = {alert['symbol']: {} for alert in alerts}
    
    print("🚨 价格预警工具已启动")
    print(f"   检查间隔: {args.interval}秒")
    print(f"   冷却时间: {COOLDOWN_SECONDS}秒")
    print(f"   预警规则:")
    for alert in alerts:
        high_str = f"上限:{alert.get('high')}" if alert.get('high') else ""
        low_str = f"下限:{alert.get('low')}" if alert.get('low') else ""
        print(f"     {alert['symbol']}: {high_str} {low_str}")
    print("=" * 50)
    print("按 Ctrl+C 停止\n")
    
    # 启动时先语音确认
    speak("价格预警已启动")
    
    try:
        while True:
            for alert in alerts:
                symbol = alert['symbol']
                high = alert.get('high')
                low = alert.get('low')
                
                price = get_price(symbol)
                if price is None:
                    continue
                
                # 状态显示
                status = "✅"
                if high and price >= high * 0.99:
                    status = "⚠️ 接近上限"
                elif low and price <= low * 1.01:
                    status = "⚠️ 接近下限"
                
                logger.info(f"{status} {symbol}: ${price:,.2f}  (上限:{high or '-'} 下限:{low or '-'})")
                
                # 检查阈值
                cooldowns[symbol] = check_alerts(
                    symbol, price, high, low, cooldowns[symbol]
                )
            
            # 等待下一次检查
            time.sleep(args.interval)
            
    except KeyboardInterrupt:
        print("\n\n🛑 预警工具已停止")
        speak("价格预警已停止")


if __name__ == "__main__":
    main()
