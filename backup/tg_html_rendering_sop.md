# TG HTML 渲染管线 SOP · L3 (v1.0)
> 源码: `../frontends/tg_html.py`(371行) + `../frontends/tgapp.py` Summary发送段

## 执行摘要（≥1步执行前必读）
1. TG消息统一走 HTML parse_mode，**非 Markdown**
2. 渲染管线: `LLM输出` → `normalize_markdown_artifacts()` → `render_for_telegram_html()` → `_TelegramHTMLSanitizer` → Telegram API
3. **已知坑**: LLM裸输出`<blockquote>`无闭合标签 → 必须在normalize阶段用正则清理（见§3 fix）

## §1 渲染管线全景

```
LLM raw text
  │
  ▼
① normalize_markdown_artifacts(text)        # frontends/tg_html.py:55
  │  - 将Markdown标记(**粗体**、*斜体*、```代码块```)转为HTML标签
  │  - 处理表格、标题(##→<b>)、列表、分隔线
  │  - 【bug点】此处不处理裸<blockquote>！
  │
  ▼
② render_for_telegram_html(markdown_text)   # frontends/tg_html.py
  │  - 抽取代码块→token占位
  │  - normalize_markdown_artifacts()
  │  - 处理blockquote: 把 <blockquote>xxx</blockquote> 或 > xxx 包装为 <tg-quote>
  │  - 恢复代码块token
  │
  ▼
③ _TelegramHTMLSanitizer                    # frontends/tg_html.py:224
  │  - HTMLParser白名单过滤
  │  - 允许标签: b/strong/i/em/u/s/code/pre/a/blockquote/tg-quote/br 等
  │  - 允许属性: href(a标签)、class(tg-spoiler)
  │  - 自动关闭未闭合标签
  │
  ▼
④ split_html_text(html, limit=4096)         # 分割长消息
  │  - token化HTML标签，按limit切割
  │  - 自动关闭/重开标签保持结构完整
  │
  ▼
⑤ Telegram API sendMessage(parse_mode='HTML')
```

## §2 关键数据结构

### 2.1 允许的HTML标签 (`_ALLOWED_TAGS`)
`b, strong, i, em, u, ins, s, strike, del, code, pre, a, blockquote, tg-quote, tg-spoiler, span, br`

### 2.2 代码块token化
- 代码块被替换为 `@@CODE_n@@` token，避免sanitize破坏
- 处理完后恢复为 `<pre><code class="language-xxx">...</code></pre>`

### 2.3 Telegram HTML限制
- 单消息 ≤ 4096字符
- `<pre>`内不可嵌套标签
- `<a href>`仅允许http/https/mailto/tg协议

## §3 已知Bug与Fix记录

### Bug-001: Summary裸<blockquote>未闭合（2026-05-09修复）

**症状**: Summary小消息中出现原始`<blockquote>`文本显示，而非Telegram引用样式

**根因**: LLM输出的Summary文本含裸`<blockquote>`（无`</blockquote>`闭合），直接进入`render_for_telegram_html`时：
- `normalize_markdown_artifacts()`不处理裸HTML标签
- `render_for_telegram_html()`的blockquote处理正则要求闭合标签`</blockquote>`
- 裸标签穿透sanitizer后被Telegram API当无效HTML显示为原文

**修复位置**: `tgapp.py` 第584-586行（Summary发送前）
```python
# fix: 清理裸<blockquote>标签，防止穿透sanitizer显示为原文
cleaned = re.sub(r'<blockquote>', '<_quote_>', cleaned)
cleaned = re.sub(r'</blockquote>', '</_quote_>', cleaned)
text = re.sub(r'<_quote_>(?:(?!</_quote_>).)*', '', cleaned) or cleaned
```
**逻辑**: 先把`<blockquote>`转义为`<_quote_>`占位→移除无闭合的残留→确保干净文本进入HTML渲染

### 通用避坑规则
1. LLM输出可能含任意HTML标签片段 → **发送前必须清理裸标签**
2. Summary消息不走主回复渲染流程 → 需要独立的HTML清理
3. 正则清理裸标签时，**先转义再移除**，避免误伤闭合的正常blockquote

## §4 修改指南

### 新增允许标签
1. 在`_ALLOWED_TAGS` frozenset中添加
2. 在`_TelegramHTMLSanitizer.handle_starttag`中添加属性白名单（如需）
3. 在`_close_stack_until`中添加标签类型（block/inline）

### 修改normalize逻辑
1. 只改`normalize_markdown_artifacts()`函数
2. 注意：此函数在`render_for_telegram_html`中调用，不要在此处引入未闭合标签

### 新增预处理步骤
1. 在`tgapp.py`的消息发送入口添加清理逻辑（参考§3 Bug-001 fix）
2. 保持`render_for_telegram_html`本身干净，预处理放在外层

## 🛑 验证门禁

| # | 验证项 | 方法 | 预期 |
|---|--------|------|------|
| 1 | blockquote闭合 | 发送含`> 引用`的文本 | TG显示灰色引用块 |
| 2 | 裸标签清理 | Summary含`<blockquote>`文本 | 不显示原始标签 |
| 3 | 代码块完整 | 发送含代码块的消息 | 语法高亮、无截断 |
| 4 | 长消息分割 | 发送>4096字符 | 自动分段、格式完整 |

最终裁定：`VERDICT: PASS` / `VERDICT: FAIL`
