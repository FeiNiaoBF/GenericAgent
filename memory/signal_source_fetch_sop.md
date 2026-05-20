---
name: signal_source_fetch
description: 消息源抓取、筛选并写入日记今日信号区块
---
# signal_source_fetch_sop · 消息源管理 SOP

## 定义
- 新闻📰=今天发生什么 → `news_fetch_daily_sop.md` → 日记`## 📰 新闻`。
- 消息源📡=值得深度学习的内容 → 本SOP → 日记`📡今日信号`。

## 执行
1. `python ../memory/{source}_daily_fetch.py`抓取。
2. 选3-5条最高价值内容，写入今日日记`📡今日信号`。
3. 回复TOP3，每条加唧解读，过验证门禁。

## 三层架构
```text
Layer 1 数据脚本: memory/{source}_daily_fetch.py
Layer 2 定时任务: sche_tasks/{source}_daily.json
Layer 3 流程SOP: 本SOP统一管理
```

## 脚本接口
```python
def fetch_items(count=15) -> list[dict]: ...       # [{title,url,score,comments,...}]
def format_for_diary(items) -> str: ...           # 写入📡今日信号的Markdown
def format_for_source_note(items) -> str: ...     # 可选，更新源笔记
```
脚本必须可独立运行：`python xxx.py`直接产出数据。

## 定时任务JSON
```json
{"schedule":"10:00","repeat":"daily","enabled":true,"max_delay_hours":4,
 "description":"📡 {源名称} 消息源 {时间}",
 "prompt":"运行 python ../memory/{source}_daily_fetch.py；写今日日记📡今日信号；有源笔记则更新；回复TOP3"}
```

## 日记格式
位置：`{vault}/00.Chronicles/Daily/{YYYY-MM-DD}.md` 的`📡今日信号`区块。
```markdown
### 📡 {源名称}
- ⭐ **[title](url)** (score pts) — 唧的解读：...
- [title](url) (score pts)
```
多源按时间排列在同一大区块下。

## 现有源与扩展
- HN：10:00，`hn_daily_fetch.py`，科技/技术洞察。
- 新增源：写`memory/{source}_daily_fetch.py` → 加`sche_tasks/{source}_daily.json` → 在本SOP登记并同步L1/L2。
- 同类源间隔≥2h；JSON prompt写给GA，不写用户文案。

## 验证门禁
脚本返回≥5条；title无重复；日记`📡今日信号`含源名；未窜入`📰 新闻`区。

`VERDICT: PASS` / `VERDICT: FAIL`
