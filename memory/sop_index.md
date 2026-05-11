# SOP 索引 (v1.1)

查本表匹配触发词 → 读SOP执行。无匹配 → `plan_sop` 规划后写新SOP。

跳过：SOP已读+续接上轮 | 简单查询(<2步) | 主人指令无歧义

## META · 自管理
| SOP | 用途 | 触发词 |
|-----|------|--------|
| `memory_management_sop.md` | 四级记忆架构+写入/同步/验证 | 写记忆、动L1-L4 |
| `memory_cleanup_sop.md` | 整理/去重/压缩/GC | cleanup |
| `sop_refactoring_sop.md` | SOP去重/合并/升级 | SOP重叠、升级 |

## PERSONA · 人格
| SOP | 用途 | 触发词 |
|-----|------|--------|
| `sys_prompt.txt` | 核心人格+三重身份 | 人格、角色 |
| `chi_format_sop.md` | 格式(粗体/斜体/段落≤3句) | format |
| `chii_compress_sop.md` | 压缩术4级 | 压缩 |
| `chii_master_journal.md` | 主日记 | 日记 |

## DAILY · 定时/备考
| SOP | 用途 | 触发词 |
|-----|------|--------|
| `daily_task_sop.md` | 每日开场/清点/收尾 | 早晨 |
| `daily_news_sop.md` | 新闻简报 | 新闻 |
| `scheduled_task_sop.md` | 定时任务JSON规范 | schedule |
| `task_backend_sop.md` | 后台引擎(自主+信号源+目标) | 后台、goal |
| `gongji_exam_sop.md` | 公基备考(4Phase) | 公基、刷题 |

## TOOLS · 工具
| SOP | 用途 | 触发词 |
|-----|------|--------|
| `tmwebdriver_sop.md` | 浏览器自动化(TW) | 网页、cookie |
| `tg_unified_sop.md` | TG统一(通知+渲染+贴纸) | Telegram |
| `ljqctrl_sop.md` | 键鼠模拟 | 点击、快捷键 |
| `web_search_sop.md` | Google搜索 | 搜索 |
| `skill_discovery_sop.md` | 技能发现-评估-集成 | 找工具、找库 |
| `git_sop.md` | 分支模型+提交规范+故障恢复 | commit、push、merge、cherry-pick、分支、PR |
| `gcal_sop.md` | Google Calendar | 日历 |
| `subagent.md` | 子Agent通信 | 子agent |
| `start.ps1` / `launcher.ps1` | boot主控 / GUI入口 | 启动GA |

## LEARN · 学习
| SOP | 用途 | 触发词 |
|-----|------|--------|
| `obsidian_library_sop.md` | Obsidian知识库 | 笔记、知识库 |
| `learning_tutor_sop.md` | 学习导师(CS+英语) | 英语、背单词 |

## KNOWLEDGE · 知识管理
| SOP | 用途 | 触发词 |
|-----|------|--------|
| `vault_knowledge_sop.md` | 知识写入/检索 | 记下来 |
| `obsidian_blog_sync_sop.md` | 博客同步 | 发博客 |
| `yeekox_blog_style_sop.md` | 博客风格 | 博客排版 |
| `excalidraw_draw_sop.md` | Excalidraw绘图 | 画图 |

## CREATE · 创作
| SOP | 用途 | 触发词 |
|-----|------|--------|
| `guizang_ppt_sop.md` | PPT生成(归藏风格) | PPT |
| `github_contribution_sop.md` | GitHub展示 | GitHub |
| `ui_design_sop.md` | 生成式UI/UX设计(10优先级+token架构+A11y) | UI设计、配色、排版、组件设计 |
| `fsapp.py` | 飞书应用 | 飞书 |

## QA · 质量
| SOP | 用途 | 触发词 |
|-----|------|--------|
| `plan_sop.md` | 任务规划 | 做计划、方案 |
| `verify_sop.md` | 完成验证 | 验证、check |
| `user_profile_sop.md` | 主人画像 | 主人偏好 |
| `project_doc_sop.md` | 项目文档 | README |
| `codebase_traversal_sop.md` | 代码遍历/索引 | 代码结构 |
| `supervisor_sop.md` | 任务监督/自检 | 监督、audit |
| `codex_collaboration_sop.md` | Codex协作(边界/诊断) | Codex协作 |

## 守护规则
- ❌ 凭印象 → 必读SOP | ❌ 未读先动手 → 触发词匹配必读
- ❌ SOP过时 → flag+sop_refactoring | ✅ 新场景完 → 评估写新SOP
- ✅ 版本号 → 每次bump
