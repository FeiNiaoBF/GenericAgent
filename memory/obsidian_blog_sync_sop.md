# [L3 SOP] obsidian_blog_sync_sop — Obsidian→Blog发布SOP (v1.0)

## 执行摘要（≥1步执行前必读）
1. 确认笔记 status:published + tags含blog/xxx → 映射目标目录(content/blog/等)
2. 清理Obsidian-only语法(dataview双链等) → 双链替换/删除 → --preview预览
3. hugo server验证无报错 → 提交发布 → 🛑 过验证门禁

## 1. Tag→Blog目录映射规则

| Obsidian tags | status条件 | Blog目标目录 | 文件名规则 |
|---|---|---|---|
| `blog/tech` | published | `content/blog/` | `xxx.zh-cn.md` |
| `blog/essay` | published | `content/essay/` | `xxx.zh-cn.md` |
| `blog/project` | published | `content/projects/` | `xxx.zh-cn.md` |
| `blog/novel` | published | `content/novel/` | `xxx.zh-cn.md` |
| `blog/gaming` | published | `content/gaming/` | `xxx.zh-cn.md` |
| `blog` (无二级tag) | published | `content/blog/` | `xxx.zh-cn.md` |
| 无 `blog*` tag 或 status≠published | — | 不发布 | — |
| 含 `archived` tag | — | 不发布 | — |

## 2. 发布流程

### 手动流程
1. 在Obsidian中写好Note，tags按映射表填
2. 将 `status` 改为 `published`
3. 运行发布脚本 `obsidian_blog_sync.py`（自动扫描处理）
4. 检查Blog是否正常显示

### 自动同步 (脚本 opsidian_blog_sync.py)
```
python ../memory/obsidian_blog_sync.py [--preview] [--file "Note Title"]
```
- `--preview`：只预览不实际写入（安全模式）
- `--file`：只处理指定笔记（不指定则全量扫描）

### 脚本做了什么
1. 扫描Obsidian vault中 `status: published` 且含 `blog` tag的笔记
2. 按tags映射到Blog目录
3. 转换frontmatter格式（Obsidian→Hugo Hextra）
4. 写入Blog对应目录
5. 生成发布报告

## 3. Frontmatter转换规则
```yaml
# Obsidian格式 →
---
type: note
tags:
  - blog/tech
status: published
title: 自定义标题
created_date: 2026-04-25
---

# Hugo Hextra格式 →
---
title: "自定义标题"
date: 2026-04-25
tags: ["tech"]
draft: false
---
```

## 4. 前置条件
- Hugo Blog路径正确: `D:\Creative_Studio\WorkSpace\yeekox-blog`
- Obsidian模板 `Note.md` 的frontmatter与脚本兼容
- 发布后需在Blog目录 `hugo server` 预览

## 5. 红牌规则
- ❌ 忘记改 `status: published` → 脚本不处理
- ❌ tags写了 `blog` 但没写二级tag（如 `blog/tech`）→ 默认走blog
- ❌ 笔记内含Obsidian-only语法（如 ````dataview`）→ 发布前需清理
- ✅ 发布前用 `--preview` 预览一次
- ✅ 双链 `[[链接]]` 需手动替换为Hugo链接格式或删除

## 🛑 验证门禁（执行前/后强制检查）

| 检查项 | 状态 |
|--------|------|
| 已--preview预览(无异常)？ | |
| Obsidian-only语法已清理(dataview等)？ | |
| 双链已替换为Hugo格式或删除？ | |
| frontmatter字段完整？ | |

最终裁定：`VERDICT: PASS` / `VERDICT: FAIL`
