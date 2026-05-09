#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
"""
vault_tools.py — Obsidian Vault 实用工具集 (基于 vault_classifier 分类结果)
用法:
  python memory/vault_tools.py search <keyword>        # 关键词搜索
  python memory/vault_tools.py search <keyword> --type daily  # 按类型过滤
  python memory/vault_tools.py inspect                 # 仓库健康检查
  python memory/vault_tools.py move <file>             # 移动 LLM-Drafts 到正确位置
"""

import os, sys, re, yaml
from collections import Counter, defaultdict
from pathlib import Path

# 添加父目录到 path 以便 import vault_classifier
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vault_classifier import VAULT, classify_type, classify_status, classify_tags

# 文件类型 → 目标目录映射
TYPE_TO_DIR = {
    'daily': '00.Chronicles/Daily',
    'moc': '05.MOCs',
    'project': '10.Projects',
    'book': '20.Bookshelf',
    'note': '80.Knowledge',
    'resource': '15.ResourceHub',
    'archive': '90.Archive',
    'unknown': None,
}

LLM_DRAFTS = os.path.join(VAULT, '99.LLM-Drafts')


def load_frontmatter(fp: str) -> dict:
    """读取文件 frontmatter，不解析 body"""
    with open(fp, 'r', encoding='utf-8') as f:
        content = f.read(4096)  # 只读前4KB足够
    if not content.startswith('---'):
        return {}
    m = re.match(r'^---\s*\n(.*?)\n(?:---|\.\.\.)\n', content, re.DOTALL)
    if not m:
        return {}
    try:
        return yaml.safe_load(m.group(1)) or {}
    except:
        return {}


def scan_vault():
    """扫描整个 vault，返回文件列表及分类结果"""
    files = []
    for root, dirs, filenames in os.walk(VAULT):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '.git']
        for f in filenames:
            if f.endswith('.md'):
                fp = os.path.join(root, f)
                rel = os.path.relpath(fp, VAULT)
                fm = load_frontmatter(fp)
                if fm:
                    files.append({'path': fp, 'rel': rel, 'fm': fm,
                                  'type': fm.get('type', 'unknown'),
                                  'status': fm.get('status', 'unknown'),
                                  'tags': fm.get('tags', [])})
    return files


def cmd_search(keyword: str, type_filter: str = None):
    """关键词搜索 — 全文搜索，支持类型过滤"""
    print(f"🔍 搜索: \"{keyword}\"", end='')
    if type_filter:
        print(f" (type={type_filter})")
    else:
        print()
    
    # 使用 findstr (Windows) 或 grep
    import subprocess
    vocab = {'keyword': keyword.lower()}
    matches = []
    
    for root, dirs, filenames in os.walk(VAULT):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '.git']
        for f in filenames:
            if not f.endswith('.md'):
                continue
            fp = os.path.join(root, f)
            rel = os.path.relpath(fp, VAULT)
            
            # 类型过滤
            if type_filter:
                fm = load_frontmatter(fp)
                if fm.get('type') != type_filter:
                    continue
            
            # 全文搜索
            try:
                with open(fp, 'r', encoding='utf-8') as fh:
                    content = fh.read()
                if keyword.lower() in content.lower():
                    matches.append((rel, fp))
            except:
                pass
    
    if not matches:
        print("  (无匹配)")
        return
    
    for rel, fp in matches:
        print(f"  📄 {rel}")
    print(f"\n  📊 共 {len(matches)} 个匹配")


def cmd_inspect():
    """仓库健康检查 — 孤儿检测 / MOC 完整性 / 类型统计"""
    files = scan_vault()
    
    print("=" * 50)
    print("📊 Vault 统计")
    print("=" * 50)
    
    # 类型分布
    type_counts = Counter(f['type'] for f in files)
    print(f"\n  总文件: {len(files)}")
    for t, c in type_counts.most_common():
        print(f"    {t}: {c}")
    
    # 状态分布
    status_counts = Counter(f['status'] for f in files)
    print(f"\n  状态分布:")
    for s, c in status_counts.most_common():
        print(f"    {s}: {c}")
    
    # LLM-Drafts 检查
    llm_dir = os.path.join(VAULT, '99.LLM-Drafts')
    if os.path.exists(llm_dir):
        drafts = []
        for root, dirs, filenames in os.walk(llm_dir):
            for f in filenames:
                if f.endswith('.md'):
                    drafts.append(os.path.relpath(os.path.join(root, f), VAULT))
        if drafts:
            print(f"\n  ⚠️  LLM-Drafts 残留 ({len(drafts)}个):")
            for d in drafts:
                print(f"    📝 {d}")
    
    # 无 frontmatter 的文件
    no_fm = []
    for root, dirs, filenames in os.walk(VAULT):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '.git']
        for f in filenames:
            if f.endswith('.md'):
                fp = os.path.join(root, f)
                fm = load_frontmatter(fp)
                if not fm:
                    no_fm.append(os.path.relpath(fp, VAULT))
    
    if no_fm:
        print(f"\n  ⚠️  无 frontmatter ({len(no_fm)}个):")
        for n in no_fm[:10]:
            print(f"    📄 {n}")
        if len(no_fm) > 10:
            print(f"    ... 等 {len(no_fm)-10} 个")
    
    # 可疑标签
    valid_tags = {
        'tech/cs', 'tech/ai', 'tech/algorithm', 'tech/development',
        'tech/rust', 'tech/math', 'tech/database', 'tech/network',
        'tech/computer', 'tech/cs144', 'tech/technology',
        'english', 'english/phonetics',
        'reading', 'game', 'history', 'health', 'psychology',
        'productivity', 'philosophy', 'culture', 'business',
        'journal', 'library', 'blog', 'project',
    }
    suspicious = Counter()
    for f in files:
        for t in f.get('tags', []):
            if '/' in t:
                suspicious[t] += 1  # 层级标签 OK
            elif t not in valid_tags and not t.startswith('#'):
                suspicious[t] += 1
    
    if suspicious:
        print(f"\n  ⚠️  非标准标签:")
        for t, c in suspicious.most_common(10):
            print(f"    {t}: {c}次")


def cmd_move(file_rel: str):
    """将文件从 LLM-Drafts 移动到正确的目录"""
    full_path = os.path.join(VAULT, file_rel)
    if not os.path.exists(full_path):
        full_path = os.path.join(LLM_DRAFTS, file_rel)
    
    if not os.path.exists(full_path):
        print(f"❌ 文件不存在: {file_rel}")
        return
    
    # 分类
    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    rel_path = os.path.relpath(full_path, VAULT)
    ftype = classify_type(content, rel_path)
    target_dir = TYPE_TO_DIR.get(ftype)
    
    if not target_dir:
        print(f"❌ 无法确定目标目录 (type={ftype})")
        return
    
    target_full = os.path.join(VAULT, target_dir)
    os.makedirs(target_full, exist_ok=True)
    
    fname = os.path.basename(full_path)
    dest = os.path.join(target_full, fname)
    
    if os.path.exists(dest):
        print(f"⚠️  目标已存在: {dest}")
        return
    
    os.rename(full_path, dest)
    print(f"✅ 移动: {os.path.relpath(full_path, VAULT)} → {os.path.relpath(dest, VAULT)}")
    print(f"   类型: {ftype}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Obsidian Vault 工具集')
    sub = parser.add_subparsers(dest='cmd')
    
    p_search = sub.add_parser('search', help='关键词搜索')
    p_search.add_argument('keyword', help='搜索关键词')
    p_search.add_argument('--type', dest='type_filter', help='按类型过滤')
    
    p_inspect = sub.add_parser('inspect', help='仓库健康检查')
    
    p_move = sub.add_parser('move', help='移动文件到正确目录')
    p_move.add_argument('file', help='文件相对路径')
    
    args = parser.parse_args()
    
    if args.cmd == 'search':
        cmd_search(args.keyword, args.type_filter)
    elif args.cmd == 'inspect':
        cmd_inspect()
    elif args.cmd == 'move':
        cmd_move(args.file)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()