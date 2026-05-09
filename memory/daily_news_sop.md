# daily_news_sop · 唧式早安新闻简报 (v1.1)

## 执行摘要
1. `python ../memory/daily_news_fetch.py --json` → 15条(国际/国内/财经各5)
2. 每类挑3条+唧解读 → 写日记`## 📰 新闻` → 回复主人摘要 → 🛑 门禁

## 架构
- **新闻(📰)** = 时事播报 → 本SOP 08:00 | **消息源(📡)** = 深度学习 → `signal_source_sop.md` 10:00
- ⚠️ 科技新闻不归本任务，归HN消息源

## 触发
- 定时：`sche_tasks/daily_news.json` 08:00
- 手动："唧早安"/"唧新闻"/"/today"
- Vault：`D:\Documents_Learn\Personal\Obsidian\Codex Vitae`
- 日记：`{vault}/00.Chronicles/Daily/{YYYY-MM-DD}.md`

## 执行流程

**Step 1** 脚本取数 → JSON含`国际`/`国内`/`财经`各5条
- RSS源：Google News WORLD(en-US) / zh-CN综合 / BUSINESS(en-US)

**Step 2** 唧化解读 → 每类挑3条，1-2句俏皮点评，保留`[标题](URL)`+`— *来源*`

**Step 3** 写入日记
- 确认日记存在(daily_task_sop步骤3-5)
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

最终裁定：`VERDICT: PASS` / `VERDICT: FAIL`
