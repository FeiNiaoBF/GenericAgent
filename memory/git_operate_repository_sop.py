#!/usr/bin/env python3
"""Git操作 - 执行标准Git操作

SOP: git_operate_repository_sop.md
用途: 常用的Git操作封装: 状态检查/提交/推送/分支管理
DIY: 一个脚本只做Git操作
"""

import subprocess, sys, os

GIT_ROOT = 'D:\Creative_Studio\WorkSpace\Github\GenericAgent'

def _git(*args):
    """执行Git命令"""
    result = subprocess.run(['git'] + list(args), capture_output=True, text=True, cwd=GIT_ROOT)
    if result.returncode != 0:
        print(f'❌ Git错误: {result.stderr.strip()}')
        return None
    return result.stdout.strip()

def status():
    """检查仓库状态"""
    s = _git('status', '--short')
    print('📦 Git状态:')
    if s:
        for line in s.split('\n'):
            print(f'  {line}')
    else:
        print('  ✅ 干净, 无更改')

def branch_current():
    """获取当前分支"""
    branch = _git('rev-parse', '--abbrev-ref', 'HEAD')
    print(f'🌿 当前分支: {branch}')
    return branch

def commit_and_push(message):
    """提交并推送"""
    _git('add', '-A')
    _git('commit', '-m', message)
    branch = _git('rev-parse', '--abbrev-ref', 'HEAD')
    _git('push', 'origin', branch)
    print(f'✅ 已提交并推送到 origin/{branch}')

def diff_summary():
    """差异摘要"""
    diff = _git('diff', '--stat')
    if diff:
        print('📊 变更统计:')
        for line in diff.split('\n'):
            print(f'  {line}')
    else:
        print('  ✅ 无未提交变更')

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Git操作工具')
    parser.add_argument('action', choices=['status', 'branch', 'push', 'diff'], help='操作')
    parser.add_argument('-m', '--message', help='提交信息')
    args = parser.parse_args()

    if args.action == 'status':
        status()
    elif args.action == 'branch':
        branch_current()
    elif args.action == 'push':
        if not args.message:
            print('❌ push需要 -m 提交信息')
            sys.exit(1)
        commit_and_push(args.message)
    elif args.action == 'diff':
        diff_summary()

if __name__ == '__main__':
    main()
