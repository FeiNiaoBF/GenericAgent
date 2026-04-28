# Git SOP — 通用提交规范与故障恢复
> 版本: v1.0 | 最后更新: 2026-04-28
**触发**：任何Git操作 | **前置**：确认全局别名可用（`git aliases` 列出全部45个）

## 1. Conventional Commits（祈使语气·≤72字符）
```
<type>[!][scope]: <description>

[body]

[footer]
```
|| type: feat/fix/docs/style/refactor/perf/test/build/ci/chore/revert
|| `!` 紧贴type=Breaking Change | body: 解释what/why | footer: `Closes #123`
|| 例: `feat(auth): add OAuth2 login` | `fix(api): handle null response`

## 2. 提交四步法
### ① Analyze Diff — 确定变更范围
```
git st                              # = status --porcelain
git diff --staged                   # 有暂存; 无暂存用 git diff
```
### ② Stage Files — 逐文件暂存（一个commit一件事）
```
git a <file1> <file2>               # 精确暂存
git a '*.py'                        # 模式暂存
git a -p                            # 交互式选择hunk
```
|| 禁: .env / credentials / *.pem / *.key
### ③ Generate Message — 分析diff → 确定type/scope/description
|| type → §1 | scope → 受影响模块 | description → 祈使语气·现在时·≤72字符
### ④ Execute Commit
```
git cm "<type>[scope]: <desc>"      # 单行
# 多行(含body/footer):
git cm "$(cat <<'EOF'
<type>[scope]: <desc>

<optional body>

<optional footer>
EOF
)"
git ps                              # 推送(新分支用 git psu)
```
|| commit失败(hooks) → 修复后新建commit，不amend

## 3. 安全红线
| 操作 | 条件 |
|------|------|
| `--force` / `reset --hard` | 仅用户明确指令 |
| `--no-verify` | 仅用户明确指令 |
| force push main/master | 永禁 |
| 修改 `git config` | 仅用户明确指令 |
| commit secrets | 永禁 |
| amend 已推送commit | 仅用户明确指令 |
| commit失败后amend修复 | 必须新建commit |

## 4. 故障恢复
| 场景 | 方案 |
|------|------|
| 误commit到错误分支 | `git undo` → `git co` 正确分支重commit |
| merge冲突 | `git st`看冲突→解决→`git a <files>`→`git cm "merge: ..."` |
| 丢弃本地修改 | `git co -- <file>`(单文件)/`git reset --hard`(全量⚠需确认) |
| rebase冲突 | 解决→`git a <file>`→`git rc`继续/`git ra`放弃 |
| detached HEAD | `git cob <new-branch>`保存 |
| 误删分支 | `git reflog` → `git cob <name> <sha>` |
| push被拒(non-fast-forward) | `git pr`先拉取→解决冲突→`git ps` |

## 5. 环境特有坑
|| Win/PowerShell: code_run必配`type="powershell"`; 禁`&&`→用`;`; 禁`echo.`; 禁`ls -la`
|| GA项目gitignore: 白名单模式=先`sche_tasks/*`全拦+`!`例外放行; 禁`sche_tasks/`(目录级忽略→`!`失效)
|| subprocess调用: `subprocess.run(['git', ...])`→勿用os.system/shell字符串

## 6. 提交准则
|| 一个commit一个逻辑变更 | 祈使语气现在时("add"非"added")
|| 关联issue: `Closes #123` / `Refs #456` | description ≤72字符
|| commit失败(hooks) → 修复后新建commit，不amend
## 7. Fork同步（3分支合并上游）
> remote：`origin`=上游(lsdefine/GenericAgent)，`yeelight`=当前fork

### 前置报告（必须先做，用户确认后才能合并）
每次从上游拉取时，主分支是`dev`，必须先做干跑分析并报告给用户：
1. `git fetch origin` 后，`git log dev..origin/main --oneline` 列出上游新增提交
2. 逐commit分析变更内容（`git show --stat <sha>`）
3. `git merge --no-commit --no-ff origin/main` 干跑，检测冲突文件
4. 对每个冲突文件，列出冲突位置和双方差异，**给出具体合并建议**
5. 完整报告（更新内容+冲突+建议）→ 等待用户确认 → 才执行实际合并
6. `git merge --abort` 清理干跑（无论有无冲突）

### 标准顺序（不可颠倒，用户确认后执行）
```
git fetch origin
git switch original && git merge origin/main --ff-only
git switch dev    && git merge origin/main --no-ff
# ---- 解决冲突（按前置报告中确认的方案） ----
git switch main   && git merge dev --no-ff
git push yeelight --all
```
### 特有坑点
- `--ff-only`忽略`-m`参数(快进不动HEAD，正常)；merge模拟测试后必须abort并检查`.git\MERGE_HEAD`
- 冲突解决: THEIRS为底(`git checkout --theirs <file>`)→逐块file_patch回OUR修改。先读THEIRS全文确认结构再patch，禁凭推理脑补
- 合并后验证(commit前): grep缺imports(上游可能删除/重命名模块)、grep缺函数/别名引用、确认新增符号可解析
- file_patch精度: THEIRS的import路径可能与OUR不同(如`from chatapp_common` vs `from frontends.chatapp_common`)，必先file_read确认
- commit message: `Merge upstream lsdefine/GenericAgent changes into dev` / `Merge dev into main: <desc>`
