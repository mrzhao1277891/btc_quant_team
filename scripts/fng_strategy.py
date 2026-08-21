"""
恐慌贪婪指数极端反转策略回测。

规则:
  - 买入: FNG 向上首次突破 20 (前一日 <=20, 当日 >20), 以当日 BTC 收盘价买入 10000 USDT。
  - 卖出: 持仓后, FNG 向下首次跌破 80 (前一日 >=80, 当日 <80), 以当日 BTC 收盘价卖出。
  - 平仓后重新等待下一次 "上穿20" 信号。

数据来源: btc_fng + klines 日线收盘价 (按 UTC 日期对齐)。
金额单位: 美元。
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
BUY_LEVEL = 20            # 上穿此值买入
SELL_LEVEL = 80          # 下穿此值卖出


def get_conn():
    db = config.get_database_config()
    return mysql.connector.connect(
        host=db.get("host", "localhost"), port=int(db.get("port", 3306)),
        user=db.get("user", "root"), password=db.get("password", ""),
        database=db.get("database", "btc_assistant"), charset="utf8mb4",
    )


def load_data():
    """返回按日期升序: [{date, fng, price}]。"""
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    if START_DATE:
        cur.execute("SELECT stat_date, fng_value FROM btc_fng WHERE stat_date >= %s ORDER BY stat_date ASC", (START_DATE,))
    else:
        cur.execute("SELECT stat_date, fng_value FROM btc_fng ORDER BY stat_date ASC")
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
        rows.append({"date": diso, "fng": int(r["fng_value"]), "price": price_map.get(diso)})
    return rows


def backtest(rows):
    trades = []
    position = None
    prev = None
    for row in rows:
        fng, price = row["fng"], row["price"]
        if prev is not None:
            if position is None:
                # 买入: 上穿 BUY_LEVEL
                if prev <= BUY_LEVEL and fng > BUY_LEVEL and price:
                    qty = TRADE_USD / price
                    position = {"buy_date": row["date"], "buy_price": price, "qty": qty, "buy_fng": fng}
            else:
                # 卖出: 下穿 SELL_LEVEL
                if prev >= SELL_LEVEL and fng < SELL_LEVEL and price:
                    pnl = (price - position["buy_price"]) * position["qty"]
                    pnl_pct = (price / position["buy_price"] - 1) * 100
                    d0 = datetime.fromisoformat(position["buy_date"]).date()
                    d1 = datetime.fromisoformat(row["date"]).date()
                    trades.append({**position, "sell_date": row["date"], "sell_price": price,
                                   "sell_fng": fng, "pnl": pnl, "pnl_pct": pnl_pct,
                                   "hold_days": (d1 - d0).days, "status": "closed"})
                    position = None
        prev = fng

    # 期末仍持仓: 用最后有价格的收盘价做浮盈
    if position is not None:
        last = next((r for r in reversed(rows) if r["price"]), None)
        if last:
            price = last["price"]
            pnl = (price - position["buy_price"]) * position["qty"]
            pnl_pct = (price / position["buy_price"] - 1) * 100
            d0 = datetime.fromisoformat(position["buy_date"]).date()
            d1 = datetime.fromisoformat(last["date"]).date()
            trades.append({**position, "sell_date": last["date"] + " (未平仓)", "sell_price": price,
                           "sell_fng": None, "pnl": pnl, "pnl_pct": pnl_pct,
                           "hold_days": (d1 - d0).days, "status": "open"})
    return trades


def main():
    rows = load_data()
    print(f"数据区间: {rows[0]['date']} ~ {rows[-1]['date']} (共 {len(rows)} 天)")
    print(f"规则: FNG 上穿 {BUY_LEVEL} 买入, 下穿 {SELL_LEVEL} 卖出, 每次 {TRADE_USD:,.0f} USDT\n")
    trades = backtest(rows)
    if not trades:
        print("区间内没有产生任何交易信号。")
        return

    print(f"{'#':>2}  {'买入日期':<12} {'买入价':>10} {'买FNG':>5}  {'卖出日期':<18} {'卖出价':>10} {'卖FNG':>5}  "
          f"{'持有天':>5}  {'收益(USD)':>11}  {'收益率':>8}")
    print("-" * 108)
    total_pnl = 0.0
    wins = 0
    for i, t in enumerate(trades, 1):
        total_pnl += t["pnl"]
        if t["pnl"] > 0:
            wins += 1
        sfng = t["sell_fng"] if t["sell_fng"] is not None else "-"
        flag = " *持仓中" if t["status"] == "open" else ""
        print(f"{i:>2}  {t['buy_date']:<12} {t['buy_price']:>10,.0f} {t['buy_fng']:>5}  "
              f"{t['sell_date']:<18} {t['sell_price']:>10,.0f} {str(sfng):>5}  "
              f"{t['hold_days']:>5}  {t['pnl']:>+11,.2f}  {t['pnl_pct']:>+7.2f}%{flag}")

    n = len(trades)
    closed = [t for t in trades if t["status"] == "closed"]
    invested = TRADE_USD * n
    print("-" * 108)
    print(f"\n总交易笔数: {n} (已平仓 {len(closed)}, 持仓中 {n-len(closed)})")
    print(f"胜率: {wins}/{n} = {wins/n*100:.1f}%")
    print(f"累计投入本金: {invested:,.0f} USD (每笔 {TRADE_USD:,.0f})")
    print(f"总收益: {total_pnl:+,.2f} USD")
    print(f"总收益率(相对每笔本金累加): {total_pnl/invested*100:+.2f}%")


if __name__ == "__main__":
    main()
