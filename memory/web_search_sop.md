# Web 搜索 SOP (v1.1 ⚡干练)

> 触发: 搜索需求 | 前置: 浏览器可用

## 执行摘要
1. 铁律：Google唯一 → Bing后备 → 新标签页 → ≥1操作符
2. 构造查询：`site:`/`intitle:`/`"引号"`/`-排除`组合，禁裸搜
3. 交叉验证：≥2独立来源 + GitHub API间隔≥6s → 🛑 验证门禁

## 1. 操作符速查
| 类型 | 操作符 | 示例 |
|------|--------|------|
| 站点 | `site:domain` | `site:github.com` |
| 标题 | `intitle:kw` | `intitle:"error handling"` |
| 精确 | `"phrase"` | `"dependency injection"` |
| 排除 | `-keyword` | `-tutorial -w3schools` |
| 时间 | `after:YYYY-MM-DD` + `&as_qdr=d/w/m/y` | |
| OR | `(A OR B)` | |

## 2. 策略分类
| 类型 | 操作符组合 |
|------|-----------|
| 官方文档 | `site:docs.python.org intitle:keyword` |
| 技术问答 | `"error" site:stackoverflow.com OR site:github.com` |
| 最新消息 | `keyword &tbm=nws&as_qdr=d after:YYYY-MM-DD` |
| 中文 | `&hl=zh-CN&lr=lang_zh-CN` |
| 跨语言 | 中英文各搜一次 |

## 3. 执行流程
```
构造查询 → quick_search() → web_execute_js新标签打开 → web_scan
→ 提取Top2-3 → 点进详情页交叉验证 → ≥2来源确认
```
停止：第1轮不满足→换关键词；第2轮仍不满足→终止标注不确定。

## 4. 避坑
| 坑 | 解法 |
|----|------|
| 中国搜索引擎 | 🚫 永不使用 |
| 裸搜 | ≥1操作符 |
| 覆盖标签页 | 新建 |
| 摘要截断 | 进详情页核实 |
| 过时结果 | `after:` + `&as_qdr=` |
| 无限搜索 | 2轮上限 |
| Google不可用 | 降级bing |

## 5. 代码工具
```python
import urllib.parse
def google_url(query, tbm=None, hl='en', num=20, as_qdr=None):
    params = {'q': query, 'hl': hl, 'num': min(num, 100)}
    if tbm:   params['tbm'] = tbm
    if as_qdr: params['as_qdr'] = as_qdr
    return f"https://www.google.com/search?{urllib.parse.urlencode(params)}"

def bing_url(query):
    return f"https://www.bing.com/search?{urllib.parse.urlencode({'q': query})}"

def quick_search(keywords, site=None, after_date=None, title_only=False,
                 news_mode=False, use_bing=False, as_qdr=None):
    parts = []
    if after_date: parts.append(f'after:{after_date}')
    if site:       parts.append(f'site:{site}')
    kw = ' '.join(keywords)
    if title_only: kw = f'intitle:({kw})'
    parts.append(kw)
    url = bing_url(' '.join(parts)) if use_bing else google_url(' '.join(parts), tbm='nws' if news_mode else None, as_qdr=as_qdr)
    return url
```

## 6. GitHub 代码搜索（REST API）
`https://api.github.com/search/repositories?q=...` — 无认证~10 req/min，间隔≥6s
`stars:>=50` 过滤噪声 → 点进repo确认stars一致

## 🛑 验证门禁
| 检查项 | PASS | FAIL |
|--------|------|------|
| 铁律 | Google优先+新标签+≥1操作符 | 重搜 |
| 交叉验证 | ≥2来源一致 | 标注未验证 |
| 间隔 | GitHub API≥6s | 等待重试 |

`VERDICT: PASS` / `VERDICT: FAIL`
