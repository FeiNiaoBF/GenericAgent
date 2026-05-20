---
name: sop_creation
description: 创建一个职责单一、可复用、可验证的新SOP
---
# 🔧 SOP 创建流程 (Meta-SOP)

> 用途：当唧需要基于外部资源创建新SOP时的标准流程
> 触发：主人要求学习/集成新能力，或唧发现需要新SOP时

## 核心流程（3步）

### Step 1：搜索 & 收集
1. **先查已有**：`file_read` 搜 `../memory/*.md` 文件名+关键词，确认不重合
2. **外部搜索**（按需选源）：
   - skills.sh / GitHub / npm / PyPI / Google
   - 用Python抓取详情页（requests+BeautifulSoup）
   - React壳页面 → 用浏览器 `web_execute_js` 提取
3. **批量收集**：TOP N相关内容存入 `./temp/` 临时文件

### Step 2：排名 & 筛选
用 `code_run` 脚本批量评分：
```
评分维度（每项1-5分）：
- 相关性：与主人需求的匹配度
- 质量：内容深度、结构清晰度
- 实用性：可直接转化为SOP/脚本
- 独特性：与现有SOP无重合
总分 = 相关性×3 + 质量×2 + 实用性×2 + 独特性×1
```
输出TOP N排名表给主人确认。

### Step 3：整合 & 脚本化
1. **融合**：提取多个来源的核心方法论，合并为一份SOP
2. **去重**：对比现有SOP，只保留新增内容
3. **结构**：遵循 `memory_management_sop.md` 的SOP模板
4. **脚本化**：固定重复操作 → 写Python脚本到 `../memory/*.py`
5. **索引**：更新 `global_mem_insight.txt` + `sop_index.md`

---

## ⚠️ 关键约束

- **不重合**：创建前必查现有SOP，新SOP只记录增量
- **不过度**：3步内完成，不在搜索环节无限扩展
- **脚本化阈值**：同一操作重复≥2次 → 脚本化
- **主人确认**：排名结果先展示，主人OK再整合

---

## 📁 配套脚本

|脚本|用途|位置|
|------|------|------|
|`skill_scraper.py`|批量抓取skills.sh/GitHub内容|`../memory/`|
|`skill_ranker.py`|自动评分排名|`../memory/`|

（脚本见下文）
