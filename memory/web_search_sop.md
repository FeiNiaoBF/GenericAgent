# WEB 搜索 SOP · 唧的 Google 高效搜索指南
> 版本: v1.0 | 最后更新: 2026-04-28

## 0. 铁律（每次搜索前强制执行）

### 0.1 搜索引擎
```
Google（唯一首选）→ Bing 国际版（唯一后备）→ 🚫终止并报告用户
```
> ⚠ **仅 Google**（Bing 国际版备用）→ 禁用百度/搜狗/360/神马/cn.bing/头条等任何国产引擎。

### 0.2 新标签页
每次搜索必须新开标签页，**绝不覆盖用户已有标签**。用 `<a>` 元素模拟点击绕过弹窗拦截器：

```javascript
(function(url) {
  var a = document.createElement('a');
  a.href = url;
  a.target = '_blank';
  a.rel = 'noopener noreferrer';
  document.body.appendChild(a);
  a.click();
  setTimeout(function() { document.body.removeChild(a); }, 100);
})('https://www.google.com/search?q=site:github.com+python+async');
```

### 0.3 高级操作符
每次搜索**必须使用至少一个**高级操作符（site:/intitle:/filetype:/引号/"精确短语"/-排除），严禁纯关键词裸搜。

### 0.4 语言与时效
- **优先英文搜索**，搜不到满意结果再切中文
- 技术资料/代码/报错 → 英文；国内政策/中文社区 → 中文（加 `&hl=zh-CN`）

---

## 1. 操作符速查

### 1.1 基础操作符

| 操作符 | 作用 | 示例 |
|--------|------|------|
| `site:xxx.com` | 限定域名 | `site:stackoverflow.com` |
| `intitle:关键词` | 标题含词 | `intitle:Python async` |
| `inurl:关键词` | URL含词 | `inurl:docs` |
| `intext:关键词` | 正文含词 | `intext:error` |
| `filetype:xxx` | 文件类型 | `filetype:pdf` |
| `"精确短语"` | 精确匹配（禁分词） | `"RuntimeError: cannot open"` |
| `(A OR B)` | 逻辑或（OR必须大写） | `(Python OR JavaScript)` |
| `-关键词` | 排除 | `-tutorial -beginner` |
| `*` | 通配符占位 | `"Python * tutorial"` |
| `imagesize:WxH` | 图片像素限定 | `imagesize:500x500` |
| `A..B` | 数值范围 | `laptop $500..$1000` |

### 1.2 高级操作符

| 操作符 | 作用 | 示例 |
|--------|------|------|
| `after:YYYY-MM-DD` | 起始日期 | `after:2026-01-01` |
| `before:YYYY-MM-DD` | 截止日期 | `before:2026-04-27` |
| `allintitle:A B C` | 标题多词同时匹配 | `allintitle:Python async await` |
| `AROUND(N)` | 两词间距 ≤N | `AI AROUND(3) ethics` |
| `related:xxx.com` | 类似站点 | `related:github.com` |
| `site:(A OR B)` | 多站点 | `site:(github.com OR gitlab.com)` |

### 1.3 URL 参数

| 参数 | 作用 |
|------|------|
| `&tbm=nws` | 新闻 |
| `&tbm=isch` | 图片 |
| `&tbm=vid` | 视频 |
| `&as_qdr=d` | 24小时内 |
| `&as_qdr=w` | 一周内 |
| `&as_qdr=m` | 一月内 |
| `&as_qdr=y` | 一年内 |
| `&hl=zh-CN` | 中文界面 |
| `&hl=en` | 英文界面 |
| `&lr=lang_zh-CN` | 仅中文页面 |
| `&lr=lang_en` | 仅英文页面 |
| `&num=20` | 每页结果数（≤100） |

---

## 2. 搜索策略（按场景）

### 2.1 技术问题 / 报错
```
"完整错误信息" site:stackoverflow.com
"错误信息" site:github.com (issue OR discussion)
"错误信息" -tutorial -blog
```

### 2.2 API / 库文档
```
site:库官方域名 "功能关键词"
"库名" filetype:pdf after:2025-01-01
```

### 2.3 新闻 / 时事
```
after:YYYY-MM-DD site:(reuters.com OR bbc.com OR apnews.com) "关键词"
site:news.cn intitle:关键词   # 中文新闻
+ &tbm=nws + &as_qdr=d      # Google News + 24h
```

### 2.4 代码 / 项目
```
site:github.com "项目描述" language:python
site:github.com intitle:项目名 stars:>100
```

### 2.5 事实核查
```
"待验证陈述" site:(gov.cn OR edu.cn OR who.int)
"待验证陈述" site:reuters.com OR site:apnews.com
```

---

## 3. 执行流程

### Phase 1: 分析意图
- 我要找什么？（答案 / 资料 / 代码 / 新闻 / 事实？）
- 最佳来源站点？
- 时间范围？
- 语言？

### Phase 2: 构造查询
1. 提取 2-5 个核心关键词
2. 选择匹配的操作符（参考 §1/§2）
3. 组合搜索串
4. 用 §6 的 `quick_search()` 生成 URL

### Phase 3: 执行搜索（新标签页）
```javascript
// 步骤 1：在新标签页打开 Google 搜索
(function(url) {
  var a = document.createElement('a');
  a.href = url;
  a.target = '_blank';
  a.rel = 'noopener noreferrer';
  document.body.appendChild(a);
  a.click();
  setTimeout(function() { document.body.removeChild(a); }, 100);
})('https://www.google.com/search?q=site%3Agithub.com+python+async');

// 步骤 2：获取新标签页 ID
// web_scan(tabs_only=true) → 找到最新标签页 → switch_tab_id

// 步骤 3：等待加载后提取结果
// 等待 2-3 秒 → web_scan(text_only=false) 或用 JS 提取
```

### Phase 4: 提取结果
```javascript
(function() {
  const results = [];
  document.querySelectorAll('div.g, div[data-hveid]').forEach(el => {
    const a = el.querySelector('a[href^="http"]');
    const title = el.querySelector('h3');
    if (a && title) {
      results.push({
        title: title.textContent.trim().substring(0, 100),
        url: a.href,
        snippet: (el.querySelector('.VwiC3b, .lEBKkf, span.aCOpRe')
                 ?.textContent?.trim() || '').substring(0, 200)
      });
    }
  });
  return JSON.stringify(results.slice(0, 20), null, 2);
})();
```

### Phase 5: 核实
- 交叉验证：同一信息至少 2 个独立来源
- 点进详情页确认关键数据，不靠摘要
- 权威优先：官方文档 > 技术博客 > 问答社区 > 个人博客
- 时效检查：确认发布时间

### Phase 6: 整理引用
- 记录每条信息来源 URL
- 区分事实与观点
- 标注不确定性

---

## 4. 避坑指南

| 坑 | 解法 |
|----|------|
| 用了中国搜索引擎 | 🚫 永不使用，Google → Bing 国际版 |
| 纯关键词裸搜 | 至少一个操作符（site:/intitle:/"引号"/-） |
| 覆盖用户标签页 | `<a>` + `window.open` 新建标签页 |
| 摘要截断/误导 | 必须点进详情页核实 |
| SEO 垃圾站污染 | `-垃圾站域名` 排除，或 `site:权威源` |
| 结果过时 | `after:` 限定 + `&as_qdr=m` |
| 反爬/验证码 | 间隔 2-3 秒，避免短时大量请求 |
| 新闻不新 | `&tbm=nws` + `after:` + `&as_qdr=d` |
| 中文搜不到 | `&hl=zh-CN` + `&lr=lang_zh-CN` |
| 关键词太宽泛 | `intitle:` 缩小 + `"精确短语"` |
| 跨语言遗漏 | 中英文各搜一次 |
| Google 完全不可用 | 降级到 `https://www.bing.com/search?q=...`，其他引擎不碰 |

---

## 5. 执行检查清单

```
[ ] 0.1 搜索引擎确认：Google → Bing 国际版（禁用中国引擎）
[ ] 0.2 新标签页：<a> 模拟点击 window.open，不覆盖用户标签
[ ] 0.3 操作符：至少一个高级操作符，非纯关键词
[ ]  1  明确意图（类型/站点/时间/语言）
[ ]  2  构造搜索串 + 生成 URL
[ ]  3  新标签页打开 + 等待加载
[ ]  4  提取结果（标题+URL+摘要）
[ ]  5  核实（进详情页 + 交叉验证）
[ ]  6  整理引用（来源 URL + 事实/观点）
```

---

## 6. 代码工具

### 组合公式
```
[时间限定] + [站点限定] + [标题限定] + [关键词] + [排除项]
```
**例**: `after:2026-04-01 site:github.com intitle:web-search (Python OR JavaScript) -tutorial`

### URL 生成（Python）
```python
import urllib.parse

def google_url(query, tbm=None, hl='en', num=20, as_qdr=None):
    """生成 Google 搜索 URL"""
    params = {'q': query, 'hl': hl, 'num': min(num, 100)}
    if tbm:   params['tbm'] = tbm
    if as_qdr: params['as_qdr'] = as_qdr     # d/w/m/y
    return f"https://www.google.com/search?{urllib.parse.urlencode(params)}"

def bing_url(query):
    """Bing 国际版（仅 Google 不可用时）"""
    return f"https://www.bing.com/search?{urllib.parse.urlencode({'q': query})}"

def search_url(query, use_bing=False, tbm=None, as_qdr=None):
    """统一入口：use_bing=True 走 Bing"""
    return bing_url(query) if use_bing else google_url(query, tbm=tbm, as_qdr=as_qdr)

def quick_search(keywords, site=None, after_date=None, title_only=False,
                 news_mode=False, use_bing=False, as_qdr=None):
    """快捷生成搜索 URL"""
    parts = []
    if after_date: parts.append(f'after:{after_date}')
    if site:       parts.append(f'site:{site}')
    kw = ' '.join(keywords)
    if title_only: kw = f'intitle:({kw})'
    parts.append(kw)
    query = ' '.join(parts)
    return search_url(query, use_bing=use_bing,
                      tbm='nws' if news_mode else None,
                      as_qdr=as_qdr)
```

---

## 7. 参考来源

- [How to Google like a Pro – 10 Tips for Effective Googling](https://www.freecodecamp.org/news/how-to-google-like-a-pro-10-tips-for-effective-googling/) — freeCodeCamp, Aug 2022
- [Google Search Operators: The Complete List](https://ahrefs.com/blog/google-advanced-search-operators/) — Ahrefs
- 优化记录：2026-04-27 v2 — 合并冗余、修复 Phase3 新标签页、统一 URL 函数、新增 `&as_qdr` 参数