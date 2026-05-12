#!/usr/bin/env python3
"""Obsidian知识管理 - 管理Obsidian知识库

SOP: obsidian_knowledge_sop.md
用途: 整理/分类/检索Obsidian中的知识笔记
DIY: 一个脚本只做知识管理
"""

import os, sys

KNOWLEDGE_DIR = 'D:\Creative_Studio\WorkSpace\Github\GenericAgent\05.Knowledge'

def list_categories():
    """列出知识分类"""
    if not os.path.exists(KNOWLEDGE_DIR):
        print('⚠️ 知识库目录不存在: %s' % KNOWLEDGE_DIR)
        return []
    
    categories = []
    for entry in sorted(os.listdir(KNOWLEDGE_DIR)):
        full = os.path.join(KNOWLEDGE_DIR, entry)
        if os.path.isdir(full):
            count = len([f for f in os.listdir(full) if f.endswith('.md')])
            categories.append((entry, count))
    
    print('📚 知识库分类 (%d个):' % len(categories))
    for cat, count in categories:
        print('  📁 %s/ (%d篇笔记)' % (cat, count))
    return categories

def search_notes(keyword):
    """搜索笔记"""
    if not os.path.exists(KNOWLEDGE_DIR):
        return []
    
    results = []
    keyword = keyword.lower()
    for root, dirs, files in os.walk(KNOWLEDGE_DIR):
        for f in files:
            if f.endswith('.md'):
                fpath = os.path.join(root, f)
                try:
                    with open(fpath, 'r', encoding='utf-8') as fh:
                        content = fh.read()
                    if keyword in content.lower():
                        relpath = os.path.relpath(fpath, KNOWLEDGE_DIR)
                        results.append(relpath)
                except:
                    pass
    
    print('🔍 搜索 "%s": 找到 %d篇' % (keyword, len(results)))
    for r in results[:20]:
        print('  📄 %s' % r)
    if len(results) > 20:
        print('  ... 还有%d篇未显示' % (len(results) - 20))
    return results

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Obsidian知识管理')
    parser.add_argument('action', choices=['categories', 'search'], help='操作')
    parser.add_argument('--keyword', help='搜索关键词')
    args = parser.parse_args()

    if args.action == 'categories':
        list_categories()
    elif args.action == 'search':
        search_notes(args.keyword or '')

if __name__ == '__main__':
    main()
