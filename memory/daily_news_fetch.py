#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from _encoding import setup_utf8; setup_utf8()
'''
Daily News Fetch Tool — 定时获取新闻简报（国际/国内/财经）
=========================================================
用法:
  from memory.daily_news_fetch import fetch_all_news, format_news_for_diary

  data = fetch_all_news()
  # data: {"国际": [(title, url, source), ...], "国内": [...], "财经": [...]}

  md = format_news_for_diary(data)  # → 日记 新闻 区块

独立运行:
  python daily_news_fetch.py           # 打印完整输出
  python daily_news_fetch.py --json    # 打印 JSON 格式

设计原则:
  - 新闻 = 时事播报（今天发生了什么）
  - 消息源 = 深度学习内容（HN 等，另见 hn_daily_fetch.py）
  - 本脚本不含科技板块，科技归 HN 消息源管
'''

import urllib.request
import xml.etree.ElementTree as ET
import json
import sys
import ssl
from datetime import date, datetime, timezone

FEEDS = {
    "国际": [
        "https://news.google.com/rss/headlines/section/topic/WORLD?hl=en-US&gl=US&ceid=US:en",
    ],
    "国内": [
        "https://news.google.com/rss?hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
    ],
    "财经": [
        "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=Federal%20Reserve%20OR%20inflation%20OR%20markets%20OR%20economy%20OR%20earnings%20when:1d&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=stocks%20OR%20bonds%20OR%20oil%20OR%20dollar%20OR%20tariffs%20when:1d&hl=en-US&gl=US&ceid=US:en",
    ],
}

PER_CATEGORY = 5
FETCH_LIMIT_PER_FEED = 20
REQUEST_TIMEOUT = 10
USER_AGENT = "Mozilla/5.0 (compatible; GenericAgent-News-fetcher/1.0)"

TECH_KEYWORDS = {
    "ai", "artificial intelligence", "openai", "chatgpt", "altman", "anthropic",
    "google i/o", "apple", "iphone", "microsoft", "nvidia", "cerebras", "softbank",
    "arm", "chip", "semiconductor", "spacex", "tesla", "rocket", "code", "software",
}

FINANCE_KEYWORDS = {
    "fed", "federal reserve", "rate", "inflation", "market", "stock", "bond", "yield",
    "oil", "dollar", "tariff", "trade", "economy", "economic", "earnings", "bank",
    "finance", "business", "gdp", "recession", "central bank", "treasury", "wall street",
}


def _norm_title(title: str) -> str:
    return " ".join(title.lower().replace("—", "-").split())


def _title_body(title: str) -> str:
    # Google News RSS title often ends with " - Source"; use body for duplicate checks.
    return _norm_title(title.rsplit(" - ", 1)[0])


def _is_tech(title: str) -> bool:
    t = _norm_title(title)
    return any(k in t for k in TECH_KEYWORDS)


def _is_finance(title: str) -> bool:
    t = _norm_title(title)
    return any(k in t for k in FINANCE_KEYWORDS)


def _fetch_rss(url: str, limit: int = FETCH_LIMIT_PER_FEED):
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT, context=ssl_ctx) as resp:
            data = resp.read()
    except Exception as e:
        print(f"[News Fetch] ERROR: {url[:60]}... -> {e}", file=sys.stderr)
        return []
    try:
        root = ET.fromstring(data)
    except ET.ParseError as e:
        print(f"[News Fetch] XML Parse Error: {e}", file=sys.stderr)
        return []
    results = []
    for item in root.findall(".//item"):
        title = item.findtext("title", "")
        link = item.findtext("link", "")
        source = item.findtext("source", "")
        if len(title) < 8 or not link:
            continue
        results.append((title.strip(), link.strip(), source.strip() if source else ""))
        if len(results) >= limit:
            break
    return results


def _dedupe_items(items):
    seen = set()
    output = []
    for title, url, source in items:
        key = _title_body(title)
        if key in seen:
            continue
        seen.add(key)
        output.append((title, url, source))
    return output


def _select_category(category: str, items):
    unique = _dedupe_items(items)
    non_tech = [item for item in unique if not _is_tech(item[0])]
    if category == "财经":
        preferred = [item for item in non_tech if _is_finance(item[0])]
        fallback = [item for item in non_tech if item not in preferred]
        return (preferred + fallback)[:PER_CATEGORY]
    return non_tech[:PER_CATEGORY]


def fetch_all_news():
    result = {}
    for category, urls in FEEDS.items():
        if isinstance(urls, str):
            urls = [urls]
        collected = []
        for url in urls:
            collected.extend(_fetch_rss(url))
        result[category] = _select_category(category, collected)
    return result


def _clean_title(title: str) -> str:
    # Google News RSS title often ends with " - Source"; diary title should be concise.
    return title.rsplit(" - ", 1)[0].strip()


def _source_name(title: str, source: str) -> str:
    if source:
        return source.strip()
    if " - " in title:
        return title.rsplit(" - ", 1)[-1].strip()
    return "来源"


def _topic_emoji(category: str, title: str) -> str:
    text = _norm_title(title)
    if category == "国际":
        if any(k in text for k in ["war", "military", "iran", "ukraine", "gaza", "israel"]):
            return "🕊️"
        if any(k in text for k in ["virus", "outbreak", "health", "death"]):
            return "🦠"
        return "🌍"
    if category == "国内":
        if any(k in text for k in ["习近平", "中美", "特朗普", "北京", "政策", "会议"]):
            return "🏛️"
        return "🇨🇳"
    if category == "财经":
        if any(k in text for k in ["oil", "tariff", "trade", "dollar"]):
            return "🛢️"
        if any(k in text for k in ["stock", "market", "ipo", "earnings"]):
            return "📊"
        return "💹"
    return "📌"


def _brief_summary(category: str, title: str) -> str:
    clean = _clean_title(title)
    # RSS has no full article body; keep a faithful one-line brief based on the headline.
    if "：" in clean:
        return clean.split("：", 1)[-1].strip()
    if ":" in clean:
        return clean.split(":", 1)[-1].strip()
    if " - " in clean:
        return clean.rsplit(" - ", 1)[0].strip()
    return clean


def _chii_comment(category: str, title: str) -> str:
    text = _norm_title(title)
    if category == "国际":
        if any(k in text for k in ["war", "military", "iran", "ukraine", "gaza", "israel"]):
            return "这类安全议题会牵动能源、难民与外交谈判，后续要看各方是否把冲突控制在可谈判范围内。"
        if any(k in text for k in ["bill", "tax", "election", "senate", "president"]):
            return "政治新闻表面是单点事件，背后常常是制度博弈与选民情绪的同步变化。"
        return "这条更像全球局势的温度计，值得继续观察它会不会扩散成区域连锁反应。"
    if category == "国内":
        if any(k in text for k in ["中美", "特朗普", "美国", "访华"]):
            return "中美互动一旦升温，贸易、科技与地缘预期都会跟着重新定价，主人可以留意会晤后的具体清单。"
        if any(k in text for k in ["水库", "长江", "北京", "天气"]):
            return "民生与基础设施新闻看似日常，却最能反映治理调度和普通人的真实体感。"
        return "国内新闻要抓政策信号和民生影响，两条线合在一起看会更清楚。"
    if category == "财经":
        if any(k in text for k in ["oil", "tariff", "trade"]):
            return "油价与关税会直接传导到通胀和企业成本，市场短期波动背后是利润预期在重排。"
        if any(k in text for k in ["stock", "market", "ipo", "earnings"]):
            return "资本市场的乐观通常跑在现实前面，关键要看后续盈利和流动性能不能接住估值。"
        return "财经新闻适合看二阶影响：谁的成本上升，谁的现金流改善，谁的预期被重新定价。"
    return "这条值得先记下，后续结合更多信号再判断影响范围。"


def format_news_for_diary(data):
    emoji_map = {"国际": "🌏", "国内": "♾️", "财经": "📈"}
    lines = [
        "## 📰 新闻",
        "",
        f"> 🗞️ **唧式早安播报 · {date.today().strftime('%m月%d日')}**",
        "",
    ]
    for category in ["国际", "国内", "财经"]:
        items = data.get(category, [])
        emoji = emoji_map.get(category, "📌")
        lines.append(f"### {emoji} {category}")
        if not items:
            lines.append("> 今日暂无数据~")
        else:
            for title, url, source in items[:3]:
                clean_title = _clean_title(title)
                summary = _brief_summary(category, title)
                source_label = _source_name(title, source)
                topic_emoji = _topic_emoji(category, title)
                lines.append(f"- {topic_emoji} **{clean_title}**：{summary} — [{source_label}]({url})")
                lines.append(f"  > 唧の解读：{_chii_comment(category, title)}")
        lines.append("")
    lines += [
        "> 📌 **新闻三大特性**：✅ 真实性 ✅ 时效性 ✅ 准确性",
        "> 📡 科技资讯请见 [📡今日信号] 区的 HN 消息源~",
        "",
    ]
    return "\n".join(lines)


def format_summary(data):
    lines = []
    emoji = {"国际": "🌏", "国内": "♾️", "财经": "📈"}
    for cat in ["国际", "国内", "财经"]:
        items = data.get(cat, [])
        lines.append(f"{emoji.get(cat, '')} **{cat}** ({len(items)}条)")
        for title, url, source in items:
            s = f"  • [{title[:50]}]({url})"
            if source:
                s += f" · {source}"
            lines.append(s)
    return "\n".join(lines)


def _main():
    import argparse
    parser = argparse.ArgumentParser(description="Daily News Fetch (Google News RSS)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--category", choices=["国际", "国内", "财经"], help="Single category")
    args = parser.parse_args()
    if args.category:
        urls = FEEDS[args.category]
        if isinstance(urls, str):
            urls = [urls]
        collected = []
        for url in urls:
            collected.extend(_fetch_rss(url))
        data = {args.category: _select_category(args.category, collected)}
    else:
        data = fetch_all_news()
    total = sum(len(v) for v in data.values())
    if total == 0:
        print("ERROR: No news fetched", file=sys.stderr)
        sys.exit(1)
    if args.json:
        out = {cat: [{"title": t, "url": u, "source": s} for t, u, s in items]
               for cat, items in data.items()}
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print("=== 新闻简报 ===\n")
        print(format_summary(data))
        print("\n\n=== 日记格式 ===\n")
        print(format_news_for_diary(data))
        print(f"\n✅ Fetched {total} items at {datetime.now(timezone.utc).isoformat()}")
        print("\n💡 提醒：科技版块请用 HN 消息源 -> `python hn_daily_fetch.py`")

if __name__ == "__main__":
    _main()
