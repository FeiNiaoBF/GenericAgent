# Guizang PPT · 10 Layout Skeletons
> 每个布局为 `<section>` 骨架，可直接粘贴到模板 `<body>` 中。`{ }` 为占位符。

---

## L01: Hero Dark 封面
> 深色底+大标题+引导语。用于开场或章节分隔（暗版）。

```html
<section class="slide hero dark">
  <div class="kicker mb-1">{KICKER}</div>
  <h1 class="h-hero">{TITLE}</h1>
  <p class="lead mt-2">{SUBTITLE}</p>
  <div class="meta-row mt-3">
    <span><i class="lucide-user"></i> {AUTHOR}</span>
    <span><i class="lucide-calendar"></i> {DATE}</span>
  </div>
</section>
```

---

## L02: Hero Light 过渡页
> 浅色底+大标题。章节分隔，给观众呼吸感。

```html
<section class="slide hero light text-center">
  <div class="kicker">{SECTION}</div>
  <h2 class="h-hero">{TITLE}</h2>
  <p class="lead mt-2">{SUBTITLE}</p>
</section>
```

---

## L03: 2-6-6 双栏（标题区重）
> 左侧窄留白→中栏正文→右栏补充。信息密度高。

```html
<section class="slide light">
  <div class="kicker mb-1">{SECTION}</div>
  <div class="frame grid-2-6-6 mt-1">
    <div></div>
    <div>
      <h2 class="h-xl">{TITLE}</h2>
      <p class="body-zh mt-1">{BODY}</p>
    </div>
    <div>
      <div class="stat-card mt-2"><div class="stat-num">{NUM}</div><div class="stat-label">{LABEL}</div></div>
      <div class="callout mt-2">{CALLOUT}</div>
    </div>
  </div>
</section>
```

---

## L04: 2-7-5 双栏（正文区重）
> 左留白→正文8分→1/3补充。阅读优先。

```html
<section class="slide light">
  <div class="kicker mb-1">{SECTION}</div>
  <div class="frame grid-2-7-5 mt-1">
    <div></div>
    <div>
      <h2 class="h-xl">{TITLE}</h2>
      <p class="body-zh mt-1">{BODY}</p>
      <div class="stat-card mt-2"><div class="stat-num">{NUM}</div><div class="stat-label">{LABEL}</div></div>
    </div>
    <div></div>
  </div>
</section>
```

---

## L05: 2-8-4 双栏（数据区重）
> 左留白→1/3正文→8分数据。适合图表/代码。

```html
<section class="slide light">
  <div class="kicker mb-1">{SECTION}</div>
  <div class="frame grid-2-8-4 mt-1">
    <div></div>
    <div>
      <h2 class="h-xl">{TITLE}</h2>
      <p class="body-zh mt-1">{BODY}</p>
    </div>
    <div>
      <div class="stat-card"><div class="stat-num">{NUM}</div><div class="stat-label">{LABEL}</div></div>
    </div>
  </div>
</section>
```

---

## L06: 三列卡片
> 3等分卡片。适合对比/步骤/功能展示。

```html
<section class="slide dark">
  <div class="kicker mb-1">{SECTION}</div>
  <h3 class="h-md">{TITLE}</h3>
  <div class="frame grid-3 mt-1 gap-1">
    <div class="stat-card"><div class="stat-num">{N1}</div><div class="stat-label">{L1}</div></div>
    <div class="stat-card"><div class="stat-num">{N2}</div><div class="stat-label">{L2}</div></div>
    <div class="stat-card"><div class="stat-num">{N3}</div><div class="stat-label">{L3}</div></div>
  </div>
</section>
```

---

## L07: 六列仪表盘
> 6等分数据卡片。适合多项KPI展示。

```html
<section class="slide light">
  <div class="kicker mb-1">{SECTION}</div>
  <h3 class="h-md">{TITLE}</h3>
  <div class="frame grid-6 mt-1">
    <div class="stat-card"><div class="stat-num">{N1}</div><div class="stat-label">{L1}</div></div>
    <div class="stat-card"><div class="stat-num">{N2}</div><div class="stat-label">{L2}</div></div>
    <div class="stat-card"><div class="stat-num">{N3}</div><div class="stat-label">{L3}</div></div>
    <div class="stat-card"><div class="stat-num">{N4}</div><div class="stat-label">{L4}</div></div>
    <div class="stat-card"><div class="stat-num">{N5}</div><div class="stat-label">{L5}</div></div>
    <div class="stat-card"><div class="stat-num">{N6}</div><div class="stat-label">{L6}</div></div>
  </div>
</section>
```

---

## L08: 流程管道
> 水平步骤条。适合流程图/时间线。

```html
<section class="slide light">
  <div class="kicker mb-1">{SECTION}</div>
  <h3 class="h-md">{TITLE}</h3>
  <div class="pipeline mt-2">
    <div class="pipe-step">{STEP1}</div><div class="pipe-arrow">→</div>
    <div class="pipe-step">{STEP2}</div><div class="pipe-arrow">→</div>
    <div class="pipe-step">{STEP3}</div><div class="pipe-arrow">→</div>
    <div class="pipe-step">{STEP4}</div>
  </div>
</section>
```

---

## L09: 引用金句页
> 大引用块。适合金句/名言/观点聚焦。

```html
<section class="slide hero dark text-center">
  <div class="kicker">{CONTEXT}</div>
  <blockquote>
    <p class="h-xl">{QUOTE}</p>
  </blockquote>
  <p class="lead mt-2">— {AUTHOR}</p>
</section>
```

---

## L10: 致谢尾页
> 深色底+简洁署名。结尾。

```html
<section class="slide hero dark text-center">
  <div class="kicker">{PHRASE}</div>
  <h2 class="h-hero">{TITLE}</h2>
  <p class="lead mt-2">{SUBTITLE}</p>
  <div class="meta-row mt-3" style="justify-content:center">
    <span><i class="lucide-github"></i> {CONTACT}</span>
  </div>
</section>
```

---

## 布局选型指南
| 目标 | 推荐布局 |
|------|----------|
| 开场/震撼 | L01 Hero Dark |
| 章节过渡 | L02 Hero Light |
| 正文叙述 | L03/L04/L05 |
| 数据对比 | L06 三列 / L07 六列 |
| 流程展示 | L08 流程管道 |
| 金句强调 | L09 引用页 |
|| 结束 | L10 致谢尾页 |
|| 数据表格 | L11 数据表格（新增v1.1） |
|| 图表/图片 | L12 图表占位（新增v1.1） |

---

## L11: 数据表格
> 结构化表格+侧栏说明。适合数据展示/对比清单。v1.1新增。

```html
<section class="slide light">
  <div class="kicker mb-1">{SECTION}</div>
  <div class="frame grid-2-7-5 mt-1">
    <div></div>
    <div>
      <h2 class="h-xl">{TITLE}</h2>
      <p class="body-zh mt-1">{DESC}</p>
    </div>
    <div></div>
  </div>
  <table class="data-table mt-2">
    <thead><tr><th>{COL1}</th><th>{COL2}</th><th>{COL3}</th></tr></thead>
    <tbody>
      <tr><td>{R1C1}</td><td class="num">{R1C2}</td><td><span class="tag">{R1C3}</span></td></tr>
      <tr><td>{R2C1}</td><td class="num">{R2C2}</td><td><span class="tag">{R2C3}</span></td></tr>
      <tr><td>{R3C1}</td><td class="num">{R3C2}</td><td><span class="tag">{R3C3}</span></td></tr>
    </tbody>
  </table>
</section>
```

---

## L12: 图表占位
> 图片占位器+说明文字。适合未准备实际图片时保持版式完整。v1.1新增。

```html
<section class="slide light">
  <div class="kicker mb-1">{SECTION}</div>
  <div class="frame grid-2-5-7 mt-1">
    <div></div>
    <div>
      <h2 class="h-xl">{TITLE}</h2>
      <p class="body-zh mt-1">{DESC}</p>
      <div class="callout mt-2">{CALLOUT}</div>
    </div>
    <div>
      <div class="img-placeholder">
        <div class="text-center">
          <i class="lucide-bar-chart-3"></i>
          <p>图表占位<br>{CHART_DESC}</p>
        </div>
      </div>
    </div>
  </div>
</section>
```
