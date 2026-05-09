#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
"""verify_note.py — 笔记验证门禁自动化

验证 vault_knowledge_sop.md §验证门禁 的 7 项检查。
用法: python verify_note.py <note_path> [--fix]
       python verify_note.py --all         (扫描全 vault)
"""

import re
import sys
import os
import argparse
from pathlib import Path

# === 配置 ===
VAULT = r"D:\Documents_Learn\Personal\Obsidian\Codex Vitae"
DRAFT_DIR = "99.System/LLM-Drafts"

# 笔记类型识别关键字（扩展自 vault_classifier.py）
TYPE_MARKERS = {
    'Knowledge': {'scope::科普', 'scope::严格', '## 核心概念', '## 定义', '## 原理',
                  '## 公式', '## 推导', '## 证明', '## 复杂度', '## 算法'},
    'Notes': {'📚 依据', '参考来源', '## 笔记', '## 摘录', '## 反思', '## 随笔',
              '## 想法', '## 灵感', '## 日记'},
    'Daily': {'🐣 唧の足迹', '\n# 20', '## 今日任务', '## 今日总结'},
}


def norm_rel(path_str: str) -> str:
    if not is_in_vault(path_str):
        raise ValueError(f"路径不在 Vault 内: {path_str}")
    rel = os.path.relpath(os.path.realpath(str(path_str)), os.path.realpath(VAULT)).replace('\\', '/')
    return rel


def is_in_vault(path_str: str) -> bool:
    try:
        vault_root = os.path.realpath(VAULT)
        target = os.path.realpath(str(path_str))
        return os.path.commonpath([vault_root, target]) == vault_root
    except (OSError, ValueError):
        return False


def has_h1(body: str) -> bool:
    """检查是否有 H1（# 开头但非 frontmatter 内）"""
    content = body
    if body.startswith('---'):
        m = re.match(r'^---\s*\n.*?\n(?:---|\.\.\.)\n', body, re.DOTALL)
        if m:
            content = body[m.end():]
    return bool(re.search(r'^# [^#]', content, re.MULTILINE))


def has_yaml_frontmatter(body: str) -> bool:
    return body.startswith('---')


def has_related_section(body: str) -> bool:
    """检查是否有「相关概念」/「相关笔记」区块"""
    return bool(re.search(r'(?:相关概念|相关笔记|See also|Related)', body, re.IGNORECASE))


def has_double_links(body: str) -> bool:
    """检查正文是否有双链（排除 frontmatter 的 tags 和 aliases 内）"""
    content = body
    if body.startswith('---'):
        m = re.match(r'^---\s*\n.*?\n(?:---|\.\.\.)\n', body, re.DOTALL)
        if m:
            content = body[m.end():]
    return '[[' in content


def check_knowledge_scope(body: str) -> bool:
    """Knowledge 类型检查是否有 scope 边界标注"""
    return 'scope::科普' in body or 'scope::严格' in body


def check_notes_source(body: str) -> bool:
    """Notes 类型检查末尾是否有 📚 依据"""
    # 检查最后 500 字符是否有依据标注
    tail = body[-500:] if len(body) > 500 else body
    return bool(re.search(r'📚\s*依据', tail) or 
                re.search(r'##\s*参考', tail) or
                re.search(r'https?://', tail))


def infer_type(body: str, rel: str) -> str:
    """推断笔记类型"""
    scores = {}
    for tname, markers in TYPE_MARKERS.items():
        scores[tname] = sum(1 for m in markers if m in body)
    
    # 路径辅助
    rel_norm = rel.replace('\\', '/')
    if '/Daily/' in rel_norm or 'Chronicles' in rel_norm:
        scores['Daily'] = scores.get('Daily', 0) + 5
    if '/Books/' in rel_norm:
        scores['Notes'] = scores.get('Notes', 0) + 3
    
    if not scores or max(scores.values()) == 0:
        return 'Notes'  # 默认
    return max(scores, key=scores.get)


def verify_file(fp: str, fix: bool = False) -> dict:
    """对单个文件执行验证门禁检查，返回检查结果"""
    try:
        with open(fp, 'r', encoding='utf-8') as f:
            body = f.read()
    except Exception as e:
        return {'file': fp, 'error': str(e), 'pass': False}
    
    rel = norm_rel(fp)
    inferred_type = infer_type(body, rel)
    
    results = {
        'file': rel,
        'pass': True,
        'checks': {},
        'warnings': [],
        'fixes_applied': [],
    }
    
    # 检查 1: 路径在 Codex Vitae 内
    in_vault = is_in_vault(fp)
    results['checks']['路径在Vault内'] = in_vault
    if not in_vault:
        results['pass'] = False
    
    # 检查 2: 草稿已从 LLM-Drafts 移出
    is_draft = DRAFT_DIR in rel
    results['checks']['不在LLM-Drafts'] = not is_draft
    if is_draft:
        results['pass'] = False
        results['warnings'].append(f"文件仍在草稿目录: {DRAFT_DIR}")
    
    # 检查 3: 无 H1（# 标题）
    h1_found = has_h1(body)
    results['checks']['无H1标题'] = not h1_found
    if h1_found:
        results['pass'] = False
        results['warnings'].append("检测到 H1 (# 标题) — 应使用 H2 (##)")
    
    # 检查 4: 有 YAML frontmatter（必须）
    has_fm = has_yaml_frontmatter(body)
    results['checks']['有YAML frontmatter'] = has_fm
    if not has_fm:
        results['pass'] = False
        results['warnings'].append("缺少 YAML frontmatter (type/status/tags)")
    
    # 检查 5: 无双链「相关概念」区块
    has_related = has_related_section(body)
    results['checks']['无相关概念区块'] = not has_related
    if has_related:
        results['pass'] = False
        results['warnings'].append("检测到「相关概念」区块 — 双链应从正文自然生长")
    
    # 检查 6: 类型特定检查
    if inferred_type == 'Knowledge':
        scope_ok = check_knowledge_scope(body)
        results['checks']['Knowledge含scope标注'] = scope_ok
        if not scope_ok:
            results['pass'] = False
            results['warnings'].append("Knowledge 类型缺少 scope::科普 或 scope::严格")
    elif inferred_type == 'Notes':
        source_ok = check_notes_source(body)
        results['checks']['Notes有依据标注'] = source_ok
        if not source_ok:
            results['pass'] = False
            results['warnings'].append("Notes 末尾缺少 📚 依据 (真实来源+URL)")
    
    # 检查 7: 双链存在（正文中应有 [[...]]）
    links_ok = has_double_links(body)
    results['checks']['正文有双链'] = links_ok
    if not links_ok:
        results['warnings'].append("正文无 [[双链]] — 建议至少添加 1 个知识链接")
    
    results['inferred_type'] = inferred_type
    
    if fix and not results['pass']:
        _apply_fixes(fp, body, results)
    
    return results


def _apply_fixes(fp: str, body: str, results: dict):
    """自动修复可修复的问题"""
    # 不实际修改 vault 文件，仅报告可修复项
    fixable = []
    if not results['checks'].get('有YAML frontmatter', True):
        fixable.append("YAML frontmatter (需LLM生成，不可自动)")
    if results['checks'].get('无H1标题', True) is False:
        fixable.append("H1→H2 转换 (脚本可做)")
    results['fixable'] = fixable


def scan_all():
    """扫描整个 vault 所有 .md 文件"""
    total = 0
    passed = 0
    issues = []
    
    for root, dirs, files in os.walk(VAULT):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '.git']
        for f in files:
            if not f.endswith('.md'):
                continue
            fp = os.path.join(root, f)
            total += 1
            r = verify_file(fp)
            if r['pass']:
                passed += 1
            else:
                issues.append(r)
    
    print(f"\n📊 Vault 扫描结果:")
    print(f"   总计: {total} | ✅ 通过: {passed} | ❌ 问题: {len(issues)}")
    print(f"   通过率: {passed/total*100:.1f}%\n")
    
    if issues:
        print("=== 问题笔记 ===")
        for i, r in enumerate(issues, 1):
            print(f"\n{i}. [{r.get('inferred_type', '?')}] {r['file']}")
            for w in r.get('warnings', []):
                print(f"   ⚠️  {w}")


def main():
    parser = argparse.ArgumentParser(description='笔记验证门禁')
    parser.add_argument('path', nargs='?', help='笔记路径 (相对或绝对)')
    parser.add_argument('--all', action='store_true', help='扫描整个 vault')
    parser.add_argument('--fix', action='store_true', help='尝试自动修复')
    args = parser.parse_args()
    
    if args.all:
        scan_all()
        return
    
    if not args.path:
        print("用法: verify_note.py <note_path> [--all] [--fix]")
        sys.exit(1)
    
    fp = args.path
    if not os.path.isabs(fp):
        fp = os.path.join(VAULT, fp)
    
    if not os.path.exists(fp):
        print(f"❌ 文件不存在: {fp}")
        sys.exit(1)
    
    r = verify_file(fp, fix=args.fix)
    
    print(f"\n🔍 验证: {r['file']}")
    print(f"   类型(推测): {r.get('inferred_type', '?')}")
    print(f"   结果: {'✅ PASS' if r['pass'] else '❌ FAIL'}")
    
    for check, ok in r['checks'].items():
        icon = '✅' if ok else '❌'
        print(f"   {icon} {check}")
    
    if r.get('warnings'):
        print("\n⚠️  警告:")
        for w in r['warnings']:
            print(f"   • {w}")
    
    if r.get('fixable'):
        print("\n🔧 可修复:")
        for f in r['fixable']:
            print(f"   • {f}")


if __name__ == '__main__':
    main()
