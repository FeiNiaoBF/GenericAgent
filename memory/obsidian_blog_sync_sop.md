# obsidian_blog_sync_sop — Obsidian→Blog发布 (v1.0)

## 执行摘要
1. 笔记status:published + tags含blog/xxx → 映射目标目录
2. 清理Obsidian-only语法(dataview/双链) → `--preview`预览
3. hugo server验证 → 提交发布 → 🛑

## Tag→目录映射
`blog/tech`→`content/blog/` | `blog/essay`→`content/essay/` | `blog/project`→`content/projects/` | `blog/novel`→`content/novel/` | `blog/gaming`→`content/gaming/` | `blog`(无二级)→`content/blog/` | 无blog*或archived→不发布
文件名统一`xxx.zh-cn.md`

## 发布命令
```bash
python ../memory/obsidian_blog_sync.py [--preview] [--file "Note Title"]
```
`--preview`安全模式 | `--file`指定单文件 | 不指定→全量扫描

## Frontmatter转换
```yaml
# Obsidian→Hugo Hextra
type:note | tags:[blog/tech] | status:published → title:"标题" | date:YYYY-MM-DD | tags:["tech"] | draft:false
```

## 前置条件
Blog路径: `D:\Creative_Studio\WorkSpace\yeekox-blog` | 模板Note.md兼容 | 发布后`hugo server`预览

## 红牌
- ❌ status≠published→不处理 | ❌ blog无二级tag→默认blog | ❌ dataview语法→发布前清理
- ✅ `--preview`先预览 | ✅ 双链`[[链接]]`替换为Hugo格式

## 🛑 验证门禁
`--preview`通过 | Obsidian语法已清理 | 双链已替换 | frontmatter完整

`VERDICT: PASS` / `VERDICT: FAIL`
