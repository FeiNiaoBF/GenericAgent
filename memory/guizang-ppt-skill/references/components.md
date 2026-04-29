# Guizang PPT · Components Reference

## 标题系统
| 类名 | 用途 | 字重 | 字体族 | 尺寸 |
|------|------|------|--------|------|
| `.h-mega` | 超大字 | 900 | 衬线 | clamp(3.5rem,8vw,6rem) |
| `.h-hero` | 封面/分隔大标题 | 800 | 衬线 | clamp(2.4rem,5.5vw,4rem) |
| `.h-xl` | 页面主标题 | 700 | 衬线 | clamp(1.8rem,3.5vw,2.6rem) |
| `.h-sub` | 副标题 | 600 | 衬线 | 1.4rem |
| `.h-md` | 小标题 | 600 | 非衬线 | 1.15rem |

## 正文系统
| 类名 | 用途 | 字重 | 行高 |
|------|------|------|------|
| `.body-zh` | 正文段落 | 400 | 1.75 |
| `.lead` | 引导/摘要文字 | 300 | 1.6 |
| `.kicker` | 章节标签/眉题 | 600 | - |
| `blockquote` | 引用块 | italic | - |

## 布局系统
| 类名 | 列数 | 列宽比 | 用途 |
|------|------|--------|------|
| `.frame.grid-2-8-4` | 3 | 2:8:4 | 数据优先 |
| `.frame.grid-2-7-5` | 3 | 2:7:5 | 正文优先 |
| `.frame.grid-2-6-6` | 3 | 2:6:6 | 均衡双栏 |
| `.frame.grid-2-5-7` | 3 | 2:5:7 | 图表优先 |
| `.frame.grid-3` | 3 | 1:1:1 | 三列对比 |
| `.frame.grid-6` | 6 | 等分 | KPI仪表盘 |
| `.frame.grid-2` | 2 | 1:1 | 双列 |
| `.frame.grid-4` | 4 | 等分 | 四列 |
| `.frame.stack` | 1 | 全宽 | 垂直堆叠 |

## 组件
| 类名 | 用途 | 结构 |
|------|------|------|
| `.meta-row` | 元信息行（作者/日期） | flex行 |
| `.stat-card` | 数据卡片 | .stat-num + .stat-label |
| `.callout` | 要点提示 | 左侧色条+内容 |
| `.pipeline` | 流程管道 | .pipe-step + .pipe-arrow |
| `table.data-table` | 结构化数据表格 | thead th + tbody td |
| `.img-placeholder` | CSS图片占位器 | 虚线框+图标+文字 |

## 主题系统
| 主题 | 暗/亮 | 特征 |
|------|--------|------|
| Noir Editorial | dark hero + light | 深墨暖纸 |
| Bone & Blood | dark hero + light | 骨白赤墨 |
| Midnight Navy | dark hero + light | 海军蓝科技 |
| Forest Ink | dark hero + light | 墨绿羊皮 |
| Slate & Snow | dark hero + light | 冷灰极简 |

## 图标（Lucide）
```html
<i class="lucide-user"></i>
<i class="lucide-calendar"></i>
<i class="lucide-github"></i>
<i class="lucide-globe"></i>
<i class="lucide-cpu"></i>
<i class="lucide-zap"></i>
<i class="lucide-target"></i>
<i class="lucide-trending-up"></i>
<i class="lucide-check-circle"></i>
<i class="lucide-arrow-right"></i>
<i class="lucide-bar-chart-3"></i>
<i class="lucide-image"></i>
```

---

## 表格组件 `.data-table` (v1.1新增)

用于结构化多列数据展示。标准HTML `<table>` + `.data-table` 类名：
- 表头自动大写+字间距+底部边框
- 数据行hover高亮
- `.num` 数字列右对齐+等宽数字
- `.tag` 标签/状态单元格

```html
<table class="data-table">
  <thead><tr><th>名称</th><th>数值</th><th>状态</th></tr></thead>
  <tbody>
    <tr><td>项目A</td><td class="num">85%</td><td><span class="tag">进行中</span></td></tr>
  </tbody>
</table>
```

## 图片占位器 `.img-placeholder` (v1.1新增)

纯CSS占位图，无外部图片依赖。虚线框+半透明图标+文字。适合：
- 实际图片未准备好时保持版式
- Mockup/原型演示
- 可用图标：`lucide-bar-chart-3`, `lucide-image`, `lucide-trending-up`

```html
<div class="img-placeholder">
  <div class="text-center">
    <i class="lucide-bar-chart-3"></i>
    <p>图表占位<br>Q1 用户增长趋势</p>
  </div>
</div>
```
