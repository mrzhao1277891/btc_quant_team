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
    'touch_atr_mult': 0.5,
    # 止损距离：位点 ± stop_atr_mult × ATR
    'stop_atr_mult': 1.0,
    # 最小盈亏比：低于此不入场
    'min_rr': 2.0,
    # 最大持仓根数（4H K线数），超过强制平仓
    'max_bars': 12,          # 12根4H = 48小时
    # 位点最低评分（final_score，1-15分），低于此不交易
    'min_score': 7,
    # 反弹/回落成立的最小幅度（相对入场价）
    'min_move_pct': 0.005,   # 0.5%
    # 回测用的 K 线时间框架
    'exec_timeframe': '4h',
    # 计算支撑阻力位时，每次向前看多少根 K 线
    'sr_lookback_bars': 200,
    # 支撑阻力位计算间隔（每隔多少根 K 线重新计算一次，节省时间）
    'sr_recalc_interval': 6,
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

    # ── 数据库 ──────────────────────────────────────────────────────────

    def connect(self):
        self.conn = mysql.connector.connect(**self.db_config)
        logger.info("✅ 数据库连接成功")

    def disconnect(self):
        if self.conn and self.conn.is_connected():
            self.conn.close()

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

    # ── 支撑阻力位计算（滚动，避免未来函数）──────────────────────────

    def _calc_sr_levels(self, klines: List[Dict], current_price: float
                        ) -> Tuple[List[Dict], List[Dict]]:
        """
        用传入的历史 K 线计算支撑阻力位（独立实现，不依赖外部模块）
        包含：摆动高低点 + 斐波那契回撤/延伸
        """
        closes = [k['close'] for k in klines]
        highs  = [k['high']  for k in klines]
        lows   = [k['low']   for k in klines]

        supports, resistances = [], []

        # ── 1. 摆动高低点 ──────────────────────────────────────────────
        window = 3
        n = len(closes)
        for i in range(window, n - window):
            # 摆动低点
            if all(lows[i] < lows[i-j] and lows[i] < lows[i+j] for j in range(1, window+1)):
                p = lows[i]
                score = 8  # 摆动点基础分
                (supports if p < current_price else resistances).append(
                    {'price': p, 'type': 'technical', 'score': score})
            # 摆动高点
            if all(highs[i] > highs[i-j] and highs[i] > highs[i+j] for j in range(1, window+1)):
                p = highs[i]
                score = 8
                (resistances if p > current_price else supports).append(
                    {'price': p, 'type': 'technical', 'score': score})

        # ── 2. 斐波那契（近期波段）────────────────────────────────────
        recent = closes[-100:] if len(closes) >= 100 else closes
        recent_h = highs[-100:] if len(highs) >= 100 else highs
        recent_l = lows[-100:]  if len(lows)  >= 100 else lows

        # 找近期局部高低点（窗口=5）
        w = 5
        local_highs, local_lows = [], []
        for i in range(w, len(recent) - w):
            if all(recent_h[i] >= recent_h[i-j] and recent_h[i] >= recent_h[i+j]
                   for j in range(1, w+1)):
                local_highs.append((i, recent_h[i]))
            if all(recent_l[i] <= recent_l[i-j] and recent_l[i] <= recent_l[i+j]
                   for j in range(1, w+1)):
                local_lows.append((i, recent_l[i]))

        waves = []
        if local_highs and local_lows:
            last_hi_idx, last_hi = local_highs[-1]
            last_lo_idx, last_lo = local_lows[-1]
            diff = abs(last_hi - last_lo)
            amp  = diff / max(last_lo, 1)
            if amp >= 0.03:
                if last_hi_idx > last_lo_idx:
                    waves.append(('up', last_lo, last_hi))
                else:
                    waves.append(('down', last_hi, last_lo))

        if not waves:
            # 兜底：全段高低点
            sh, sl = max(recent_h), min(recent_l)
            if (sh - sl) / max(sl, 1) >= 0.03:
                waves.append(('down', sh, sl))

        ret_ratios = [0.236, 0.382, 0.5, 0.618, 0.786]
        ext_ratios = [1.272, 1.618]

        for direction, wa, wb in waves:
            diff = abs(wb - wa)
            if diff <= 0:
                continue
            hi = max(wa, wb)
            lo = min(wa, wb)

            if direction == 'up':
                # 回撤位（下方支撑）
                for r in ret_ratios:
                    p = hi - diff * r
                    score = 10 if r in (0.382, 0.618) else 8
                    (supports if p < current_price else resistances).append(
                        {'price': round(p, 2), 'type': 'fibonacci', 'score': score})
                # 延伸位（上方阻力）
                for r in ext_ratios:
                    p = lo + diff * r
                    if p > current_price:
                        resistances.append(
                            {'price': round(p, 2), 'type': 'fibonacci', 'score': 8})
            else:
                # 回撤位（上方阻力）
                for r in ret_ratios:
                    p = lo + diff * r
                    score = 10 if r in (0.382, 0.618) else 8
                    (resistances if p > current_price else supports).append(
                        {'price': round(p, 2), 'type': 'fibonacci', 'score': score})
                # 延伸位（下方支撑）
                for r in ext_ratios:
                    p = hi - diff * r
                    if p < current_price:
                        supports.append(
                            {'price': round(p, 2), 'type': 'fibonacci', 'score': 8})

        # ── 3. 均线位（直接从 klines 数据读最新一根的均线字段）────────
        latest = klines[-1]
        for key, score in [('ema50', 9), ('ema25', 8), ('ema7', 7),
                            ('boll_up', 8), ('boll_dn', 8), ('boll_md', 7)]:
            val = latest.get(key)
            if val and val > 0:
                p = float(val)
                (supports if p < current_price else resistances).append(
                    {'price': p, 'type': 'dynamic', 'score': score})

        supports    = self._dedup_levels(supports)
        resistances = self._dedup_levels(resistances)
        return supports, resistances

    def _dedup_levels(self, levels: List[Dict], tol_pct: float = 0.01) -> List[Dict]:
        if not levels:
            return []
        levels = sorted(levels, key=lambda x: x['price'])
        merged = [levels[0]]
        for lv in levels[1:]:
            if abs(lv['price'] - merged[-1]['price']) / max(merged[-1]['price'], 1) <= tol_pct:
                # 保留评分更高的
                if lv.get('score', 0) > merged[-1].get('score', 0):
                    merged[-1] = lv
            else:
                merged.append(lv)
        return merged

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

    # ── 主回测循环 ──────────────────────────────────────────────────────

    def run(self, symbol: str = 'BTCUSDT') -> Dict[str, Any]:
        """执行完整回测，返回所有交易记录和统计"""
        logger.info(f"🚀 开始回测 {symbol} ...")

        all_bars = self._fetch_klines(symbol, self.cfg['exec_timeframe'])
        if len(all_bars) < self.cfg['sr_lookback_bars'] + self.cfg['max_bars'] + 10:
            raise ValueError(f"数据不足，只有 {len(all_bars)} 根 K 线")

        trades: List[Dict] = []
        last_sr_calc_idx = -999
        supports, resistances = [], []
        next_trade_idx = 0   # 下一笔可开仓的 K 线索引（上笔出场后才能开新仓）

        start_idx = self.cfg['sr_lookback_bars']
        end_idx   = len(all_bars) - self.cfg['max_bars'] - 1

        logger.info(f"回测区间: [{start_idx}, {end_idx}]，共 {end_idx - start_idx} 根 K 线")

        for i in range(start_idx, end_idx):
            bar = all_bars[i]
            atr = bar.get('atr') or 500.0   # 兜底值

            # 每隔 sr_recalc_interval 根 K 线重新计算支撑阻力位
            if i - last_sr_calc_idx >= self.cfg['sr_recalc_interval']:
                history = all_bars[max(0, i - self.cfg['sr_lookback_bars']):i]
                try:
                    supports, resistances = self._calc_sr_levels(history, bar['close'])
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

            # ── 做多：检查支撑位触及 ──────────────────────────────────
            for sup in supports:
                if sup.get('score', 0) < self.cfg['min_score']:
                    continue
                touch_zone = atr * self.cfg['touch_atr_mult']
                if abs(bar['low'] - sup['price']) > touch_zone:
                    continue

                entry  = bar['close']
                stop   = sup['price'] - atr * self.cfg['stop_atr_mult']
                stop_dist = entry - stop
                if stop_dist <= 0:
                    continue

                # 目标：最近阻力位 或 entry + 2×stop_dist
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

                future = all_bars[i + 1: i + 1 + self.cfg['max_bars']]
                trade = self._simulate_trade('long', entry, stop, target, future)
                trade.update({
                    'bar_idx': i,
                    'timestamp': bar['timestamp'],
                    'level_price': sup['price'],
                    'level_score': sup.get('score', 0),
                    'level_type': sup.get('type', ''),
                    'atr': atr,
                })
                trades.append(trade)
                in_trade = True
                break

            if in_trade:
                in_trade = False   # 简化：每笔交易独立，不锁仓
                continue

            # ── 做空：检查阻力位触及 ──────────────────────────────────
            for res in resistances:
                if res.get('score', 0) < self.cfg['min_score']:
                    continue
                touch_zone = atr * self.cfg['touch_atr_mult']
                if abs(bar['high'] - res['price']) > touch_zone:
                    continue

                entry  = bar['close']
                stop   = res['price'] + atr * self.cfg['stop_atr_mult']
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

                future = all_bars[i + 1: i + 1 + self.cfg['max_bars']]
                trade = self._simulate_trade('short', entry, stop, target, future)
                trade.update({
                    'bar_idx': i,
                    'timestamp': bar['timestamp'],
                    'level_price': res['price'],
                    'level_score': res.get('score', 0),
                    'level_type': res.get('type', ''),
                    'atr': atr,
                })
                trades.append(trade)
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
