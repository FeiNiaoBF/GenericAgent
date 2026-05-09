#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
"""diary_append.py — 日记追加自动化

向 Codex Vitae/00.Chronicles/Daily/YYYY-MM-DD.md 追加条目
格式: 🐣 唧の足迹 section 下 - HH:MM:: 内容

用法:
  python diary_append.py "今天学习了黑洞热力学"                    # 当前时间
  python diary_append.py "完成代码审查" --time "14:30"             # 指定时间
  python diary_append.py "里程碑: 项目上线" --date 2026-05-04      # 指定日期
  python diary_append.py --stdin                                    # 从标准输入读取
  echo "完成GA优化" | python diary_append.py --stdin

安全: 文件不存在自动创建(含模板框架), section 不存在自动插入
"""

import os
import sys
import argparse
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

HN_SIGNAL_MARKER = "📡 **HN 今日信号**"


VAULT = r"D:\Documents_Learn\Personal\Obsidian\Codex Vitae"
DAILY_DIR = "00.Chronicles/Daily"
SECTION_MARKER = "🐣 唧の足迹"


def get_daily_path(date_str: str = None) -> str:
    """获取日记文件路径"""
    if date_str:
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            print(f"❌ 日期格式错误: {date_str} (需 YYYY-MM-DD)")
            sys.exit(1)
    else:
        dt = datetime.now()
    
    fname = dt.strftime("%Y-%m-%d") + ".md"
    return os.path.join(VAULT, DAILY_DIR, fname)


def create_daily_template(fp: str, dt: datetime):
    """创建日记模板"""
    weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    weekday = weekday_names[dt.weekday()]
    
    template = f"""---
type: Daily
status: active
date: {dt.strftime('%Y-%m-%d')}
weekday: {weekday}
tags: [daily]
---

## 📰 新闻

> 🗞️ **唧式早安播报 · {dt.strftime('%m月%d日')}**

### 🌏 国际

### ♾️ 国内

### 📈 财经

---

## 📡 今日信号

> 信息摄入 · 来自 [[Info-Sources|🗺️信息源MOC]]

---

## ✅ 待办

- [ ] 

---

## 🐣 唧の足迹

- {dt.strftime('%H:%M')}:: 📝 日记创建
"""
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    with open(fp, 'w', encoding='utf-8') as f:
        f.write(template)


def append_entry(fp: str, content: str, time_str: str = None):
    """追加一条日记条目"""
    # 处理 --stdin 的换行符
    content = content.strip()
    if not content:
        print("❌ 内容为空")
        sys.exit(1)
    
    # 支持多行内容，后续行缩进对齐
    lines = content.split('\n')
    first_line = lines[0]
    continuation = '\n  '.join(lines[1:]) if len(lines) > 1 else ''
    if continuation:
        continuation = '\n  ' + continuation
    
    if time_str:
        try:
            datetime.strptime(time_str, "%H:%M")
        except ValueError:
            print(f"❌ 时间格式错误: {time_str} (需 HH:MM)")
            sys.exit(1)
    else:
        time_str = datetime.now().strftime("%H:%M")
    
    entry = f"- {time_str}:: {first_line}{continuation}\n"
    
    if not os.path.exists(fp):
        dt = datetime.strptime(os.path.basename(fp).replace('.md', ''), '%Y-%m-%d')
        create_daily_template(fp, dt)
        print(f"📝 新建日记: {fp}")
    
    with open(fp, 'r', encoding='utf-8') as f:
        lines_list = f.readlines()
    
    # 查找 section marker 所在行
    section_idx = None
    for i, line in enumerate(lines_list):
        if SECTION_MARKER in line:
            section_idx = i
            break
    
    if section_idx is None:
        # 没有 section，在 frontmatter 后插入
        # 找 frontmatter 结束位置
        fm_end = 0
        if lines_list and lines_list[0].startswith('---'):
            for i in range(1, len(lines_list)):
                if lines_list[i].startswith('---'):
                    fm_end = i + 1
                    break
        
        # 在 frontmatter 后插入 section
        section_block = f"\n## {SECTION_MARKER}\n\n{entry}\n"
        lines_list.insert(fm_end, section_block)
    else:
        # 找到 section 后的第一个空行或下一行，在末尾追加
        # 在 section 行后面找到最后一个以 - 开头的行，在其后追加
        insert_pos = section_idx + 1
        last_entry_idx = section_idx
        for i in range(section_idx + 1, len(lines_list)):
            if lines_list[i].startswith('- ') or lines_list[i].startswith('  '):
                last_entry_idx = i
            elif lines_list[i].strip() == '':
                continue
            else:
                # 遇到非条目非空行，停止 (如 ## 其他标题)
                break
            insert_pos = i + 1
        
        # 在最后条目之后插入
        insert_pos = last_entry_idx + 1
        lines_list.insert(insert_pos, entry)
    
    with open(fp, 'w', encoding='utf-8') as f:
        f.writelines(lines_list)
    
    rel = os.path.relpath(fp, VAULT)
    print(f"✅ 已追加到 [{rel}]")
    print(f"   {time_str}:: {first_line}")


def inject_hn_signal(fp: str):
    """抓取HN热点并注入到日记的 📡今日信号 区块"""
    try:
        from hn_daily_fetch import fetch_top_stories, parse_stories, format_for_diary
    except ImportError:
        print("❌ 无法导入 hn_daily_fetch，请确认文件存在于 memory 目录")
        return False

    print("🔄 正在抓取 Hacker News 热点...")
    raw = fetch_top_stories()
    if not raw:
        print("❌ HN API 抓取失败")
        return False

    data = parse_stories(raw)
    if not data:
        print("⚠️ HN 无有效数据")
        return False

    signal_md = format_for_diary(data)

    if not os.path.exists(fp):
        print(f"⚠️ 日记不存在: {fp}")
        return False

    with open(fp, 'r', encoding='utf-8') as f:
        content = f.read()

    if HN_SIGNAL_MARKER not in content:
        print(f"⚠️ 日记中未找到 '{HN_SIGNAL_MARKER}' 标记，跳过注入")
        return False

    # 替换标记为实际HN内容
    new_content = content.replace(HN_SIGNAL_MARKER, signal_md)

    with open(fp, 'w', encoding='utf-8') as f:
        f.write(new_content)

    rel = os.path.relpath(fp, VAULT)
    print(f"✅ HN信号已注入 [{rel}]，共 {len(data)} 条热点")
    return True


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(
        description='日记追加 — 向 Codex Vitae 日记追加 🐣 唧の足迹 条目',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  diary_append.py "今天研究了黑洞信息悖论"
  diary_append.py "午休散步" --time "12:30"
  diary_append.py "项目里程碑" --date 2026-05-01
  echo "GA系统优化完成" | diary_append.py --stdin
        """
    )
    parser.add_argument('content', nargs='?', help='条目内容')
    parser.add_argument('--time', '-t', help='时间 (HH:MM, 默认现在)')
    parser.add_argument('--date', '-d', help='日期 (YYYY-MM-DD, 默认今天)')
    parser.add_argument('--stdin', action='store_true', help='从标准输入读取内容')
    parser.add_argument('--hn', action='store_true',
                        help='抓取HN热点并注入📡今日信号区块')
    args = parser.parse_args()
    
    fp = get_daily_path(args.date)
    
    # --hn 模式：注入HN信号
    if args.hn:
        inject_hn_signal(fp)
        return
    
    # 获取内容
    if args.stdin:
        content = sys.stdin.read()
    elif args.content:
        content = args.content
    else:
        parser.print_help()
        sys.exit(1)
    
    append_entry(fp, content, args.time)


if __name__ == '__main__':
    main()