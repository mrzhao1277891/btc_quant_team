#!/usr/bin/env python3
"""
初始化交易日志相关表

创建两张表：
- trade_journal: 交易订单（含下单理由、盈亏、复盘、纪律检查）
- investment_framework: 投资框架与纪律（单行配置）
"""

import mysql.connector
import argparse


TRADE_JOURNAL_SQL = """
CREATE TABLE IF NOT EXISTS trade_journal (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL DEFAULT 'SOLUSDT',
    direction VARCHAR(10) NOT NULL,           -- long / short
    entry_price DECIMAL(20,8) NOT NULL,       -- 开仓价
    position_value DECIMAL(20,8) NOT NULL,    -- 仓位价值(USDT)
    leverage DECIMAL(10,2) NOT NULL DEFAULT 1, -- 杠杆倍数
    stop_loss DECIMAL(20,8) NULL,             -- 止损价
    take_profit DECIMAL(20,8) NULL,           -- 止盈价
    reason TEXT NOT NULL,                     -- 下单理由
    discipline_check TEXT NULL,               -- 纪律检查(JSON)
    status VARCHAR(10) NOT NULL DEFAULT 'open', -- open / closed
    exit_price DECIMAL(20,8) NULL,            -- 平仓价
    review TEXT NULL,                         -- 复盘
    pnl DECIMAL(20,8) NULL,                   -- 平仓盈亏金额
    pnl_pct DECIMAL(10,4) NULL,               -- 平仓盈亏百分比(对本金)
    entry_time DATETIME NOT NULL,
    exit_time DATETIME NULL,
    create_time DATETIME NOT NULL,
    update_time DATETIME NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

INVESTMENT_FRAMEWORK_SQL = """
CREATE TABLE IF NOT EXISTS investment_framework (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL DEFAULT 'SOLUSDT',
    framework TEXT NULL,        -- 投资框架
    discipline TEXT NULL,       -- 投资纪律
    update_time DATETIME NOT NULL,
    UNIQUE KEY uniq_symbol (symbol)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""


def main():
    parser = argparse.ArgumentParser(description='初始化交易日志表')
    parser.add_argument('--host', default='localhost')
    parser.add_argument('--port', type=int, default=3306)
    parser.add_argument('--user', default='root')
    parser.add_argument('--password', default='')
    parser.add_argument('--database', default='btc_assistant')
    args = parser.parse_args()

    conn = mysql.connector.connect(
        host=args.host, port=args.port, user=args.user,
        password=args.password, database=args.database, charset='utf8mb4'
    )
    cursor = conn.cursor()

    print("创建 trade_journal 表...")
    cursor.execute(TRADE_JOURNAL_SQL)
    print("✅ trade_journal 表已创建")

    print("创建 investment_framework 表...")
    cursor.execute(INVESTMENT_FRAMEWORK_SQL)
    print("✅ investment_framework 表已创建")

    conn.commit()
    cursor.close()
    conn.close()
    print("\n🎉 完成")


if __name__ == "__main__":
    main()
