# CS Teaching Page SOP

> 目标：根据主人指定的计算机科学知识点，生成一个专业、自包含、可直接打开的 HTML/CSS/JS 交互式教学页面。融合 `cs-teaching-page` / `cs-visual-teacher` 的教学完整性，以及 `html-ppt-skill` / `guizang-ppt-skill` 的高级视觉排版能力。

## 触发场景

当主人提出以下需求时启用本 SOP：

- “用 HTML/CSS 讲解 [CS知识点]”
- “生成 [算法/数据结构/网络/操作系统/编程基础] 教学页面”
- “可视化教学 [概念]”
- “做一个 [CS概念] 的学习卡片/网页”
- “做专业 CS 教学页 / 交互式教学页”

## 输入源与优先级

1. **教学结构来源**
   - `C:\Users\Yeekox\Downloads\cs-teaching-page\SKILL.md`
   - `C:\Users\Yeekox\Downloads\cs-visual-teacher\SKILL.md`
2. **视觉与排版来源**
   - `memory/html_ppt_skill/index.md`
   - `memory/html_ppt_skill/recommendations.md`
   - `memory/html_ppt_skill/themes.md`
   - `memory/html_ppt_skill/templates.md`
   - `memory/guizang-ppt-skill/SKILL.md`
   - `memory/guizang-ppt-skill/references/themes.md`
   - `memory/guizang-ppt-skill/references/components.md`
   - `memory/guizang-ppt-skill/references/layouts.md`
   - `https://github.com/lewislulu/html-ppt-skill`

若本地技能文件存在，先读本地；若不存在再探测远程或询问主人。

### html-ppt-skill 联动规则

生成专业 CS 教学页时，必须优先读取 `memory/html_ppt_skill/` 目录下的精简资产库：

1. 先读 `recommendations.md` 取得默认组合：`engineering-whiteprint` + `cover/toc/two-column/code/flow-diagram/arch-diagram/comparison/table/thanks` 的布局语言。
2. 再按主题读 `themes.md`：默认浅色用 `engineering-whiteprint`；长时间理论学习用 `solarized-light`；严肃理论用 `academic-paper`；现代开发者课程用 `catppuccin-latte`；代码或运行机制偏重时可用 `tokyo-night`。
3. 再按页面模块读 `templates.md`：概念讲解优先 `two-column.html`；代码演示优先 `code.html`；流程机制优先 `flow-diagram.html`；系统结构优先 `arch-diagram.html`；对比主题优先 `comparison.html` / `diff.html`；总结归纳优先 `table.html` / `mindmap.html`。
4. 不要直接复制 PPT 模板文件。只吸收其视觉语言、信息层级、卡片节奏、版式结构，最终仍生成单文件教学 HTML。
5. 若主人没有指定美术风格，默认采用 `engineering-whiteprint` 的白底坐标纸工程风，兼顾专业感、可读性和代码展示。
6. 若生成的是深色主题，也必须保留浅色/深色切换，并确保两套 CSS 变量完整。

## 生成原则

### 必须满足

- 输出完整 `.html` 文件内容，浏览器可直接打开。
- 自包含：HTML、CSS、JS 全部在单文件内。
- 教学页包含：
  1. 概念标题与一句话定义
  2. 学习目标
  3. 核心概念解释
  4. 纯 HTML/CSS 可视化示意图
  5. 代码示例与注释
  6. 分步骤解析
  7. 常见误区 / 对比表 / 小测验至少一种
  8. 总结卡片
- 支持浅色/深色主题切换，使用 `data-theme` + CSS 变量。
- 响应式布局，移动端不破版。
- 代码示例与可视化必须解释同一个核心概念。
- 代码示例语法正确，建议 15-40 行，有关键注释。

### 禁止事项

- 禁止外部图片、外部 CSS、外部 JS 库。
- 默认禁止 Canvas / SVG；优先纯 HTML 元素 + CSS。
- 禁止未定义 CSS 类。
- 禁止为了炫技牺牲可读性。
- 禁止代码示例和可视化脱节。
- 禁止只给片段，必须给完整 HTML。

## 工作流

### Step 0：落地策略

先确认主人要的是哪一种交付：

- 只要代码：直接输出完整 HTML。
- 要“做一个页面”：默认写入当前工作区 `.html` 文件，并做物理验证。
- 要放入指定项目 / Vault / 博客：先确认路径，避免把临时教学页误入知识库。

文件命名建议：`cs_lesson_<topic-slug>.html`，主题 slug 用小写英文、短横线或下划线，避免中文路径导致浏览器/脚本验证差异。

生成前先列出页面设计约束：知识点、读者水平、核心可视化、代码语言、主题风格、交互点。若主人没有指定，按默认值执行，不反复询问。

主题选择门禁（压缩版）：

- 未指定主题：先给最多 6 个选项，让主人选；不可直接生成。
- 主人说“你决定”：按 Step 3 自动匹配主题。
- 主人说“所有主题 / 多主题预览”：不询问，直接批量生成并验证。
- 多主题不是换色：必须按 `memory/html_ppt_skill/themes.md` 的 Theme DNA 改变 `默认明暗`、`背景纹理`、`字体气质`、`卡片形态`、`边框/阴影`、`可视化节点/线条`。
- 深色主题默认 `data-theme="dark"`，浅色主题默认 `data-theme="light"`；两套变量都要完整。

推荐选项（默认最多 6 个）：

- 编程基础 / 代码实践：`catppuccin-latte`、`catppuccin-mocha`。
- 系统设计 / API / 架构：`engineering-whiteprint`、`tokyo-night`。
- 理论 / 算法 / 长时间学习：`solarized-light`、`academic-paper`。

询问格式：

```text
唧可以用这些主题给主人做：
1. <theme> — <一句话说明>
2. <theme> — <一句话说明>
...
主人选编号/主题名就好；如果主人说“你决定”，唧按知识点自动选择。
```

### Step 0.5：套用 html-ppt-skill 版式骨架

除非主人明确要求极简页面，否则生成前先做一次“教学模块 → 推荐模板语言”的映射：

| 教学模块 | 推荐模板语言 | 页面实现要点 |
|---|---|---|
| 开场定义 | `cover.html` / `toc.html` | Hero 区给出标题、定义、难度、预计时间、学习路径。 |
| 概念解释 | `two-column.html` | 左侧解释心智模型，右侧放例子、规则或小图。 |
| 代码示例 | `code.html` | 代码块必须可读、带注释、行数适中，并配行级解释。 |
| 执行流程 | `flow-diagram.html` / `process-steps.html` | 用 CSS 节点、箭头、步骤卡展示机制流动。 |
| 系统结构 | `arch-diagram.html` | 用分层卡片、连接线、数据流表示组件关系。 |
| 对比取舍 | `comparison.html` / `diff.html` | 用双栏、差异高亮、收益/代价讲清选择依据。 |
| 归纳总结 | `table.html` / `mindmap.html` | 用表格、要点卡或知识地图收束。 |
| 结尾行动 | `thanks.html` / `cta.html` | 给复习清单、下一步练习或主人可继续问的问题。 |

执行原则：模板只提供“版式语言”，不得引入外链资源，不得生成多文件 PPT。最终仍必须是一个自包含 HTML 教学页。

### Step 1：解析知识点

先判断主人要讲的内容属于哪一类：

- 数据结构：数组、链表、栈、队列、树、图、堆、哈希表等。
- 算法：排序、搜索、动态规划、贪心、回溯、图算法等。
- 计算机网络：TCP/IP、HTTP、DNS、TLS、拥塞控制等。
- 操作系统：进程、线程、内存管理、调度、文件系统等。
- 编程基础：变量、函数、递归、闭包、异步、类型系统等。

同时确定：

- 教学目标：读者学完能做什么。
- 可视化重点：最适合用图形表达的机制。
- 代码语言：若主人未指定，算法/数据结构优先 Python 或 JavaScript；前端概念用 JavaScript；系统概念可用伪代码。
- 难度：默认“入门到中级”，可按主人要求调整。

### Step 2：设计页面信息架构

推荐页面顺序：

1. `hero`：标题、副标题、难度、预计学习时间、主题切换按钮。
2. `overview`：一句话定义 + 适用场景。
3. `mental-model`：用生活类比或计算机内部模型解释。
4. `visualization`：纯 CSS/HTML 可视化。
5. `walkthrough`：按步骤拆解可视化。
6. `code-example`：代码示例 + 行级解释。
7. `complexity-or-tradeoff`：复杂度、优缺点或对比表。
8. `pitfalls`：常见误区。
9. `quiz`：2-4 个小问题或交互检查。
10. `summary`：核心要点卡片。

页面长度不宜无限扩张。单页教学要“完整但不臃肿”。

### Step 3：选择视觉主题

先从 `memory/html_ppt_skill/themes.md` 读取推荐主题和“主题 DNA”，再按知识点匹配：

- 深色科技风：网络、操作系统、并发、架构，优先 `tokyo-night` / `blueprint` / `catppuccin-mocha`。
- 浅色工程风：系统设计、API、数据流、课堂讲解，优先 `engineering-whiteprint` / `nord`。
- 极简学术风：算法复杂度、理论概念，优先 `academic-paper` / `solarized-light` / `minimal-white`。
- 现代开发者风：编程基础、语言对比、代码实践，优先 `catppuccin-latte` / `catppuccin-mocha`。
- 企业培训风：工程规范、方案评审、团队分享，优先 `corporate-clean`。

主题生成不是“统一模板换颜色”。必须先写一个简短 Theme Brief：

```text
Theme: <name>
Default mode: dark/light
Mood: <工程蓝图/护眼讲义/论文纸张/夜间编辑器...>
Background: <网格/纸张/渐变/纯白/深蓝图纸...>
Typography: <衬线学术/几何无衬线/代码编辑器...>
Cards: <圆角/直角/描边/阴影/玻璃/纸片...>
Visualization: <线框/节点/泳道/卡片/表格...>
Motion: <克制/柔和/强视觉>
```

硬性要求：

1. 至少落实 5 类主题差异：`背景纹理`、`字体气质`、`卡片形态`、`边框/阴影`、`可视化线条/节点`。
2. 深色主题默认 `data-theme="dark"`，浅色主题默认 `data-theme="light"`；仍要同时提供完整 dark/light 变量。
3. 主题切换后不允许出现低对比文字、隐形边框、看不清的代码块。
4. 同一知识点生成多主题预览时，页面骨架可以共享，但 hero、卡片、图示、代码区、装饰背景必须体现各主题 DNA。
5. 强视觉主题只用于短页、封面或专题页；长 CS 教学默认用推荐主题。

美术原则：

- 使用 CSS 变量管理颜色：`--bg`、`--surface`、`--surface-2`、`--text`、`--muted`、`--accent`、`--accent-2`、`--border`、`--code-bg`、`--shadow`。
- 用额外变量管理主题形态：`--radius`、`--radius-lg`、`--font-display`、`--font-body`、`--grid-opacity`、`--line-style`。
- 标题有明确层级：`h1` 强视觉，`h2` 稳定分区，正文易读。
- 卡片、代码块、流程节点必须跟随主题形态，而不是使用固定圆角和固定阴影。
- 页面要像专业教学产品，不像默认文档。
- 图标可用纯 CSS 小标记或文本标签；若必须图标，用内联字符，不依赖库。

### Step 4：设计 CSS 可视化

优先使用：

- Flexbox / Grid
- border / border-radius
- linear-gradient / radial-gradient
- pseudo-elements `::before` / `::after`
- CSS variables
- transition / keyframes
- transform

典型映射：

- 树：节点圆形 + 连接线 + 层级 grid。
- 链表：节点卡片 + next 指针箭头。
- 栈/队列：竖向或横向容器 + push/pop 指示。
- 排序：柱状图 + 当前比较高亮。
- 图算法：节点网格 + 边线 + 访问状态。
- 网络协议：时序图泳道 + 消息箭头。
- OS 调度：时间轴 + 进程状态卡片。
- 内存：地址块、页表、缓存层级。

可视化要求：

- 每个元素有文字标注。
- 颜色承载含义，不能只装饰。
- 状态变化要有说明。
- 若加交互，按钮必须有明确反馈。

### Step 5：代码示例规范

代码块必须：

- 与当前可视化讲同一个概念。
- 有注释解释关键步骤。
- 长度适中，建议 15-40 行。
- 自定义语法高亮可用 `<span class="kw">`、`<span class="fn">`、`<span class="comment">` 等。
- 提供“为什么这样写”的解释。

可选交互：

- 复制代码按钮。
- 步骤切换按钮。
- 小测验答案展开。

## HTML 骨架建议

```html
<!DOCTYPE html>
<html lang="zh-CN" data-theme="dark">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>知识点标题 · CS Visual Lesson</title>
  <style>
    /* 1. CSS Variables */
    /* 2. Reset & Base */
    /* 3. Layout */
    /* 4. Typography */
    /* 5. Components */
    /* 6. Visualization */
    /* 7. Code Highlight */
    /* 8. Interactions */
    /* 9. Responsive */
  </style>
</head>
<body>
  <main class="lesson-shell">
    <header class="hero">...</header>
    <section class="card overview">...</section>
    <section class="card visualization">...</section>
    <section class="card walkthrough">...</section>
    <section class="card code-example">...</section>
    <section class="card pitfalls">...</section>
    <section class="card quiz">...</section>
    <section class="card summary">...</section>
  </main>
  <script>
    // theme toggle / optional interactions
  </script>
</body>
</html>
```

## 质量检查清单

生成后必须自检：

### P0 阻断级

- [ ] 是完整 HTML，不是片段。
- [ ] 无外部依赖。
- [ ] 所有 CSS 类均已定义。
- [ ] 可视化由 HTML/CSS 实现，不依赖图片/Canvas/SVG。
- [ ] 知识点解释准确，无明显错误。
- [ ] 代码示例语法正确。
- [ ] 代码示例与可视化对应同一概念。
- [ ] 浅色/深色主题可切换。
- [ ] 移动端布局不破版。
- [ ] 已按 `memory/html_ppt_skill/recommendations.md` 选择主题与核心模板语言。
- [ ] 已读取 `memory/html_ppt_skill/themes.md` 的对应主题 DNA，并在代码前形成 Theme Brief。
- [ ] 若生成多主题预览，每个主题至少改变 5 类视觉变量：背景纹理、字体气质、卡片形态、边框/阴影、图示线条/节点。
- [ ] 主题差异不能只靠改色；同一页面在 50% 缩略图中必须能分辨不同版式气质。
- [ ] 若使用深色主题，默认 `data-theme="dark"` 且仍提供完整浅色变量；若使用浅色主题，默认 `data-theme="light"` 且仍提供完整深色变量。
- [ ] CSS 变量是语义命名体系（`--bg`/`--surface`/`--text`/`--accent`/`--border`/`--code-bg` 等），不直接写颜色字面值。
- [ ] 间距/圆角/字号遵循节奏表（4/8/12/16/20/24/32/48px），不使用随机数值。
- [ ] 交互元素（切换按钮/选项卡/测验/折叠区）具备 hover/focus/active/disabled 四种完整状态。
- [ ] 页面每个 section 可映射到一种模板语言（cover/two-column/code/flow-diagram/arch-diagram/comparison/table/summary）。

### P1 体验级

- [ ] 信息层级清晰，读者能按顺序学习。
- [ ] 视觉风格统一，颜色变量统一。
- [ ] 关键概念有标注和步骤解释。
- [ ] 代码块可读性强。
- [ ] 对比表/误区/小测验至少有一个。
- [ ] 至少包含一个“概念解释 + 可视化 + 代码/示例 + 归纳”的闭环。
- [ ] 页面首屏能让读者立刻知道：学什么、为什么重要、怎么学。

- [ ] 动画有节奏设计：transition duration 统一（200ms/300ms/400ms），easing 曲线一致，运动有目的不花哨。
- [ ] 卡片/组件间距一致：section 间 gap/margin 统一，版式有明显呼吸感。
- [ ] 页面有完整叙事结构：从“这是什么”→“为什么重要”→“怎么工作”→“自己试试”→“记住什么”。
- [ ] 静态验证时检查：信息层级完整、教学闭环完整性、首屏信息可读性、代码示例与可视化标题对应同一概念。
### P2 美术级

- [ ] 页面有专业设计感：留白、卡片、渐变、阴影、边框节奏一致。
- [ ] 标题、正文、代码字体栈区分明显。
- [ ] 状态颜色有语义，不只是装饰。
- [ ] hover/focus/active 状态清晰。
- [ ] 版式能看出 `html-ppt-skill` 的卡片、分栏、流程、架构图或对比表语言。
- [ ] 默认风格优先达到 `engineering-whiteprint` 的工程白板质感，而不是普通 Markdown 文档。

#### P2.1 视觉系统门禁

- [ ] 页面具备明确的视觉母题：工程网格/蓝图线框/论文纸张/开发者暗色/极简白板，只能选一种主母题。
- [ ] 背景不是纯空白：至少包含一种低干扰纹理（网格、径向光斑、分区底色、纸张感、蓝图线条），并使用 CSS 实现。
- [ ] 卡片层级不少于 2 层：主内容卡、辅助说明卡、交互卡在 border/shadow/background 上有可感知差异。
- [ ] accent 色只用于关键路径：主按钮、当前步骤、重要标注、可视化高亮；普通装饰不得滥用 accent。
- [ ] 阴影与边框服务层级：浅色主题优先边框 + 轻阴影；深色主题优先发光边框 + 半透明 surface。

#### P2.2 排版与信息密度

- [ ] 字体栈分工明确：标题用 display/system，正文用 readable sans，代码用 monospace；三者字号/字重有明显层级。
- [ ] 标题区具备 PPT 感：eyebrow/kicker、主标题、副标题、学习目标四件套至少出现三件。
- [ ] 每屏/每 section 有一个视觉焦点，不把解释、代码、图表、测验平均摊平。
- [ ] 长段落拆为短卡片、步骤条、对比表或 callout；正文单段不超过 3 行为宜。
- [ ] 代码块有标题栏/语言标识/运行含义提示，不只是裸 `<pre>`。

#### P2.3 教学可视化美术门禁

- [ ] 至少一个核心可视化具备“输入→处理→输出”或“状态变化前→后”的视觉叙事。
- [ ] 流程图/架构图/对比表必须有方向感：箭头、编号、连接线、阶段标签至少使用两种。
- [ ] 图示元素命名与正文概念一致，视觉标签不能出现只好看但不解释的抽象词。
- [ ] 可视化高亮与代码高亮同步：同一概念使用同一 accent 或同一状态色。
- [ ] 误区/注意/最佳实践使用固定 callout 样式，不临时发明颜色。

#### P2.4 html-ppt-skill 风格映射

- [ ] `engineering-whiteprint`：白底坐标纸、细蓝灰边框、工程标注、轻阴影、模块化卡片。
- [ ] `solarized-light`：低眩光底色、柔和对比、适合长时间阅读，不使用刺眼纯白。
- [ ] `tokyo-night` / `catppuccin-mocha`：深色代码演示时使用高对比代码区、霓虹式 focus，但正文保持克制。
- [ ] `blueprint`：适合架构/网络/流程主题，使用深蓝背景、线框模块、连接线和编号节点。
- [ ] `corporate-clean` / `academic-paper`：适合正式培训或理论主题，减少花哨渐变，强调表格、编号、引用式说明。

#### P2.5 美术自检

- [ ] 缩小到 50% 预览时，仍能一眼分辨标题、主图、代码、总结四个区域。
- [ ] 页面截图去掉文字后，仍能看出版式结构而不是普通文档流。
- [ ] 黑白查看时，信息层级仍能通过字号、间距、边框、形状区分。
- [ ] 首屏有“作品感”：不像默认浏览器样式、不像 Markdown 导出、不像表单后台。
- [ ] 美术增强没有牺牲 P0：仍自包含、无外链、响应式、主题切换可用。

### 生成前小抄

```text
默认主题：engineering-whiteprint
默认骨架：cover/toc + two-column + flow/arch + code + comparison/table + summary/thanks
默认门禁：自包含 + 响应式 + 主题切换 + 物理验证 + 教学闭环
```

若时间紧，宁可减少章节，也不能牺牲 P0。

## 验证方式

若有落地文件，优先执行物理验证：

1. 保存为 `.html`。
2. 静态扫描：
   - 必须包含 `<!DOCTYPE html>`、`<html`、`<style>`、`<script>`、`data-theme`、`viewport`。
   - 禁止出现 `http://`、`https://`、`cdn.`、`<img`、`<canvas`、`<svg`、`<link rel="stylesheet"`、外部 `<script src=`。
   - 检查常用交互 hook：主题切换按钮、quiz/step 按钮、复制按钮等对应 JS 查询对象不为空。
3. 用浏览器或本地静态服务打开。
4. 检查控制台错误。
5. 检查移动端宽度（约 390px）是否破版。
6. 检查主题切换是否生效。
7. 抽查教学一致性：可视化标题、代码示例标题、步骤解析必须指向同一个核心概念。

可用 Python 静态验证模板：

```python
from pathlib import Path
p = Path("cs_lesson_topic.html")
s = p.read_text(encoding="utf-8")
required = ["<!DOCTYPE html>", "<html", "<style>", "<script>", "data-theme", "viewport"]
for token in required:
    assert token in s, token
for token in ["http://", "https://", "cdn.", "<img", "<canvas", "<svg", "<link rel=\"stylesheet\"", "<script src="]:
    assert token.lower() not in s.lower(), token
print("static validation ok", p)
```

若只在对话中输出代码，也必须在文本生成前做静态自检：标签闭合、类名一致、主题变量完整、无外链。

## 输出规则

- 用户要求“生成页面”时：直接给完整 HTML 代码，除非主人要求解释。
- 用户要求“保存文件”时：写入 `.html` 文件并验证。
- 用户要求“做 SOP”时：写入 memory SOP，并更新 L1 极简索引。

## 关联记忆

- `learning_tutor`
- `programming_teaching`
- `guizang_ppt`
- `ui_design`
- `skill_discovery`
