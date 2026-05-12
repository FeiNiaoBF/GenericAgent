#!/usr/bin/env python3
"""Obsidian图书馆管理 - 管理Obsidian图书馆藏书

SOP: obsidian_manage_library_sop.md
用途: 添加/查询/整理Obsidian中的书籍笔记
DIY: 一个脚本只做图书馆管理
"""

import json, os, datetime

LIBRARY_FILE = 'D:\Creative_Studio\WorkSpace\Github\GenericAgent\memory\library_index.json'

def load_library():
    if os.path.exists(LIBRARY_FILE):
        with open(LIBRARY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_library(books):
    with open(LIBRARY_FILE, 'w', encoding='utf-8') as f:
        json.dump(books, f, ensure_ascii=False, indent=2)

def add_book(title, author, status='unread', tags=None):
    """添加书籍"""
    books = load_library()
    book = {
        'id': len(books) + 1,
        'title': title,
        'author': author,
        'status': status,
        'tags': tags or [],
        'added': datetime.datetime.now().isoformat()[:10]
    }
    books.append(book)
    save_library(books)
    print('✅ 已添加: 《%s》- %s' % (title, author))
    return book

def list_books(status=None):
    """列出书籍"""
    books = load_library()
    if status:
        books = [b for b in books if b['status'] == status]
    
    print('📚 藏书 (%d本)' % len(books))
    status_icons = {'reading': '📖', 'unread': '📕', 'done': '✅'}
    for b in books:
        icon = status_icons.get(b['status'], '📄')
        print('  %s #%d 《%s》- %s' % (icon, b['id'], b['title'], b['author']))

def search_books(keyword):
    """搜索书籍"""
    books = load_library()
    keyword = keyword.lower()
    results = [b for b in books if keyword in b['title'].lower() or keyword in b['author'].lower()]
    print('🔍 搜索 "%s": 找到 %d本' % (keyword, len(results)))
    for b in results:
        print('  #%d 《%s》- %s [%s]' % (b['id'], b['title'], b['author'], b['status']))

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Obsidian图书馆管理')
    parser.add_argument('action', choices=['add', 'list', 'search'], help='操作')
    parser.add_argument('--title', help='书名')
    parser.add_argument('--author', default='未知', help='作者')
    parser.add_argument('--status', choices=['unread', 'reading', 'done'], default='unread')
    parser.add_argument('--keyword', help='搜索关键词')
    parser.add_argument('--tag', action='append', help='标签')
    args = parser.parse_args()

    if args.action == 'add':
        add_book(args.title or '未命名', args.author, args.status, args.tag)
    elif args.action == 'list':
        list_books(args.status)
    elif args.action == 'search':
        search_books(args.keyword or '')

if __name__ == '__main__':
    main()
