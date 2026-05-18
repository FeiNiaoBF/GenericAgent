#!/usr/bin/env python3
"""Codex协作 - 与Codex/Claude协作编程

SOP: codex_collaborate_tasks_sop.md
用途: 管理Codex协作任务的创建、执行和提交
DIY: 一个脚本只做协作管理
"""

import json, os, sys

def create_collab_task(description, files=None):
    """创建协作任务"""
    task = {
        'description': description,
        'files': files or [],
        'status': 'created'
    }
    print(f'📋 协作任务已创建')
    print(f'   描述: {description}')
    print(f'   文件: {", ".join(task["files"]) if task["files"] else "无"}')
    return task

def review_code(code_content, language='python'):
    """审查代码质量"""
    issues = []
    
    lines = code_content.split('\n')
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if len(line) > 120:
            issues.append({'line': i, 'type': 'length', 'msg': '行过长 (>120字符)'})
        if stripped.endswith(' ') or stripped.endswith('\t'):
            issues.append({'line': i, 'type': 'trailing', 'msg': '行尾有空格'})
    
    return issues

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Codex协作工具')
    parser.add_argument('action', choices=['create', 'review'], help='操作')
    parser.add_argument('--desc', help='任务描述')
    parser.add_argument('--file', action='append', help='涉及的文件')
    parser.add_argument('--code', help='代码内容(用于review)')
    args = parser.parse_args()

    if args.action == 'create':
        create_collab_task(args.desc or '未命名任务', args.file)
    elif args.action == 'review':
        if not args.code:
            print('❌ review需要 --code')
            sys.exit(1)
        issues = review_code(args.code)
        if issues:
            print(f'⚠️ 发现 {len(issues)} 个问题:')
            for iss in issues:
                print(f'  L{iss["line"]}: {iss["msg"]}')
        else:
            print('✅ 代码干净!')

if __name__ == '__main__':
    main()
