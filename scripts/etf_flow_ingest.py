"""
BTC 现货 ETF 每日净流入入库脚本 (MySQL)。

从 Farside 抓取数据, 计算 5/14/30 交易日移动平均, 写入 btc_etf_flow 表。

两种模式:
    init    全量初始化 —— 抓全量历史, 计算均线, UPSERT 所有行 (可重复执行, 幂等)。
    update  增量更新   —— 只写新增交易日, 并回算最近若干行 (兼容 Farside 的历史数据修订)。

用法:
    python3 scripts/etf_flow_ingest.py init
    python3 scripts/etf_flow_ingest.py update
    python3 scripts/etf_flow_ingest.py update --dry-run   # 只打印将写入的行, 不落库

数据库连接复用项目配置 (config/backtest.yaml + 环境变量 DB_HOST/DB_USER/DB_PASSWORD/DB_NAME)。
单位: 百万美元 (与 Farside 原始口径一致, 负数=净流出)。
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import mysql.connector

# 让脚本能 import 同目录的抓取模块 与 项目内的配置
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from btc_etf_flow import fetch_flows, compute_mas  # noqa: E402
from backend.backtest.config import config  # noqa: E402

TABLE = "btc_etf_flow"
WINDOWS = (5, 14, 30)
# 增量模式下额外回算的尾部行数 (>= 最大窗口, 用于兜住 Farside 对近期数据的修订)
RECOMPUTE_TAIL = 35


def get_connection():
    """用项目配置创建 MySQL 连接。"""
    db = config.get_database_config()
    return mysql.connector.connect(
        host=db.get("host", "localhost"),
        port=int(db.get("port", 3306)),
        user=db.get("user", "root"),
        password=db.get("password", ""),
        database=db.get("database", "btc_assistant"),
        charset=db.get("charset", "utf8mb4"),
    )


def _num(v):
    """把 pandas 数值转成 float, NaN/None -> None (写入 SQL NULL)。"""
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(f) else round(f, 4)


def build_rows(df):
    """把 DataFrame 转成待写入的元组列表: (date, net_flow, ma5, ma14, ma30)。"""
    rows = []
    for ts, r in df.iterrows():
        rows.append((
            ts.date(),
            _num(r["Total"]),
            _num(r["ma5"]),
            _num(r["ma14"]),
            _num(r["ma30"]),
        ))
    return rows


def upsert(conn, rows) -> int:
    """批量 UPSERT。值完全相同的行不会触发更新 (updated_at 不变)。返回受影响行数。"""
    if not rows:
        return 0
    sql = f"""
        INSERT INTO {TABLE} (trade_date, net_flow, ma5, ma14, ma30, source)
        VALUES (%s, %s, %s, %s, %s, 'farside')
        ON DUPLICATE KEY UPDATE
            net_flow = VALUES(net_flow),
            ma5      = VALUES(ma5),
            ma14     = VALUES(ma14),
            ma30     = VALUES(ma30),
            source   = VALUES(source)
    """
    cur = conn.cursor()
    cur.executemany(sql, rows)
    conn.commit()
    affected = cur.rowcount
    cur.close()
    return affected


def get_max_date(conn):
    cur = conn.cursor()
    cur.execute(f"SELECT MAX(trade_date) FROM {TABLE}")
    row = cur.fetchone()
    cur.close()
    return row[0] if row else None


def fetch_and_compute():
    """抓取全量数据并计算三条均线, 返回带 ma5/ma14/ma30 的 DataFrame。"""
    df = fetch_flows()
    df = compute_mas(df, column="Total", windows=WINDOWS)
    return df


def run_init(dry_run: bool = False):
    print("[init] 抓取全量数据 ...")
    df = fetch_and_compute()
    print(f"[init] 共 {len(df)} 个交易日, 区间 {df.index.min().date()} ~ {df.index.max().date()}")
    rows = build_rows(df)

    if dry_run:
        print(f"[init][dry-run] 将 UPSERT {len(rows)} 行, 示例最近 3 行:")
        for r in rows[-3:]:
            print("   ", r)
        return

    conn = get_connection()
    try:
        affected = upsert(conn, rows)
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM {TABLE}")
        total = cur.fetchone()[0]
        cur.close()
        print(f"[init] 完成: 提交 {len(rows)} 行, 受影响 {affected}, 表内现有 {total} 行")
    finally:
        conn.close()


def run_update(dry_run: bool = False):
    print("[update] 抓取全量数据 ...")
    df = fetch_and_compute()

    conn = get_connection()
    try:
        db_max = get_max_date(conn)
        if db_max is None:
            print("[update] 表为空, 转为全量初始化")
            rows = build_rows(df)
        else:
            print(f"[update] 库内最新日期: {db_max}")
            import pandas as pd
            db_max_ts = pd.Timestamp(db_max)
            new_part = df[df.index > db_max_ts]                       # 新增交易日
            tail_part = df[df.index <= db_max_ts].tail(RECOMPUTE_TAIL)  # 回算尾部(应对修订)
            to_write = pd.concat([tail_part, new_part])
            to_write = to_write[~to_write.index.duplicated(keep="last")]
            rows = build_rows(to_write)
            print(f"[update] 新增 {len(new_part)} 行, 回算尾部 {len(tail_part)} 行, 合计写入 {len(rows)} 行")

        if dry_run:
            print(f"[update][dry-run] 将 UPSERT {len(rows)} 行, 示例最近 5 行:")
            for r in rows[-5:]:
                print("   ", r)
            return

        affected = upsert(conn, rows)
        print(f"[update] 完成: 提交 {len(rows)} 行, 受影响(新增+变更) {affected}")
    finally:
        conn.close()


def main(argv=None):
    ap = argparse.ArgumentParser(description="BTC ETF 净流入入库 (MySQL)")
    ap.add_argument("mode", choices=["init", "update"], help="init=全量初始化, update=增量更新")
    ap.add_argument("--dry-run", action="store_true", help="只打印将写入的数据, 不落库")
    args = ap.parse_args(argv)

    if args.mode == "init":
        run_init(dry_run=args.dry_run)
    else:
        run_update(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
