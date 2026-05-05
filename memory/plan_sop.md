# Plan Mode SOP

**触发**：3步以上有依赖/多文件协同/条件分支/需并行 | **禁用**：1-2步简单任务直接做
任务开始前必须先创建工作目录 `./plan_XXX/`（XXX=任务英文短名）
`code_run({'inline_eval':True, 'script':'handler.enter_plan_mode("./plan_XXX/plan.md")'})`

## 执行摘要（≥1步执行前必读）
① 判断复杂度(≥3步/多文件/分支/并行)→② 建plan_XXX目录+plan.md→③ 逐项执行/委托[D]/验证完成→④ 🛑 过验证门禁

## 🔑 速查

| 态 | 输入 | 主agent做 | 子产出 |
|---|------|----------|--------|
| 探索 | 任务需求 | mkdir+匹配SOP→启subagent→监察→收结论 | exploration_findings.md |
| 规划 | findings+SOP | 写plan.md→自检→ask_user确认 | plan.md |
| 执行 | plan.md | 逐步[ ]执行+标记[✓]→终止检查 | 交付物 |
| 验证 | 交付物清单 | 启subagent对抗验证→收VERDICT | result.md |

---

## 一、探索态（委托subagent，主agent只监察）

⛔ **硬规则**: 主agent禁直接探测→必须委托subagent | subagent禁写文件 | 启动失败重试≤2次

**步骤**: ①mkdir plan_XXX/ ②从L1匹配领域SOP ③更新checkpoint ④启探索subagent(角色=只读不写,读匹配SOP,≤10次调用)→写exploration_findings.md ⑤监察output.txt(按需_intervene/_keyinfo/_stop) ⑥收exploration_findings.md→写入plan.md「探索发现」段

**产出格式**: `## 环境现状` / `## 关键发现` / `## 风险/不确定点`（含数据规模供[D]判断）

---

## 二、规划态（含审查门）

### [D] 委托标注（写plan时评估每步）

标[D]条件（任一条）：需读>3个文件或>100行 / 需浏览网页提取信息 / 3次以上重复操作 / 需运行测试分析输出
不标[D]：读/更新plan.md / 单文件小改 / ask_user / 简单一次性命令

### plan.md 模板

```markdown
<!-- EXECUTION PROTOCOL (每轮必读，这是你的执行指南)
1. file_read(plan.md)，找到第一个 [ ] 项
2. 该步标注了SOP → file_read 该SOP的🔑速查段
3. 执行该步骤 + Mini验证产出
4. file_patch 标记 [ ] → [✓]+简要结果，然后回到步骤1继续下一个[ ]
5. 所有步骤（包括验证步骤）标记完成后 → 终止检查：file_read(plan.md)确认0个[ ]残留
⚠ 禁止凭记忆执行 | 禁止跳过验证步骤 | 禁止未经终止检查就结束 | 禁止停下来输出纯文字汇报
💡 搬砖活（读大量代码/文件/网页/重复操作）优先委托subagent -->
# 任务标题
需求：一句话 | 约束：关键限制

## 探索发现
- 发现1：XXX（来源：file_read/web_scan/code_run）
- 发现2：YYY
- 不确定点：ZZZ

## 执行计划
1. [ ] 步骤1简述
   SOP: xxx_sop.md
2. [D] 步骤2简述（委托subagent）
   SOP: yyy_sop.md
   依赖：1
3. [P] 步骤3简述（并行Map模式,读subagent.md）
   SOP: yyy_sop.md
4. [?] 步骤4（条件分支）
   条件：X成功→4.1，否则→4.2

---

## 验证检查点
N+1. [ ] **[VERIFY] 启动独立验证subagent**
     SOP: verify_sop.md plan_sop.md
     ⚠ 不可跳过，不可在未启动subagent的情况下标记[✓]
```

### 自检清单

□ 探索发现反映在plan? □ 每步SOP合理? □ 依赖正确? □ 高风险步有思路? □ 粒度OK(禁"处理所有文件")
□ 复杂步标[D]? □ 有[VERIFY]步?

### 用户确认 → 执行态

ask_user确认 → 更新checkpoint→`[执行] plan.md | ⚡有[P]标记读subagent.md执行Map`

---

## 三、执行态循环

**每轮**: file_read(plan.md)找首个[ ]→该步有SOP则读SOP→[D]委托subagent/[P]Map模式/[?]选分支→执行→Mini验证(非空/exit code)→file_patch标[✓]→立即循环下一个[ ]

**终止检查**: 最后步标记后file_read全文扫描→确认0个[ ]残留→输出`🏁 终止检查：[N]步全部完成，0残留→任务结束`

**禁令**: 禁凭记忆执行 | 禁跳过[VERIFY] | 禁未经终止检查结束 | 禁输出纯文字汇报

---

## 四、验证态（强制subagent独立验证）

全部步骤[✓]后进入。**必须**启动独立subagent对抗验证。

### verify_context.json → 启subagent → 收VERDICT

**准备**: 在plan_XXX/下创建verify_context.json: task_description/task_type/deliverables/required_checks（只传任务描述+交付物，不传执行过程）

**启动**: subagent角色=独立验证者，首步file_read verify_sop.md，每检查有工具调用证据，3轮内完成，输出result.md最后一行VERDICT: PASS/FAIL/PARTIAL

**处理**: FAIL→回执行态修复(附加[FIX]步)→重验证≤2轮→超限ask_user | PASS→标[VERIFY]为[✓]→更新checkpoint→确认完成 | 无VERDICT→从output.txt提取判断

### 修复循环

FAIL→提取失败项→plan.md追加[FIX]步→只修失败项→重验证→最多2轮

---

## 五、失败处理

1. check: `step_X: [FAILED] 原因 (retry: N/3)` | 网络超时→重试3次(2/4/8s) | 配置错误→ask_user | 其他→[✗]
2. subagent: 查stderr→修正重启 | 未知错误重试1次 | 最多重启2次
3. 依赖传播: 失败后后续标[SKIP] | plan有误→回规划态

## 强制约束

- 每项独立完成判据 | 禁"处理所有文件"展开具体条目
- 一次一项；plan有误回规划态 | 不可逆操作前多验证一步
- [D]执行中发现也能主动委托(读大量代码/反复试错/浏览网页提取)

## 🛑 验证门禁（执行前/后强制检查）

| 检查项 | 状态 |
|--------|------|
| plan_XXX目录已创建？ | |
| plan.md含独立完成判据？ | |
| 逐项执行未跳步？ | |
| 失败项已标[SKIP]或回规划态？ | |
| 不可逆操作前多验证？ | |

最终裁定：`VERDICT: PASS` / `VERDICT: FAIL`