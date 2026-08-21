"""
BTC 恐慌贪婪指数入库脚本 (MySQL)。

数据源: https://api.alternative.me/fng/ (免费, 无需 key)
写入表: btc_fng (stat_date, fng_value, classification)

两种模式:
    init    全量初始化 —— 拉取全部历史 (回溯到 2018), UPSERT 所有行 (幂等, 可重复执行)。
    update  增量更新   —— 只拉最近若干天, UPSERT (覆盖新增日 + 当日盘中修订)。

用法:
    python3 scripts/fng_ingest.py init
    python3 scripts/fng_ingest.py update
    python3 scripts/fng_ingest.py update --days 60      # 增量回拉天数(默认30)
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

    返回按日期升序的列表: [(stat_date(date), value(int), classification(str))]
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


def upsert(conn, rows) -> int:
    """批量 UPSERT。值不变的行不会触发更新。返回受影响行数。"""
    if not rows:
        return 0
    sql = f"""
        INSERT INTO {TABLE} (stat_date, fng_value, classification, source)
        VALUES (%s, %s, %s, 'alternative.me')
        ON DUPLICATE KEY UPDATE
            fng_value      = VALUES(fng_value),
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


def run_init(dry_run: bool = False):
    print("[init] 拉取全部历史 ...")
    rows = fetch_fng(limit=0)
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


def run_update(days: int = 30, dry_run: bool = False):
    print(f"[update] 拉取最近 {days} 天 ...")
    rows = fetch_fng(limit=days)

    conn = get_connection()
    try:
        db_max = get_max_date(conn)
        if db_max is None:
            print("[update] 表为空, 建议先执行 init 做全量初始化 (本次仅写入最近窗口)")
        else:
            print(f"[update] 库内最新日期: {db_max}")
            new_days = [r for r in rows if r[0] > db_max]
            print(f"[update] 窗口内新增 {len(new_days)} 天, 另回写最近 {len(rows)-len(new_days)} 天(应对修订)")

        if dry_run:
            print(f"[update][dry-run] 将 UPSERT {len(rows)} 行, 最近 5 行:")
            for r in rows[-5:]:
                print("   ", r)
            return

        affected = upsert(conn, rows)
        print(f"[update] 完成: 提交 {len(rows)} 行, 受影响(新增+变更) {affected}")
    finally:
        conn.close()


def main(argv=None):
    ap = argparse.ArgumentParser(description="BTC 恐慌贪婪指数入库 (MySQL)")
    ap.add_argument("mode", choices=["init", "update"], help="init=全量初始化, update=增量更新")
    ap.add_argument("--days", type=int, default=30, help="update 模式回拉天数 (默认 30)")
    ap.add_argument("--dry-run", action="store_true", help="只打印将写入的数据, 不落库")
    args = ap.parse_args(argv)

    if args.mode == "init":
        run_init(dry_run=args.dry_run)
    else:
        run_update(days=args.days, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
