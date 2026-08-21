"""
BTC 恐慌贪婪指数入库脚本 (MySQL)。

数据源: https://api.alternative.me/fng/ (免费, 无需 key)
写入表: btc_fng (stat_date, fng_value, ma5, ma14, ma30, classification)

两种模式:
    init    全量初始化 —— 拉取全部历史, 计算 5/14/30 日均线, UPSERT 所有行 (幂等)。
    update  增量更新   —— 拉全量算均线, 只写新增日 + 回算最近若干行 (应对当日修订)。

均线均在全量序列上计算, 保证窗口边界也正确; 均线按 "最近 N 天" 计算, 窗口不满为 NULL。

用法:
    python3 scripts/fng_ingest.py init
    python3 scripts/fng_ingest.py update
    python3 scripts/fng_ingest.py update --dry-run       # 只打印不落库

数据库连接复用项目配置 (config/backtest.yaml + 环境变量)。
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from backend.backtest.config import config  # noqa: E402
import mysql.connector  # noqa: E402

API_URL = "https://api.alternative.me/fng/"
TABLE = "btc_fng"
WINDOWS = (5, 14, 30)
# 增量模式额外回算的尾部行数 (>= 最大窗口, 兜住当日/近期修订)
RECOMPUTE_TAIL = 35


def get_connection():
    db = config.get_database_config()
    return mysql.connector.connect(
        host=db.get("host", "localhost"),
        port=int(db.get("port", 3306)),
        user=db.get("user", "root"),
        password=db.get("password", ""),
        database=db.get("database", "btc_assistant"),
        charset=db.get("charset", "utf8mb4"),
    )


def fetch_fng(limit: int = 0):
    """拉取恐慌贪婪指数。limit=0 表示全部历史。

    返回按日期升序: [(stat_date(date), value(int), classification(str))]
    """
    resp = requests.get(API_URL, params={"limit": limit, "format": "json"}, timeout=20)
    resp.raise_for_status()
    payload = resp.json()
    if payload.get("metadata", {}).get("error"):
        raise RuntimeError(f"API 返回错误: {payload['metadata']['error']}")

    rows = []
    for item in payload.get("data", []):
        ts = int(item["timestamp"])
        d = datetime.fromtimestamp(ts, tz=timezone.utc).date()
        rows.append((d, int(item["value"]), item["value_classification"]))
    rows.sort(key=lambda r: r[0])  # 升序
    return rows


def _rolling_mean(vals, window):
    """简单移动平均: 返回与 vals 等长列表, 前 window-1 项为 None。"""
    out = [None] * len(vals)
    s = 0.0
    for i, v in enumerate(vals):
        s += v
        if i >= window:
            s -= vals[i - window]
        if i >= window - 1:
            out[i] = round(s / window, 2)
    return out


def build_rows_with_mas(fng_rows):
    """输入 [(date, value, cls)] (升序), 输出含均线的 6 元组列表:
    (date, value, ma5, ma14, ma30, cls)
    """
    values = [r[1] for r in fng_rows]
    mas = {w: _rolling_mean(values, w) for w in WINDOWS}
    out = []
    for i, (d, v, cls) in enumerate(fng_rows):
        out.append((d, v, mas[5][i], mas[14][i], mas[30][i], cls))
    return out


def upsert(conn, rows) -> int:
    """批量 UPSERT。rows: (date, value, ma5, ma14, ma30, cls)。值不变不触发更新。"""
    if not rows:
        return 0
    sql = f"""
        INSERT INTO {TABLE} (stat_date, fng_value, ma5, ma14, ma30, classification, source)
        VALUES (%s, %s, %s, %s, %s, %s, 'alternative.me')
        ON DUPLICATE KEY UPDATE
            fng_value      = VALUES(fng_value),
            ma5            = VALUES(ma5),
            ma14           = VALUES(ma14),
            ma30           = VALUES(ma30),
            classification = VALUES(classification),
            source         = VALUES(source)
    """
    cur = conn.cursor()
    cur.executemany(sql, rows)
    conn.commit()
    affected = cur.rowcount
    cur.close()
    return affected


def get_max_date(conn):
    cur = conn.cursor()
    cur.execute(f"SELECT MAX(stat_date) FROM {TABLE}")
    row = cur.fetchone()
    cur.close()
    return row[0] if row else None


def fetch_and_compute():
    """拉全量历史并计算均线, 返回含均线的行列表 (升序)。"""
    return build_rows_with_mas(fetch_fng(limit=0))


def run_init(dry_run: bool = False):
    print("[init] 拉取全部历史 ...")
    rows = fetch_and_compute()
    print(f"[init] 共 {len(rows)} 天, 区间 {rows[0][0]} ~ {rows[-1][0]}")

    if dry_run:
        print(f"[init][dry-run] 将 UPSERT {len(rows)} 行, 最近 3 行:")
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
    print("[update] 拉取全部历史并计算均线 ...")
    rows = fetch_and_compute()

    conn = get_connection()
    try:
        db_max = get_max_date(conn)
        if db_max is None:
            print("[update] 表为空, 转为全量初始化")
            to_write = rows
        else:
            print(f"[update] 库内最新日期: {db_max}")
            new_part = [r for r in rows if r[0] > db_max]           # 新增日
            tail_part = [r for r in rows if r[0] <= db_max][-RECOMPUTE_TAIL:]  # 回算尾部
            # 合并去重(按日期), 保持升序
            seen = set()
            to_write = []
            for r in tail_part + new_part:
                if r[0] not in seen:
                    seen.add(r[0])
                    to_write.append(r)
            to_write.sort(key=lambda r: r[0])
            print(f"[update] 新增 {len(new_part)} 天, 回算尾部 {len(tail_part)} 天, 合计写入 {len(to_write)} 行")

        if dry_run:
            print(f"[update][dry-run] 将 UPSERT {len(to_write)} 行, 最近 5 行:")
            for r in to_write[-5:]:
                print("   ", r)
            return

        affected = upsert(conn, to_write)
        print(f"[update] 完成: 提交 {len(to_write)} 行, 受影响(新增+变更) {affected}")
    finally:
        conn.close()


def main(argv=None):
    ap = argparse.ArgumentParser(description="BTC 恐慌贪婪指数入库 (MySQL)")
    ap.add_argument("mode", choices=["init", "update"], help="init=全量初始化, update=增量更新")
    ap.add_argument("--dry-run", action="store_true", help="只打印将写入的数据, 不落库")
    args = ap.parse_args(argv)

    if args.mode == "init":
        run_init(dry_run=args.dry_run)
    else:
        run_update(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
