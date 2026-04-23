#!/usr/bin/env python3
"""
支撑阻力位回测引擎

回测逻辑：
  做多：价格 low 触及支撑位 ± 0.5×ATR → 收盘入场做多
        止损：支撑位 - 1×ATR
        目标：最近阻力位 或 入场价 + 2×止损距离（取较近）
  做空：价格 high 触及阻力位 ± 0.5×ATR → 收盘入场做空
        止损：阻力位 + 1×ATR
        目标：最近支撑位 或 入场价 - 2×止损距离（取较近）

避免未来函数：
  每根 K 线只用该时间点之前的历史数据计算支撑阻力位
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mysql.connector
import numpy as np
from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import logging

# 导入支撑阻力分析器
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'analysis'))
from support_resistance import SupportResistanceAnalyzerPhase1
from market_regime import MarketRegimeAnalyzer

logger = logging.getLogger(__name__)


def ensure_float(v):
    if v is None:
        return None
    if isinstance(v, Decimal):
        return float(v)
    return float(v)


# ──────────────────────────────────────────────
# 回测参数配置
# ──────────────────────────────────────────────
BACKTEST_CONFIG = {
    # 触及判定：价格进入位点 ± touch_atr_mult × ATR 范围内算触及
    'touch_atr_mult': 0.3,
    # 止损距离：位点 ± stop_atr_mult × ATR
    'stop_atr_mult': 1.0,
    # 限价单入场缓冲：在位点 ± entry_buffer_mult × ATR 处挂单
    # 做多：sup['price'] + entry_buffer_mult × ATR（支撑位稍上方）
    # 做空：res['price'] - entry_buffer_mult × ATR（阻力位稍下方）
    'entry_buffer_mult': 0.1,
    # 最小盈亏比：低于此不入场
    'min_rr': 2.0,
    # 最大持仓根数（4H K线数），超过强制平仓
    'max_bars': 24,          # 24根4H = 96小时（4天）
    # 位点最低评分（final_score，1-15分），低于此不交易
    'min_score': 7,
    # 反弹/回落成立的最小幅度（相对入场价）
    'min_move_pct': 0.005,   # 0.5%
    # 回测用的 K 线时间框架
    'exec_timeframe': '4h',
    # 计算支撑阻力位时，每次向前看多少根 K 线
    # 4h数据现有4380条(约2年)，lookback设500覆盖约83天的历史位点
    'sr_lookback_bars': 500,
    # 支撑阻力位计算间隔（每隔多少根 K 线重新计算一次，节省时间）
    # 数据量大了适当加密，每4根重算一次（约16小时）
    'sr_recalc_interval': 4,
    # 市场状态重算间隔（每隔多少根4H K线重新判断一次）
    # 24根=4天，市场状态变化慢，不需要频繁重算
    'regime_recalc_interval': 24,
}


class SRBacktester:
    """支撑阻力位回测器"""

    def __init__(self, host='localhost', port=3306, user='root',
                 password='', database='btc_assistant'):
        self.db_config = dict(
            host=host, port=port, user=user,
            password=password, database=database, charset='utf8mb4'
        )
        self.conn = None
        self.cfg = BACKTEST_CONFIG

        # 支撑阻力分析器（共享数据库连接）
        self.sr_analyzer = SupportResistanceAnalyzerPhase1(
            host=host, port=port, user=user,
            password=password, database=database
        )
        # 市场状态分析器（共享数据库连接）
        self.regime_analyzer = MarketRegimeAnalyzer()

    # ── 数据库 ──────────────────────────────────────────────────────────

    def connect(self):
        self.conn = mysql.connector.connect(**self.db_config)
        self.sr_analyzer.connection = self.conn
        self.regime_analyzer.connection = self.conn
        logger.info("✅ 数据库连接成功")

    def disconnect(self):
        if self.conn and self.conn.is_connected():
            self.conn.close()
        self.sr_analyzer.connection = None
        self.regime_analyzer.connection = None

    def _fetch_klines(self, symbol: str, timeframe: str,
                      limit: int = None, before_ts: int = None) -> List[Dict]:
        """按时间正序取 K 线，可限制截止时间戳（毫秒）"""
        cursor = self.conn.cursor(dictionary=True)
        if before_ts:
            cursor.execute(
                "SELECT timestamp, open, high, low, close, volume, atr, "
                "ema7, ema25, ema50, boll_up, boll_dn, boll_md "
                "FROM klines WHERE symbol=%s AND timeframe=%s AND timestamp<%s "
                "ORDER BY timestamp ASC" + (f" LIMIT {limit}" if limit else ""),
                (symbol, timeframe, before_ts)
            )
        else:
            cursor.execute(
                "SELECT timestamp, open, high, low, close, volume, atr, "
                "ema7, ema25, ema50, boll_up, boll_dn, boll_md "
                "FROM klines WHERE symbol=%s AND timeframe=%s "
                "ORDER BY timestamp ASC" + (f" LIMIT {limit}" if limit else ""),
                (symbol, timeframe)
            )
        rows = cursor.fetchall()
        cursor.close()
        return [{k: ensure_float(v) if k not in ('timestamp',) else v
                 for k, v in r.items()} for r in rows]

    # ── 支撑阻力位计算（调用 SupportResistanceAnalyzerPhase1）──────────

    def _calc_sr_levels(self, before_ts: int, current_price: float, symbol: str
                        ) -> Tuple[List[Dict], List[Dict]]:
        """
        调用 SupportResistanceAnalyzerPhase1 计算支撑阻力位。
        before_ts: 只使用该时间戳之前的数据（避免未来函数）
        """
        self.sr_analyzer.before_ts = before_ts
        try:
            result = self.sr_analyzer.multi_timeframe_analysis(symbol)
        finally:
            self.sr_analyzer.before_ts = None  # 用完重置，不影响正常使用

        # 统一字段：final_score → score
        supports = []
        for lv in result.get('supports', []):
            supports.append({
                'price': lv['price'],
                'score': lv.get('final_score', 7),
                'type':  lv.get('type', lv.get('types', ['unknown'])[0] if lv.get('types') else 'unknown'),
            })

        resistances = []
        for lv in result.get('resistances', []):
            resistances.append({
                'price': lv['price'],
                'score': lv.get('final_score', 7),
                'type':  lv.get('type', lv.get('types', ['unknown'])[0] if lv.get('types') else 'unknown'),
            })

        return supports, resistances

    # ── 单笔交易模拟 ────────────────────────────────────────────────────

    def _simulate_trade(self, direction: str, entry_price: float,
                        stop_price: float, target_price: float,
                        future_bars: List[Dict]) -> Dict:
        """
        模拟一笔交易，逐根 K 线判断止损/止盈/超时
        direction: 'long' | 'short'
        返回交易结果字典
        """
        stop_dist = abs(entry_price - stop_price)
        target_dist = abs(target_price - entry_price)
        rr = target_dist / stop_dist if stop_dist > 0 else 0

        result = {
            'direction': direction,
            'entry_price': entry_price,
            'stop_price': stop_price,
            'target_price': target_price,
            'rr': round(rr, 2),
            'exit_price': None,
            'exit_reason': None,
            'bars_held': 0,
            'pnl_pct': 0.0,
            'win': False,
        }

        for i, bar in enumerate(future_bars[:self.cfg['max_bars']]):
            result['bars_held'] = i + 1

            if direction == 'long':
                # 先判止损（用 low），再判止盈（用 high）
                if bar['low'] <= stop_price:
                    result['exit_price'] = stop_price
                    result['exit_reason'] = 'stop_loss'
                    break
                if bar['high'] >= target_price:
                    result['exit_price'] = target_price
                    result['exit_reason'] = 'take_profit'
                    result['win'] = True
                    break
            else:  # short
                if bar['high'] >= stop_price:
                    result['exit_price'] = stop_price
                    result['exit_reason'] = 'stop_loss'
                    break
                if bar['low'] <= target_price:
                    result['exit_price'] = target_price
                    result['exit_reason'] = 'take_profit'
                    result['win'] = True
                    break
        else:
            # 超时平仓
            result['exit_price'] = future_bars[min(self.cfg['max_bars'], len(future_bars)) - 1]['close']
            result['exit_reason'] = 'timeout'
            result['win'] = (
                result['exit_price'] > entry_price if direction == 'long'
                else result['exit_price'] < entry_price
            )

        if result['exit_price']:
            if direction == 'long':
                result['pnl_pct'] = (result['exit_price'] - entry_price) / entry_price * 100
            else:
                result['pnl_pct'] = (entry_price - result['exit_price']) / entry_price * 100

        return result

    def _get_monthly_trend(self, monthly_bars: List[Dict], ts: int) -> Optional[str]:
        """
        根据时间戳查找对应月线K线的趋势方向。
        返回 'bull'（多头）、'bear'（空头）或 None（数据不足）。
        判断逻辑：close > ema25 或 close > ema50 → 多头；反之 → 空头。
        """
        # 找到 ts 之前最近一根月线（二分查找）
        lo, hi = 0, len(monthly_bars) - 1
        idx = -1
        while lo <= hi:
            mid = (lo + hi) // 2
            if monthly_bars[mid]['timestamp'] < ts:
                idx = mid
                lo = mid + 1
            else:
                hi = mid - 1
        if idx < 0:
            return None
        bar = monthly_bars[idx]
        close = bar.get('close') or 0
        ema25 = bar.get('ema25')
        ema50 = bar.get('ema50')
        if close <= 0:
            return None
        # close > ema25 或 close > ema50 任一满足即视为多头
        bull = (ema25 and close > ema25) or (ema50 and close > ema50)
        return 'bull' if bull else 'bear'

    # ── 主回测循环 ──────────────────────────────────────────────────────

    def run(self, symbol: str = 'BTCUSDT') -> Dict[str, Any]:
        """执行完整回测，返回所有交易记录和统计"""
        logger.info(f"🚀 开始回测 {symbol} ...")

        all_bars = self._fetch_klines(symbol, self.cfg['exec_timeframe'])
        if len(all_bars) < self.cfg['sr_lookback_bars'] + self.cfg['max_bars'] + 10:
            raise ValueError(f"数据不足，只有 {len(all_bars)} 根 K 线")

        # 加载月线数据用于趋势过滤（一次性，避免循环内查询）
        monthly_bars = self._fetch_klines(symbol, '1M')
        logger.info(f"📅 月线数据: {len(monthly_bars)} 根，用于趋势过滤")

        # 打印数据覆盖范围
        first_dt = datetime.fromtimestamp(all_bars[0]['timestamp'] / 1000).strftime('%Y-%m-%d')
        last_dt  = datetime.fromtimestamp(all_bars[-1]['timestamp'] / 1000).strftime('%Y-%m-%d')
        logger.info(f"📊 数据范围: {first_dt} ~ {last_dt}，共 {len(all_bars)} 根4H K线"
                    f"（约 {len(all_bars) * 4 / 24 / 365:.1f} 年）")

        trades: List[Dict] = []
        last_sr_calc_idx = -999
        last_regime_calc_idx = -999
        supports, resistances = [], []
        regime = {'allow_long': True, 'allow_short': True, 'overall': 'range'}
        next_trade_idx = 0

        start_idx = self.cfg['sr_lookback_bars']
        end_idx   = len(all_bars) - self.cfg['max_bars'] - 1

        logger.info(f"回测区间: [{start_idx}, {end_idx}]，共 {end_idx - start_idx} 根 K 线")

        for i in range(start_idx, end_idx):
            bar = all_bars[i]
            atr = bar.get('atr') or 500.0   # 兜底值

            # 每隔 regime_recalc_interval 根 K 线重新判断市场状态
            if i - last_regime_calc_idx >= self.cfg['regime_recalc_interval']:
                try:
                    regime = self.regime_analyzer.analyze(
                        symbol=symbol,
                        before_ts=bar['timestamp']
                    )
                    if i == start_idx:
                        logger.info(f"🌍 首次市场状态: {regime['overall'].upper()} "
                                    f"(得分:{regime['weighted_score']:+.1f}) "
                                    f"多:{regime['allow_long']} 空:{regime['allow_short']}")
                except Exception as e:
                    logger.debug(f"市场状态判断失败 i={i}: {e}")
                last_regime_calc_idx = i

            # 每隔 sr_recalc_interval 根 K 线重新计算支撑阻力位
            if i - last_sr_calc_idx >= self.cfg['sr_recalc_interval']:
                try:
                    supports, resistances = self._calc_sr_levels(
                        before_ts=bar['timestamp'],
                        current_price=bar['close'],
                        symbol=symbol
                    )
                    if i == start_idx:
                        logger.info(f"🔍 首次位点计算: {len(supports)}支撑, {len(resistances)}阻力, "
                                    f"价格={bar['close']:.0f}, ATR={atr:.0f}")
                except Exception as e:
                    logger.debug(f"位点计算失败 i={i}: {e}")
                    supports, resistances = [], []
                last_sr_calc_idx = i

            # 上笔交易未出场，跳过
            if i < next_trade_idx:
                continue

            # ── 趋势过滤（多周期市场状态 + 4H均线双重确认）────────
            ema7  = bar.get('ema7')
            ema25 = bar.get('ema25')
            ema50 = bar.get('ema50')
            close = bar['close']
            # 4H均线确认（执行层）
            bull_4h = (ema7 and ema25 and ema7 > ema25) or (ema50 and close > ema50)
            bear_4h = (ema7 and ema25 and ema7 < ema25) or (ema50 and close < ema50)
            # 综合：市场状态允许 且 4H均线同向
            allow_long  = regime['allow_long']  and bull_4h
            allow_short = regime['allow_short'] and bear_4h

            # ── 做多：检查支撑位触及，挂限价单 ──────────────────────
            if allow_long:
                for sup in supports:
                    if sup.get('score', 0) < self.cfg['min_score']:
                        continue
                    touch_zone = atr * self.cfg['touch_atr_mult']
                    if abs(bar['low'] - sup['price']) > touch_zone:
                        continue

                    # 限价单入场：支撑位稍上方，止损在支撑位下方 1×ATR
                    entry = sup['price'] + atr * self.cfg['entry_buffer_mult']
                    stop  = sup['price'] - atr * self.cfg['stop_atr_mult']
                    stop_dist = entry - stop
                    if stop_dist <= 0:
                        continue

                    # 目标：最近阻力位 或 entry + min_rr×stop_dist
                    default_target = entry + self.cfg['min_rr'] * stop_dist
                    res_above = [r for r in resistances if r['price'] > entry]
                    if res_above:
                        nearest_res = min(res_above, key=lambda x: x['price'])
                        target = min(nearest_res['price'], default_target * 1.05)
                        target = max(target, default_target)
                    else:
                        target = default_target

                    rr = (target - entry) / stop_dist
                    if rr < self.cfg['min_rr']:
                        continue

                    # 下一根K线判断限价单是否成交（low <= entry 才成交）
                    future = all_bars[i + 1: i + 1 + self.cfg['max_bars']]
                    if not future or future[0]['low'] > entry:
                        continue

                    trade = self._simulate_trade('long', entry, stop, target, future)
                    trade.update({
                        'bar_idx': i,
                        'timestamp': bar['timestamp'],
                        'level_price': sup['price'],
                        'level_score': sup.get('score', 0),
                        'level_type': sup.get('type', ''),
                        'atr': atr,
                        'regime': regime['overall'],
                    })
                    trades.append(trade)
                    next_trade_idx = i + 1 + trade['bars_held']
                    break

            # ── 做空：检查阻力位触及，挂限价单 ──────────────────────
            if allow_short:
                for res in resistances:
                    if res.get('score', 0) < self.cfg['min_score']:
                        continue
                    touch_zone = atr * self.cfg['touch_atr_mult']
                    if abs(bar['high'] - res['price']) > touch_zone:
                        continue

                    # 限价单入场：阻力位稍下方，止损在阻力位上方 1×ATR
                    entry = res['price'] - atr * self.cfg['entry_buffer_mult']
                    stop  = res['price'] + atr * self.cfg['stop_atr_mult']
                    stop_dist = stop - entry
                    if stop_dist <= 0:
                        continue

                    default_target = entry - self.cfg['min_rr'] * stop_dist
                    sup_below = [s for s in supports if s['price'] < entry]
                    if sup_below:
                        nearest_sup = max(sup_below, key=lambda x: x['price'])
                        target = max(nearest_sup['price'], default_target * 0.95)
                        target = min(target, default_target)
                    else:
                        target = default_target

                    rr = (entry - target) / stop_dist
                    if rr < self.cfg['min_rr']:
                        continue

                    # 下一根K线判断限价单是否成交（high >= entry 才成交）
                    future = all_bars[i + 1: i + 1 + self.cfg['max_bars']]
                    if not future or future[0]['high'] < entry:
                        continue

                    trade = self._simulate_trade('short', entry, stop, target, future)
                    trade.update({
                        'bar_idx': i,
                        'timestamp': bar['timestamp'],
                        'level_price': res['price'],
                        'level_score': res.get('score', 0),
                        'level_type': res.get('type', ''),
                        'atr': atr,
                        'regime': regime['overall'],
                    })
                    trades.append(trade)
                    next_trade_idx = i + 1 + trade['bars_held']
                    break

        logger.info(f"✅ 回测完成，共触发 {len(trades)} 笔交易")
        return self._build_report(trades)

    # ── 统计报告 ────────────────────────────────────────────────────────

    def _build_report(self, trades: List[Dict]) -> Dict[str, Any]:
        """生成完整统计报告"""
        if not trades:
            return {'trades': [], 'stats': {}, 'by_direction': {}, 'by_score': {}}

        def stats_for(subset: List[Dict]) -> Dict:
            if not subset:
                return {}
            wins   = [t for t in subset if t['win']]
            losses = [t for t in subset if not t['win']]
            win_pnl  = [t['pnl_pct'] for t in wins]
            loss_pnl = [t['pnl_pct'] for t in losses]

            win_rate   = len(wins) / len(subset)
            avg_win    = np.mean(win_pnl)  if win_pnl  else 0
            avg_loss   = np.mean(loss_pnl) if loss_pnl else 0
            profit_factor = (sum(win_pnl) / abs(sum(loss_pnl))
                             if loss_pnl and sum(loss_pnl) != 0 else float('inf'))
            expectancy = win_rate * avg_win + (1 - win_rate) * avg_loss

            # 最大连续亏损
            max_consec_loss = cur = 0
            for t in subset:
                cur = cur + 1 if not t['win'] else 0
                max_consec_loss = max(max_consec_loss, cur)

            # 最大回撤（按 pnl_pct 累计）
            equity = np.cumsum([t['pnl_pct'] for t in subset])
            peak   = np.maximum.accumulate(equity)
            dd     = equity - peak
            max_dd = float(np.min(dd))

            return {
                'total':            len(subset),
                'wins':             len(wins),
                'losses':           len(losses),
                'win_rate':         round(win_rate * 100, 1),
                'avg_win_pct':      round(avg_win, 2),
                'avg_loss_pct':     round(avg_loss, 2),
                'avg_rr':           round(np.mean([t['rr'] for t in subset]), 2),
                'profit_factor':    round(profit_factor, 2),
                'expectancy_pct':   round(expectancy, 2),
                'max_consec_loss':  max_consec_loss,
                'max_drawdown_pct': round(max_dd, 2),
                'total_pnl_pct':    round(float(equity[-1]) if len(equity) else 0, 2),
                'exit_reasons':     {
                    'take_profit': sum(1 for t in subset if t['exit_reason'] == 'take_profit'),
                    'stop_loss':   sum(1 for t in subset if t['exit_reason'] == 'stop_loss'),
                    'timeout':     sum(1 for t in subset if t['exit_reason'] == 'timeout'),
                },
            }

        longs  = [t for t in trades if t['direction'] == 'long']
        shorts = [t for t in trades if t['direction'] == 'short']

        # 按评分分组
        score_groups = {}
        for t in trades:
            bucket = f"{(t['level_score'] // 2) * 2}-{(t['level_score'] // 2) * 2 + 1}"
            score_groups.setdefault(bucket, []).append(t)

        return {
            'trades':        trades,
            'stats':         stats_for(trades),
            'by_direction':  {
                'long':  stats_for(longs),
                'short': stats_for(shorts),
            },
            'by_score':      {k: stats_for(v) for k, v in sorted(score_groups.items())},
        }
