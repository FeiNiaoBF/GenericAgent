#!/usr/bin/env python3
"""信号源获取：从配置的源拉取新闻/通知/任务信号"""
import json, requests
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / '..' / 'config' / 'signal_sources.json'

def load_sources() -> list:
    """加载信号源配置"""
    cfg = json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
    return cfg.get('sources', [])

def fetch_source(source: dict) -> list:
    """从单个信号源拉取数据"""
    try:
        resp = requests.get(source['url'], timeout=10)
        resp.raise_for_status()
        return resp.json() if source.get('type') == 'json' else resp.text
    except Exception as e:
        return [f"❌ 拉取失败: {e}"]

def fetch_all() -> dict:
    """拉取所有信号源"""
    results = {}
    for s in load_sources():
        results[s['name']] = fetch_source(s)
    return results

if __name__ == '__main__':
    data = fetch_all()
    for name, items in data.items():
        print(f"[{name}] {len(items) if isinstance(items, list) else 'ok'} items")
