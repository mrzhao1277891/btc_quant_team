"""
ETF MA14 择时策略回测。

规则:
  - 买入: ETF 净流入的 MA14 连续 >=7 天为负后, 首次转正当日, 以 BTC 日收盘价买入 10000 USDT。
  - 卖出: 持仓后, MA14 首次转负当日, 以 BTC 日收盘价卖出。
  - 平仓后重新计数, 等待下一个 "连续7天负 -> 转正" 信号。
  - 回测区间: 2024-01-01 起。

数据来源: btc_etf_flow (MA14) + klines 日线收盘价 (按 UTC 日期对齐)。
单位: 净流入=百万美元, 价格/金额=美元。
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from backend.backtest.config import config  # noqa: E402
import mysql.connector  # noqa: E402

START_DATE = "2024-01-01"
TRADE_USD = 10000.0       # 每次买入金额
NEG_STREAK = 7            # 至少连续为负的天数
SELL_THRESHOLD = 100.0    # 卖出阈值(百万美元): 持仓后 MA14 跌破此值卖出
SELL_REQUIRE_PEAK = True  # True=需先站上阈值再跌破才卖; False=持仓后首次<阈值即卖


def get_conn():
    db = config.get_database_config()
    return mysql.connector.connect(
        host=db.get("host", "localhost"), port=int(db.get("port", 3306)),
        user=db.get("user", "root"), password=db.get("password", ""),
        database=db.get("database", "btc_assistant"), charset="utf8mb4",
    )


def load_data():
    """返回按日期升序的列表: [{date, ma14, price}]。"""
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        "SELECT trade_date, ma14 FROM btc_etf_flow "
        "WHERE trade_date >= %s ORDER BY trade_date ASC",
        (START_DATE,),
    )
    flow = cur.fetchall()

    # BTC 日线收盘价: 按 UTC 日期建映射
    cur.execute(
        "SELECT timestamp, close FROM klines "
        "WHERE symbol='BTCUSDT' AND timeframe='1d' ORDER BY timestamp ASC"
    )
    price_map = {}
    for r in cur.fetchall():
        d = datetime.fromtimestamp(r["timestamp"] / 1000, tz=timezone.utc).date()
        price_map[d.isoformat()] = float(r["close"]) if r["close"] else None
    cur.close()
    conn.close()

    rows = []
    for r in flow:
        diso = r["trade_date"].isoformat()
        rows.append({
            "date": diso,
            "ma14": float(r["ma14"]) if r["ma14"] is not None else None,
            "price": price_map.get(diso),
        })
    return rows


def backtest(rows):
    trades = []
    position = None          # {buy_date, buy_price, qty}
    neg_streak = 0           # 当前连续为负天数
    armed = False            # 持仓期间 MA14 是否已站上卖出阈值

    for row in rows:
        ma = row["ma14"]
        price = row["price"]
        if ma is None:
            # 窗口未满, 视为中断连负计数
            neg_streak = 0
            prev_ma_sign = None
            continue

        is_neg = ma < 0
        is_pos = ma > 0

        if position is None:
            # 空仓: 找买点 —— 之前连续>=7天为负, 今日首次转正
            if is_pos and neg_streak >= NEG_STREAK and price:
                qty = TRADE_USD / price
                position = {"buy_date": row["date"], "buy_price": price, "qty": qty,
                            "buy_ma14": ma}
                armed = ma >= SELL_THRESHOLD  # 买入当日若已在阈值上则直接进入警戒
            # 更新连负计数
            if is_neg:
                neg_streak += 1
            else:
                neg_streak = 0
        else:
            # 持仓: 更新是否已站上阈值
            if ma >= SELL_THRESHOLD:
                armed = True
            # 卖点: MA14 < 阈值 (若要求先站上, 则需 armed)
            sell_ok = ma < SELL_THRESHOLD and (armed or not SELL_REQUIRE_PEAK)
            if sell_ok and price:
                pnl = (price - position["buy_price"]) * position["qty"]
                pnl_pct = (price / position["buy_price"] - 1) * 100
                d0 = datetime.fromisoformat(position["buy_date"]).date()
                d1 = datetime.fromisoformat(row["date"]).date()
                trades.append({
                    "buy_date": position["buy_date"], "buy_price": position["buy_price"],
                    "sell_date": row["date"], "sell_price": price,
                    "qty": position["qty"], "pnl": pnl, "pnl_pct": pnl_pct,
                    "hold_days": (d1 - d0).days, "status": "closed",
                })
                position = None
                neg_streak = 1 if is_neg else 0  # 卖出当日若为负则计入新的连负计数
            # 持仓期间不累计买点连负计数(空仓时才用)

    # 期末仍持仓: 用最后一个有价格的收盘价做浮盈
    if position is not None:
        last = next((r for r in reversed(rows) if r["price"]), None)
        if last:
            price = last["price"]
            pnl = (price - position["buy_price"]) * position["qty"]
            pnl_pct = (price / position["buy_price"] - 1) * 100
            d0 = datetime.fromisoformat(position["buy_date"]).date()
            d1 = datetime.fromisoformat(last["date"]).date()
            trades.append({
                "buy_date": position["buy_date"], "buy_price": position["buy_price"],
                "sell_date": last["date"] + " (未平仓)", "sell_price": price,
                "qty": position["qty"], "pnl": pnl, "pnl_pct": pnl_pct,
                "hold_days": (d1 - d0).days, "status": "open",
            })
    return trades


def main():
    rows = load_data()
    print(f"数据区间: {rows[0]['date']} ~ {rows[-1]['date']} (共 {len(rows)} 个交易日)\n")
    trades = backtest(rows)

    if not trades:
        print("区间内没有产生任何交易信号。")
        return

    print(f"{'#':>2}  {'买入日期':<12} {'买入价':>10}  {'卖出日期':<18} {'卖出价':>10}  "
          f"{'持有天':>5}  {'收益(USD)':>11}  {'收益率':>8}")
    print("-" * 92)
    total_pnl = 0.0
    wins = 0
    for i, t in enumerate(trades, 1):
        total_pnl += t["pnl"]
        if t["pnl"] > 0:
            wins += 1
        flag = " *持仓中" if t["status"] == "open" else ""
        print(f"{i:>2}  {t['buy_date']:<12} {t['buy_price']:>10,.2f}  "
              f"{t['sell_date']:<18} {t['sell_price']:>10,.2f}  "
              f"{t['hold_days']:>5}  {t['pnl']:>+11,.2f}  {t['pnl_pct']:>+7.2f}%{flag}")

    closed = [t for t in trades if t["status"] == "closed"]
    n = len(trades)
    invested = TRADE_USD * n
    print("-" * 92)
    print(f"\n总交易笔数: {n} (已平仓 {len(closed)}, 持仓中 {n-len(closed)})")
    print(f"胜率: {wins}/{n} = {wins/n*100:.1f}%")
    print(f"累计投入本金: {invested:,.0f} USD (每笔 {TRADE_USD:,.0f})")
    print(f"总收益: {total_pnl:+,.2f} USD")
    print(f"总收益率(相对每笔本金累加): {total_pnl/invested*100:+.2f}%")


if __name__ == "__main__":
    main()
