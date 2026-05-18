#!/usr/bin/env python3
"""每日新闻获取 - 获取并汇总每日新闻

SOP: news_fetch_daily_sop.md
用途: 从指定源获取每日新闻，整理摘要
DIY: 一个脚本只做新闻获取
"""

import json, sys
from _encoding import setup_utf8

setup_utf8()
try:
    import urllib.request as req
except ImportError:
    import urllib2 as req

NEWS_SOURCES = {
    'github_trending': 'https://api.github.com/search/repositories?q=created:>2026-05-11&sort=stars&order=desc',
    'hackernews': 'https://hacker-news.firebaseio.com/v0/topstories.json',
}

def fetch_hn_top(n=5):
    """获取HackerNews前n条"""
    try:
        resp = req.urlopen(NEWS_SOURCES['hackernews'], timeout=10)
        ids = json.loads(resp.read())[:n]
        items = []
        for item_id in ids:
            r = req.urlopen(f'https://hacker-news.firebaseio.com/v0/item/{item_id}.json', timeout=5)
            items.append(json.loads(r.read()))
        return items
    except Exception as e:
        print(f'❌ HN获取失败: {e}')
        return []

def format_news(items):
    """格式化新闻列表"""
    lines = ['📰 每日新闻摘要', f'日期: 2026-05-12', '']
    for i, item in enumerate(items, 1):
        title = item.get('title', '无标题')
        url = item.get('url', f'https://news.ycombinator.com/item?id={item.get("id")}')
        score = item.get('score', 0)
        lines.append(f'{i}. {title}')
        lines.append(f'   得分: {score} | {url}')
        lines.append('')
    return '\n'.join(lines)

def main():
    print('🌐 获取每日新闻...')
    items = fetch_hn_top()
    result = format_news(items) if items else '⚠️ 未获取到新闻'
    print(result)

if __name__ == '__main__':
    main()
