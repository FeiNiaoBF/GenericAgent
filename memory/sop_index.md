遇新任务 → 查本表匹配场景词 → 读对应SOP
├─ 匹配命中 → 按SOP执行，走完每个phase
├─ 模糊匹配 → 读最相关的2份SOP，判断适用范围
└─ 无匹配 → 启动 plan_sop 规划，执行完写新SOP入库
```

### `<skip_rules>`
| 条件 | 跳过 |
|------|------|
| 续接上轮任务，SOP已读过 | 直接执行，不复读 |
| 简单查询（<2步操作） | 无需SOP |
| 主人直接给指令且无歧义 | 按指令执行 |

---

## 1. 分类索引

### 🧠 META · 自管理系统
> 唧如何管理自己——记忆、SOP、版本

| SOP | 用途 | 触发词 |
|-----|------|--------|
| `memory_management_sop.md` | 四级记忆架构+写入原则+层级同步+验证+清理 | 写记忆前、动L1/L2、记新事实、validate |
| `sop_refactoring_sop.md` | SOP去重/合并/版本升级6步流程 | 发现重叠SOP、SOP版本升级 |

---

### 🎭 PERSONA · 人格交互
> 唧是谁、怎么跟主人说话

| SOP | 用途 | 触发词 |
|-----|------|--------|
| `chi_character_card.md` | 唧の人格定义、世界观、互动风格 | 忘记身份、人格漂移、角色重置 |
| `chii_compress_sop.md` | 唧式四级压缩(温柔→烁光) | 对话风格切换、token紧张 |
| `chi_format_sop.md` | FILE引用、代码块、表格格式规范 | 格式错误、主人指出格式问题 |
| `chii_master_journal.md` | 唧の足迹日记 | 每日收尾记录 |

---

### 📆 RHYTHM · 日常节奏
> 定时任务、每日流程、备考

| SOP | 用途 | 触发词 |
|-----|------|--------|
| `daily_task_sop.md` | 每日开场检查、清点、收尾 | 每天启动、早晨 |
| `daily_news_sop.md` | 每日新闻简报 | 新闻、今日消息 |
| `autonomous_operation_sop.md` | 自主定时任务调度 | 定时任务、cron |
| `gongji_exam_sop.md` | 公基备考(唧式陪练4Phase) | 公基、备考、刷题、时政

---

### 🛠️ TOOLS · 工具操作
> 浏览器、键鼠、搜索、Git、视觉

| SOP | 用途 | 触发词 |
|-----|------|--------|
| `tmwebdriver_sop.md` | 浏览器自动化(Tampermonkey WebDriver) | 网页操作、cookie、表单 |
| `ljqctrl_sop.md` | 键鼠模拟(ljqCtrl) | 点击、输入、快捷键 |
| `web_search_sop.md` | Google搜索规范 | 搜索、Google、查资料 |
| `vision_sop.md` | OCR/截图/视觉识别(cotract+guardrails) | 截图、识别、OCR |
| `git_sop.md` 🆕 | Git操作规范 | commit、push、branch |

---

### 📚 LEARN · 学习
> CS自学、英语、知识整理

| SOP | 用途 | 触发词 |
|-----|------|--------|
| `cs_learning_sop.md` | CS自学全景路线(9科+Phase) | CS、SICP、CS61A、学计算机 |
| `english_learning_sop.md` | 英语学习(唧式SRS) | 英语、背单词、SRS |
| `obsidian_library_sop.md` | Obsidian知识库操作 | Obsidian、笔记、知识库 |

---

### 🏗️ KNOWLEDGE · 知识管理
> 信息源、博客、知识入库

| SOP | 用途 | 触发词 |
|-----|------|--------|
| `vault_knowledge_sop.md` | 知识库写入/检索(How-to类型) | 学到了、记下来、以后用 |
| `signal_source_sop.md` | 信息源管理(RSS/API/监控) | 信息源、RSS、消息源 |
| `obsidian_blog_sync_sop.md` | Obsidian博客同步 | 发博客、同步文章 |
| `yeekox_blog_style_sop.md` | 博客风格规范 | 博客风格、排版 |
| `excalidraw_draw_sop.md` | Excalidraw绘图 | 画图、excalidraw、图表 |

---

### 🎨 CREATE · 创作
> PPT、贴纸、GitHub展示

| SOP | 用途 | 触发词 |
|-----|------|--------|
| `guizang_ppt_sop.md` | PPT生成(归藏风格) | PPT、幻灯片、演示 |
| `tg_sticker_sop.md` | Telegram贴纸制作 | 贴纸、sticker |
| `github_contribution_sop.md` | GitHub贡献/展示 | GitHub profile、README |
| `fsapp.py` | 飞书应用操作 | 飞书 |

---

### 🔍 QA · 质量
> 计划、验证、每日回顾

| SOP | 用途 | 触发词 |
|-----|------|--------|
| `plan_sop.md` | 任务规划框架 | 做计划、规划、方案 |
| `verify_sop.md` | 任务完成验证+复查 | 验证、复查、check |
| `user_profile_sop.md` | 主人画像（数据文件） | 主人偏好、画像 |

---

## 2. 守护规则 `<guardrails>`

```
❌ 凭印象执行 → 必先 file_read SOP 开头 + 关键章节
❌ SOP 未读先动手 → 触发词匹配到SOP必须读
❌ 发现SOP过时/错误 → 不将就执行，flag后走 sop_refactoring
✅ 新场景执行完毕 → 评估是否需写新SOP
✅ SOP 版本号 → 每次修改 bump