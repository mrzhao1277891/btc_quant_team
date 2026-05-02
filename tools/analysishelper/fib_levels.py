#!/usr/bin/env python3
"""
斐波那契位计算工具（手动设置波段）

用法：
  # 直接在代码里设置波段
  python3 tools/analysis/fib_levels.py --password 你的密码

  # 命令行传入波段
  python3 tools/analysis/fib_levels.py --password 你的密码 \
      --1M-high 126200 --1M-low 60000 \
      --1w-high 98364  --1w-low 64220  \
      --1d-high 97924  --1d-low 65000  \
      --4h-high 79486  --4h-low 73724

波段方向自动判断：
  high > low 且 high 在后 → 上涨波段（计算回撤位）
  high > low 且 low  在后 → 下跌波段（计算回撤位）
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# ── 斐波那契比例 ─────────────────────────────────────────────────
RETRACEMENT_RATIOS = [0.236, 0.382, 0.5, 0.618, 0.786]
EXTENSION_RATIOS   = [1.0, 1.272, 1.618, 2.0]

# ── 各周期波段配置（手动设置，None 表示不计算该周期）────────────
# 格式：(high, low, direction)
#   direction: 'up'   = 上涨波段（从 low 涨到 high，计算回撤支撑）
#              'down' = 下跌波段（从 high 跌到 low，计算回撤阻力）
#              'auto' = 自动判断（根据哪个在后面）
WAVE_CONFIG: Dict[str, Optional[Tuple[float, float, str]]] = {
    '1M': (126200, 60000, 'down'),   # 月线：从高点跌到低点
    '1w': (98364,  64220, 'up'),     # 周线：从低点涨到高点
    '1d': (97924,  65000, 'down'),   # 日线：从高点跌到低点
    '4h': (88.08,  81.4, 'down'),   # 4H：从高点跌到低点
}

TF_LABELS = {'1M': '月线', '1w': '周线', '1d': '日线', '4h': '4H'}


def _get_current_price(symbol: str = 'BTCUSDT') -> Optional[float]:
    try:
        resp = requests.get(
            'https://api.binance.com/api/v3/ticker/price',
            params={'symbol': symbol}, timeout=5
        )
        resp.raise_for_status()
        return float(resp.json()['price'])
    except Exception:
        return None


def calc_fib_levels(high: float, low: float, direction: str,
                    current_price: float) -> Dict:
    """
    计算斐波那契回撤位和延伸位。

    direction='up'：上涨波段，回撤位在下方（支撑），延伸位在上方（阻力）
    direction='down'：下跌波段，回撤位在上方（阻力），延伸位在下方（支撑）
    """
    diff = high - low
    if diff <= 0:
        return {}

    levels = {'supports': [], 'resistances': [], 'direction': direction,
               'wave_high': high, 'wave_low': low}

    if direction == 'up':
        # 上涨波段：回撤位 = high - diff × ratio（下方支撑）
        for r in RETRACEMENT_RATIOS:
            price = round(high - diff * r, 2)
            dist  = (current_price - price) / current_price * 100
            entry = {
                'price': price, 'ratio': r,
                'label': f'回撤{r*100:.1f}%',
                'dist_pct': dist,
                'side': 'support' if price < current_price else 'resistance'
            }
            if price < current_price:
                levels['supports'].append(entry)
            else:
                levels['resistances'].append(entry)
        # 延伸位 = low + diff × ratio（上方阻力）
        for r in EXTENSION_RATIOS:
            price = round(low + diff * r, 2)
            dist  = (price - current_price) / current_price * 100
            if price > current_price:
                levels['resistances'].append({
                    'price': price, 'ratio': r,
                    'label': f'延伸{r*100:.1f}%',
                    'dist_pct': dist, 'side': 'resistance'
                })

    else:  # down
        # 下跌波段：回撤位 = low + diff × ratio（上方阻力）
        for r in RETRACEMENT_RATIOS:
            price = round(low + diff * r, 2)
            dist  = (price - current_price) / current_price * 100
            entry = {
                'price': price, 'ratio': r,
                'label': f'回撤{r*100:.1f}%',
                'dist_pct': dist,
                'side': 'resistance' if price > current_price else 'support'
            }
            if price > current_price:
                levels['resistances'].append(entry)
            else:
                levels['supports'].append(entry)
        # 延伸位 = high - diff × ratio（下方支撑）
        for r in EXTENSION_RATIOS:
            price = round(high - diff * r, 2)
            dist  = (current_price - price) / current_price * 100
            if price < current_price:
                levels['supports'].append({
                    'price': price, 'ratio': r,
                    'label': f'延伸{r*100:.1f}%',
                    'dist_pct': dist, 'side': 'support'
                })

    # 按距当前价格排序
    levels['supports'].sort(key=lambda x: x['dist_pct'])
    levels['resistances'].sort(key=lambda x: x['dist_pct'])
    return levels


def print_report(wave_config: Dict, symbol: str = 'BTCUSDT'):
    current_price = _get_current_price(symbol)
    if current_price is None:
        print("⚠️  无法获取实时价格，请检查网络")
        return

    print(f"\n{'='*60}")
    print(f"📐 {symbol} 斐波那契位分析  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"当前价格: ${current_price:,.2f}")
    print(f"{'='*60}")

    all_supports    = []
    all_resistances = []

    for tf in ['1M', '1w', '1d', '4h']:
        wave = wave_config.get(tf)
        if wave is None:
            continue
        high, low, direction = wave
        if high <= low:
            print(f"\n⚠️  {TF_LABELS[tf]}: high({high}) 必须大于 low({low})，跳过")
            continue

        result = calc_fib_levels(high, low, direction, current_price)
        if not result:
            continue

        dir_str = '上涨波段↑' if direction == 'up' else '下跌波段↓'
        amp_pct = (high - low) / low * 100

        print(f"\n【{TF_LABELS[tf]}】{dir_str}  "
              f"${low:,.0f} ~ ${high:,.0f}  振幅{amp_pct:.1f}%")
        print(f"{'─'*60}")

        print("  📉 阻力位（由近到远）:")
        for lv in result['resistances'][:5]:
            print(f"    ${lv['price']:>10,.2f}  +{lv['dist_pct']:.1f}%  {lv['label']}")

        print("  📈 支撑位（由近到远）:")
        for lv in result['supports'][:5]:
            print(f"    ${lv['price']:>10,.2f}  -{lv['dist_pct']:.1f}%  {lv['label']}")

        # 收集用于综合视图
        for lv in result['resistances']:
            all_resistances.append({**lv, 'timeframe': tf})
        for lv in result['supports']:
            all_supports.append({**lv, 'timeframe': tf})

    # 综合视图：所有周期合并，按距离排序
    print(f"\n{'='*60}")
    print("🔥 综合视图（所有周期，按距当前价格排序）")
    print(f"{'='*60}")

    all_resistances.sort(key=lambda x: x['dist_pct'])
    all_supports.sort(key=lambda x: x['dist_pct'])

    print("\n  📉 上方阻力（由近到远）:")
    for lv in all_resistances[:8]:
        tf_label = TF_LABELS.get(lv['timeframe'], lv['timeframe'])
        print(f"    ${lv['price']:>10,.2f}  +{lv['dist_pct']:.1f}%  "
              f"{tf_label} {lv['label']}")

    print("\n  📈 下方支撑（由近到远）:")
    for lv in all_supports[:8]:
        tf_label = TF_LABELS.get(lv['timeframe'], lv['timeframe'])
        print(f"    ${lv['price']:>10,.2f}  -{lv['dist_pct']:.1f}%  "
              f"{tf_label} {lv['label']}")

    print(f"\n{'='*60}")


def main():
    logging.basicConfig(level=logging.WARNING)
    print_report(WAVE_CONFIG)


if __name__ == '__main__':
    main()
