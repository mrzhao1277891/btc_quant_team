#!/usr/bin/env python3
"""统一数据刷新入口 —— 一条命令刷新全部数据源。

背景：原来有五条互不相干的命令，各自记参数、各自建日志，而且除了 K 线之外
都没有定时任务，导致 fed_rate_decisions 陈旧了 279 天没人发现。

    python3 tools/data/refresh_data.py --action refresh --password ''
    python3 scripts/fng_ingest.py update
    python3 scripts/etf_flow_ingest.py update
    python3 scripts/news_fetch.py update
    python3 scripts/fed_rate_ingest.py update

现在：

    python3 scripts/refresh_all.py                  # 全部刷新
    python3 scripts/refresh_all.py --only klines fng  # 只刷指定源
    python3 scripts/refresh_all.py --skip news      # 跳过指定源
    python3 scripts/refresh_all.py --list           # 列出所有源
    python3 scripts/refresh_all.py --dry-run        # 只打印将执行的命令

设计要点：
  · **每个源跑在独立子进程里**，一个崩溃/超时不影响其它源 —— 以前手动挨个跑，
    中间一个失败就得重来；合并成一个脚本后更不能让单点拖垮整体。
  · **每个源有独立超时**，防止某个上游挂住导致整条命令永远不返回。
  · **失败不中断**，最后统一汇报 + 非零退出码（cron 能据此告警）。
  · 退出码 = 失败源的数量（0 = 全成功）。
"""
import argparse
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PY = sys.executable

# (名称, 说明, 命令, 超时秒)
SOURCES = [
    ("klines",    "K线 + 技术指标 (4h/1d/1w/1M, BTC/ETH/SOL)",
     [PY, "tools/data/refresh_data.py", "--action", "refresh", "--password", ""], 600),

    ("fng",       "恐慌贪婪指数 (alternative.me)",
     [PY, "scripts/fng_ingest.py", "update"], 180),

    ("etf_flow",  "BTC 现货 ETF 净流入 (Farside)",
     [PY, "scripts/etf_flow_ingest.py", "update"], 300),

    ("fed_rates", "美联储利率决议 (AKShare)",
     [PY, "scripts/fed_rate_ingest.py", "update"], 300),

    # 放最后：它要跑 9 个 RSS + 一次 LLM 调用，是最慢的一个
    ("news",      "每日加密要闻 (9 个 RSS + LLM 排序翻译)",
     [PY, "scripts/news_fetch.py", "update"], 600),
]

BY_NAME = {s[0]: s for s in SOURCES}


def show(cmd):
    """把空参数渲染成 ''，否则 '--password ""' 打印出来是尾随空格，看不出是空串。"""
    return " ".join(f"'{c}'" if c == "" else c for c in cmd)


def run_one(name, desc, cmd, timeout):
    print(f"\n{'=' * 68}")
    print(f"▶ {name} — {desc}")
    print(f"  $ {show(cmd)}")
    print("=" * 68)

    t0 = time.time()
    try:
        p = subprocess.run(cmd, cwd=str(REPO), capture_output=True,
                           text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        el = time.time() - t0
        print(f"  ✗ 超时（{timeout}s）")
        return {"name": name, "ok": False, "elapsed": el,
                "detail": f"超时 {timeout}s"}

    el = time.time() - t0
    out = (p.stdout or "") + (p.stderr or "")
    # 成功时只显示末尾几行；失败时多给一些上下文
    lines = [l for l in out.splitlines() if l.strip()]
    tail = lines[-6:] if p.returncode == 0 else lines[-20:]
    for l in tail:
        print(f"  {l}")

    ok = p.returncode == 0
    print(f"  {'✓' if ok else '✗'} 退出码 {p.returncode}，耗时 {el:.1f}s")
    return {"name": name, "ok": ok, "elapsed": el,
            "detail": "" if ok else f"退出码 {p.returncode}"}


def main():
    ap = argparse.ArgumentParser(
        description="统一数据刷新入口",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="可用的源：\n  " + "\n  ".join(
            f"{n:<10} {d}" for n, d, _, _ in SOURCES))
    ap.add_argument("--only", nargs="+", metavar="NAME",
                    help="只刷新这些源")
    ap.add_argument("--skip", nargs="+", metavar="NAME", default=[],
                    help="跳过这些源")
    ap.add_argument("--list", action="store_true", help="列出所有源后退出")
    ap.add_argument("--dry-run", action="store_true", help="只打印将执行的命令")
    ap.add_argument("--continue-on-error", action="store_true", default=True,
                    help="某个源失败后继续跑其余源（默认开启）")
    args = ap.parse_args()

    if args.list:
        print("可刷新的数据源：")
        for n, d, cmd, to in SOURCES:
            print(f"  {n:<10} {d}")
            print(f"             {show(cmd)}  (超时 {to}s)")
        return 0

    # 校验源名，避免拼错后静默什么都不刷
    unknown = set((args.only or []) + args.skip) - set(BY_NAME)
    if unknown:
        print(f"✗ 未知的源: {sorted(unknown)}")
        print(f"  可用: {sorted(BY_NAME)}")
        return 2

    chosen = [BY_NAME[n] for n in (args.only or BY_NAME)]
    chosen = [s for s in chosen if s[0] not in args.skip]
    if not chosen:
        print("✗ 没有要刷新的源")
        return 2

    if args.dry_run:
        print("将依次执行：")
        for n, d, cmd, to in chosen:
            print(f"  [{n}] {show(cmd)}   (超时 {to}s)")
        return 0

    started = datetime.now(timezone.utc)
    print(f"数据刷新开始  {started:%Y-%m-%d %H:%M:%S} UTC")
    print(f"共 {len(chosen)} 个源：{', '.join(s[0] for s in chosen)}")

    results = []
    for name, desc, cmd, timeout in chosen:
        results.append(run_one(name, desc, cmd, timeout))

    total = time.time() - started.timestamp()
    failed = [r for r in results if not r["ok"]]

    print(f"\n{'=' * 68}")
    print(f"汇总  （总耗时 {total:.0f}s）")
    print("=" * 68)
    for r in results:
        print(f"  {'✓' if r['ok'] else '✗'} {r['name']:<10} {r['elapsed']:>6.1f}s"
              f"  {r['detail']}")
    print(f"\n  成功 {len(results) - len(failed)}/{len(results)}")

    if failed:
        print(f"\n⚠ 失败的源：{', '.join(r['name'] for r in failed)}")
        print("  建议单独重跑看完整输出，例如：")
        print(f"    python3 scripts/refresh_all.py --only {failed[0]['name']}")

    # 退出码 = 失败数，方便 cron/CI 判断
    return len(failed)


if __name__ == "__main__":
    sys.exit(main())
