# Vault 知识库架构 SOP (v2.1)
> Vault: `D:\Documents_Learn\Personal\Obsidian\Codex Vitae`
> 实现: `vault_tools.py`(统一接口) | `verify_note.py`(验证) | `diary_append.py`(日记追加)
> 架构文档: `Codex Vitae知识库架构.md`(vault根目录，此SOP的权威依据)

## 执行流程
①收集素材→②`99.System/LLM-Drafts/`写草稿→③`vault_tools.py classify`→④`verify_note.py`验证→⑤`vault_tools.py move`→⑥双链自然生长→⑦`diary_append.py`收尾

## 8箱架构
| # | 箱 | 用途 | 写作规则 |
|---|-----|------|---------|
|00|Chronicles|日记/周记/徒步记录|按日期存档，模板化|
|01|Quests|项目/任务(含生命周期)|Active→Waiting→Someday/Done→死链至04|
|02|Domains|人生领域(代码/英语/阅读等)|文件拍平，MOC在目录层|
|03|Library|知识资产(书籍/笔记/地图)|5子区：Books+Notes+Maps+Clippings+SignalSources|
|04|Archives|已完成Quest归档|Quest Done后移入，保留死链|
|05|Knowledge|验证后断言|一句assertion+scope(科普/严格)|
|88|Inbox|待分类着陆区|临时存放，定期清理→对应箱|
|99|System|模板/脚本/草稿/追踪|Templates/Scripts/LLM-Drafts/Tracking|

**跨版本变化说明**（v1.0→v2.1）：
- 移除：`01.Attachments`(附件归入各箱)／`04.Projects`(改为01.Quests+04.Archives)／`06.Perspectives`(归入03)／`07.Practice`(归入02)
- 新增：`01.Quests`(生命周期)／`04.Archives`(归档)／`88.Inbox`(着陆区)／`99.System`(系统)
- 路径映射：`02`→domain名称 | `03`→subject+类型 | `05`→subject

### 01.Quests 任务生命周期
- **Active**：进行中项目，放在01.Quests根
- **Waiting**：等待外部输入，标记 `status: waiting`
- **Someday**：未来可能执行的项目/计划，标记 `status: someday`；不是通用灵感箱
- **Done**：完成后创建死链 `→ [[04.Archives/QuestName/QuestName]]`，物理文件移至04
- 每个Quest含frontmatter(type/status/tags/created/updated) + 笔记正文
- 缺少 `deadline` 时由主人设定，助手保持空值/待设定并提醒，禁止编造日期
- Quest完整生命周期管理（模板/状态转换/验证/归档）见 `obsidian_manage_quest_sop.md`

### 03.Library 五子区
- `Books/`：完整书摘/书评，含isbn/dewey字段
- `Notes/`：主题笔记(按subject分：地理/历史/CS/Math/AI/Engineering等)
- `Notes/Writing/Fiction/`：小说与虚构写作材料独立区，文件夹名使用英语；不默认放入Domain/Quest
- `Maps/`：MOC(同subject≥3-5篇时创建)
- `Clippings/`：简短摘录/片段，快速收集
- `SignalSources/`：信号源原文(资讯/文章/播客)，完读后提炼至Notes/
- Clipping流程：原文→SignalSources/→提炼Notes/→assertion入05.Knowledge
- Note书写规范(类型填充/双链/模板/风格)见 `obsidian_note_wiki_sop.md`
- Notes不设"例题/出处/易错/陷阱"节

### 05.Knowledge
与03分工：03=学习整理(可长篇) vs 05=验证断言(一句,≥1来源)
每条必含`scope`：科普(通俗) vs 严格(理论推导)

**子目录结构（按subject分）**：`CS/`／`Economics/`／`History/`／`法律/` 等

⚠️ **路径映射一致性**: `vault_tools.py` 中 `TYPE_TO_DIR` 必须与 Vault 真实目录一致。修改目录结构时同步更新脚本映射。

### 88.Inbox 着陆区
- 临时存放所有待分类笔记
- 定期巡检→分类移至对应箱
- 禁长期滞留(超过30天需标记)

### 99.System 系统区
- `Templates/`：笔记模板(Daily/Note/Quest/Book等)
- `Scripts/`：vault内部脚本
- `LLM-Drafts/`：GA草稿暂存区(流程②)
- `Tracking/`：追踪清单/看板

## 属性体系
type/status/created/updated/tags→全箱必填(frontmatter) | domain/subject→Library/Knowledge | source→Clippings必填
✅元数据存笔记.md的frontmatter(YAML)，**禁止双重存储**（不另建SQLite索引）
**Tags规则**：全小写 | 类型/主题标签从frontmatter自动继承 | 禁CamelCase标签

## 操作接口
搜索：`vault_tools.py search --keyword "..."` | 巡检：`vault_tools.py inspect` | 移动：`vault_tools.py move <src> <dest>` | 验证：`verify_note.py <path>`
收尾：`diary_append.py "任务简述"`

## 红牌
🚫地理/历史不放02 | Notes禁例题/陷阱/判据(Wiki风,3-5KB) | 05只存断言(禁考试元素,300-600B) | Clipping必加source | 书读完必评分 | 88.Inbox禁长期滞留

## MOC/地图笔记
MOC创建、模板、字段、同步清单见 `obsidian_manage_moc_sop.md`。
`03.Library/Maps` 只在同subject≥3-5篇或领域导航需要时创建，禁用MOC替代正文自然双链。

## 双链原则
双链规范（嵌入双链/禁"相关概念"区块）见 `obsidian_note_wiki_sop.md`。
核心原则：零链接正常态 | 新笔记加前向链接，已有笔记不自动回改(MOC例外)
Quest Done时创建死链至04.Archives

## 📚依据
Notes末尾必附来源标题+作者+URL/书名 | GA写入前必须获取真实URL，禁编造

## 验证门禁
Note格式/内容验证（类型/模板/双链/📚依据）见 `obsidian_note_wiki_sop.md`。
Knowledge含scope | 路径在Vault内 | 草稿已移出99.System/LLM-Drafts
Quest标记Done时检查死链指向04.Archives
运行`verify_note.py <path>`→PASS后`vault_tools.py move`→`diary_append.py`收尾
