# 定时任务 SOP (v1.0)

目录：`../sche_tasks/` 放任务定义JSON，`../sche_tasks/done/` 放执行报告

## 执行摘要（≥1步执行前必读）
① 查任务JSON(enabled/schedule/prompt)→② 等调度器触发或手动执行→③ 写报告到done/ → 🛑 过验证门禁。调度器不触发先查端口50123

## 任务JSON格式（*.json）
```json
{"schedule":"08:00", "repeat":"daily", "enabled":true, "prompt":"...", "max_delay_hours":6}
```
repeat可选：daily | weekday | weekly | monthly | once | every_Nh（每N小时）| every_Nd（每N天）
max_delay_hours（可选，默认6）：超过schedule多少小时后不再触发，防止开机太晚执行过时任务

## 触发流程
1. scheduler.py（reflect/）每60秒轮询 sche_tasks/*.json
2. 条件全满足才触发：enabled=true + 当前时间≥schedule + 冷却时间已过（基于done/最新报告时间戳）
3. 触发时拼prompt，含报告路径 `../sche_tasks/done/YYYY-MM-DD_任务名.md`
4. **收到任务后第一件事**：用 update_working_checkpoint 记录报告目标文件路径，防止长任务执行中遗忘
5. 执行完毕后将报告写入上述路径（scheduler靠此文件判断今天已执行）

## 日志与监控
- scheduler自动写日志到 `sche_tasks/scheduler.log`（触发/跳过/错误）
- `scheduler.health_check()` 返回所有任务状态列表（HEALTHY/OVERDUE/DISABLED/NEVER_RUN/ERROR）
- JSON解析错误、schedule格式错误、未知repeat类型均会记录日志

## 设计原则：脚本先行 (Script-First)
> 已验证：Google News RSS + HN Firebase API 均秒级稳定返回，远优于浏览器方案
- **新建定时数据采集任务时，优先搜索 API/RSS → 无API才考虑浏览器**
- 标准三层: `memory/{name}_fetch.py`(数据脚本) → `sche_tasks/{name}.json`(定时) → `memory/{name}_sop.md`(可选)
- 脚本须可独立运行 (`python xxx.py` 直接出数据)，方便手动测试和调试
- 参考: `memory/daily_news_fetch.py`, `memory/hn_daily_fetch.py`, `memory/signal_source_sop.md`

## 注意
- once类型：执行一次后冷却100年（实际效果为永久跳过）
- 任务文件只管"干什么"，报告路径由scheduler自动生成注入prompt
- sche_tasks目录在../，即code root下

## 故障排查 (Troubleshooting)
调度器不触发任务时，按以下三步排查：
1. **查进程**: `netstat -ano | findstr ":50123"` — 无输出说明调度器未启动
2. **查日志**: `sche_tasks/scheduler.log` 尾行，看 TRIGGER（触发）/ SKIP（跳过）/ 无新条目（未运行）
3. **手动验证**: 用console python（非pythonw）运行 `importlib.import_module('reflect.scheduler').check()`，排除文件缓冲导致的日志延迟
- 常见根因: hub.pyw在boot_config被禁用但未创建独立scheduler条目 → 需 `boot/run_scheduler.py` + boot_config.json 配对
- 端口冲突: 50123已被占用说明调度器在运行（OK），勿杀

## 🛑 验证门禁（执行前/后强制检查）

| 检查项 | 状态 |
|--------|------|
| 任务JSON格式正确(enabled/schedule/prompt)？ | |
| 调度器端口50123可达？ | |
| 执行报告已写入done/？ | |
| 故障已查scheduler.log？ | |

最终裁定：`VERDICT: PASS` / `VERDICT: FAIL`