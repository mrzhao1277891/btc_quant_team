#!/usr/bin/env python3
"""
摆动点识别工具

识别4个周期（1M/1w/1d/4h）的摆动高点和低点，直接输出。
所有参数集中在文件开头配置。
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mysql.connector
from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# ================================================================
# 参数配置 —— 所有可调参数都在这里
# ================================================================

DB_CONFIG = {
    'host':     'localhost',
    'port':     3306,
    'user':     'root',
    'password': '',
    'database': 'btc_assistant',
}

SYMBOL = 'BTCUSDT'

# 各周期配置
# swing_window : 左右各看几根K线判断极值点
# swing_klines : 取多少根K线用于识别摆动点
# min_amplitude: 摆动点相对周围均值的最小振幅，过滤噪音
TF_CONFIG = {
    '1M': {'swing_window': 3, 'swing_klines': 60,  'min_amplitude': 0.01},
    '1w': {'swing_window': 3, 'swing_klines': 100, 'min_amplitude': 0.008},
    '1d': {'swing_window': 5, 'swing_klines': 150, 'min_amplitude': 0.005},
    '4h': {'swing_window': 3, 'swing_klines': 120, 'min_amplitude': 0.003},
}

# 每个周期最多输出几个摆动点（按距当前价格由近到远）
MAX_LEVELS_PER_TF = 40

# ================================================================


def _f(v) -> Optional[float]:
    if v is None:
        return None
    return float(Decimal(v)) if isinstance(v, Decimal) else float(v)


def fetch_klines(conn, symbol: str, timeframe: str, limit: int) -> List[Dict]:
    """从数据库取K线，按时间正序返回"""
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT timestamp, high, low, close FROM klines "
        "WHERE symbol=%s AND timeframe=%s "
        "ORDER BY timestamp DESC LIMIT %s",
        (symbol, timeframe, limit)
    )
    rows = list(reversed(cursor.fetchall()))
    cursor.close()
    return [{'timestamp': r['timestamp'],
             'high': _f(r['high']), 'low': _f(r['low']), 'close': _f(r['close'])}
            for r in rows]


def find_swing_points(klines: List[Dict], window: int,
                      min_amplitude: float) -> Tuple[List[Dict], List[Dict]]:
    """
    识别摆动高点和低点。

    返回：
        (swing_highs, swing_lows)
        每个元素：{'price': float, 'timestamp': int, 'idx': int}
    """
    n = len(klines)
    highs_list = [k['high'] for k in klines]
    lows_list  = [k['low']  for k in klines]

    swing_highs = []
    swing_lows  = []

    for i in range(window, n - window):
        # 摆动高点
        if all(highs_list[i] > highs_list[i - j] and
               highs_list[i] > highs_list[i + j]
               for j in range(1, window + 1)):
            # 振幅过滤
            surrounding = (sum(highs_list[i - window:i]) +
                           sum(highs_list[i + 1:i + window + 1])) / (window * 2)
            if surrounding > 0 and abs(highs_list[i] - surrounding) / surrounding >= min_amplitude:
                swing_highs.append({
                    'price':     highs_list[i],
                    'timestamp': klines[i]['timestamp'],
                    'idx':       i,
                })

        # 摆动低点
        if all(lows_list[i] < lows_list[i - j] and
               lows_list[i] < lows_list[i + j]
               for j in range(1, window + 1)):
            surrounding = (sum(lows_list[i - window:i]) +
                           sum(lows_list[i + 1:i + window + 1])) / (window * 2)
            if surrounding > 0 and abs(lows_list[i] - surrounding) / surrounding >= min_amplitude:
                swing_lows.append({
                    'price':     lows_list[i],
                    'timestamp': klines[i]['timestamp'],
                    'idx':       i,
                })

    return swing_highs, swing_lows


def print_report(conn, symbol: str):
    """识别并打印各周期摆动点"""

    # 获取当前价格（最新4H收盘价）
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT close FROM klines WHERE symbol=%s AND timeframe='4h' "
        "ORDER BY timestamp DESC LIMIT 1", (symbol,)
    )
    row = cursor.fetchone()
    cursor.close()
    current_price = _f(row['close']) if row else 0

    print(f"\n{'='*60}")
    print(f"📊 {symbol} 摆动点分析  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"当前价格: ${current_price:,.2f}")
    print(f"{'='*60}")

    tf_labels = {'1M': '月线', '1w': '周线', '1d': '日线', '4h': '4H'}
    tf_fmts   = {'1M': '%Y-%m', '1w': '%Y-%m-%d', '1d': '%Y-%m-%d', '4h': '%m-%d %H:%M'}

    for tf in ['1M', '1w', '1d', '4h']:
        cfg    = TF_CONFIG[tf]
        klines = fetch_klines(conn, symbol, tf, cfg['swing_klines'])

        if len(klines) < cfg['swing_window'] * 2 + 1:
            print(f"\n【{tf_labels[tf]}】数据不足，跳过")
            continue

        swing_highs, swing_lows = find_swing_points(
            klines, cfg['swing_window'], cfg['min_amplitude']
        )

        fmt = tf_fmts[tf]

        # 阻力：摆动高点在当前价格上方
        resistances = [p for p in swing_highs if p['price'] > current_price]
        resistances.sort(key=lambda x: x['price'])  # 由近到远

        # 支撑：摆动低点在当前价格下方
        supports = [p for p in swing_lows if p['price'] < current_price]
        supports.sort(key=lambda x: x['price'], reverse=True)  # 由近到远

        # 也把摆动高点在价格下方的算支撑（前高被跌破后转支撑）
        prev_highs_as_sup = [p for p in swing_highs if p['price'] < current_price]
        prev_highs_as_sup.sort(key=lambda x: x['price'], reverse=True)

        # 摆动低点在价格上方的算阻力（前低被突破后转阻力）
        prev_lows_as_res = [p for p in swing_lows if p['price'] > current_price]
        prev_lows_as_res.sort(key=lambda x: x['price'])

        print(f"\n【{tf_labels[tf]}】  共识别 {len(swing_highs)} 个摆动高点，{len(swing_lows)} 个摆动低点")
        print(f"{'─'*60}")

        print("  📉 阻力（摆动高点，由近到远）:")
        shown = 0
        for p in resistances[:MAX_LEVELS_PER_TF]:
            ts  = datetime.fromtimestamp(p['timestamp'] / 1000).strftime(fmt)
            dist = (p['price'] - current_price) / current_price * 100
            print(f"    ${p['price']:>10,.2f}  +{dist:.1f}%  {ts}")
            shown += 1
        for p in prev_lows_as_res[:max(0, MAX_LEVELS_PER_TF - shown)]:
            ts  = datetime.fromtimestamp(p['timestamp'] / 1000).strftime(fmt)
            dist = (p['price'] - current_price) / current_price * 100
            print(f"    ${p['price']:>10,.2f}  +{dist:.1f}%  {ts}  (前低转阻)")
        if not resistances and not prev_lows_as_res:
            print("    无")

        print("  📈 支撑（摆动低点，由近到远）:")
        shown = 0
        for p in supports[:MAX_LEVELS_PER_TF]:
            ts  = datetime.fromtimestamp(p['timestamp'] / 1000).strftime(fmt)
            dist = (current_price - p['price']) / current_price * 100
            print(f"    ${p['price']:>10,.2f}  -{dist:.1f}%  {ts}")
            shown += 1
        for p in prev_highs_as_sup[:max(0, MAX_LEVELS_PER_TF - shown)]:
            ts  = datetime.fromtimestamp(p['timestamp'] / 1000).strftime(fmt)
            dist = (current_price - p['price']) / current_price * 100
            print(f"    ${p['price']:>10,.2f}  -{dist:.1f}%  {ts}  (前高转支)")
        if not supports and not prev_highs_as_sup:
            print("    无")

    print(f"\n{'='*60}")


def main():
    conn = mysql.connector.connect(**DB_CONFIG)
    try:
        print_report(conn, SYMBOL)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
