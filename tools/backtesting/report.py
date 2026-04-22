#!/usr/bin/env python3
"""回测报告输出"""

from typing import Dict, Any


def print_report(report: Dict[str, Any]):
    trades = report.get('trades', [])
    stats  = report.get('stats', {})

    print("\n" + "=" * 70)
    print("📊 支撑阻力位回测报告")
    print("=" * 70)

    if not trades:
        print("⚠️  没有触发任何交易，请检查参数或数据")
        return

    # ── 总体统计 ──────────────────────────────────────────────────────
    print(f"\n【总体统计】  共 {stats['total']} 笔")
    print(f"  胜率          : {stats['win_rate']}%  "
          f"({stats['wins']}胜 / {stats['losses']}负)")
    print(f"  平均盈亏比    : {stats['avg_rr']}")
    print(f"  盈利因子      : {stats['profit_factor']}")
    print(f"  期望收益/笔   : {stats['expectancy_pct']}%")
    print(f"  平均盈利      : +{stats['avg_win_pct']}%")
    print(f"  平均亏损      : {stats['avg_loss_pct']}%")
    print(f"  最大连续亏损  : {stats['max_consec_loss']} 笔")
    print(f"  最大回撤      : {stats['max_drawdown_pct']}%")
    print(f"  累计收益      : {stats['total_pnl_pct']}%")
    er = stats['exit_reasons']
    print(f"  出场原因      : 止盈 {er['take_profit']} | "
          f"止损 {er['stop_loss']} | 超时 {er['timeout']}")

    # ── 做多 vs 做空 ──────────────────────────────────────────────────
    print(f"\n{'─'*70}")
    print("【方向对比】")
    bd = report.get('by_direction', {})
    for direction, label in [('long', '做多（支撑位）'), ('short', '做空（阻力位）')]:
        s = bd.get(direction, {})
        if not s:
            print(f"  {label}: 无交易")
            continue
        print(f"\n  {label}  ({s['total']} 笔)")
        print(f"    胜率: {s['win_rate']}%  |  盈利因子: {s['profit_factor']}  "
              f"|  期望: {s['expectancy_pct']}%  |  最大回撤: {s['max_drawdown_pct']}%")
        print(f"    平均盈利: +{s['avg_win_pct']}%  |  平均亏损: {s['avg_loss_pct']}%  "
              f"|  最大连续亏损: {s['max_consec_loss']} 笔")

    # ── 按评分分组 ────────────────────────────────────────────────────
    print(f"\n{'─'*70}")
    print("【评分分组】（验证评分越高胜率是否越高）")
    print(f"  {'评分区间':10} {'笔数':>6} {'胜率':>8} {'盈利因子':>10} {'期望%':>8} {'最大回撤':>10}")
    print(f"  {'─'*10} {'─'*6} {'─'*8} {'─'*10} {'─'*8} {'─'*10}")
    for bucket, s in sorted(report.get('by_score', {}).items()):
        if not s:
            continue
        print(f"  {bucket:10} {s['total']:>6} {s['win_rate']:>7}% "
              f"{s['profit_factor']:>10} {s['expectancy_pct']:>7}% "
              f"{s['max_drawdown_pct']:>9}%")

    # ── 最近 10 笔交易明细 ────────────────────────────────────────────
    print(f"\n{'─'*70}")
    print("【最近 10 笔交易明细】")
    print(f"  {'时间':20} {'方向':6} {'入场':>10} {'止损':>10} {'目标':>10} "
          f"{'出场':>10} {'原因':10} {'盈亏%':>7} {'结果':6}")
    print(f"  {'─'*20} {'─'*6} {'─'*10} {'─'*10} {'─'*10} "
          f"{'─'*10} {'─'*10} {'─'*7} {'─'*6}")
    from datetime import datetime
    for t in trades[-10:]:
        ts = datetime.fromtimestamp(t['timestamp'] / 1000).strftime('%Y-%m-%d %H:%M')
        result = '✅ 盈' if t['win'] else '❌ 亏'
        print(f"  {ts:20} {t['direction']:6} "
              f"{t['entry_price']:>10,.0f} {t['stop_price']:>10,.0f} "
              f"{t['target_price']:>10,.0f} {t['exit_price']:>10,.0f} "
              f"{t['exit_reason']:10} {t['pnl_pct']:>+6.2f}% {result}")

    print("\n" + "=" * 70)
