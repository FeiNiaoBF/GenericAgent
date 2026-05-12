#!/usr/bin/env python3
"""Anki管理词汇 - 管理Anki词汇卡片

SOP: anki_manage_vocab_sop.md
用途: 添加/更新/删除Anki词汇卡片
DIY: 一个脚本只做词汇管理
"""

import json, sys
try:
    import urllib.request, urllib.error
except ImportError:
    import urllib2

ANKI_CONNECT_URL = 'http://localhost:8765'

def _request(action, **params):
    payload = json.dumps({'action': action, 'params': params, 'version': 6}).encode()
    try:
        req = urllib.request.Request(ANKI_CONNECT_URL, payload, {'Content-Type': 'application/json'})
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read())
    except Exception as e:
        return {'error': str(e)}

def add_vocab_card(deck_name, front, back, tags=None):
    """添加一张词汇卡片"""
    note = {
        'deckName': deck_name,
        'modelName': 'Basic',
        'fields': {'Front': front, 'Back': back},
        'options': {'allowDuplicate': False, 'duplicateScope': 'deck'},
        'tags': tags or []
    }
    result = _request('addNote', note=note)
    if 'error' in result and result['error']:
        print(f'❌ 添加卡片失败: {result["error"]}')
        return None
    note_id = result.get('result')
    print(f'✅ 添加成功! ID: {note_id}')
    return note_id

def find_notes(query):
    """搜索笔记"""
    result = _request('findNotes', query=query)
    return result.get('result', [])

def delete_notes(note_ids):
    """删除笔记"""
    if not note_ids:
        print('⚠️ 没有指定要删除的笔记')
        return
    result = _request('deleteNotes', notes=note_ids)
    if 'error' in result and result['error']:
        print(f'❌ 删除失败: {result["error"]}')
    else:
        print(f'✅ 删除了 {len(note_ids)} 张卡片')

def main():
    import argparse
    parser = argparse.ArgumentParser(description='管理Anki词汇卡片')
    parser.add_argument('action', choices=['add', 'find', 'delete'], help='操作类型')
    parser.add_argument('--deck', default='Default', help='牌组名称')
    parser.add_argument('--front', help='正面内容')
    parser.add_argument('--back', help='背面内容')
    parser.add_argument('--query', help='搜索查询')
    args = parser.parse_args()

    if args.action == 'add':
        if not args.front or not args.back:
            print('❌ add操作需要 --front 和 --back')
            sys.exit(1)
        add_vocab_card(args.deck, args.front, args.back)
    elif args.action == 'find':
        if not args.query:
            print('❌ find操作需要 --query')
            sys.exit(1)
        notes = find_notes(args.query)
        print(f'找到 {len(notes)} 张卡片: {notes}')
    elif args.action == 'delete':
        if not args.query:
            print('❌ delete操作需要 --query 指定范围')
            sys.exit(1)
        notes = find_notes(args.query)
        delete_notes(notes)

if __name__ == '__main__':
    main()
