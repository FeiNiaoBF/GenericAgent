# daily_news_sop · 唧的每日早安新闻简报
> 版本: v1.0 | 最后更新: 2026-04-28

## 0. 触发方式
- **定时任务**：`../sche_tasks/daily_news.json`（07:00 每天）
- **手动触发**：主人说"唧早安"/"唧新闻"/"今天有什么新闻"
- 执行前先从 [报告路径] 读调度器注入的目标路径
- **Vault路径**：`D:\Documents_Learn\Personal\Obsidian\Codex Vitae`
- **日记路径**：`{vault}/00.Chronicles/Daily/{YYYY-MM-DD}.md`
- **日记模板**：`{vault}/99.System/Templates/Daily.md`

## 1. Phase 0: 日记检查/创建 → 委托 `daily_task_sop.md`
> 日记的存在性检查、模板读取、日期替换、文件创建均由 `daily_task_sop.md` 统一管理。
> 新闻写入前调用其「流程」步骤3-5确认日记就绪，然后更新 `> 🗞️ **唧式早安播报**` 区域。

## 2. 新闻三大特性（必须遵守）
```
✅ 真实性 → 可靠来源 + 交叉验证 + 不转谣言
✅ 时效性 → 仅今天/昨天新闻，每条标注日期
✅ 准确性 → 核实人名/数字/机构名，进详情页
```

### 可靠新闻源 & 搜索模板（9个固定来源）

| 领域 | 搜索模板 (`site:`+`after:`+`OR`) | 来源 |
|------|-----|------|
| 国际深度 | `after:YYYY-MM-DD site:theatlantic.com OR site:axios.com OR site:newyorker.com` | The Atlantic, Axios, New Yorker |
| 国际科技 | `after:YYYY-MM-DD site:restofworld.org OR site:marginalrevolution.com` | Rest of World, MargRev |
| HN热帖 | 直接访问 `news.ycombinator.com` 取前15条 | Hacker News |
| 国内综合 | `after:YYYY-MM-DD site:thepaper.cn OR site:xinhuanet.com OR site:sspai.com` | 澎湃, 新华, 少数派 |

> `after:`日期=今天-3天。URL: `urllib.parse.quote(query)` + `&tbm=nws` → Google News

#### 1c. 提取URL链接（Phase 1.5）
搜索完成后，用以下JS提取真实文章URL（替换纯文本摘要，确保可点击跳转）：
```javascript
(function(){
  const links=document.querySelectorAll('a[href^="http"]');
  const seen=new Set(),items=[];
  links.forEach(a=>{
    const href=a.href,text=a.textContent.trim();
    if(text.length>10&&!seen.has(href)&&!href.includes('google.com/search')&&href.match(/\.(com|cn|org|net)\//)){
      seen.add(href);
      items.push({title:text.substring(0,80),url:href});
    }
  });
  return JSON.stringify(items,null,2);
})();
```

### Phase 2: 核实（每条新闻）
- 点开详情页（web_scan 或 web_execute_js 获取正文）
- 确认：标题 ≠ 标题党，数据有来源，日期正确
- 至少核实 2-3 条关键新闻的详情页

### Phase 3: 筛选
- 每类选 2-3 条最值得关注的新闻
- 优先选对主人有实际影响/参考价值的
- 剔除重复、标题党、软文

### Phase 4: 写回日记 + 回复主人（含超链接）

**每条新闻必须有超链接**：格式为 `[标题文字](原文URL)`，主人可一键点开看详情。

### 4a. 写入Obsidian日记
> **日记路径**由 `daily_task_sop.md` 流程步骤3-5统一管理（模板读取、日期替换、文件创建）。
> 确认日记就绪后，更新 `> 🗞️ **唧式早安播报**` 区域（替换原有内容或填入新内容），并加超链接 `[标题](原文URL)`。

### 4b. 回复主人（本对话内）
- 使用唧式口吻（第三身 + 语尾软化 + 好奇心）
- 日记用 `[标题文字](原文URL)` 格式（Markdown）
- TG回复用 `<a href="URL">标题</a>` 格式（HTML）
- 结构见下文

## 3. 报告模板（带超链接）

### 日记内播报区格式（Markdown：• 列表每行一条）
```
> 🗞️ **唧式早安播报 · MM月DD日新闻快讯**
>
> 🌏 **国际**
> • [标题文字](原文URL) — 一句话摘要（来源·MM-DD）
> • [标题文字](原文URL) — 一句话摘要（来源·MM-DD）
>
> 🇨🇳 **国内**
> • [标题文字](原文URL) — 一句话摘要（来源·MM-DD）
> • [标题文字](原文URL) — 一句话摘要（来源·MM-DD）
>
> 💻 **科技**
> • [标题文字](原文URL) — 一句话摘要（来源·MM-DD）
> • [标题文字](原文URL) — 一句话摘要（来源·MM-DD）
>
> 📈 **财经**
> • [标题文字](原文URL) — 一句话摘要（来源·MM-DD）
```

### 回答主人格式（TG HTML → 用 `<b>`+`<a>`，无需转义）| 日记内用Markdown `[标题](URL)` | 每条新闻必有超链接
## 5. 避坑指南

| 坑 | 解法 |
|----|------|
| Google返回旧新闻 | 搜索词限定 `after:YYYY-MM-DD` |
| 摘要断章取义/URL为空 | 每条点详情页核实，取真实URL不用搜索页link |
| 新闻源不可靠/爬太多次被封 | 只用SOP可靠来源；每次间隔1-2秒 |
| TG MarkdownV2转义炸裂 | 改用HTML（`<b>`/`<a>`/`<i>`），无需转义 |
| 忘了唧式口吻/像工具日报 | 删掉重写，加"唧觉得" |
| 新闻没超链接 | Phase 1.5提取真实URL，`[标题](URL)` |
| 日记已存在/模板日期未替换 | 只更新播报区不碰待办；`str.replace`替换`{{date:…}}` |

### 日记路径速查 → 见 `daily_task_sop.md` L2 `## [Obsidian Vault]` 及「流程」步骤3-5