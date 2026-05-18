---
name: obsidian_manage_quest
description: 管理Obsidian任务Quest体系与进度记录
---
# Quest 生命周期管理 SOP (v1.0)

> 关联知识库：`obsidian_knowledge_sop.md` → 01.Quests 箱摘要
> 关联模板：`99.System/Templates/Quest.md`
> 关联工具：`vault_tools.py`(分类/移动) | `verify_note.py`(验证) | `diary_append.py`(收尾)

## 执行流程

① 新想法 → 写入 `01.Quests/Someday/` 占位
② 决定执行 → 用模板创建 → 放 `01.Quests/Active/`
③ 定期推进 → 更新 `progress`+`Status` 节
④ 完成 → 创建死链 → 移 `01.Quests/Archives/`
⑤ `vault_tools.py move` + `diary_append.py` 收尾

## 生命周期

| 状态 | 路径 | 条件 |
|------|------|------|
| **Someday** | `01.Quests/Someday/` | 未来可能执行的项目/计划，暂未决定启动；必须仍具备“可转化为行动”的可能 |
| **Active** | `01.Quests/Active/` | 正在进行，有明确目标和完成标准 |
| **Waiting** | `01.Quests/Waiting/` | 阻塞中，等待外部输入/他人 |
| **Done→Archive** | `01.Quests/Archives/` | 完成，创建死链 `→ [[04.Archives/QuestName/QuestName]]` 后物理移至 `04.Archives/` |

> 判定边界：Someday 不是通用灵感箱。纯灵感/素材/片段迁入 `03.Library/Notes/` 或 `03.Library/Sources/`；小说与虚构写作材料独立管理到 `03.Library/Notes/Writing/Fiction/`（目录名用英语）。

## Frontmatter 规范

```yaml
---
type: quest
status: active        # active | waiting | someday | done
priority: ""         # P0/P1/P2/P3 或空
progress: 0          # 0-100 整数
deadline: ""         # YYYY-MM-DD 或空
created: "2026-05-13"
updated: "2026-05-13"
domain: ""           # 所属领域
tags:
  - quest
  - active
aliases:
  - "Quest名称"
---
```

- `type: quest` — 固定值，所有 Quest 统一
- `status` 严格使用 4 种值
- `deadline` 由主人决策；缺失时保持空值或标记待主人设定，助手只整理结构与提醒，禁止编造日期。
- `domain` 与知识库的箱体/领域对应
- `tags` 自动继承 type/status 标签，可追加领域标签

## 写作规则

1. **Mission** — 一句话定位：为什么要做？完成后世界有何不同？
2. **Completion Criteria** — 可验证的关闭条件，全部满足才能关闭
3. **Dashboard** — 进度/优先级/时限/Dataview聚合查询
4. **Status** — 当前阶段、遇到什么坑、什么在阻塞
5. **Action Plan** — 按 Phase 切分，可执行的任务列表
6. **Milestones** — 关键节点跟踪（预期/实际/状态）
7. **Related** — 双向链接关联笔记 + 相关文件路径
8. **Changelog** — 关键决策/状态变更，按时间倒序

## 状态转换规则

- **Someday → Active**：决定启动时，从模板创建新文件，放入 Active/
- **Active → Waiting**：阻塞时标记，在 Status 节说明等待什么
- **Active → Done**：Completion Criteria 全部满足
- **Waiting → Active**：阻塞解除，恢复推进
- **Done → Archive**：创建死链 `→ [[04.Archives/QuestName/QuestName]]`，物理文件移至 `04.Archives/`
- 跨状态迁移后同步更新 `updated` 字段

## 质量门禁

运行 `verify_note.py <path>` 验证：
- [ ] frontmatter 字段完整（type/status/tags/created/updated）
- [ ] status 值合法（active/waiting/someday/done）
- [ ] Mission + Completion Criteria 非空
- [ ] 双链正确，无断裂
- [ ] 📚依据节（若有）附真实来源

验证通过后：
1. `vault_tools.py move <src> <dest>` — 移至正确目录
2. `diary_append.py "Quest <名称> 完成/迁移"` — 日记收尾

## 目录结构

```
01.Quests/
├── Active/          # 进行中
│   ├── 项目A.md
│   └── 项目B/
├── Waiting/         # 等待外部输入
├── Someday/         # 将来想做
└── Archives/        # 已完成(软链接至 04.Archives)
```

> **提示**：Active/ 下超过 5 个活跃 Quest 时建议做优先级排序。每个 Quest 文件大小控制在 3-10KB，过长时拆分子文件至同名目录。
