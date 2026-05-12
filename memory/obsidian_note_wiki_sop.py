#!/usr/bin/env python3
"""Obsidian Wiki笔记 - 创建和管理Wiki风格的笔记

SOP: obsidian_note_wiki_sop.md
用途: 创建带[[双链]]的Wiki笔记、维护单个概念页
DIY: 一个脚本只做Wiki笔记管理
"""

import os, re, datetime

NOTES_DIR = 'D:\Creative_Studio\WorkSpace\Github\GenericAgent\05.Knowledge'

def create_note(title, content='', category=''):
    """创建Wiki笔记"""
    safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
    
    if category:
        note_dir = os.path.join(NOTES_DIR, category)
    else:
        note_dir = NOTES_DIR
    
    os.makedirs(note_dir, exist_ok=True)
    
    filepath = os.path.join(note_dir, '%s.md' % safe_title)
    if os.path.exists(filepath):
        print('⚠️ 笔记已存在: %s' % filepath)
        return filepath
    
    frontmatter_lines = [
        '---',
        'title: %s' % title,
        'created: %s' % datetime.date.today(),
        'tags: []',
        '---',
        '',
        '# %s' % title,
        '',
        content,
        '',
    ]
    frontmatter = '\n'.join(frontmatter_lines)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(frontmatter)
    
    print('✅ 笔记已创建: %s' % filepath)
    return filepath

def find_orphans():
    """查找孤立笔记(没有被任何[[双链]]引用的笔记)"""
    if not os.path.exists(NOTES_DIR):
        print('⚠️ 笔记目录不存在')
        return []
    
    all_notes = []
    for root, dirs, files in os.walk(NOTES_DIR):
        for f in files:
            if f.endswith('.md'):
                with open(os.path.join(root, f), 'r', encoding='utf-8') as fh:
                    content = fh.read()
                all_notes.append((f.replace('.md', ''), content))
    
    linked = set()
    for name, content in all_notes:
        links = re.findall(r'\[\[(\w+)\]\]', content)
        linked.update(links)
    
    orphans = [(name, content) for name, content in all_notes if name not in linked]
    
    print('🔗 孤立笔记 (%d篇):' % len(orphans))
    for name, _ in orphans:
        print('  📄 [[%s]]' % name)
    return orphans

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Obsidian Wiki笔记管理')
    parser.add_argument('action', choices=['create', 'orphans'], help='操作')
    parser.add_argument('--title', help='笔记标题')
    parser.add_argument('--content', default='', help='笔记内容')
    parser.add_argument('--category', help='分类目录')
    args = parser.parse_args()

    if args.action == 'create':
        if not args.title:
            print('❌ create需要 --title')
            sys.exit(1)
        create_note(args.title, args.content, args.category or '')
    elif args.action == 'orphans':
        find_orphans()

if __name__ == '__main__':
    import sys
    main()
