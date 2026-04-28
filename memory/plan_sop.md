# Plan Mode SOP
> 版本: v1.0 | 最后更新: 2026-04-28

**触发**：3步以上有依赖/多文件协同/条件分支/需并行 | **禁用**：1-2步简单任务直接做
任务开始前必须先创建工作目录 `./plan_XXX/`（XXX=任务英文短名）
单独使用一个code_run({'inline_eval':True, 'script':'handler.enter_plan_mode("./plan_XXX/plan.md")'})进入plan模式

---

## 一、探索态（规划前置，必须执行）

⛔ **硬性规则**：主agent禁止直接探测环境→必须委托subagent（≤2次重试）。subagent只读不写。目标：搞清①环境现状 ②可用SOP ③关键不确定点。

### 步骤1：创建目录（必做） + SOP匹配 + 设置plan标志（主agent直接做）

1. 创建工作目录 `mkdir plan_XXX/`
2. 读 `sop_index.md` 匹配可用领域SOP
3. 更新checkpoint：`[任务] XXX | [需求] 一句话 | [约束] 关键限制 | [匹配SOP] ... | [进度] 探索态`

### 步骤2：启动探索subagent（监察模式，`--verbose`）
按 subagent.md 启动，input: 任务→写入 `exploration_findings.md` | 探测: 按类型(代码/浏览器/自动化/数据)选做→首5+尾5抽样 | 约束: 只读, ≤10工具调用, 记录规模(文件数/行数/页面数)供委托判断

### 步骤3：监察等待 + 读取结论
观察output.txt (非盲sleep): 读方向+原始数据 → 偏了写 `_intervene` → 缺上下文写 `_keyinfo` → 够就 `_stop`。`[ROUND END]`→读findings→进入规划态。主agent监察获得的一手认知直接用于规划。

---

## 二、规划态（含审查门）

### 步骤4：读领域SOP → 写plan.md

先读探索态匹配到的SOP，然后写plan骨架。允许"⚠待确认"，禁止以"没调研清楚"推迟。

**[D] 委托标注规则**：写每个步骤时，结合探索发现评估操作量，符合以下任一条件则标 `[D]`：

- 需要读取大量代码/文件（预估 >3个文件或 >100行）
- 需要浏览网页并提取信息
- 需要执行 3 次以上重复性操作
- 需要运行测试/构建并分析输出

不标 `[D]` 的情况：读/更新 plan.md、单文件小幅修改、ask_user、简单一次性命令

**plan.md格式**：

```markdown
<!-- EXECUTION PROTOCOL (每轮必读，这是你的执行指南)
1. file_read(plan.md)，找到第一个 [ ] 项
2. 该步标注了SOP → file_read 该SOP的🔑速查段
3. 执行该步骤 + Mini验证产出
4. file_patch 标记 [ ] → [✓]+简要结果，然后回到步骤1继续下一个[ ]
5. 所有步骤（包括验证步骤）标记完成后 → 终止检查：file_read(plan.md)确认0个[ ]残留
⚠ 禁止凭记忆执行 | 禁止跳过验证步骤 | 禁止未经终止检查就结束 | 禁止停下来输出纯文字汇报
💡 搬砖活（读大量代码/文件/网页/重复操作）优先委托subagent，保持主agent上下文干净
-->
# 任务标题
需求：一句话 | 约束：关键限制

## 探索发现
- 发现1：XXX（来源：file_read/web_scan/code_run）
- 发现2：YYY
- 不确定点：ZZZ

## 执行计划
1. [ ] 步骤1简述
   SOP: xxx_sop.md
2. [D] 步骤2简述（委托subagent执行）
   SOP: yyy_sop.md
   依赖：1
3. [P] 步骤3简述（并行，读subagent.md执行Map模式）
   SOP: yyy_sop.md
4. [?] 步骤4（条件分支）
   SOP: (无) ← 高风险
   条件：X成功→4.1，否则→4.2

---

## 验证检查点
N+1. [ ] **[VERIFY] 启动独立验证subagent**
     SOP: verify_sop.md plan_sop.md
     操作：读plan_sop.md第四章内容 → 准备verify_context.json → 启动验证subagent → 读取VERDICT → 按结果处理
     ⚠ 不可跳过，不可在未启动subagent的情况下标记[✓]

---
```

### 步骤5：自检清单（主agent逐项检查）

| # | 检查项 |
|---|--------|
| 1 | 探索发现是否都反映在plan中？ |
| 2 | 每步SOP标注合理？该SOP真能解决该步？ |
| 3 | 步骤间依赖正确？有无隐含依赖？ |
| 4 | 高风险步骤（SOP:无/不可逆）有清晰执行思路？ |
| 5 | 粒度合适？"处理所有文件"→展开具体条目 |
| 6 | **[D]标注**：读大量代码/网页/重复操作→标[D]委托subagent |
| 7 | **[VERIFY]步骤**：必须有，不可跳过 |

### 步骤6：用户确认

ask_user 确认plan后才能转入执行态。**⛔ 用户未确认不得执行。**

### 步骤7：转入执行态

更新checkpoint：`[执行] plan.md | 当前：步骤1 | ⚡有[P]标记必须读subagent.md执行Map模式`

---

## 三、执行态循环

> **核心原则：连续执行，不停顿汇报。** 做完一步立即 file_read(plan.md) 找下一个 `[ ]`，直到全部完成。

### 每轮流程

1. **读plan** — `file_read(plan.md)` 定位第一个 `[ ]` 项
2. **读SOP** — 该步标注了SOP → 先 file_read 该SOP
3. **检查标记** — `[D]`标记 → 必须委托subagent执行，主agent只收结果摘要；`[P]`标记 → 读 subagent_sop.md 执行Map模式；`[?]`条件 → 评估条件选分支，未选标[SKIP]
4. **执行** — 无特殊标记的步骤由主agent自己执行
5. **Mini验证** — 快速确认产出存在且合理（file_read确认非空、检查exit code等）
6. **标记完成** — `file_patch` 标记 `[ ]` → `[✓ 简要结果]`（进度写入plan.md）
7. **继续** — 立即回到步骤1，file_read(plan.md) 执行下一个 `[ ]`

### 终止检查（最后一步标记后，不可跳过）

file_read(plan.md) 全文扫描，确认所有步骤（含[VERIFY]）均为 `[✓]`/`[✗]`，0个 `[ ]` 残留。
输出：`🏁 终止检查：[总步数]步全部完成，0个[ ]残留 → 任务结束`
若发现遗漏 → 继续执行，禁止声称完成。

### ⚠ 执行态禁令

- **禁止凭记忆执行**：每次做新步骤前必须 `file_read(plan.md)`，不可"我记得下一步是..."
- **禁止跳过验证步骤**：[VERIFY]步骤是强制的，不可以"任务都做完了"为由跳过
- **禁止未经终止检查就结束**：最后一步标记后必须 file_read 全文扫描确认0个[ ]残留，输出🏁终止确认行
- **禁止停下来输出纯文字汇报**：做完一步后必须立即 file_read(plan.md) 继续，不要输出进度总结

### 💡 动态委托原则

即使步骤未标 `[D]`，执行中发现以下情况时，主动委托 subagent 处理：

- 需要读取大量代码/文件才能理解上下文（>3个文件或预估 >100行）
- 需要反复试错调试
- 需要浏览网页提取信息

做法：起 subagent 完成具体操作，要求返回精简摘要，主 agent 基于摘要继续决策。保持主 agent 上下文干净是第一优先级。

---

## 四、验证态（subagent独立验证）

> 全部步骤[✓]后进入。**强制**启动独立subagent做对抗性验证，避免上下文污染。

### 触发条件

- 所有执行步骤标记为 `[✓]`
- **所有plan模式任务必须经subagent验证**（主agent有确认偏误，易被表面成功迷惑）

### 步骤8：准备验证上下文

在 `./plan_XXX/` 下创建 `verify_context.json`，包含：

- task_description：原始任务描述（用户原话）
- plan_file：plan.md绝对路径
- task_type：code|data|browser|file|system
- deliverables：交付物列表（type/path/expected）
- required_checks：必做检查列表（check/tool）

**传什么**：任务描述、plan路径、交付物清单、必做检查。**不传**：执行过程、调试记录。

### 步骤9：启动验证subagent → 详见 `verify_sop.md`

简要流程：创建 `verify_context.json` → 启动验证subagent（传路径） → subagent读verify_sop.md自行执行 → 收集VERDICT

FAULT处理：FAIL→回执行态修复→最多2轮→超限 ask_user

---

## 五、失败处理

1. **记录**：checkpoint中 `step_X: [FAILED] 原因 (retry: N/3)`
2. **重试**：网络超时→自动重试3次(2s/4s/8s) | 配置错误→询问用户 | 其他→标[✗]跳过
3. **subagent失败**：查stderr.log→明确错误主agent修正重启 | 未知错误重试1次 | 最多重启2次
4. **依赖传播**：步骤失败后，后续依赖项标[SKIP]
5. **plan有误**：回退到规划态修正plan.md，重新过审查门

## 强制约束

- 每项必须有独立完成判据
- 禁止"处理所有文件"，必须展开具体条目
- 一次只做一项；计划有误回规划态修正
- 不可逆操作前多验证一步
