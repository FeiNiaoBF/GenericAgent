#!/usr/bin/env python3
"""Obsidian MOC管理 - 管理Obsidian知识地图(MOC)

SOP: obsidian_manage_moc_sop.md
用途: 创建/更新/查询MOC标签页
DIY: 一个脚本只做MOC管理
"""

import json, os, datetime

MOC_FILE = 'D:\Creative_Studio\WorkSpace\Github\GenericAgent\memory\moc_index.json'

def load_mocs():
    if os.path.exists(MOC_FILE):
        with open(MOC_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def create_moc(name, description=''):
    """创建MOC"""
    mocs = load_mocs()
    if name in mocs:
        print('⚠️ MOC "%s" 已存在' % name)
        return False
    mocs[name] = {
        'description': description,
        'entries': [],
        'created': datetime.datetime.now().isoformat()[:10],
        'updated': datetime.datetime.now().isoformat()[:10]
    }
    with open(MOC_FILE, 'w', encoding='utf-8') as f:
        json.dump(mocs, f, ensure_ascii=False, indent=2)
    print('✅ MOC "%s" 已创建' % name)
    return True

def add_entry(moc_name, entry_title, entry_path=''):
    """添加MOC条目"""
    mocs = load_mocs()
    if moc_name not in mocs:
        print('❌ MOC "%s" 不存在' % moc_name)
        return False
    mocs[moc_name]['entries'].append({
        'title': entry_title,
        'path': entry_path,
        'added': datetime.datetime.now().isoformat()[:10]
    })
    mocs[moc_name]['updated'] = datetime.datetime.now().isoformat()[:10]
    with open(MOC_FILE, 'w', encoding='utf-8') as f:
        json.dump(mocs, f, ensure_ascii=False, indent=2)
    print('✅ 已添加到 "%s": %s' % (moc_name, entry_title))
    return True

def list_mocs():
    """列出所有MOC"""
    mocs = load_mocs()
    if not mocs:
        print('📋 暂无MOC')
        return
    print('📋 MOC列表 (%d个):' % len(mocs))
    for name, moc in mocs.items():
        print('  📌 %s (%d条目)' % (name, len(moc['entries'])))
        print('     %s' % moc.get('description', ''))
        for e in moc['entries'][:5]:
            print('       📄 %s' % e['title'])
        if len(moc['entries']) > 5:
            print('       ... 还有%d条' % (len(moc['entries']) - 5))

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Obsidian MOC管理')
    parser.add_argument('action', choices=['create', 'add', 'list'], help='操作')
    parser.add_argument('--name', help='MOC名称')
    parser.add_argument('--desc', help='MOC描述')
    parser.add_argument('--entry', help='条目标题')
    parser.add_argument('--path', help='条目路径')
    args = parser.parse_args()

    if args.action == 'create':
        create_moc(args.name or '未命名', args.desc or '')
    elif args.action == 'add':
        add_entry(args.name or '', args.entry or '未命名', args.path or '')
    elif args.action == 'list':
        list_mocs()

if __name__ == '__main__':
    main()
