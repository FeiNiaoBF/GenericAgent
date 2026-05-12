#!/usr/bin/env python3
"""Google日历管理 - 管理Google日历日程

SOP: gcal_manage_schedule_sop.md
用途: 查询/创建/更新Google日历事件
DIY: 一个脚本只做日历管理(需要credentials)
"""

import datetime, json, os, sys

CONFIG_FILE = 'D:\Creative_Studio\WorkSpace\Github\GenericAgent\config\gcal_config.json'

def check_credentials():
    """检查Google Calendar凭据"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        print(f'✅ 凭据已配置: {config.get("email", "未知")}')
        return True
    print(f'⚠️ 未找到凭据: {CONFIG_FILE}')
    print('   请先配置Google Calendar API凭据')
    return False

def format_event(event):
    """格式化事件显示"""
    summary = event.get('summary', '无标题')
    start = event.get('start', {}).get('dateTime', event.get('start', {}).get('date', '未知'))
    end = event.get('end', {}).get('dateTime', event.get('end', {}).get('date', '未知'))
    return f'  {summary}\n     {start} → {end}'

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Google日历管理')
    parser.add_argument('action', choices=['check', 'list'], help='操作')
    parser.add_argument('--days', type=int, default=7, help='查询天数范围')
    args = parser.parse_args()

    if args.action == 'check':
        check_credentials()
    elif args.action == 'list':
        if not check_credentials():
            sys.exit(1)
        print(f'📅 未来{args.days}天的日程:')
        print('   (需要安装 google-api-python-client)')

if __name__ == '__main__':
    main()
