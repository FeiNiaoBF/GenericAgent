---
name: obsidian_manage_quest
description: 管理Obsidian任务Quest体系与进度记录
---
# Quest 生命周期管理 SOP

## 关联
- 知识库：`obsidian_knowledge_sop.md` 的 `01.Quests` 箱。
- 模板：`99.System/Templates/Quest.md`。
- 工具：`vault_tools.py`(移动/分类)；`verify_note.py`(验证)；`diary_append.py`(收尾)。

## 生命周期
- `Someday` → `01.Quests/Someday/`：未来可能执行；不是灵感箱。
- `Active` → `01.Quests/Active/`：正在推进，有目标与完成标准。
- `Waiting` → `01.Quests/Waiting/`：等待外部输入/他人。
- `Done` → `04.Archives/QuestName/`：完成后先留死链 `→ [[04.Archives/QuestName/QuestName]]`，再物理归档。

边界：纯灵感/素材/片段进 `03.Library/Notes/` 或 `03.Library/Sources/`；小说材料进 `03.Library/Notes/Writing/Fiction/`。

## Frontmatter
```yaml
---
type: quest
status: active   # active | waiting | someday | done
priority: ""    # P0/P1/P2/P3 或空
progress: 0     # 0-100整数
deadline: ""    # 不编造日期
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
domain: ""
tags: [quest, active]
aliases: ["Quest名称"]
---
```
- 状态迁移必须同步 `status/tags/updated`。
- `deadline` 只能用主人给出的日期；缺失时留空或标待定。

## 正文骨架
1. `Mission`：为什么做，完成后改变什么。
2. `Completion Criteria`：可验证关闭条件；全满足才可Done。
3. `Dashboard`：进度/优先级/时限/Dataview。
4. `Status`：当前阶段、坑点、阻塞。
5. `Action Plan`：按Phase拆任务。
6. `Milestones`：预期/实际/状态。
7. `Related`：双链与文件路径。
8. `Changelog`：关键决策倒序。

## 操作流程
1. 新想法：可行动则建 `Someday`；不可行动转Library。
2. 决定启动：套模板建文件，移 `Active`。
3. 推进中：更新 `progress` 与 `Status`。
4. 阻塞：改 `Waiting` 并写清等待对象/条件。
5. 完成：确认 `Completion Criteria` 全满足 → `Done` → 死链 → 移 `04.Archives/`。
6. 收尾：`diary_append.py "Quest <名称> 完成/迁移"`。

## 质量门禁
运行 `verify_note.py <path>`：
- frontmatter字段完整；`status` 合法。
- `Mission` 与 `Completion Criteria` 非空。
- 双链正确；依据节若存在须有真实来源。
- 通过后用 `vault_tools.py move <src> <dest>` 移至正确目录。

## 维护规则
- `Active/` 超过5个时建议优先级排序。
- 单Quest控制3–10KB；过长拆同名目录。

`VERDICT: PASS` / `VERDICT: FAIL`
