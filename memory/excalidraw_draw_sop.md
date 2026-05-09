# Excalidraw 画图 SOP (v1.1)

> **图即论证** — 视觉选择承载语义，遮字识图
> Simple(3-15元素)→Canvas | Technical(15-50+)→Frame+Multi-Zoom

## 执行摘要
1. 判断复杂度 → 选pattern → `from excalidraw_draw import Canvas; c = Canvas("标题")`
2. 遮字识图验证 → 🛑 门禁

## 视觉模式
| 模式 | 方法 | 适用 |
|------|------|------|
| 时间演进 | `pattern_timeline()` | 椭圆节点+线主幹 |
| 中心辐射 | `pattern_fan_out()` | 椭圆中心+矩形分支 |
| 多路汇聚 | `pattern_convergence()` | 矩形→椭圆 |
| 并排对比 | `pattern_side_by_side()` | 矩形列 |
| 流程图 | `quick_flowchart()` | 矩形/菱形/椭圆 |
| 思维导图 | `quick_mindmap()` | 椭圆根+分支+叶子 |
| 代码/数据 | `add_code_block()`/`add_json_block()` | 等宽+灰底 |
| 事件序列 | `add_event_sequence()` | 角色+箭头+详情 |

## 快速调用
```python
from excalidraw_draw import Canvas
c = Canvas("标题", palette="default|warm|cool|pastel|deep", semantic=True)
# c.add_rect / add_ellipse / diamond / arrow / connect / ...
vault = r"D:\Documents_Learn\Personal\Obsidian\Codex Vitae"
c.save(os.path.join(vault, "99.System", "Excalidraw", "文件名.excalidraw"))
```

## 语义配色
primary/#dbeafe | secondary/#f3e8ff | start/#dcfce7 | end/#fef2f2 | warning/#fef9c3 | decision/#f3e8ff | ai/#ccfbf1 | inactive/#f1f5f9 | error/#fef2f2 | data/#e0f2fe | external/#fff7ed | highlight/#fdf2f8

## 注意
1. 语义>装饰 | 2. 遮字看形状能否独立说明结构 | 3. 复杂图Frame分3层(概览→证据→细节)
4. 有背景文字→`add_rect(label=)`，纯标签→`add_text()`
5. `connect`(绑定箭头跟随) vs `add_arrow`(坐标箭头无绑定)
6. Frame用`backgroundColor=`设背景色(不接受fill=)

## 🛑 验证门禁
| # | 验证动作 | 工具 | 预期结果 | PASS/FAIL |
|---|----------|------|----------|-----------|
| 1 | 元素计数 | web_scan | Simple 3-15 / Technical 15-50+ | |
| 2 | Frame分组 | web_scan | Frame内含绑定元素 | |
| 3 | 遮字识图 | 肉眼 | 形状/颜色独立传达结构 | |
| 4 | 坐标无NaN | web_execute_js | x/y为有效数值 | |
| 5 | 导出验证 | 肉眼 | Obsidian渲染正常 | |

最终裁定：`VERDICT: PASS` / `VERDICT: FAIL`