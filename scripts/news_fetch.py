#!/usr/bin/env python3
"""每日加密货币要闻抓取：RSS → 去重聚类 → LLM 排序+翻译 → web/data/news.json

用法:
    python3 scripts/news_fetch.py init              # 抓取并生成 JSON
    python3 scripts/news_fetch.py update            # 同上（保留以对齐 fng_ingest.py 的接口）
    python3 scripts/news_fetch.py init --dry-run    # 只抓取解析，不调 LLM、不写文件
    python3 scripts/news_fetch.py init --no-llm     # 跳过 LLM，直接用规则打分

LLM 配置（按优先级）:
    1. config/secrets/llm.yaml    { base_url, model, api_key }
    2. 环境变量 NEWS_LLM_BASE_URL / NEWS_LLM_MODEL / NEWS_LLM_KEY
    3. 回退到 ANTHROPIC_BASE_URL / ANTHROPIC_AUTH_TOKEN
       ⚠ 第 3 条是 Claude Code 的会话级临时凭证，仅供本机调试，正式使用请配 1 或 2

⚠ 不要写不带参数的 anthropic.Anthropic()。本机 ANTHROPIC_BASE_URL 指向
  https://api.deepseek.com/anthropic，裸 client 会把请求静默发到那里；
  必须显式传 base_url，否则传 claude-* 的模型名会直接失败。

LLM 挂了不会导致没新闻：自动回退到纯规则打分，JSON 里 engine 字段会标成 "rules"。
"""
import argparse
import html as html_mod
import json
import math
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
import xml.etree.ElementTree as ET

try:
    import requests
except ImportError:
    sys.exit("需要 requests: pip install requests")

try:
    import yaml
except ImportError:
    yaml = None

REPO = Path(__file__).resolve().parents[1]
OUT_PATH = REPO / "web" / "data" / "news.json"
CONF_PATH = REPO / "config" / "secrets" / "llm.yaml"

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/122.0 Safari/537.36")

WINDOW_HOURS = 36   # 只看最近这么久的条目
PREFILTER = 40      # 规则先筛出这么多簇交给 LLM（控制 token 用量）
TOP_N = 5

# (名称, RSS 地址, 可信度档位)
SOURCES = [
    ("Cointelegraph", "https://cointelegraph.com/rss",        1),
    ("The Block",     "https://www.theblock.co/rss.xml",      1),
    ("Decrypt",       "https://decrypt.co/feed",              1),
    ("The Defiant",   "https://thedefiant.io/feed",           2),
    ("CryptoPotato",  "https://cryptopotato.com/feed/",       2),
    ("BeInCrypto",    "https://beincrypto.com/feed/",         2),
    ("AMBCrypto",     "https://ambcrypto.com/feed/",          3),
    ("CoinGape",      "https://coingape.com/feed/",           3),
    ("U.Today",       "https://u.today/rss",                  3),
]
TIER_WEIGHT = {1: 1.0, 2: 0.7, 3: 0.4}

# 命中即加分的题材。权重是经验值，不是精确科学 —— LLM 在位时这些只用来做预筛。
KEYWORDS = [
    (re.compile(r"\b(etf|sec|cftc|federal reserve|\bfed\b|rate cut|rate hike|"
                r"regulation|regulator|lawsuit|approval|ban)\b", re.I), 2.0),
    (re.compile(r"\b(hack|hacked|exploit|stolen|breach|sanction|bankrupt|"
                r"insolven\w*|fraud|seized)\b", re.I), 2.0),
    (re.compile(r"\b(blackrock|microstrategy|strategy|treasury|whale|"
                r"liquidation|halving|ipo|listing|delist\w*)\b", re.I), 1.5),
    (re.compile(r"\b(bitcoin|btc|ethereum|ether|eth|solana|sol)\b", re.I), 0.8),
]

STOP = set("""a an the of to in on for and or with at by from as is are was were be
been it its this that his her their our your my we you they he she will would can
could should may might must not no nor but if then than so such about into over
after before new says say said amid ahead""".split())

# 时间词和新闻套话 —— 这些不承载「是哪件事」的信息，但 idf 很高，
# 会把不同事件拉到一起。实测：「Zoomex 月报」「Gate 月报」因为共享
# August/2026/report 被判成同一件事；「BTC 金叉」和「NEAR 金叉」也是。
STOP |= set("""january february march april may june july august september october
november december monday tuesday wednesday thursday friday saturday sunday
report reports monthly weekly daily update news latest today week month year
million billion percent price prices market markets crypto cryptocurrency
token tokens network launch launches announces announced reveals revealed
first top best next last here what why how when who""".split())

# 行情套话。刻意**只加这一小撮** —— 之前一次性加了几十个（rally/cools/
# slips/major/move…），把短标题削到只剩 {bitcoin}，而重合系数按较小一方
# 归一化，一个「处处都是子集」的单词集合直接拿满分，Blockstream 簇从 7 条
# 炸到 21 条，把「BTC 2030 年到 40 万」这类不相干新闻全吸了进去。
# 教训：删词要克制，重合系数对过小的集合极不稳定。
STOP |= set("golden death coming".split())

ATOM = "{http://www.w3.org/2005/Atom}"


# ----------------------------------------------------------------- 抓取 / 解析

HEADERS = {
    "User-Agent": UA,
    "Accept": "application/rss+xml, application/atom+xml, application/xml, "
              "text/xml, */*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
}


def fetch(url, attempts=3):
    """带退避重试。

    实测两个源会拦：The Block 间歇性 409/403（抓取风控，只带裸 UA 几乎必挂），
    CryptoPotato 连续请求会 429。补全 Accept 头 + 退避重试基本能过。
    正常每天跑一次不会触发限流，这里主要是防连续调试时的偶发失败。
    """
    last = None
    for n in range(attempts):
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            if r.status_code in (403, 409, 429) and n < attempts - 1:
                time.sleep(4.0 * (n + 1))       # 429 需要更长的退避
                continue
            r.raise_for_status()
            return r.content
        except requests.RequestException as e:
            last = e
            if n < attempts - 1:
                time.sleep(4.0 * (n + 1))
    raise last


def _txt(elem, *tags):
    """按顺序取第一个非空子标签的文本。"""
    for t in tags:
        node = elem.find(t)
        if node is not None:
            if node.text and node.text.strip():
                return node.text.strip()
            href = node.get("href")
            if href:
                return href.strip()
    return ""


def _clean(text):
    """去标签、解实体、压空白。"""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = html_mod.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def parse_date(s):
    if not s:
        return None
    s = s.strip()
    try:                                  # RFC 822 —— RSS 的 pubDate
        dt = parsedate_to_datetime(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        pass
    try:                                  # ISO 8601 —— Atom 的 updated/published
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def parse_feed(source, raw, tier):
    """同时吃 RSS 2.0 和 Atom。返回归一化后的条目列表。"""
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as e:
        print(f"  [{source}] XML 解析失败: {e}")
        return []

    out = []
    for it in root.iter("item"):                                    # RSS 2.0
        out.append({
            "title": _clean(_txt(it, "title")),
            "url": (_txt(it, "link") or _txt(it, "guid")).strip(),
            "summary": _clean(_txt(it, "description"))[:400],
            "published": parse_date(_txt(it, "pubDate", "dc:date")),
        })
    if not out:                                                     # Atom
        for it in root.iter(ATOM + "entry"):
            link = ""
            for ln in it.findall(ATOM + "link"):
                if ln.get("rel") in (None, "alternate"):
                    link = (ln.get("href") or "").strip()
                    break
            out.append({
                "title": _clean(_txt(it, ATOM + "title")),
                "url": link,
                "summary": _clean(_txt(it, ATOM + "summary", ATOM + "content"))[:400],
                "published": parse_date(_txt(it, ATOM + "published", ATOM + "updated")),
            })

    items = []
    for o in out:
        if not o["title"] or not o["url"]:
            continue
        items.append({
            "title": o["title"],
            "url": o["url"],
            "summary": o["summary"],
            "published": o["published"].isoformat() if o["published"] else None,
            "_ts": o["published"].timestamp() if o["published"] else 0.0,
            "source": source,
            "tier": tier,
        })
    return items


# 行情汇总 / 日报 / 纯技术分析。对「今天最重要的 5 件事」是噪声：
# 它们不含具体事件，却因为发布时间新而容易挤进候选，甚至成为簇代表。
NOISE_TITLE = re.compile(
    r"here'?s what happened|morning minute|daily digest|weekly recap|"
    r"price (prediction|forecast|analysis|update)|technical analysis|"
    r"what to expect|things to know|markets? (today|recap)",
    re.I)


def collect(window_hours):
    print(f"[fetch] {len(SOURCES)} 个源, 窗口 {window_hours}h")
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=window_hours)).timestamp()
    seen_url, items, per_source = set(), [], {}

    for name, url, tier in SOURCES:
        try:
            got = parse_feed(name, fetch(url), tier)
        except Exception as e:
            print(f"  [{name}] 抓取失败: {type(e).__name__}: {e}")
            per_source[name] = 0
            continue
        fresh = [i for i in got
                 if (i["_ts"] == 0.0 or i["_ts"] >= cutoff)
                 and not NOISE_TITLE.search(i["title"])]
        for i in fresh:
            key = i["url"].split("?")[0].rstrip("/")
            if key in seen_url:
                continue
            seen_url.add(key)
            items.append(i)
        per_source[name] = len(fresh)
        print(f"  [{name}] {len(got)} 条 → 窗口内 {len(fresh)} 条")

    print(f"[fetch] 合计 {len(items)} 条")
    return items, per_source


# ----------------------------------------------------------------- 去重聚类

def tokens(title):
    """只保留以字母开头的词。

    纯数字/年份（2026、600）不承载「是哪件事」的信息，但在小语料里 idf 极高，
    会把不相关的新闻拉成同一簇 —— 所以直接从分词阶段就排除。
    """
    words = re.findall(r"[a-z][a-z0-9]*", title.lower())
    return {w for w in words if w not in STOP and len(w) > 2}


def build_idf(items):
    """词的逆文档频率。'blockstream' 比 'bitcoin' 信息量大得多，
    不加权的话两家报道同一事件的标题会被判成不相似（实测相似度只有 0.33）。"""
    df = {}
    for it in items:
        for w in tokens(it["title"]):
            df[w] = df.get(w, 0) + 1
    n = max(1, len(items))
    return {w: math.log(n / c) for w, c in df.items()}


def similarity(a, b, idf):
    """IDF 加权重合系数（overlap coefficient）。

    返回 (相似度, 共享词里的最大 idf)。

    ⚠ 这里刻意**不用 Jaccard**。Jaccard 拿并集做分母，而标题的用词差异极大
      —— 同一件事，8 家会写成 rejects / refuses / won't pay / delusional…
      每个独有词都带最高 idf，把分母撑爆。实测 Blockstream 那条新闻的
      两两 Jaccard 只有 0.17~0.43，全部低于阈值，8 家报道被拆成 3 个簇。

      改成分母取**较小一方**的信息量，问的是「短的那条标题有多少信息
      被对方覆盖了」。同一事件措辞不同 → 高分；不相关事件 → 低分。
    """
    if not a or not b:
        return 0.0, 0.0
    shared = a & b
    # 只共享一个词不足以判定是同一件事。否则「Bitcoin A」和「Bitcoin B」
    # 这种只有 bitcoin 重叠的标题会互相合并。
    if len(shared) < 2:
        return 0.0, 0.0
    inter = sum(idf.get(w, 0.0) for w in shared)
    smaller = min(sum(idf.get(w, 0.0) for w in a), sum(idf.get(w, 0.0) for w in b))
    return (inter / smaller if smaller else 0.0), max(idf.get(w, 0.0) for w in shared)


def cluster(items, idf, sim_bar=0.45, jac_bar=0.85, rare_idf=2.5):
    """近似标题聚类。跨源重复本身就是重要性信号，顺带完成去重。

    合并条件（满足其一）：
      · 有共享罕见词(实体名) 且 加权相似度 >= sim_bar
      · 加权相似度 >= jac_bar（措辞几乎一致的转载）

    关键：和簇内**每个成员**比、取最高分，而不是只跟首个成员比。
    同一事件被 8 家报道时措辞各不相同，只跟代表比会断链 —— 实测
    Blockstream 那条 8 家报道的新闻就是因此没合上。
    """
    clusters = []
    for it in sorted(items, key=lambda x: -x["_ts"]):
        tk = tokens(it["title"])
        best, best_key = None, None
        for c in clusters:
            sim, rare = 0.0, 0.0
            for member in c["_members"]:
                s, r = similarity(tk, member, idf)
                if s > sim or (s == sim and r > rare):
                    sim, rare = s, r
            key = (sim + (0.25 if rare >= rare_idf else 0.0), sim, rare)
            if best_key is None or key > best_key:
                best, best_key = c, key

        merge = False
        if best is not None:
            sim, rare = best_key[1], best_key[2]
            merge = (rare >= rare_idf and sim >= sim_bar) or (sim >= jac_bar)

        if merge:
            best["items"].append(it)
            best["sources"].add(it["source"])
            best["best_tier"] = min(best["best_tier"], it["tier"])
            best["_members"].append(tk)
        else:
            clusters.append({
                "items": [it],
                "sources": {it["source"]},
                "best_tier": it["tier"],
                "_members": [tk],
                "_ts": it["_ts"],
            })
    return clusters


def rule_score(c, now_ts):
    """规则打分：跨源重复 × 3.0 + 来源权重 + 关键词权重 + 时间衰减(6h 半衰期)。"""
    head = c["items"][0]
    score = (len(c["sources"]) - 1) * 3.0
    score += TIER_WEIGHT.get(c["best_tier"], 0.3)
    for pat, w in KEYWORDS:
        if pat.search(head["title"]):
            score += w
    age_h = max(0.0, (now_ts - c["_ts"]) / 3600.0)
    score += 1.5 * (0.5 ** (age_h / 6.0))
    return round(score, 3)


def to_public(c, now_ts, rank=None, zh=None):
    head = c["items"][0]
    others = sorted(c["sources"] - {head["source"]})
    return {
        "rank": rank,
        "title_zh": (zh or {}).get("title_zh") or head["title"],
        "title_en": head["title"],
        "summary_zh": (zh or {}).get("summary_zh") or head["summary"][:200],
        "why": (zh or {}).get("why") or "",
        "source": head["source"],
        "published": head["published"],
        "url": head["url"],
        "also_covered_by": others,
        "score": rule_score(c, now_ts),
    }


# ----------------------------------------------------------------- LLM

def load_llm_config():
    """返回 (base_url, model, api_key, source_desc)；取不到就返回 None。"""
    if CONF_PATH.exists() and yaml is not None:
        try:
            cfg = yaml.safe_load(CONF_PATH.read_text(encoding="utf-8")) or {}
            if cfg.get("api_key"):
                return (cfg.get("base_url", "").rstrip("/") or None,
                        cfg.get("model") or "deepseek-chat",
                        cfg["api_key"], f"config/secrets/llm.yaml")
        except Exception as e:
            print(f"[llm] 读 {CONF_PATH} 失败: {e}")

    if os.environ.get("NEWS_LLM_KEY"):
        return (os.environ.get("NEWS_LLM_BASE_URL", "").rstrip("/") or None,
                os.environ.get("NEWS_LLM_MODEL", "deepseek-chat"),
                os.environ["NEWS_LLM_KEY"], "环境变量 NEWS_LLM_*")

    if os.environ.get("ANTHROPIC_AUTH_TOKEN"):
        # ⚠ 刻意**不读 ANTHROPIC_MODEL**：那是 Claude Code 自己的别名
        # （本机是 deepseek-flash[1m]，一个推理模型）。实测拿它跑完整
        # prompt 会 2000 tokens 全花在思考上、正文返回空字符串，
        # 于是 JSON 解析失败。这里一律用 NEWS_LLM_MODEL 或 deepseek-chat。
        return (os.environ.get("ANTHROPIC_BASE_URL", "").rstrip("/") or None,
                os.environ.get("NEWS_LLM_MODEL") or "deepseek-chat",
                os.environ["ANTHROPIC_AUTH_TOKEN"],
                "⚠ ANTHROPIC_AUTH_TOKEN (会话级临时凭证，仅供调试)")

    return None


PROMPT = """你是加密市场编辑。下面是最近 {hours} 小时内、去重聚类后的加密新闻候选，按规则初筛过。

请挑出对**交易者**最重要的 {n} 条 —— 判断标准是：会不会影响仓位、资金流、监管格局或市场情绪。
不要选：价格行情播报、单币种涨跌快讯、推广软文、纯科普、迷因币异动。

候选（编号 | 标题 | 来源数 | 来源）：
{listing}

只输出 JSON，不要任何别的文字、不要 markdown 围栏：
{{"picks":[{{"i":编号,"title_zh":"中文标题","summary_zh":"一句话中文摘要(40字内)","why":"为什么重要(20字内)"}}]}}

要求：恰好 {n} 条；按重要性从高到低排；title_zh 是自然的财经中文，不要逐字硬翻。"""


def _extract_json(text):
    """兼容端点未必支持结构化输出，所以防御性提取。"""
    text = re.sub(r"```(?:json)?", "", text).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("响应里找不到 JSON")
    return json.loads(text[start:end + 1])


def llm_rank(clusters, now_ts, cfg):
    """返回 {cluster_index: {...中文...}}；失败抛异常，由调用方回退。"""
    import anthropic

    base_url, model, api_key, desc = cfg
    print(f"[llm] {desc} | model={model} base_url={base_url or '(SDK 默认)'}")

    # 显式传 base_url —— 绝不能让 SDK 去读环境变量推断
    client = anthropic.Anthropic(api_key=api_key, base_url=base_url) if base_url \
        else anthropic.Anthropic(api_key=api_key)

    pool = clusters[:PREFILTER]
    listing = "\n".join(
        f'{i} | {c["items"][0]["title"]} | {len(c["sources"])} 家 | '
        f'{", ".join(sorted(c["sources"]))}'
        for i, c in enumerate(pool)
    )
    msg = client.messages.create(
        model=model,
        max_tokens=4000,        # 部分模型会先思考；留够余量，否则正文被挤空
        messages=[{"role": "user", "content": PROMPT.format(
            hours=WINDOW_HOURS, n=TOP_N, listing=listing)}],
    )
    text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    if not text.strip():
        # 最常见的成因：推理模型把 max_tokens 全用在思考上，正文为空
        raise ValueError(
            f"响应正文为空 (stop_reason={msg.stop_reason}, "
            f"output_tokens={msg.usage.output_tokens}) —— "
            f"model={model} 可能是推理模型，把 token 预算耗在思考上了")
    data = _extract_json(text)

    picks, out = data.get("picks", []), {}
    for p in picks:
        try:
            i = int(p["i"])
        except (KeyError, TypeError, ValueError):
            continue
        if 0 <= i < len(pool):
            out[i] = {
                "title_zh": str(p.get("title_zh", "")).strip(),
                "summary_zh": str(p.get("summary_zh", "")).strip(),
                "why": str(p.get("why", "")).strip(),
            }
    if not out:
        raise ValueError("LLM 没返回可用的 picks")
    return out


# ----------------------------------------------------------------- 主流程

def build(window_hours, use_llm):
    now = datetime.now(timezone.utc)
    now_ts = now.timestamp()

    items, per_source = collect(window_hours)
    if not items:
        raise SystemExit("[!] 一条都没抓到 —— 检查网络或源地址")

    clusters = cluster(items, build_idf(items))
    merged = sum(1 for c in clusters if len(c["items"]) > 1)
    print(f"[cluster] {len(items)} 条 → {len(clusters)} 个独立事件 "
          f"(其中 {merged} 个跨源合并)")

    for c in clusters:
        c["score"] = rule_score(c, now_ts)
    clusters.sort(key=lambda c: -c["score"])

    picked, engine, note = clusters[:TOP_N], "rules", ""
    if use_llm:
        cfg = load_llm_config()
        if not cfg:
            note = "未找到 LLM 凭证，已用规则打分"
            print(f"[llm] {note}")
        else:
            try:
                for i, zh in llm_rank(clusters, now_ts, cfg).items():
                    clusters[i]["_zh"] = zh
                ranked = sorted(
                    (c for c in clusters if "_zh" in c),
                    key=lambda c: -c["score"])
                if ranked:
                    picked, engine = ranked[:TOP_N], "llm"
            except Exception as e:
                note = f"LLM 调用失败({type(e).__name__}: {e})，已回退规则打分"
                print(f"[llm] {note}")

    top = [to_public(c, now_ts, rank=n + 1, zh=c.get("_zh"))
           for n, c in enumerate(picked)]

    return {
        "generated_at": now.isoformat(),
        "window_hours": window_hours,
        "engine": engine,
        "note": note,
        "fetched": len(items),
        "clusters": len(clusters),
        "sources": [{"name": n, "count": c} for n, c in per_source.items()],
        "top": top,
        "all": [{"title": i["title"], "url": i["url"], "source": i["source"],
                 "published": i["published"]} for i in
                sorted(items, key=lambda x: -x["_ts"])[:400]],
    }


def main():
    ap = argparse.ArgumentParser(description="每日加密货币要闻抓取")
    ap.add_argument("mode", choices=["init", "update"], nargs="?", default="init")
    ap.add_argument("--dry-run", action="store_true", help="只抓取解析，不调 LLM、不写文件")
    ap.add_argument("--no-llm", action="store_true", help="跳过 LLM，直接用规则打分")
    ap.add_argument("--window", type=int, default=WINDOW_HOURS, help="时间窗小时数")
    args = ap.parse_args()

    payload = build(args.window, use_llm=not (args.no_llm or args.dry_run))

    if args.dry_run:
        print("\n[dry-run] 不写文件。Top 5（规则打分）：")
        for t in payload["top"]:
            print(f'  {t["rank"]}. [{t["score"]:>5}] {t["source"]:<14} {t["title_en"][:70]}')
        print(f'\n[dry-run] 引擎={payload["engine"]} 来源数={len(payload["sources"])}')
        return

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    print(f'\n[write] {OUT_PATH}  ({OUT_PATH.stat().st_size} bytes)')
    print(f'[write] 引擎={payload["engine"]}  Top {len(payload["top"])} 条:')
    for t in payload["top"]:
        mark = "🀄" if payload["engine"] == "llm" else "  "
        print(f'  {t["rank"]}. {mark} {t["title_zh"][:64]}')
        if t["source"]:
            extra = f' (+{len(t["also_covered_by"])} 家)' if t["also_covered_by"] else ""
            print(f'        └ {t["source"]}{extra}')


if __name__ == "__main__":
    main()
