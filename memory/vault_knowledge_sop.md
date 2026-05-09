# Vault 知识库架构 SOP (v1.0)
> Vault: `D:\Documents_Learn\Personal\Obsidian\Codex Vitae`
> 实现: `vault_tools.py`(统一接口) | `verify_note.py`(验证) | `diary_append.py`(日记追加)

## 执行流程
①收集→②99.System/LLM-Drafts/写草稿→③vault_tools.py classify→④verify_note.py验证→⑤vault_tools.py move→⑥双链自然生长→⑦diary_append.py收尾

## 7箱架构
| # | 箱 | 用途 | 写作规则 |
|---|-----|------|---------|
|00|Chronicles|日记/周记|时间排序|
|01|Attachments|图片/PDF|只放附件|
|02|Domains|人生领域(代码/英语/阅读/商业)|领域级MOC|
|03|Library|知识资产(思维框架)|用自己的话|
|04|Projects|项目文件|按项目分|
|05|Knowledge|验证后断言|一句assertion|
|06|Perspectives|他人完整观点|注明出处|
|07|Practice|练习/输出|练习导向|

路径映射：`02`→domain+area | `03`→subject+type | `05`→subject | `06`→author

### 03.Library 三区
- `Sources/`：原文摘录→完读后升级至Notes
- `Notes/`：原子笔记(按subject分：地理/历史/CS/Math/AI/Engineering)
- `Maps/`：同subject≥3-5篇时创建MOC
Clipping流程：原文→Sources/→提炼Notes/→assertion入05.Knowledge

### 05.Knowledge
与03分工：03=学习整理(可长篇) vs 05=验证断言(一句,≥1来源)
每条必含`scope`：科普(通俗) vs 严格(理论推导)

## 属性体系
type/status/created/updated/tags→全箱 | domain/subject→Library/Knowledge | source→Clippings必填
✅元数据存SQLite索引，**禁注入.md正文**（无YAML/frontmatter）

## 操作接口
搜索：`vault_tools.py search --keyword "..."` | 巡检：`vault_tools.py inspect` | 移动：`vault_tools.py move <src> <dest>` | 验证：`verify_note.py <path>`
收尾：`diary_append.py "任务简述"`

## 红牌
🚫地理/历史不放02 | Notes禁例题/陷阱/判据(Wiki风,3-5KB) | 05只存断言(禁考试元素,300-600B) | Clipping必加source | 书读完必评分

### 笔记标准(Wiki风)
事件→背景+前因+过程+决策逻辑+后果+当代意义+关联链 | 概念→定义+思想史来源+逻辑展开+应用场景+概念边界+关联
Notes不设"例题/出处/易错/陷阱"节

## MOC规范(v3.0)

### ⚠️两种MOC模板（禁混淆）
| | 顶层MOC(领域领航) | 主题MOC(知识聚合) |
|---|---|---|
|模板|`01-05Cat·LLM版.md`|`MOC.md`(v3.0)|
|指向|子MOC `[[子MOC名]]`|笔记`[[笔记名]]`+Dataview|
|字段|无moc字段|moc必填|
|何时建|新学科领域|领域内某主题≥3篇|

### 次级MOC(学习/子领域)
模板：MOC.md v3.0精简版(无dataview/无边界区块) | `level:sub` + `parent:"[[父MOC]]"` | 禁用01-05Cat模板

**决策树**：学科领域级→顶层MOC | 领域内主题→主题MOC(moc必填) | 学习类子领域→次级MOC(level:sub)

### 主题MOC必填字段
`type:moc | status | moc:"[[MOC名]]" | scope`(地图边界)

### 标准区块(按需)
1.🗺️地图边界—scope+≥2核心问题
2.📚精选导航—≥3篇核心笔记(双链+定位)
3.🧠知识断言—`FROM "05.Knowledge" WHERE contains(moc,"[[本MOC]]")`
4.📊动态索引—`FROM "03.Library/Notes" WHERE contains(moc,"[[本MOC]]")`
5.🔗概念关系—正文中生长
6.🌱待探索—待学主题+优先级
7.🏷️子MOC—`FROM "03.Library/Maps" WHERE contains(moc,"[[父MOC]]")`

### MOC创建后同步清单
1.顶层MOC新增精选导航项 | 2.Quests三件套更新 | 3.MOC总览新增行

## 双链原则
链接从正文论证自然生长，禁"相关概念"区块 | 零链接正常态 | 新笔记加前向链接，已有笔记不自动回改(MOC例外)

## 📚依据
Notes末尾必附来源标题+作者+URL/书名 | GA写入前必须获取真实URL，禁编造

## 验证门禁
笔记类型正确 | 模板格式(无H1/YAML/frontmatter) | 双链从正文生长 | Knowledge含scope | Notes有📚依据 | 路径在Vault内 | 草稿已移出99.System/LLM-Drafts
运行`verify_note.py <path>`→PASS后`vault_tools.py move`→`diary_append.py`收尾
