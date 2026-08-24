"""
恐慌贪婪指数 MA14 择时策略回测。

规则:
  - 买入: FNG 的 MA14 向上首次突破 20 (前一日 <=20, 当日 >20), 当日 BTC 收盘价买入 10000 USDT。
  - 卖出: 持仓后, MA14 向下首次跌破 60 (前一日 >=60, 当日 <60), 当日收盘价卖出。
  - 平仓后重新等待下一次 "上穿20" 信号。

MA14 = 恐贪指数 14 日简单移动平均 (直接取 btc_fng.ma14)。
数据来源: btc_fng + klines 日线收盘价。金额单位: 美元。
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from backend.backtest.config import config  # noqa: E402
import mysql.connector  # noqa: E402

START_DATE = None         # None=全量; 或 "2024-01-01"
TRADE_USD = 10000.0
BUY_LEVEL = 20            # MA14 上穿此值买入
SELL_LEVEL = 75          # MA14 下穿此值卖出


def get_conn():
    db = config.get_database_config()
    return mysql.connector.connect(
        host=db.get("host", "localhost"), port=int(db.get("port", 3306)),
        user=db.get("user", "root"), password=db.get("password", ""),
        database=db.get("database", "btc_assistant"), charset="utf8mb4",
    )


def load_data():
    """返回按日期升序: [{date, ma14, price}]。"""
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    if START_DATE:
        cur.execute("SELECT stat_date, ma14 FROM btc_fng WHERE stat_date >= %s ORDER BY stat_date ASC", (START_DATE,))
    else:
        cur.execute("SELECT stat_date, ma14 FROM btc_fng ORDER BY stat_date ASC")
    fng = cur.fetchall()

    cur.execute("SELECT timestamp, close FROM klines WHERE symbol='BTCUSDT' AND timeframe='1d' ORDER BY timestamp ASC")
    price_map = {}
    for r in cur.fetchall():
        d = datetime.fromtimestamp(r["timestamp"] / 1000, tz=timezone.utc).date()
        price_map[d.isoformat()] = float(r["close"]) if r["close"] else None
    cur.close()
    conn.close()

    rows = []
    for r in fng:
        diso = r["stat_date"].isoformat()
        rows.append({
            "date": diso,
            "ma14": float(r["ma14"]) if r["ma14"] is not None else None,
            "price": price_map.get(diso),
        })
    return rows


def backtest(rows):
    trades = []
    position = None
    prev = None
    for row in rows:
        m, price = row["ma14"], row["price"]
        if m is None:
            prev = None  # 窗口未满, 中断跨越判断
            continue
        if prev is not None:
            if position is None:
                if prev <= BUY_LEVEL and m > BUY_LEVEL and price:
                    qty = TRADE_USD / price
                    position = {"buy_date": row["date"], "buy_price": price, "qty": qty, "buy_ma": m}
            else:
                if prev >= SELL_LEVEL and m < SELL_LEVEL and price:
                    pnl = (price - position["buy_price"]) * position["qty"]
                    pnl_pct = (price / position["buy_price"] - 1) * 100
                    d0 = datetime.fromisoformat(position["buy_date"]).date()
                    d1 = datetime.fromisoformat(row["date"]).date()
                    trades.append({**position, "sell_date": row["date"], "sell_price": price,
                                   "sell_ma": m, "pnl": pnl, "pnl_pct": pnl_pct,
                                   "hold_days": (d1 - d0).days, "status": "closed"})
                    position = None
        prev = m

    if position is not None:
        last = next((r for r in reversed(rows) if r["price"]), None)
        if last:
            price = last["price"]
            pnl = (price - position["buy_price"]) * position["qty"]
            pnl_pct = (price / position["buy_price"] - 1) * 100
            d0 = datetime.fromisoformat(position["buy_date"]).date()
            d1 = datetime.fromisoformat(last["date"]).date()
            trades.append({**position, "sell_date": last["date"] + " (未平仓)", "sell_price": price,
                           "sell_ma": None, "pnl": pnl, "pnl_pct": pnl_pct,
                           "hold_days": (d1 - d0).days, "status": "open"})
    return trades


def main():
    rows = load_data()
    print(f"数据区间: {rows[0]['date']} ~ {rows[-1]['date']} (共 {len(rows)} 天)")
    print(f"规则: FNG MA14 上穿 {BUY_LEVEL} 买入, 下穿 {SELL_LEVEL} 卖出, 每次 {TRADE_USD:,.0f} USDT\n")
    trades = backtest(rows)
    if not trades:
        print("区间内没有产生任何交易信号。")
        return

    print(f"{'#':>2}  {'买入日期':<12} {'买入价':>10} {'买MA':>6}  {'卖出日期':<18} {'卖出价':>10} {'卖MA':>6}  "
          f"{'持有天':>5}  {'收益(USD)':>11}  {'收益率':>8}")
    print("-" * 112)
    total_pnl, wins = 0.0, 0
    for i, t in enumerate(trades, 1):
        total_pnl += t["pnl"]
        if t["pnl"] > 0:
            wins += 1
        sma = f"{t['sell_ma']:.1f}" if t["sell_ma"] is not None else "-"
        flag = " *持仓中" if t["status"] == "open" else ""
        print(f"{i:>2}  {t['buy_date']:<12} {t['buy_price']:>10,.0f} {t['buy_ma']:>6.1f}  "
              f"{t['sell_date']:<18} {t['sell_price']:>10,.0f} {sma:>6}  "
              f"{t['hold_days']:>5}  {t['pnl']:>+11,.2f}  {t['pnl_pct']:>+7.2f}%{flag}")

    n = len(trades)
    closed = [t for t in trades if t["status"] == "closed"]
    invested = TRADE_USD * n
    print("-" * 112)
    print(f"\n总交易笔数: {n} (已平仓 {len(closed)}, 持仓中 {n-len(closed)})")
    print(f"胜率: {wins}/{n} = {wins/n*100:.1f}%")
    print(f"累计投入本金: {invested:,.0f} USD (每笔 {TRADE_USD:,.0f})")
    print(f"总收益: {total_pnl:+,.2f} USD")
    print(f"总收益率(相对每笔本金累加): {total_pnl/invested*100:+.2f}%")


if __name__ == "__main__":
    main()
