---
name: obsidian_tag_governance
description: 治理Obsidian全库标签命名空间与收敛规则
---
# [L3 SOP] obsidian_tag_governance_sop — 全库标签治理SOP (v1.0, 干练)
> Vault: `Codex Vitae` | 单职责: 全库tags统一命名空间/治理/巡检

## 1. 触发
主人指令: 统一/Obsidian tags/清理标签/检查tag → 激活本SOP。
不处理: Library专属tag见 `obsidian_manage_library_sop` §1.1。

## 2. 命名空间体系（硬规则）
每条tag必须有前缀，禁裸标签：
- `topic/` — 学科/主题 (topic/economics, topic/typescript)
- `type/` — 对象类型 (type/book, type/map, type/note, type/domain, type/quest, type/daily)
- `source/` — 来源渠道 (source/pocket, source/rss, source/zhihu)
- `exam/` — 考试分类 (exam/gongji, exam/programming)
- `project/` — 项目标记 (project/agentdock, project/blog)
- `status/` — 状态标记 (status/draft, status/archived) — 仅用于Daily模板

权威依据: `03.Library/Notes/00.Meta/03.Library Tag Taxonomy.md` (命名空间清单+频率统计)

## 3. 治理流程
① **扫描现状** → 提取全库 `tags:` 字段, 分类: 合法/裸/旧式/颜色值#xxxxxx
② **映射规则**:
   - old_tag → 新tag (保持语义不变, 仅加前缀/标准化)
   - 颜色值 `#xxxxxx` → 排除, 非tag
   - 空标签 `tags: []` → 清除(空字段无意义)
③ **批量替换**: 按置信度分批 → A(确定)→B1(模糊)→B2(中)→B2-mini(专清)
④ **终检门禁**:
   - 旧式遗留tag = 0
   - 裸标签(无前缀) = 0 frontmatter, 正文#标签非治理范围
⑤ **巡检维护**: Tags治理完成后, 每次Obsidian操作前扫全库tags状态, 发现问题直接修

## 4. 避坑（教训）
- ⚠️ YAML禁用嵌入式`#`值: `source/pocket`否改`source/getpocket`→YAML解析为颜色值
- ⚠️ 空frontmatter `---\n---` 陷阱: `yaml.safe_load()` 返回 `None` 而非 `{}`, 需额外判 `if fm is None: fm = {}`
- ⚠️ 引号包裹: 含`.`的tag必须加引号 `"topic/programming/typescript"`
- ⚠️ 批次替换后复检: 每批替换完立即抽查+回滚方案就绪
- ⚠️ 换tag不换old_tag文件名: tag变动不涉及文件名/路径变动

## 5. 工具委托
- 扫描全库tags: 自写Python脚本(glob+yaml.safe_load)提取tags字段；`vault_tools.py inspect`仅`--help`无`--tags`参数
- 验证单文件: `python ../memory/verify_note.py "<路径>"`
- 分类检查: `python ../memory/vault_classifier.py --all`

## 🛑 终检门禁
|检查项|状态|
|--------|------|
|旧式遗留tag = 0?|
|裸标签 = 0 frontmatter?|
|颜色值已排除?|
|空tags:[]已清理?|
|Tag Taxonomy存在且最新?|
