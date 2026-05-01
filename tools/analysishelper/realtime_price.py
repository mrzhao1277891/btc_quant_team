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

BINANCE_TICKER_URL = 'https://api.binance.com/api/v3/ticker/24hr'


def get_price(symbol: str) -> dict:
    """获取24小时行情数据"""
    resp = requests.get(BINANCE_TICKER_URL, params={'symbol': symbol}, timeout=5)
    resp.raise_for_status()
    d = resp.json()
    return {
        'price':        float(d['lastPrice']),
        'change_pct':   float(d['priceChangePercent']),
        'change_amt':   float(d['priceChange']),
        'high_24h':     float(d['highPrice']),
        'low_24h':      float(d['lowPrice']),
        'volume_24h':   float(d['volume']),
        'quote_vol_24h': float(d['quoteVolume']),
    }


def print_price(symbol: str):
    data = get_price(symbol)
    now  = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    sign = '+' if data['change_pct'] >= 0 else ''
    color_open  = '\033[92m' if data['change_pct'] >= 0 else '\033[91m'
    color_close = '\033[0m'

    print(f"\r{now}  {symbol}  "
          f"{color_open}${data['price']:>12,.2f}  "
          f"{sign}{data['change_pct']:.2f}%  "
          f"{sign}${data['change_amt']:,.2f}{color_close}  "
          f"H:${data['high_24h']:,.2f}  L:${data['low_24h']:,.2f}  "
          f"Vol:{data['volume_24h']:,.0f}",
          end='', flush=True)


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
