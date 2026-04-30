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

## Chart.js 图表 `.chart-box` (v1.2新增)

容器使用 `.chart-box`，内放 `<canvas>`。颜色由主题 CSS 变量 `--chart-1` ~ `--chart-5` 驱动，无需硬编码 hex。

### 柱状图 (Bar)
```html
<div class="chart-box">
  <canvas id="chart1"></canvas>
</div>
<script>
(function(){
  const cs=getComputedStyle(document.documentElement);
  const colors=[1,2,3,4,5].map(i=>cs.getPropertyValue('--chart-'+i).trim());
  const isDark=document.body.classList.contains('dark');
  new Chart(document.getElementById('chart1'),{
    type:'bar',
    data:{
      labels:['Q1','Q2','Q3','Q4'],
      datasets:[{
        label:'营收(百万)',
        data:[12,19,8,24],
        backgroundColor:colors,
        borderColor:isDark?'rgba(255,255,255,0.08)':'rgba(0,0,0,0.06)',
        borderWidth:1
      }]
    },
    options:{
      responsive:true,maintainAspectRatio:true,
      plugins:{legend:{labels:{color:isDark?'rgba(255,255,255,0.6)':'rgba(0,0,0,0.6)'}}},
      scales:{
        x:{ticks:{color:isDark?'rgba(255,255,255,0.45)':'rgba(0,0,0,0.45)'},grid:{display:false}},
        y:{ticks:{color:isDark?'rgba(255,255,255,0.45)':'rgba(0,0,0,0.45)'},grid:{color:isDark?'rgba(255,255,255,0.06)':'rgba(0,0,0,0.06)'}}
      }
    }
  });
})();
</script>
```

### 折线图 (Line)
```html
<div class="chart-box">
  <canvas id="chart2"></canvas>
</div>
<script>
(function(){
  const cs=getComputedStyle(document.documentElement);
  const colors=[1,2,3].map(i=>cs.getPropertyValue('--chart-'+i).trim());
  const isDark=document.body.classList.contains('dark');
  new Chart(document.getElementById('chart2'),{
    type:'line',
    data:{
      labels:['1月','2月','3月','4月','5月','6月'],
      datasets:[
        {label:'产品A',data:[30,45,38,52,48,60],borderColor:colors[0],backgroundColor:colors[0]+'22',fill:true,tension:0.3},
        {label:'产品B',data:[20,35,28,40,42,50],borderColor:colors[1],backgroundColor:colors[1]+'22',fill:true,tension:0.3}
      ]
    },
    options:{
      responsive:true,maintainAspectRatio:true,
      plugins:{legend:{labels:{color:isDark?'rgba(255,255,255,0.6)':'rgba(0,0,0,0.6)'}}},
      scales:{
        x:{ticks:{color:isDark?'rgba(255,255,255,0.45)':'rgba(0,0,0,0.45)'},grid:{display:false}},
        y:{ticks:{color:isDark?'rgba(255,255,255,0.45)':'rgba(0,0,0,0.45)'},grid:{color:isDark?'rgba(255,255,255,0.06)':'rgba(0,0,0,0.06)'}}
      }
    }
  });
})();
</script>
```

### 饼图 (Doughnut)
```html
<div class="chart-box-sm">
  <canvas id="chart3"></canvas>
</div>
<script>
(function(){
  const cs=getComputedStyle(document.documentElement);
  const colors=[1,2,3,4].map(i=>cs.getPropertyValue('--chart-'+i).trim());
  const isDark=document.body.classList.contains('dark');
  new Chart(document.getElementById('chart3'),{
    type:'doughnut',
    data:{
      labels:['直销','渠道','电商','其他'],
      datasets:[{data:[40,30,20,10],backgroundColor:colors,borderColor:isDark?'rgba(255,255,255,0.1)':'white',borderWidth:2}]
    },
    options:{
      responsive:true,maintainAspectRatio:true,
      plugins:{legend:{labels:{color:isDark?'rgba(255,255,255,0.6)':'rgba(0,0,0,0.6)'}}}
    }
  });
})();
</script>
```

### 主题颜色映射
| 主题 | --chart-1 | --chart-2 | --chart-3 | --chart-4 | --chart-5 |
|------|-----------|-----------|-----------|-----------|-----------|
| Noir | #2d3561 | #6b2d3e | #c9a96e | #5c6b5c | #8a8a9a |
| Bone | #c0392b | #6b1a1a | #e8d5c0 | #7a6a6a | #b8944a |
| Navy | #3b6db5 | #2da4a4 | #9aacbc | #6b4d8b | #d4863b |
| Forest | #4a7c4a | #8b9a3b | #b87b3b | #5a3d2b | #3b6b8b |
| Slate | #4a6fa5 | #5a5a6a | #9a9a9a | #6b8ba4 | #b8706e |

### 注意事项
- 每个图表 `<canvas>` 需要唯一 `id`
- 颜色从 CSS 变量读取，`dark` 模式自动切换网格/文字颜色
- 饼图推荐用 `.chart-box-sm`（限制高度），柱状/折线用 `.chart-box`
