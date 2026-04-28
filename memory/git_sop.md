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
| push到public/fork | 必须先执行 §8 检查表 |

### 教训 (2026-04-28): gitignore白名单(!)会复写黑名单
> 上游`!memory/global_mem.txt`导致敏感文件被`git add -A`纳入并推送到公开fork。
> 此后push前必做：`git ls-files | grep -E "global_mem|boot_config|secret|key"` 验证零命中。

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
### 首次打通（force push后历史分叉专用）
> 当fork历史被force push重写后，`git merge`会报`refusing to merge unrelated histories`。
> 首次打通时在dev合并步骤加`--allow-unrelated-histories`：
```
git switch dev && git merge origin/main --allow-unrelated-histories --no-ff
```
> 此后`original`与`dev`共享历史，后续同步恢复标准流程（不再需要`--allow-unrelated-histories`）。

### 特有坑点
- `--ff-only`忽略`-m`参数(快进不动HEAD，正常)；merge模拟测试后必须abort并检查`.git\MERGE_HEAD`
- **首次打通**：force push后历史分叉，merge必须加`--allow-unrelated-histories`。此后标准流程恢复正常
- 冲突解决: THEIRS为底(`git checkout --theirs <file>`)→逐块file_patch回OUR修改。先读THEIRS全文确认结构再patch，禁凭推理脑补
- 合并后验证(commit前): grep缺imports(上游可能删除/重命名模块)、grep缺函数/别名引用、确认新增符号可解析
- file_patch精度: THEIRS的import路径可能与OUR不同(如`from chatapp_common` vs `from frontends.chatapp_common`)，必先file_read确认
- commit message: `Merge upstream lsdefine/GenericAgent changes into dev` / `Merge dev into main: <desc>`

### AA冲突分类决策框架 (2026-04-28实战验证)
> 当merge产生大量AA冲突（本次28个）时，不逐文件盲解，先分类再批量处理：

| 分类 | 判定特征 | 策略 | 示例 |
|---|---|---|---|
| **OURS** 本地独有SOP/工具 | `memory/*.md`, `memory/*.py`, 本地自定义脚本 | `git checkout --ours <file>` 全量保留 | `memory/plan_sop.md`, `memory/web_setup_sop.md` |
| **THEIRS** 上游核心引擎 | `llmcore.py`, `ga.py`, `agentmain.py`, `*app.py` | `git checkout --theirs <file>` 为底，逐文件审查补丁 | `llmcore.py`, `tgapp.py`, `agentmain.py` |
| **MANUAL** 配置/边界 | `.gitignore`, `assets/*`, 二极管的混合文件 | 逐行手动合并(先THEIRS+补OUR additions) | `.gitignore`, `GETTING_STARTED.md` |

**分类流程**:
1. `git diff --name-only --diff-filter=U` 列全冲突文件
2. 对每个文件判定归属(OURS/THEIRS/MANUAL)，输出分类表格给用户确认
3. 确认后批量执行: `git checkout --ours file1 file2...` → `git add` → 逐个THEIRS文件审查补丁 → MANUAL手动合并 → commit

### THEIRS文件本地补丁回注
当取上游THEIRS为底但需恢复本地增量时（如tgapp.py的HTML降级逻辑）:
```
git show <pre-merge-OURS-commit>:<file> > temp_ours.py  # 提取旧版
diff temp_ours.py <theirs-file> | grep '^<'               # 提取我们独有的行
# 用 file_patch 逐块回注（非全量覆盖THEIRS）
```
**原则**: 补丁最小化——只补上游明确缺失的本地功能，不动上游新增/修改。

### 合并后清理（关键！遗漏会导致下次merge混乱）
任何merge commit后必须:
1. `git status -s` 检查unstaged残留（常见: `M`=modified未暂存, `D`=deleted未暂存）
2. 立即 `git add -A && git commit -m "chore: commit staged ... and remove ..."` 清理
3. 再次 `git status -s` 确认 clean
> 本次实战: 合并commit后发现git_sop.md(M) + procmem_scanner.py(D)未暂存，清洗后才clean

### 已知文件级风险登记
| 文件 | 风险 | 缓解 |
|---|---|---|
| `frontends/tgapp.py` | 上游纯MarkdownV2替代了本地`safe_format` HTML→MDV2→plain三层降级 | TG消息格式异常(中文特殊字符MDV2解析失败)时，需快速补回fallback分支 |
