#!/usr/bin/env python3
"""美联储利率决策历史数据入库脚本 (数据源: AKShare macro_bank_usa_interest_rate)

用法:
    python3 scripts/fed_rate_ingest.py          # 首次入库
    python3 scripts/fed_rate_ingest.py update   # 增量更新
"""
import sys, datetime, decimal, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.backtest.config import config
import mysql.connector
import pandas as pd

def fetch_from_akshare():
    """从 AKShare 拉取美联储利率决策."""
    try:
        import akshare as ak
    except ImportError:
        import subprocess
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'akshare', '-q'])
        import akshare as ak
    df = ak.macro_bank_usa_interest_rate()
    # 转换为 (date, rate, prev_rate) 列表
    data = []
    for _, row in df.iterrows():
        try:
            d = datetime.datetime.strptime(str(row['日期']), "%Y-%m-%d").date()
            
            # 跳过今值为 NaN 的行
            current_val = row['今值']
            if pd.isna(current_val):
                print(f"跳过 {d}: 今值为 NaN")
                continue
                
            v = decimal.Decimal(str(current_val))
            
            # 处理前值（可能是 NaN）
            prev_val = row['前值']
            prev_v = None
            if pd.notna(prev_val):  # pandas 的 isnull/notnull
                try:
                    prev_v = decimal.Decimal(str(prev_val))
                except:
                    prev_v = None
                    
            data.append((d, v, prev_v))
        except Exception as e:
            print(f"解析错误 {row['日期']}: {e}")
            continue
    return data

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

def get_existing_dates(cur):
    cur.execute("SELECT decision_date FROM fed_rate_decisions")
    return set(r[0] for r in cur.fetchall())

def insert_decisions(cur, rows):
    if not rows: return 0
    inserted = 0
    for d, v, prev_v in rows:
        if prev_v is None:
            change = decimal.Decimal('0')
            dtype = 'hold'  # 第一条数据或前值缺失，默认为 hold
        else:
            change = v - prev_v
            if change > 0:
                dtype = 'hike'
            elif change < 0:
                dtype = 'cut'
            else:
                dtype = 'hold'
        cur.execute("""
            INSERT INTO fed_rate_decisions (decision_date, rate, rate_change, decision_type)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE rate=VALUES(rate), rate_change=VALUES(rate_change), decision_type=VALUES(decision_type)
        """, (d, v, change if change != 0 else None, dtype))
        inserted += 1
    return inserted

def main():
    parser = argparse.ArgumentParser(description='美联储利率数据入库')
    parser.add_argument('command', nargs='?', default='init', help='init | update')
    args = parser.parse_args()

    db = config.get_database_config()
    conn = mysql.connector.connect(
        host=db.get('host'), port=int(db.get('port', 3306)),
        user=db.get('user'), password=db.get('password', ''), database=db.get('database')
    )
    try:
        cur = conn.cursor()
        ensure_table(cur)
        rows = fetch_from_akshare()
        existing = get_existing_dates(cur) if args.command == 'update' else set()
        new_rows = [(d, v, prev_v) for d, v, prev_v in rows if d not in existing]
        n = insert_decisions(cur, new_rows)
        conn.commit()
        print(f"Inserted/updated {n} rate decisions (total {len(rows)} from AKShare).")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
