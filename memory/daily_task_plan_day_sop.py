#!/usr/bin/env python3
"""每日任务计划 - 规划和追踪每日任务

SOP: daily_task_plan_day_sop.md
用途: 创建每日任务清单、追踪进度
DIY: 一个脚本只做任务计划
"""

import datetime, json, os

TASK_FILE = 'D:\Creative_Studio\WorkSpace\Github\GenericAgent\memory\tasks.json'

def load_tasks():
    """加载任务文件"""
    if os.path.exists(TASK_FILE):
        with open(TASK_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_tasks(tasks):
    """保存任务"""
    with open(TASK_FILE, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

def add_task(description, priority='medium', tags=None):
    """添加任务"""
    tasks = load_tasks()
    task = {
        'id': len(tasks) + 1,
        'description': description,
        'priority': priority,
        'tags': tags or [],
        'created': datetime.datetime.now().isoformat(),
        'done': False
    }
    tasks.append(task)
    save_tasks(tasks)
    print(f'✅ 任务已添加 [#{task["id"]}]: {description}')
    return task

def list_tasks(show_done=False):
    """列出任务"""
    tasks = load_tasks()
    pending = [t for t in tasks if not t['done']]
    completed = [t for t in tasks if t['done']]
    
    print(f'📋 任务清单')
    print(f'   待办: {len(pending)} | 完成: {len(completed)}')
    print()
    
    if pending:
        print('⏳ 待办:')
        for t in pending:
            pri = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(t['priority'], '⚪')
            print(f'  #{t["id"]} {pri} {t["description"]}')
    
    if show_done and completed:
        print()
        print('✅ 已完成:')
        for t in completed[-5:]:  # 只显示最近5个
            print(f'  #{t["id"]} ✓ {t["description"]}')

def complete_task(task_id):
    """标记任务为完成"""
    tasks = load_tasks()
    for t in tasks:
        if t['id'] == task_id and not t['done']:
            t['done'] = True
            t['completed_at'] = datetime.datetime.now().isoformat()
            save_tasks(tasks)
            print(f'✅ 任务 #{task_id} 已完成!')
            return True
    print(f'❌ 未找到任务 #{task_id}')
    return False

def main():
    import argparse
    parser = argparse.ArgumentParser(description='每日任务管理')
    parser.add_argument('action', choices=['add', 'list', 'done'], help='操作')
    parser.add_argument('--desc', help='任务描述')
    parser.add_argument('--priority', choices=['high', 'medium', 'low'], default='medium')
    parser.add_argument('--id', type=int, help='任务编号')
    args = parser.parse_args()

    if args.action == 'add':
        if not args.desc:
            print('❌ add需要 --desc')
            sys.exit(1)
        add_task(args.desc, args.priority)
    elif args.action == 'list':
        list_tasks()
    elif args.action == 'done':
        if not args.id:
            print('❌ done需要 --id')
            sys.exit(1)
        complete_task(args.id)

if __name__ == '__main__':
    import sys
    main()
