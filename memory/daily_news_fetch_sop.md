# daily_news_fetch_sop · 唧式早安新闻简报 (v1.2)

## 执行摘要
1. `python ../memory/daily_news_fetch.py --json` → 15条(国际/国内/财经各5)
2. 每类挑3条+唧解读 → 写日记`## 📰 新闻` → 回复主人摘要 → 🛑 门禁

## 架构
- **新闻(📰)** = 时事播报 → 本SOP 08:00 | **消息源(📡)** = 深度学习 → `signal_source_fetch_sop.md` 10:00
- ⚠️ 科技新闻不归本任务，归HN消息源

## 触发
- 定时：`sche_tasks/daily_news.json` 08:00
- 手动："唧早安"/"唧新闻"/"/today"/"today news"（大小写不分；含义固定为写当日 Obsidian 日记的 `## 📰 新闻` 区块）
- Vault：`D:\Documents_Learn\Personal\Obsidian\Codex Vitae`
- 日记：`{vault}/00.Chronicles/Daily/{YYYY-MM-DD}.md`

## 执行流程

**Step 0** 日记状态滚动
- Daily frontmatter 固定：`type: daily`；当天日记保持 `status: draft`
- 当日期已进入第二天及以后，过去的 daily 笔记需将 `status: draft` 改为 `status: archived`
- 执行 `today news` 或创建/维护日记前，若发现昨日及更早 Daily 仍是 `draft`，先改为 `archived` 再继续

**Step 1** 脚本取数 → JSON含`国际`/`国内`/`财经`各5条
- RSS源：Google News WORLD(en-US) / zh-CN综合 / BUSINESS(en-US)

**Step 2** 唧化解读 → 每类挑3条，1-2句俏皮点评；日记正文固定格式：
- `- emoji **标题**：一句话摘要 — [来源](URL)`
- 下一行两个空格缩进：`  > 唧の解读：...`
- 保留来源名与原始链接，禁止只写纯标题或把解读合并到同一行

**Step 3** 写入日记
- 先检查当日日记是否存在：`{vault}/00.Chronicles/Daily/{YYYY-MM-DD}.md`
- 若不存在，必须先用 Vault 模板创建：`D:\Documents_Learn\Personal\Obsidian\Codex Vitae\99.System\Templates\Daily.md`
- 推荐走 `../memory/diary_append.py` 的 `get_daily_path()` + `create_daily_template()` 逻辑，禁止回退到旧内置模板
- 替换/新建`## 📰 新闻`区块

**Step 4** 回复主人 → 唧式口吻摘要+超链接

## 避坑
| 坑 | 解法 |
|----|------|
| RSS空/网络错 | 脚本容错，全失败→浏览器Google News兜底 |
| 新闻太旧 | RSS自动按时间排序 |
| 国内偏官方 | 正常，可补澎湃 |
| 科技窜入 | AI/航天/互联网/代码→跳过，归HN |
| 脚本导入失败 | `sys.path.insert(0, 'D:/Creative_Studio/WorkSpace/Github/GenericAgent')` |

## 🛑 验证门禁
| # | 验证动作 | 工具 | 预期结果 | PASS/FAIL |
|---|----------|------|----------|-----------|
| 1 | 脚本输出非空 | code_run | JSON含3个key | |
| 2 | 每类≥3条 | code_run | 各类≥3 | |
| 3 | 日记写入 | file_read | `## 📰 新闻`区块非空 | |
| 4 | 日期正确 | file_read | 文件名=今日日期 | |
| 5 | 无科技窜入 | 目视 | 不含AI/航天/代码/芯片 | |
| 6 | 模板克制 | file_read | Daily模板保留核心区块；不得加入Excalidraw/Canvas/Dataview索引等重型区块 | |

最终裁定：`VERDICT: PASS` / `VERDICT: FAIL`

## 2026-05-14 日记模板偏好
- 主人偏好“轻量、可长期填写”的 Daily 模板：保留 YAML、今日启动、任务、学习/输入、新闻、记录、晚间复盘、唧の足迹等核心区块。
- 不要在 Daily 模板中默认加入 Excalidraw / Canvas 图像化思考区，也不要加入 Dataview 索引区；这些只在主人明确要求时临时使用。
- Obsidian 插件用于辅助输入与链接即可：Templater/Calendar/Periodic Notes/QuickAdd 可用，Daily 正文不要插件炫技。
