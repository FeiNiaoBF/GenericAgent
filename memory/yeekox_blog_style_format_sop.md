# [L3 SOP] yeekox_blog_style_format_sop — YeelightBlog 写作规范 (v1.0)
> 基于 16 篇博文分析 + Google blog best practices
> 通用格式 → [`chi_format_sop`](../memory/chi_format_sop.md)

## 执行摘要（≥1步执行前必读）
① 确认文章类型(教程/工具/理论/项目)→② 按frontmatter+结构写→③ `status:published`后`obsidian_blog_sync.py`推送 → 🛑 过验证门禁

## 1. 博客画像
| 类型 | 占比 | 代表 |
|------|------|------|
| 技术教程/笔记 | 60% | cache, gdb, k8s, http, lock, bit, makefile |
| 短篇笔记 | 15% | redis_timeout, scm |
| 好奇探索 | 15% | beef, futures |
| 元博/个人 | 10% | plan_cs |

核心风格: 对话式开篇("想一个问题")、第一人称、类比思维、短段落、代码+注释混合。

## 2. 文章类型策略

### 2.1 技术教程（主力60%）
结构: 开篇问题 → 核心概念(类比≤3段) → 逐步展开(概念+代码+踩坑) → 总结+来源
原则: 允许列表/表格，但每段开头/结尾有自己的话，代码配解释，外部链接放文末。

### 2.2 短篇笔记（15%）
至少200字: 一句话定义 + 为什么值得知道 + 你的理解 + 参考链接。内容不足→放Obsidian不发布。

### 2.3 好奇探索（15%）
结构: 现象/问题 → 原因分析(可编号) → 怎么判断/怎么用 → 来源

### 2.4 个人元博（10%）
保持 Hugo shortcode 丰富 + 参考文献引用即可。

## 3. 写作流程
- **写前(5min)**: 确定类型A/B/C/D → 核心问题一句话写下来 → 查Obsidian草稿/站内引用
- **初稿**: 先写正文不边写边改 → 第一段:是什么+为什么写 → 结尾收束
- **发布前检查**: 标题清晰/第一段切入/主观观点/代码有解释/有收尾
  - tags≥2个 / front matter完整 / 作者统一 / 图片链接有效 / `<!--more-->`分隔符

## 4. 反AI腔调
❌ 禁用: 首先/其次/综上所述/值得注意的是/有着重要意义/该文/本文/笔者/"在当今XXX背景下"/"随着XXX不断发展"
✅ 你的腔调: "想一个问题…"/"说实话…"/"我觉得…"/"还挺…"/"哈哈哈"/"笑死"/"说白了就是…"/emoji点缀🚧✏️⭐
判断标准: 读一遍问自己"我跟朋友聊天会这样说吗？"

## 5. 发布技术规范
- Front matter:
```yaml
title: "..."
date: YYYY-MM-DD
draft: false
authors:
  - name: "Yeelight"
    link: https://github.com/FeiNiaoBF
    image: https://github.com/FeiNiaoBF.png
toc: true
comments: true
tags: ["tag1", "tag2"]
```
- 发布: status:published → `obsidian_blog_sync.py` → Hugo deploy

## 🛑 验证门禁（执行前/后强制检查）

| 检查项 | 状态 |
|--------|------|
| frontmatter字段完整(layout/title/date/tags)？ | |
| 类型匹配(教程60%|工具20%|理论15%|项目5%)？ | |
| status:published→已触发blog_sync？ | |
| 交叉引用路径有效？ | |

最终裁定：`VERDICT: PASS` / `VERDICT: FAIL`
