---
name: obsidian_blog_sync
description: 同步Obsidian笔记到Hugo博客并维护发布流程
---
# obsidian_blog_sync_sop — Obsidian→Hugo Blog发布 (v2.0)

## 执行摘要
1. Blog文章统一放在 Vault 的 `00.Chronicles/Blog/`，不要放 `02.Domains/`。
2. 发布门禁：frontmatter 有 `title` + `status: published` + `blog`/`blog/*` 标签。
3. 先 `--preview`，确认无错误后再同步到 Hugo Blog。

## 路径与工具
- Vault: `D:\Documents_Learn\Personal\Obsidian\Codex Vitae`
- Blog: `D:\Creative_Studio\WorkSpace\yeekox-blog`
- Blog源目录: `00.Chronicles/Blog`
- 脚本: `memory/obsidian_blog_sync.py`

## Obsidian文章落点
- 博客文章属于时间性输出，落在：`00.Chronicles/Blog/`
- `02.Domains/` 只放“我是谁、我长期关注的身份和角色”，扁平文件，不做博客树。
- 博客模板保持轻量：只给必要 frontmatter，不固定正文结构；正文按当次主题自由写。

## 发布门禁
```yaml
title: 文章标题
status: published
tags:
  - blog          # 或 blog/tech、blog/essay 等
```
- `status: archived` 跳过。
- 缺 `title` 跳过并报错。
- 无 `blog`/`blog/*` 标签不发布。

## Tag→Hugo目录映射
- `blog` 或 `blog/tech` → `content/blog/`
- `blog/essay` → `content/essay/`
- `blog/project` → `content/projects/`
- `blog/novel` → `content/novel/`
- `blog/gaming` → `content/gaming/`
- 输出文件名统一为 `xxx.zh-cn.md`

## 命令
```bash
python ../memory/obsidian_blog_sync.py --preview
python ../memory/obsidian_blog_sync.py
python ../memory/obsidian_blog_sync.py --file "标题"
python ../memory/obsidian_blog_sync.py --legacy --preview
```
- 默认只扫描 `00.Chronicles/Blog/`。
- `--file` 在默认源目录内按标题/文件名匹配。
- `--legacy` 才兼容扫描全库；全库扫描时会跳过 `00.Chronicles` 下非 Blog 内容，避免把 Daily/日志误发布。

## 转换规则
- 清理 Obsidian-only 语法：Dataview 代码块、`= this.xxx` 行等。
- 双链转普通文本：`[[A|B]] → B`，`[[A]] → A`。
- Hugo frontmatter 自动生成：`title/date/tags/draft:false`。
- Obsidian `blog/*` 标签转 Hugo 标签时去掉 `blog/` 前缀。

## 红牌
- ❌ 不要把博客放进 `02.Domains/`。
- ❌ 不要全库默认扫描；需要旧文章迁移才用 `--legacy`。
- ❌ 不要跳过 `--preview`。
- ❌ 不要在博客模板里固定正文提纲，主人的博客每次可能说不同的事。

## 🛑 验证门禁
- `python ../memory/obsidian_blog_sync.py --preview` 通过。
- 报告里无误发布的 Daily/Domain/Library 笔记。
- Hugo内容路径符合 tag 映射。
- 必要时在 Blog 目录运行 `hugo server` 预览。

`VERDICT: PASS` / `VERDICT: FAIL`
