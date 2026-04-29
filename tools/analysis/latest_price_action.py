#!/usr/bin/env python3
"""
价格行为描述工具

基于最近几根K线，生成当前价格行为的动态描述：
- 价格区间和波动特征
- 成交量状态
- RSI 动量
- K线形态信号（放量阳线、长下影线等）
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import mysql.connector
import requests
from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

TIMEFRAME_LABELS = {
    '4h': '4小时', '1d': '日线', '1w': '周线', '1M': '月线'
}


def _ensure_float(v) -> Optional[float]:
    if v is None:
        return None
    if isinstance(v, Decimal):
        return float(v)
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _get_realtime_price(symbol: str) -> Optional[float]:
    try:
        resp = requests.get(
            'https://api.binance.com/api/v3/ticker/price',
            params={'symbol': symbol}, timeout=5
        )
        resp.raise_for_status()
        return float(resp.json()['price'])
    except Exception:
        return None


class PriceActionAnalyzer:
    """价格行为分析器"""

    def __init__(self, connection=None):
        self.connection = connection

    def _fetch_recent_klines(self, symbol: str, timeframe: str,
                              limit: int = 10) -> List[Dict]:
        """取最近 N 根K线（正序）"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(
                "SELECT timestamp, open, high, low, close, volume, "
                "atr, rsi14, rsi6, ema7, ema25, ema50, boll_up, boll_md, boll_dn "
                "FROM klines WHERE symbol=%s AND timeframe=%s "
                "ORDER BY timestamp DESC LIMIT %s",
                (symbol, timeframe, limit)
            )
            rows = list(reversed(cursor.fetchall()))
            cursor.close()
            return [{k: _ensure_float(v) if k != 'timestamp' else v
                     for k, v in r.items()} for r in rows]
        except Exception as e:
            logger.warning(f"获取K线失败: {e}")
            return []

    def _median(self, values: List[float]) -> float:
        s = sorted(v for v in values if v is not None)
        if not s:
            return 0.0
        n = len(s)
        return (s[n//2 - 1] + s[n//2]) / 2 if n % 2 == 0 else s[n//2]

    def _describe_timeframe(self, symbol: str, timeframe: str,
                             current_price: float, n: int = 6) -> str:
        """生成单个周期的价格行为描述"""
        bars = self._fetch_recent_klines(symbol, timeframe, limit=n + 5)
        if len(bars) < 3:
            return f"{TIMEFRAME_LABELS.get(timeframe, timeframe)}: 数据不足"

        recent = bars[-n:]   # 最近 n 根
        prev   = bars[:-n]   # 更早的用于对比

        tf_label = TIMEFRAME_LABELS.get(timeframe, timeframe)

        # ── 价格区间 ──────────────────────────────────────────────
        highs  = [b['high']  for b in recent if b['high']]
        lows   = [b['low']   for b in recent if b['low']]
        closes = [b['close'] for b in recent if b['close']]
        opens  = [b['open']  for b in recent if b['open']]

        range_high = max(highs)
        range_low  = min(lows)
        range_pct  = (range_high - range_low) / range_low * 100 if range_low else 0

        # 价格方向
        first_close = closes[0]
        last_close  = closes[-1]
        price_chg_pct = (last_close - first_close) / first_close * 100

        if price_chg_pct > 1.5:
            direction = '持续上涨'
        elif price_chg_pct > 0.3:
            direction = '小幅上涨'
        elif price_chg_pct < -1.5:
            direction = '持续下跌'
        elif price_chg_pct < -0.3:
            direction = '小幅下跌'
        else:
            direction = '横盘震荡'

        # ── 成交量 ────────────────────────────────────────────────
        volumes = [b['volume'] for b in recent if b['volume']]
        prev_vols = [b['volume'] for b in prev if b['volume']]

        if volumes and prev_vols:
            avg_recent = sum(volumes) / len(volumes)
            avg_prev   = sum(prev_vols) / len(prev_vols)
            vol_ratio  = avg_recent / avg_prev if avg_prev > 0 else 1.0
            if vol_ratio >= 1.5:
                vol_desc = f"成交量明显放大（均量{vol_ratio:.1f}倍）"
            elif vol_ratio >= 1.1:
                vol_desc = f"成交量温和放大（均量{vol_ratio:.1f}倍）"
            elif vol_ratio <= 0.6:
                vol_desc = f"成交量持续萎缩（均量{vol_ratio:.1f}倍）"
            else:
                vol_desc = "成交量正常"
        else:
            vol_desc = "成交量数据不足"

        # ── RSI ───────────────────────────────────────────────────
        latest = recent[-1]
        rsi6  = latest.get('rsi6')
        rsi14 = latest.get('rsi14')
        rsi_parts = []
        if rsi6  is not None: rsi_parts.append(f"RSI6={rsi6:.0f}")
        if rsi14 is not None: rsi_parts.append(f"RSI14={rsi14:.0f}")
        rsi_str = '，'.join(rsi_parts)

        if rsi14 is not None:
            if rsi14 < 30:
                rsi_signal = '超卖区域'
            elif rsi14 > 70:
                rsi_signal = '超买区域'
            elif rsi14 < 45:
                rsi_signal = '偏弱'
            elif rsi14 > 55:
                rsi_signal = '偏强'
            else:
                rsi_signal = '中性'
        else:
            rsi_signal = ''

        # ── K线形态信号 ───────────────────────────────────────────
        atr = latest.get('atr') or (range_high - range_low) / len(recent)
        signals = []

        for b in recent[-3:]:  # 只看最近3根
            o, h, l, c = b.get('open'), b.get('high'), b.get('low'), b.get('close')
            v = b.get('volume')
            if not all([o, h, l, c]):
                continue

            body = abs(c - o)
            upper_shadow = h - max(o, c)
            lower_shadow = min(o, c) - l
            ts = datetime.fromtimestamp(b['timestamp'] / 1000).strftime('%m-%d %H:%M' if timeframe == '4h' else '%m-%d')

            # 放量阳线
            if c > o and body > atr * 0.5 and v and prev_vols:
                avg_v = sum(prev_vols) / len(prev_vols)
                if v > avg_v * 1.5:
                    signals.append(f"{ts}放量阳线(+{(c-o)/o*100:.1f}%，量{v/avg_v:.1f}x)")

            # 放量阴线
            if c < o and body > atr * 0.5 and v and prev_vols:
                avg_v = sum(prev_vols) / len(prev_vols)
                if v > avg_v * 1.5:
                    signals.append(f"{ts}放量阴线({(c-o)/o*100:.1f}%，量{v/avg_v:.1f}x)")

            # 长下影线（锤子线）
            if lower_shadow > body * 2 and lower_shadow > atr * 0.3:
                signals.append(f"{ts}长下影线(影线{lower_shadow:.0f})")

            # 长上影线（流星线）
            if upper_shadow > body * 2 and upper_shadow > atr * 0.3:
                signals.append(f"{ts}长上影线(影线{upper_shadow:.0f})")

        # ── 均线位置 ──────────────────────────────────────────────
        ema7  = latest.get('ema7')
        ema25 = latest.get('ema25')
        ema50 = latest.get('ema50')
        ma_parts = []
        if ema7  and current_price: ma_parts.append(f"EMA7={'上方' if current_price > ema7 else '下方'}(${ema7:,.0f})")
        if ema25 and current_price: ma_parts.append(f"EMA25={'上方' if current_price > ema25 else '下方'}(${ema25:,.0f})")
        ma_str = '，'.join(ma_parts) if ma_parts else ''

        # ── 组装描述 ──────────────────────────────────────────────
        lines = []

        # 第1句：价格区间和方向
        lines.append(
            f"最近{n}根{tf_label}：{direction}，"
            f"区间${range_low:,.0f}~${range_high:,.0f}（振幅{range_pct:.1f}%）"
        )

        # 第2句：成交量 + RSI
        rsi_full = f"{rsi_str}（{rsi_signal}）" if rsi_signal else rsi_str
        lines.append(f"{vol_desc}，{rsi_full}")

        # 第3句：K线信号 或 均线位置
        if signals:
            lines.append('，'.join(signals[:2]))
        elif ma_str:
            lines.append(f"价格在{ma_str}")
        else:
            lines.append("无明显K线形态信号")

        return '\n   '.join(lines)

    def analyze(self, symbol: str = 'BTCUSDT',
                timeframes: List[str] = None) -> Dict:
        """分析多个周期的价格行为"""
        if timeframes is None:
            timeframes = ['4h', '1d']

        current_price = _get_realtime_price(symbol)
        if current_price is None:
            # 降级用数据库最新价
            try:
                cursor = self.connection.cursor(dictionary=True)
                cursor.execute(
                    "SELECT close FROM klines WHERE symbol=%s AND timeframe='4h' "
                    "ORDER BY timestamp DESC LIMIT 1", (symbol,)
                )
                row = cursor.fetchone()
                cursor.close()
                current_price = _ensure_float(row['close']) if row else 0
            except Exception:
                current_price = 0

        # 取4H ATR
        atr = 0.0
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(
                "SELECT atr FROM klines WHERE symbol=%s AND timeframe='4h' "
                "AND atr IS NOT NULL ORDER BY timestamp DESC LIMIT 1", (symbol,)
            )
            row = cursor.fetchone()
            cursor.close()
            atr = _ensure_float(row['atr']) if row else 0.0
        except Exception:
            pass

        descriptions = {}
        for tf in timeframes:
            descriptions[tf] = self._describe_timeframe(symbol, tf, current_price)

        return {
            'symbol':        symbol,
            'current_price': current_price,
            'atr_4h':        atr,
            'descriptions':  descriptions,
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }

    def print_report(self, result: Dict):
        cp  = result['current_price']
        atr = result['atr_4h']
        print(f"\n{'='*60}")
        print(f"📈 {result['symbol']} 价格行为分析  {result['analysis_time']}")
        print(f"当前价格: ${cp:,.2f}  |  4H ATR: ${atr:,.2f}")
        print(f"{'='*60}")
        for tf, desc in result['descriptions'].items():
            print(f"\n【{TIMEFRAME_LABELS.get(tf, tf)}】")
            print(f"   {desc}")
        print(f"\n{'='*60}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='价格行为描述工具')
    parser.add_argument('--host',       default='localhost')
    parser.add_argument('--port',       type=int, default=3306)
    parser.add_argument('--user',       default='root')
    parser.add_argument('--password',   default='')
    parser.add_argument('--database',   default='btc_assistant')
    parser.add_argument('--symbol',     default='BTCUSDT')
    parser.add_argument('--timeframes', default='4h,1d',
                        help='周期列表，逗号分隔，如 4h,1d,1w')
    parser.add_argument('--bars',       type=int, default=6,
                        help='分析最近几根K线，默认6')
    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING)

    conn = mysql.connector.connect(
        host=args.host, port=args.port, user=args.user,
        password=args.password, database=args.database, charset='utf8mb4'
    )
    try:
        analyzer = PriceActionAnalyzer(connection=conn)
        tfs = [t.strip() for t in args.timeframes.split(',')]
        result = analyzer.analyze(args.symbol, timeframes=tfs)
        analyzer.print_report(result)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
