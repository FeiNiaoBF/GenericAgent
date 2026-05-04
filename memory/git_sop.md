# Git SOP — 通用提交规范与故障恢复
> 触发: 任何Git操作 | 前置: 确认全局别名可用(`git aliases`列出)

## 1. Conventional Commits（祈使语气·≤72字符）
`<type>[!][scope]: <description>` — type: feat/fix/docs/style/refactor/perf/test/build/ci/chore/revert
`!`紧贴type=Breaking Change | body解释what/why | footer `Closes #123`

## 2. 提交四步法
① `git st` + `git diff [--staged]` 分析变更
② `git a <files>` 逐文件暂存(一个commit一件事) — 禁: .env/credentials/*.pem/*.key
③ 分析diff→确定type/scope/description
④ `git cm "<type>[scope]: <desc>"` | 多行用heredoc → `git ps`(新分支`git psu`)
commit失败(hooks)→修复后新建commit，不amend

## 3. 安全红线
| 操作 | 条件 |
|------|------|
| `--force`/`reset --hard` | 仅用户明确指令 |
| `--no-verify` | 仅用户明确指令 |
| force push main/master | 永禁 |
| 修改`git config` | 仅用户明确指令 |
| commit secrets | 永禁 |
| amend已推送commit | 仅用户明确指令 |
| commit失败→amend修复 | 必须新建commit |
| push到public/fork | 必先执行§8检查表 |
> ⚠ gitignore白名单`!`会复写黑名单: push前必做`git ls-files | grep -E "global_mem|boot_config|secret|key"`验证零命中

## 4. 故障恢复
| 场景 | 方案 |
|------|------|
| 误commit到错误分支 | `git undo`→切正确分支重commit |
| merge冲突 | `git st`看冲突→解决→`git a`→`git cm "merge:..."` |
| 丢弃本地修改 | `git co -- <file>`单文件/`git reset --hard`全量⚠需确认 |
| rebase冲突 | 解决→`git a`→`git rc`继续/`git ra`放弃 |
| detached HEAD | `git cob <name>`保存 |
| 误删分支 | `git reflog`→`git cob <name> <sha>` |
| push被拒 | `git pr`先拉取→解决冲突→`git ps` |

## 5. 环境特有坑
Win/PS: code_run必`type="powershell"`; 禁`&&`用`;`; 禁`echo.`; 禁`ls -la`
GA gitignore: 白名单模式=`sche_tasks/*`全拦+`!`放行; 禁`sche_tasks/`(目录忽略→`!`失效)
subprocess: `subprocess.run(['git',...])`勿用os.system/shell字符串

## 6. 提交准则
一个commit一个逻辑变更 | 祈使语气现在时 | 关联issue: `Closes #123`/`Refs #456` | ≤72字符
commit失败→修复后新建commit，不amend

## 7. Fork同步（3分支合并上游）
remote: `origin`=上游(lsdefine/GenericAgent), `yeelight`=当前fork

### 分支铁律（AI Agent必遵守）
| 分支 | 用途 | 允许 | 禁止 |
|------|------|------|------|
| `original` | 跟踪上游 | `git merge origin/main --ff-only` | 任何写入 |
| `dev` | 日常工作主分支 | 所有开发操作 | — |
| `main` | 稳定版 | `git merge dev --no-ff` | 直接commit/file_write |
> 文件修改前必`git branch --show-current`确认dev。在main/original→`git stash -u`→`git switch dev`→`git stash pop`

### 前置报告（必须干跑+用户确认）
1. `git fetch origin`→`git log dev..origin/main --oneline`
2. 逐commit分析`git show --stat <sha>`
3. `git merge --no-commit --no-ff origin/main`干跑检测冲突
4. 对冲突文件列双方差异+合并建议→报告→等确认
5. `git merge --abort`清理

### 标准顺序（用户确认后）
```
git fetch origin
git switch original && git merge origin/main --ff-only
git switch dev    && git merge origin/main --no-ff
# 解决冲突
git switch main   && git merge dev --no-ff
git push yeelight --all
```
首次打通(force push后历史分叉): dev merge加`--allow-unrelated-histories`

### AA冲突分类决策框架
| 分类 | 判定 | 策略 | 示例 |
|------|------|------|------|
| OURS 本地独有 | `memory/*.md`/`*.py`/自定义脚本 | `git checkout --ours <file>`全量保留 | `memory/plan_sop.md` |
| THEIRS 上游核心 | `llmcore.py`/`ga.py`/`agentmain.py`/`*app.py` | `git checkout --theirs <file>`为底+审查补丁 | `tgapp.py` |
| MANUAL 配置边界 | `.gitignore`/`assets/*`/混合文件 | 逐行手动合并 | `.gitignore` |
流程: `git diff --name-only --diff-filter=U`→分类表→用户确认→批量执行→commit

### THEIRS补丁回注
```bash
git show <pre-merge-OURS-commit>:<file> > temp_ours.py
diff temp_ours.py <theirs-file> | grep '^<'  # 提取独有行
# file_patch逐块回注，最小化——只补上游缺失的本地功能
```

### 合并后清理（关键！）
任何merge commit后: `git status -s`→`git add -A && git commit -m "chore: cleanup..."`→再次`git status -s`确认clean

### 已知风险
| 文件 | 风险 | 缓解 |
|------|------|------|
| `frontends/tgapp.py` | 上游纯MDV2替代本地三层降级 | TG中文特殊字符异常时补回fallback分支 |
