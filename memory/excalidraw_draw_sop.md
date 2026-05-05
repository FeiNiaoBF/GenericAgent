# Excalidraw 画图 SOP — 精简参考

> 核心哲学: **图即论证** — 每个视觉选择承载语义, 遮字识图
> 级别: Simple(3-15元素)→直接Canvas+视觉模式 | Technical(15-50+)→Frame分组+Multi-Zoom(概览→证据→细节)

## 执行摘要（≥1步执行前必读）
1. 判断复杂度 → Simple(3-15元素)直接Canvas | Technical(15-50+)用Frame分组+Multi-Zoom
2. 从视觉模式映射表选 pattern → `from excalidraw_draw import Canvas; c = Canvas("标题")`
3. 遮字识图验证：遮住文字看形状/颜色能否独立说明结构 → 🛑 过验证门禁

## 视觉模式映射表(完整参考见excalidraw_draw.py docstring)
- 时间演进: `pattern_timeline()` 椭圆节点+线主幹
- 中心辐射: `pattern_fan_out()` 椭圆中心+矩形分支
- 多路汇聚: `pattern_convergence()` 矩形→椭圆
- 并排对比: `pattern_side_by_side()` 矩形列
- 流程图: `quick_flowchart()` 矩形/菱形/椭圆
- 思维导图: `quick_mindmap()` 椭圆根+矩形分支+文字叶子
- 代码/数据: `add_code_block()` / `add_json_block()` 等宽+灰底
- 事件序列: `add_event_sequence()` 椭圆角色+箭头+矩形详情
- 段落分隔: `pattern_gap()` 虚线

## 快速调用流程
```python
from excalidraw_draw import Canvas
c = Canvas("标题", palette="default", semantic=True)  # palette: default|warm|cool|pastel|deep
c.add_rect/wait_for_add_ellipse/diamond/arrow/connect/...  # 详见 .py API
vault = r"D:\Documents_Learn\Personal\Obsidian\Codex Vitae"
c.save(os.path.join(vault, "99.System", "Excalidraw", "文件名.excalidraw"))
```

## 语义配色
| 语义 | 用途 | 填充色 |
|------|------|--------|
| primary | 主要 | #dbeafe |
| secondary | 次要 | #f3e8ff |
| start | 开始 | #dcfce7 |
| end | 结束 | #fef2f2 |
| warning | 注意 | #fef9c3 |
| decision | 决策 | #f3e8ff |
| ai | AI | #ccfbf1 |
| inactive | 非活跃 | #f1f5f9 |
| error | 异常 | #fef2f2 |
| data | 数据 | #e0f2fe |
| external | 外部 | #fff7ed |
| highlight | 高亮 | #fdf2f8 |

## 注意事项
1. 语义>装饰: 颜色永远服务于语义
2. 视觉同构: 遮住文字看形状/颜色能否独立说明结构
3. Multi-Zoom: 复杂图用Frame分3层(概览→证据→细节)
4. Container vs Free: 有背景文字用add_rect(label=), 纯标签用add_text()
5. 分组: 相关元素用begin_group/end_group包裹
6. connect vs add_arrow: connect(绑定箭头,拖拽跟随) vs add_arrow(坐标箭头,无绑定)
7. Frame不接受fill=, 用backgroundColor=设背景色
8. 画布首次打开可能需要手动调整视图

## Known Issues
- `_add_bound_text` Eager ID修复(2026-04-27): label在Obsidian中不渲染, 根因boundElements.id延迟生成→修复为eager ID生成

## 🛑 验证门禁（必须执行，否则流程未完成）

| # | 验证动作 | 工具 | 预期结果 | PASS/FAIL |
|---|----------|------|----------|-----------|
| 1 | 元素计数 | web_scan | Canvas内元素数符合预期(Simple 3-15 / Technical 15-50+) | |
| 2 | Frame分组 | web_scan | 每个Frame内含绑定元素，层级关系正确 | |
| 3 | 遮字识图 | 肉眼 | 遮住文字后形状/颜色/布局仍能独立传达结构 | |
| 4 | 坐标无NaN | web_execute_js | 所有元素x/y为有效数值，无undefined | |
| 5 | 导出验证 | 肉眼 | Obsidian渲染正常，无缺失/错位 | |

最终裁定：`VERDICT: PASS` / `VERDICT: FAIL`