---
name: ui_design
description: 产出界面设计方案、视觉规范与组件建议
---
# UI Design SOP

## 边界
- 单责：生成/审查UI与UX方案。
- 组件代码实现转 `vue3_component_sop`。

## 启动确认
- 品牌调性：正式/活泼/极简/奢华；缺省中性。
- 可访问性：默认 WCAG AA；无障碍优先则 AAA。
- 设备：mobile-first；断点 `640/768/1024/1280`。
- 主题：暗色模式从 token 层独立设计。

## 设计顺序
1. 信息层级：主任务、次任务、危险操作分层。
2. Token：颜色/字体/间距/圆角/阴影先变量化。
3. 布局：页面 Grid，组件 Flex，移动端先行。
4. 组件状态：`default/hover/active/focus/disabled/loading/error`。
5. 可访问性：对比度、键盘、标签、减弱动效。
6. 输出：说明、tokens、组件状态、验收清单。

## 关键规范
- 颜色：优先 `OKLCH`；主色12阶 `50..950`；中性60%+主色30%+强调10%。
- 对比：正文 `>=4.5:1`；大字/图标/边框 `>=3:1`。
- 禁止：硬编码 `hex/rgb`；只靠颜色表达状态；`outline:none` 无替代。
- 排版：字号用 `rem`；正文 `>=16px`，移动 `>=14px`；行高 `1.4-1.8`。
- 间距：4px网格；常用 `4/8/12/16/20/24/32/40/48/64/80/96`。
- 布局：移动1列，平板2-4列，桌面6-12列。
- 组件：尺寸 `sm/md/lg`；变体 `fill > outline > ghost`；触摸目标 `>=44x44px`。
- 键盘：Tab顺序合理；Enter/Space触发；Escape关闭。

## Token架构
```css
:root {
  --blue-500: oklch(65% 0.24 250);  /* 原始层 */
  --color-primary: var(--blue-500);  /* 语义层 */
  --button-bg: var(--color-primary); /* 组件层 */
}
```
- 命名：`{role}-{property}-{modifier}`，如 `color-primary-bg-hover`。
- 暗色模式用独立色阶，不做简单反色。

## 可访问性验收
- 图片有有效 `alt`；装饰图 `alt=""`。
- 表单有 `<label>`，错误提示与字段关联。
- focus ring 可见；disabled 说明原因，不只改透明度。
- 动画支持 `prefers-reduced-motion`。
- 状态用颜色 + 文字/图标/形状表达。

## 输出模板
```markdown
## Design Intent
<目标用户、品牌调性、核心任务>
## Layout
<断点、网格、信息层级>
## Tokens
<颜色/字体/间距/圆角核心变量>
## Components
<关键组件状态矩阵>
## Accessibility
<对比度、键盘、表单、动效验收>
## Risks
<体验或实现风险>
```

## 验收
- 先 token 后组件，无散落硬编码。
- 交互组件覆盖7状态与键盘操作。
- 文本/图标/边框达到WCAG AA。
- 响应式按 mobile-first 描述。
- `VERDICT: PASS` / `VERDICT: FAIL`
