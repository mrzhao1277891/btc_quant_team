#!/usr/bin/env python3
"""美联储利率决策历史数据入库。

两个数据源，各司其职 —— 单靠任何一个都不完整：

  ① FRED `DFEDTARU`（目标利率上限，日频序列）
     - 官方数据、当日更新、全历史
     - 但**只在利率变动时才有信号**：一次「按兵不动」的会议在序列上不留任何痕迹

  ② Fed 官网 FOMC 日历
     - 给出**所有**会议日期，包括没动利率的那些
     - 但只有日期，没有利率

用法:
    python3 scripts/fed_rate_ingest.py            # 增量补齐（= update，默认）
    python3 scripts/fed_rate_ingest.py update     # 同上（保持旧 CLI 兼容）
    python3 scripts/fed_rate_ingest.py init       # 同 update（幂等，不会重建表）
    python3 scripts/fed_rate_ingest.py --verify   # 只核对、不写库

━━━ 日期约定：存的是**生效日**，不是决议日 ━━━

表里的 `decision_date` 实际是**生效日**（决议次日）。这不是 bug，是刻意保留的：

  美联储 14:00 ET 公布决议 = **次日凌晨**北京时间（夏令时 02:00 / 冬令时 03:00）。
  本项目的 K 线是东八区的，所以「包含公布时刻的那根日线」正好就是生效日那天。

  实测：2025-09-17 决议 → 东八区 09-17 那根 -0.29%、09-18 那根 +0.54%（公布在其中）
        2024-09-18 决议 → 东八区 09-18 那根 +2.40%、09-19 那根 +1.92%（公布在其中）

  也就是说，这个日期和图上的反应 K 线是对齐的，直接标在图上不会错位。
  字段名沿用 `decision_date` 是历史原因（改它要重写全部 298 行，而 2020 年前的
  官方日历查不到，新旧会混用两种约定，得不偿失）。

━━━ 为什么不用 AKShare ━━━

原来用的 `ak.macro_bank_usa_interest_rate()` 已经坏了（2026-09 实测）：

  - 最新一条停在 2025-10-30，2025-12-11 那次决议**根本没有**
  - 2025-09-18 / 2025-10-30 两行的「今值」是 NaN（脚本跳过 NaN → 静默少两行）
  - 于是 update 跑多少次都是「0 rows」，退出码 0、没有任何报错 —— 静默降级

AKShare 是聚合的二手源，坏了只能等它修。FRED 是美联储自己的数据，直连。
"""
import argparse
import csv
import datetime
import decimal
import html as html_mod
import io
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.backtest.config import config  # noqa: E402
import mysql.connector  # noqa: E402

FRED_UPPER = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFEDTARU"
# 2008-12-15 之前的序列（已停更）。**必须一起拉** —— 只用 DFEDTARU 的话
# 它只能覆盖 2008 年以后，表一旦被清空重建，1982~2008 的历史就永久丢失。
# 这正是实际发生过的：有人清空表后重跑脚本，304 行变成了 44 行。
FRED_UPPER_OLD = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFEDTAR"
FOMC_CALENDAR = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
# DFEDTARU 的首日。两个序列日期口径的分界线，见 change_points() 的说明。
FRED_ERA_BOUNDARY = datetime.date(2008, 12, 16)

# ⚠ 两个源要求的 User-Agent 是**相反**的，实测（每个组合跑 2 次，结果稳定）：
#
#     UA             FRED           Fed 日历
#     不设 UA        ✓ 101KB        ✗ HTTPError
#     中性 UA        ✗ 超时         ✓ 161KB
#     浏览器 UA      ✗ 超时         ✓ 161KB
#
# FRED 对任何自定义 UA 都是**挂起**（超时，不是报错）—— 留空让它用 urllib 默认值。
# Fed 官网反过来，拒绝 Python-urllib 的默认 UA，必须带一个。
# 别「顺手」把它统一成一个 UA：那样两边会各坏一个，且 FRED 那边表现为卡住不返回。
UA_FRED = None                                   # None = 用 urllib 默认的 Python-urllib/x.y
UA_CALENDAR = "Mozilla/5.0 (compatible; btc-quant-team/1.0)"

MONTHS = ("January|February|March|April|May|June|July|August|September|"
          "October|November|December")


def _get(url, ua, timeout=30):
    headers = {"User-Agent": ua} if ua else {}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


def fetch_fred_series():
    """FRED 目标利率 → {date: Decimal}，覆盖 1982 年至今。

    两段拼接，缺一不可：
      DFEDTAR   1982-09-27 ~ 2008-12-15  （旧序列，已停更）
      DFEDTARU  2008-12-16 ~ 至今        （目标区间上限，与旧序列数值口径一致：
                                          2008-12-15 = 1.00 → 12-16 = 0.25，
                                          恰好对应 0~0.25% 区间）

    序列是**日历日**的（含周末，值顺延），所以「决议日之后第一行」不能直接
    当生效日，得按工作日推（见 effective_date）。
    """
    out = {}
    for url, col in ((FRED_UPPER_OLD, "DFEDTAR"), (FRED_UPPER, "DFEDTARU")):
        text = _get(url, UA_FRED)
        n = 0
        for row in csv.DictReader(io.StringIO(text)):
            d, v = row.get("observation_date"), row.get(col)
            if not d or v in (None, "", "."):
                continue
            out[datetime.date.fromisoformat(d)] = decimal.Decimal(v)
            n += 1
        print(f"    {col}: {n} 天")
    if not out:
        raise RuntimeError("FRED 返回空序列")
    return out


def change_points(series):
    """序列里所有利率变动点 → [(生效日, 新利率, 变动额, 类型)]。

    这是**重建历史的主力**，覆盖 1982 年以来的每一次加息/降息。

    局限：只有「动了利率」的会议才有信号，1982~2020 那些「按兵不动」的会议
    在序列上不留痕迹，重建不出来（要靠 FOMC 日历，而官方日历只到 2021）。

    ⚠ 日期口径：两个 FRED 序列**不是同一个口径**。拿库里的 184 个变动点逐条
    比对过，规律很干净 ——
        DFEDTAR （2008-12-15 及以前）：比生效日**早一天**，按决议日记的
        DFEDTARU（2008-12-16 起）  ：就是生效日，一天不差
    所以早期要 +1 天才能和表里其余行对齐。不校正的话，重建出来的 1982~2008
    会整体错位一天，而且和库里已有的行对不上（表现为「凭空多出 150 行」）。
    """
    ks = sorted(series)
    out = []
    for a, b in zip(ks, ks[1:]):
        if series[a] != series[b]:
            ch = series[b] - series[a]
            eff = b if b >= FRED_ERA_BOUNDARY else b + datetime.timedelta(days=1)
            out.append((eff, series[b], ch, "hike" if ch > 0 else "cut"))
    return out


def fetch_fomc_meetings():
    """官方 FOMC 日历 → 决议日列表（会议第二天）。

    按年切片解析：页面是「2026 FOMC Meetings」这样的年标题后面跟会议日期，
    必须用年标题当边界 —— 固定窗口会把邻年的会议串进来（2026 的 Jan 28
    被算成 2025 的第 9 次会议）。
    """
    text = _flatten(_get(FOMC_CALENDAR, UA_CALENDAR))
    text = re.sub(r"&nbsp;?", " ", text)

    heads = [(m.start(), int(m.group(1)))
             for m in re.finditer(r"(20\d\d) FOMC Meetings", text)]
    meetings = []
    for i, (pos, year) in enumerate(heads):
        seg = text[pos:heads[i + 1][0] if i + 1 < len(heads) else len(text)]
        for mon, _d1, d2 in re.findall(rf"({MONTHS})\s+(\d+)\s*[-–]\s*(\d+)", seg):
            m = datetime.datetime.strptime(mon, "%B").month
            meetings.append(datetime.date(year, m, int(d2)))
    if not meetings:
        raise RuntimeError("FOMC 日历解析出 0 次会议（页面结构可能变了）")
    return sorted(set(meetings))


def effective_date(decision):
    """生效日 = 决议日的下一个工作日。

    美联储的调息在决议次日生效（implementation note 原文）。
    这里只跳周末；万一碰上假日顺延，下面的 resolve 会用 FRED 的实际变动日校正。
    """
    d = decision + datetime.timedelta(days=1)
    while d.weekday() >= 5:
        d += datetime.timedelta(days=1)
    return d


def resolve(meeting, series, today):
    """把一次会议解析成 (生效日, 新利率, 变动额, 类型)；会议还没开则返回 None。

    生效日优先取「决议日的下一个工作日」，再用 FRED 的实际变动日校正 ——
    后者能同时兜住假日顺延和序列本身的修订。
    """
    # 变动前的基准取**决议前一天**的值，不是决议当天的。
    # FRED 的历史序列有个坑：2015-12 和 2016-12 那两次，新值在**决议当天**
    # 就出现了（其余 30 次都是次日）。若用决议当天的值当基准，算出来变动为 0，
    # 这两次加息会被误记成「按兵不动」。
    before = series.get(meeting - datetime.timedelta(days=1))
    if before is None:
        before = series.get(meeting) or _value_at_or_after(series, meeting)
    if before is None:
        return None

    eff = effective_date(meeting)
    # 若实际变动发生在更晚的日期（假日顺延），以后者为准。
    # 全程无变动说明是「按兵不动」，eff 保持推定值不动。
    probe = eff
    for _ in range(5):
        v = series.get(probe)
        if v is not None and v != before:
            eff = probe
            break
        probe += datetime.timedelta(days=1)

    if eff > today:
        return None                      # 会议还没开完，别猜

    rate = series.get(eff)
    if rate is None:
        # 会议刚开完、FRED 还没发布生效日那天的值 —— 退到官方文档
        return from_official(meeting, before)

    change = rate - before
    kind = "hike" if change > 0 else ("cut" if change < 0 else "hold")
    return eff, rate, change, kind


def _frac(s):
    """把美联储写法的利率转成数字：'3-3/4' → 3.75，'1/4' → 0.25，'4' → 4。"""
    s = s.strip()
    if "-" in s:
        w, f = s.split("-", 1)
        return float(w) + _frac(f)
    if "/" in s:
        a, b = s.split("/", 1)
        return float(a) / float(b)
    return float(s)


def from_official(meeting, before):
    """FRED 尚未发布时的兜底：直接解析美联储官方文档。

    为什么必须有这条路径：决议在 14:00 ET 公布，而 FRED 要到**次日**才有生效日
    的值 —— 中间十几个小时恰好是新决议影响最大的时候（实测 2026-09-16 那次
    加息 25bp 就落在窗口里，而脚本当时只能跳过它）。等一天对日级别交易太贵。

    两份文档各取一半（都是官方原文，比任何二手源的转述可靠）：
      - 声明       `.../monetary{YYYYMMDD}a.htm`  → 目标区间
      - 实施说明   `.../monetary{YYYYMMDD}a1.htm` → 生效日（原文写明）
    """
    stamp = meeting.strftime("%Y%m%d")
    base = "https://www.federalreserve.gov/newsevents/pressreleases/"

    try:
        st = _flatten(_get(base + f"monetary{stamp}a.htm", UA_CALENDAR))
    except Exception as e:
        print(f"    {meeting} 取声明失败: {type(e).__name__}")
        return None
    m = re.search(r"target range for the federal funds rate"
                  r"(?:\s+by\s+[^,]+,?)?\s+(?:to|at)\s+"
                  r"([\d\-\/ ]+?)\s+to\s+([\d\-\/ ]+?)\s+percent", st)
    if not m:
        print(f"    {meeting} 声明里没解析出目标区间")
        return None
    rate = decimal.Decimal(str(_frac(m.group(2))))

    # 生效日以实施说明为准（原文写明「effective September 17, 2026」）
    eff = effective_date(meeting)
    try:
        note = _flatten(_get(base + f"monetary{stamp}a1.htm", UA_CALENDAR))
        m2 = re.search(r"effective\s+([A-Z][a-z]+ \d{1,2}, \d{4})", note)
        if m2:
            eff = datetime.datetime.strptime(m2.group(1), "%B %d, %Y").date()
    except Exception:
        pass                              # 取不到就用推定的生效日，不阻断

    change = rate - before
    kind = "hike" if change > 0 else ("cut" if change < 0 else "hold")
    print(f"    {meeting} 用官方声明兜底：目标区间上限 {rate}（{kind}）")
    return eff, rate, change, kind


def _flatten(raw_html):
    t = re.sub(r"<[^>]+>", " ", raw_html)
    t = html_mod.unescape(t)
    return re.sub(r"\s+", " ", t)


def _value_at_or_after(series, d):
    for k in sorted(series):
        if k >= d:
            return series[k]
    return None


def ensure_table(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS fed_rate_decisions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            decision_date DATE NOT NULL UNIQUE,
            rate DECIMAL(6,2) NOT NULL,
            rate_change DECIMAL(6,2),
            decision_type ENUM('hike','cut','hold') NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            KEY idx_date (decision_date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)


def main():
    ap = argparse.ArgumentParser(description="美联储利率数据入库")
    ap.add_argument("command", nargs="?", default="update",
                    choices=["init", "update"],
                    help="init | update（两者行为相同，都是增量补齐）")
    ap.add_argument("--verify", action="store_true",
                    help="只核对库里已有行与 FRED 是否一致，不写库")
    args = ap.parse_args()

    today = datetime.date.today()
    series = fetch_fred_series()
    cps = change_points(series)
    meetings = fetch_fomc_meetings()
    print(f"  FRED 序列 {len(series)} 天（{min(series)} ~ {max(series)}），"
          f"变动点 {len(cps)} 个（{cps[0][0]} ~ {cps[-1][0]}）")
    print(f"  FOMC 日历 {len(meetings)} 次会议（{meetings[0]} ~ {meetings[-1]}）")

    db = config.get_database_config()
    conn = mysql.connector.connect(
        host=db.get("host"), port=int(db.get("port", 3306)),
        user=db.get("user"), password=db.get("password", ""),
        database=db.get("database"))
    try:
        cur = conn.cursor()
        ensure_table(cur)
        cur.execute("SELECT decision_date, rate FROM fed_rate_decisions")
        existing = {r[0]: decimal.Decimal(r[1]) for r in cur.fetchall()}

        # 解析所有会议
        resolved = []
        for m in meetings:
            got = resolve(m, series, today)
            if got:
                resolved.append((m, *got))
        print(f"  可解析的已开会议 {len(resolved)} 次")

        # 已经开过、却两条路都解析不出来的会议必须报出来，不能静默跳过 ——
        # 漏掉一次真实调息，下游的宏观判断就会整个反过来。
        # 正常情况下这里应该是空的：FRED 没有的，官方声明能兜住。
        done = {r[0] for r in resolved}
        stuck = [m for m in meetings
                 if m not in done and m < today
                 and (today - m).days <= 30]
        if stuck:
            print(f"  ⚠ 以下会议已开过但 FRED 和官方文档都没解析出来：{stuck}")
            print("     → 去查 https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
                  " 对应的声明，确认是页面结构变了还是真的没有决议")

        if args.verify:
            bad = []
            for m, eff, rate, change, kind in resolved:
                if eff in existing and existing[eff] != rate:
                    bad.append(f"    {eff}: 库里 {existing[eff]} ≠ FRED {rate}")

            # 「决议日 + 生效日」各存一遍 —— 同一个事件被记两次，
            # 累计加息/降息幅度会虚高。实测踩过 3 次（2015-12、2016-12、2020-03）。
            dups = []
            cur.execute("""SELECT decision_date, rate, rate_change, decision_type
                           FROM fed_rate_decisions ORDER BY decision_date""")
            allrows = cur.fetchall()
            for a, b in zip(allrows, allrows[1:]):
                if a[1] == b[1] and (b[0] - a[0]).days <= 3:
                    dups.append(f"    {a[0]} 与 {b[0]} 同为 {a[1]}"
                                f"（{a[3]}），同一次事件被记了两遍")
            # 反向：库里有、但 FRED 的变动点里找不到（可能是已下线的旧数据）
            fred_changes = set()
            ks = sorted(series)
            for a, b in zip(ks, ks[1:]):
                if series[a] != series[b]:
                    fred_changes.add(b)
            orphans = [d for d in fred_changes
                       if d not in existing and d >= datetime.date(2015, 1, 1)]
            print(f"\n  库里与 FRED 不一致的行: {len(bad)}")
            print("\n".join(bad) if bad else "    无")
            print(f"  疑似重复（决议日+生效日各存一遍）: {len(dups)}")
            print("\n".join(dups) if dups else "    无")
            print(f"  FRED 有变动、库里没有: {len(orphans)}")
            for d in orphans:
                print(f"    {d}  → {series[d]}")
            return 0 if not bad and not orphans and not dups else 1

        # ── 合并两个来源 ──────────────────────────────────────────────
        # ① FRED 变动点：1982 年以来的每次加息/降息（表被清空时靠它重建）
        # ② 日历会议  ：2021 年以来的全部会议，包括没动利率的那些
        # 两者在「有变动的会议」上重合，用日期去重（表上也有 UNIQUE 约束兜底）。
        by_date = {d: (rate, ch, kind) for d, rate, ch, kind in cps}
        for m, eff, rate, ch, kind in resolved:
            by_date.setdefault(eff, (rate, ch, kind))
        print(f"  合并后共 {len(by_date)} 个决议日"
              f"（FRED 变动点 {len(cps)} + 日历会议补齐）")

        # 判断某个变动点库里是否已有 —— **按利率比对，不按日期精确匹配**。
        #
        # 日期口径根本不统一，这是实测出来的：FRED 早期序列按决议日、库里的行
        # 按生效日（差一天），而危机期间的紧急降息（2008-10-08 那次）是当天生效、
        # 没有 +1。任何「统一平移 N 天」的规则都会在某个时期出错，把同一件事
        # 当成新的插进去 —— 实测凭空多出 150 行，或制造出 2008 年那两行重复。
        #
        # 利率变了才是「新事件」，所以按利率认；±5 天窗口用来排除同一利率水平
        # 在不同周期重复出现的情况（如 1.75% 在 2008 和 2019 都到过）。
        # 利率用容差比较，不用严格相等：1980 年代美联储按 1/8 点调整
        # （9.4375、8.375 这种），而 rate 列是 DECIMAL(6,2)，入库时被截断成
        # 9.43 / 8.37。严格相等会把它们当成新事件重复插入。
        def have(eff, rate):
            return any(abs((d - eff).days) <= 5 and abs(r - rate) < decimal.Decimal("0.011")
                       for d, r in existing.items())

        new_rows = [(d, *by_date[d]) for d in sorted(by_date)
                    if d not in existing and not have(d, by_date[d][0])]

        # 表被清空/重建过时大声说出来 —— 上面那次静默事故里，脚本照常报
        # 「新增 44 行」，没人知道 260 行历史没了。
        missing_old = [d for d in by_date if d not in existing and d < min(existing or by_date)]
        if len(new_rows) > 20:
            print(f"  ⚠ 将补齐 {len(new_rows)} 行 —— 数量偏大，表可能被清空/截断过")
            if missing_old:
                print(f"     其中 {len(missing_old)} 行早于库里现有最早日期"
                      f"（{min(existing)}），即历史缺口")
        for eff, rate, change, kind in new_rows:
            cur.execute("""
                INSERT INTO fed_rate_decisions
                    (decision_date, rate, rate_change, decision_type)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE rate=VALUES(rate)
            """, (eff, rate, change if change != 0 else None, kind))
        conn.commit()
        print(f"\n  新增 {len(new_rows)} 行")
        for eff, rate, change, kind in new_rows:
            print(f"    {eff}  利率 {rate}  {kind}"
                  f"{'  ' + str(change) if change else ''}")
        cur.execute("SELECT COUNT(*), MAX(decision_date) FROM fed_rate_decisions")
        n, latest = cur.fetchone()
        print(f"  表内共 {n} 行，最新 {latest}")
        if latest and (today - latest).days > 120:
            print(f"  ⚠ 最新一条距今 {(today - latest).days} 天 —— 检查日历解析是否失效")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
