#!/usr/bin/env python3
"""
动态位识别工具

输出4个周期（1M/1w/1d/4h）的最新均线和布林带值。
用倒数第二根K线（已收盘），避免未收盘数据不稳定。
所有参数集中在文件开头配置。
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mysql.connector
import requests
from decimal import Decimal
from datetime import datetime
from typing import Optional

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

# ================================================================


def _f(v) -> Optional[float]:
    if v is None:
        return None
    return float(Decimal(v)) if isinstance(v, Decimal) else float(v)


def get_current_price(symbol: str) -> Optional[float]:
    """从 Binance 获取实时价格，失败时返回 None"""
    try:
        resp = requests.get(
            'https://api.binance.com/api/v3/ticker/price',
            params={'symbol': symbol}, timeout=5
        )
        resp.raise_for_status()
        return float(resp.json()['price'])
    except Exception:
        return None


def fetch_dynamic_levels(conn, symbol: str, timeframe: str) -> Optional[dict]:
    """
    取倒数第二根K线（已收盘）的均线和布林带值。
    实盘模式下避免未收盘K线数据不稳定。
    """
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT timestamp, close, "
        "ema7, ema12, ema25, ema50, "
        "boll_up, boll_md, boll_dn, "
        "rsi6, rsi14, dif, dea, macd "
        "FROM klines WHERE symbol=%s AND timeframe=%s "
        "ORDER BY timestamp DESC LIMIT 2",
        (symbol, timeframe)
    )
    rows = cursor.fetchall()
    cursor.close()

    if len(rows) < 2:
        return None

    # 用倒数第二根（已收盘）
    r = rows[1]
    return {
        'timestamp': r['timestamp'],
        'close':     _f(r['close']),
        'ema7':      _f(r['ema7']),
        'ema12':     _f(r['ema12']),
        'ema25':     _f(r['ema25']),
        'ema50':     _f(r['ema50']),
        'boll_up':   _f(r['boll_up']),
        'boll_md':   _f(r['boll_md']),
        'boll_dn':   _f(r['boll_dn']),
        'rsi6':      _f(r['rsi6']),
        'rsi14':     _f(r['rsi14']),
        'dif':       _f(r['dif']),
        'dea':       _f(r['dea']),
        'macd':      _f(r['macd']),
    }


def print_report(conn, symbol: str):
    # 实时价格
    current_price = get_current_price(symbol)
    if current_price is None:
        # 降级用最新4H收盘价
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT close FROM klines WHERE symbol=%s AND timeframe='4h' "
            "ORDER BY timestamp DESC LIMIT 1", (symbol,)
        )
        row = cursor.fetchone()
        cursor.close()
        current_price = _f(row['close']) if row else 0

    print(f"\n{'='*60}")
    print(f"📊 {symbol} 动态位分析  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"当前价格: ${current_price:,.2f}")
    print(f"{'='*60}")

    tf_labels = {'1M': '月线', '1w': '周线', '1d': '日线', '4h': '4H'}
    tf_fmts   = {'1M': '%Y-%m', '1w': '%Y-%m-%d', '1d': '%Y-%m-%d', '4h': '%m-%d %H:%M'}

    for tf in ['1M', '1w', '1d', '4h']:
        data = fetch_dynamic_levels(conn, symbol, tf)
        if data is None:
            print(f"\n【{tf_labels[tf]}】数据不足，跳过")
            continue

        ts_str = datetime.fromtimestamp(data['timestamp'] / 1000).strftime(tf_fmts[tf])
        print(f"\n【{tf_labels[tf]}】  数据时间: {ts_str}  收盘: ${data['close']:,.2f}")
        print(f"{'─'*60}")

        # 指标行
        rsi6  = data.get('rsi6')
        rsi14 = data.get('rsi14')
        dif   = data.get('dif')
        dea   = data.get('dea')
        macd  = data.get('macd')

        rsi_str  = f"RSI6={rsi6:.1f}  RSI14={rsi14:.1f}" if rsi6 and rsi14 else ''
        macd_str = ''
        if dif is not None and dea is not None and macd is not None:
            macd_str = f"DIF={dif:.2f}  DEA={dea:.2f}  MACD={macd:.2f}"
        if rsi_str or macd_str:
            print(f"  {rsi_str}{'  ' if rsi_str and macd_str else ''}{macd_str}")

        # 均线和布林带，按价格从高到低排列，标注与当前价格的关系
        levels = []
        indicators = [
            ('EMA7',    data['ema7']),
            ('EMA12',   data['ema12']),
            ('EMA25',   data['ema25']),
            ('EMA50',   data['ema50']),
            ('布林上轨', data['boll_up']),
            ('布林中轨', data['boll_md']),
            ('布林下轨', data['boll_dn']),
        ]
        for name, val in indicators:
            if val is None:
                continue
            dist = (val - current_price) / current_price * 100
            side = '阻力' if val > current_price else '支撑'
            levels.append((val, name, dist, side))

        # 按价格从高到低排列
        levels.sort(key=lambda x: x[0], reverse=True)

        # 找当前价格插入位置，加一条分隔线
        printed_separator = False
        for val, name, dist, side in levels:
            if not printed_separator and val < current_price:
                print(f"  {'─'*20} 当前价格 ${current_price:,.2f} {'─'*20}")
                printed_separator = True
            sign = '+' if dist >= 0 else ''
            print(f"  ${val:>10,.2f}  {sign}{dist:>6.1f}%  {name:6}  {side}")

        if not printed_separator:
            print(f"  {'─'*20} 当前价格 ${current_price:,.2f} {'─'*20}")

    # ── 综合分析：所有周期动态位汇总，按距当前价格排序 ──────────
    print(f"\n{'='*60}")
    print("🔥 综合动态位（所有周期，由近到远）")
    print(f"{'='*60}")

    all_levels = []
    for tf in ['1M', '1w', '1d', '4h']:
        data = fetch_dynamic_levels(conn, symbol, tf)
        if data is None:
            continue
        tf_lbl = tf_labels[tf]
        indicators = [
            ('EMA7',    data['ema7']),
            ('EMA12',   data['ema12']),
            ('EMA25',   data['ema25']),
            ('EMA50',   data['ema50']),
            ('布林上轨', data['boll_up']),
            ('布林中轨', data['boll_md']),
            ('布林下轨', data['boll_dn']),
        ]
        for name, val in indicators:
            if val is None:
                continue
            dist = (val - current_price) / current_price * 100
            side = '阻力' if val > current_price else '支撑'
            all_levels.append({
                'price': val,
                'name':  name,
                'tf':    tf_lbl,
                'dist':  dist,
                'side':  side,
            })

    resistances = sorted([l for l in all_levels if l['side'] == '阻力'],
                         key=lambda x: x['dist'])
    supports    = sorted([l for l in all_levels if l['side'] == '支撑'],
                         key=lambda x: -x['dist'])

    print("\n  📉 阻力（由远到近）:")
    for lv in reversed(resistances):
        print(f"    ${lv['price']:>10,.2f}  +{lv['dist']:>5.1f}%  {lv['tf']:4}  {lv['name']}")

    print(f"\n  {'─'*20} 当前价格 ${current_price:,.2f} {'─'*20}")

    print("\n  📈 支撑（由近到远）:")
    for lv in supports:
        print(f"    ${lv['price']:>10,.2f}  -{abs(lv['dist']):>5.1f}%  {lv['tf']:4}  {lv['name']}")

    # 最近支撑阻力和盈亏比
    if resistances and supports:
        nr = resistances[0]
        ns = supports[0]
        rr = (nr['price'] - current_price) / (current_price - ns['price'])
        rr_tag = '✅ 可做多' if rr >= 2 else '⚠️ 盈亏比不足'
        print(f"\n  💡 上方最近阻力: ${nr['price']:,.2f} ({nr['tf']} {nr['name']})  "
              f"+{nr['dist']:.1f}%")
        print(f"     下方最近支撑: ${ns['price']:,.2f} ({ns['tf']} {ns['name']})  "
              f"-{abs(ns['dist']):.1f}%")
        print(f"     盈亏比(做多): {rr:.2f}  {rr_tag}")

    print(f"\n{'='*60}")


def main():
    conn = mysql.connector.connect(**DB_CONFIG)
    try:
        print_report(conn, SYMBOL)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
