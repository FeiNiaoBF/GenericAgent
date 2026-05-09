#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
"""
HN Daily Fetch Tool — 定时/手动获取 Hacker News 头条
=====================================================
用法:
  from memory.hn_daily_fetch import fetch_top_stories, format_for_diary, format_for_source_note

  data = fetch_top_stories(n=15)
  # data: [(rank, title, url, score, descendants, item_id), ...]

  diary_md = format_for_diary(data)      # → 日记 📡今日信号 区块
  note_md  = format_for_source_note(data) # → HN 源笔记 今日热点 区块

独立运行:
  python hn_daily_fetch.py          # 打印完整输出
  python hn_daily_fetch.py --json   # 打印 JSON 格式
"""

import urllib.request
import json
import time
import sys
from datetime import date, datetime, timezone

# ── Config ──────────────────────────────────────────
API_TOPSTORIES = "https://hacker-news.firebaseio.com/v0/topstories.json"
API_ITEM       = "https://hacker-news.firebaseio.com/v0/item/{}.json"
TOP_N          = 15
REQUEST_TIMEOUT = 8
USER_AGENT     = "Mozilla/5.0 (compatible; GenericAgent-HN-fetcher/1.0)"


def _fetch_json(url: str):
    """Fetch JSON from URL, return None on failure."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[HN Fetch] ERROR: {url[:60]}... → {e}", file=sys.stderr)
        return None


def fetch_top_stories(n: int = TOP_N):
    """
    获取 HN Top N 故事。
    返回: [(rank, title, url, score, descendants, item_id), ...]
    失败返回空列表。
    """
    ids = _fetch_json(API_TOPSTORIES)
    if not ids:
        return []

    results = []
    for item_id in ids:
        if len(results) >= n:
            break
        item = _fetch_json(API_ITEM.format(item_id))
        if not item:
            continue

        # 跳过非 story 类型 (job, poll 等)
        if item.get("type") != "story":
            continue

        url = item.get("url") or f"https://news.ycombinator.com/item?id={item_id}"
        title = item.get("title", "(No title)")
        score = item.get("score", 0)
        descendants = item.get("descendants", 0)

        results.append((
            len(results) + 1,  # rank
            title,
            url,
            score,
            descendants,
            item_id
        ))

    return results


def format_for_diary(data):
    """
    格式化为日记 📡今日信号 区块插入内容。
    """
    today_str = date.today().strftime("%Y-%m-%d")
    lines = [
        f"> 📡 **HN 今日信号 · {today_str}**",
        f"> 自动抓取 {len(data)} 条热门话题，唧已帮你排好优先级~",
        "",
        "| # | 评分 | 💬 | 标题 |",
        "|---|------|-----|------|",
    ]
    for rank, title, url, score, descendants, item_id in data:
        title_short = title[:80] + "…" if len(title) > 80 else title
        hn_link = f"https://news.ycombinator.com/item?id={item_id}"
        lines.append(
            f"| {rank} | **{score}** | {descendants} | "
            f"[{title_short}]({url} '🔗 原文') [[HN]]({hn_link} '💬 HN 评论') |"
        )

    lines += [
        "",
        "💡 评分 >200 的精读 1 篇，>100 的扫标题，<50 的可跳过",
    ]
    return "\n".join(lines)


def format_for_source_note(data):
    """
    格式化为 HN 源笔记 ## 今日热点 区块内容。
    """
    today_str = date.today().strftime("%Y-%m-%d")
    lines = [
        f"## 今日热点 ({today_str})",
        "",
        "> 📊 自动抓取快照，反映当前社区兴趣",
        "",
        f"### 🔥 TOP {len(data)}",
    ]

    for rank, title, url, score, descendants, item_id in data:
        comment_str = f", {descendants}💬" if descendants > 0 else ""
        lines.append(f"{rank}. **{title}** ({score}pts{comment_str})")
        if url and "item?id=" not in url:
            lines.append(f"   → {url}")
        else:
            lines.append(f"   → https://news.ycombinator.com/item?id={item_id}")

    lines += [
        "",
        "### 信号解读",
        "- ",
        "- ",
        "- ",
    ]
    return "\n".join(lines)


# ── CLI ─────────────────────────────────────────────
def _main():
    import argparse
    parser = argparse.ArgumentParser(description="HN Daily Fetch")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--count", type=int, default=TOP_N, help="Number of stories")
    args = parser.parse_args()

    data = fetch_top_stories(n=args.count)
    if not data:
        print("ERROR: Failed to fetch HN data", file=sys.stderr)
        sys.exit(1)

    if args.json:
        out = [{"rank": r, "title": t, "url": u, "score": s, "comments": d, "id": i}
               for r, t, u, s, d, i in data]
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print("=== DIARY FORMAT ===\n")
        print(format_for_diary(data))
        print("\n\n=== SOURCE NOTE FORMAT ===\n")
        print(format_for_source_note(data))
        print(f"\n✅ Fetched {len(data)} stories at {datetime.now(timezone.utc).isoformat()}")


if __name__ == "__main__":
    _main()