# Obsidian Domain 管理 · obsidian_manage_domain_sop
> 单职责：管理 Codex Vitae 的 `02.Domains/` 领域文件。Vault架构见 `obsidian_knowledge_sop.md`，Note规范见 `obsidian_note_wiki_sop.md`，Quest规则见 `obsidian_manage_quest_sop.md`。

## 一、Domain 定义

Domain 是长期身份/责任领域，不是项目、任务或知识笔记。

- 目录：`D:\Documents_Learn\Personal\Obsidian\Codex Vitae\02.Domains\`
- 模板：`D:\Documents_Learn\Personal\Obsidian\Codex Vitae\99.System\Templates\Domain.md`
- `type` 固定为 `domain`
- `status` 通常为 `active`
- `review_cycle` 通常为 `monthly`

## 二、创建/优化前置

1. 先读取真实模板，禁止凭记忆补结构。
2. 先列出 `02.Domains/*.md`，确认现有领域，避免重复。
3. 修改单个 Domain 前先读原文件，保留已验证内容。
4. 不确定是否合并/删除领域时先问主人；领域合并属于知识结构决策。
5. 读 Domain 时先看标题下一句话和 `身份仪表盘`，一屏内确认“我是谁 / 这个领域管什么 / 不管什么 / 维护频率”。
6. Domain 只负责长期身份与边界；有期限、有完成标准的事项，转入 `01.Quests/`。
7. 整理 Domain 必须同时看 `01.Quests/`、`03.Library/`、`05.Knowledge/` 的关联；以 vault 根目录 `Codex Vitae知识库架构.md` 为权威依据，禁止把 Domain 当孤立文件夹维护。
8. 小说/创作素材不默认放 Domain；小说独立管理到 `03.Library/Notes/Writing/Fiction/`（文件夹用英语），只有长期身份边界才在写作相关 Domain 中保留入口链接。

## 三、模板结构

Domain 文件必须贴合 `99.System/Templates/Domain.md`：

```markdown
---
type: domain
status: active
review_cycle: monthly
last_reviewed: YYYY-MM-DD
created: YYYY-MM-DD
tags:
  - domain
---

# 领域名

> 一句话描述这个身份——你在这个领域是谁

---

## 身份仪表盘

| 维度 | 当前定义 |
|------|----------|
| 我是谁 | 这个身份的一句话定义 |
| 这个领域管什么 | 长期责任、能力、关注范围 |
| 不管什么 | 应该放到 Quest / Note / Daily 的内容 |
| 维护频率 | monthly / quarterly / none |

---

## 当前关注

-
-

---

## 关联索引

| 类别 | 链接 |
|------|------|
| 行动 | `01.Quests/` 下与此领域相关的 Quest |
| 笔记 | `03.Library/Notes/` 下的相关笔记 |
| 知识 | `05.Knowledge/` 下的相关断言 |
| 素材 | `03.Library/Sources/` 下的原始材料 |

---

## 回顾记录

- `YYYY-MM-DD` 创建本领域
```

## 四、旧内容迁移规则

优化旧 Domain 时按“保留内容、重组结构”处理：

- 原来的领域介绍/定位：压缩进标题下方的一句话描述。
- 原来的目标、习惯、计划：归入 `## 当前关注`，只保留当前仍有效的关注点。
- 原来的项目清单：不要塞进 Domain 正文，优先迁移/链接到 `01.Quests/`。
- 原来的知识/资料链接：放在 `## 关联索引` 表格或其后的补充区块。
- 原来的日志/变更说明：迁入 `## 回顾记录`，用日期列表保留。
- 大段历史资料不要删除；若不适合模板主结构，放在 `## 补充记录` 或拆到 Library/Knowledge 后链接。

## 五、后续维护方式

Domain 的用途是帮助主人持续关注身份和角色，不是存放任务清单：

1. 月度回顾时，先读 `身份仪表盘`，确认这个身份是否仍然成立。
2. 若身份边界变化，优先更新 `我是谁 / 这个领域管什么 / 不管什么`。
3. 若只是近期行动变化，只更新 `当前关注`，不要把 Domain 写成项目计划。
4. 新出现的具体目标，建立或链接到 `01.Quests/`，不要堆在 Domain 正文。
5. 新出现的知识沉淀，建立或链接到 Note/MOC/Knowledge，不要把 Domain 写成知识文章。
6. 每次结构性调整都在 `回顾记录` 追加日期与原因。

## 六、领域合并经验

- `博客` 可作为 `写作` 的子方向，不单独保留 active Domain。
- `博客.md` 若保留文件，应作为 `status: archived` 的历史跳转页，正文明确“已合并至 [[写作]]”。
- `编程` 是主人的独立爱好/长期身份，不能并入其他 Domain。
- 合并 Domain 前必须得到主人明确确认。
- 合并后要在保留方 `回顾记录` 写明合并动作。
- 被合并领域若仍存在文件，需根据主人指令删除、归档或改为普通笔记；不可擅自不可逆删除。

## 七、验证门禁

批量优化完成后必须验证：

1. `02.Domains` 下 Domain 文件数量和名称符合预期。
2. 每个文件都有 frontmatter，且 `type: domain`。
3. active Domain 必须包含：`身份仪表盘`、`当前关注`、`关联索引`、`回顾记录`。
4. archived Domain 可作为历史跳转页保留，但必须明确指向合并后的 active Domain，并说明归档原因。
5. `last_reviewed` 更新为本次处理日期；archived 跳转页可保留归档日期语义。
6. 没有把 `Quest/Note/MOC` 的结构混入 Domain。
7. 合并经验已体现在相关 Domain 的回顾记录中。

## 八、禁区

- ❌ 不读模板就按旧印象改。
- ❌ 把短期项目当 Domain。
- ❌ 为每个话题都新建 Domain。
- ❌ 擅自删除/合并主人明确要保留的领域。
- ❌ 把 Domain 写成 MOC 索引页或 Note 知识文章。
- ❌ 批量覆盖前不读取原文件。
