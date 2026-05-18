---
name: agent_execute_sop_gate
description: 任务执行前自动识别、读取并引用相关SOP；用于弥补仅靠L1索引不会强制展开L3的执行缺口
---

# Agent执行SOP门禁

## 触发
- 用户任务涉及：Git、记忆、SOP、重构、Obsidian、后台任务、浏览器、代码修改、长程计划。
- 用户明确说：按SOP、检查SOP、使用/goal、规划、提交、推送、重构。
- 连续失败≥2次或工具结果与预期不符。
- 对话中出现可复用的新经验、避坑、环境事实、流程缺口，且已经被工具结果验证。

## 原则
- L1只做索引，不等于已读SOP。
- 决策前必须把候选SOP展开到L3正文。
- 有同名`.py`工具时，优先用工具；不用要说明原因。
- 不凭记忆复述SOP，不用过期摘要替代文件内容。

## 步骤
1. **识别场景**：从用户目标、路径、风险词抽取关键词。
2. **查索引**：先读`global_mem_insight.txt`，必要时读`global_mem.txt`。
3. **定位L3**：找出1-3个最相关SOP；找不到时列出缺口。
4. **读取正文**：用`file_read`读取SOP关键段；复杂/高风险任务读完整文件。
5. **提取门禁**：把触发、禁止项、验证项写入工作记忆。
6. **成长判定**：若产生可复用经验，先读`memory_management_sop.md`，按L1索引/L2事实/L3专项SOP分层；未被工具验证的信息不得写入记忆。
7. **执行任务**：按SOP步骤行动；偏离SOP必须说明理由。
8. **同步索引**：新增/修改L3后，同步`global_mem.txt`可执行细节与`global_mem_insight.txt`极简入口；只改L2时按需同步L1。
9. **闭环验证**：运行SOP要求的验证；失败按“读错误→探测环境→换方案/问主人”。

## 快速映射
- Git/提交/推送 → `git_operate_repository_sop.md`
- 记忆/L1/L2/L3/成长 → `memory_management_sop.md`
- SOP新增/拆分/重命名/去重 → `sop_refactor_sop.md`
- 计划/长程任务 → `plan_manage_task_sop.md` 或 `/plan`相关SOP
- 代码库遍历/项目理解 → `codebase_traverse_repository_sop.md`
- Obsidian知识库 → `obsidian_knowledge_sop.md` + 对应箱体SOP

## 红线
- 禁止只看到L1关键词就宣称“已按SOP”。
- 禁止未读`git_operate_repository_sop.md`就执行push/merge/rebase。
- 禁止未读`memory_management_sop.md`就写L1/L2/L3。
- 禁止未读`sop_refactor_sop.md`就批量重命名/删除SOP。
- 禁止无新信息重复尝试同一失败操作。

## 验证门禁
- 任务回复或工作记忆中出现：已读哪些SOP、采用哪些门禁。
- 相关文件存在且frontmatter包含`name`/`description`。
- L1包含极简入口，L2包含可执行细节。
- 关键操作后有物理验证输出。

`VERDICT: PASS` / `VERDICT: FAIL`
