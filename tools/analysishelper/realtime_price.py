#!/usr/bin/env python3
"""
实时价格工具

从 Binance 获取最新价格，支持单次查询和持续刷新。
所有参数集中在文件开头配置。
"""

import requests
import time
from datetime import datetime

# ================================================================
# 参数配置
# ================================================================

SYMBOL = 'BTCUSDT'

# 持续刷新间隔（秒），设为 0 则只查询一次
REFRESH_INTERVAL = 0

# ================================================================

BINANCE_TICKER_URL = 'https://api.binance.com/api/v3/ticker/price'


def get_price(symbol: str) -> float:
    resp = requests.get(BINANCE_TICKER_URL, params={'symbol': symbol}, timeout=5)
    resp.raise_for_status()
    return float(resp.json()['price'])


def print_price(symbol: str):
    price = get_price(symbol)
    now   = datetime.now().strftime('%H:%M:%S')
    print(f"\r{now}  {symbol}  ${price:,.2f}  ", end='', flush=True)


def main():
    print(f"📡 实时价格  {SYMBOL}  (Ctrl+C 退出)")
    print(f"{'─'*80}")

    if REFRESH_INTERVAL <= 0:
        # 单次查询
        print_price(SYMBOL)
        print()
    else:
        # 持续刷新
        try:
            while True:
                print_price(SYMBOL)
                time.sleep(REFRESH_INTERVAL)
        except KeyboardInterrupt:
            print(f"\n\n已停止")


if __name__ == '__main__':
    main()
