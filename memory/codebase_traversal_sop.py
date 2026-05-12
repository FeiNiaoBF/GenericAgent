#!/usr/bin/env python3
"""Codebase遍历 - 遍历和分析代码库结构

SOP: codebase_traversal_sop.md
用途: 递归遍历代码库，输出文件树、统计信息
DIY: 一个脚本只做遍历分析
"""

import os, sys

def walk_codebase(root_dir, exclude_dirs=None, max_depth=5):
    """遍历代码库，生成文件树"""
    exclude_dirs = exclude_dirs or {'.git', '__pycache__', 'node_modules', '.venv', 'venv', '.idea', '.vscode'}
    result = {'dirs': 0, 'files': 0, 'extensions': {}, 'tree': []}
    
    def _walk(dirpath, depth=0):
        if depth > max_depth:
            return
        try:
            entries = sorted(os.listdir(dirpath))
        except PermissionError:
            return
        
        indent = '  ' * depth
        for entry in entries:
            full = os.path.join(dirpath, entry)
            if entry.startswith('.') and entry != '.env':
                if depth > 0:
                    continue
            
            if os.path.isdir(full):
                if entry in exclude_dirs:
                    result['tree'].append(f'{indent}📁 {entry}/ (跳过)')
                    continue
                result['dirs'] += 1
                result['tree'].append(f'{indent}📁 {entry}/')
                _walk(full, depth + 1)
            else:
                result['files'] += 1
                ext = os.path.splitext(entry)[1].lower()
                result['extensions'][ext] = result['extensions'].get(ext, 0) + 1
                result['tree'].append(f'{indent}📄 {entry}')
    
    _walk(root_dir)
    return result

def main():
    import argparse
    parser = argparse.ArgumentParser(description='代码库遍历工具')
    parser.add_argument('path', nargs='?', default='.', help '目标路径')
    parser.add_argument('--depth', type=int, default=5, help='最大深度')
    args = parser.parse_args()

    root = os.path.abspath(args.path)
    if not os.path.exists(root):
        print(f'❌ 路径不存在: {root}')
        sys.exit(1)

    print(f'🔍 遍历: {root}')
    result = walk_codebase(root, max_depth=args.depth)
    
    print(f'\n{"="*50}')
    print(f'📊 统计')
    print(f'  目录: {result["dirs"]}个')
    print(f'  文件: {result["files"]}个')
    print(f'  文件类型:')
    for ext, count in sorted(result['extensions'].items(), key=lambda x: -x[1]):
        icon = '📄' if ext else '(无扩展名)'
        print(f'    {icon} {ext or "无"}: {count}个')
    
    print(f'\n{"="*50}')
    print(f'📂 文件树:')
    print('\n'.join(result['tree']))

if __name__ == '__main__':
    main()
