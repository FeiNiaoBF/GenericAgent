---
name: obsidian_manage_domain
description: 管理Obsidian领域Domain笔记与领域索引
---
# Obsidian Domain 管理 SOP

## 定义与边界
- Domain=长期身份/责任领域；有期限→`01.Quests/`，非项目/任务/知识笔记。
- 路径:`D:\Documents_Learn\Personal\Obsidian\Codex Vitae\02.Domains\`；模板:`99.System\Templates\Domain.md`；FM:`type: domain`，常用`status: active`、`review_cycle: monthly`。
- 架构以`Codex Vitae知识库架构.md`为准；关联:`obsidian_knowledge_sop`、`obsidian_note_wiki_sop`、`obsidian_manage_quest_sop`。
- 小说/创作→`03.Library/Notes/Writing/Fiction/`；仅长期身份在写作Domain保入口。

## 前置门禁
1. 先读模板，禁凭记忆补结构。
2. 列`02.Domains/*.md`确认现有领域，避重复。
3. 改单个Domain前读原文件，保留已验证内容。
4. 合并/删除/不确定保留→先问主人；禁擅自不可逆操作。
5. 读Domain先看标题首句+`身份仪表盘`，一屏确认：我是谁/管什么/不管什么/频率。
6. 整理Domain必须联动`01.Quests/`、`03.Library/`、`05.Knowledge/`。

## 标准骨架
必须贴合 `99.System/Templates/Domain.md`：
```markdown
---
type: domain
status: active
review_cycle: monthly
last_reviewed: YYYY-MM-DD
created: YYYY-MM-DD
tags: [domain]
---
# 领域名
> 一句话描述这个身份——你在这个领域是谁

## 身份仪表盘
| 维度 | 当前定义 |
|---|---|
| 我是谁 | 一句话定义 |
| 这个领域管什么 | 长期责任、能力、关注范围 |
| 不管什么 | 应放到 Quest / Note / Daily 的内容 |
| 维护频率 | monthly / quarterly / none |

## 当前关注
-
## 关联索引
| 类别 | 链接 |
|---|---|
| 行动 | `01.Quests/`相关Quest |
| 笔记 | `03.Library/Notes/`相关笔记 |
| 知识 | `05.Knowledge/`相关断言 |
| 素材 | `03.Library/Sources/`原始材料 |
## 回顾记录
- `YYYY-MM-DD` 创建/调整原因
```

## 迁移与维护
- 领域定位→标题首句；目标/习惯/计划→`当前关注`留有效项；项目→迁移/链接`01.Quests/`；知识/资料→`关联索引`或拆Library/Knowledge；日志→`回顾记录`；大段历史先放`补充记录`或拆链，勿直删。
- 月回顾先读`身份仪表盘`；边界变更改`我是谁/管什么/不管什么`；行动变更只改`当前关注`；新目标建/链Quest；新知识建/链Note/MOC/Knowledge；结构调整在`回顾记录`追加日期+原因。

## 合并经验
- `博客`可作`写作`子方向；若保留`博客.md`，设`status: archived`并跳转`[[写作]]`。
- `编程`是独立爱好/长期身份，不能并入其他Domain。
- 合并前必确认；合并后在保留方`回顾记录`写明；被合并领域按指令删/归档/改普通笔记，禁擅自。

## 验证门禁
- 批量后查：`02.Domains`数量/名称；每篇FM且`type: domain`；active含`身份仪表盘/当前关注/关联索引/回顾记录`；archived跳active并说明原因；`last_reviewed`更新；未混Quest/Note/MOC；合并经验已记录。

## 禁区
- 不读模板按旧印象改；短期项目当Domain；每话题新建Domain；擅删/合并主人明确保留的领域；Domain写成MOC/Note；批量覆盖前不读原文件。
