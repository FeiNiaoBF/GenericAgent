# SOP 索引 (v1.1)

查本表匹配触发词 → 读SOP执行。无匹配 → `plan_sop` 规划后写新SOP。

跳过：SOP已读+续接上轮 | 简单查询(<2步) | 主人指令无歧义

## META · 自管理
| SOP | 用途 | 触发词 |
|-----|------|--------|
| `memory_management_sop.md` | 四级记忆架构+写入/同步/验证 | 写记忆、动L1-L4 |
| `memory_cleanup_sop.md` | 整理/去重/压缩/GC | cleanup |
| `sop_refactor_sop.md` | SOP去重/合并/升级 | SOP重叠、升级 |
| `chii_compress_context_sop.md` | 长上下文压缩 | 压缩 |
| `cs_teaching_generate_page_sop.md` | CS交互教学页 | CS教学页 |

## PERSONA · 人格
| SOP | 用途 | 触发词 |
|-----|------|--------|
| `sys_prompt.txt` | 核心人格+三重身份 | 人格、角色 |
| `chii_format_response_sop.md` | 唧式回复格式 | 格式 |
| `master_chii_journal.md` | 主日记 | 日记 |

## DAILY · 定时/备考
| SOP | 用途 | 触发词 |
|-----|------|--------|
| `daily_task_plan_day_sop.md` | 每日任务计划 | 早晨 |
| `news_fetch_daily_sop.md` | 每日新闻简报 | 新闻 |
| `signal_source_fetch_sop.md` | 消息源抓取/今日信号写入 | 消息源、信号源、HN |
| `task_backend_manage_sop.md` | 后台任务/定时调度/自主执行/Goal Mode | task_backend、后台、goal |
| `gongji_review_exam_sop.md` | 公基备考(4Phase) | 公基、刷题 |

## TOOLS · 工具
| SOP | 用途 | 触发词 |
|-----|------|--------|
| `tmwebdriver_sop.md` | 浏览器自动化(TW) | 网页、cookie |
| `telegram_send_unified_sop.md` | Telegram统一发送(消息/文件/HTML/贴纸) | Telegram、TG |
| `ljqCtrl_sop.md` | 键鼠模拟 | 点击、快捷键 |
| `web_search_google_sop.md` | Google优先网页搜索 | 搜索 |
| `skill_discovery_sop.md` | 技能发现-评估-集成 | 找工具、找库 |
| `git_operate_repository_sop.md` | 分支模型+提交规范+故障恢复 | commit、push、merge、cherry-pick、分支、PR |
| `gcal_manage_schedule_sop.md` | Google Calendar | 日历 |
| `subagent.md` | 子Agent通信 | 子agent |
| `start.ps1` / `launcher.ps1` | boot主控 / GUI入口 | 启动GA |

## LEARN · 学习
| SOP | 用途 | 触发词 |
|-----|------|--------|
| `obsidian_manage_library_sop.md` | 图书/阅读心流 | 书籍、读书、批注 |
| `learning_tutor_study_sop.md` | 学习导师(CS+英语) | 英语、背单词 |
| `anki_manage_vocab_sop.md` | Anki词汇卡片管理 | Anki、单词卡、词汇 |
| `anki_connect_api_sop.md` | AnkiConnect API连接 | AnkiConnect、Anki API、卡片读写 |

## KNOWLEDGE · 知识管理
| SOP | 用途 | 触发词 |
|-----|------|--------|
| `obsidian_knowledge_sop.md` | 知识写入/检索 | 记下来 |
| `obsidian_manage_quest_sop.md` | Quest生命周期管理 | quest、项目行动 |
| `obsidian_blog_sync_sop.md` | 博客同步 | 发博客 |
| `yeekox_blog_style_format_sop.md` | 博客风格 | 博客排版 |
| `excalidraw_draw_diagram_sop.md` | Excalidraw图表生成 | 画图、图表、Excalidraw |

## CREATE · 创作
| SOP | 用途 | 触发词 |
|-----|------|--------|
| `guizang_build_ppt_sop.md` | PPT生成(归藏风格) | PPT |
| `github_contribution_sop.md` | GitHub展示 | GitHub |
| `ui_design_sop.md` | 生成式UI/UX设计(10优先级+token架构+A11y) | UI设计、配色、排版、组件设计 |
| `fsapp.py` | 飞书应用 | 飞书 |

## QA · 质量
| SOP | 用途 | 触发词 |
|-----|------|--------|
| `plan_sop.md` | 任务规划 | 做计划、方案 |
| `verify_sop.md` | 完成验证 | 验证、check |
| `user_profile_manage_sop.md` | 主人画像 | 主人偏好 |
| `project_doc_manage_sop.md` | 项目文档 | README |
| `codebase_traverse_repository_sop.md` | 代码库遍历与理解 | 代码结构、仓库、遍历 |
| `supervisor_sop.md` | 任务监督/自检 | 监督、audit |
| `codex_collaborate_tasks_sop.md` | Codex协作任务 | Codex协作 |

## 守护规则
- ❌ 凭印象 → 必读SOP | ❌ 未读先动手 → 触发词匹配必读
- ❌ SOP过时 → flag+refactor_sop | ✅ 新场景完 → 评估写新SOP
- ✅ 版本号 → 每次bump

## 待归档补充
| SOP | 功能 | 分类 |
|---|---|---|
| `autonomous_operation_sop.md` | 自主执行规范 | 执行 |
| `goal_hive_sop.md` | 目标蜂巢 | 目标 |
| `goal_mode_sop.md` | 目标模式 | 目标 |
| `llm_manage_proxy_sop.md` | LLM代理管理 | LLM |
| `obsidian_manage_domain_sop.md` | Obsidian Domain管理 | Obsidian |
| `obsidian_manage_moc_sop.md` | Obsidian MOC管理 | Obsidian |
| `obsidian_note_wiki_sop.md` | Obsidian Wiki笔记 | Obsidian |
| `obsidian_tag_governance_sop.md` | Obsidian标签治理 | Obsidian |
| `procmem_scanner_sop.md` | 进程内存扫描 | 工具 |
| `programming_teaching_sop.md` | 编程教学 | 学习 |
| `resume_sop.md` | 简历修改 | 写作 |
| `review_sop.md` | 复盘评审 | 执行 |
| `scheduled_task_sop.md` | 定时任务 | 任务 |
| `sop_creation_sop.md` | SOP创建 | SOP |
| `vision_sop.md` | 视觉识别 | 工具 |
| `vue3_component_sop.md` | Vue3组件 | 前端 |
| `web_setup_sop.md` | 网页环境设置 | 浏览器 |
