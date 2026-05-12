# Git SOP — 分支模型 & 提交规范 & 故障恢复 (v2.0)

> 触发: 任何Git操作 | 前置: `git aliases`确认别名可用

## 执行摘要
0. **Step 0（前置必做）：确认cwd在git仓库根目录** — `git rev-parse --show-toplevel`
1. 四步法：`git st`→`git a`逐文件→定type/scope→`git cm`
2. Push前：`git status -s`确认干净 + 禁提交密钥
3. 合并后：`git status -s`→确认clean → 🛑 验证门禁

---

## 0. 前置检查 (Step 0 — 必须最先执行)

> ⚠️ 教训：cwd≠git根目录时直接执行git命令会fatal，浪费回合

```powershell
# 确认git仓库根目录，后续所有命令在该目录执行
$gitRoot = (git rev-parse --show-toplevel 2>$null)
if (-not $gitRoot) { Write-Error "❌ cwd不在git仓库内！请先确认路径" }
else { Set-Location $gitRoot; Write-Output "✅ git根: $gitRoot" }
```

- 若cwd不是git根 → **立即cd到git根**，不要在错误目录重试
- 工具调用时在 `cwd` 参数中指定git根路径，或在脚本内 `cd`

---

## 1. 分支模型

### 1.0 术语铁律

- **官方 / upstream / 上游默认只指 `origin/main`**，不要把本地 `main` 或 `yeelight/main` 当官方。
- 用户说“和官方比 / 官方有什么更新 / 同步官方”时，默认基准都是 `origin/main`。
- 用户只说“main”时必须先判定上下文：本地 `main`、`yeelight/main`、还是 `origin/main`；不清楚就用命令核实，不凭印象。

### 1.1 对官方差异/更新自检

```bash
git fetch origin --prune
git rev-list --left-right --count origin/main...HEAD
git diff --stat origin/main...HEAD
git log --oneline --left-right --cherry-pick origin/main...HEAD
```

- `rev-list` 左侧 >0：官方有本分支未包含的提交；右侧 >0：本分支有官方没有的提交。
- “有什么更新”优先看 `origin/main..HEAD` 与 `HEAD..origin/main` 两边提交，别只看工作区 diff。

### 远端 (Remote)

| 远端 | 分支 | 用途 |
|------|------|------|
| `origin` | `main` | 上游官方主线。**只读**，拉最新代码、PR对比基准 |
| `yeelight` | `main` | fork上的个人主线。跨设备同步 |
| `yeelight` | `dev` | fork上的开发分支。同步实验内容 |

### 本地 (Local)

| 分支 | 跟踪 | 用途 | 允许 | 禁止 |
|------|------|------|------|------|
| `base/origin-main` | `origin/main` | 本地干净官方基准 | `merge --ff-only` | 任何个人代码 |
| `pr/*` | `yeelight/pr/*` | 上游贡献分支，一事一分支 | 所有相关改动 | 混入无关改动 |
| `main` | `yeelight/main` | 个人跨设备主线。稳定可用的功能 | cherry-pick from dev | 直接做实验/放半成品 |
| `dev` | `yeelight/dev` | 个人开发分支。实验、boot调整、辅助脚本 | 所有开发 | — |
| `backup/*` | 无 | 清理前备份。平时不开发不合并 | 回滚查阅 | 日常开发 |

### 日常决策速查

| 想做什么 | 用哪个分支 |
|----------|-----------|
| 给上游提PR | `base/origin-main` → `pr/xxx` |
| 做稳定的个人功能 | `main` |
| 做实验/开发辅助/调boot | `dev` |
| dev的改动进main | 只 `cherry-pick`，不整体merge |
| 同步上游最新代码 | `origin/main` → `base/origin-main` → (按需merge到dev) |
| 换设备继续开发 | `git pull --ff-only yeelight main/dev` |
| 做清理前备份 | `backup/<描述>-<日期>` |

---

## 2. 标准操作流程

### 2.1 同步上游（origin/main → base/origin-main）
```bash
git fetch origin --prune
git switch base/origin-main
git merge --ff-only origin/main
```
> 如需将上游更新合入dev：`git switch dev && git merge base/origin-main`

### 2.2 创建上游PR分支
```bash
git switch -c pr/<feature-name> base/origin-main
# 开发、提交...
git push yeelight pr/<feature-name>
```
> PR合并后删除：`git branch -d pr/<feature-name>` + `git push yeelight --delete pr/<feature-name>`

### 2.3 个人开发（dev）
```bash
git switch dev
git merge main   # 保持dev包含main的最新稳定内容
# 开发、提交...
git push yeelight dev
```

### 2.4 dev → main（cherry-pick，非merge）
```bash
git switch main
git log dev --oneline   # 选要cherry-pick的commit
git cherry-pick <commit-sha>
git push yeelight main
```
> **铁律**：dev → main 只用cherry-pick，禁`git merge dev`

### 2.5 跨设备同步
```bash
git fetch yeelight
git switch main && git pull --ff-only yeelight main
git switch dev  && git pull --ff-only yeelight dev
```

### 2.6 清理前备份
```bash
git switch dev
git branch backup/dev-before-<描述>-<YYYY-MM-DD>
# 确认长期稳定后可删除
```

---

## 3. Conventional Commits（祈使语气·≤72字符）
`<type>[!][scope]: <description>` — type: feat/fix/docs/style/refactor/perf/test/build/ci/chore/revert
`!`紧贴type=Breaking Change | body: what/why | footer: `BREAKING CHANGE: <描述>`

## 4. 提交四步法
① `git st` + `git diff [--staged]` 分析变更（staged有内容→`--staged`）
② `git a <files>` 逐文件暂存（一个commit一件事）— 禁: .env/credentials/*.pem/*.key
   - `git a -p` 逐hunk暂存（混合变更拆分）
③ 分析diff→确定type/scope/description（祈使语气, ≤72字符）
④ `git cm "<type>[scope]: <desc>"` | 多行用heredoc → `git ps`(新分支`git psu`)
   commit失败(hooks)→修复后新建commit，不amend

## 5. 安全红线

| 操作 | 条件 |
|------|------|
| `--force`/`reset --hard`/`--no-verify` | 仅用户明确指令 |
| force push main | **永禁** |
| 修改`git config` | 仅用户明确指令 |
| commit secrets | **永禁** |
| amend已推送commit | 仅用户明确指令 |
| push到public/yeelight | 必先执行验证门禁 |
| dev整体merge到main | **永禁**（只cherry-pick） |

> ⚠ push前必做`git ls-files | grep -E "global_mem|boot_config|secret|key"`验证零命中

---

## 6. 故障恢复

| 场景 | 方案 |
|------|------|
| 误commit到错误分支 | `git undo`→切正确分支重commit |
| merge冲突 | `git st`→解决→`git a`→`git cm "merge:..."` |
| 丢弃本地修改 | `git co -- <file>` / `git reset --hard`⚠ |
| rebase冲突 | 解决→`git a`→`git rc`继续/`git ra`放弃 |
| detached HEAD | `git cob <name>` |
| 误删分支 | `git reflog`→`git cob <name> <sha>` |
| push被拒 | `git pr`→解决冲突→`git ps` |
| cherry-pick冲突 | 解决→`git a`→`git cherry-pick --continue` |

## 7. 上游合并冲突分类

| 分类 | 判定 | 策略 |
|------|------|------|
| OURS 本地独有 | `memory/*.md`/`*.py`/自定义脚本 | `--ours`全量保留 |
| THEIRS 上游核心 | `llmcore.py`/`ga.py`/`agentmain.py`/`*app.py` | `--theirs`为底+审查补丁 |
| MANUAL 配置边界 | `.gitignore`/`assets/*`/混合文件 | 手动合并 |

流程: `git diff --name-only --diff-filter=U`→分类→确认→执行→commit

### THEIRS补丁回注
```bash
git show <pre-merge-OURS>:<file> > temp_ours.py
diff temp_ours.py <theirs> | grep '^<'  # 提取独有行
# file_patch逐块回注，只补上游缺失功能
```

---

## 8. 环境特有坑
- Win/PS: code_run必`type="powershell"`; 禁`&&`用`;`; 禁`echo.`; 禁`ls -la`
- GA gitignore: 白名单=`sche_tasks/*`全拦+`!`放行; 禁`sche_tasks/`(目录忽略→`!`失效)
- subprocess: `subprocess.run(['git',...])`勿用os.system

## 🛑 验证门禁

| 检查项 | PASS | FAIL |
|--------|------|------|
| 无密钥泄漏 | `git diff --staged`无.env/credentials + `git ls-files`无密钥文件 | 撤销+加gitignore |
| status干净 | `git status -s`仅预期变更 | 清理/checkout |
| merge后已清理 | `git status -s`确认clean | `git add -A && git commit` |
| main无直接commit | `git log main --oneline`无实验性提交 | cherry-pick整理 |

> ⚠️ 密钥检查必须用**双重验证**：diff --staged + ls-files grep，缺一不可

`VERDICT: PASS` / `VERDICT: FAIL`
