#!/usr/bin/env python3
"""
K线数据查看工具

拉取4个周期最新N根K线的完整数据并输出。
支持终端输出（简洁）和文件输出（完整CSV）。
所有参数集中在文件开头配置。
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mysql.connector
import csv
from decimal import Decimal
from datetime import datetime
from typing import Optional, List, Dict

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

# 各周期拉取的K线数量
N_KLINES = {
    '1M': 12,   # 最近12根月线
    '1w': 20,   # 最近20根周线
    '1d': 30,   # 最近30根日线
    '4h': 48,   # 最近48根4H
}

# 输出到文件（None=只输出终端，填路径则同时输出CSV）
OUTPUT_FILE = '/tmp/klines_data.csv'

# 终端输出时每个周期显示的列（太多会换行）
TERMINAL_COLS = ['time', 'open', 'high', 'low', 'close', 'volume',
                 'ema7', 'ema25', 'rsi14', 'macd', 'atr']

# ================================================================


def _f(v, decimals=2) -> str:
    if v is None:
        return 'N/A'
    val = float(Decimal(v)) if isinstance(v, Decimal) else float(v)
    return f'{val:,.{decimals}f}'


def fetch_klines(conn, symbol: str, timeframe: str, limit: int) -> List[Dict]:
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT timestamp, open, high, low, close, volume, "
        "ema7, ema12, ema25, ema50, ma5, ma10, "
        "dif, dea, macd, rsi6, rsi14, "
        "boll_up, boll_md, boll_dn, atr "
        "FROM klines WHERE symbol=%s AND timeframe=%s "
        "ORDER BY timestamp DESC LIMIT %s",
        (symbol, timeframe, limit)
    )
    rows = list(reversed(cursor.fetchall()))
    cursor.close()
    return rows


def format_row(row: Dict, timeframe: str) -> Dict:
    """格式化一行数据"""
    tf_fmt = {'1M': '%Y-%m', '1w': '%Y-%m-%d', '1d': '%Y-%m-%d', '4h': '%m-%d %H:%M'}
    ts = datetime.fromtimestamp(row['timestamp'] / 1000).strftime(tf_fmt.get(timeframe, '%m-%d %H:%M'))
    return {
        'time':     ts,
        'open':     _f(row['open']),
        'high':     _f(row['high']),
        'low':      _f(row['low']),
        'close':    _f(row['close']),
        'volume':   _f(row['volume'], 0),
        'ema7':     _f(row['ema7']),
        'ema12':    _f(row['ema12']),
        'ema25':    _f(row['ema25']),
        'ema50':    _f(row['ema50']),
        'ma5':      _f(row['ma5']),
        'ma10':     _f(row['ma10']),
        'dif':      _f(row['dif']),
        'dea':      _f(row['dea']),
        'macd':     _f(row['macd']),
        'rsi6':     _f(row['rsi6'], 1),
        'rsi14':    _f(row['rsi14'], 1),
        'boll_up':  _f(row['boll_up']),
        'boll_md':  _f(row['boll_md']),
        'boll_dn':  _f(row['boll_dn']),
        'atr':      _f(row['atr']),
    }


def print_terminal(rows: List[Dict], timeframe: str, cols: List[str]):
    """终端输出（只显示指定列）"""
    tf_labels = {'1M': '月线', '1w': '周线', '1d': '日线', '4h': '4H'}
    formatted = [format_row(r, timeframe) for r in rows]

    # 计算每列宽度
    widths = {c: max(len(c), max(len(r[c]) for r in formatted)) for c in cols}

    # 表头
    header = '  '.join(c.ljust(widths[c]) for c in cols)
    sep    = '  '.join('─' * widths[c] for c in cols)
    print(f"\n【{tf_labels.get(timeframe, timeframe)}】  共{len(rows)}根")
    print(f"{'─'*60}")
    print(header)
    print(sep)
    for r in formatted:
        print('  '.join(r[c].ljust(widths[c]) for c in cols))


def write_csv(all_data: Dict[str, List[Dict]], filepath: str):
    """输出完整CSV文件"""
    all_cols = ['timeframe', 'time', 'open', 'high', 'low', 'close', 'volume',
                'ema7', 'ema12', 'ema25', 'ema50', 'ma5', 'ma10',
                'dif', 'dea', 'macd', 'rsi6', 'rsi14',
                'boll_up', 'boll_md', 'boll_dn', 'atr']

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=all_cols)
        writer.writeheader()
        for tf, rows in all_data.items():
            for row in rows:
                fmt = format_row(row, tf)
                fmt['timeframe'] = tf
                writer.writerow(fmt)

    print(f"\n📁 完整数据已保存到: {filepath}")


def main():
    conn = mysql.connector.connect(**DB_CONFIG)
    try:
        print(f"\n{'='*60}")
        print(f"📊 {SYMBOL} K线数据  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*60}")

        all_data = {}
        for tf in ['1M', '1w', '1d', '4h']:
            n = N_KLINES.get(tf, 20)
            rows = fetch_klines(conn, SYMBOL, tf, n)
            all_data[tf] = rows
            print_terminal(rows, tf, TERMINAL_COLS)

        if OUTPUT_FILE:
            write_csv(all_data, OUTPUT_FILE)

        print(f"\n{'='*60}")
    finally:
        conn.close()


if __name__ == '__main__':
    main()
