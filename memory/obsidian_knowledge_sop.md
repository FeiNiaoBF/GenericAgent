---
name: obsidian_knowledge
description: 维护Obsidian知识库架构、箱体分类与知识流转
---
# Vault 知识库架构 SOP (v2.1)
> 实现: `vault_tools.py`|`verify_note.py`|`diary_append.py`
> 架构文档: `Codex Vitae知识库架构.md`(vault根目录，权威依据)

## 执行流程
①收集→②`99.System/LLM-Drafts/`→③对应SOP处理→④vault_tools.py move→⑤日记收尾

## 8箱架构
v1.0→v2.1: 01.Quests取代Projects；MOC独立箱`Maps/`；04.Archives移为只读；03.Library统一Book.md模板骨架
箱号|名称|说明|接口
---|---|---|---
01|Quests|任务/项目|obsidian_manage_quest_sop.md
02|Notes|Wiki笔记|obsidian_note_wiki_sop.md
03|Library|书籍/阅读|obsidian_manage_library_sop.md
04|Archives|已归档(只读)|无
05|Knowledge|领域知识|见下方
06|Maps|MOC/索引|obsidian_manage_moc_sop.md
88|Inbox|收集箱|见下方
99|System|系统/模板|见下方

### 01.Quests
参见`obsidian_manage_quest_sop.md`
生命周期：Inbox→Active→(MOC/Note)→Done→04.Archives(死链)
Done时创建`→ [[04.Archives/...]]`

### 03.Library
参见`obsidian_manage_library_sop.md`
书页必用Book.md模板骨架(工具只填字段不写正文)→信息源填充见`obsidian_book_source_enricher`

### 05.Knowledge
`02.Domains/`下按领域组织，跨领域双链互联
单领域≤100条知识；层次变化直接改文件夹+内容；无大变动不创建MOC

### 88.Inbox
`88.Inbox/`→零整理临时节点→每日处理→48h未处理触发提醒→日常记录用diary

### 99.System
`99.System/`→templates/|LLM-Drafts/|archives/|system/|draw/

## 属性体系
`#知识/已读` `#知识/待读` `#知识/精读` | `#MOC` `#Index` `#Dashboard` | `#领域/[名]` `#类型/[书|文|影|课]`

## 操作接口
统一: `vault_tools.py` | 验证: `verify_note.py` | 日记: `diary_append.py`

## 红牌
- 不创建重复索引/MOC | 不编辑`99.System/templates/`(经SOP审核) | 不修改04.Archives
- OCR/MD正文不混用

## MOC/地图笔记
参见`obsidian_manage_moc_sop.md` | MOC放`Maps/` | 索引层≤3

## 双链原则
参见`obsidian_note_wiki_sop.md`
零链接正常态 | 新笔记加前向链接，已有笔记不自动回改(MOC例外)
Quest Done时创建死链至04.Archives

## 📚依据
Notes末尾必附来源标题+作者+URL/书名 | GA写入前获取真实URL，禁编造

## 验证门禁
Note验证(类型/模板/双链/📚依据)→`obsidian_note_wiki_sop.md`
Knowledge含scope | 路径在Vault内 | 草稿移出LLM-Drafts
Quest Done时检查死链→04.Archives
`verify_note.py <path>`→PASS→`vault_tools.py move`→`diary_append.py`
