# [L3 SOP] obsidian_manage_library_sop — 图书馆·读书心流/03.Library治理SOP (v2.1)
> Vault: `D:\Documents_Learn\Personal\Obsidian\Codex Vitae`
> 单职责：只处理“书籍笔记/阅读心流”。知识库架构见 `obsidian_knowledge_sop.md`；发布见 `obsidian_blog_sync_sop.md`。

## 执行摘要（≥1步执行前必读）
① 确认书籍与阅读状态 → ② 用 `Templates/Book.md` 建 `03.Library/Books/书名.md` → ③ 记录划线/思考 → ④ 读完提炼核心断言 → ⑤ 运行验证/分类工具 → 🛑

## 1. 触发场景
主人要：找书、建书籍笔记、整理读书批注、整理/重构 `03.Library/`、治理 Library 标签与 MOC 时激活。

不处理：
- 全库架构裁决 → `obsidian_knowledge_sop.md`
- Blog发布 → `obsidian_blog_sync_sop.md`
- 日记追加 → `diary_append.py`
- 全库分类 → `vault_classifier.py`

## 1.1 `03.Library/` 重构原则（干练版）
- 文件夹管主归属：顶层不按学科拆；`Notes/` 才按学科体系组织。
- YAML管筛选：`type/status/tags/moc` 等字段用于过滤，不替代目录。
- MOC管导航：索引页只服务导航；不要建与知识点无关的总MOC。
- 双链管知识关系：正文自然链接概念；禁凑链接。
- `00.Meta/` 与少量特殊 `Notes/` 可排除在内容门禁外，但需说明边界。
- 标签以 `03.Library/Notes/00.Meta/03.Library Tag Taxonomy.md` 为准(全库命名空间)；新造标签必查Taxonomy验证是否存在；旧式标签按 `obsidian_tag_governance_sop` 治理；批量替换后复检清零。
- 临时报告、Backups、Tracking 禁止落在 Vault 内；产物要么归档到正式笔记，要么迁到 Vault 外。

## 2. 路径与模板
- 书籍管理页路径：`03.Library/Books/书名.md`
- 书籍总览页路径：`03.Library/Books/Library Catalog.md`
- 书籍管理页模板：`99.System/Templates/Book.md`
- 从书中拆出的知识/读书笔记模板：`99.System/Templates/Note.md`
- 一书一文件，禁把多本书混在同一笔记。
- `Book.md` 是“私人图书馆的管理页”：管元数据、阅读状态、核心观点、书摘批注、关联沉淀、Dataview 聚合。
- `Library Catalog.md` 是“私人图书馆总览页”：前半只做浏览图书，后半集中放待补元数据/维护清单；不要把书摘正文塞进去。
- `Note.md` 是“从书中拆出的内容页”：管单个概念、观点、章节主题或可复用知识。

## 3. 阅读状态流
`tbr` → `reading` → `done`

读完必须补：评分、完成状态、至少1段读后感或核心收获。

## 4. 批注格式
Obsidian Callout：
```md
> [!quote] 原文摘录
> [!think] 唧的思考/主人的判断
```

原则：原文和思考分开；摘录服务于后续断言，不堆材料。

## 5. 核心断言输出
Book笔记底部保留：
```md
## 💡 核心断言
- [[书名]] 支持的一个明确判断。
```

高价值断言再拆到 `05.Knowledge/`，执行 `obsidian_knowledge_sop.md`。

## 6. Book-Note 联动与 Dataview 聚合
- `Book.md` 负责管理“一本书”：放在 `03.Library/Books/书名.md`。
- `Note.md` 负责承载“从书里拆出的笔记”：优先放在 `03.Library/Notes/` 下的合适学科目录。
- 绑定规则：从某本书拆出的 Note，必须在 YAML 写：`source_book: [[书名]]`。
- Book 页用 Dataview 自动找回相关 Note，推荐查询：
```dataview
TABLE status AS "状态", subject AS "学科", updated AS "更新"
FROM "03.Library/Notes"
WHERE source_book = this.file.link
SORT updated DESC, file.mtime DESC
```
- 任务聚合可用：
```dataview
TASK
FROM "03.Library"
WHERE !completed
  AND (
    source_book = this.file.link
    OR contains(file.outlinks, this.file.link)
  )
GROUP BY file.link
```
- 关键经验：不要让 Book 正文堆满所有章节内容；Book 是目录卡/管理卡，Note 才是可复用知识单元。
- 若 Dataview 找不到 Note，优先检查：① Note 是否在 `03.Library/Notes`；② YAML 是否写了 `source_book: [[书名]]`；③ 书名链接是否与 Book 文件名一致。

## 7. 工具委托
- 分类：`python ../memory/vault_classifier.py --file "书名"`
- 验证：`python ../memory/verify_note.py "<Vault内相对或绝对路径>"`
- 日记收尾：`python ../memory/diary_append.py "读完/整理《书名》"`

## 8. 红牌规则
- 🚫 `00.Inbox/` 暂存超过24h不归类。
- 🚫 frontmatter 中 `type` 乱手填；优先走分类工具。
- 🚫 书籍元数据缺评分/状态。
- 🚫 断言散落在正文里不汇总。
- 🚫 用本SOP处理课程笔记、技术主题笔记、MOC建设。

## 🛑 验证门禁
| 检查项 | 状态 |
|--------|------|
| 路径在 `D:\Documents_Learn\Personal\Obsidian\Codex Vitae` 内？ | |
| 一书一文件？ | |
| 状态/评分已补齐？ | |
| `## 💡 核心断言` 存在且至少1条？ | |
| 双链自然生长且非垃圾链接？ | |
| 需要拆出的断言已转 `obsidian_knowledge_sop.md`？ | |

最终裁定：`VERDICT: PASS` / `VERDICT: FAIL`

