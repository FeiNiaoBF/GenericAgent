#!/usr/bin/env python3
"""网页搜索：通过Google等搜索引擎获取信息"""
import requests
from urllib.parse import quote_plus

def google_search(query: str, num: int = 5) -> list:
    """Google搜索（需配置API）"""
    try:
        # 尝试使用配置的搜索API
        from config import search_cfg
        url = f"https://www.googleapis.com/customsearch/v1?q={quote_plus(query)}&key={search_cfg.api_key}&cx={search_cfg.cx}&num={num}"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        return [{"title": item.get('title'), "link": item.get('link'), "snippet": item.get('snippet')}
                for item in data.get('items', [])]
    except (ImportError, Exception) as e:
        return [f"❌ 搜索失败: {e}"]

def search_fallback(query: str) -> str:
    """备用：直接返回搜索提示"""
    return f"🔍 搜索: {query} (请配置搜索API)"
