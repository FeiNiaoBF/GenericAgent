# Git SOP — 提交规范与故障恢复 (v1.1 ⚡干练)

> 触发: 任何Git操作 | 前置: `git aliases`确认别名可用

## 执行摘要
1. 四步法：`git st`→`git a`逐文件→定type/scope→`git cm`
2. Push前：`git status -s`确认干净 + 禁提交密钥
3. 合并后：`git status -s`→`git add -A`→确认clean → 🛑 验证门禁

## 1. Conventional Commits（祈使语气·≤72字符）
`<type>[!][scope]: <description>` — type: feat/fix/docs/style/refactor/perf/test/build/ci/chore/revert
`!`紧贴type=Breaking Change | body: what/why | footer: `BREAKING CHANGE: <描述>`

## 2. 提交四步法
① `git st` + `git diff [--staged]` 分析变更（staged有内容→`--staged`）
② `git a <files>` 逐文件暂存（一个commit一件事）— 禁: .env/credentials/*.pem/*.key
   - `git a -p` 逐hunk暂存（混合变更拆分）
③ 分析diff→确定type/scope/description（祈使语气, ≤72字符）
④ `git cm "<type>[scope]: <desc>"` | 多行用heredoc → `git ps`(新分支`git psu`)
   commit失败(hooks)→修复后新建commit，不amend

## 3. 安全红线
| 操作 | 条件 |
|------|------|
| `--force`/`reset --hard`/`--no-verify` | 仅用户明确指令 |
| force push main/master | 永禁 |
| 修改`git config` | 仅用户明确指令 |
| commit secrets | 永禁 |
| amend已推送commit | 仅用户明确指令 |
| push到public/fork | 必先执行验证门禁 |

> ⚠ push前必做`git ls-files | grep -E "global_mem|boot_config|secret|key"`验证零命中

## 4. 故障恢复
| 场景 | 方案 |
|------|------|
| 误commit到错误分支 | `git undo`→切正确分支重commit |
| merge冲突 | `git st`→解决→`git a`→`git cm "merge:..."` |
| 丢弃本地修改 | `git co -- <file>` / `git reset --hard`⚠ |
| rebase冲突 | 解决→`git a`→`git rc`继续/`git ra`放弃 |
| detached HEAD | `git cob <name>` |
| 误删分支 | `git reflog`→`git cob <name> <sha>` |
| push被拒 | `git pr`→解决冲突→`git ps` |

## 5. 环境特有坑
Win/PS: code_run必`type="powershell"`; 禁`&&`用`;`; 禁`echo.`; 禁`ls -la`
GA gitignore: 白名单=`sche_tasks/*`全拦+`!`放行; 禁`sche_tasks/`(目录忽略→`!`失效)
subprocess: `subprocess.run(['git',...])`勿用os.system

## 6. Fork同步（3分支）
remote: `origin`=上游(lsdefine/GenericAgent), `yeelight`=当前fork

### 分支铁律
| 分支 | 用途 | 允许 | 禁止 |
|------|------|------|------|
| `original` | 跟踪上游 | `git merge origin/main --ff-only` | 任何写入 |
| `dev` | 日常工作 | 所有开发 | — |
| `main` | 稳定版 | `git merge dev --no-ff` | 直接commit/file_write |

> 改文件前必`git branch --show-current`确认dev。在main/original→`git stash -u`→`git switch dev`→`git stash pop`

### 前置报告（必须干跑+用户确认）
1. `git fetch origin`→`git log dev..origin/main --oneline`
2. 逐commit `git show --stat <sha>`
3. `git merge --no-commit --no-ff origin/main`干跑
4. 冲突文件列双方差异+建议→报告→等确认
5. `git merge --abort`清理

### 标准顺序
```
git fetch origin
git switch original && git merge origin/main --ff-only
git switch dev    && git merge origin/main --no-ff
git switch main   && git merge dev --no-ff
git push yeelight --all
```
首次打通(force push后分叉): dev merge加`--allow-unrelated-histories`

### AA冲突分类
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

### 合并后清理
`git status -s`→`git add -A && git commit -m "chore: cleanup..."`→确认clean

## 🛑 验证门禁
| 检查项 | PASS | FAIL |
|--------|------|------|
| 无密钥泄漏 | `git diff --staged`无.env/credentials | 撤销+加gitignore |
| status干净 | `git status -s`仅预期变更 | 清理/checkout |
| merge后已清理 | `git status -s`确认clean | `git add -A && git commit` |

`VERDICT: PASS` / `VERDICT: FAIL`
