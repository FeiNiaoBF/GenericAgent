# 🔧 任务后端 SOP (v1.2)
> 含：自主执行 + 定时调度器 (scheduler)
> 单职责：后台任务/定时/自主执行的启动、记录、收尾。

## 执行摘要
① 启动→读history+todo→② 选任务执行≤30回合→③ 收尾四件套 → 🛑

## ⚠️ 路径
`autonomous_reports/` 在 **temp/** 下，用 `./autonomous_reports/`

## §1 启动+任务选择
```python
from task_backend_manage_sop.helper import *
print(get_history(40))  # 历史避免重复
print(get_todo())       # 当前待办
```
- 有未完成条目→取一条执行 | 无→读`task_planning.md`规划
- 禁连续两次选相同子任务 | **价值公式**：训练数据无覆盖 × 持久收益

## §2 执行规范
- ≤30回合，小步快跑，临时脚本验证假设
- 失败也记录过程 | 需决策问题写入报告待审

## §3 收尾（4件缺一不可）
0. 重读本SOP | 1. cwd写报告+记忆更新建议
2. `complete_task(title, historyline, report_path)` | 3. `set_todo()`标`[x]`

## §4 Goal Mode
用户给开放目标+时间预算 → 设置 `temp/goal_state.json`（或自定义 `GOAL_STATE` 路径）:
```json
{"objective":"用户原话","budget_seconds":10800,"start_time":"<time.time()>","turns_used":0,"max_turns":200,"status":"running"}
```
- `budget_seconds`: 最少3小时按需调 | `max_turns`: 防空转一般200 | `status`: 必须`running`
- 启动: `start /b python agentmain.py --reflect reflect/goal_mode.py`
- 多实例: `set GOAL_STATE=temp/goal_xxx.json && start /b python agentmain.py --reflect reflect/goal_mode.py`
- 换模型: 追加 `--llm_no 1`（编号从0开始）
- 停止: 预算耗尽自动收口；手动停需精确PID杀进程
- 观察: 读`goal_state.json`的`turns_used`/`status` | 详情看`temp/model_responses/`最近文件尾部

## §5 权限边界
| 级别 | 操作 |
|------|------|
| 无需批准 | 只读探测、cwd内写操作/脚本实验 |
| 待审 | 修改global_mem/SOP、安装软件、外部API、删非临时文件 |
| 禁止 | 读密钥、改核心代码、不可逆危险操作 |

## §6 回调速查
| 回调 | 调用 |
|------|------|
| `set_task` | `helper.set_task(desc)` |
| `set_todo` | `helper.set_todo(path, items)` |
| `complete_task` | `helper.complete_task(title, hist, path)` |

## §7 定时调度器（scheduler）
> 实现：`reflect/scheduler.py` | 任务目录：`../sche_tasks/`（尚未部署）

### 任务JSON格式（`*.json`→`sche_tasks/`）
```json
{"schedule":"08:00", "repeat":"daily", "enabled":true, "prompt":"...", "max_delay_hours":6}
```
- **repeat**：`daily` | `weekday` | `weekly` | `monthly` | `once` | `every_Nh` | `every_Nd`
- **max_delay_hours**（可选，默认6）：超过schedule多少小时后不再触发

### 行为规范
1. scheduler每 **120秒** 轮询 `sche_tasks/*.json`
2. 启用任务→读上次报告文件→check今天是否已执行→未执行则触发
3. 触发方式：写入 `temp/task_planning.md` 令agentmain下一轮读取
4. `once` 任务执行后冷却100年
5. 报告路径由scheduler自动生成注入prompt

### 任务创建步骤
1. 在 `sche_tasks/` 下建JSON → 2. scheduler自动触发 → 3. 执行完写入报告路径
4. scheduler靠报告文件判断当天是否已执行

### 日志与监控
- 日志：`sche_tasks/scheduler.log`（触发/跳过/错误）
- `scheduler.health_check()` 返回任务状态列表（HEALTHY/OVERDUE/DISABLED/NEVER_RUN/ERROR）

## 🛑 验证门禁
报告已写 | history已更新 | TODO已标`[x]` | 权限合规

`VERDICT: PASS` / `VERDICT: FAIL`
