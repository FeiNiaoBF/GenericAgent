# 公基备考 SOP (唧式陪练) (v3.0)
> 触发: 公基/备考/刷题/时政/常识判断/事业单位考试
> 依赖: web_search_sop | obsidian_knowledge_sop | user_profile_manage_sop

## 执行摘要
1. 路由：具体题→答疑 | 无题→随机出题 | 累了→收尾统计+鼓励
2. 按模块出题→连对3题升难度→错题三步归档(笔记→MOC→Anki) → 🛑

## 0. 路由
```
有具体题→Phase 2答疑 | 无题→Phase 1出题 | "累了"→收尾
```
skip: 贴题直答 | 上轮同类换模块 | 连对3题升难度

## 笔记归档策略
公基是触发器，知识归档到所属领域，公基只叠加tag。
| 模块 | 目录 | | 模块 | 目录 |
|------|------|---|------|------|
| 法律 | Law/ | | 科技 | Science/ |
| 政治 | Politics/ | | 地理 | Geography/ |
| 经济 | Economics/ | | 时政 | Current-Affairs/ |
| 文史 | History/Culture/ | | 管理 | Management/ |
（基路径: `03.Library/Notes/`）
流程: 不懂概念→查资料→写Wiki原子笔记→`tags: [公基]`→错题追加`## 🐛 错题`
索引: `#公基` 由 [[公基备考地图]] Dataview 自动发现

## MOC创建规范
### 两种MOC
| | 顶层MOC | 主题MOC |
|---|---------|---------|
| 模板 | `01-05Cat·LLM版.md` | `MOC.md`(v3.0) |
| 定位 | 领域领航 | 单一主题聚合 |
| 指向 | 子MOC | 笔记 |
| 字段 | 无moc | `moc: "[[所属顶层MOC]]"` |

### 创建主题MOC步骤
1. 模板: `99.System/Templates/MOC.md`(v3.0)，禁用顶层模板
2. YAML: `type: moc | moc: "[[所属顶层MOC]]" | status: seedling`
3. 启用区块: scope+核心问题≥2 → 精选导航≥3 → 知识断言 → Dataview动态索引
4. 顶层MOC新增 `- [[主题MOC名]]`
5. 同步Quests三件套（Dashboard/备考/备考地图）

### 禁手
🚫 主题MOC禁用顶层模板 | 🚫 不同步Quests | 🚫 顶层不更新子MOC入口

## Phase 1: 出题模式
轮换: 法律→政治→经济→文史→科技→地理→时政→管理
单选4选项 | 难度动态 | 优先真题改编 | 不连续同模块 | 答错→解析+归档

## Phase 2: 答疑模式
流程: 读题→搜索(web_search, 政府>教材>百科)→解析(选项+陷阱+延伸)→三步归档

### ⭐ 错题三步归档（必执行）

**Step 1: 写知识笔记**
提取核心知识点→查资料→写Wiki原子笔记→归档到对应目录
frontmatter: `tags: [公基], moc: "[[对应主题MOC]]", status: seedling, created: YYYY-MM-DD`
正文: 定义→来源→逻辑→场景→关联（禁"例题/陷阱"节）

**Step 2: 更新MOC**
主题MOC不存在→按obsidian_knowledge_sop §5创建(MOC.md v3.0)→同步Quests三件套
存在→Dataview靠moc字段自动索引

**Step 3: 推送Anki卡片（用utils）**

前提：Anki桌面端已打开 + AnkiConnect插件运行中（端口8765）

```python
import sys; sys.path.insert(0, r"D:\Creative_Studio\WorkSpace\Github\GenericAgent\memory")
from anki_connect_utils import Anki

anki = Anki()
note_id = anki.add_note(
    deck="公基错题", model="公基错题",
    fields={
        "id": "编号(如 002)",
        "question": "题干全文",
        "options": "选项1||选项2||选项3||选项4",  # 只写纯选项，禁带A/B/C/D与<br>；模板会自动生成字母
        "answer": "正确选项字母",
        "notes": "法条原文+逐项解析+陷阱标注"
    },
    tags=["公基", "错题", "学科分类"]
)
```

② 验证（必须！）：`add_note`内部已含noteId校验 + `notes_info`读回确认

参考：anki_connect_sop.md v3.0（用utils而非裸HTTP）

## Phase 3: 错题复习
触发: "复习错题" 或 每20题提醒
Dataview调取 #公基+#错题 → 抽3-5题重测 → 二次错→重点标记 | 连对→移除

## Phase 4: 模拟考试
触发: "来套模拟卷" | 10/20/30题 | 限时1题/分 | 输出得分率+薄弱分析

## 🛑 验证门禁
| 检查项 | 状态 |
|--------|------|
| 错题按领域归档(vault笔记)？ | |
| MOC已同步(moc字段+Dataview索引)？ | |
| Anki卡片已推送(noteId已获取)？ | |
| Anki卡片读回验证(fields一致)？ | |
| 薄弱模块已标记(正确率<60%)？ | |
| 统计已输出？ | |
