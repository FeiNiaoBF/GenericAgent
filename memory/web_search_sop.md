# WEB 搜索 SOP · 唧的 Google 高效搜索 (v1.0)

## 执行摘要（≥1步执行前必读）
1. 铁律检查：Google唯一 → Bing后备 → 新标签页打开 → 至少一个操作符
2. 构造查询：`site:`/`intitle:`/`"引号"`/`-排除`组合，禁止纯关键词裸搜
3. 结果验证：交叉确认来源 + GitHub代码搜索用REST API(间隔≥6s) → 🛑 过验证门禁

## 0. 铁律（每次搜索前强制执行）

1. **搜索引擎**：Google（唯一）→ Bing 国际版（后备）→ 🚫终止
2. **新标签页**：`<a>` 模拟点击或 `window.open`，禁止覆盖用户标签页
3. **至少一个操作符**：`site:` / `intitle:` / `"引号"` / `-排除词`，禁止纯关键词裸搜

## 1. 操作符速查

| 类型 | 操作符 | 示例 |
|------|--------|------|
| 站点限定 | `site:domain` | `site:github.com` |
| 标题限定 | `intitle:kw` | `intitle:"error handling"` |
| 精确匹配 | `"phrase"` | `"dependency injection"` |
| 排除词 | `-keyword` | `-tutorial -w3schools` |
| 时间 | `after:YYYY-MM-DD` + `&as_qdr=d/w/m/y` | 新闻时效 |
| OR | `(A OR B)` | `(Python OR JS)` |
| 间距 | `AROUND(N)` | `AI AROUND(3) ethics` |
| 类似站点 | `related:domain` | `related:github.com` |
| 文件类型 | `filetype:pdf` | `filetype:pdf` |

> 完整列表 → [Google Search Operators (Ahrefs)](https://ahrefs.com/blog/google-advanced-search-operators/)

## 2. 搜索策略分类

| 类型 | 意图 | 典型操作符组合 |
|------|------|---------------|
| 官方文档 | 查API/规范 | `site:docs.python.org intitle:keyword` |
| 技术问答 | 解决报错 | `"error message" site:stackoverflow.com OR site:github.com` |
| 最新消息 | 新闻/更新 | `keyword &tbm=nws&as_qdr=d after:YYYY-MM-DD` |
| 中文内容 | 中文资料 | `&hl=zh-CN&lr=lang_zh-CN keyword` |
| 跨语言 | 中英各搜一次 | 中文→再搜英文 |

## 3. 搜索执行

委托 `quick_search()`（见§5），构造URL后在新标签页打开。流程：

```
构造查询 → quick_search() 生成 URL → web_execute_js 打开 → web_scan 读结果
→ 提取 Top 2-3 → 点进详情页交叉验证 → >=2独立来源确认 → 整理输出
```

**停止条件**：第1轮不满足→换关键词/语言；第2轮仍不满足→终止，标注不确定性。

**成功输出**：`✅ 深度查找完成 | 来源1: [URL], 来源2: [URL] | 结论: [事实]`
**失败输出**：`⚠️ 未找到可靠答案 | 已查: [URL1], [URL2] | 建议: [请求用户重新表述]`

## 4. 避坑指南

| 坑 | 解法 |
|----|------|
| 中国搜索引擎 | 🚫 永不使用 |
| 纯关键词裸搜 | 至少一个操作符 |
| 覆盖用户标签页 | 新建标签页 |
| 摘要截断误导 | 必须进详情页核实 |
| SEO垃圾站 | `-垃圾站域名` / `site:权威源` |
| 结果过时 | `after:` + `&as_qdr=` |
| 无限搜索 | 2轮上限 |
| 新闻不新 | `&tbm=nws` + `&as_qdr=d` |
| 中文搜不到 | `&hl=zh-CN&lr=lang_zh-CN` |
| 跨语言遗漏 | 中英文各搜一次 |
| Google不可用 | 降级 `bing.com/search?q=...` |
| GitHub搜技术 | `site:github.com language:python stars:>=50` |

## 5. 代码工具

```python
import urllib.parse

def google_url(query, tbm=None, hl='en', num=20, as_qdr=None):
    """生成 Google 搜索 URL"""
    params = {'q': query, 'hl': hl, 'num': min(num, 100)}
    if tbm:   params['tbm'] = tbm
    if as_qdr: params['as_qdr'] = as_qdr  # d/w/m/y
    return f"https://www.google.com/search?{urllib.parse.urlencode(params)}"

def bing_url(query):
    """Bing 国际版（仅 Google 不可用时）"""
    return f"https://www.bing.com/search?{urllib.parse.urlencode({'q': query})}"

def search_url(query, use_bing=False, tbm=None, as_qdr=None):
    return bing_url(query) if use_bing else google_url(query, tbm=tbm, as_qdr=as_qdr)

def quick_search(keywords, site=None, after_date=None, title_only=False,
                 news_mode=False, use_bing=False, as_qdr=None):
    """快捷生成搜索 URL。keywords: list of str"""
    parts = []
    if after_date: parts.append(f'after:{after_date}')
    if site:       parts.append(f'site:{site}')
    kw = ' '.join(keywords)
    if title_only: kw = f'intitle:({kw})'
    parts.append(kw)
    return search_url(' '.join(parts), use_bing=use_bing,
                      tbm='nws' if news_mode else None, as_qdr=as_qdr)
```

## 6. GitHub 代码搜索（无需浏览器）

`code_run` 直接用 `https://api.github.com/search/repositories?q=...` REST API：
- 无认证 ~10 req/min，间隔 >= 6s
- `stars:>=50` 过滤噪声
- 结果交叉验证（点进 repo URL 确认 stars/描述一致）

## 🛑 验证门禁
| 检查项 | PASS条件 | FAIL处理 | 状态 |
|--------|---------|---------|------|
| 铁律遵守 | Google优先 + 新标签页 + ≥1操作符 | 改查询重搜 | |
| 结果交叉验证 | ≥2个独立来源一致 / API search确认stars | 标注未验证 | |
| 间隔守规 | GitHub API调用间隔≥6s | 等待后重试 | |

最终裁定：`VERDICT: PASS` / `VERDICT: FAIL`
