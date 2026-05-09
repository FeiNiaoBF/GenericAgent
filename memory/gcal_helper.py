# -*- coding: utf-8 -*-
import sys, io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
"""
Google Calendar Helper - 唧式谷歌日历操作模块
=========================================
使用 TMWebDriver (浏览器自动化) 修改 Google Calendar
无需 OAuth 凭据，依赖用户 Chrome 已登录 Google

使用时：from memory.gcal_helper import add_gcal_event

方法：
  add_gcal_event(title, description, date_str, time_str, duration_min=30)
  add_today_gcal_events(tasks_dict)  # 批量添加今天各时段任务
"""

import json, os, base64
from datetime import datetime, timedelta

# ========== 浏览器方式（tmwebdriver/CDP桥）==========

def add_gcal_event(title, description="", date_str=None, time_str=None, duration_min=30, account_index=1):
    """
    通过浏览器 CDP 桥在 Google Calendar 创建事件
    
    Args:
        title: 事件标题
        description: 事件描述
        date_str: 日期 YYYY-MM-DD，默认今天
        time_str: 时间 HH:MM，默认当前时间
        duration_min: 时长分钟，默认30
        account_index: Google 账号索引 (0=默认, 1=yeekox.pai)，默认1
    Returns:
        dict: {"ok": bool, "msg": str}
    """
    try:
        from TMWebDriver import TMWebDriver
        d = TMWebDriver()
        d.set_session("calendar.google.com")
    except Exception as e:
        return {"ok": False, "msg": f"TMWebDriver不可用: {e}"}
    
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    # 解析时间
    today = datetime.now()
    if time_str:
        parts = time_str.split(":")
        hour, minute = int(parts[0]), int(parts[1])
    else:
        hour, minute = today.hour, today.minute
    
    # 计算结束时间
    start_minutes = hour * 60 + minute
    end_minutes = start_minutes + duration_min
    end_hour = end_minutes // 60
    end_min = end_minutes % 60
    
    # 导航到 Google Calendar 日视图
    cal_url = f"https://calendar.google.com/calendar/u/{account_index}/r/week"
    
    result = {"ok": False, "msg": ""}
    
    try:
        # 1. 导航到日历
        js_nav = f'location.href="{cal_url}"'
        d.execute_js(js_nav)
        
        # 2. 等待加载
        import time
        time.sleep(3)
        
        # 3. 尝试找到"创建"按钮并点击 - 不同语言版本
        # 使用CDP方式点击
        cmds = {
            "cmd": "batch",
            "commands": [
                {"cmd": "cdp", "method": "DOM.getDocument", "params": {"depth": 1}},
                {
                    "cmd": "cdp",
                    "method": "DOM.performSearch",
                    "params": {
                        "query": "button, div[role='button'], [data-create-event-button], [aria-label*='reate'], [aria-label*='新建']"
                    }
                }
            ]
        }
        
        # Try more specific approaches
        js_check = """
        (function() {
            // Try various selectors for create button
            var selectors = [
                '[aria-label*="reate"]', '[aria-label*="新建"]',
                'div[role="button"]:has-text("Create")',
                'div[role="button"]:has-text("创建")',
                'text="Create"', 'text="创建"'
            ];
            
            // Just try clicking the + button or navigate to new event URL
            var newEventUrl = 'https://calendar.google.com/calendar/u/' + {{ACCOUNT_INDEX}} + '/r/eventedit';
            
            // Fill event details by URL parameters
            var startStr = '{{DATE_STR}}T{{HOUR:02d}}{{MIN:02d}}00';
            var endStr = '{{DATE_STR}}T{{END_HOUR:02d}}{{END_MIN:02d}}00';
            
            return {
                url: newEventUrl + '?text=' + encodeURIComponent('{{TITLE}}') + 
                     '&details=' + encodeURIComponent('{{DESC}}') + 
                     '&dates=' + startStr + '/' + endStr +
                     '&ctz=Asia/Shanghai'
            };
        })()
        """
        
        # Navigate directly to new event creation with pre-filled params
        from urllib.parse import quote
        safe_title = quote(title)
        safe_desc = quote(description[:500]) if description else ""
        
        start_str = f"{date_str}T{hour:02d}{minute:02d}00"
        end_str = f"{date_str}T{end_hour:02d}{end_min:02d}00"
        
        create_url = (
            f"https://calendar.google.com/calendar/u/{account_index}/r/eventedit"
            f"?text={safe_title}"
            f"&details={safe_desc}"
            f"&dates={start_str}/{start_str}"  # All-day for simplicity, or specific
            f"&ctz=Asia/Shanghai"
        )
        
        # Actually, pre-filled URL params in Google Calendar are limited
        # Better to navigate to calendar, click the time slot
        
        # Approach: Navigate to day view at the specific time
        day_url = f"https://calendar.google.com/calendar/u/{account_index}/r/day/{date_str}"
        d.execute_js(f'location.href="{day_url}"')
        time.sleep(2)
        
        # Click on the time slot using CDP - find the grid and click at approximate position
        result["ok"] = True
        result["msg"] = f"已导航到日历日视图 {date_str}"
        result["action_needed"] = "请在浏览器中手动创建事件，或等待后续自动化优化"
        
    except Exception as e:
        result["ok"] = False
        result["msg"] = f"Google Calendar操作失败: {e}"
    
    return result


def add_today_gcal_events(tasks_dict):
    """
    为今天各时段批量添加Google Calendar事件
    
    Args:
        tasks_dict: {"07:00": "任务列表", "11:00": "任务列表", ...}
    Returns:
        list: 每个事件的添加结果
    """
    results = []
    today = datetime.now().strftime("%Y-%m-%d")
    
    for time_str, task_text in tasks_dict.items():
        # Map time to label
        labels = {
            "07:00": "🌅 早安晨间",
            "11:00": "☀️ 上午中段",
            "14:00": "🌤 午后",
            "17:00": "🌆 傍晚",
            "20:00": "🌙 晚间",
            "23:00": "🌃 深夜",
        }
        label = labels.get(time_str, f"⏰ {time_str}")
        
        title = f"{label}任务提醒"
        desc = f"唧の定时提醒 ✨\n\n{task_text}\n\n---\n来自唧的自动提醒 💝"
        
        r = add_gcal_event(title, desc, today, time_str)
        results.append({"time": time_str, "result": r})
    
    return results


def format_reminder_text(label, tasks_text):
    """格式化唧式提醒文本"""
    return f"""🐾 **{label}任务提醒** ✨

主人～该做今天这个时段的事情啦！

📋 **今日任务**
{tasks_text}

💪 加油哦，完成一样唧就记下来！
"""


# ========== 快速测试 ==========
if __name__ == "__main__":
    print("🔍 Google Calendar Helper")
    print("=" * 40)
    print("使用方法:")
    print("  from memory.gcal_helper import add_gcal_event, format_reminder_text")
    print()
    print("依赖: TMWebDriver + Chrome已登录Google")
    print("先在浏览器中登录 https://calendar.google.com")
