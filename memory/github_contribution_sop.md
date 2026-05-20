# GitHub Contribution SOP (v2.0)
> 触发: 给开源项目提PR | 禁用: 仅读代码时
> 原则: 一个PR一件事，测试过才推，尊重项目规范

## 前置准备（新项目首次）
1. 读规范: `CONTRIBUTING.md` → `.github/PULL_REQUEST_TEMPLATE.md` → README Contributing段
2. 找测试命令: `package.json`/`Makefile`/`pyproject.toml`，跑不了测试=未验证PR
3. Fork+Clone: `gh repo fork OWNER/REPO --clone`

## PR工作流
### Step 1-2: 目标+分支
读Issue→一句话写清改什么+为什么→检查有无人在做
`git checkout -b fix|feat|docs/issue-描述`

### Step 3: 实现
最小化改动 | 遵循项目风格 | 每逻辑点一commit
commit格式: `type: 简短描述` (fix/feat/docs/refactor/test/chore)

### Step 4: 测试（⛔硬门槛）
跑项目测试→现有测试全过→新功能有测试→lint通过→不过不推

### Step 5: 推送+提PR
`git push origin HEAD`
PR正文: What + Why(`Fixes #123`) + Testing。禁过度解释/自夸

### Step 6: CI
✅全过→等review | ❌失败→看`gh run view --log-failed`修自己的问题
upstream问题→PR里说明

### Step 7: Review回应
reviewer说改就改→追加commit+测试+push→禁force push(除非要求squash)
要求加测试→加，非可选项

## 避坑速查
|错误|正确|
|------|------|
|一PR改多事|拆多个独立PR|
|不跟进|每天查review状态|
|测试没跑就推|Step4硬门槛|
|commit写"update"|写具体改了啥|
|force push覆盖历史|追加commit|
|PR描述空白|What/Why/Testing|

## 跟进状态机
```
提交→等CI → ✅等Review → 通过→Merge ✅
               ↑        要改→改+测试↗
               ❌修 ↗
```
跟进: `gh pr status` / `gh pr checks PR_NUM` / `gh pr view PR_NUM --comments`
