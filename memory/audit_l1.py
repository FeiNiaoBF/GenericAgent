#!/usr/bin/env python3
"""
audit_l1.py — L1 Insight 索引审计工具
用法:
  python memory/audit_l1.py check                  # 对照模板检查
  python memory/audit_l1.py sync                   # 自动同步（安全模式）
  python memory/audit_l1.py sync --force           # 强制同步
  python memory/audit_l1.py report                 # 生成审计报告
"""

import os, sys, re
from datetime import datetime

from _encoding import setup_utf8; setup_utf8()

# 工作目录
MEMORY_DIR = os.path.dirname(os.path.abspath(__file__))
L1_FILE = os.path.join(MEMORY_DIR, 'global_mem_insight.txt')

# L1 模板：必须包含的 key 前缀
REQUIRED_KEYS = [
    '浏览器:', '键鼠:', '视觉:', '定时:', '手机:',
    '画像:', '搜索:', 'PPT:', '飞书:',
    'Obsidian:', '英语:', 'CS:',
    'MEM:', 'L2:', 'L3:', 'L4:', '知识库:',
    '人格:', '日记:', '压缩:', '重构:',
    '计划:', '验证:', '文档:', '遍历:',
    'Git:', '贴纸:', '新闻:',
    'TG发送:', '日历:', '消息源:', '公基:', 'GitHub:',
]

# 可选但建议有的
OPTIONAL_KEYS = [
    'blog_sync', 'daily_task', 'excalidraw', '插件:',
    'skill_search', 'web_search',
]


def load_l1_content() -> str:
    """读取 L1 内容"""
    if not os.path.exists(L1_FILE):
        return ''
    with open(L1_FILE, 'r', encoding='utf-8') as f:
        return f.read()


def parse_l1_keys(content: str) -> list:
    """解析 L1 中的 key:value 行（支持 | 分隔多key）"""
    keys = []
    for line in content.split('\n'):
        line = line.strip()
        if ':' in line and not line.startswith('#'):
            # 先按 | 拆分多key行，再逐段提取key
            for segment in line.split('|'):
                segment = segment.strip()
                if ':' in segment:
                    key = segment.split(':')[0] + ':'
                    keys.append(key)
    return keys


def cmd_check():
    """检查 L1 — 对照模板"""
    content = load_l1_content()
    if not content:
        print("❌ L1 文件不存在或为空")
        return False
    
    existing_keys = set(parse_l1_keys(content))
    
    print("=" * 50)
    print("📋 L1 索引审计")
    print("=" * 50)
    
    missing = []
    for req in REQUIRED_KEYS:
        found = any(k.startswith(req) for k in existing_keys)
        if not found:
            missing.append(req)
            print(f"  ❌ 缺失: {req}")
    
    # 可选键
    for opt in OPTIONAL_KEYS:
        found = any(opt in k for k in existing_keys)
        if not found:
            print(f"  ⚠️  可选缺失: {opt}")
    
    if missing:
        print(f"\n  📊 共 {len(missing)} 个必需键缺失")
        print(f"  💡 运行: python memory/audit_l1.py sync")
        return False
    else:
        print(f"\n  ✅ 全部 {len(REQUIRED_KEYS)} 个必需键存在")
        print(f"  📊 共 {len(existing_keys)} 个键")
        return True


def cmd_sync(force: bool = False):
    """同步 L1 — 扫描 memory/*.md 和 memory/*.py 推断缺失键"""
    content = load_l1_content()
    existing_keys = parse_l1_keys(content)
    existing_key_set = set(existing_keys)
    
    # 扫描 memory 目录下的文件
    files_in_memory = []
    for f in os.listdir(MEMORY_DIR):
        fp = os.path.join(MEMORY_DIR, f)
        if os.path.isfile(fp) and (f.endswith('.md') or f.endswith('.py')):
            # 跳过自身
            if f == 'audit_l1.py':
                continue
            files_in_memory.append(f)
    
    print("=" * 50)
    print("🔄 L1 索引同步")
    print("=" * 50)
    
    # 从文件名推断可能的 key
    inferred = {}
    for f in files_in_memory:
        stem = os.path.splitext(f)[0]
        # 映射已知模式
        if 'verify' in stem.lower() or 'validate' in stem.lower():
            inferred.setdefault('验证:', []).append(f)
        elif 'sop' in stem.lower():
            key = stem.replace('_sop', '').replace('_', ':')
            if ':' not in key:
                key = key + ':'
            inferred.setdefault(key, []).append(f)
        elif 'diary' in stem.lower():
            inferred.setdefault('日记:', []).append(f)
        elif 'vault' in stem.lower():
            inferred.setdefault('Obsidian:', []).append(f)
        elif 'audit' in stem.lower() or 'cleanup' in stem.lower():
            inferred.setdefault('MEM:', []).append(f)
    
    # 查找缺失键
    missing = []
    for req in REQUIRED_KEYS:
        found = any(k.startswith(req) for k in existing_key_set)
        if not found:
            missing.append(req)
    
    if not missing:
        print("  ✅ 无缺失，无需同步")
        return
    
    if not force:
        print(f"  ⚠️  发现 {len(missing)} 个缺失键:")
        for m in missing:
            print(f"     - {m}")
        print(f"\n  📁 扫描到 {len(files_in_memory)} 个相关文件:")
        for ik, ifiles in inferred.items():
            print(f"     {ik} {ifiles}")
        print(f"\n  💡 请手动补充或运行: python memory/audit_l1.py sync --force")
        return
    
    # --force: 自动补充空值
    new_lines = []
    for m in missing:
        new_lines.append(f"{m} ")
    
    if new_lines:
        new_content = '\n'.join(new_lines) + '\n'
        with open(L1_FILE, 'a', encoding='utf-8') as f:
            f.write(new_content)
        print(f"  ✅ 已补充 {len(new_lines)} 个缺失键（值为空，请手动填写）")
        for nl in new_lines:
            print(f"     + {nl.strip()}")


def cmd_report():
    """生成详细审计报告"""
    content = load_l1_content()
    existing_keys = parse_l1_keys(content)
    
    # 统计 memory/ 下所有文件
    md_files = []
    py_files = []
    for f in os.listdir(MEMORY_DIR):
        if os.path.isfile(os.path.join(MEMORY_DIR, f)):
            if f.endswith('.md'):
                md_files.append(f)
            elif f.endswith('.py'):
                py_files.append(f)
    
    print(f"📅 审计时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"\n📊 统计:")
    print(f"  L1 键数: {len(existing_keys)}")
    print(f"  memory/*.md: {len(md_files)} 个")
    print(f"  memory/*.py: {len(py_files)} 个")
    
    # 检查是否有 L1 引用但文件不存在的
    referenced = set()
    for line in content.split('\n'):
        line = line.strip()
        if ':' in line and not line.startswith('#'):
            value = line.split(':', 1)[1].strip()
            if value and value.endswith('.md') or value.endswith('.py'):
                referenced.add(value)
    
    orphan_refs = referenced - set(md_files) - set(py_files)
    if orphan_refs:
        print(f"\n  ⚠️  L1 引用了不存在的文件:")
        for o in orphan_refs:
            print(f"     📛 {o}")
    
    # 检查 memory 有但 L1 未引用
    l1_text = content.lower()
    unref_files = []
    for f in md_files + py_files:
        if f == 'audit_l1.py':
            continue
        stem = os.path.splitext(f)[0].lower()
        if stem not in l1_text and f.lower() not in l1_text:
            unref_files.append(f)
    
    if unref_files:
        print(f"\n  ⚠️  L1 未引用的文件 ({len(unref_files)}个):")
        for u in sorted(unref_files):
            print(f"     📄 {u}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='L1 索引审计工具')
    sub = parser.add_subparsers(dest='cmd')
    sub.add_parser('check', help='检查 L1 完整性')
    sub.add_parser('report', help='生成审计报告')
    p_sync = sub.add_parser('sync', help='同步缺失键')
    p_sync.add_argument('--force', action='store_true', help='强制自动补充')
    
    args = parser.parse_args()
    
    if args.cmd == 'check':
        ok = cmd_check()
        sys.exit(0 if ok else 1)
    elif args.cmd == 'sync':
        cmd_sync(args.force)
    elif args.cmd == 'report':
        cmd_report()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()