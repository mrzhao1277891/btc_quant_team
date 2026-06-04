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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
