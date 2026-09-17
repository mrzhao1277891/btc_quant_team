#!/usr/bin/env python3
"""
BTC 多周期指标数据 API — BTW Quant Team
FastAPI backend serving kline indicator data for the dashboard.
"""

import mysql.connector
from fastapi import FastAPI, Query, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from pathlib import Path
import logging
import json
import subprocess
import sys

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


# ============================================================
# 每日新闻 API
# ============================================================

REPO_ROOT   = Path(__file__).resolve().parents[1]
NEWS_SCRIPT = REPO_ROOT / "scripts" / "news_fetch.py"
NEWS_JSON   = REPO_ROOT / "web" / "data" / "news.json"

# 单进程内的作业状态。刻意不落库：news.json 自身就是作业产物，
# API 重启导致这里重置，也不会留下卡死的锁。
_news_job = {"proc": None, "started_at": None, "finished_at": None,
             "returncode": None, "error": None}


def _news_running():
    p = _news_job["proc"]
    return p is not None and p.poll() is None


def _news_generated_at():
    """读产物里的生成时间 —— 页面用它判断「新一轮跑完了没有」。"""
    try:
        with open(NEWS_JSON, encoding="utf-8") as f:
            return json.load(f).get("generated_at")
    except Exception:
        return None


@app.post("/api/news/refresh")
def news_refresh():
    """后台触发一次抓取，立刻返回。

    抓取要跑 9 个 RSS + 一次 LLM 调用（约 40 秒），同步等必然超时，
    所以这里只负责拉起进程，进度由 /api/news/refresh/status 暴露。
    """
    if _news_running():
        return {"status": "running", "started_at": _news_job["started_at"],
                "generated_at": _news_generated_at()}

    if not NEWS_SCRIPT.exists():
        raise HTTPException(500, f"找不到抓取脚本: {NEWS_SCRIPT}")

    try:
        _news_job["proc"] = subprocess.Popen(
            [sys.executable, str(NEWS_SCRIPT), "init"],
            cwd=str(REPO_ROOT),
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
    except Exception as e:
        _news_job["error"] = f"{type(e).__name__}: {e}"
        return {"status": "error", "error": _news_job["error"]}

    _news_job.update(started_at=datetime.now(timezone.utc).isoformat(),
                     finished_at=None, returncode=None, error=None)
    logging.info("news refresh started (pid=%s)", _news_job["proc"].pid)
    return {"status": "started", "started_at": _news_job["started_at"],
            "generated_at": _news_generated_at()}


@app.get("/api/news/refresh/status")
def news_refresh_status():
    """轮询用。running 翻成 false 时顺手回收进程并收集错误输出。"""
    p = _news_job["proc"]

    if p is not None and p.poll() is not None and _news_job["returncode"] is None:
        _news_job["returncode"] = p.returncode
        _news_job["finished_at"] = datetime.now(timezone.utc).isoformat()
        if p.returncode != 0:
            try:
                tail = (p.stdout.read() or "")[-800:]
            except Exception:
                tail = ""
            _news_job["error"] = f"退出码 {p.returncode}: {tail}"
            logging.warning("news refresh failed: %s", _news_job["error"][:200])
        else:
            logging.info("news refresh finished ok")

    return {
        "running":      _news_running(),
        "returncode":   _news_job["returncode"],
        "error":        _news_job["error"],
        "started_at":   _news_job["started_at"],
        "finished_at":  _news_job["finished_at"],
        "generated_at": _news_generated_at(),
    }


# ============================================================
# 关键价位分布快照 API
# ============================================================
# 由 dashboard.html 的「关键价位分布（按现价1%聚合）」面板上报。
#
# 为什么要绕这么一圈：那个面板的数据依赖浏览器 localStorage 里的
# 手工斐波那契标记和 K 线标记，而 localStorage 是**跨源隔离**的 ——
# 分析师页面跑在另一个端口，读不到同一份数据，后端脚本更读不到。
# 所以只能由能读到的那一方（dashboard）算完主动上报。

import hashlib

DDL_ZONE_SNAPSHOTS = """
CREATE TABLE IF NOT EXISTS zone_snapshots (
  id           BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  symbol       VARCHAR(20)   NOT NULL,
  captured_at  DATETIME      NOT NULL COMMENT '页面计算时刻(东八区)',
  -- last_seen_at 是「dashboard 最后一次上报这份（相同的）数据」的时间，
  -- 是一个存活信号，用来区分「数据一直没变」和「页面一直没打开」。
  -- 它会随每次上报推进，而 captured_at / price 只在真正入库时更新。
  last_seen_at DATETIME      NOT NULL COMMENT '最后一次看到这份数据(东八区)，存活信号',
  -- ⚠ price 是「capture 那一刻的现价」，不是「当前价」。
  -- 它是 zones 的计算基准（聚类阈值 = 这个价 × 1%），必须和 zones 同时点才有意义。
  -- 节流时只推进 last_seen_at、不动 price —— 否则 zones 和 price 会不同源。
  -- 所以看到 price 比 last_seen_at 旧是正常的，不是数据坏了。
  price        DECIMAL(20,8) NOT NULL COMMENT 'capture 时刻的现价(zones 的计算基准)',
  zone_count   INT           NOT NULL DEFAULT 0,
  point_count  INT           NOT NULL DEFAULT 0,
  fingerprint  CHAR(32)      NOT NULL COMMENT '内容指纹，用于去重',
  has_manual   BOOLEAN       NOT NULL DEFAULT FALSE COMMENT '是否含手工标注(FIB/PIN)',
  zones_json   JSON          NOT NULL COMMENT '面板完整结构',
  -- 必须是 DATETIME 且由程序显式写入，时区与 captured_at 一致（东八区）。
  -- 原来用 TIMESTAMP DEFAULT CURRENT_TIMESTAMP 时，值由 MySQL 按服务器时区填，
  -- 而 captured_at 是程序写的另一个基准，同一行里差 8 小时 ——
  -- 看着像数据对不上，实际是字段不同源。
  created_at   DATETIME      NOT NULL COMMENT '写入时间(东八区)',
  KEY idx_symbol_seen (symbol, last_seen_at),
  KEY idx_fingerprint (fingerprint, captured_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='关键价位分布快照(由 dashboard 页面产生)'
"""

# 表已存在时把 created_at 迁到 DATETIME（幂等）。只做一次，失败无所谓。
MIGRATE_CREATED_AT = """
ALTER TABLE zone_snapshots
  MODIFY created_at DATETIME NOT NULL DEFAULT '1970-01-01 00:00:00'
  COMMENT '写入时间(东八区)'
"""

_zone_table_ready = False


def _ensure_zone_table():
    global _zone_table_ready
    if _zone_table_ready:
        return
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(DDL_ZONE_SNAPSHOTS)
        # 老表可能是 TIMESTAMP 版的 created_at，迁移到 DATETIME
        try:
            cur.execute("""SELECT DATA_TYPE FROM information_schema.COLUMNS
                           WHERE TABLE_SCHEMA=DATABASE()
                             AND TABLE_NAME='zone_snapshots'
                             AND COLUMN_NAME='created_at'""")
            row = cur.fetchone()
            if row and row[0].lower() != "datetime":
                cur.execute(MIGRATE_CREATED_AT)
                logging.info("zone_snapshots.created_at 已迁移到 DATETIME(UTC)")
        except Exception as e:
            logging.warning("created_at 迁移跳过: %s", e)
        conn.commit()
        cur.close()
    finally:
        conn.close()
    _zone_table_ready = True


class ZoneSnapshot(BaseModel):
    symbol: str = "BTCUSDT"
    price: float
    zones: List[dict] = []
    points: List[dict] = []
    # 斐波那契标记工具里，每个周期**你拉的那两个端点**。
    # 比五个散落的档位信息量大得多 —— 直接说明「你的波段是从哪到哪」，
    # 而档位只能靠反推。形如：
    #   {"1w": {"pointA": {...}, "pointB": {...}, "high": 126200, "low": 57800, "direction": "up"}}
    # ⚠ 必须在这里声明。Pydantic 默认丢弃未声明字段，而入库走的是 model_dump()，
    #   不声明的话这个字段会**静默消失**。
    #
    # ⚠⚠ 默认值必须是 None 而不是 {} —— 这两者在语义上完全不同：
    #   None = 客户端**没上报**这个字段（页面是旧版本 / 缓存副本），= 未知
    #   {}   = 客户端上报了，你确实没画斐波那契
    # 用 {} 当默认值会把「未知」伪装成「没有」：一个跑着旧代码的标签页
    # 每 30 秒上报一次，就能把你真实画好的波段静默盖成空的，且页面上看不出异常。
    # 配合下面的 dump()，未知的键根本不入库，读取侧才有机会回溯到上一份有效值。
    fib_waves: Optional[dict] = None

    # K线价格走势 panel 上手工点的 📌 标记，**带时间戳** —— 这是和 points 里
    # type=PIN 的关键区别：那边只有「价格 + 高/低」，挂在哪根 K 线上丢了。
    #   {"1w": [{"ts": 1754870400000, "price": 82380, "type": "high"}, ...]}
    # 同样用 None 当默认值，理由见上：没上报 ≠ 没标。
    manual_pins: Optional[dict] = None

    def dump(self) -> dict:
        """算指纹和入库统一走这里。

        exclude_none 让「没上报」在库里表现为**键不存在**，而不是 {}。
        其余字段都有非 None 默认值，不受影响。
        """
        return self.model_dump(exclude_none=True)


# 快照最小间隔（小时）。页面约 30 秒重渲染一次，不节流会写爆表。
# 6 小时 ≈ 一个日线级别的粒度，也大致对齐 4h K 线的更新节奏。
#
# NOTE: 若希望「手工标记一改就立即入库」，在这里加一个例外：
#   把 has_manual 也纳入判断 —— 上一行 has_manual=0 而本次 has_manual=1
#   （或手工点位集合变了）时跳过节流直接插入。
#   代价是增长上限不再确定（取决于你多久改一次标记）。
#   当前实现**没有**这个例外，即手工改动最多滞后 MIN_INTERVAL_HOURS 生效。
MIN_INTERVAL_HOURS = 6

# 库里统一用东八区。
#
# 这不是随手选的 —— btc_assistant 现有表的约定就是本地时间：
#   · klines.create_time        Python datetime.now() naive，本地
#   · btc_fng / btc_etf_flow /
#     fed_rate_decisions 的 created_at   MySQL CURRENT_TIMESTAMP，session tz=SYSTEM=本地
# 实测 12:00 UTC 的 K 线对应 create_time=20:00，固定 +8。
#
# 所以这里显式写 +8 而不是跟机器时区走：意图写在代码里，
# 换台机器部署也不会突然变成另一个基准。
TZ_CN = timezone(timedelta(hours=8))

# 价格量化粒度（美元）。指纹仍会计算并记录（供事后分析「节流期间内容变过几次」），
# 但**不再作为插入与否的判断依据** —— 见 save_zone_snapshot 的说明。
PRICE_QUANTUM = 500


def _manual_sig(payload: dict) -> tuple:
    """手工标注（斐波那契 / K线标记）的指纹。

    只取 type 为 FIB/PIN 的点，排序后作为签名。用来判断「用户改过标记没有」——
    指标点位（EMA/BOLL）随 K 线走，不在这个签名的范围内。
    """
    pts = payload.get("points") or []
    return tuple(sorted(
        (round(p.get("price", 0), 2), p.get("label", ""))
        for p in pts if p.get("type") in ("FIB", "PIN")
    )) + (("__waves__", json.dumps(payload.get("fib_waves") or {}, sort_keys=True)),)


def _fingerprint(payload: dict) -> str:
    """按**输入点位**算指纹，不是按聚类结果。

    ⚠ 这里踩过坑：最初是按聚类后的 zones 算的，结果每 30 秒写一行 ——
    因为 thr = 现价×1% 会随价格微动，簇边界跟着漂，zone_count 从 22 变 23，
    指纹就变了。而 35 个点位自始至终没变过（只在 K 线收盘或用户改标记时才变）。

    所以指纹要算在「真正会变的东西」上：点位集合 + 量化后的价格。
    """
    norm = {
        "price": round(payload["price"] / PRICE_QUANTUM),
        "points": sorted(
            (round(p.get("price", 0), 2), p.get("label", ""), p.get("type", ""))
            for p in (payload.get("points") or [])
        ),
    }
    raw = json.dumps(norm, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


@app.post("/api/zone-snapshot")
def save_zone_snapshot(payload: ZoneSnapshot):
    """接收 dashboard 上报的关键价位分布。

    **按时间节流**：距上一条快照不足 MIN_INTERVAL_HOURS 就只更新 last_seen_at，
    不插新行。页面约 30 秒重渲染一次，不节流的话一天 2880 行。

    节流而不是按内容去重，是为了行为可预测 —— 之前用「内容指纹」判重，
    结果因为聚类阈值 `现价×1%` 随价格微动，簇边界漂移导致指纹每次都变，
    每 30 秒照样写一行。时间节流的增长上限是确定的：一天最多 4 行。

    ⚠ 代价：节流窗口内**手工标记的变化不会立即入库**。你新画一条斐波那契，
    要等窗口过去才会写进去，而分析师读的是「最新一行」—— 所以最多滞后
    MIN_INTERVAL_HOURS 小时才生效。要改成立即生效见下面的 NOTE。
    """
    _ensure_zone_table()

    now_dt = datetime.now(TZ_CN)
    now = now_dt.strftime("%Y-%m-%d %H:%M:%S")
    fp = _fingerprint(payload.dump())                # 仍记录，供事后分析
    has_manual = any(p.get("type") in ("FIB", "PIN") for p in payload.points)

    conn = get_db()
    try:
        cur = conn.cursor(dictionary=True)
        # ⚠ 排序必须带 id 兜底：captured_at 只精确到秒，同一秒内插入的多行
        # 在 ORDER BY captured_at 下顺序未定义，取到的可能不是最新那行 ——
        # 会导致「上一条」判断错位（实测把节流判成了插入）。
        cur.execute("""SELECT id, captured_at, zones_json FROM zone_snapshots
                       WHERE symbol=%s ORDER BY captured_at DESC, id DESC LIMIT 1""",
                    (payload.symbol,))
        last = cur.fetchone()

        if last:
            # 库里存的是东八区 naive，读回来显式补上 +8，别指望 MySQL 会话时区
            last_dt = last["captured_at"].replace(tzinfo=TZ_CN)
            age_h = (now_dt - last_dt).total_seconds() / 3600

            if age_h < MIN_INTERVAL_HOURS:
                # 例外：**手工标注变了就立即入库**，不受节流限制。
                #
                # 节流是为了控增长（页面 30 秒重渲染一次），但手工标注是这套
                # 系统里最有价值的输入，和「页面又渲染了一遍」不是一个性质的东西。
                # 不破例的话：你早上调完关键位，分析里最多 6 小时还是旧的 ——
                # 恰好撞在「刚做完判断、最想看反馈」的时刻。
                #
                # 代价可控：上限 = 4 条/天 + 你重画标记的次数（实际一周几次）。
                try:
                    prev_manual = _manual_sig(json.loads(last["zones_json"]))
                except Exception:
                    prev_manual = None
                curr_manual = _manual_sig(payload.dump())

                if prev_manual == curr_manual:
                    cur.execute("UPDATE zone_snapshots SET last_seen_at=%s WHERE id=%s",
                                (now, last["id"]))
                    conn.commit()
                    cur.close()
                    return {"status": "throttled", "id": last["id"],
                            "age_hours": round(age_h, 2),
                            "next_allowed_in_hours": round(MIN_INTERVAL_HOURS - age_h, 2)}
                logging.info("手工标注变化，跳过节流立即入库")

        # created_at 也显式写 —— 别再依赖 CURRENT_TIMESTAMP，那会取 MySQL 会话时区，
        # 和程序写的 captured_at 不同源（本机曾经因此差 8 小时）。
        cur.execute("""INSERT INTO zone_snapshots
            (symbol, captured_at, last_seen_at, price, zone_count, point_count,
             fingerprint, has_manual, zones_json, created_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (payload.symbol, now, now, payload.price, len(payload.zones),
             len(payload.points), fp, has_manual,
             json.dumps(payload.dump(), ensure_ascii=False), now))
        conn.commit()
        new_id = cur.lastrowid
        cur.close()
        logging.info("zone snapshot 新增 id=%s zones=%d points=%d manual=%s",
                     new_id, len(payload.zones), len(payload.points), has_manual)
        return {"status": "created", "id": new_id, "fingerprint": fp}
    finally:
        conn.close()


@app.get("/api/zone-snapshot/latest")
def latest_zone_snapshot(symbol: str = "BTCUSDT"):
    """给分析师侧用的最新一份（也便于人工核对上报是否正常）。"""
    _ensure_zone_table()
    conn = get_db()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("""SELECT * FROM zone_snapshots WHERE symbol=%s
                       ORDER BY captured_at DESC LIMIT 1""", (symbol,))
        row = cur.fetchone()
        cur.close()
        if not row:
            return {"count": 0, "data": None}
        row["captured_at"] = row["captured_at"].isoformat()
        row["last_seen_at"] = row["last_seen_at"].isoformat()
        row["price"] = float(row["price"])
        row["zones"] = json.loads(row["zones_json"])
        row.pop("zones_json", None)
        return {"count": 1, "data": row}
    finally:
        conn.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)


# ============================================================
# 美联储利率决策 API
# ============================================================

@app.get("/api/fed-rates")
def list_fed_rates(limit: int = Query(100, ge=1, le=500)):
    """返回美联储利率决策历史 (从旧到新).

    ⚠ `limit` 取的是**最近的** limit 条，不是最旧的。
    之前是 `ORDER BY decision_date ASC LIMIT n` —— 那返回的是最旧的 n 条，
    表一旦超过 n 行，**最新的数据会被静默截掉**，图上表现为「利率线停在过去」，
    而且没有任何提示。取最近 N 条才是调用方要的语义，返回值再升序排列。
    """
    conn = get_db()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """SELECT * FROM (
                   SELECT id, decision_date, rate, rate_change, decision_type
                   FROM fed_rate_decisions
                   ORDER BY decision_date DESC, id DESC
                   LIMIT %s
               ) t ORDER BY decision_date ASC, id ASC""",
            (limit,),
        )
        rows = cur.fetchall()
        for r in rows:
            r["decision_date"] = r["decision_date"].isoformat()
            if r["rate_change"] is not None:
                r["rate_change"] = float(r["rate_change"])
            r["rate"] = float(r["rate"])
        cur.close()
        return {"count": len(rows), "data": rows}
    finally:
        conn.close()
