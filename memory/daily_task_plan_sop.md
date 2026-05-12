# 每日任务 SOP (v1.0)
## 执行摘要
① 先读模板`{vault}/99.System/Templates/Daily.md`确认最新结构→② 三时段(🌅上午/☀️下午/🌙晚上)填任务→③ 新闻播报用daily_news_sop→④ 🛑门禁

## 流程
1. 用户告知任务→整理为三时段清单
2. 读模板→创建/覆盖`{vault}/00.Chronicles/Daily/{YYYY-MM-DD}.md`
3. 填入: frontmatter(type=daily) + 标题(`{{date:YYYY年MM月DD日-dddd}}`) + 🗞️播报 + 待办(checkbox) + 闪念/回顾(骨架) + 🐣唧の足迹
4. 创建定时提醒→回复预览

## 🐣 唧の足迹
触发: 完成用户任务后 | append到`## 🐣 唧の足迹`区块 | 无日记先创建
格式: `- **任务名** — 简述+涉及文件` | ❌不覆盖/不超2行 | ✅多轮=1条/标注文件名

## ⏰ 定时提醒
调用`task_reminder_helper.py`生成json到`../sche_tasks/`，scheduler触发唧提醒
时段映射: 🌅→09:30 | ☀️→13:30 | 🌙→18:30
```python
from memory.task_reminder_helper import create_task_reminders, cleanup_old_reminders
create_task_reminders(date_str="2026-04-26", tasks={"上午":[...],"下午":[...],"晚间":[...]})
cleanup_old_reminders(keep_days=3)
```
提醒: 唧式口吻+任务清单 | 完成后告诉唧→日记勾选✅

## 避坑
- 必须先读模板再创建日记 | 时间块按实际密度填 | 新闻用daily_news_sop三大特性
- 长文→独立笔记+[[双链]]，日记只存摘要+链接 | vault路径见L2

## 🛑 验证门禁
模板已读确认？| 三时段填充？| 长文→独立笔记+双链？
`VERDICT: PASS` / `VERDICT: FAIL`