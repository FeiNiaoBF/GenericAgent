# [L3 SOP] obsidian_library_sop — 图书馆·读书心流SOP (v2.0)
> Vault: `D:\Documents_Learn\Personal\Obsidian\Codex Vitae`
> 单职责：只处理“书籍笔记/阅读心流”。知识库架构见 `vault_knowledge_sop.md`；发布见 `obsidian_blog_sync_sop.md`。

## 执行摘要（≥1步执行前必读）
① 确认书籍与阅读状态 → ② 用 `Templates/Book.md` 建 `03.Library/Books/书名.md` → ③ 记录划线/思考 → ④ 读完提炼核心断言 → ⑤ 运行验证/分类工具 → 🛑

## 1. 触发场景
主人要：找书、建书籍笔记、整理读书批注、把一本书读完归档时激活。

不处理：
- 主题MOC/知识库结构 → `vault_knowledge_sop.md`
- Blog发布 → `obsidian_blog_sync_sop.md`
- 日记追加 → `diary_append.py`
- 全库分类 → `vault_classifier.py`

## 2. 路径与模板
- 书籍笔记路径：`03.Library/Books/书名.md`
- 模板：`Templates/Book.md`
- 一书一文件，禁把多本书混在同一笔记。

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

高价值断言再拆到 `05.Knowledge/`，执行 `vault_knowledge_sop.md`。

## 6. 双链与聚合
- Book笔记至少自然链接到1个相关主题或MOC。
- 多书围绕同一主题时，MOC创建/维护交给 `obsidian_moc_sop.md`。
- 禁为了凑链接添加“相关概念”垃圾区块。

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
| 需要拆出的断言已转 `vault_knowledge_sop.md`？ | |

最终裁定：`VERDICT: PASS` / `VERDICT: FAIL`

