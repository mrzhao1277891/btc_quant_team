#!/usr/bin/env python3
"""
BTC 多周期指标数据 API — BTW Quant Team
FastAPI backend serving kline indicator data for the dashboard.
"""

import mysql.connector
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import logging

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


def fetch_klines(timeframe: str, limit: int = 120, descending: bool = False) -> List[dict]:
    """Fetch klines for a given timeframe, ordered by timestamp."""
    col_names = ", ".join(COLUMNS)
    order = "DESC" if descending else "ASC"
    sql = f"""
        SELECT {col_names}
        FROM klines
        WHERE symbol = 'BTCUSDT' AND timeframe = %s
        ORDER BY timestamp {order}
        LIMIT %s
    """
    rows = []
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, (timeframe, limit))
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
):
    rows = fetch_klines(timeframe, limit)
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
def get_all_timeframes(limit: int = Query(60, ge=3, le=300)):
    """Return all 4 timeframes in one call."""
    result = {}
    for tf in ["1m", "1w", "1d", "4h"]:
        rows = fetch_klines(tf, limit)
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
def get_latest():
    """Get the latest row for each timeframe (current values)."""
    result = {}
    for tf in ["1m", "1w", "1d", "4h"]:
        rows = fetch_klines(tf, 1, descending=True)  # get the most recent row
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
