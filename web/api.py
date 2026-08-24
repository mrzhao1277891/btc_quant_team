#!/usr/bin/env python3
"""
BTC 多周期指标数据 API — BTW Quant Team
FastAPI backend serving kline indicator data for the dashboard.
"""

import mysql.connector
from fastapi import FastAPI, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import logging
import json

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = FastAPI(title="BTC Quant Dashboard API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MySQL connection ---
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "btc_assistant",
}

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

TIMEFRAME_CONFIG = {
    "1m": {"label": "月线", "retention": 60, "limit": 60},
    "1w": {"label": "周线", "retention": 52, "limit": 52},
    "1d": {"label": "日线", "retention": 120, "limit": 120},
    "4h": {"label": "4小时", "retention": 168, "limit": 128},
}

COLUMNS = [
    "timestamp", "open", "high", "low", "close", "volume",
    "ema7", "ema25", "ema50", "ema12",
    "ma5", "ma10",
    "dif", "dea", "macd",
    "rsi14", "rsi6",
    "boll_up", "boll_md", "boll_dn",
    "atr",
]


def ms_to_iso(ts_ms: int) -> str:
    """Convert millisecond timestamp to ISO string (Asia/Shanghai)"""
    dt = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc) + timedelta(hours=8)
    return dt.isoformat()


def fetch_klines(timeframe: str, limit: int = 120, descending: bool = False, symbol: str = 'BTCUSDT') -> List[dict]:
    """Fetch klines for a given timeframe, ordered by timestamp."""
    col_names = ", ".join(COLUMNS)
    order = "DESC" if descending else "ASC"
    sql = f"""
        SELECT {col_names}
        FROM klines
        WHERE symbol = %s AND timeframe = %s
        ORDER BY timestamp {order}
        LIMIT %s
    """
    rows = []
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, (symbol, timeframe, limit))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception as e:
        logging.error(f"DB error: {e}")
    return rows


@app.get("/api/klines")
def get_klines(
    timeframe: str = Query(..., pattern="^(1m|1w|1d|4h)$"),
    limit: int = Query(60, ge=3, le=500),
    symbol: str = Query('BTCUSDT'),
):
    # Fetch most recent rows, then reverse to chronological order
    rows = fetch_klines(timeframe, limit, descending=True, symbol=symbol)
    rows.reverse()
    data = []
    for r in rows:
        entry = {
            "time": ms_to_iso(r["timestamp"]),
            "ts": r["timestamp"],
            "open": float(r["open"]) if r["open"] else 0,
            "high": float(r["high"]) if r["high"] else 0,
            "low": float(r["low"]) if r["low"] else 0,
            "close": float(r["close"]) if r["close"] else 0,
            "volume": float(r["volume"]) if r["volume"] else 0,
            "ema7": float(r["ema7"]) if r["ema7"] else None,
            "ema25": float(r["ema25"]) if r["ema25"] else None,
            "ema50": float(r["ema50"]) if r["ema50"] else None,
            "ema12": float(r["ema12"]) if r["ema12"] else None,
            "ma5": float(r["ma5"]) if r["ma5"] else None,
            "ma10": float(r["ma10"]) if r["ma10"] else None,
            "dif": float(r["dif"]) if r["dif"] else None,
            "dea": float(r["dea"]) if r["dea"] else None,
            "macd": float(r["macd"]) if r["macd"] else None,
            "rsi14": float(r["rsi14"]) if r["rsi14"] else None,
            "rsi6": float(r["rsi6"]) if r["rsi6"] else None,
            "boll_up": float(r["boll_up"]) if r["boll_up"] else None,
            "boll_md": float(r["boll_md"]) if r["boll_md"] else None,
            "boll_dn": float(r["boll_dn"]) if r["boll_dn"] else None,
            "atr": float(r["atr"]) if r["atr"] else None,
        }
        data.append(entry)
    return {"timeframe": timeframe, "count": len(data), "data": data}


@app.get("/api/all")
def get_all_timeframes(limit: int = Query(60, ge=3, le=300), symbol: str = Query('BTCUSDT')):
    """Return all 4 timeframes in one call. Returns most recent data in chronological order."""
    result = {}
    for tf in ["1m", "1w", "1d", "4h"]:
        # Fetch most recent rows (DESC), then reverse to chronological order
        rows = fetch_klines(tf, limit, descending=True, symbol=symbol)
        rows.reverse()  # Now in chronological order (oldest first)
        data = []
        for r in rows:
            entry = {
                "time": ms_to_iso(r["timestamp"]),
                "ts": r["timestamp"],
                "close": float(r["close"]) if r["close"] else 0,
                "volume": float(r["volume"]) if r["volume"] else 0,
                "ema7": float(r["ema7"]) if r["ema7"] else None,
                "ema25": float(r["ema25"]) if r["ema25"] else None,
                "ema50": float(r["ema50"]) if r["ema50"] else None,
                "ema12": float(r["ema12"]) if r["ema12"] else None,
                "dif": float(r["dif"]) if r["dif"] else None,
                "dea": float(r["dea"]) if r["dea"] else None,
                "macd": float(r["macd"]) if r["macd"] else None,
                "rsi14": float(r["rsi14"]) if r["rsi14"] else None,
                "rsi6": float(r["rsi6"]) if r["rsi6"] else None,
                "boll_up": float(r["boll_up"]) if r["boll_up"] else None,
                "boll_md": float(r["boll_md"]) if r["boll_md"] else None,
                "boll_dn": float(r["boll_dn"]) if r["boll_dn"] else None,
                "atr": float(r["atr"]) if r["atr"] else None,
            }
            data.append(entry)
        result[tf] = data
    return result


@app.get("/api/latest")
def get_latest(symbol: str = 'BTCUSDT'):
    """Get the latest row for each timeframe (current values)."""
    result = {}
    for tf in ["1m", "1w", "1d", "4h"]:
        rows = fetch_klines(tf, 1, descending=True, symbol=symbol)  # get the most recent row
        if rows:
            r = rows[0]  # first row is the most recent since we fetch DESC
            result[tf] = {
                "close": float(r["close"]) if r["close"] else 0,
                "volume": float(r["volume"]) if r["volume"] else 0,
                "ema7": float(r["ema7"]) if r["ema7"] else None,
                "ema25": float(r["ema25"]) if r["ema25"] else None,
                "ema50": float(r["ema50"]) if r["ema50"] else None,
                "dif": float(r["dif"]) if r["dif"] else None,
                "dea": float(r["dea"]) if r["dea"] else None,
                "macd": float(r["macd"]) if r["macd"] else None,
                "rsi14": float(r["rsi14"]) if r["rsi14"] else None,
                "rsi6": float(r["rsi6"]) if r["rsi6"] else None,
                "boll_up": float(r["boll_up"]) if r["boll_up"] else None,
                "boll_md": float(r["boll_md"]) if r["boll_md"] else None,
                "boll_dn": float(r["boll_dn"]) if r["boll_dn"] else None,
                "atr": float(r["atr"]) if r["atr"] else None,
            }
    return result


@app.get("/api/trend-state")
def get_trend_state(symbol: str = 'BTCUSDT', timeframe: str = '1w'):
    """
    分析指定周期的趋势状态
    返回MACD区间、转向、DIF/DEA状态、EMA排列、BOLL带宽、交易量趋势
    """
    # 获取最近10条有指标的数据
    rows = fetch_klines(timeframe, 10, descending=True, symbol=symbol)
    rows.reverse()  # 时间正序
    
    # 过滤有效数据
    valid = [r for r in rows if r.get('dif') and r.get('dea') and r.get('macd')]
    if len(valid) < 3:
        return {"error": "数据不足", "symbol": symbol, "timeframe": timeframe}
    
    curr = valid[-1]  # 最新一根
    prev = valid[-2]  # 上一根
    prev2 = valid[-3] # 上上根
    
    dif = float(curr['dif'])
    dea = float(curr['dea'])
    macd_val = float(curr['macd'])  # DIF - DEA
    prev_macd = float(prev['macd'])
    
    # 1. MACD区间
    if macd_val >= 0:
        macd_zone = "上方上涨" if macd_val >= prev_macd else "上方下跌"
    else:
        macd_zone = "下方下跌" if macd_val <= prev_macd else "下方上涨"
    
    # 2. MACD转向
    if macd_val > 0 and macd_val < prev_macd:
        macd_turning = "上方转向"
    elif macd_val < 0 and macd_val > prev_macd:
        macd_turning = "下方转向"
    else:
        macd_turning = "不属于"
    
    # 3. DIF/DEA状态
    dif_position = "零轴上" if dif >= 0 else "零轴下"
    dea_position = "零轴上" if dea >= 0 else "零轴下"
    dif_dea_cross = "金叉" if dif > dea else "死叉"
    
    # 4. EMA排列
    ema7 = float(curr['ema7']) if curr.get('ema7') else None
    ema25 = float(curr['ema25']) if curr.get('ema25') else None
    ema50 = float(curr['ema50']) if curr.get('ema50') else None
    
    prev_ema7 = float(prev['ema7']) if prev.get('ema7') else None
    prev_ema25 = float(prev['ema25']) if prev.get('ema25') else None
    prev_ema50 = float(prev['ema50']) if prev.get('ema50') else None
    
    ema_state = "未知"
    ema_direction = "未知"
    if ema7 and ema25 and ema50:
        if ema7 > ema25 > ema50:
            ema_state = "多头排列 (EMA7>EMA25>EMA50)"
        elif ema7 < ema25 < ema50:
            ema_state = "空头排列 (EMA7<EMA25<EMA50)"
        elif ema7 > ema25 and ema25 < ema50:
            ema_state = "EMA7金叉EMA25, EMA25仍在EMA50下方"
        elif ema7 < ema25 and ema25 > ema50:
            ema_state = "EMA7死叉EMA25, EMA25仍在EMA50上方"
        else:
            ema_state = f"交叉中 (EMA7:{ema7:.0f} EMA25:{ema25:.0f} EMA50:{ema50:.0f})"
        
        # 方向判断
        if prev_ema7 and prev_ema25 and prev_ema50:
            ema7_up = ema7 > prev_ema7
            ema25_up = ema25 > prev_ema25
            ema50_up = ema50 > prev_ema50
            
            if ema7_up and ema25_up and ema50_up:
                ema_direction = "全部向上"
            elif not ema7_up and not ema25_up and not ema50_up:
                ema_direction = "全部向下"
            elif ema7_up:
                ema_direction = "EMA7向上, 长期均线向下"
            else:
                ema_direction = "EMA7向下, 长期均线向上"
    
    # 5. BOLL带宽
    boll_up = float(curr['boll_up']) if curr.get('boll_up') else None
    boll_dn = float(curr['boll_dn']) if curr.get('boll_dn') else None
    prev_boll_up = float(prev['boll_up']) if prev.get('boll_up') else None
    prev_boll_dn = float(prev['boll_dn']) if prev.get('boll_dn') else None
    prev2_boll_up = float(prev2['boll_up']) if prev2.get('boll_up') else None
    prev2_boll_dn = float(prev2['boll_dn']) if prev2.get('boll_dn') else None
    
    boll_state = "未知"
    if boll_up and boll_dn and prev_boll_up and prev_boll_dn and prev2_boll_up and prev2_boll_dn:
        curr_width = boll_up - boll_dn
        prev_width = prev_boll_up - prev_boll_dn
        prev2_width = prev2_boll_up - prev2_boll_dn
        
        if curr_width > prev_width and prev_width > prev2_width:
            boll_state = "扩口（带宽持续扩大）"
        elif curr_width < prev_width and prev_width < prev2_width:
            boll_state = "缩口（带宽持续缩小）"
        elif curr_width > prev_width:
            boll_state = "开始扩口"
        elif curr_width < prev_width:
            boll_state = "开始缩口"
        else:
            boll_state = "平稳"
        
        boll_state += f" (当前带宽:{curr_width:.0f})"
    
    # 6. 交易量趋势
    volumes = [float(r['volume']) for r in valid if r.get('volume')]
    vol_state = "未知"
    if len(volumes) >= 6:
        recent_avg = sum(volumes[-3:]) / 3
        earlier_avg = sum(volumes[-6:-3]) / 3
        ratio = recent_avg / earlier_avg if earlier_avg > 0 else 1
        
        if ratio > 1.2:
            vol_state = f"放量 (近3根/前3根: {ratio:.2f}x)"
        elif ratio < 0.8:
            vol_state = f"缩量 (近3根/前3根: {ratio:.2f}x)"
        else:
            vol_state = f"平稳 (近3根/前3根: {ratio:.2f}x)"
    elif len(volumes) >= 3:
        if volumes[-1] > volumes[-2] > volumes[-3]:
            vol_state = "连续放量"
        elif volumes[-1] < volumes[-2] < volumes[-3]:
            vol_state = "连续缩量"
        else:
            vol_state = "不明显"
    
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "close": float(curr['close']) if curr.get('close') else None,
        "macd_zone": macd_zone,
        "macd_turning": macd_turning,
        "dif_dea": {
            "dif": round(dif, 2),
            "dea": round(dea, 2),
            "macd": round(macd_val, 2),
            "dif_position": dif_position,
            "dea_position": dea_position,
            "cross": dif_dea_cross
        },
        "ema": {
            "ema7": round(ema7, 2) if ema7 else None,
            "ema25": round(ema25, 2) if ema25 else None,
            "ema50": round(ema50, 2) if ema50 else None,
            "state": ema_state,
            "direction": ema_direction
        },
        "boll": boll_state,
        "volume": vol_state
    }


# ============================================================
# BTC 现货 ETF 净流入 API
# ============================================================

@app.get("/api/etf-flow")
def get_etf_flow(
    limit: int = Query(180, ge=5, le=1000),
    symbol: str = Query("BTCUSDT"),
):
    """返回每日 ETF 净流入 + 5/14/30 日均线, 并融合对应日期的 BTC 日线收盘价。

    - net_flow / ma5 / ma14 / ma30 单位: 百万美元 (负=净流出)
    - price: 同日 BTC 日线收盘价 (来自 klines 表, 按 UTC 日期对齐)
    """
    conn = get_db()
    try:
        cur = conn.cursor(dictionary=True)
        # 取最近 limit 个交易日, 时间正序
        cur.execute(
            """
            SELECT trade_date, net_flow, ma5, ma14, ma30
            FROM btc_etf_flow
            ORDER BY trade_date DESC
            LIMIT %s
            """,
            (limit,),
        )
        flow_rows = cur.fetchall()
        flow_rows.reverse()

        if not flow_rows:
            cur.close()
            return {"count": 0, "data": []}

        # 用最早日期做下界, 拉取该区间的 BTC 日线收盘价
        min_date = flow_rows[0]["trade_date"]
        start_dt = datetime(min_date.year, min_date.month, min_date.day, tzinfo=timezone.utc)
        start_ts = int((start_dt - timedelta(days=2)).timestamp() * 1000)

        cur.execute(
            """
            SELECT timestamp, close FROM klines
            WHERE symbol = %s AND timeframe = '1d' AND timestamp >= %s
            ORDER BY timestamp ASC
            """,
            (symbol, start_ts),
        )
        price_map = {}
        for r in cur.fetchall():
            d = datetime.fromtimestamp(r["timestamp"] / 1000, tz=timezone.utc).date()
            price_map[d.isoformat()] = float(r["close"]) if r["close"] else None

        # 恐慌贪婪指数 (按日期对齐)
        cur.execute(
            """
            SELECT stat_date, fng_value, classification FROM btc_fng
            WHERE stat_date >= %s
            """,
            (min_date,),
        )
        fng_map = {}
        for r in cur.fetchall():
            fng_map[r["stat_date"].isoformat()] = {
                "value": int(r["fng_value"]),
                "class": r["classification"],
            }
        cur.close()

        data = []
        for r in flow_rows:
            diso = r["trade_date"].isoformat()
            fng = fng_map.get(diso)
            data.append({
                "date": diso,
                "net_flow": float(r["net_flow"]) if r["net_flow"] is not None else None,
                "ma5": float(r["ma5"]) if r["ma5"] is not None else None,
                "ma14": float(r["ma14"]) if r["ma14"] is not None else None,
                "ma30": float(r["ma30"]) if r["ma30"] is not None else None,
                "price": price_map.get(diso),
                "fng": fng["value"] if fng else None,
                "fng_class": fng["class"] if fng else None,
            })
        return {"count": len(data), "data": data}
    finally:
        conn.close()


# ============================================================
# 恐慌贪婪指数 API
# ============================================================

@app.get("/api/fng")
def get_fng(
    limit: int = Query(365, ge=5, le=4000),
    symbol: str = Query("BTCUSDT"),
):
    """返回每日恐慌贪婪指数 + 对应日期的 BTC 日线收盘价 (按 UTC 日期对齐)。

    - fng: 0-100, fng_class: Fear/Greed 等
    - price: 同日 BTC 日线收盘价 (来自 klines 表)
    """
    conn = get_db()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT stat_date, fng_value, ma5, ma14, ma30, classification FROM btc_fng
            ORDER BY stat_date DESC LIMIT %s
            """,
            (limit,),
        )
        rows = cur.fetchall()
        rows.reverse()
        if not rows:
            cur.close()
            return {"count": 0, "data": []}

        min_date = rows[0]["stat_date"]
        start_dt = datetime(min_date.year, min_date.month, min_date.day, tzinfo=timezone.utc)
        start_ts = int((start_dt - timedelta(days=2)).timestamp() * 1000)

        cur.execute(
            """
            SELECT timestamp, close FROM klines
            WHERE symbol = %s AND timeframe = '1d' AND timestamp >= %s
            ORDER BY timestamp ASC
            """,
            (symbol, start_ts),
        )
        price_map = {}
        for r in cur.fetchall():
            d = datetime.fromtimestamp(r["timestamp"] / 1000, tz=timezone.utc).date()
            price_map[d.isoformat()] = float(r["close"]) if r["close"] else None
        cur.close()

        data = []
        for r in rows:
            diso = r["stat_date"].isoformat()
            data.append({
                "date": diso,
                "fng": int(r["fng_value"]),
                "ma5": float(r["ma5"]) if r["ma5"] is not None else None,
                "ma14": float(r["ma14"]) if r["ma14"] is not None else None,
                "ma30": float(r["ma30"]) if r["ma30"] is not None else None,
                "fng_class": r["classification"],
                "price": price_map.get(diso),
            })
        return {"count": len(data), "data": data}
    finally:
        conn.close()


# ============================================================
# 交易理由 API (trade_reason)
# ============================================================

class ReasonCreate(BaseModel):
    symbol: str = "BTCUSDT"
    category: str = "技术面"
    signal_tag: Optional[str] = None
    detail: Optional[str] = None
    weight: Optional[int] = None
    trade_id: Optional[int] = None

class ReasonUpdate(BaseModel):
    category: Optional[str] = None
    signal_tag: Optional[str] = None
    detail: Optional[str] = None
    weight: Optional[int] = None


def _reason_row(r: dict) -> dict:
    return {
        "id": r["id"],
        "trade_id": r["trade_id"],
        "symbol": r["symbol"],
        "category": r["category"],
        "signal_tag": r["signal_tag"],
        "detail": r["detail"],
        "weight": int(r["weight"]) if r["weight"] is not None else None,
        "created_at": r["created_at"].isoformat() if r["created_at"] else None,
        "updated_at": r["updated_at"].isoformat() if r["updated_at"] else None,
    }


@app.get("/api/reasons")
def list_reasons(symbol: str = Query("BTCUSDT"), limit: int = Query(100, ge=1, le=500)):
    """获取某标的的交易理由列表 (按时间倒序)。"""
    conn = get_db()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT * FROM trade_reason WHERE symbol=%s ORDER BY sort_order ASC, created_at DESC LIMIT %s",
            (symbol, limit),
        )
        rows = [_reason_row(r) for r in cur.fetchall()]
        cur.close()
        return {"count": len(rows), "data": rows}
    finally:
        conn.close()


@app.post("/api/reasons")
def create_reason(r: ReasonCreate):
    """新增一条交易理由。"""
    conn = get_db()
    try:
        cur = conn.cursor()
        # 新理由放到列表最顶部 (sort_order 取当前最小值 - 1)
        cur.execute("SELECT COALESCE(MIN(sort_order), 0) - 1 FROM trade_reason WHERE symbol=%s", (r.symbol,))
        new_sort = cur.fetchone()[0]
        cur.execute(
            """INSERT INTO trade_reason (trade_id, symbol, category, signal_tag, detail, weight, sort_order)
               VALUES (%s,%s,%s,%s,%s,%s,%s)""",
            (r.trade_id, r.symbol, r.category, r.signal_tag, r.detail, r.weight, new_sort),
        )
        conn.commit()
        new_id = cur.lastrowid
        cur.close()
        return {"success": True, "id": new_id}
    finally:
        conn.close()


class ReasonReorder(BaseModel):
    symbol: str = "BTCUSDT"
    ids: List[int]

@app.post("/api/reasons/reorder")
def reorder_reasons(body: ReasonReorder):
    """按给定的 id 顺序重排 (ids[0] 在最上, sort_order=0,1,2...)。"""
    conn = get_db()
    try:
        cur = conn.cursor()
        for idx, rid in enumerate(body.ids):
            cur.execute(
                "UPDATE trade_reason SET sort_order=%s WHERE id=%s AND symbol=%s",
                (idx, rid, body.symbol),
            )
        conn.commit()
        cur.close()
        return {"success": True, "count": len(body.ids)}
    finally:
        conn.close()


@app.put("/api/reasons/{reason_id}")
def update_reason(reason_id: int, r: ReasonUpdate):
    """编辑一条交易理由 (只更新提供的字段)。"""
    fields, vals = [], []
    for col in ("category", "signal_tag", "detail", "weight"):
        v = getattr(r, col)
        if v is not None:
            fields.append(f"{col}=%s")
            vals.append(v)
    if not fields:
        return {"success": False, "error": "没有要更新的字段"}
    vals.append(reason_id)
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(f"UPDATE trade_reason SET {', '.join(fields)} WHERE id=%s", tuple(vals))
        conn.commit()
        ok = cur.rowcount >= 0
        cur.close()
        return {"success": ok}
    finally:
        conn.close()


@app.delete("/api/reasons/{reason_id}")
def delete_reason(reason_id: int):
    """删除一条交易理由。"""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM trade_reason WHERE id=%s", (reason_id,))
        conn.commit()
        cur.close()
        return {"success": True}
    finally:
        conn.close()


# ============================================================
# 交易日志 API
# ============================================================

class OrderCreate(BaseModel):
    symbol: str = "SOLUSDT"
    direction: str
    entry_price: float
    position_value: float
    leverage: float = 1.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    reason: str
    discipline_check: Optional[dict] = None

class OrderClose(BaseModel):
    exit_price: float
    review: Optional[str] = None

class FrameworkUpdate(BaseModel):
    symbol: str = "SOLUSDT"
    framework: Optional[str] = None
    discipline: Optional[str] = None
    market_view: Optional[str] = None


def _calc_pnl(direction, entry_price, exit_price, position_value, leverage):
    """计算盈亏：position_value是仓位价值(含杠杆)，本金=position_value/leverage"""
    qty = position_value / entry_price  # 币数量
    if direction == "long":
        pnl = (exit_price - entry_price) * qty
    else:
        pnl = (entry_price - exit_price) * qty
    margin = position_value / leverage  # 本金
    pnl_pct = (pnl / margin) * 100 if margin else 0
    return pnl, pnl_pct


@app.post("/api/journal/order")
def create_order(order: OrderCreate):
    """创建新订单（默认挂单中状态）"""
    conn = get_db()
    cursor = conn.cursor()
    now = datetime.now()
    cursor.execute("""
        INSERT INTO trade_journal
        (symbol, direction, entry_price, position_value, leverage, stop_loss, take_profit,
         reason, discipline_check, status, entry_time, create_time, update_time)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'pending',%s,%s,%s)
    """, (
        order.symbol, order.direction, order.entry_price, order.position_value, order.leverage,
        order.stop_loss, order.take_profit, order.reason,
        json.dumps(order.discipline_check, ensure_ascii=False) if order.discipline_check else None,
        now, now, now
    ))
    conn.commit()
    order_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return {"success": True, "id": order_id}


class OrderFill(BaseModel):
    entry_price: Optional[float] = None  # 实际成交价（可选，不填用挂单价）

@app.post("/api/journal/order/{order_id}/fill")
def fill_order(order_id: int, data: OrderFill = Body(default=OrderFill())):
    """确认成交：挂单中 -> 持仓中"""
    conn = get_db()
    cursor = conn.cursor()
    now = datetime.now()
    if data.entry_price is not None:
        cursor.execute("""
            UPDATE trade_journal SET status='open', entry_price=%s, entry_time=%s, update_time=%s
            WHERE id=%s AND status='pending'
        """, (data.entry_price, now, now, order_id))
    else:
        cursor.execute("""
            UPDATE trade_journal SET status='open', entry_time=%s, update_time=%s
            WHERE id=%s AND status='pending'
        """, (now, now, order_id))
    conn.commit()
    cursor.close()
    conn.close()
    return {"success": True}


@app.post("/api/journal/order/{order_id}/close")
def close_order(order_id: int, data: OrderClose):
    """平仓订单"""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM trade_journal WHERE id=%s", (order_id,))
    row = cursor.fetchone()
    if not row:
        cursor.close(); conn.close()
        return {"success": False, "error": "订单不存在"}
    
    pnl, pnl_pct = _calc_pnl(
        row["direction"], float(row["entry_price"]), data.exit_price,
        float(row["position_value"]), float(row["leverage"])
    )
    now = datetime.now()
    cursor2 = conn.cursor()
    cursor2.execute("""
        UPDATE trade_journal SET status='closed', exit_price=%s, review=%s,
        pnl=%s, pnl_pct=%s, exit_time=%s, update_time=%s WHERE id=%s
    """, (data.exit_price, data.review, pnl, pnl_pct, now, now, order_id))
    conn.commit()
    cursor.close(); cursor2.close(); conn.close()
    return {"success": True, "pnl": round(pnl, 2), "pnl_pct": round(pnl_pct, 2)}


@app.delete("/api/journal/order/{order_id}")
def delete_order(order_id: int):
    """删除订单"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM trade_journal WHERE id=%s", (order_id,))
    conn.commit()
    cursor.close(); conn.close()
    return {"success": True}


@app.get("/api/journal/orders")
def list_orders(symbol: str = "SOLUSDT", status: Optional[str] = None):
    """获取订单列表"""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    if status:
        cursor.execute("SELECT * FROM trade_journal WHERE symbol=%s AND status=%s ORDER BY entry_time DESC", (symbol, status))
    else:
        cursor.execute("SELECT * FROM trade_journal WHERE symbol=%s ORDER BY entry_time DESC", (symbol,))
    rows = cursor.fetchall()
    cursor.close(); conn.close()
    
    result = []
    for r in rows:
        result.append({
            "id": r["id"],
            "symbol": r["symbol"],
            "direction": r["direction"],
            "entry_price": float(r["entry_price"]),
            "position_value": float(r["position_value"]),
            "leverage": float(r["leverage"]),
            "stop_loss": float(r["stop_loss"]) if r["stop_loss"] else None,
            "take_profit": float(r["take_profit"]) if r["take_profit"] else None,
            "reason": r["reason"],
            "discipline_check": json.loads(r["discipline_check"]) if r["discipline_check"] else None,
            "status": r["status"],
            "exit_price": float(r["exit_price"]) if r["exit_price"] else None,
            "review": r["review"],
            "pnl": float(r["pnl"]) if r["pnl"] is not None else None,
            "pnl_pct": float(r["pnl_pct"]) if r["pnl_pct"] is not None else None,
            "entry_time": r["entry_time"].isoformat() if r["entry_time"] else None,
            "exit_time": r["exit_time"].isoformat() if r["exit_time"] else None,
        })
    return result


@app.get("/api/journal/framework")
def get_framework(symbol: str = "SOLUSDT"):
    """获取投资框架与纪律"""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM investment_framework WHERE symbol=%s", (symbol,))
    row = cursor.fetchone()
    cursor.close(); conn.close()
    if not row:
        return {"symbol": symbol, "framework": "", "discipline": "", "market_view": ""}
    return {"symbol": row["symbol"], "framework": row["framework"] or "", "discipline": row["discipline"] or "", "market_view": row.get("market_view") or ""}


@app.post("/api/journal/framework")
def save_framework(data: FrameworkUpdate):
    """保存投资框架与纪律"""
    conn = get_db()
    cursor = conn.cursor()
    now = datetime.now()
    cursor.execute("""
        INSERT INTO investment_framework (symbol, framework, discipline, market_view, update_time)
        VALUES (%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE framework=VALUES(framework), discipline=VALUES(discipline), market_view=VALUES(market_view), update_time=VALUES(update_time)
    """, (data.symbol, data.framework, data.discipline, data.market_view, now))
    conn.commit()
    cursor.close(); conn.close()
    return {"success": True}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
