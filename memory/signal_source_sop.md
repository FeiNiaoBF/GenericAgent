# signal_source_sop · 消息源管理 SOP

## 执行摘要（≥1步执行前必读）
1. `python ../memory/{source}_daily_fetch.py` → 获取消息源数据
2. 挑 3-5 条最有价值的 → 写入日记 `📡今日信号` 区块
3. 回复摘要（TOP 3，每条加唧解读）→ 🛑 **过验证门禁**

## 0. 概念定义
- **新闻（📰）** = 今天发生了什么 → `daily_news_sop.md` → 日记 `## 📰 新闻`
- **消息源（📡）** = 有什么值得深度学习 → 本 SOP → 日记 `📡今日信号`
- 新闻讲时效（今天），消息源讲深度（值得学的东西）

## 1. 成功模式（三层架构）
每次新增消息源按此模板，已验证可行：

```
Layer 1 — 数据脚本:  memory/{source}_daily_fetch.py
Layer 2 — 定时任务:  sche_tasks/{source}_daily.json
Layer 3 — 流程 SOP:  本 SOP（统一管理，无需每源单独SOP）
```

## 2. 脚本接口规范
```python
# {source}_daily_fetch.py 必须导出：
def fetch_items(count=15) -> list[dict]:
    """返回 [{title, url, score, comments, ...}, ...]"""

def format_for_diary(items) -> str:
    """返回 Markdown，写入日记 📡今日信号"""

# 可选导出：
def format_for_source_note(items) -> str:
    """返回 Markdown，更新源笔记"""
```

## 3. JSON 任务格式
```json
{
  "schedule": "10:00",
  "repeat": "daily",
  "enabled": true,
  "max_delay_hours": 4,
  "description": "📡 {源名称} 消息源 {时间}",
  "prompt": "## 📡 {源名称} 消息源任务\n\n### 执行流程\n1. 运行 `python ../memory/{source}_daily_fetch.py`\n2. 解析数据，按 diary 格式写入今日日记 📡今日信号\n3. 有源笔记则更新对应区块\n4. 回复摘要（TOP 3）"
}
```

## 4. 日记写入位置
统一写入 `{vault}/00.Chronicles/Daily/{YYYY-MM-DD}.md` → `📡今日信号` 区块

格式：
```markdown
### 📡 {源名称}

- ⭐ **[title](url)** (score pts) — 唧的解读：...
- [title](url) (score pts)
```

多个消息源按时间排列在同一 `📡今日信号` 大区块下。

## 5. 现有消息源清单
| 源 | 时间 | 脚本 | 分类 |
|----|------|------|------|
| HN | 10:00 | `hn_daily_fetch.py` | 科技/技术洞察 |

## 6. 扩展流程
新增消息源仅需两步：
1. 写 `memory/{source}_daily_fetch.py`（遵守 §2 接口）
2. 添加 `sche_tasks/{source}_daily.json`（遵守 §3 格式）
3. 在本 SOP §5 登记 → 同步 L1/L2

## 7. 避坑
- 消息源 ≠ 新闻：不要往 `📰 新闻` 区块写
- 时间错开：同类源间隔 ≥2h，避免碰撞
- 脚本必须可独立运行（`python xxx.py` 能直接出数据）
- JSON prompt 是给 GA 看的执行指令，不要写成给用户看的文案

## 🛑 验证门禁

| # | 验证动作 | 工具 | 预期结果 | PASS/FAIL |
|---|----------|------|----------|-----------|
| 1 | 脚本返回≥5条 | code_run | `fetch_items()` 返回长度≥5 | |
| 2 | 无重复条目 | code_run | title 去重后数量=原始数量 | |
| 3 | 日记写入确认 | file_read | `📡今日信号` 区块有对应源名称 | |
| 4 | 未窜入新闻区 | file_read | `📰 新闻` 区无消息源内容 | |

最终裁定：`VERDICT: PASS` / `VERDICT: FAIL`
