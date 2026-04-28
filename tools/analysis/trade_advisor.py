#!/usr/bin/env python3
"""
交易机会分析工具

基于支撑阻力位分析 + 多周期市场状态，结合 Francis 交易习惯，
输出当前最优交易机会和完整交易方案。

交易参数（来自 profiles/我的交易习惯.md）：
  保证金: 2403U  杠杆: 5倍  单笔最大: 10000U
  硬止损: 100U/笔  盈亏比要求: ≥2:1  持仓: ≤48小时
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import mysql.connector
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from support_resistance import SupportResistanceAnalyzerPhase1
from market_regime import MarketRegimeAnalyzer

logger = logging.getLogger(__name__)

# ── 交易参数 ─────────────────────────────────────────────────────
TRADE_PARAMS = {
    'account_balance':  2403,    # U
    'leverage':         5,
    'max_position':     10000,   # U（名义仓位上限）
    'hard_stop_usd':    100,     # U（每笔硬止损）
    'min_rr':           2.0,     # 最小盈亏比
    'max_hold_hours':   48,      # 最大持仓小时
}


def _calc_position(entry: float, stop: float) -> Dict:
    """
    基于入场价和止损价，计算仓位和风险参数。
    硬止损 100U，名义仓位不超过 10000U。
    """
    stop_pct = abs(entry - stop) / entry
    if stop_pct <= 0:
        return {}

    # 理论最大仓位（保证100U止损）
    theoretical_pos = TRADE_PARAMS['hard_stop_usd'] / stop_pct
    position = min(theoretical_pos, TRADE_PARAMS['max_position'])

    margin = position / TRADE_PARAMS['leverage']
    margin_pct = margin / TRADE_PARAMS['account_balance'] * 100
    stop_usd = position * stop_pct

    return {
        'position':    round(position, 0),
        'margin':      round(margin, 0),
        'margin_pct':  round(margin_pct, 1),
        'stop_usd':    round(stop_usd, 1),
        'stop_pct':    round(stop_pct * 100, 2),
    }


def _find_best_opportunity(
    supports: List[Dict],
    resistances: List[Dict],
    current_price: float,
    allow_long: bool,
    allow_short: bool,
    atr: float,
) -> List[Dict]:
    """
    遍历支撑/阻力位，找出满足盈亏比要求的交易机会，按综合评级排序。
    """
    opportunities = []

    # ── 做多机会：支撑位入场 ─────────────────────────────────────
    if allow_long:
        for sup in supports:
            sup_price = sup['price']
            score     = sup.get('final_score', 0)

            # 入场价：支撑位 + 0.1×ATR（限价单）
            entry = sup_price + atr * 0.1
            # 止损：支撑位 - 1×ATR
            stop  = sup_price - atr * 1.0
            stop_dist = entry - stop
            if stop_dist <= 0:
                continue

            # 目标：找最近阻力位，或 entry + 2×stop_dist
            default_target = entry + TRADE_PARAMS['min_rr'] * stop_dist
            res_above = [r for r in resistances if r['price'] > entry]
            if res_above:
                nearest_res = min(res_above, key=lambda x: x['price'])
                target = max(nearest_res['price'], default_target)
            else:
                target = default_target

            rr = (target - entry) / stop_dist
            if rr < TRADE_PARAMS['min_rr']:
                continue

            pos = _calc_position(entry, stop)
            if not pos:
                continue

            profit_usd = pos['position'] * (target - entry) / entry

            opportunities.append({
                'direction':   'long',
                'entry':       round(entry, 2),
                'stop':        round(stop, 2),
                'target':      round(target, 2),
                'rr':          round(rr, 2),
                'level_price': sup_price,
                'level_score': score,
                'level_desc':  _level_label(sup),
                'profit_usd':  round(profit_usd, 0),
                **pos,
            })

    # ── 做空机会：阻力位入场 ─────────────────────────────────────
    if allow_short:
        for res in resistances:
            res_price = res['price']
            score     = res.get('final_score', 0)

            entry = res_price - atr * 0.1
            stop  = res_price + atr * 1.0
            stop_dist = stop - entry
            if stop_dist <= 0:
                continue

            default_target = entry - TRADE_PARAMS['min_rr'] * stop_dist
            sup_below = [s for s in supports if s['price'] < entry]
            if sup_below:
                nearest_sup = max(sup_below, key=lambda x: x['price'])
                target = min(nearest_sup['price'], default_target)
            else:
                target = default_target

            rr = (entry - target) / stop_dist
            if rr < TRADE_PARAMS['min_rr']:
                continue

            pos = _calc_position(entry, stop)
            if not pos:
                continue

            profit_usd = pos['position'] * (entry - target) / entry

            opportunities.append({
                'direction':   'short',
                'entry':       round(entry, 2),
                'stop':        round(stop, 2),
                'target':      round(target, 2),
                'rr':          round(rr, 2),
                'level_price': res_price,
                'level_score': score,
                'level_desc':  _level_label(res),
                'profit_usd':  round(profit_usd, 0),
                **pos,
            })

    # 按位点评分 × 盈亏比排序
    opportunities.sort(key=lambda x: x['level_score'] * x['rr'], reverse=True)
    return opportunities


def _level_label(level: Dict) -> str:
    SUBTYPE = {
        'EMA7': 'EMA7', 'EMA12': 'EMA12', 'EMA25': 'EMA25', 'EMA50': 'EMA50',
        'BOLL_MD': '布林中轨', 'BOLL_UP': '布林上轨', 'BOLL_DN': '布林下轨',
        'swing_low': '摆动低点', 'swing_high': '摆动高点',
        'swing_low_optimized': '摆动低点', 'swing_high_optimized': '摆动高点',
        'retracement_0.382': 'Fib38.2%', 'retracement_0.5': 'Fib50%',
        'retracement_0.618': 'Fib61.8%', 'major': '整五千关口',
    }
    TYPE = {'technical': '技术位', 'dynamic': '动态位',
            'fibonacci': '斐波那契', 'psychological': '心理位'}
    tf = {'1M': '月', '1w': '周', '1d': '日', '4h': '4H', 'all': '通用'}.get(
        level.get('timeframe', ''), level.get('timeframe', ''))
    sub = SUBTYPE.get(level.get('subtype', ''), '')
    typ = TYPE.get(level.get('type', ''), '')
    detail = sub or typ
    return f"{tf} {detail}".strip() if detail else tf


def _stars(score: int) -> str:
    if score >= 13: return '★★★★★'
    if score >= 10: return '★★★★'
    if score >= 7:  return '★★★'
    if score >= 4:  return '★★'
    return '★'


class TradeAdvisor:
    """交易机会分析器"""

    def __init__(self, host='localhost', port=3306, user='root',
                 password='', database='btc_assistant'):
        self.db_config = dict(host=host, port=port, user=user,
                              password=password, database=database,
                              charset='utf8mb4')
        self.conn = None
        self.sr_analyzer     = SupportResistanceAnalyzerPhase1(
            host=host, port=port, user=user, password=password, database=database)
        self.regime_analyzer = MarketRegimeAnalyzer()

    def connect(self):
        self.conn = mysql.connector.connect(**self.db_config)
        self.sr_analyzer.connection     = self.conn
        self.regime_analyzer.connection = self.conn

    def disconnect(self):
        if self.conn and self.conn.is_connected():
            self.conn.close()

    def analyze(self, symbol: str = 'BTCUSDT') -> Dict:
        """运行完整的交易机会分析"""

        # 1. 市场状态
        regime = self.regime_analyzer.analyze(symbol)

        # 2. 支撑阻力分析
        sr_result = self.sr_analyzer.multi_timeframe_analysis(symbol)
        current_price = sr_result.get('current_price', 0)
        base_atr      = sr_result.get('base_atr', 1000)
        supports      = sr_result.get('supports', [])
        resistances   = sr_result.get('resistances', [])

        # 3. 找交易机会
        opportunities = _find_best_opportunity(
            supports, resistances, current_price,
            allow_long  = regime['allow_long'],
            allow_short = regime['allow_short'],
            atr         = base_atr,
        )

        return {
            'symbol':        symbol,
            'current_price': current_price,
            'base_atr':      base_atr,
            'regime':        regime,
            'supports':      supports,
            'resistances':   resistances,
            'opportunities': opportunities,
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }

    def print_report(self, result: Dict):
        """打印交易机会报告"""
        cp     = result['current_price']
        atr    = result['base_atr']
        regime = result['regime']
        opps   = result['opportunities']
        dec    = regime['decision']

        dir_icon = {'只做多': '🟢', '偏多': '🟩', '观望': '🟡',
                    '偏空': '🟧', '只做空': '🔴'}.get(dec['direction'], '⚪')

        print(f"\n{'='*60}")
        print(f"📊 {result['symbol']} 交易机会分析  {result['analysis_time']}")
        print(f"{'='*60}")
        print(f"当前价格: ${cp:,.2f}  |  ATR(4H): ${atr:,.2f}")
        print(f"市场方向: {dir_icon} {dec['direction']}  ({dec['basis']})")
        print(f"做多: {'✅' if regime['allow_long'] else '❌'}  "
              f"做空: {'✅' if regime['allow_short'] else '❌'}")

        if not opps:
            print(f"\n⚠️  当前无满足条件的交易机会（盈亏比≥{TRADE_PARAMS['min_rr']}）")
            print(f"{'='*60}")
            return

        print(f"\n{'─'*60}")
        print(f"🎯 交易机会（共 {len(opps)} 个，按综合评级排序）")
        print(f"{'─'*60}")

        for i, opp in enumerate(opps[:5], 1):
            dir_str  = '做多 📈' if opp['direction'] == 'long' else '做空 📉'
            stars    = _stars(opp['level_score'])
            conf_notes = []  # 共振信息从 level 里取

            print(f"\n  {i}. {dir_str}  {stars} [{opp['level_score']}/15]  {opp['level_desc']}")
            print(f"     位点价格: ${opp['level_price']:,.2f}")
            print(f"     ┌ 入场价: ${opp['entry']:,.2f}")
            print(f"     ├ 止  损: ${opp['stop']:,.2f}  "
                  f"(-{opp['stop_pct']}%  -{opp['stop_usd']}U)")
            print(f"     ├ 目  标: ${opp['target']:,.2f}  "
                  f"(盈亏比 {opp['rr']:.1f}:1  +{opp['profit_usd']:.0f}U)")
            print(f"     └ 仓  位: {opp['position']:,.0f}U  "
                  f"保证金 {opp['margin']:,.0f}U ({opp['margin_pct']}%)")

        print(f"\n{'─'*60}")
        print(f"⚙️  交易参数: 保证金{TRADE_PARAMS['account_balance']}U  "
              f"杠杆{TRADE_PARAMS['leverage']}x  "
              f"硬止损{TRADE_PARAMS['hard_stop_usd']}U  "
              f"持仓≤{TRADE_PARAMS['max_hold_hours']}h")
        print(f"{'='*60}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='交易机会分析工具')
    parser.add_argument('--host',     default='localhost')
    parser.add_argument('--port',     type=int, default=3306)
    parser.add_argument('--user',     default='root')
    parser.add_argument('--password', default='')
    parser.add_argument('--database', default='btc_assistant')
    parser.add_argument('--symbol',   default='BTCUSDT')
    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING)

    advisor = TradeAdvisor(
        host=args.host, port=args.port, user=args.user,
        password=args.password, database=args.database
    )
    advisor.connect()
    try:
        result = advisor.analyze(args.symbol)
        advisor.print_report(result)
    finally:
        advisor.disconnect()


if __name__ == '__main__':
    main()
