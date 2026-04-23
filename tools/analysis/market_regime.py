#!/usr/bin/env python3
"""
多周期市场趋势判断工具

基于 docs/BTC_MULTI_TIMEFRAME_TREND_ANALYSIS.md 实现。

三个维度独立打分，综合判断每个周期的市场状态：
  1. 均线排列（40%，±2分）
  2. 价格与EMA20关系（30%，±1.5分）
  3. 波峰波谷结构（30%，±1.5分）

总分 ≥ +2 → 上涨(up)，≤ -2 → 下跌(down)，中间 → 震荡(ranging)

四周期联动：月线+周线决定主方向，低周期检测趋势破坏风险。
"""

from typing import Dict, List, Optional, Tuple
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

# ── 各周期配置 ───────────────────────────────────────────────────
PERIOD_CONFIG = {
    '1M': {
        'min_bars': 20, 'recommend_bars': 20,
        'ema_fast': 5, 'ema_mid': 10, 'ema_slow': 20,
        'swing_window': 2,
    },
    '1w': {
        'min_bars': 30, 'recommend_bars': 30,
        'ema_fast': 5, 'ema_mid': 10, 'ema_slow': 20,
        'swing_window': 2,
    },
    '1d': {
        'min_bars': 100, 'recommend_bars': 100,
        'ema_fast': 10, 'ema_mid': 20, 'ema_slow': 50,
        'swing_window': 2,
    },
    '4h': {
        'min_bars': 150, 'recommend_bars': 150,
        'ema_fast': 20, 'ema_mid': 50, 'ema_slow': 100,
        'swing_window': 2,
    },
}

# 主方向决策表（月线状态, 周线状态） → (方向, 说明)
DIRECTION_TABLE = {
    ('up',      'up'):      ('只做多', '月线周线同向上涨，最强趋势'),
    ('up',      'ranging'): ('偏多',   '月线上涨中的盘整，等待周线方向明确'),
    ('up',      'down'):    ('观望',   '周线回调，等待企稳，不做空'),
    ('down',    'down'):    ('只做空', '月线周线同向下跌，最强下跌'),
    ('down',    'ranging'): ('偏空',   '月线下跌中的盘整，等待周线方向明确'),
    ('down',    'up'):      ('观望',   '周线反弹，等待结束，不做多'),
    ('ranging', 'up'):      ('观望',   '月线无方向，趋势策略失效'),
    ('ranging', 'down'):    ('观望',   '月线无方向，趋势策略失效'),
    ('ranging', 'ranging'): ('观望',   '月线无方向，趋势策略失效'),
}

# 趋势破坏风险表（高周期状态, 低周期状态） → 风险等级
RISK_TABLE = {
    ('up',   'down'):    '高风险',
    ('up',   'ranging'): '中风险',
    ('up',   'up'):      '无风险',
    ('down', 'up'):      '高风险',
    ('down', 'ranging'): '中风险',
    ('down', 'down'):    '无风险',
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


def _calc_ema(closes: List[float], period: int) -> List[float]:
    """计算EMA序列"""
    if len(closes) < period:
        return []
    k = 2.0 / (period + 1)
    ema = [sum(closes[:period]) / period]
    for price in closes[period:]:
        ema.append(price * k + ema[-1] * (1 - k))
    # 补齐前面的 NaN 位置（用 None 占位，保持索引对齐）
    return [None] * (period - 1) + ema


def _find_swing_points(highs: List[float], lows: List[float],
                       window: int = 2) -> Tuple[List[float], List[float]]:
    """
    识别摆动高点和低点价格列表。
    左右各看 window 根K线，严格大于/小于两侧。
    """
    n = len(highs)
    peaks   = []
    troughs = []
    for i in range(window, n - window):
        if all(highs[i] > highs[i - j] and highs[i] > highs[i + j]
               for j in range(1, window + 1)):
            peaks.append(highs[i])
        if all(lows[i] < lows[i - j] and lows[i] < lows[i + j]
               for j in range(1, window + 1)):
            troughs.append(lows[i])
    return peaks, troughs


def detect_trend(klines: List[Dict], period_type: str) -> Dict:
    """
    判断单个周期的市场趋势。

    参数:
        klines: K线列表，每条需包含 open/high/low/close
        period_type: '1M' | '1w' | '1d' | '4h'

    返回:
        {
          'trend': 'up' | 'down' | 'ranging' | 'insufficient_data',
          'confidence': float,
          'details': { ma_score, price_ma_score, structure_score, total_score }
        }
    """
    cfg = PERIOD_CONFIG.get(period_type, PERIOD_CONFIG['4h'])
    min_bars = cfg['min_bars']

    if len(klines) < min_bars:
        return {
            'trend': 'insufficient_data',
            'confidence': 0.0,
            'details': {'reason': f'数据不足，需要{min_bars}根，实际{len(klines)}根'}
        }

    closes = [_ensure_float(k.get('close', k.get('c'))) for k in klines]
    highs  = [_ensure_float(k.get('high',  k.get('h'))) for k in klines]
    lows   = [_ensure_float(k.get('low',   k.get('l'))) for k in klines]

    # 过滤 None
    if any(v is None for v in closes + highs + lows):
        closes = [v for v in closes if v is not None]
        highs  = [v for v in highs  if v is not None]
        lows   = [v for v in lows   if v is not None]

    fast, mid, slow = cfg['ema_fast'], cfg['ema_mid'], cfg['ema_slow']
    window = cfg['swing_window']

    ema_fast = _calc_ema(closes, fast)
    ema_mid  = _calc_ema(closes, mid)
    ema_slow = _calc_ema(closes, slow)

    # ── 维度1：均线排列（±2）────────────────────────────────────
    ef, em, es = ema_fast[-1], ema_mid[-1], ema_slow[-1]
    ef_prev = ema_fast[-2] if len(ema_fast) >= 2 else None

    if ef and em and es and ef_prev:
        if ef > em > es and ef > ef_prev:
            ma_score = 2.0
        elif ef < em < es and ef < ef_prev:
            ma_score = -2.0
        else:
            ma_score = 0.0
    else:
        ma_score = 0.0

    # ── 维度2：价格与慢线（EMA_slow对应文档EMA20）关系（±1.5）──
    # 取最近5根K线的收盘价与ema_slow对比
    above_count = 0
    for i in range(-5, 0):
        c = closes[i] if abs(i) <= len(closes) else None
        e = ema_slow[i] if abs(i) <= len(ema_slow) else None
        if c and e and c > e:
            above_count += 1

    if closes[-1] and ema_slow[-1]:
        if closes[-1] > ema_slow[-1] and above_count >= 4:
            price_ma_score = 1.5
        elif closes[-1] < ema_slow[-1] and above_count <= 1:
            price_ma_score = -1.5
        else:
            price_ma_score = 0.0
    else:
        price_ma_score = 0.0

    # ── 维度3：波峰波谷结构（±1.5）──────────────────────────────
    peaks, troughs = _find_swing_points(highs, lows, window)
    last_peaks   = peaks[-3:]   if len(peaks)   >= 3 else peaks
    last_troughs = troughs[-3:] if len(troughs) >= 3 else troughs

    if (len(last_troughs) == 3
            and last_troughs[0] < last_troughs[1] < last_troughs[2]
            and len(last_peaks) >= 2
            and last_peaks[-1] > last_peaks[-2]):
        structure_score = 1.5
    elif (len(last_peaks) == 3
            and last_peaks[0] > last_peaks[1] > last_peaks[2]
            and len(last_troughs) >= 2
            and last_troughs[-1] < last_troughs[-2]):
        structure_score = -1.5
    else:
        structure_score = 0.0

    # ── 综合判定 ─────────────────────────────────────────────────
    total = ma_score + price_ma_score + structure_score
    if total >= 2:
        trend = 'up'
    elif total <= -2:
        trend = 'down'
    else:
        trend = 'ranging'

    return {
        'trend':      trend,
        'confidence': round(min(abs(total) / 5.0, 1.0), 2),
        'details': {
            'ma_score':        ma_score,
            'price_ma_score':  price_ma_score,
            'structure_score': structure_score,
            'total_score':     round(total, 1),
            'ema_fast':        round(ef, 2) if ef else None,
            'ema_mid':         round(em, 2) if em else None,
            'ema_slow':        round(es, 2) if es else None,
            'peaks_count':     len(peaks),
            'troughs_count':   len(troughs),
        }
    }


class MarketRegimeAnalyzer:
    """多周期市场状态分析器"""

    def __init__(self, connection=None):
        self.connection = connection
        self.timeframes = ['1M', '1w', '1d', '4h']

    def _fetch_klines(self, symbol: str, timeframe: str,
                      limit: int, before_ts: int = None) -> List[Dict]:
        """从数据库取K线，按时间正序返回"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            if before_ts:
                cursor.execute(
                    "SELECT open, high, low, close FROM klines "
                    "WHERE symbol=%s AND timeframe=%s AND timestamp<%s "
                    "ORDER BY timestamp DESC LIMIT %s",
                    (symbol, timeframe, before_ts, limit)
                )
            else:
                cursor.execute(
                    "SELECT open, high, low, close FROM klines "
                    "WHERE symbol=%s AND timeframe=%s "
                    "ORDER BY timestamp DESC LIMIT %s",
                    (symbol, timeframe, limit)
                )
            rows = cursor.fetchall()
            cursor.close()
            # 反转为正序（旧→新）
            return list(reversed(rows))
        except Exception as e:
            logger.warning(f"获取 {timeframe} K线失败: {e}")
            return []

    def analyze(self, symbol: str = 'BTCUSDT',
                before_ts: int = None) -> Dict:
        """
        分析多周期市场状态。

        参数:
            symbol: 交易对
            before_ts: 回测时传入时间戳（毫秒），只看该时间点之前的数据

        返回:
            {
              'timeframes': { '1M': {...}, '1w': {...}, '1d': {...}, '4h': {...} },
              'risk': { 'month_risk': ..., 'week_risk': ..., 'day_risk': ... },
              'decision': { 'direction': ..., 'basis': ... },
              'allow_long': bool,
              'allow_short': bool,
            }
        """
        tf_results = {}

        for tf in self.timeframes:
            cfg   = PERIOD_CONFIG[tf]
            limit = cfg['recommend_bars'] + 10  # 多取几根保证够用
            klines = self._fetch_klines(symbol, tf, limit, before_ts)
            result = detect_trend(klines, tf)
            tf_results[tf] = result
            logger.debug(f"{tf}: {result['trend']} (置信度{result['confidence']:.2f})")

        # ── 趋势破坏风险 ─────────────────────────────────────────
        def get_risk(high_tf, low_tf):
            ht = tf_results.get(high_tf, {}).get('trend', 'ranging')
            lt = tf_results.get(low_tf,  {}).get('trend', 'ranging')
            if ht in ('up', 'down'):
                return RISK_TABLE.get((ht, lt), '无风险')
            return '无风险'

        risk = {
            'month_risk': get_risk('1M', '1w'),
            'week_risk':  get_risk('1w', '1d'),
            'day_risk':   get_risk('1d', '4h'),
        }

        # ── 主方向决策 ───────────────────────────────────────────
        month_trend = tf_results.get('1M', {}).get('trend', 'ranging')
        week_trend  = tf_results.get('1w', {}).get('trend', 'ranging')

        # insufficient_data 当作 ranging 处理
        if month_trend == 'insufficient_data':
            month_trend = 'ranging'
        if week_trend == 'insufficient_data':
            week_trend = 'ranging'

        direction, basis = DIRECTION_TABLE.get(
            (month_trend, week_trend),
            ('观望', f'月线{month_trend}，周线{week_trend}')
        )

        allow_long  = direction in ('只做多', '偏多')
        allow_short = direction in ('只做空', '偏空')

        return {
            'timeframes': tf_results,
            'risk':       risk,
            'decision':   {'direction': direction, 'basis': basis},
            'allow_long':  allow_long,
            'allow_short': allow_short,
        }

    def format_report(self, result: Dict) -> str:
        """格式化输出市场状态报告"""
        trend_icon = {'up': '🟢', 'down': '🔴', 'ranging': '🟡',
                      'insufficient_data': '⚪'}
        risk_icon  = {'无风险': '✅', '中风险': '⚠️', '高风险': '🚨'}
        dir_icon   = {'只做多': '🟢', '偏多': '🟩', '观望': '🟡',
                      '偏空': '🟧', '只做空': '🔴'}

        decision = result['decision']
        risk     = result['risk']
        tfs      = result['timeframes']

        lines = [
            f"\n{'═'*60}",
            f"📊 BTC 多周期市场状态分析",
            f"{'═'*60}",
            f"  主方向: {dir_icon.get(decision['direction'],'')} {decision['direction']}",
            f"  依据:   {decision['basis']}",
            f"  做多许可: {'✅' if result['allow_long'] else '❌'}  "
            f"做空许可: {'✅' if result['allow_short'] else '❌'}",
            f"{'─'*60}",
            f"  {'周期':4}  {'状态':8}  {'置信度':6}  {'总分':5}  "
            f"{'均线':5}  {'价格':5}  {'结构':5}",
            f"  {'─'*4}  {'─'*8}  {'─'*6}  {'─'*5}  "
            f"{'─'*5}  {'─'*5}  {'─'*5}",
        ]

        tf_order = ['1M', '1w', '1d', '4h']
        tf_label = {'1M': '月线', '1w': '周线', '1d': '日线', '4h': '4小时'}
        for tf in tf_order:
            r = tfs.get(tf, {})
            trend = r.get('trend', '?')
            icon  = trend_icon.get(trend, '⚪')
            conf  = f"{r.get('confidence', 0):.0%}"
            d     = r.get('details', {})
            total = d.get('total_score', '-')
            ma    = d.get('ma_score', '-')
            pm    = d.get('price_ma_score', '-')
            st    = d.get('structure_score', '-')
            lines.append(
                f"  {tf_label[tf]:4}  {icon}{trend:7}  {conf:6}  "
                f"{str(total):5}  {str(ma):5}  {str(pm):5}  {str(st):5}"
            )

        lines += [
            f"{'─'*60}",
            f"  趋势破坏风险:",
            f"    月线风险 (参考周线): {risk_icon.get(risk['month_risk'],'')} {risk['month_risk']}",
            f"    周线风险 (参考日线): {risk_icon.get(risk['week_risk'],'')}  {risk['week_risk']}",
            f"    日线风险 (参考4h):   {risk_icon.get(risk['day_risk'],'')}  {risk['day_risk']}",
            f"{'═'*60}",
        ]
        return '\n'.join(lines)


# ── 命令行入口 ───────────────────────────────────────────────────

def main():
    import argparse
    import mysql.connector

    parser = argparse.ArgumentParser(description='多周期市场趋势判断工具')
    parser.add_argument('--host',     default='localhost')
    parser.add_argument('--port',     type=int, default=3306)
    parser.add_argument('--user',     default='root')
    parser.add_argument('--password', default='')
    parser.add_argument('--database', default='btc_assistant')
    parser.add_argument('--symbol',   default='BTCUSDT')
    args = parser.parse_args()

    conn = mysql.connector.connect(
        host=args.host, port=args.port,
        user=args.user, password=args.password,
        database=args.database, charset='utf8mb4'
    )
    try:
        analyzer = MarketRegimeAnalyzer(connection=conn)
        result   = analyzer.analyze(args.symbol)
        print(analyzer.format_report(result))
    finally:
        conn.close()


if __name__ == '__main__':
    main()
