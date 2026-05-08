# codebase_traversal_sop · 代码库遍历与理解 SOP (v1.0)
> 知识融合: codebase-understanding(SKILL 5-step) | investigating-a-codebase(验证优先)
> 复用工具: file_read(文件读取+keyword搜索) | code_run Python(os.walk/glob/AST/依赖图) | code_run PowerShell(dir/findstr) | web_scan/web_execute_js(前端项目)

## 执行摘要（≥1步执行前必读）
① 确定目标(理解/找bug/改代码/学架构)→② QuickScan(项目类型+技术栈+规模)→③ DeepDive(入口→依赖→数据流)→④ 验证所有假设→⑤ 结构化输出 → 🛑 过验证门禁

## §0 触发
用户说: "看看这个项目/理解代码/找bug/梳理架构/这个项目怎么跑/代码结构是怎么样的/为什么这个功能不对/帮忙改这个项目"

## §1 快速扫描 (QuickScan · ≤3步)

### 1.1 项目定位
首先确认项目路径和整体面貌：
```
# 方法1: code_run python 批量探测
import os
root = "<项目路径>"
# 列出顶层文件/目录
for item in sorted(os.listdir(root)):
    full = os.path.join(root, item)
    tag = "[DIR]" if os.path.isdir(full) else ""
    print(f"{tag} {item}")

# 方法2: 关键文件探测
key_files = ['.git/config', 'package.json', 'Cargo.toml', 'go.mod', 'requirements.txt',
             'pyproject.toml', 'CMakeLists.txt', 'Makefile', 'Dockerfile', 'README.md']
for kf in key_files:
    p = os.path.join(root, kf)
    if os.path.exists(p): print(f"FOUND: {kf}")
```

### 1.2 技术栈快速判定
| 标志文件 | 判定 |
|---------|------|
| `package.json` | Node.js/前端项目 → 读 `dependencies/devDependencies` 判断框架 |
| `tsconfig.json` → TypeScript |
| `next.config.*` → Next.js | `vite.config.*` → Vite | `webpack.config.*` → Webpack |
| `Cargo.toml` | Rust |
| `go.mod` | Go |
| `requirements.txt/pyproject.toml` | Python |
| `.svelte` 文件 → Svelte | `.vue` → Vue | `.jsx/.tsx` → React |

### 1.3 规模评估
用 `code_run` 统计文件数量、代码行数（抽样，不读全量）：
```python
# 统计各扩展名文件数和总行数
import os, collections
stats = collections.Counter()
for root, dirs, files in os.walk(project_root):
    dirs[:] = [d for d in dirs if d not in ('node_modules','.git','target','build','dist','__pycache__')]  # 跳过依赖
    for f in files:
        ext = os.path.splitext(f)[1] or '(noext)'
        stats[ext] += 1
for ext, cnt in stats.most_common(10):
    print(f"  {ext}: {cnt} files")
```

> **铁律**: QuickScan≤3步，不深入读代码。目的只是回答"这是什么项目、多大规模、用了什么技术栈"。

## §2 深入分析 (DeepDive)

### 2.1 入口点定位（按优先级，找到一个即停）
1. `package.json` → `"main"` / `"scripts.start"` / `"scripts.dev"`
2. 根目录 `index.*` / `main.*` / `app.*` / `server.*`
3. `src/index.*` / `src/main.*` / `src/app.*`
4. `docker-compose.yml` → `command:` / `entrypoint:`
5. 对 Web 项目：`pages/` (Next.js) / `routes/` / `App.jsx`

### 2.2 目录结构映射
用 code_run 打印项目树（限制深度3，跳过依赖目录）：
```python
def print_tree(path, prefix="", depth=3):
    if depth <= 0: return
    try:
        items = sorted(os.listdir(path))
    except PermissionError: return
    skip = {'.git','node_modules','target','build','dist','__pycache__','.next','vendor','venv','.venv'}
    items = [i for i in items if i not in skip and not i.startswith('.git')]
    dirs = [i for i in items if os.path.isdir(os.path.join(path,i))]
    files = [i for i in items if not os.path.isdir(os.path.join(path,i))]
    for i, name in enumerate(dirs + files):
        is_last = (i == len(dirs + files) - 1)
        conn = "└── " if is_last else "├── "
        print(f"{prefix}{conn}{name}")
        if os.path.isdir(os.path.join(path, name)):
            ext = "    " if is_last else "│   "
            print_tree(os.path.join(path, name), prefix + ext, depth-1)
print_tree("<root>")
```

### 2.3 依赖关系追踪
**对 import/require 链**: 读入口文件 → 提取 import → 递归读关键模块（最多3层深）
- 使用 `file_read(path, keyword="import ")` 提取所有 import 语句
- 构建 `模块A → 被哪些模块引用` 的反向索引

**对 Web 前端项目**: 用 `web_scan` 看页面结构，`web_execute_js` 获取运行时路由/组件树

### 2.4 代码搜索策略（遇到问题时用）
| 需求 | Chii工具 | 示例 |
|------|----------|------|
| 找某个函数/类定义 | file_read keyword | `file_read(path, keyword="def handle_login")` |
| 找所有引用某模块 | code_run python grep | 遍历文件搜索 import 语句 |
| 找配置文件中的值 | code_run powershell findstr | `findstr /s "KEY" *.env` |
| 全局文本搜索 | code_run python | `os.walk + read + str.find` |
| 前端运行时状态 | web_execute_js | `JSON.stringify(window.__NEXT_DATA__)` |

> **策略优先级**: Glob(找文件) → Grep(搜文本) → Read(精读) → Follow imports(追踪依赖)。每次只深入一层。

## §3 验证原则 (Verify Everything)

### 3.1 禁止的假设
- ❌ 根据文件名猜测功能（必须打开看内容）
- ❌ 根据框架惯例假设（必须是代码中确认的）
- ❌ 把注释/文档当事实（代码才是真相）
- ❌ 看到 `user.service.ts` 就断言有 User CRUD（必须看代码确认）

### 3.2 设计假设验证标记
每探索一个模块，用标记报告：
- **✓ 确认**: 假设与代码一致
- **✗ 矛盾**: 假设与代码不符（必须报告具体行号和差异）
- **+ 补充**: 代码中有但最初假设未提及
- **- 缺失**: 假设有但代码中不存在

### 3.3 处理"未找到"
- ❌ "找不到" → **✓** "在以下位置搜索但未找到: [具体路径列表]"
- ❌ "不存在" → **✓** "确认不存在于代码库，搜索了 [N] 个文件"

## §4 按任务类型的执行路径

### 4.1 理解整个项目
```
QuickScan(§1) → 目录树(§2.2) → 入口点(§2.1) → 核心模块链追踪(§2.3, 3层) → 输出架构图
```

### 4.2 找 Bug
```
重现路径(用户描述) → 搜索相关代码(file_read keyword) → 追踪调用链(§2.3) → 定位根因 → 验证(§3)
```
> 溯源顺序：错误点 → 调用者 → 数据来源 → 配置/环境变量 → 假设检查

### 4.3 改代码
```
理解相关代码(搜索+追踪) → 确认修改点+影响范围 → file_read读完整上下文 → file_patch修改 → 验证
```
> 改前必须 file_read 确认当前最新内容（防止基于过期缓存修改）

### 4.4 学习框架/模式
```
QuickScan → 找核心模块(入口3层) → 提取设计模式 → 对比框架最佳实践 → 输出学习笔记
```

## §5 输出规范

### 5.1 输出必须包含
- **项目类型/技术栈** (1行)
- **架构概览** (3-5句，含入口→核心模块→数据层)
- **目录结构** (可视化树)
- **关键文件清单** (带行号，如 `src/router.ts:23-45` 路由定义)
- **验证标记** (每个重要断言带 ✓/✗/+/-)

### 5.2 输出禁止
- 空泛断言(如"代码组织良好") — 必须是可验证的具体描述
- 未经验证的推测作为事实
- 遗漏关键文件的具体路径

## 避坑清单 (Chii特别版)
| # | 坑 | 正解 |
|---|------|------|
| 1 | `file_read` 不设 limit 读大文件 | 先 tiny scan 确认大小，再用 keyword 或 start+count |
| 2 | code_run 遍历时不跳过 node_modules | 必须 skip 依赖目录，否则超时 |
| 3 | 读项目前没确认路径存在 | 先用 `os.path.exists` 探测 |
| 4 | 改代码前不读最新内容 | file_patch 前必须 file_read 确认 |
| 5 | 前端项目只读源码不看运行态 | SPA/SSR项目用 web_scan + web_execute_js 获取运行时 |
| 6 | 重复读同一文件 | 一次 file_read 获取够多上下文(合理设 count) |
| 7 | powerShell 递归搜索被禁 | 使用 python code_run 替代，或用 / 分隔而非 \ |

## 🛑 验证门禁

| 检查项 | 状态 |
|--------|------|
| 全文已读(非局部分析)？ | |
| 版本号已更新？ | |
| 交叉引用闭环？ | |
| L2(global_mem)+L1(insight)已同步？ | |
| 编号无断链？ | |
| 角色卡优先改(源)，SOP后改(引用者)？ | |
| 批量操作后全量重扫？ | |

最终裁定：`VERDICT: PASS` / `VERDICT: FAIL`