# [L3 SOP] obsidian_library_sop — 图书馆·读书心流SOP
> Vault: `D:\Documents_Learn\Personal\Obsidian\Codex Vitae`
> 架构文档: `Codex Vitae知识库架构.md` (v2.1)

## 执行摘要（≥1步执行前必读）
① 确认书类型(技术/科幻/哲学等)→② 读取对应模板创建笔记→③ 填充断言+底部Dataview+双链至MOC → 🛑 步骤③后必须过验证门禁

## 1. 适用场景
主人要读书/整理Book笔记/需要读书笔记模板时激活。

## 2. 核心流程

```
找书 → 建笔记 → 读书标记 → 提炼断言 → MOC聚合 → Blog发布
```

详细执行委托给阶段A-D（见§3），分类委托给 `vault_classifier.py`。

## 3. 阶段详解

### 阶段A：找书入架
- 路径：`03.Library/Books/书名.md`
- 模板：`Templates/Book.md`
- 填充：frontmatter（评分/状态/封面/标签）、目录、阅读动机

### 阶段B：读书标注
- 划线/批注直接用Obsidian Callout：`> [!quote] 原文` / `> [!think] 思考`
- 状态：`tbr` → `reading` → `done`
- 评分：读完填1-5星

### 阶段C：提炼断言
- 笔记底部 `## 💡 核心断言` 节，每条断言一行
- 双链规则：`[[书名]]` 引用；Book笔记底部Dataview自动发现
- 高价值断言 → 独立卡片 `05.Knowledge/` — 走 vault_knowledge_sop

### 阶段D：MOC主题聚合
多书围绕同一主题时 → `03.Library/Maps/` 下创建 `MOC.md` → 双链汇总 → 可发布Blog

## 4. Type 分类规则
委托 `../memory/vault_classifier.py` 自动分类。类型定义见该脚本注释。
CLI：`python ../memory/vault_classifier.py`（全量）| `--dry-run`（预览）| `--file "关键词"`（单文件）

### 阶段D补充：MOC 模板强制规则
- 写任何 MOC 必须从 `99.System/Templates/MOC.md` 模板起步。
- 模板覆盖4类 MOC：
  - **Category MOC**（如 CS MOC）：启用 `子MOC` 节，用 Dataview 收集子节点
  - **Subject MOC**（如 Economics MOC）：启用 `核心笔记`+`知识断言`，按领域分组
  - **Tech/Tool MOC**：启用 `核心笔记`+`外部资源`，Dataview 按 category 过滤
  - **Resource MOC**：轻量，仅 `外部资源`+Dataview 链接列表
- 硬性要求：`Ctrl+E` 提示行、`核心笔记`节（有笔记时）、至少1个 Dataview 查询、统计 footer。
- 🚫 禁手写表格列举笔记（Dataview 替代）；禁缺少 Ctrl+E 阅读模式提示。

## 5. YAML 坑点
- Tags 用空格缩进列表格式（别用 `[a, b]`）
- 日期 `YYYY-MM-DD`，无引号
- status 必须用脚本定义值（`tbr/reading/done` 等），手填易错

## 6. 红牌规则（禁触）
- 🚫 笔记内容放 `00.Inbox/` 超过24h不归类
- 🚫 不同书笔记混在同一文件
- 🚫 断言不加双链（变成孤立知识孤岛）
- 🚫 frontmatter 中 `type` 手填（用 vault_classifier.py）
- 🚫 书籍元数据缺失（评分/状态至少一项）

## 7. Diary 写作规范
触发：读书完成后。路径：`04.Diary/YYYY-MM-DD-书名简写.md`
内容：阅读时长、感悟（≥1段）、新断言数、下一步行动

## 8. 课程学习笔记

### 课程大纲（quest）
路径：`01.Quests/Active/课程名.md`
frontmatter：`type: quest | status: active | domain: "[[学业]]" | subject: CS | topic: 课程名`

### 学习笔记（blog）
路径：`03.Library/Notes/计算机/主题/笔记.md`
frontmatter：`type: note | status: budding | created: YYYY-MM-DD`
唧第一人称叙事。

### 断言输出
`05.Knowledge/CS/断言.md`（走 vault_knowledge_sop）

## 9. 技术主题笔记
路径：`03.Library/Notes/计算机/{语言或框架}/{主题}.md`
- 中文文件名：`{主概念} - {副标题}.md`
- frontmatter：`type: note | status: budding | created: YYYY-MM-DD | category: 计算机/{语言} | proficiency: 1-5`
- 先建目录再写文件（`os.makedirs`）
- 长篇解释→03，短断言→05.Knowledge/

## 10. 避免常见问题
1. **路径错误**：Vault根 `D:\Documents_Learn\Personal\Obsidian\Codex Vitae`，已记本SOP头部
2. **Type手填** → 走脚本
3. **断言散落** → 必须双链 + 底部Dataview
4. **模板缺失** → 参考 `Templates/Book.md` 和 `Templates/Blog.md`
5. **MOC孤立** → 至少引用2本书才建MOC

## 🛑 验证门禁（执行前/后强制检查）

| 检查项 | 状态 |
|--------|------|
| 笔记类型(Type)正确？ | |
| 模板字段完整(断言+Dataview)？ | |
| 双链出度≥1(关联MOC)？ | |
| MOC引用≥2本书？ | |
| 路径基D:\Documents_Learn\Personal\Obsidian\Codex Vitae？ | |

最终裁定：`VERDICT: PASS` / `VERDICT: FAIL`
