# codebase_traversal_sop · 代码库遍历与理解 (v1.0)
> 复用: file_read(+keyword) | code_run Python(os.walk/glob) | web_scan/web_execute_js(前端)

## 执行摘要
① 确定目标→② QuickScan(类型+栈+规模)→③ DeepDive(入口→依赖→数据流)→④ 验证假设→⑤ 输出→⑥ 🛑门禁

## §1 QuickScan (≤3步，不读代码)
```python
import os, collections
root = "<路径>"
for item in sorted(os.listdir(root)):
    print(f"{'[DIR]' if os.path.isdir(os.path.join(root,item)) else ''} {item}")
for kf in ['.git/config','package.json','Cargo.toml','go.mod','requirements.txt','pyproject.toml','Makefile','Dockerfile','README.md']:
    if os.path.exists(os.path.join(root,kf)): print(f"FOUND: {kf}")
# 规模: os.walk统计各扩展名(skip node_modules/.git/target等)
stats = collections.Counter()
for r,dirs,fs in os.walk(root):
    dirs[:]=[d for d in dirs if d not in ('node_modules','.git','target','build','dist','__pycache__')]
    for f in fs: stats[os.path.splitext(f)[1] or'(noext)']+=1
for ext,cnt in stats.most_common(10): print(f"  {ext}: {cnt}")
```
栈判定: package.json→Node|tsconfig→TS|next/vite/webpack→框架|Cargo.toml→Rust|go.mod→Go|pyproject→Python

## §2 DeepDive

### 2.1 入口点(找到即停)
package.json main/scripts | 根/index/main/app/server.* | src/index/main/app.* | docker-compose command | pages/(Next)/routes/App.jsx

### 2.2 目录树(depth3, skip依赖)
```python
def tree(path,pfx="",d=3):
    if d<=0:return
    try: items=sorted(os.listdir(path))
    except: return
    skip={'.git','node_modules','target','build','dist','__pycache__','.next','vendor','venv'}
    items=[i for i in items if i not in skip]
    dc=[i for i in items if os.path.isdir(os.path.join(path,i))]
    fc=[i for i in items if not os.path.isdir(os.path.join(path,i))]
    for i,n in enumerate(dc+fc):
        last=i==len(dc+fc)-1; c="└──" if last else"├──"; print(f"{pfx}{c} {n}")
        if os.path.isdir(os.path.join(path,n)): tree(os.path.join(path,n),pfx+("    "if last else"│   "),d-1)
```

### 2.3 依赖追踪
入口→import提取→递归3层(`file_read(keyword="import")`) | 反向索引 | 前端用web_scan+web_execute_js

### 2.4 搜索策略(每次只深一层)
Glob(找文件)→Grep(搜文本)→Read(精读)→Follow imports | 找定义用file_read keyword | 找引用python grep | 运行时web_execute_js

## §3 验证原则
❌禁: 文件名猜功能/惯例假设/注释当事实 | ✓确认/✗矛盾(附行号)/+补充/-缺失
"未找到"→报告搜索路径和文件数

## §4 任务路径
- **理解**: QuickScan→目录树→入口→模块链3层→架构图
- **找Bug**: 重现→搜索→调用链→根因(溯源: 错误→调用者→数据→配置→假设)
- **改代码**: 搜索+追踪→影响范围→file_read最新→file_patch→验证
- **学框架**: QuickScan→核心模块→设计模式→最佳实践→笔记

## §5 输出
必含: 栈(1行)+架构(3-5句)+目录树+关键文件(带行号)+验证标记(✓✗/+-)
禁: 空泛断言/未验证推测/遗漏路径

## 避坑
大文件先确认大小用keyword|必skip依赖|先os.path.exists|改前必file_read|前端看运行态|PS禁→python替代|Windows CLI编码统一入口setup_utf8，禁多处TextIOWrapper包stdout/stderr

## 🛑 验证门禁
全文已读？|版本号更新？|交叉引用闭环？|L2+L1同步？|编号无断链？
`VERDICT: PASS` / `VERDICT: FAIL`