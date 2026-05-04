# [L3 SOP] obsidian_library_sop — 图书馆·读书心流SOP
> 版本: v1.4 | 最后更新: 2026-05-04 | 变更: v1.3→新增§9技术主题笔记创建; v1.4→§5新增批量修改避坑(file_patch→Python)
> Vault 路径: `D:\Documents_Learn\Personal\Obsidian\Codex Vitae`
> 架构文档: `Codex Vitae知识库架构.md` (v2.1, Vault根) — 写笔记前必读

## 1. 核心心流 (读书→笔记→发布)
```
读书(设备划线) → Clipping摘录(双链→[[书名]]) → Book随笔/原子笔记(双链关联) → MOC主题聚合 → Blog发布
```

## 2. 图书馆管理 (入馆流程)

### 入馆新书
1. 用 `Book.md` 模板创建 → `03.Library/Books/` 下
2. 必填字段：
   - `dewey`：杜威十进分类（如823/931/005）
   - `status`：to-read / reading / finished / abandoned
   - `rating`：0(未评) / 1★~5★
   - `isbn`：可选但推荐
3. **杜威速查**：
   ```
   000 计算机/总论 | 100 哲学/心理 | 200 宗教
   300 社科 | 400 语言 | 500 自然科学
   600 应用科学/技术 | 700 艺术 | 800 文学 | 900 历史/地理
   ```
4. **Catalog自动展示**：03.Library/Catalog.md 的Dataview按杜威大类分组

### 评分体系 (★)
| rating | 含义 |
|--------|------|
| 5 | 经典必读，影响深远 |
| 4 | 优秀，强烈推荐 |
| 3 | 良好，有所收获 |
| 2 | 一般，略有亮点 |
| 1 | 不值一读 |

## 3. 读书心流操作

### 阶段A：读书中 (设备记录)
- 设备上划线/高亮/批注 → 后续同步

### 阶段B：摘录入库 (Clipping)
1. 用 `Clipping.md` 模板 → `03.Library/Clippings/`
2. **关键规则**：`source: [[书名]]` ← 必须双链回指！否则断链
3. 结构：`## 摘要` + `## 想法`(自己的) + `## 引用`(原文用`>`)
4. tags: `clippings, 书名简写`

### 阶段C：随笔与原子笔记
- **轻量**：Book笔记的 `## 随笔` 区直接写
- **结构化**：创建 `[[书名-主题]]` 原子笔记
  - 用Note模板，tags加 `book, 书名简写`
  - 正文中用 `[[书名]]` 双链引用
  - Book笔记底部Dataview自动发现

### 阶段D：MOC主题聚合
多书围绕同一主题时：
1. 用 `MOC.md` 模板 → `03.Library/Maps/` 下（路径以 `vault_knowledge_sop` §1 为准）
2. 双链汇总所有相关笔记
3. 进一步提炼 → 可发布为Blog文章

## 4. Type 分类规则 (内容分类v2)

> 基于文件内容+路径特征综合推断，不再依赖单一目录位置。
> 分类器脚本: `../memory/vault_classifier.py` (支持全量/dry-run/单文件模式)

### 4.1 类型检测表
| 类型 | 目录信号(路径) | 内容信号(H2/关键词/字段) | 优先级 | 说明 | 典型位置 |
|------|---------------|--------------------------|--------|------|----------|
| template | `/Templates/` | `{{date:}}` 或 `{{title}}` | 0(最高) | 模板文件，不参与内容归档 | `99.System/Templates/` |
| daily | `/Daily/` | `# 202X年M月D日` / `本日待办` / 含checkbox | 1 | 日记/日志 | `00.Chronicles/Daily/` |
| book | `/Books/` | `## 核心摘要/书摘与批注/书评/概要/读书笔记` 或 isbn/dewey字段 | 2 | 读书笔记 | `03.Library/Books/` |
| moc | `/Maps/` | 含DATAVIEW 或 `[[`双链>=3 或 含`总览/索引/目录` | 3 | 主题聚合/索引 | `03.Library/Maps/` |
| project | `/Quests/` | `## 项目定义/项目规划/功能拆解/架构拆解/系统设计` | 4 | 项目笔记 | `01.Quests/` |
| technique | 不限 | `## 步骤/方法/流程/技巧/操作/实现方式/操作步骤/实施` | 5 | 方法论/操作指南 | `02.Domains/` |
| area | `/Domains/` | `[[`双链>=3 | 6 | 领域总览/成熟知识 | `02.Domains/` |
| resource | `03.Library/`(排除Books) | 无特殊H2信号 | 7 | 外部资源/存档 | `03.Library/*/` |
| note | 不限 | 默认兜底(无匹配) | 9(最低) | 原子笔记 | `02.Domains/` |

### 4.2 多类型匹配优先级

文件同时符合多个条件时，**按优先级数字(小→大)判定**，数字最小的胜出：

```
template(0) → daily(1) → book(2) → moc(3) → project(4) → technique(5) → area(6) → resource(7) → note(9)
```

**常见冲突场景**：
- `02.Domains/CS/` 下有方法H2 → **technique** (而非area/note)
- `03.Library/Books/feynman.md` 但无book内容信号 → **note** (不满足book条件则fallback到note，不按目录推断)
- `01.Quests/` 下无checkbox也无项目H2 → **draft** (type保留project，status=draft)

### 4.3 Status 判定 (基于内容特征)

| 值 | 适用type | 判定依据 |
|----|----------|--------------------------|
| draft | note/technique/area/moc/template | 默认状态；短<80字或待完善 |
| completed | daily | 所有checkbox已完成 或 无checkbox |
| in-progress | daily/project | 存在未完成checkbox `[ ]` |
| processed | resource | Library资源默认状态 |
| to-read | book | 无开始/完成标记 |
| reading | book | 有`started_reading`或`## 随笔` |
| finished | book | 有`finished_reading`或`rating:`评分 |
| evergreen | note/moc/area | `[[`双链>=5 且 正文>500字 且 结构化 |
| in-review | note/resource | 含`#review`或`需整理`标记 |

**判定逻辑**：
- Book: to-read(默认) → 有读书记录 → reading → 有评分 → finished
- Daily: 无checkbox → completed, 有checkbox → 全完成=completed, 否则in-progress
- Project: 有未完成checkbox → in-progress, 全完成 → completed, 无checkbox → draft
- Note/resource/technique/area/moc: 正文含`#review`或`需整理`或已有in-review状态 → **in-review**
  - 排除后的note/technique: 双链>=3且>500字 → evergreen, 否则 draft
  - 排除后的area/moc: 双链>=5且>500字 → evergreen, 否则 draft
  - 排除后的resource: → processed

### 4.4 Tags 推断规则

**第一步：目录→tag** | `02.Domains/Computer-science/`→`#cs` | `AI/`→`#ai` | `English/Language/`→`#english` | `History/`→`#history` | `Health/`→`#health` | `Mathematics/Math/`→`#math` | `03.Library/Technology/`→`#technology` | `Business/`→`#business` | `Culture/`→`#culture` | `Psychology/`→`#psychology` | `Philosophy/`→`#philosophy` | `Productivity/`→`#productivity` | `Game/Gaming/`→`#game` | `Reading/`→`#reading` | `Networking/`→`#networking` | 其他非系统目录→原样保留

**第二步：内容关键词→tag** | `#ai`: machine learning, deep learning, llm, gpt, transformer, neural network, 人工智能, 大模型, chatgpt, claude, agent | `#cs`: algorithm, data structure, tcp, http, api, database, 操作系统, 编译, 编程, 代码 | `#english`: vocabulary, grammar, phonetics, pronunciation, 单词, 语法, 音标, 英语 | `#reading`: book, reading, 读书, 阅读, 笔记, 书评 | `#game`: game, gaming, 游戏, rpg | `#development`: project, build, develop, github, 项目, 开发, 部署 | `#productivity`: method, workflow, 效率, gtd, para, 习惯, 时间管理 | `#psychology`: psychology, 心理, 认知, 情绪 | `#history`: history, 历史, 古代, 帝国, 战争 | `#philosophy`: 哲学, philosophy, stoic, 存在主义

**第三步：类型特有tag**（不添加冗余type标签）| daily→`#journal` | book→`#reading` | resource→`#library` | 其他类型→不追加同名tag

去重+按字母排序，全小写英文，`-`连字符，禁中文/点号/大写。

### 4.5 分类器脚本

**Python API**:
```python
from memory.vault_classifier import classify_file
result = classify_file("path/to/file.md")
# 返回: {"rel": "...", "type": str, "status": str, "tags": [...]}
# 一次import内存常驻，批量调用更快
```
**CLI**:
```bash
# 全量扫描+写入 (修改frontmatter中的type/status/tags)
python ../memory/vault_classifier.py

# 预览模式(只扫不写)
python ../memory/vault_classifier.py --dry-run

# 处理特定文件
python ../memory/vault_classifier.py --file "书名关键词"

# 仅统计分布
python ../memory/vault_classifier.py --stats-only
```

## 5. YAML 坑点 (Obsidian Frontmatter)
- ⚠️ **模板变量**：`{{date:YYYY-MM-DD}}` 导致 `yaml.safe_load` 崩溃 → 解析时 try/except 跳过
- ⚠️ **冒号在值中**：`title: The PARA Method: The Simple...` 需要引号包围 → `title: "The PARA Method: The Simple..."` 
- ⚠️ **Daily文件**：`00.Chronicles/Daily/` 下的日记第一次扫描容易漏status，需要单独处理补 `completed`
- ⚠️ **批量修改**：file_patch 对 vault 文件的空格/编码匹配不稳定（多次失败）→ 批量操作(>2文件)直接用 Python `code_run` 读写，避免逐文件 patch

## 6. 红牌规则

> **⚡ 权威红牌**：Vault 级通用禁则参见 [`vault_knowledge_sop` §10 红牌禁则](../memory/vault_knowledge_sop.md)，涵盖 domain/subject 区分、Notes 禁原文、Knowledge 断言句、Clipping 双链、评分体系等。以下仅列 **obsidian_library 独有规则**（读书心流 + 日记写作）：

- ❌ Clipping 忘加 `source: [[书名]]` → 双链断裂（同 vault_knowledge §10 #5）
- ❌ Book 放 Books 外 → Catalog 查不到
- ❌ 只粘贴不写想法 → 沦为搬运工
- ❌ 日记中 `[[文件夹路径/]]` 双链 → 生成垃圾 .md 文件（用纯文本或 `[]()` 代替）
- ❌ 外部链接用双链 `[[GitHub项目]]` → 应使用 `[文字](URL)` 格式
- ❌ 同一条目同时在"今日消化"+"✍️今日笔记" → 只留一处
- ✅ 多用 `[[ ]]` 双链 → 知识网络自然生长
- ❌ 项目/调研类笔记放错位置 → **进行中的 quest → `01.Quests/Active/`**（勿放 Someday 或其他目录），完成后由用户移至对应子目录

## 7. Diary 写作规范（唧专用）

### 7.1 链接三原则
| 场景 | 格式 | 示例 |
|------|------|------|
| 指向 Obsidian 笔记 | `[[笔记名]]` | `[[caveman - AI输出token压缩工具]]` |
| 外部 URL | `[文字](URL)` | `[JuliusBrussee/caveman](https://github.com/...)` |
| 文件夹/节标题 | **纯文本**，不用双链 | `📥 Inbox` 而非 `[[88.Inbox/\|📥 Inbox]]` |

**原理**：`[[88.Inbox/|📥 Inbox]]` 这种写法 Obsidian 会解释为"在 `88.Inbox/` 下链接到 `📥 Inbox.md`"，从而创建一个不存在的垃圾笔记文件。

### 7.2 日记 section 不重复
- 一个笔记只在一个 section 出现：
  - 外部收藏/发现 → `📥 Inbox`
  - 自己写的笔记 → `✍️ 今日笔记`
  - **禁止同一条目两处都出现**

### 7.3 映射速查
| 日记 Section | 放什么 | 链接格式 |
|-------------|--------|---------|
| 📥 今日收藏 | 外部发现的项目/文章 | `[文字](URL)` |
| 📝 今日消化 | 从 Inbox 消化后的笔记 | `[[笔记名]]` |
| ✍️ 今日笔记 | 今天自己写的笔记 | `[[笔记名]]` |
| 文件夹标题 | 纯文本分隔 | 无链接 |

## 8. 课程学习笔记 (Course Learning Notes)

> 新增于 2026-05-02 | 经验来源：Shell 学习（MIT Missing Semester）+ SICP 预习笔记实践

### 8.1 双笔记模式

每开一门新课，创建**两份**笔记，各司其职：

| # | 笔记 | Type | 位置 | 用途 |
|---|------|------|------|------|
| 1 | 课程大纲 | `quest` | `01.Quests/Active/课程名.md` | 课程信息、讲次清单、进度追踪、`progress` 字段 |
| 2 | 学习笔记 | `note` | `01.Quests/Active/主题名.md` | Blog 风格、唧第一人称叙事、代码配解释、顿悟记录 |

**示例**（MIT Missing Semester）：
- 课程大纲：`MIT Missing Semester 2026.md`（type: quest, progress: "L1 Shell 学习中"）
- 学习笔记：`Shell 简要学习.md`（type: note, status: budding）

### 8.2 课程大纲 frontmatter 模板

```yaml
---
type: quest
status: active
created: YYYY-MM-DD
updated: YYYY-MM-DD
domain: "[[学业]]"
subject: CS  # 学科缩写
topic: 课程名
source: "[课程名](URL)"
priority: high  # high | medium | low
progress: "未开始"  # 持续更新
tags:
  - 相关标签
---
```

### 8.3 Blog 学习笔记风格

> 风格参考 → [`yeekox_blog_style_sop` §4 反AI腔调黑名单](../memory/yeekox_blog_style_sop.md)，但不是对外博文，是 Obsidian 内笔记。核心差异见下。

**必须有的元素**：
- 🎙️ **唧第一人称叙事**（"唧の一句话"、"唧の顿悟"、"唧の学习心得"）
- 🧩 **困惑→探索→顿悟 结构**（从一个让你困惑的问题开始）
- 💻 **代码配解释**，不是文档堆砌（每个代码块后必须有唧的解读）
- 🔗 **双链到课程大纲 + VKB 断言卡片**

**style difference from yeekox blog**：
| 维度 | Yeekox 博文（对外） | Blog 学习笔记（对内） |
|------|-------------------|---------------------|
| 受众 | 网络读者 | 主人 + 唧自己 |
| 长度 | 2000-8000字 | 800-3000字即可 |
| 结尾 | Hugo `<!--more-->` 分隔 | `## 下一步` + checklist |
| frontmatter | Hugo配置(title/date/draft/tags) | Obsidian(type/status/domain/subject/topic) |
| 外部链接 | 文末"外部链接"区 | 文末 `## 相关链接` 区，区分双链和URL |
| 语调 | 带个人风味但适度 | 可以更随意，唧の口吻更浓 |

**反AI腔**：同 yeekox_blog_style_sop §4 黑名单，特别注意：
- ❌ "首先/其次/最后/值得注意的是/有着重要意义"
- ✅ "说实话.../我踩坑了.../唧逼自己做实验..."

### 8.4 VKB 提取规则

学习中**验证通过**的概念 → 提取到 `05.Knowledge/{subject}/`：

```
学习笔记中验证的概念（如 2>&1 = dup2(1,2)）
        │
        ▼  满足以下条件：
        │  1. 唧亲手做过实验验证 ✅
        │  2. 能用一句话说清本质 ✅
        │  3. 被坑过一次所以终身难忘 ✅
        ▼
05.Knowledge/CS/Shell redirection dup2 semantics.md
  type: knowledge
  assertion: "2>&1 = dup2(1,2)，一次性快照，不是永久绑定"
  verified_date + verified_by: 唧 + 来源学习笔记双链
```

**触发时机**：不在学习过程中打断心流，而是在**学习笔记收尾时**统一检查"哪些概念值得入VKB"。

### 8.5 完整心流（新课）

```
主人："我要学 X"
  │
  ├─ Step 1: 创建课程大纲 (quest) → 01.Quests/Active/X.md
  ├─ Step 2: 提取课程内容（课程网站抓取/视频目录）
  ├─ Step 3: 学习第一讲 → 创建学习笔记 (note) → 01.Quests/Active/主题.md
  ├─ Step 4: 学习中验证概念 → 写入学习笔记"唧の顿悟"区
  └─ Step 5: 收尾 → VKB提取检查 → 笔记归档
```

---

## 9. 技术主题笔记 (Tech Topic Notes)

> 新增于 2026-05-03 | 经验来源：TypeScript async/await 教程笔记创建

### 9.1 适用场景

独立的技术知识点教程（非课程体系），用户问"给我写个 XX 教程"类需求。与 §8 课程笔记不同——不依赖 quest 驱动，是自学/分享型独立笔记。

### 9.2 分类路径

```
03.Library/Notes/计算机/{语言或框架}/{主题}.md
```

- 子目录按语言分类（如 `TypeScript/`、`Python/`、`Shell/`）
- 中文文件名格式：`{主概念} - {副标题}.md`
- 示例：`异步编程 - async await 详解.md`

### 9.3 Properties 模板

```yaml
---
type: note
status: budding
domain: "[[02.Domains/编程]]"
subject: CS
topic: {一句话主题}
created: {YYYY-MM-DD}
updated: {YYYY-MM-DD}
tags:
  - {语言名小写}
  - {技术关键词}
  - tech/development
---
```

- `type: note` — 长篇学习笔记（非 `resource`/`quest`），用自己话写的教程
- `status: budding` — 结构完善但可进一步打磨；成熟后改 `evergreen`
- `domain` — 固定 `[[02.Domains/编程]]`
- `tags` — 至少语言名（小写）+ 关联技术关键词 + `tech/development`

### 9.4 写作风格

**教程风（通俗易懂，从零讲起）**：
- 从"为什么需要"开始讲动机，而非直接丢定义
- 三代进化式叙述（问题 → 改善 → 最优解），体现演进逻辑
- 代码示例逐步演进，每个代码块配一句白话解释
- 关键技巧用表格速查（如并行/串行选择表、常见坑速查表）
- 结尾附学习路线，用 `[[wikilink]]` 预留后续主题链接
- 背后原理给简版，不深入但给入口

### 9.5 与 §8 课程笔记的区别

| 维度 | §8 课程笔记 | §9 技术主题笔记 |
|------|-----------|---------------|
| 驱动 | 课程（quest） | 独立知识点 |
| 位置 | `01.Quests/Active/` | `03.Library/Notes/` |
| 类型 | `quest` + `note`（双笔记） | `note`（单笔记） |
| 数量 | 每课两份（大纲+学习笔记） | 每主题一份 |
| 进度追踪 | `progress` 字段 | 无（`status` 表示成熟度） |

### 9.6 注意事项

- **先建目录**：语言子目录可能不存在，应先 `os.makedirs` 创建再写入文件
- **笔记 vs 断言**：长篇解释留在 03，短断言卡片在 `05.Knowledge/`（后者除非用户明确要求否则不创建）
- **文件路径**：Vault 根路径 `D:\Documents_Learn\Personal\Obsidian\Codex Vitae`，已记录在 SOP 头部


