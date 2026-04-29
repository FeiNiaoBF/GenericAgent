# Guizang PPT · Quality Checklist

## P0: 阻断级（必须全部通过）
- [ ] 所有CSS类名在模板中已定义（无 `h-hero`/`h-xl`/`grid-*`/`stat-card`/`callout`/`pipeline` 等未定义）
- [ ] 主题节奏：无连续3页同一 theme（light/dark/hero 交替）
- [ ] >=8页时包含至少 1 页 hero dark + 1 页 hero light
- [ ] 大标题使用衬线体（h-hero/h-xl/h-sub），正文使用非衬线体（body-zh）
- [ ] 无 emoji，使用 Lucide 图标（`<i class="lucide-*"></i>`）
- [ ] 图片使用 `height:Nvh` 而非 `aspect-ratio`
- [ ] 无 `align-self: end`（图片堆底问题）

## P1: 严重（影响视觉质量）
- [ ] `<section>` 类名格式：`slide {theme} [{hero}]`，如 `slide hero dark`
- [ ] kicker 文本 <= 5字用 `nowrap`，>5字手动加 `<br>` 断行
- [ ] 每页不超过一个核心论点
- [ ] 中英交替时 chrome/kicker 每页不同，不重复翻译
- [ ] stat-card 内 stat-num 为数字/短字，stat-label 为描述
- [ ] 所有 `<section>` 标签闭合正确

## P2: 中度（影响体验）
- [ ] 页面数量 6-12 页（含封面和致谢）
- [ ] 封面使用 L01 Hero Dark
- [ ] 至少一个章节分隔页（L02 Hero Light）
- [ ] 尾页使用 L10 致谢
- [ ] 模板注释中的示例 `<section>` 需过滤，不参与计数

## P3: 轻度（锦上添花）
- [ ] 色彩对比度足够（WCAG AA）
- [ ] 字体回退栈完整
- [ ] 打印样式正确（@media print）
- [ ] file:// URL 浏览器可打开（或 python serve）
