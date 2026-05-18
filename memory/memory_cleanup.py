#!/usr/bin/env python3
"""
memory_cleanup.py — Memory 目录清理工具
用法:
  python memory/memory_cleanup.py dry-run                # 预览清理计划
  python memory/memory_cleanup.py run                    # 执行清理
  python memory/memory_cleanup.py stats                  # 目录统计

清理规则:
  - 匹配 memory_management_sop.md §5 的自动化清理清单
  - 删除临时/重复文件
  - 归档旧日志到 L4
  - 合并小 fragments
"""

import os, sys, re, shutil, io
from _encoding import setup_utf8; setup_utf8()
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

# Fix Windows GBK encoding for emoji output

MEMORY_DIR = os.path.dirname(os.path.abspath(__file__))
L4_DIR = os.path.join(MEMORY_DIR, 'L4_raw_sessions')

# 保留文件白名单（永不删除）
KEEP_ALWAYS = {
    'global_mem.txt', 'global_mem_insight.txt',
    'memory_management_sop.md', 'obsidian_knowledge_sop.md',
    'learning_tutor_study_sop.md', 'english_learning.md',
    'chi_character_card.md', 'user_profile.md',
    '.gitkeep', '.gitignore', 'README.md',
}

# 当前活跃的脚本
ACTIVE_SCRIPTS = {
    'vault_classifier.py', 'vault_tools.py',
    'verify_note.py', 'diary_append.py',
    'audit_l1.py', 'memory_cleanup.py',
}


def get_all_files():
    """获取 memory 目录下所有文件"""
    files = []
    for f in os.listdir(MEMORY_DIR):
        fp = os.path.join(MEMORY_DIR, f)
        if os.path.isfile(fp) and not f.startswith('.'):
            stat = os.stat(fp)
            files.append({
                'name': f, 'path': fp, 'size': stat.st_size,
                'mtime': stat.st_mtime, 'ext': os.path.splitext(f)[1],
            })
    return sorted(files, key=lambda x: x['mtime'], reverse=True)


def get_l4_files():
    """获取 L4 目录下所有文件"""
    if not os.path.exists(L4_DIR):
        return []
    files = []
    for f in os.listdir(L4_DIR):
        fp = os.path.join(L4_DIR, f)
        if os.path.isfile(fp):
            stat = os.stat(fp)
            files.append({
                'name': f, 'path': fp, 'size': stat.st_size,
                'mtime': stat.st_mtime,
            })
    return sorted(files, key=lambda x: x['mtime'], reverse=True)


def cmd_stats():
    """目录统计"""
    files = get_all_files()
    l4_files = get_l4_files()
    
    total_size = sum(f['size'] for f in files)
    l4_total = sum(f['size'] for f in l4_files)
    
    print("=" * 50)
    print("📊 Memory 目录统计")
    print("=" * 50)
    print(f"\n  memory/:")
    print(f"    文件数: {len(files)}")
    print(f"    总大小: {total_size / 1024:.1f} KB")
    
    print(f"\n  memory/L4_raw_sessions/:")
    print(f"    文件数: {len(l4_files)}")
    print(f"    总大小: {l4_total / 1024:.1f} KB")
    
    # 按扩展名分类
    ext_counts = defaultdict(lambda: {'count': 0, 'size': 0})
    for f in files:
        ext = f['ext'] or '(无)'
        ext_counts[ext]['count'] += 1
        ext_counts[ext]['size'] += f['size']
    
    print(f"\n  按类型:")
    for ext, info in sorted(ext_counts.items()):
        print(f"    {ext}: {info['count']}个, {info['size']/1024:.1f}KB")


def cmd_dry_run():
    """预览清理计划"""
    files = get_all_files()
    now = datetime.now()
    
    actions = {
        'delete': [],
        'archive': [],
        'merge': [],
        'keep': [],
    }
    
    # 识别碎片文件（<500B 的 .md 文件，非白名单，非活跃脚本）
    fragments = []
    for f in files:
        if f['name'] in KEEP_ALWAYS:
            actions['keep'].append(f['name'])
            continue
        if f['name'] in ACTIVE_SCRIPTS:
            actions['keep'].append(f['name'])
            continue
        if f['size'] < 500 and f['ext'] == '.md':
            fragments.append(f)
        elif f['size'] < 200 and f['ext'] != '.md':
            actions['delete'].append(f['name'])
    
    # 碎片合并建议
    if fragments:
        actions['merge'] = [f['name'] for f in fragments]
    
    print("=" * 50)
    print("🔍 清理预览 (dry-run)")
    print("=" * 50)
    
    if actions['merge']:
        print(f"\n  📦 可合并碎片 ({len(actions['merge'])}个 <500B):")
        for f in actions['merge']:
            print(f"     📄 {f}")
        print(f"  💡 合并后删除原文件")
    
    if actions['delete']:
        print(f"\n  🗑️  可删除 ({len(actions['delete'])}个):")
        for f in actions['delete']:
            print(f"     ❌ {f}")
    
    if actions['keep']:
        print(f"\n  ✅ 保留 ({len(actions['keep'])}个)")
    
    print(f"\n  💡 执行: python memory/memory_cleanup.py run")


def cmd_run():
    """执行清理"""
    files = get_all_files()
    
    deleted = 0
    merged = 0
    errors = 0
    
    print("=" * 50)
    print("🧹 执行清理")
    print("=" * 50)
    
    # 收集碎片
    fragments = []
    for f in files:
        if f['name'] in KEEP_ALWAYS or f['name'] in ACTIVE_SCRIPTS:
            continue
        if f['size'] < 500 and f['ext'] == '.md':
            fragments.append(f)
    
    # 合并碎片到 global_mem_fragments_archive.md
    if fragments:
        archive_path = os.path.join(MEMORY_DIR, '_fragment_archive.md')
        with open(archive_path, 'w', encoding='utf-8') as af:
            af.write(f"# Fragment Archive\n")
            af.write(f"合并时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
            
            for f in fragments:
                af.write(f"## {f['name']}\n")
                af.write(f"大小: {f['size']}B | 修改: {datetime.fromtimestamp(f['mtime']).strftime('%Y-%m-%d')}\n\n")
                try:
                    with open(f['path'], 'r', encoding='utf-8') as src:
                        content = src.read(2000)
                    af.write(content)
                    af.write('\n\n---\n\n')
                    # 删除原文件
                    os.remove(f['path'])
                    merged += 1
                    print(f"  📦 合并+删除: {f['name']}")
                except Exception as e:
                    errors += 1
                    print(f"  ❌ 无法合并 {f['name']}: {e}")
        
        print(f"  ✅ 碎片存档: _fragment_archive.md ({merged}个文件)")
    
    # 删除微小非 md 文件
    for f in files:
        if f['name'] in KEEP_ALWAYS or f['name'] in ACTIVE_SCRIPTS:
            continue
        if f['size'] < 200 and f['ext'] != '.md' and f['ext'] != '.py':
            try:
                os.remove(f['path'])
                deleted += 1
                print(f"  🗑️  删除: {f['name']} ({f['size']}B)")
            except Exception as e:
                errors += 1
                print(f"  ❌ 无法删除 {f['name']}: {e}")
    
    # 归档旧 L4（>30天的日志文件可选压缩）
    if os.path.exists(L4_DIR):
        old_count = 0
        cutoff = (datetime.now() - timedelta(days=30)).timestamp()
        for f_name in os.listdir(L4_DIR):
            fp = os.path.join(L4_DIR, f_name)
            if os.path.isfile(fp):
                if os.stat(fp).st_mtime < cutoff and not f_name.endswith('.gz'):
                    old_count += 1
        if old_count:
            print(f"\n  📦 L4 旧日志 ({old_count}个 >30天), 可手动归档:")
            print(f"     tar -czf L4_archive_$(date +%Y%m).tar.gz L4_raw_sessions/old_*.md")
    
    # 清理 __pycache__ 目录
    pycache_dirs = []
    for root, dirs, files in os.walk(MEMORY_DIR):
        for d in dirs:
            if d == '__pycache__':
                pycache_dirs.append(os.path.join(root, d))
    for pd in pycache_dirs:
        try:
            shutil.rmtree(pd)
            print(f"  🧹 删除 __pycache__: {pd}")
        except Exception as e:
            errors += 1
            print(f"  ❌ 无法删除 {pd}: {e}")
    
    # .zip 文件已是压缩格式，gzip 无效（12.9MB→12.8MB），跳过
    
    print(f"\n  📊 清理完成: 合并 {merged}, 删除 {deleted}, 错误 {errors}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Memory 目录清理工具')
    sub = parser.add_subparsers(dest='cmd')
    sub.add_parser('dry-run', help='预览清理计划')
    sub.add_parser('run', help='执行清理')
    sub.add_parser('stats', help='目录统计')
    
    args = parser.parse_args()
    
    if args.cmd == 'dry-run':
        cmd_dry_run()
    elif args.cmd == 'run':
        cmd_run()
    elif args.cmd == 'stats':
        cmd_stats()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()