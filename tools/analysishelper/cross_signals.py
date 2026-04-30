#!/usr/bin/env python3
"""
金叉死叉状态判断工具

判断各周期当前是否处于金叉/死叉状态，以及是否刚发生穿越。
所有参数集中在文件开头配置。

判断逻辑：
  - 当前状态：当前根的指标关系（DIF > DEA 为金叉状态）
  - 刚发生穿越：前一根是死叉状态，当前根变为金叉状态（反之亦然）
  - MACD 柱体：连续3根的方向变化（扩张/收缩）
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mysql.connector
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

# 取多少根K线用于判断（至少需要3根）
LOOKBACK = 3

# ================================================================


def _f(v) -> Optional[float]:
    if v is None:
        return None
    return float(Decimal(v)) if isinstance(v, Decimal) else float(v)


def fetch_klines(conn, symbol: str, timeframe: str, limit: int) -> List[Dict]:
    """取最近 N 根K线（正序），用倒数第二根作为当前已收盘"""
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT timestamp, close, "
        "ema7, ema25, ema50, "
        "dif, dea, macd, "
        "rsi6, rsi14 "
        "FROM klines WHERE symbol=%s AND timeframe=%s "
        "ORDER BY timestamp DESC LIMIT %s",
        (symbol, timeframe, limit + 1)  # 多取一根，用倒数第二根作当前
    )
    rows = list(reversed(cursor.fetchall()))
    cursor.close()
    # 去掉最新一根（未收盘），用已收盘数据
    if len(rows) > 1:
        rows = rows[:-1]
    return [{k: _f(v) if k != 'timestamp' else v for k, v in r.items()}
            for r in rows]


def _cross_status(a_cur, b_cur, a_prev, b_prev, label_a, label_b):
    """
    判断 a 和 b 的金叉/死叉状态。
    返回：(状态描述, 是否刚发生穿越, 图标)
    """
    if any(v is None for v in [a_cur, b_cur, a_prev, b_prev]):
        return None, False, ''

    golden_now  = a_cur  > b_cur
    golden_prev = a_prev > b_prev
    just_cross  = golden_now != golden_prev  # 刚发生穿越

    if golden_now:
        icon   = '🟢'
        status = f'{label_a} > {label_b}（金叉状态）'
    else:
        icon   = '🔴'
        status = f'{label_a} < {label_b}（死叉状态）'

    if just_cross:
        cross_type = '⚡刚发生金叉' if golden_now else '⚡刚发生死叉'
        status = f'{status}  {cross_type}'

    return status, just_cross, icon


def _macd_bar_trend(bars: List[Optional[float]]) -> str:
    """
    判断 MACD 柱体趋势（最近3根）。
    bars: [最早, 中间, 最新]，用绝对值判断扩张/收缩
    """
    valid = [b for b in bars if b is not None]
    if len(valid) < 2:
        return ''

    abs_bars = [abs(b) for b in valid]
    if len(abs_bars) >= 3:
        if abs_bars[-1] > abs_bars[-2] > abs_bars[-3]:
            trend = '扩张↑↑'
        elif abs_bars[-1] < abs_bars[-2] < abs_bars[-3]:
            trend = '收缩↓↓'
        elif abs_bars[-1] > abs_bars[-2]:
            trend = '扩张↑'
        elif abs_bars[-1] < abs_bars[-2]:
            trend = '收缩↓'
        else:
            trend = '持平'
    else:
        trend = '扩张↑' if abs_bars[-1] > abs_bars[-2] else '收缩↓'

    # 红柱/绿柱
    color = '红柱' if valid[-1] > 0 else '绿柱'
    return f'{color} {trend}'


def analyze_tf(conn, symbol: str, timeframe: str) -> List[str]:
    """分析单个周期，返回输出行列表"""
    bars = fetch_klines(conn, symbol, timeframe, LOOKBACK)
    if len(bars) < 2:
        return [f"  数据不足（需要至少2根已收盘K线）"]

    cur  = bars[-1]   # 当前已收盘
    prev = bars[-2]   # 前一根

    tf_fmt = {'1M': '%Y-%m', '1w': '%Y-%m-%d', '1d': '%Y-%m-%d', '4h': '%m-%d %H:%M'}
    ts_str = datetime.fromtimestamp(cur['timestamp'] / 1000).strftime(
        tf_fmt.get(timeframe, '%m-%d %H:%M'))

    lines = [f"  数据时间: {ts_str}  收盘: ${cur['close']:,.2f}"]

    # ── 均线金叉死叉 ──────────────────────────────────────────────
    lines.append("  【均线】")

    # EMA7 vs EMA25
    status, just, icon = _cross_status(
        cur['ema7'], cur['ema25'], prev['ema7'], prev['ema25'], 'EMA7', 'EMA25')
    if status:
        lines.append(f"    {icon} EMA7/EMA25: {status}")

    # EMA25 vs EMA50
    status, just, icon = _cross_status(
        cur['ema25'], cur['ema50'], prev['ema25'], prev['ema50'], 'EMA25', 'EMA50')
    if status:
        lines.append(f"    {icon} EMA25/EMA50: {status}")

    # ── MACD ─────────────────────────────────────────────────────
    lines.append("  【MACD】")

    # DIF vs DEA（金叉死叉）
    status, just, icon = _cross_status(
        cur['dif'], cur['dea'], prev['dif'], prev['dea'], 'DIF', 'DEA')
    if status:
        # 加零轴位置说明
        zero_pos = ''
        if cur['dif'] is not None:
            zero_pos = '零轴上方' if cur['dif'] > 0 else '零轴下方'
        lines.append(f"    {icon} DIF/DEA: {status}  [{zero_pos}]")

    # MACD 柱体趋势
    macd_bars = [b['macd'] for b in bars]
    bar_trend = _macd_bar_trend(macd_bars)
    if bar_trend:
        dif_val = cur['dif']
        dea_val = cur['dea']
        macd_val = cur['macd']
        vals = ''
        if all(v is not None for v in [dif_val, dea_val, macd_val]):
            vals = f"  DIF={dif_val:.2f}  DEA={dea_val:.2f}  柱={macd_val:.2f}"
        lines.append(f"    📊 柱体: {bar_trend}{vals}")

    # ── RSI ──────────────────────────────────────────────────────
    lines.append("  【RSI】")
    rsi6  = cur.get('rsi6')
    rsi14 = cur.get('rsi14')
    if rsi6 and rsi14:
        # RSI6 vs RSI14 穿越
        status, just, icon = _cross_status(
            rsi6, rsi14, prev.get('rsi6'), prev.get('rsi14'), 'RSI6', 'RSI14')
        if status:
            lines.append(f"    {icon} RSI6/RSI14: {status}")

        # 超买超卖
        rsi_signals = []
        if rsi14 < 30:
            rsi_signals.append(f"RSI14={rsi14:.1f} 🔵超卖")
        elif rsi14 > 70:
            rsi_signals.append(f"RSI14={rsi14:.1f} 🔴超买")
        else:
            rsi_signals.append(f"RSI14={rsi14:.1f}")
        if rsi6 < 20:
            rsi_signals.append(f"RSI6={rsi6:.1f} 极度超卖")
        elif rsi6 > 80:
            rsi_signals.append(f"RSI6={rsi6:.1f} 极度超买")
        else:
            rsi_signals.append(f"RSI6={rsi6:.1f}")
        lines.append(f"    📈 {' | '.join(rsi_signals)}")

    return lines


def print_report(conn, symbol: str):
    print(f"\n{'='*60}")
    print(f"⚡ {symbol} 金叉死叉状态  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}")

    tf_labels = {'1M': '月线', '1w': '周线', '1d': '日线', '4h': '4H'}

    for tf in ['1M', '1w', '1d', '4h']:
        print(f"\n【{tf_labels[tf]}】")
        print(f"{'─'*60}")
        lines = analyze_tf(conn, symbol, tf)
        for line in lines:
            print(line)

    print(f"\n{'='*60}")


def main():
    conn = mysql.connector.connect(**DB_CONFIG)
    try:
        print_report(conn, SYMBOL)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
