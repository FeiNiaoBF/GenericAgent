#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
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
    "国际": "https://news.google.com/rss/headlines/section/topic/WORLD?hl=en-US&gl=US&ceid=US:en",
    "国内": "https://news.google.com/rss?hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
    "财经": "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-US&gl=US&ceid=US:en",
}

PER_CATEGORY = 5
REQUEST_TIMEOUT = 10
USER_AGENT = "Mozilla/5.0 (compatible; GenericAgent-News-fetcher/1.0)"


def _fetch_rss(url: str):
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
        if len(results) >= PER_CATEGORY:
            break
    return results


def fetch_all_news():
    result = {}
    for category, url in FEEDS.items():
        result[category] = _fetch_rss(url)
    return result


def format_news_for_diary(data):
    today_str = date.today().strftime("%Y-%m-%d")
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
            for title, url, source in items:
                source_tag = f" — *{source}*" if source else ""
                lines.append(f"- [{title}]({url}){source_tag}")
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
        data = {args.category: _fetch_rss(FEEDS[args.category])}
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
