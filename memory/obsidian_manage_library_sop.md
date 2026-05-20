---
name: obsidian_manage_library
description: 管理Obsidian Library书籍目录、模板与Dataview字段
---
# Obsidian Library 管理 SOP
> 管 `03.Library/` 书籍阅读心流。全库→`obsidian_knowledge_sop`，Blog→`obsidian_blog_sync_sop`，日记→`diary_append`。

## 快速流程
确认书籍/状态→读Book模板→建/改Book→填摘录/思考→读完补核心断言→跑验证/分类/信息源→VERDICT。

## 边界与路径
- 触发：找书、建书籍笔记、整理批注、治理`03.Library/Books/`、维护Catalog；不处理课程/技术主题/全库分类/MOC裁决/发布。
- 原则：文件夹管主归属，YAML管筛选，MOC管导航，双链管真实关系；禁凑链接。
- 标签以 `03.Library/Notes/00.Meta/03.Library Tag Taxonomy.md` 为准；新标签先查Taxonomy，旧标签走 `obsidian_tag_governance_sop`。
- Book：一书一文件；Catalog只做浏览维护，禁塞书摘；拆Note放合适目录；临时/Backups/Tracking禁落Vault。

## Book硬门禁
1. 新建/重写Book前必须读取原模板，禁凭记忆复刻。
2. 保留模板章节序：`概要`→`核心观点`→`书摘与批注`→`关联与沉淀`→`Dataview`。
3. 正文只写有据内容：阅读记录、主人提供、原文、出版方简介、Wikidata/Open Library/豆瓣等可核验来源；观点标来源，缺证据写`待阅读后补`。
4. `## 关联与沉淀`必须非空：至少MOC、可拆Note候选、相关来源方向；不确定也写`待阅读后补`+下一步。
5. 写回后复核：章节齐全、关联非空、无虚构书评/断言。

## 阅读输出
- 状态流：`tbr`→`reading`→`done`；读完补评分/完成态/≥1段读后感。
- 批注格式：
```md
> [!quote] 原文摘录
> [!think] 唧的思考/主人的判断
```
- 原文/思考分开；Book底保留`## 💡 核心断言`；高价值断言拆到`05.Knowledge/`并走`obsidian_knowledge_sop`。
- 拆Note：YAML写`source_book: [[书名]]`；Dataview查`WHERE source_book = this.file.link`；查不到核路径/字段/书名链接。

## 工具门禁
- 分类：`python ../memory/vault_classifier.py --file "书名"`
- 验证：`python ../memory/verify_note.py "<Vault内路径>"`
- 日记：`python ../memory/diary_append.py "读完/整理《书名》"`
- 信息源：`python ../memory/obsidian_book_source_enricher.py scan|preview --file "03.Library/Books/书名.md"`；全库预览`preview`；写回`apply --confirm`。
- 信息源写回前必须有可接受preview；只补缺失字段，不覆盖保护字段；写前生成`.bak_book_enricher`；只处理`03.Library/Books/` Markdown；跨目录/批量覆盖/删备份先请示。

## 红牌与验证
- 红牌：`00.Inbox/`超24h；frontmatter`type`乱填；缺状态/评分；断言不汇总；越权处理课程/技术主题/MOC；虚构书评/断言；骨架偏离模板或`关联与沉淀`空。
- 验证：路径在Vault且一书一文件；已读Book模板；骨架一致且关联非空；正文来源可靠；状态/评分/核心断言齐；信息源已preview再apply；双链自然，需拆断言已转知识SOP。

最终裁定：`VERDICT: PASS` / `VERDICT: FAIL`
