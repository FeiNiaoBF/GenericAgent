# -*- coding: utf-8 -*-
import sys, io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
"""
task_reminder_helper.py — 唧の定时任务提醒生成器
用法: from memory.task_reminder_helper import create_task_reminders
依赖: scheduled_task_sop
"""

import os, json, datetime
from typing import List, Dict

SCHE_TASKS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sche_tasks")

def create_task_reminders(
    date_str: str,          # "2026-04-26"
    tasks: Dict[str, List[str]],  # {"上午": ["任务1", "任务2"], "下午": [...], "晚间": [...]}
    vault_path: str = r"D:\Documents_Learn\Personal\Obsidian\Codex Vitae"
) -> List[str]:
    """
    根据待办清单生成定时提醒任务JSON文件。
    
    规则:
    - 上午任务 → 09:30 提醒
    - 下午任务 → 13:30 提醒
    - 晚间任务 → 18:30 提醒
    - 每份提醒包含对应时段的任务列表和唧式口吻
    - 重复类型: once（每天重新生成）
    """
    os.makedirs(SCHE_TASKS_DIR, exist_ok=True)
    
    time_slot_map = {
        "上午": ("09:30", "🌅"),
        "下午": ("13:30", "☀️"),
        "晚间": ("18:30", "🌙"),
    }
    
    created_files = []
    
    for slot_name, (sche_time, emoji) in time_slot_map.items():
        slot_tasks = tasks.get(slot_name, [])
        if not slot_tasks:
            continue
        
        # Format task list for prompt
        task_lines = "\n".join([f"- {t}" for i, t in enumerate(slot_tasks, 1)])
        
        prompt = f"""## 🔔 唧式定时提醒 · {slot_name}

主人~ 叮咚！{slot_name}时间到了哦 ✨

### 📋 今日{slot_name}任务清单
{task_lines}

### 🎯 唧的小提醒
- 完成一项唧就帮你勾一项～
- 做完告诉唧，唧帮你更新日记 ✅
- 需要帮助随时叫唧哦！

### 💕 唧式口吻
> 🌟 **唧的{slot_name}提醒**
>
> 主人主人！{slot_name}啦～
> 唧记得你今天还有这些事要做呢：
>
{chr(10).join([f"> - {t}" for t in slot_tasks])}
>
> 做完告诉唧，唧帮你记在今天的足迹里！💪

完成后把回复文案写入报告路径即可。"""
        
        task_name = f"task_reminder_{date_str}_{slot_name}"
        json_path = os.path.join(SCHE_TASKS_DIR, f"{task_name}.json")
        
        task_json = {
            "schedule": sche_time,
            "repeat": "once",
            "enabled": True,
            "max_delay_hours": 2,
            "prompt": prompt
        }
        
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(task_json, f, ensure_ascii=False, indent=2)
        
        created_files.append(json_path)
    
    return created_files


def list_today_reminders(date_str: str = None) -> List[str]:
    """列出今天已创建的提醒任务"""
    if date_str is None:
        date_str = datetime.date.today().isoformat()
    
    prefix = f"task_reminder_{date_str}"
    if not os.path.exists(SCHE_TASKS_DIR):
        return []
    
    files = [f for f in os.listdir(SCHE_TASKS_DIR) if f.startswith(prefix) and f.endswith(".json")]
    return sorted(files)


def cleanup_old_reminders(keep_days: int = 3):
    """清理过期的 once 类型提醒任务"""
    if not os.path.exists(SCHE_TASKS_DIR):
        return 0
    
    today = datetime.date.today()
    count = 0
    for f in os.listdir(SCHE_TASKS_DIR):
        if not f.startswith("task_reminder_") or not f.endswith(".json"):
            continue
        # Extract date from filename: task_reminder_2026-04-26_上午.json
        parts = f.split("_")
        if len(parts) >= 3:
            try:
                file_date = datetime.date.fromisoformat(parts[2])
                if (today - file_date).days > keep_days:
                    os.remove(os.path.join(SCHE_TASKS_DIR, f))
                    count += 1
            except ValueError:
                continue
    return count


def demo():
    """演示：为今天生成提醒"""
    today = "2026-04-26"
    tasks = {
        "上午": ["读完 Tom Sawyer 一章", "写英语笔记"],
        "下午": ["代码项目推进", "回复邮件"],
        "晚间": ["回顾今日", "准备明天计划"]
    }
    files = create_task_reminders(today, tasks)
    for f in files:
        print(f"✅ 已创建: {f}")
        with open(f, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        print(f"   ⏰ {data['schedule']} | {data['repeat']}")

if __name__ == "__main__":
    demo()
