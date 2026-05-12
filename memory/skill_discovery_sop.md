# Skill Discovery & Integration SOP · 外部技能发现-评估-集成

**触发**：主人需求当前SOP/工具无法满足 | **禁用**：已有SOP能解决的不重复搜索

## 1. 先查已有能力 → 需求拆解
1. 搜 `../memory/` SOP+sop_index.md+L2 global_mem → 找到直接用，跳过发现
2. 没找到→拆解：核心能力(硬性) / 期望能力(软性) / 约束(平台/语言/依赖/许可)

## 2. 层级搜索（由近到远禁止跳级）

| L1 本地已安装 | L2 社区(awesome/官方) | L3 GitHub搜索 | L4 Google |
|---|---|---|---|
| npm/pip/PATH/scripts/ | npmjs/pypi/awesome-* | `{q} stars:>1000 pushed:>2024` | web_search_sop规则 |

## 3. 质量评估 ⛔禁止跳过直接推荐

| ✅通过 | ⚠️谨慎 | ❌不推荐 |
|---|---|---|
| ≥1K星/装, 6月内更新, 官方维护, README完整, MIT/Apache | 100-1K, 6-12月, 活跃个人 | <100, >12月无更新, 无文档, 无许可 |

评估：读README → 查releases频率 → 查contributors → 查issues前10 → 对比3+候选选最优
快速验证：Docker/Demo优先试 → 读测试理解用法

## 4. 安装
- 前置：不冲突+版本兼容+许可OK → **不可逆操作必ask_user**
- 优先级：venv/npx隔离 > pip/npm标准 > git clone手动
- 后验：`--version` + `--help` + 最小case功能验证

## 5. 效果验证
- 核心能力最小case测试 + 边界输入不崩溃
- 失败处理：1次→读文档修配置 → 2次→回L3/L4找替代 → 3次→ask_user

## 6. 知识沉淀
- 成功→L2记录工具名/用途/安装方式 + 更新sop_index
- 失败→L2记录失败原因 + sop_index标注"不推荐"
