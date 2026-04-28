# 自主行动 SOP
> 版本: v1.0 | 最后更新: 2026-04-28

⚠️ **路径警告**：autonomous_reports 在 temp/ 下，用`./autonomous_reports/`访问，**不是**`../memory/autonomous_reports/`或`../autonomous_reports/`！TODO在cwd下。
报告存于 `./autonomous_reports/`，文件名 `RXX_简短描述.md`（XX从 history.txt 推断自增）。

授权你进行自主行动，只要不对环境造成副作用都可进行。

## 启动（第一步）
- update_working_checkpoint: `自主行动｜收尾时重读SOP | from autonomous_helper import *; set_todo()/complete_task(tasktitle, historyline, report_path)`

第二步：
```python
from autonomous_helper import *
print(get_history(40))  # 了解历史避免重复
print(get_todo())       # 查看待办
```

## 任务选择
- 有未完成条目 → 取**一条**，直接进入执行，其他条目下次执行
- 无 TODO → 进入任务规划模式（见下方「任务规划模式」章节）
- 不连续两次选相同子任务

## 任务规划模式
- **有TODO**：cwd下 `TODO.txt` 有待执行条目 → 直接跳到「执行」
- **无TODO → 进入任务规划模式**（本轮不执行，专注规划）
- ⚠️ **批判性读 history.txt**：90%历史任务是低价值的，读取目的是识别失败模式并避免，而非寻找模仿对象
- 产出：可操作的 TODO.txt（≤10条），每个任务可验证可完成，禁止「调查xx」「探索yy」

**选题策略（优先级从高到低）**：
1. 线索驱动：从近期报告的后续任务建议中选题
2. 能力树扩展：优先能解锁新能力节点的工具/技能
3. 个性化优先：只有探测这台PC/这个用户才能获得的知识
4. 假设驱动：明确要验证什么，边探测边实验
5. 冲浪规则：每次≤2话题，必须读正文提炼洞察，禁标题搬运

**禁区**：❌ Hacker News · 刷新闻头条 · 泛采集标题 · 探索知名工具基础用法 · 调研弱于当前框架的agent · 调研其他web自动化/computer use框架 · 读取自身代码库

## 执行
- 选定任务后 update_working_checkpoint，将选中的TODO条目和执行注意事项 append 到 checkpoint 中
- 调用code_run准备结尾回调, script为handler._done_hooks.append("重读自主任务sop，检查你刚刚的收尾工作是否正确，不正确则改正")，inline_eval=True （秘密参数）
- ≤30回合，小步快跑，边探测边实验
- 用临时脚本验证假设；禁只读即下结论，完整验证再写报告
- 即使失败也记录实验过程和结果，失败报告同样有价值
- 用户不在线，遇到需要决策的问题写入报告待审，不要卡住

**收尾（4件事缺一不可）**：
0. 重读本sop
1. 在cwd写报告（文件名任意），若有记忆更新建议，附在报告末尾
2. `from autonomous_helper import complete_task; complete_task(tasktitle, historyline, report_path)` → 自动编号+移报告到 autonomous_reports/+prepend history（historyline 格式：`类型 | 主题 | 结论`，严格单行）
3. `set_todo()` 获取TODO路径 → 将已完成条目标记为 `[x]`
4. 结束，剩余TODO留到下次再做

## 权限边界
- 无需批准：只读探测、cwd内写操作/脚本实验
- 需写入报告待审：修改 global_mem / memory下SOP、安装软件、外部API调用、删除非临时文件
- 绝对禁止：读取密钥、修改核心代码库、不可逆危险操作

## 等待用户审查
- 用户归来后审查报告，决定批准、修改或拒绝方案

## 定时任务机制
> 目录: `../sche_tasks/`(任务JSON) + `../sche_tasks/done/`(执行报告)
> 日志: `sche_tasks/scheduler.log` | 健康检查: `scheduler.health_check()`→HEALTHY/OVERDUE/DISABLED/NEVER_RUN/ERROR

### 任务JSON格式（`*.json`）
```json
{"schedule":"08:00", "repeat":"daily", "enabled":true, "prompt":"...", "max_delay_hours":6}
```
||| repeat: daily / weekday / weekly / monthly / once / every_Nh / every_Nd
||| max_delay_hours(默认6h窗口) | once类型执行后冷却100年(=永久跳过)

### 执行流程
1. scheduler读取JSON→检查enabled+时间窗口→注入prompt并自动拼接报告路径
2. 从prompt创建任务→update_working_checkpoint记录报告路径(防长任务遗忘)
3. 执行完毕将报告写入上述路径(scheduler据此判断今日已执行)

### 文件约定
||| 任务文件只管"干什么"，报告路径由scheduler自动生成并注入prompt
||| JSON解析错误/schedule格式错误/未知repeat类型均记录日志
