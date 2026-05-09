# [L3 SOP] vault_knowledge_sop — Obsidian 知识库架构与 GA 协作规范 (v1.0)
> Vault: `D:\Documents_Learn\Personal\Obsidian\Codex Vitae`
> 架构文档: `Codex Vitae知识库架构.md` (v2.1)
> 实现: `../memory/vault_tools.py` (统一接口/search/inspect/move) | `../memory/verify_note.py` (验证门禁) | `../memory/diary_append.py` (日记追加)

## 执行摘要（≥1步执行前必读）
① 从信息源收集→② 99.System/LLM-Drafts/ 写草稿→③ vault_tools.py classify→④ verify_note.py 验证→⑤ vault_tools.py move 移入→⑥ 双链自然生长(禁「相关概念」区块) → 🛑 diary_append.py 收尾

## 1. 触发
主人提到 "知识库/VKB/笔记/Obsidian/收藏/clip/MOC" 或判断答案需要引用来源时。

## 2. 7箱架构

| # | 箱 | 用途 | 写作规则 |
|---|-----|------|---------|
| 00 | Chronicles | 时间线记录(日记/周记) | 时间排序 |
| 01 | Attachments | 附件(图片/PDF) | 只放附件 |
| 02 | Domains | 人生领域(代码/英语/阅读/商业) | 领域级 MOC |
| 03 | Library | 知识资产(思维框架) | 用自己的话 |
| 04 | Projects | 项目文件 | 按项目分 |
| 05 | Knowledge | 验证后的断言 | 一句 assertion |
| 06 | Perspectives | 他人的完整观点 | 注明出处 |
| 07 | Practice | 练习/输出(写作/演讲/代码) | 练习导向 |

路径映射: `02.Domains` → `domain` + `area` | `03.Library` → `subject` + `type` | `05.Knowledge` → `subject` | `06.Perspectives` → `author`

### 03.Library 三区
```
03.Library/
├── Sources/  ← 原文摘录（可保留原文）→ 完读后升级至 Notes
├── Notes/    ← 用自己的话写原子笔记（按 subject 分文件夹：地理/历史/CS/Math/AI/Engineering）
└── Maps/     ← 笔记 ≥ 3~5 篇同 subject 时创建 MOC
```
Clipping流程: 摘原文 → `Sources/` → 读完 → 提炼 `Notes/`(原创) → 验证 → assertion入 `05.Knowledge`

### 05.Knowledge 验证知识库
与03分工: 03=学习/整理(可长篇) vs 05=验证后断言(一句 assertion，至少1来源)
scope边界: 每条 Knowledge 必含 `scope` 字段 — `科普`(对大众的通俗解释) vs `严格`(理论推导结论)，防止将科普解释误当严格知识
知识蒸馏: 多来源→03.Library/Notes→交叉验证→05.Knowledge assertion(含scope)→定期复查

## 3. 属性体系

| 字段 | 用途 | 箱 |
|------|------|----|
| type | 笔记分类(daily/moc/clipping/book/article/prompt/derived) | 全箱 |
| status | 成熟度(seedling/budding/evergreen) | Library/Knowledge |
| domain | 人生领域 link | Domains/Knowledge |
| subject | 学科分类 | Library/Knowledge |
| created/updated | 时间戳 | 全箱 |
| tags | 标签数组 | 全箱 |
| source | 引用双链 `[[书名]]` | Clippings必填 |

> 创建笔记: vault_tools.py template → 写入 99.System/LLM-Drafts/ → 元数据存 SQLite 索引（禁 .md 内 YAML/frontmatter）→ verify_note.py 验证 → vault_tools.py move 移入

## 4. VKB 协作规则
- GA 操作知识库: 用 `vault_tools.py` 作为统一接口（封装 vault_classifier + verify_note + diary_append）
- 创建笔记: 先判断放哪个箱 → vault_tools.py template → 元数据由 vault_classifier 外部索引（SQLite）管理 → code_run 写入草稿到 99.System/LLM-Drafts/
- 元数据: frontmatter 等效字段存于 SQLite 索引，**不注入 .md 正文**（笔记正文禁 YAML；搜索/巡检用索引字段替代 frontmatter 解析）
- 搜索: `vault_tools.py search --keyword "..."` | 巡检: `vault_tools.py inspect` | 移动: `vault_tools.py move <src> <dest>` | 验证: `verify_note.py <path>`
- 每日收尾: `diary_append.py "任务简述"` → 追加到今日日记 🐣 唧の足迹
- 红牌: 地理/历史不放02 | Notes禁例题禁陷阱禁判据(Wiki风知识分析, 3-5KB) | 05只存断言(禁一切考试元素, 300-600B) | Clipping必加source双链 | 书读完必评分 | 凭旧memory判断前先读本文档
- 笔记标准(Wiki风): 事件→背景+前因+过程+决策逻辑+后果+当代意义+关联链 | 概念→定义+思想史来源+逻辑展开+应用场景+概念边界(溶入正文,禁独立节)+关联 | Notes不设"例题/出处/易错/陷阱"节

## 5. MOC 规范 (v3.0)
> 定位: 人工精选导航 + 自动动态索引 + 知识断言入口 + 待探索队列

### ⚠️ 两种MOC模板（★创建前必读，禁止混淆）

| | 顶层MOC（领域领航） | 主题MOC（知识聚合） |
|---|---------|---------|
| **模板** | `99.System/Templates/01-05Cat·LLM版.md` | `99.System/Templates/MOC.md` (v3.0) |
| **定位** | 领域级领航(5大分部+子MOC指向) | 单一知识主题(笔记聚合) |
| **指向** | 指向子MOC `[[子MOC名]]` | 指向笔记 `[[笔记名]]` + Dataview |
| **字段** | 无moc字段 | `moc: "[[所属顶层MOC]]"` |
| **区块** | domain/subjects/顶层关系/增长引擎/7区地图 | v3.0按需(地图边界/精选导航/知识断言/动态索引等) |
| **何时建** | 新学科领域首次建MOC | 领域内某主题≥3篇笔记需聚合时 |

**决策树**: 新学科/领域级→顶层MOC(01-05Cat模板,不填moc) | 领域内某主题→主题MOC(MOC.md v3.0,moc必填)

**🚫 禁手**: 主题MOC禁用顶层MOC模板 | 顶层MOC禁用v3.0模板 | 不区分就建MOC

### 主题MOC YAML 必填
```yaml
type: moc
status: seedling/budding/evergreen
moc: "[[MOC名]]"  # 所属MOC，Dataview contains精准过滤
scope: ""          # 地图边界：本MOC覆盖的知识范围说明
```

### 标准区块 (按需启用)
1. **🗺️ 地图边界** — scope简述 + 核心问题列表 (≥2个驱动性问题，本MOC要回答什么)
2. **📚 精选导航** — 手动精选 ≥3 篇核心笔记 (双链+一句话定位，正文论证中生长)
3. **🧠 知识断言** — 关联 `05.Knowledge/` 断言入口 (Dataview: `FROM "05.Knowledge" WHERE contains(moc, "[[本MOC]]")`)
4. **📊 动态索引** — Dataview 自动发现笔记: `FROM "03.Library/Notes" WHERE contains(moc, "[[本MOC]]") SORT file.mtime DESC`
5. **🔗 概念关系** — 关键概念间的依赖/对比/层级，正文论证非独立区块
6. **🌱 待探索** — 计划笔记/待学主题，标注优先级
7. **🏷️ 子MOC** — Dataview 收集: `FROM "03.Library/Maps" WHERE contains(moc, "[[父MOC]]")`

### Dataview 核心查询
- 精选笔记: `FROM "03.Library/Notes" WHERE contains(moc, "[[本MOC]]") AND status != "seedling" SORT file.mtime DESC`
- 断言入口: `FROM "05.Knowledge" WHERE contains(moc, "[[本MOC]]")`
- 子MOC: `FROM "03.Library/Maps" WHERE contains(moc, "[[父MOC]]") SORT file.mtime DESC`
- Note/Knowledge 模板已内置 `moc` YAML 字段，写笔记时填入所属MOC即可被自动索引

### MOC 总览
[FILE:Codex Vitae/03.Library/Maps/MOC 总览.md] — 静态表格+Dataview双层，顶部提示"切换阅读模式Ctrl+E"

### 创建时机
同subject ≥3~5 篇笔记 | 用户要求 | ≥5 篇孤儿笔记待归类

### 巡检
`vault_classifier inspect --moc` 检查 moc字段/scope/静态表/孤儿(moc字段缺失或不在总览表)
附加检查: `grep -r "moc:" 03.Library/Notes/ 05.Knowledge/ | grep -v "moc: \"\"" ` 验证笔记断言已挂载MOC

### MOC 创建后同步清单 (★闭环必做)
建完MOC后必须同步，否则知识孤岛：
1. **顶层MOC**: 新增 `- [[主题MOC名]]` 精选导航项
2. **Quests三件套** (若有对应Quest): Dashboard→进度更新 | 备考→updated日期 | 备考地图→updated日期
3. **MOC总览**: 新增行到静态表格

### MOC 红牌
🚫 禁只Dataview无手动精选(≥3篇) | 🚫 子MOC必填moc字段 | 🚫 总览必有静态表格fallback | 🚫 笔记≥10→budding, ≥20→evergreen | 🚫 新建MOC必更新总览 | 🚫 禁手写表格列举笔记(Dataview替代) | 🚫 禁空scope | 🚫 禁少核心问题(≥2个) | 🚫 禁不区分顶层/主题MOC就选模板 | 🚫 禁建完MOC不同步顶层MOC+Quests

## 6. 知识域索引
| 域 | 路径 |
|----|------|
| 经济学 | `03.Library/Notes/Economics/`, `05.Knowledge/Economics/` |
| 计算机科学 | `03.Library/Notes/CS/`, `05.Knowledge/CS/` |
| 数学与逻辑 | `03.Library/Notes/Math/`, `05.Knowledge/Math/` |
| 地理 | `03.Library/Notes/地理/`, `05.Knowledge/地理/` |
| 历史 | `03.Library/Notes/历史/`, `05.Knowledge/历史/` |
| AI | `03.Library/Notes/AI/`, `05.Knowledge/AI/` |
| 工程实践 | `03.Library/Notes/Engineering/`, `05.Knowledge/Engineering/` |

> 模板: `99.System/Templates/MOC.md`

## 7. 双链使用原则
> 核心原则：双链从正文论证中自然生长，禁止人工「相关概念」区块。

- **生长规则**：概念名在正文出现 → 就地加 `[[双链]]`；未出现 → 不加。链接是论证的自然延伸，非独立区块的列举。
- **删除规则**：严禁 `## 📎 相关概念` 或类似独立"相关概念"区块。此类区块污染图谱、阻断知识网络的有机生长。
- **零链接正常态**：新建笔记正文未引用其他概念时保持零链接。随知识网络扩张，正文论证自然会引出新链接。
- **回链原则**：GA 仅在自己新写的笔记中添加前向链接；被引用的已有笔记 **不自动回改**（保护存量笔记完整性）。例外：MOC/Domain 索引等专门设计为双向链接的枢纽页，允许回链。

## 8. 资料依据（Notes 必填）
- 每篇 Notes 末尾附 `📚 依据` 区块：来源标题 + 作者 + URL（网页）/ `[[书名]]`（书籍）+ 关键段落引用
- GA 写入前必须从工具调用中获取真实来源 URL/书名，禁止编造
- Knowledge 的 `source` 字段继承自对应 Notes 的 `📚 依据`

## 🛑 验证门禁（执行前/后强制检查）

| 检查项 | 状态 |
|--------|------|
| 笔记类型(Notes/Knowledge/Daily)正确？ | |
| 模板格式完整(无H1无YAML无frontmatter)？ | |
| 双链从正文自然生长(无「相关概念」区块)？ | |
| Knowledge 含 scope 边界标注(科普/严格)？ | |
| Notes 末尾有 📚 依据(真实来源+URL)？ | |
| 路径在Codex Vitae内？ | |
| 草稿已从 99.System/LLM-Drafts 移至正式路径？ | |

最终裁定: 运行 `verify_note.py <path>` → 输出 PASS/FAIL；PASS 后 `vault_tools.py move` 移入正式路径 → `diary_append.py "笔记: <标题>"` 收尾
