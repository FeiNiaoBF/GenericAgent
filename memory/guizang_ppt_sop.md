# guizang_ppt_sop · 杂志风PPT生成 (v1.0)

## 前置资源
skill根: ../memory/guizang-ppt-skill/
- SKILL.md: 完整工作流
- references/themes.md: 5套主题色(只能选,不可自定义hex)
- references/layouts.md: 10种布局骨架(可直接粘贴)
- references/checklist.md: 质量检查清单(P0/P1/P2/P3)
- references/components.md: 组件手册
- assets/template.html: 单文件模板(拷贝到工作目录再改)

## 执行摘要（≥1步执行前必读）
1. 选主题(5套预定义，禁自定义hex) → 选布局(10种骨架) → 拷贝template.html
2. 填充内容 → 类名预检 → 主题节奏检查 → P0自检6项(衬线/非衬线/无emoji/height:Nvh/无align-self:end)
3. 生成HTML → 用户双击预览 → 🛑 过验证门禁

## 关键前置(顺序不可错)

### 0. 需求澄清
如用户仅给主题→用SKILL.md 6问清单对齐:受众/时长/素材/图片/主题色/特殊要求

### 1. 先读模板CSS(比写slide更优先)
**必须** `file_read template.html <style>` 块,核对layouts.md要用的每个类名是否在CSS存在。
常见遗漏类: h-hero/h-xl/h-sub/h-md/lead/kicker/meta-row/stat-card/grid-2-7-5/grid-2-6-6/grid-2-8-4/grid-6/grid-3/callout/pipeline

### 2. 规划主题节奏
写出每页class后再写代码。规则:
- 必须带 light/dark/hero light/hero dark 之一
- 禁止连续3页同主题
- >=8页必须有>=1 hero dark + >=1 hero light
- 每3-4页插1个hero页

### 3. 拷贝模板+换主题
- `shutil.copy2(src, dst)` 拷贝template.html到工作目录
- 只替换`:root{}`中的6行: --ink/--ink-rgb/--paper/--paper-rgb/--paper-tint/--ink-tint
- 禁止中途换色/混搭主题

## 典型坑(已踩)

| 坑 | 解法 |
|---|---|
| 类名不在CSS→样式全崩 | 写slide前用python grep `.类名` in `<style>` 块验证 |
| blockquote 搜不到类 | 它是HTML元素,不是CSS类,直接用`<blockquote>` |
| CSS中类带`.frame.`前缀 | .frame.grid-2-8-4 需同时有 frame 和 grid-2-8-4 |
| h-hero>=6字折行崩版式 | <=5字用nowrap, >5字手动加`<br>`断行 |
| file:/// URL浏览器打不开 | 在cwd内,用户自行双击打开;或python serve |
| 模板注释含`<section class="slide ...">` | 匹配`<section>`时误计数,需过滤注释 |
| 中英交替过载 | chrome/kicker每页不同,不要同一短语反复翻译 |

## 生成后自检(P0)
1. 类名全通过预检
2. 主题节奏列表 grep class="slide 检查交错
3. 大标题衬线(h-hero/h-xl),正文非衬线(body-zh)
4. 无emoji(用Lucide图标)
5. 图片用height:Nvh非aspect-ratio
6. 无align-self:end(图片堆底)

## 🛑 验证门禁（执行前/后强制检查）

| 检查项 | 状态 |
|--------|------|
| 4页+非目录（每页1核心信息）？ | |
| 1-7-7法则(每页≤7行×7词)？ | |
| 图片用height:Nvh非aspect-ratio？ | |
| 无emoji(用Lucide图标)？ | |
| 无align-self:end？ | |

最终裁定：`VERDICT: PASS` / `VERDICT: FAIL`
