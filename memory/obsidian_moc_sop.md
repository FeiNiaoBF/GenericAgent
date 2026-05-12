# obsidian_moc_sop — Obsidian MOC地图 (v1.0)
> Vault: `D:\Documents_Learn\Personal\Obsidian\Codex Vitae`
> 单职责：只处理 MOC/地图笔记创建、字段、同步。知识库分类见 `vault_knowledge_sop.md`。

## 执行摘要
① 判断MOC层级 → ② 选模板 → ③ 填字段/边界 → ④ 加精选导航/Dataview → ⑤ 同步父级/总览 → 🛑

## MOC类型
| 类型 | 用途 | 模板 | 指向 | 必填 |
|---|---|---|---|---|
| 顶层MOC | 学科/领域领航 | `01-05Cat·LLM版.md` | 子MOC | 无`moc`字段 |
| 主题MOC | 主题知识聚合 | `MOC.md` v3.0 | 笔记+Dataview | `moc` |
| 次级MOC | 学习/子领域 | `MOC.md`精简版 | 子主题/笔记 | `level:sub` + `parent` |

决策：学科领域级→顶层MOC | 领域内主题≥3篇→主题MOC | 学习类子领域→次级MOC。

## 主题MOC字段
`type:moc | status | moc:"[[MOC名]]" | scope`

`scope`写地图边界：覆盖什么、不覆盖什么、≥2个核心问题。

## 标准区块（按需）
1. 🗺️地图边界：scope + 核心问题
2. 📚精选导航：≥3篇核心笔记，双链+一句定位
3. 🧠知识断言：`FROM "05.Knowledge" WHERE contains(moc,"[[本MOC]]")`
4. 📊动态索引：`FROM "03.Library/Notes" WHERE contains(moc,"[[本MOC]]")`
5. 🔗概念关系：正文自然生长
6. 🌱待探索：待学主题+优先级
7. 🏷️子MOC：`FROM "03.Library/Maps" WHERE contains(moc,"[[父MOC]]")`

## 同步清单
- 顶层MOC：新增精选导航项。
- 主题MOC：关联笔记/断言的 `moc` 字段可被Dataview命中。
- 次级MOC：`parent` 指向父MOC。
- MOC总览：新增或更新对应行。

## 红牌
- 🚫 顶层MOC与主题MOC模板混用。
- 🚫 顶层MOC填写 `moc` 字段。
- 🚫 主题MOC缺 `moc` 或 `scope`。
- 🚫 为少于3篇笔记的普通主题强建MOC。
- 🚫 用MOC替代正文自然双链。

## 🛑 验证门禁
路径在 `03.Library/Maps` 或对应领域地图位置 | 类型判断正确 | 模板正确 | 必填字段完整 | Dataview查询可命中 | 父级/总览已同步

`VERDICT: PASS` / `VERDICT: FAIL`
