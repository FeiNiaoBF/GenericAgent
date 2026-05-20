---
name: task_backend_manage
description: 管理后台任务、定时任务与任务状态核验
---
# 任务后端 SOP

## 执行摘要
- 启动：读 `history` + `todo`；有未完成条目取一条，无则读 `task_planning.md` 规划。
- 执行：≤30回合，小步验证；禁连续两次选同子任务；价值优先=训练数据无覆盖 × 持久收益。
- 收尾四件套缺一不可：重读本SOP；cwd写报告+记忆更新建议；`complete_task(title, historyline, report_path)`；`set_todo()` 标 `[x]`。

## 路径与 helper
- `autonomous_reports/` 在 `temp/` 下，用 `./autonomous_reports/`。
```python
from task_backend_manage_sop.helper import *
print(get_history(40))
print(get_todo())
```
- 回调：`set_task(desc)`；`set_todo(path, items)`；`complete_task(title, hist, path)`。

## Goal Mode
用户给开放目标+时间预算时，写 `temp/goal_state.json`（或自定义 `GOAL_STATE`）：
```json
{"objective":"用户原话","budget_seconds":10800,"start_time":"<time.time()>","turns_used":0,"max_turns":200,"status":"running"}
```
- `budget_seconds` 最少3小时按需调；`max_turns` 一般200；`status` 必须 `running`。
- 启动：`start /b python agentmain.py --reflect reflect/goal_mode.py`；多实例：`set GOAL_STATE=temp/goal_xxx.json && start /b python agentmain.py --reflect reflect/goal_mode.py`。
- 换模型追加 `--llm_no 1`（从0开始）；手动停止必须精确PID；观察读 `goal_state.json` 或 `temp/model_responses/` 最近尾部。

## 权限边界
- 无需批准：只读探测、cwd内写操作/脚本实验。
- 待审：修改 `global_mem`/SOP、安装软件、外部API、删非临时文件。
- 禁止：读密钥、改核心代码、不可逆危险操作。

## 定时调度器 scheduler
- 实现：`reflect/scheduler.py`；任务目录：`../sche_tasks/`。
- 任务JSON：`{"schedule":"08:00","repeat":"daily","enabled":true,"prompt":"...","max_delay_hours":6}`。
- `repeat`：`daily|weekday|weekly|monthly|once|every_Nh|every_Nd`；`max_delay_hours` 默认6。
- 行为：每120秒轮询 `sche_tasks/*.json`；读上次报告判断今天是否已执行；未执行写入 `temp/task_planning.md` 触发；`once` 执行后冷却100年；报告路径由scheduler注入prompt。
- 创建：在 `sche_tasks/` 建JSON → scheduler触发 → 执行完写报告路径；日志 `sche_tasks/scheduler.log`；`scheduler.health_check()` 返回 `HEALTHY/OVERDUE/DISABLED/NEVER_RUN/ERROR`。

## 验证门禁
报告已写 | history已更新 | TODO已标 `[x]` | 权限合规

`VERDICT: PASS` / `VERDICT: FAIL`
