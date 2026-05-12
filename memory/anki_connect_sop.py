#!/usr/bin/env python3
"""AnkiConnect - 连接AnkiConnect API并测试连通性

SOP: anki_connect_sop.md
用途: 测试AnkiConnect连接状态，获取deck/note信息
DIY: 一个脚本只做连接测试
"""

import json, sys, urllib.request, urllib.error

ANKI_CONNECT_URL = 'http://localhost:8765'

def request(action, **params):
    """发送请求到AnkiConnect"""
    payload = json.dumps({'action': action, 'params': params, 'version': 6}).encode()
    try:
        req = urllib.request.Request(ANKI_CONNECT_URL, payload, {'Content-Type': 'application/json'})
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read())
    except urllib.error.URLError as e:
        return {'error': f'连接失败: {e}'}

def test_connection():
    """测试AnkiConnect连接"""
    result = request('version')
    if 'error' in result and result['error']:
        print(f'❌ AnkiConnect连接失败: {result["error"]}')
        return False
    print(f'✅ AnkiConnect连接成功! 版本: {result.get("result", "unknown")}')
    return True

def list_decks():
    """列出所有牌组"""
    result = request('deckNames')
    if 'error' in result and result['error']:
        print(f'❌ 获取牌组失败: {result["error"]}')
        return []
    decks = result.get('result', [])
    print(f'📚 牌组 ({len(decks)}个):')
    for d in decks:
        print(f'  - {d}')
    return decks

def main():
    print('=== AnkiConnect 连接测试 ===')
    if not test_connection():
        sys.exit(1)
    list_decks()

if __name__ == '__main__':
    main()
