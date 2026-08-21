"""
抓取 Farside 的比特币现货 ETF 每日净流入数据，并计算 5 日移动平均。

数据源: https://farside.co.uk/bitcoin-etf-flow-all-data/
单位: 百万美元 (USD millions)。括号表示净流出(负值)，"-" 表示当日无数据。

用法:
    python3 scripts/btc_etf_flow.py            # 抓取并打印最近记录
    python3 scripts/btc_etf_flow.py --window 5 # 指定移动平均窗口(默认5)
    python3 scripts/btc_etf_flow.py --csv out.csv  # 另存 CSV 路径
"""
from __future__ import annotations

import argparse
import io
import re
import sys
from html.parser import HTMLParser

import pandas as pd
from curl_cffi import requests  # 模拟浏览器 TLS 指纹, 绕过 Cloudflare

URL = "https://farside.co.uk/bitcoin-etf-flow-all-data/"
DEFAULT_CSV = "data/btc_etf_flow.csv"


class _TableParser(HTMLParser):
    """用标准库解析 HTML 里最大的那张表格 (Farside 的数据表)。"""

    def __init__(self) -> None:
        super().__init__()
        self._in_td = False
        self._in_tr = False
        self._cur_cell: list[str] = []
        self._cur_row: list[str] = []
        self.rows: list[list[str]] = []

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self._in_tr = True
            self._cur_row = []
        elif tag in ("td", "th"):
            self._in_td = True
            self._cur_cell = []

    def handle_endtag(self, tag):
        if tag in ("td", "th"):
            self._in_td = False
            self._cur_row.append("".join(self._cur_cell).strip())
        elif tag == "tr":
            self._in_tr = False
            if self._cur_row:
                self.rows.append(self._cur_row)

    def handle_data(self, data):
        if self._in_td:
            self._cur_cell.append(data)


def _clean_number(val: str) -> float | None:
    """把单元格文本转成数字: 括号=负数, 逗号去掉, '-'/'' -> None。"""
    if val is None:
        return None
    s = val.strip().replace(",", "").replace("\xa0", "")
    if s in ("", "-", "–", "—"):
        return None
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    try:
        num = float(s)
    except ValueError:
        return None
    return -num if neg else num


def fetch_flows(url: str = URL) -> pd.DataFrame:
    """抓取页面并返回每日净流入 DataFrame(index=日期, 列=各ETF + Total)。"""
    # 用 curl_cffi 模拟 Chrome 的 TLS/HTTP2 指纹, 通过 Cloudflare 校验
    resp = requests.get(url, impersonate="chrome", timeout=25)
    resp.raise_for_status()
    if "Just a moment" in resp.text:
        raise RuntimeError("被 Cloudflare 拦截 (返回了挑战页), 请稍后重试或更换 impersonate 版本")

    parser = _TableParser()
    parser.feed(resp.text)
    rows = parser.rows
    if not rows:
        raise RuntimeError("未能从页面解析出表格数据")

    # 表头: 第一行含 Date / Total
    header = rows[0]
    try:
        date_i = header.index("Date")
    except ValueError:
        date_i = 0

    records = []
    date_re = re.compile(r"^\d{1,2}\s+\w{3}\s+\d{4}$")  # 例: 11 Jan 2024
    for row in rows[1:]:
        if len(row) <= date_i:
            continue
        date_str = row[date_i].strip()
        # 跳过底部的累计 "Total" 行以及非日期行
        if not date_re.match(date_str):
            continue
        rec = {"Date": date_str}
        for i, col in enumerate(header):
            if i == date_i or not col:
                continue
            rec[col] = _clean_number(row[i]) if i < len(row) else None
        records.append(rec)

    df = pd.DataFrame(records)
    df["Date"] = pd.to_datetime(df["Date"], format="%d %b %Y")
    df = df.sort_values("Date").set_index("Date")
    return df


def add_moving_average(df: pd.DataFrame, window: int = 5,
                       column: str = "Total") -> pd.DataFrame:
    """在指定列上增加 N 日移动平均线。"""
    if column not in df.columns:
        raise KeyError(f"数据中没有列 '{column}', 现有列: {list(df.columns)}")
    out = df.copy()
    out[f"{column}_MA{window}"] = out[column].rolling(window).mean()
    return out


def compute_mas(df: pd.DataFrame, column: str = "Total",
                windows=(5, 14, 30)) -> pd.DataFrame:
    """一次性计算多个窗口的移动平均, 返回列: ma5 / ma14 / ma30。

    移动平均按 "最近 N 个交易日"(即 N 行) 计算, 窗口不满时为 NaN。
    """
    if column not in df.columns:
        raise KeyError(f"数据中没有列 '{column}', 现有列: {list(df.columns)}")
    out = df.copy()
    for w in windows:
        out[f"ma{w}"] = out[column].rolling(w).mean()
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="BTC 现货 ETF 每日净流入 + 移动平均")
    ap.add_argument("--window", type=int, default=5, help="移动平均窗口 (默认 5)")
    ap.add_argument("--column", default="Total", help="计算移动平均的列 (默认 Total)")
    ap.add_argument("--csv", default=DEFAULT_CSV, help=f"CSV 输出路径 (默认 {DEFAULT_CSV})")
    ap.add_argument("--tail", type=int, default=15, help="打印最近多少行 (默认 15)")
    args = ap.parse_args(argv)

    print(f"抓取数据: {URL}")
    df = fetch_flows()
    print(f"共 {len(df)} 个交易日, 区间 {df.index.min().date()} ~ {df.index.max().date()}")

    df = add_moving_average(df, window=args.window, column=args.column)

    ma_col = f"{args.column}_MA{args.window}"
    show = df[[args.column, ma_col]].tail(args.tail).round(1)
    print(f"\n最近 {args.tail} 个交易日的 {args.column} 净流入与 {args.window} 日均线 (单位: 百万美元):")
    print(show.to_string())

    import os
    os.makedirs(os.path.dirname(args.csv), exist_ok=True) if os.path.dirname(args.csv) else None
    df.round(2).to_csv(args.csv)
    print(f"\n完整数据已保存: {args.csv}")


if __name__ == "__main__":
    main()
