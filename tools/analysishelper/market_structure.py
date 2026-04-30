#!/usr/bin/env python3
"""
市场结构分析工具

基于摆动点序列判断各周期的价格结构：
  - 上涨结构：更高高点（HH）+ 更高低点（HL）
  - 下跌结构：更低高点（LH）+ 更低低点（LL）
  - 震荡结构：高低点无明显方向
  - 结构破坏（BOS）：价格突破关键摆动点

所有参数集中在文件开头配置。
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mysql.connector
from decimal import Decimal
from datetime import datetime
from typing import Optional, List, Dict, Tuple

# ================================================================
# 参数配置
# ================================================================

DB_CONFIG = {
    'host':     'localhost',
    'port':     3306,
    'user':     'root',
    'password': '',
    'database': 'btc_assistant',
}

SYMBOL = 'BTCUSDT'

# 各周期配置（与 swing_points.py 保持一致）
TF_CONFIG = {
    '1M': {'swing_window': 3, 'swing_klines': 72,  'min_amplitude': 0.01},
    '1w': {'swing_window': 4, 'swing_klines': 156, 'min_amplitude': 0.008},
    '1d': {'swing_window': 5, 'swing_klines': 365, 'min_amplitude': 0.005},
    '4h': {'swing_window': 3, 'swing_klines': 300, 'min_amplitude': 0.003},
}

# 判断结构时使用最近几个摆动点（建议3-5）
STRUCTURE_LOOKBACK = 4

# ================================================================


def _f(v) -> Optional[float]:
    if v is None:
        return None
    return float(Decimal(v)) if isinstance(v, Decimal) else float(v)


def fetch_klines(conn, symbol: str, timeframe: str, limit: int) -> List[Dict]:
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
    """识别摆动高点和低点，按时间正序返回"""
    n = len(klines)
    highs_list = [k['high'] for k in klines]
    lows_list  = [k['low']  for k in klines]
    swing_highs, swing_lows = [], []

    for i in range(window, n - window):
        if all(highs_list[i] > highs_list[i-j] and highs_list[i] > highs_list[i+j]
               for j in range(1, window + 1)):
            surrounding = (sum(highs_list[i-window:i]) +
                           sum(highs_list[i+1:i+window+1])) / (window * 2)
            if surrounding > 0 and abs(highs_list[i] - surrounding) / surrounding >= min_amplitude:
                swing_highs.append({'price': highs_list[i],
                                    'timestamp': klines[i]['timestamp'], 'idx': i})

        if all(lows_list[i] < lows_list[i-j] and lows_list[i] < lows_list[i+j]
               for j in range(1, window + 1)):
            surrounding = (sum(lows_list[i-window:i]) +
                           sum(lows_list[i+1:i+window+1])) / (window * 2)
            if surrounding > 0 and abs(lows_list[i] - surrounding) / surrounding >= min_amplitude:
                swing_lows.append({'price': lows_list[i],
                                   'timestamp': klines[i]['timestamp'], 'idx': i})

    return swing_highs, swing_lows


def analyze_structure(swing_highs: List[Dict], swing_lows: List[Dict],
                      current_price: float, lookback: int) -> Dict:
    """
    分析价格结构。

    返回：
        structure   : 'uptrend' | 'downtrend' | 'ranging' | 'insufficient_data'
        hh_hl       : 更高高点+更高低点的数量
        lh_ll       : 更低高点+更低低点的数量
        recent_highs: 最近几个摆动高点
        recent_lows : 最近几个摆动低点
        bos         : 结构破坏信息
        description : 文字描述
    """
    recent_highs = swing_highs[-lookback:] if len(swing_highs) >= 2 else swing_highs
    recent_lows  = swing_lows[-lookback:]  if len(swing_lows)  >= 2 else swing_lows

    if len(recent_highs) < 2 or len(recent_lows) < 2:
        return {
            'structure': 'insufficient_data',
            'description': f'摆动点不足（高点{len(recent_highs)}个，低点{len(recent_lows)}个），需要至少各2个',
            'recent_highs': recent_highs,
            'recent_lows':  recent_lows,
            'bos': None,
        }

    # ── 判断高点序列 ──────────────────────────────────────────────
    high_prices = [p['price'] for p in recent_highs]
    hh_count = sum(1 for i in range(1, len(high_prices)) if high_prices[i] > high_prices[i-1])
    lh_count = sum(1 for i in range(1, len(high_prices)) if high_prices[i] < high_prices[i-1])

    # ── 判断低点序列 ──────────────────────────────────────────────
    low_prices = [p['price'] for p in recent_lows]
    hl_count = sum(1 for i in range(1, len(low_prices)) if low_prices[i] > low_prices[i-1])
    ll_count = sum(1 for i in range(1, len(low_prices)) if low_prices[i] < low_prices[i-1])

    total_pairs = len(high_prices) - 1

    # ── 综合判断 ──────────────────────────────────────────────────
    # 用最近2个高点和2个低点判断当前结构方向
    last_hh = high_prices[-1] > high_prices[-2]  # 最近高点更高
    last_hl = low_prices[-1]  > low_prices[-2]   # 最近低点更高

    if last_hh and last_hl:
        structure = 'uptrend'
    elif not last_hh and not last_hl:
        structure = 'downtrend'
    else:
        structure = 'ranging'

    # ── 结构破坏检测（BOS）────────────────────────────────────────
    bos = None
    last_swing_low  = recent_lows[-1]['price']
    last_swing_high = recent_highs[-1]['price']

    if structure == 'uptrend' and current_price < last_swing_low:
        bos = {
            'type': '上涨结构破坏',
            'level': last_swing_low,
            'desc': f'价格 ${current_price:,.0f} 跌破最近摆动低点 ${last_swing_low:,.0f}'
        }
    elif structure == 'downtrend' and current_price > last_swing_high:
        bos = {
            'type': '下跌结构破坏',
            'level': last_swing_high,
            'desc': f'价格 ${current_price:,.0f} 突破最近摆动高点 ${last_swing_high:,.0f}'
        }

    # ── 文字描述 ──────────────────────────────────────────────────
    high_seq = ' → '.join([f'${p:,.0f}' for p in high_prices])
    low_seq  = ' → '.join([f'${p:,.0f}' for p in low_prices])

    if structure == 'uptrend':
        desc = f'上涨结构（HH+HL）：高点 {high_seq}，低点 {low_seq}'
    elif structure == 'downtrend':
        desc = f'下跌结构（LH+LL）：高点 {high_seq}，低点 {low_seq}'
    else:
        if last_hh and not last_hl:
            desc = f'震荡（高点抬高但低点降低，扩张）：高点 {high_seq}，低点 {low_seq}'
        elif not last_hh and last_hl:
            desc = f'震荡（高点降低但低点抬高，收缩）：高点 {high_seq}，低点 {low_seq}'
        else:
            desc = f'震荡：高点 {high_seq}，低点 {low_seq}'

    return {
        'structure':     structure,
        'description':   desc,
        'recent_highs':  recent_highs,
        'recent_lows':   recent_lows,
        'hh_count':      hh_count,
        'lh_count':      lh_count,
        'hl_count':      hl_count,
        'll_count':      ll_count,
        'bos':           bos,
    }


def print_report(conn, symbol: str):
    # 当前价格
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT close FROM klines WHERE symbol=%s AND timeframe='4h' "
        "ORDER BY timestamp DESC LIMIT 1", (symbol,)
    )
    row = cursor.fetchone()
    cursor.close()
    current_price = _f(row['close']) if row else 0

    print(f"\n{'='*60}")
    print(f"📐 {symbol} 市场结构分析  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"当前价格: ${current_price:,.2f}")
    print(f"{'='*60}")

    tf_labels = {'1M': '月线', '1w': '周线', '1d': '日线', '4h': '4H'}
    tf_fmts   = {'1M': '%Y-%m', '1w': '%Y-%m-%d', '1d': '%Y-%m-%d', '4h': '%m-%d %H:%M'}

    structure_icon = {
        'uptrend':          '🟢 上涨结构',
        'downtrend':        '🔴 下跌结构',
        'ranging':          '🟡 震荡结构',
        'insufficient_data':'⚪ 数据不足',
    }

    for tf in ['1M', '1w', '1d', '4h']:
        cfg    = TF_CONFIG[tf]
        klines = fetch_klines(conn, symbol, tf, cfg['swing_klines'])
        fmt    = tf_fmts[tf]

        if len(klines) < cfg['swing_window'] * 2 + 1:
            print(f"\n【{tf_labels[tf]}】数据不足，跳过")
            continue

        swing_highs, swing_lows = find_swing_points(
            klines, cfg['swing_window'], cfg['min_amplitude']
        )

        result = analyze_structure(swing_highs, swing_lows,
                                   current_price, STRUCTURE_LOOKBACK)

        icon = structure_icon.get(result['structure'], '⚪')
        print(f"\n【{tf_labels[tf]}】  {icon}")
        print(f"{'─'*60}")
        print(f"  {result['description']}")

        # 最近摆动点详情
        if result['recent_highs'] and result['recent_lows']:
            print(f"\n  摆动高点（最近{len(result['recent_highs'])}个）:")
            for p in result['recent_highs']:
                ts = datetime.fromtimestamp(p['timestamp'] / 1000).strftime(fmt)
                dist = (p['price'] - current_price) / current_price * 100
                sign = '+' if dist >= 0 else ''
                print(f"    ${p['price']:>10,.2f}  {sign}{dist:.1f}%  {ts}")

            print(f"\n  摆动低点（最近{len(result['recent_lows'])}个）:")
            for p in result['recent_lows']:
                ts = datetime.fromtimestamp(p['timestamp'] / 1000).strftime(fmt)
                dist = (p['price'] - current_price) / current_price * 100
                sign = '+' if dist >= 0 else ''
                print(f"    ${p['price']:>10,.2f}  {sign}{dist:.1f}%  {ts}")

        # 结构破坏
        if result['bos']:
            print(f"\n  ⚠️  {result['bos']['type']}: {result['bos']['desc']}")

    print(f"\n{'='*60}")


def main():
    conn = mysql.connector.connect(**DB_CONFIG)
    try:
        print_report(conn, SYMBOL)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
