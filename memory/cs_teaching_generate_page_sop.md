---
name: cs_teaching_generate_page
description: 生成自包含CS交互HTML教学页
---

# CS Teaching Page SOP

## 生成前
- 先定六要素：知识点类型｜学完能做什么｜核心可视化对象｜代码语言｜难度｜交互点；缺失给≤6个选项，主人说“你决定”则自动匹配。
- 若属于完整CS课程学习规划、教材融合、Lab/Homework/Project工作区或测试闭环，先走`cs_course_learning_loop`；本SOP只负责把单个概念做成HTML教学可视化。
- 主题先读`memory/html_ppt_skill/recommendations.md`、`themes.md`。默认浅色`engineering-whiteprint`；编程基础→catppuccin；网络/OS/并发→tokyo-night/blueprint；理论/算法→academic-paper/solarized-light。
- 多主题预览须改≥5类：背景/字体/卡片/边框/图示线条；深色`data-theme="dark"`，浅色`light`；CSS变量完整。

## 硬约束
- 模块线：hero→overview→mental-model→visualization→walkthrough→code-example→tradeoff→pitfalls/quiz→summary。
- 自包含HTML/CSS/JS内联；禁外部资源/Canvas/SVG；必有`style/script/viewport/data-theme`；响应式390px不破；代码15-40行有注释；全页同一概念；CSS类全定义；交互对象非空。
- 可视化优先Grid/Flex/border/gradient/pseudo-elements/CSS variables/transition/transform；图示必有标注、颜色含义、状态说明、交互反馈。

## 骨架
```html
<!DOCTYPE html><html lang="zh-CN" data-theme="dark"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>知识点标题 · CS Visual Lesson</title><style>/* variables/reset/layout/components/visual/code/responsive */</style></head><body><main class="lesson-shell"><header class="hero">...</header><section class="card overview">...</section><section class="card visualization">...</section><section class="card walkthrough">...</section><section class="card code-example">...</section><section class="card pitfalls">...</section><section class="card quiz">...</section><section class="card summary">...</section></main><script>/* theme toggle/interactions */</script></body></html>
```

## 质量门禁
- P0：HTML完整无外链/Canvas/SVG；含必备token；知识准/代码对/图码同概念；响应式不破；已读theme recommendations；多主题改≥5类；变量语义化`--bg/--surface/--text/--accent/--border/--code-bg`。
- P1：首屏讲学什么/为什么/怎么学；至少1个“概念-图-码-归纳”闭环；有误区/对比/测验；交互有hover/focus/active/disabled；动画节奏统一。
- P2：单一视觉母题；背景低干扰；卡片≥2层；accent只给关键路径；字体栈分工；长段落成卡片；核心图示有方向/状态/同步高亮；50%缩略图可辨四区。

## 验证
落地后物理验证：①存`.html`；②扫必备token`!DOCTYPE/html/style/script/data-theme/viewport`；③禁token`http/https/cdn/img/canvas/svg/link stylesheet/script src`；④JS查交互对象非空；⑤浏览器开→控制台/390px/主题切换；⑥抽查教学一致性。
```python
from pathlib import Path
s=Path("cs_lesson_topic.html").read_text(encoding="utf-8")
for t in ["<!DOCTYPE html>","<html","<style","<script","data-theme","viewport"]: assert t in s,t
for t in ["http://","https://","cdn.","<img","<canvas","<svg",'<link rel="stylesheet"','<script src=']: assert t.lower() not in s.lower(),t
print("static validation ok")
```
对话中输出代码也须自检：标签闭合、类名一致、主题变量完整、无外链。

## 经验
- 代码块修复：先静探测`pre/code/类名`，确认缺样式非正文；不改正文，只增强CSS+JS包装；改前备份；CSS含深/浅变量、等宽字体、边框、滚动、移动端；JS渐进加顶部栏/行号/复制；验证原`pre`不减、有`.code-wrap`/复制按钮/行号token/无外链。
- 双语增强：只补术语/英文短句/代码表达；页面禁写 SOP/制作策略/质量门禁/内部评估；验证扫“制作策略/学习配比/内部评估”等不得出现。

## 输出
- “生成页面”：直接给完整HTML，除非主人要求解释；“保存文件”：写入`.html`并验证；“做SOP”：写入memory SOP并更新L1极简索引。
- 关联：`learning_tutor_study`、`programming_teaching`、`guizang_ppt`、`ui_design`、`skill_discovery`。

`VERDICT: PASS` / `VERDICT: FAIL`
