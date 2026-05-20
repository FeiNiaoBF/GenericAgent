---
name: sop_refactor
description: 重构、去重、升级SOP并同步记忆索引
---
# sop_refactor_sop · SOP重构/去重/升级 (v3.1)
> 复用: `file_read`关键词对比 | `code_run+Python` diff | `file_patch`精确替换 | L2/L1 patch

## 执行摘要
① 审计→② 读全文→③ patch+升版→④ 校验引用/编号→⑤ 同步L2/L1→⑥ 🛑门禁

## 零、安全审计（代码重构前必做）

|检查项|手段|
|--------|------|
|命令白名单|`_handle_slash_cmd` 用 `set` 白名单，拒绝未知命令|
|路径穿越|用户输入路径处 `os.path.realpath` 校验，拒绝 `../`|
|动态属性|禁止外部设 `handler._xxx`；改用构造函数初始化+形式参数|
|Hook API|提供 `register/unregister` 方法，禁直接操作 `handler._hooks`|
|死代码|搜未使用私有钩子，确认无残留后删除|

流程：审计→P0安全>P1封装>P2死代码>P3异味→逐项修复+grep验证→回归→🛑门禁

## 一、触发场景
内容重叠(两SOP同主题) | 版本升级 | 层级迁移(L3细节跑进L2) | 结构腐烂(编号断裂/检查表冗余)

## 二、重构流程（6步闭环）

1. 重叠检测: `file_read`按关键词对比范围
2. 归属: 通用→角色卡 | 技术/平台→各SOP | 引用最多1级(A→B)
3. 去重: 保留方先验完整→移除方删重叠+加 `> 📄 [FILE:path]`；整节删时留空节防编号乱
4. 结构: 重排编号 | 同步检查表 | 升版本(v3→v4)
5. 记忆: L3改完→L2描述匹配→L1触发词更新
6. Git: `refactor(短名): 概述` + 明细

## 三、批量操作模式
适用：多文件统一加装摘要/门禁/格式

① 全量扫描(SG/S/NONE)→② 分批5-10→③ 注入模板(摘要先/门禁后)→④ 重扫迁移→⑤ 修异常→⑥ 100%达标

|坑|解法|
|----|------|
|patch失败不知原因|每批后重扫确认状态迁移|
|门禁标题不统一|强制 `## 🛑 验证门禁`|
|上下文过长|每批≤10，读头尾grep验证|

## 避坑
- 引用: 改后grep `FILE:`路径有效
- 版本: 搜`(v\d+)`确认已升
- 编号: 删节后审全文编号
- 记忆: L3改后搜L2本SOP描述是否匹配
- 顺序: 角色卡源先改，SOP引用后改

## 🛑 验证门禁
全文已读？| 版本号已更新？| 交叉引用闭环？| L2+L1已同步？| 编号无断链？
`VERDICT: PASS` / `VERDICT: FAIL`

---

## 进度跟踪 (2026-05-09 SOP优化)
### Step1: 删除冗余 ✅
✅ 旧角色卡/网页启动细节已并入源SOP；引用链与`sop_index.md`已更新

### Step2: 合并9→3组 + 内化3个 ✅
- TG→`telegram_send_unified_sop.md` | 学习助教→`learning_tutor_study_sop.md` | 后台/定时→`task_backend_manage_sop.md`
- MOC已拆出→`obsidian_manage_moc_sop.md`；知识库保留分类职责→`obsidian_knowledge_sop.md`

### Step3: 同步记忆+Git ⬜
