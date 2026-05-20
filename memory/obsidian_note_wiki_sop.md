---
name: obsidian_note_wiki
description: 创建和维护单概念Wiki笔记、双链与嵌入引用
---
# Obsidian 笔记规范 · obsidian_note_wiki_sop (v1.1)
> 单职责：定义 Note（`type:note`）的书写规范。Vault架构见 `obsidian_knowledge_sop.md`，MOC规则见 `obsidian_manage_moc_sop.md`。

## 一、Note 定义

一篇笔记只解释一个概念/事件/方法/理论/人物/地点。
`type` 属性为 `note`，与 MOC（`type:moc`）区分——Note 不写索引，MOC 不写知识细节。

## 二、类型决定内容填充

笔记类型决定正文侧重（根据实际类型选写，非全部必填）：

|笔记类型|正文侧重|大纲风格|
|----------|----------|----------|
|概念|分类 + 定义 + 核心特征|精简，聚焦本质|
|事件|时间线 + 经过 + 关键节点|顺叙或编年|
|方法|步骤 + 操作要点 + 适用场景|流程式|
|理论|核心观点 + 论证逻辑 + 代表人物|论点驱动|
|人物|生平 + 贡献 + 主要思想|时间线或主题|
|地点|地理位置 + 特征 + 意义|描述式|

## 三、模板强制规则

必须使用 `99.System/Templates/Note.md`，含 frontmatter 属性：

```yaml
---
type: note
topic: 所属主题领域
tags: [tag1, tag2]
source: 来源
status: seedling/growing/evergreen
---
```

**frontmatter 必填项**: type, topic, tags, status
**frontmatter 选填项**: source, created, updated, related

## 四、Wiki 风格规范

1. **内容嵌入双链** — 遇到可形成独立知识点的词，直接 `[[内链]]`
2. **禁独立"关联"/"相关概念"区块** — 所有关联通过正文双链自然体现
3. **标题无emoji/无编号** — 纯Markdown，禁 `①`、`🧠`、`📌` 等符号；标题不得写成 `## 1.xxx`，编号放到标题下方列表
4. **内容厚实，大纲精简** — 大纲只写主干（不写每段子标题），内容写透
5. **非blog非vkb** — 不写心得体会/抒情/冗长评价，客观陈述知识
6. **粒度适中** — 如"马克思主义哲学基本原理.md"允许存在，只写该理论本身
7. **Obsidian Callout** — 使用官方写法 `> [!info]` / `> [!note]` / `> [!tip]`，多行内容继续以 `>` 开头

## 五、📚 依据

Notes末尾必附来源标题+作者+URL/书名。
GA写入前必须获取真实URL，禁编造。

## 六、写作流程

```
选题 → 确定类型 → 套模板 → 填充frontmatter → 写正文(内容厚) → 精简大纲 → 嵌入双链 → verify_note核验
```

**门禁**:
- 写前查已有笔记（防重复）
- 写后 `verify_note.py` 核验
- 同领域笔记保持术语一致
- 双链指向必须存在或将在本批创建

## 七、禁区

- ❌ 多知识点杂糅到一篇笔记
- ❌ 用 `##` 加 `①/🧠/📌` 等符号
- ❌ 用 `## 1.xxx` 这类“标题+编号”混写；改为干净标题 + 下方有序/无序列表
- ❌ 写心得体会/blog风格
- ❌ 遗漏frontmatter属性
- ❌ 在Note中使用MOC结构（大量双链索引）
- ❌ 强行用 `## 相关概念` 分区（改用正文双链）
