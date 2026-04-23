#!/usr/bin/env python3
"""
多周期市场状态判断工具

判断每个周期（1M/1W/1D/4H）当前处于牛市、熊市还是震荡，
并输出加权综合结论，用于过滤交易方向。

判断维度：
  1. 均线排列：EMA7/EMA25/EMA50 的多空排列
  2. 价格位置：收盘价相对 EMA50 的位置及斜率
  3. 布林带状态：带宽扩张/收窄，价格贴近上轨/下轨/中轨
"""

from typing import Dict, List, Optional, Tuple
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

# ── 市场状态枚举 ────────────────────────────────────────────────
BULL  =  1
BEAR  = -1
RANGE =  0

# 周期权重（金字塔决策）
TF_WEIGHTS = {
    '1M': 4,
    '1w': 3,
    '1d': 2,
    '4h': 1,
}

# 综合得分阈值
BULL_THRESHOLD  =  1.5   # 加权得分 > 此值 → 牛市
BEAR_THRESHOLD  = -1.5   # 加权得分 < 此值 → 熊市


# 各周期 EMA50 斜率阈值（相邻两根K线变化幅度）
# 周期越长，单根K线跨度越大，需要更高的阈值才算有效趋势
SLOPE_THRESHOLDS = {
    '4h': 0.0005,   # 0.05%
    '1d': 0.001,    # 0.1%
    '1w': 0.003,    # 0.3%
    '1M': 0.008,    # 0.8%
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


def _judge_single_tf(bar: Dict, timeframe: str = '4h') -> Tuple[int, Dict]:
    """
    判断单个周期的市场状态。

    参数:
        bar: 该周期最新一根K线，需包含字段：
             close, ema7, ema25, ema50, boll_up, boll_md, boll_dn
             以及前一根K线的 ema50（用于斜率），通过 prev_ema50 传入

    返回:
        (状态, 详情字典)
        状态：BULL=1 / BEAR=-1 / RANGE=0
    """
    close    = _ensure_float(bar.get('close'))
    ema7     = _ensure_float(bar.get('ema7'))
    ema25    = _ensure_float(bar.get('ema25'))
    ema50    = _ensure_float(bar.get('ema50'))
    boll_up  = _ensure_float(bar.get('boll_up'))
    boll_md  = _ensure_float(bar.get('boll_md'))
    boll_dn  = _ensure_float(bar.get('boll_dn'))
    prev_ema50 = _ensure_float(bar.get('prev_ema50'))

    score = 0  # 正分→牛，负分→熊
    detail = {}

    # ── 1. 均线排列 ──────────────────────────────────────────────
    if ema7 and ema25 and ema50:
        if ema7 > ema25 > ema50:
            score += 2
            detail['ma_align'] = 'bull'       # 多头排列
        elif ema7 < ema25 < ema50:
            score -= 2
            detail['ma_align'] = 'bear'       # 空头排列
        else:
            detail['ma_align'] = 'mixed'      # 缠绕

    # ── 2. 价格相对 EMA50 ────────────────────────────────────────
    if close and ema50:
        if close > ema50:
            score += 1
            detail['price_vs_ema50'] = 'above'
        else:
            score -= 1
            detail['price_vs_ema50'] = 'below'

        # EMA50 斜率（需要前一根数据）
        if prev_ema50 and prev_ema50 > 0:
            slope_pct = (ema50 - prev_ema50) / prev_ema50
            threshold = SLOPE_THRESHOLDS.get(timeframe, 0.001)
            if slope_pct > threshold:
                score += 1
                detail['ema50_slope'] = 'up'
            elif slope_pct < -threshold:
                score -= 1
                detail['ema50_slope'] = 'down'
            else:
                detail['ema50_slope'] = 'flat'

    # ── 3. 布林带状态 ────────────────────────────────────────────
    if boll_up and boll_dn and boll_md and close:
        band_width = (boll_up - boll_dn) / boll_md if boll_md > 0 else 0
        detail['boll_width'] = round(band_width, 4)

        if band_width > 0.06:              # 带宽 > 6%，趋势扩张
            if close > boll_md:
                score += 1
                detail['boll_state'] = 'expanding_bull'
            else:
                score -= 1
                detail['boll_state'] = 'expanding_bear'
        elif band_width < 0.03:            # 带宽 < 3%，震荡收窄
            detail['boll_state'] = 'squeeze'
            score = int(score * 0.5)       # 震荡时衰减得分
        else:
            detail['boll_state'] = 'normal'

    # ── 综合判断 ─────────────────────────────────────────────────
    if score >= 3:
        state = BULL
    elif score <= -3:
        state = BEAR
    else:
        state = RANGE

    detail['raw_score'] = score
    detail['state'] = {BULL: 'bull', BEAR: 'bear', RANGE: 'range'}[state]
    return state, detail


class MarketRegimeAnalyzer:
    """多周期市场状态分析器"""

    def __init__(self, connection=None):
        """
        参数:
            connection: mysql.connector 连接对象（可后续赋值）
        """
        self.connection = connection
        self.timeframes = ['1M', '1w', '1d', '4h']

    def _fetch_latest_bars(self, symbol: str, timeframe: str,
                           before_ts: int = None) -> Tuple[Optional[Dict], Optional[Dict]]:
        """
        取最新两根K线（用于计算EMA50斜率）。
        before_ts: 回测时传入，只取该时间戳之前的数据。
        """
        try:
            cursor = self.connection.cursor(dictionary=True)
            if before_ts:
                cursor.execute(
                    "SELECT close, ema7, ema25, ema50, boll_up, boll_md, boll_dn "
                    "FROM klines WHERE symbol=%s AND timeframe=%s AND timestamp<%s "
                    "ORDER BY timestamp DESC LIMIT 2",
                    (symbol, timeframe, before_ts)
                )
            else:
                cursor.execute(
                    "SELECT close, ema7, ema25, ema50, boll_up, boll_md, boll_dn "
                    "FROM klines WHERE symbol=%s AND timeframe=%s "
                    "ORDER BY timestamp DESC LIMIT 2",
                    (symbol, timeframe)
                )
            rows = cursor.fetchall()
            cursor.close()
            if not rows:
                return None, None
            latest = rows[0]
            prev   = rows[1] if len(rows) > 1 else None
            return latest, prev
        except Exception as e:
            logger.warning(f"获取 {timeframe} K线失败: {e}")
            return None, None

    def analyze(self, symbol: str = 'BTCUSDT',
                before_ts: int = None) -> Dict:
        """
        分析多周期市场状态。

        参数:
            symbol: 交易对
            before_ts: 回测时传入时间戳（毫秒），只看该时间点之前的数据

        返回:
            {
              'overall': 'bull' | 'bear' | 'range',
              'weighted_score': float,
              'allow_long': bool,
              'allow_short': bool,
              'timeframes': {
                '1M': {'state': 'bull', 'raw_score': 4, ...},
                ...
              }
            }
        """
        tf_results = {}
        weighted_score = 0.0
        total_weight   = 0

        for tf in self.timeframes:
            latest, prev = self._fetch_latest_bars(symbol, tf, before_ts)
            if latest is None:
                logger.debug(f"跳过 {tf}：无数据")
                continue

            # 把前一根的 ema50 注入 latest，供斜率计算
            if prev:
                latest['prev_ema50'] = prev.get('ema50')

            state, detail = _judge_single_tf(latest, tf)
            weight = TF_WEIGHTS.get(tf, 1)
            weighted_score += state * weight
            total_weight   += weight
            tf_results[tf] = detail

        # 归一化得分（-1 ~ +1）
        norm_score = weighted_score / total_weight if total_weight > 0 else 0

        if norm_score > BULL_THRESHOLD / total_weight * total_weight:
            # 用原始加权分判断
            pass

        if weighted_score > BULL_THRESHOLD:
            overall = 'bull'
        elif weighted_score < BEAR_THRESHOLD:
            overall = 'bear'
        else:
            overall = 'range'

        # 交易方向许可
        # 牛市：只做多；熊市：只做空；震荡：两者都允许但需更严格过滤
        allow_long  = overall in ('bull', 'range')
        allow_short = overall in ('bear', 'range')

        return {
            'overall':        overall,
            'weighted_score': round(weighted_score, 2),
            'allow_long':     allow_long,
            'allow_short':    allow_short,
            'timeframes':     tf_results,
        }

    def format_report(self, result: Dict) -> str:
        """格式化输出市场状态报告"""
        icon = {'bull': '🟢', 'bear': '🔴', 'range': '🟡'}
        lines = [
            f"\n{'─'*50}",
            f"📊 多周期市场状态  {icon.get(result['overall'], '')} {result['overall'].upper()}"
            f"  (加权得分: {result['weighted_score']:+.1f})",
            f"  做多许可: {'✅' if result['allow_long'] else '❌'}  "
            f"做空许可: {'✅' if result['allow_short'] else '❌'}",
            f"{'─'*50}",
        ]
        tf_order = ['1M', '1w', '1d', '4h']
        for tf in tf_order:
            if tf not in result['timeframes']:
                continue
            d = result['timeframes'][tf]
            state_icon = {'bull': '🟢', 'bear': '🔴', 'range': '🟡'}.get(d.get('state', ''), '⚪')
            lines.append(
                f"  {tf:3}  {state_icon} {d.get('state','?'):5}  "
                f"均线:{d.get('ma_align','?'):5}  "
                f"EMA50:{d.get('price_vs_ema50','?'):5}  "
                f"斜率:{d.get('ema50_slope','?'):4}  "
                f"布林:{d.get('boll_state','?')}"
            )
        lines.append(f"{'─'*50}")
        return '\n'.join(lines)


# ── 命令行入口 ───────────────────────────────────────────────────

def main():
    import argparse
    import mysql.connector

    parser = argparse.ArgumentParser(description='多周期市场状态分析工具')
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
