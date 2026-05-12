# -*- coding: utf-8 -*-
from _encoding import setup_utf8; setup_utf8()
"""excalidraw_draw.py — Excalidraw 自动绘图模块
用法: from excalidraw_draw import Canvas, Rect, Text, Arrow, Ellipse, Diamond

=== 视觉模式映射 ===
时间演进→pattern_timeline(椭圆+线) | 辐射分类→pattern_fan_out(椭圆+矩形)
汇聚归因→pattern_convergence(矩形→椭圆) | 对比→pattern_side_by_side(矩形列)
流程→quick_flowchart(矩形/菱形/椭圆) | 层级→quick_mindmap(椭圆+矩形+文字)
代码/数据→add_code_block/add_json_block | 事件→add_event_sequence

=== 语义配色 ===
primary=#dbeafe | secondary=#f3e8ff | start=#dcfce7 | end=#fef2f2
warning=#fef9c3 | decision=#f3e8ff | ai=#ccfbf1 | inactive=#f1f5f9
error=#fef2f2 | data=#e0f2fe | external=#fff7ed | highlight=#fdf2f8

=== 关键规则 ===
- 语义>装饰: 颜色永远服务于语义
- 视觉同构: 遮住文字看形状能否独立说明结构
- Multi-Zoom: 复杂图用Frame分3层(概览→证据→细节)
- Container=add_rect(label=), 纯标签=add_text()
- connect()创建绑定箭头(拖拽跟随), add_arrow()坐标箭头(无绑定)
- Frame不接受fill=, 用backgroundColor=
- known issue: _add_bound_text eager ID修复(2026-04-27)
"""

import json, random, os, math
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Tuple

# ─── 语义化配色方案 ─────────────────────────────────
# 颜色编码含义，而非装饰。每个语义目的有独立的 fill/stroke
SEMANTIC_COLORS = {
    "primary":      {"fill": "#dbeafe", "stroke": "#1e40af", "desc": "主要/主体"},
    "secondary":    {"fill": "#f0fdf4", "stroke": "#15803d", "desc": "次要/支撑"},
    "start":        {"fill": "#dcfce7", "stroke": "#166534", "desc": "开始/入口"},
    "end":          {"fill": "#fef2f2", "stroke": "#991b1b", "desc": "结束/出口"},
    "warning":      {"fill": "#fef9c3", "stroke": "#a16207", "desc": "警告/注意"},
    "decision":     {"fill": "#f3e8ff", "stroke": "#6b21a8", "desc": "决策/判断"},
    "ai":           {"fill": "#ecfdf5", "stroke": "#0f766e", "desc": "AI/自动化"},
    "inactive":     {"fill": "#f3f4f6", "stroke": "#6b7280", "desc": "非活跃/参考"},
    "error":        {"fill": "#fee2e2", "stroke": "#dc2626", "desc": "错误/异常"},
    "data":         {"fill": "#e0f2fe", "stroke": "#0369a1", "desc": "数据/存储"},
    "external":     {"fill": "#fff7ed", "stroke": "#c2410c", "desc": "外部系统"},
    "highlight":    {"fill": "#fdf4ff", "stroke": "#a21caf", "desc": "高亮/强调"},
}

# 旧的随机取色方案（保留兼容）
PALETTES = {
    "default": {
        "bg": ["#a5d8ff", "#d3f9d8", "#ffc9c9", "#ffec99", "#d0bfff", "#f3d9fa", "#c5f6fa"],
        "line": "#1e1e1e", "fill_alpha": 100,
    },
    "pastel": {
        "bg": ["#e7f5ff", "#ebfbee", "#fff0f6", "#fff9db", "#f3f0ff", "#f8f0fc", "#e3fafc"],
        "line": "#495057", "fill_alpha": 80,
    },
    "vivid": {
        "bg": ["#339af0", "#51cf66", "#ff6b6b", "#fcc419", "#7950f2", "#e64980", "#22b8cf"],
        "line": "#fff", "fill_alpha": 100,
    },
}

# 箭头颜色规范：使用源元素的 stroke 或固定中性色
ARROW_COLORS = {
    "primary": "#1e40af", "secondary": "#15803d", "start": "#166534",
    "end": "#991b1b", "warning": "#a16207", "decision": "#6b21a8",
    "ai": "#0f766e", "inactive": "#6b7280", "error": "#dc2626",
    "data": "#0369a1", "external": "#c2410c", "highlight": "#a21caf",
    "neutral": "#64748b",
}

FONT_FAMILIES = {1: "手写体", 2: "等宽体", 3: "标准体"}

_SEED = 0
def _next_seed():
    global _SEED
    _SEED += 1
    return _SEED % 2**31

def _make_id(prefix="el"):
    return f"{prefix}-{random.randint(100000, 999999)}-{_next_seed()}"

def _edge_intersection(el, target_x, target_y):
    """计算从 el 中心到目标点的连线在 el 边缘的出射点。

    Returns:
        (world_x, world_y, focus): 边缘交点坐标和 focus 值(-1~1)
    """
    cx = el.x + el.width / 2
    cy = el.y + el.height / 2
    dx = target_x - cx
    dy = target_y - cy

    if dx == 0 and dy == 0:
        return (cx, cy, 0.0)

    hw = el.width / 2
    hh = el.height / 2

    if el.type == "ellipse":
        theta = math.atan2(dy, dx)
        x = cx + hw * math.cos(theta)
        y = cy + hh * math.sin(theta)
        focus = math.sin(theta)  # -1 top, 1 bottom
        return (x, y, max(-1.0, min(1.0, focus)))

    # Rectangle / Diamond
    if dx == 0:
        y = cy + hh * (1 if dy > 0 else -1)
        return (cx, y, 0.0)
    if dy == 0:
        x = cx + hw * (1 if dx > 0 else -1)
        return (x, cy, 0.0)

    tx = hw / abs(dx)
    ty = hh / abs(dy)

    if tx < ty:
        x = cx + hw * (1 if dx > 0 else -1)
        y = cy + dy * tx
        focus = (y - cy) / hh
    else:
        y = cy + hh * (1 if dy > 0 else -1)
        x = cx + dx * ty
        focus = (x - cx) / hw

    return (x, y, max(-1.0, min(1.0, focus)))

# ─── 核心元素构建器 ────────────────────────────────

@dataclass
class Element:
    """基础元素，所有形状的基类"""
    type: str = "rectangle"
    x: float = 0
    y: float = 0
    width: float = 100
    height: float = 60
    angle: float = 0
    strokeColor: str = "#1e1e1e"
    backgroundColor: str = "#ffffff"
    fillStyle: str = "solid"
    strokeWidth: int = 2
    strokeStyle: str = "solid"
    roughness: int = 1
    opacity: int = 100
    groupIds: list = field(default_factory=list)
    frameId: Optional[str] = None
    roundness: Optional[dict] = None
    seed: int = 0
    version: int = 1
    versionNonce: int = 0
    isDeleted: bool = False
    boundElements: Optional[list] = None
    updated: int = 1
    link: Optional[str] = None
    locked: bool = False
    id: str = ""

    def to_dict(self):
        d = {}
        for k, v in self.__dict__.items():
            if v is not None:
                d[k] = v
        if "id" in d and not d["id"]:
            d["id"] = _make_id(self.type)
        if "seed" in d and not d["seed"]:
            d["seed"] = _next_seed()
        return d


class Rect(Element):
    def __init__(self, x, y, w, h, label="", **kw):
        display = {k: kw.pop(k, None) for k in _DISPLAY_KEYS if k in kw}
        super().__init__(type="rectangle", x=x, y=y, width=w, height=h, **kw)
        self.roundness = {"type": 3}
        self.text = label
        self.fontSize = display.get("fontSize", 20)
        self.fontFamily = display.get("fontFamily", 3)
        self.textAlign = display.get("textAlign", "center")
        self.verticalAlign = display.get("verticalAlign", "middle")
        self.containerId = None
        self.originalText = label
        self.lineHeight = 1.25
        self.baseline = 0
        self._extra = {
            "text": label, "fontSize": self.fontSize, "fontFamily": self.fontFamily,
            "textAlign": self.textAlign, "verticalAlign": self.verticalAlign,
            "containerId": None, "originalText": label, "lineHeight": 1.25, "baseline": 0,
        }

    def to_dict(self):
        d = super().to_dict()
        d.update(self._extra)
        d.pop("_extra", None)
        return d


class Text(Element):
    """Free-Floating Text — 无容器的独立文字，用于标题/标签/注释"""
    def __init__(self, x, y, text, font_size=20, font_family=3, **kw):
        display = {k: kw.pop(k, None) for k in _DISPLAY_KEYS if k in kw}
        super().__init__(type="text", x=x, y=y, width=kw.pop("w", 200), height=kw.pop("h", 30), **kw)
        self.text = text
        self.fontSize = font_size
        self.fontFamily = font_family
        self.textAlign = display.get("textAlign", "left")
        self.verticalAlign = display.get("verticalAlign", "middle")
        self.containerId = None
        self.originalText = text
        self.lineHeight = 1.25
        self.baseline = font_size * 1.1
        self.roundness = None


_DISPLAY_KEYS = {"fontSize", "fontFamily", "textAlign", "verticalAlign"}

class Ellipse(Element):
    def __init__(self, x, y, w, h, label="", **kw):
        display = {k: kw.pop(k, None) for k in _DISPLAY_KEYS if k in kw}
        super().__init__(type="ellipse", x=x, y=y, width=w, height=h, **kw)
        self.roundness = None
        self.text = label
        self.fontSize = display.get("fontSize", 20)
        self.fontFamily = display.get("fontFamily", 3)
        self.textAlign = display.get("textAlign", "center")
        self.verticalAlign = display.get("verticalAlign", "middle")
        self.containerId = None
        self.originalText = label
        self.lineHeight = 1.25
        self.baseline = 0
        self._extra = {
            "text": label, "fontSize": self.fontSize, "fontFamily": self.fontFamily,
            "textAlign": self.textAlign, "verticalAlign": self.verticalAlign,
            "containerId": None, "originalText": label, "lineHeight": 1.25, "baseline": 0,
        }

    def to_dict(self):
        d = super().to_dict()
        d.update(self._extra)
        d.pop("_extra", None)
        return d


class Diamond(Element):
    def __init__(self, x, y, w, h, label="", **kw):
        display = {k: kw.pop(k, None) for k in _DISPLAY_KEYS if k in kw}
        super().__init__(type="diamond", x=x, y=y, width=w, height=h, **kw)
        self.roundness = None
        self.text = label
        self.fontSize = display.get("fontSize", 20)
        self.fontFamily = display.get("fontFamily", 3)
        self.textAlign = display.get("textAlign", "center")
        self.verticalAlign = display.get("verticalAlign", "middle")
        self.containerId = None
        self.originalText = label
        self.lineHeight = 1.25
        self.baseline = 0
        self._extra = {
            "text": label, "fontSize": self.fontSize, "fontFamily": self.fontFamily,
            "textAlign": self.textAlign, "verticalAlign": self.verticalAlign,
            "containerId": None, "originalText": label, "lineHeight": 1.25, "baseline": 0,
        }

    def to_dict(self):
        d = super().to_dict()
        d.update(self._extra)
        d.pop("_extra", None)
        return d


class Arrow(Element):
    def __init__(self, x1, y1, x2, y2, label="", **kw):
        display = {k: kw.pop(k, None) for k in _DISPLAY_KEYS if k in kw}
        endArrowhead = kw.pop("endArrowhead", "arrow")
        startArrowhead = kw.pop("startArrowhead", None)
        # Pop binding from kw so they don't get passed to Element base
        self.startBinding = kw.pop("startBinding", None)
        self.endBinding = kw.pop("endBinding", None)
        super().__init__(type="arrow", x=x1, y=y1, width=x2-x1, height=y2-y1, **kw)
        self.roundness = {"type": 2}
        self.points = [[0, 0], [x2-x1, y2-y1]]
        self.lastCommittedPoint = None
        self.startArrowhead = startArrowhead
        self.endArrowhead = endArrowhead
        self.text = label
        self.fontSize = display.get("fontSize", 16)
        # _extra no longer hardcodes startBinding/endBinding — to_dict handles them directly
        self._extra = {
            "points": self.points, "lastCommittedPoint": None,
            "startArrowhead": self.startArrowhead, "endArrowhead": self.endArrowhead,
            "text": label
        }

    def to_dict(self):
        d = super().to_dict()
        d.update(self._extra)
        d.pop("_extra", None)
        # Dynamically include bindings (may be set after construction)
        if self.startBinding is not None:
            d["startBinding"] = self.startBinding
        if self.endBinding is not None:
            d["endBinding"] = self.endBinding
        # Remove None entries to keep JSON clean
        for key in ("startArrowhead", "endArrowhead"):
            if key in d and d[key] is None:
                del d[key]
        return d


class Line(Element):
    def __init__(self, points, **kw):
        x = min(p[0] for p in points)
        y = min(p[1] for p in points)
        w = max(p[0] for p in points) - x
        h = max(p[1] for p in points) - y
        super().__init__(type="line", x=x, y=y, width=w or 1, height=h or 1, **kw)
        self.roundness = {"type": 2}
        self.points = [[p[0]-x, p[1]-y] for p in points]
        self.lastCommittedPoint = None
        self._extra = {
            "points": self.points, "lastCommittedPoint": None
        }

    def to_dict(self):
        d = super().to_dict()
        d.update(self._extra)
        d.pop("_extra", None)
        return d


class Frame(Element):
    """Frame 元素 — 用于 Multi-Zoom 段落分组/区域划分"""
    def __init__(self, x, y, w, h, name="", **kw):
        super().__init__(type="frame", x=x, y=y, width=w, height=h, **kw)
        self.roundness = {"type": 3}
        self.strokeColor = kw.get("strokeColor", "#94a3b8")
        self.strokeWidth = kw.get("strokeWidth", 1)
        self.strokeStyle = kw.get("strokeStyle", "dashed")
        self.backgroundColor = kw.get("backgroundColor", "#f8fafc")
        self.opacity = kw.get("opacity", 30)
        self.name = name
        self._extra = {"name": name}

    def to_dict(self):
        d = super().to_dict()
        d.update(self._extra)
        d.pop("_extra", None)
        return d


# ─── 画布 ──────────────────────────────────────────

class Canvas:
    """Excalidraw 画布 — 支持语义配色 + 视觉模式 + Frame分组"""

    def __init__(self, title="Drawing", palette="default", semantic=True):
        self.elements = []
        self.title = title
        self.use_semantic = semantic
        self.palette = PALETTES.get(palette, PALETTES["default"])
        self._color_idx = 0
        self._bounds = {"x": 0, "y": 0, "w": 1200, "h": 800}
        self._group_counter = 0
        self._current_group = []

    def _next_color(self):
        colors = self.palette["bg"]
        c = colors[self._color_idx % len(colors)]
        self._color_idx += 1
        return c

    def _semantic_color(self, semantic):
        """获取语义化颜色"""
        if semantic in SEMANTIC_COLORS:
            return SEMANTIC_COLORS[semantic]
        return {"fill": self._next_color(), "stroke": self.palette["line"]}

    # ── 核心绘制方法 ──

    def add_rect(self, x, y, w, h, label="", fill=None, semantic=None, **kw):
        """添加矩形
        Args:
            semantic: 语义角色 (primary|secondary|start|end|warning|decision|ai|inactive|error|data|external|highlight)
                      设置后自动填充对应语义颜色
        """
        if semantic and self.use_semantic:
            sc = self._semantic_color(semantic)
            fill = fill or sc["fill"]
            if "stroke" not in kw:
                kw["stroke"] = sc["stroke"]
        if fill is None:
            fill = self._next_color()
        el = Rect(x, y, w, h, "", backgroundColor=fill,
                  strokeColor=kw.pop("stroke", self.palette["line"]), **kw)
        self.elements.append(el)
        if self._current_group:
            el.groupIds = list(self._current_group)
        if label:
            self._add_bound_text(el, label, x, y, w, h, kw.pop("font_size", 20))
        return el
    def _add_bound_text(self, container, text, x, y, w, h, font_size=20):
        """为容器创建绑定文本元素（Obsidian Excalidraw 渲染容器内文字的方式）"""
        # Eagerly generate IDs so boundElement references are valid
        if not container.id:
            container.id = _make_id(container.type or "container")
        text_el = Text(x, y, text, font_size=font_size, w=w, h=h,
                       textAlign="center", verticalAlign="middle")
        if not text_el.id:
            text_el.id = _make_id("text")
        text_el.containerId = container.id
        container.boundElements = container.boundElements or []
        container.boundElements.append({"type": "text", "id": text_el.id})
        self.elements.append(text_el)
        if self._current_group:
            text_el.groupIds = list(self._current_group)
        return text_el

    def add_text(self, x, y, text, font_size=20, **kw):
        """添加独立文字（Free-Floating Text）"""
        el = Text(x, y, text, font_size, **kw)
        self.elements.append(el)
        if self._current_group:
            el.groupIds = list(self._current_group)
        return el

    def add_ellipse(self, x, y, w, h, label="", fill=None, semantic=None, **kw):
        """添加椭圆（常用于入口/出口/外部系统）"""
        if semantic and self.use_semantic:
            sc = self._semantic_color(semantic)
            fill = fill or sc["fill"]
            if "stroke" not in kw:
                kw["stroke"] = sc["stroke"]
        if fill is None:
            fill = self._next_color()
        el = Ellipse(x, y, w, h, "", backgroundColor=fill,
                     strokeColor=kw.pop("stroke", self.palette["line"]), **kw)
        self.elements.append(el)
        if self._current_group:
            el.groupIds = list(self._current_group)
        if label:
            self._add_bound_text(el, label, x, y, w, h, kw.pop("font_size", 20))
        return el

    def add_diamond(self, x, y, w, h, label="", fill=None, semantic=None, **kw):
        """添加菱形（常用于决策点）"""
        if semantic and self.use_semantic:
            sc = self._semantic_color(semantic)
            fill = fill or sc["fill"]
            if "stroke" not in kw:
                kw["stroke"] = sc["stroke"]
        if fill is None:
            fill = self._next_color()
        el = Diamond(x, y, w, h, "", backgroundColor=fill,
                     strokeColor=kw.pop("stroke", self.palette["line"]), **kw)
        self.elements.append(el)
        if self._current_group:
            el.groupIds = list(self._current_group)
        if label:
            self._add_bound_text(el, label, x, y, w, h, kw.pop("font_size", 20))
        return el

    def add_arrow(self, x1, y1, x2, y2, label="", semantic="neutral", **kw):
        """添加箭头（语义化箭头颜色）"""
        if "strokeColor" not in kw and semantic in ARROW_COLORS:
            kw["strokeColor"] = ARROW_COLORS[semantic]
        el = Arrow(x1, y1, x2, y2, label, **kw)
        self.elements.append(el)
        if self._current_group:
            el.groupIds = list(self._current_group)
        return el

    def add_line(self, points, **kw):
        """添加折线"""
        el = Line(points, **kw)
        self.elements.append(el)
        if self._current_group:
            el.groupIds = list(self._current_group)
        return el

    def add_frame(self, x, y, w, h, name="", **kw):
        """添加 Frame（段落分组框）"""
        el = Frame(x, y, w, h, name, **kw)
        self.elements.append(el)
        return el

    def connect(self, el1, el2, label="", semantic="neutral", **kw):
        """在两个元素之间画箭头（自动计算边缘位置 + 绑定元素）

        箭头会绑定到元素边缘，移动元素时箭头自动跟随。
        每个箭头在源/目标元素的 boundElements 中注册。
        """
        # 1. 确保元素有 ID（binding 需要引用）
        if not el1.id:
            el1.id = _make_id(el1.type)
        if not el2.id:
            el2.id = _make_id(el2.type)

        # 2. 生成箭头 ID（先创建，binding 中用）
        arrow_id = _make_id("arrow")

        # 3. 计算边缘交点
        #    先以目标元素中心为瞄准点计算源元素边缘出射点
        cx2 = el2.x + el2.width / 2
        cy2 = el2.y + el2.height / 2
        x1, y1, focus1 = _edge_intersection(el1, cx2, cy2)
        #    再以源元素边缘出射点计算目标元素边缘入射点
        x2, y2, focus2 = _edge_intersection(el2, x1, y1)

        # 4. 语义化箭头颜色
        if 'stroke' in kw:
            kw['strokeColor'] = kw.pop('stroke')
        if "strokeColor" not in kw and semantic in ARROW_COLORS:
            kw["strokeColor"] = ARROW_COLORS[semantic]

        # 5. 创建箭头（直接带 binding 信息）
        gap = 3
        el = Arrow(x1, y1, x2, y2, label,
                   startBinding={"elementId": el1.id, "focus": round(focus1, 4), "gap": gap},
                   endBinding={"elementId": el2.id, "focus": round(focus2, 4), "gap": gap},
                   **kw)
        el.id = arrow_id

        # 6. 在源/目标元素的 boundElements 中注册此箭头
        binding_entry = {"id": arrow_id, "type": "arrow"}
        if el1.boundElements is None:
            el1.boundElements = []
        if binding_entry not in el1.boundElements:
            el1.boundElements.append(binding_entry)

        if el2.boundElements is None:
            el2.boundElements = []
        if binding_entry not in el2.boundElements:
            el2.boundElements.append(binding_entry)

        # 7. 加入画布
        self.elements.append(el)
        if self._current_group:
            el.groupIds = list(self._current_group)
        return el

    # ── 分组支持 ──

    def begin_group(self, group_id=None):
        """开始一个组，后续添加的元素自动归入该组"""
        if group_id is None:
            self._group_counter += 1
            group_id = f"group-{self._group_counter}-{random.randint(1000,9999)}"
        self._current_group.append(group_id)
        return group_id

    def end_group(self):
        """结束当前组"""
        if self._current_group:
            return self._current_group.pop()
        return None

    # ── 概念 → 视觉模式 ──

    def pattern_fan_out(self, cx, cy, items, radius=150, box_w=120, box_h=50, semantic=None):
        """扇出模式：中心向外辐射
        items = [(label, sub_labels), ...]
        """
        center = self.add_ellipse(cx-40, cy-25, 80, 50, items[0][0] if items else "",
                                  semantic=semantic or "primary", fontSize=16)
        n = len(items)
        created = [center]
        for i, (label, _) in enumerate(items[1:], 1):
            angle = 2 * math.pi * (i-1) / (n-1) - math.pi/2
            bx = cx + radius * math.cos(angle) - box_w/2
            by = cy + radius * math.sin(angle) - box_h/2
            el = self.add_rect(bx, by, box_w, box_h, label,
                               semantic=semantic or "secondary", fontSize=14)
            self.connect(center, el, semantic="neutral")
            created.append(el)
        return created

    def pattern_convergence(self, items, target_label, cx=400, cy=300, radius=180):
        """汇聚模式：多个源指向同一目标"""
        target = self.add_rect(cx-60, cy-30, 120, 60, target_label,
                               semantic="primary", fontSize=18)
        n = len(items)
        created = [target]
        for i, label in enumerate(items):
            angle = 2 * math.pi * i / n - math.pi/2
            sx = cx + radius * math.cos(angle) - 60
            sy = cy + radius * math.sin(angle) - 25
            el = self.add_rect(sx, sy, 120, 50, label, semantic="secondary", fontSize=14)
            self.connect(el, target, semantic="neutral")
            created.append(el)
        return created

    def pattern_timeline(self, events, start_x=100, start_y=200, step_x=180):
        """时间线模式：水平排列带主干线
        events = [(label, detail), ...]
        """
        # 主干线
        line_len = len(events) * step_x
        self.add_line([[start_x, start_y], [start_x + line_len, start_y]],
                       strokeColor="#64748b", strokeWidth=2)
        created = []
        for i, (label, detail) in enumerate(events):
            x = start_x + i * step_x
            # 时间节点
            node = self.add_ellipse(x-15, start_y-15, 30, 30, "",
                                     semantic="primary", fontSize=10)
            # 上方标签
            self.add_text(x-60, start_y-80, label, font_size=14, textAlign="center", w=120)
            # 下方细节
            if detail:
                self.add_text(x-60, start_y+30, detail, font_size=11, textAlign="center",
                              w=120, strokeColor="#6b7280")
            created.append(node)
        return created

    def pattern_side_by_side(self, groups, start_x=50, start_y=50, gap=30, box_w=160, box_h=50):
        """并排对比模式：多列并排排列
        groups = [(column_title, [item_labels...]), ...]
        """
        created = []
        for i, (title, items) in enumerate(groups):
            cx = start_x + i * (box_w + gap + 60)
            # 列标题
            self.add_text(cx, start_y, title, font_size=18, fontFamily=3, strokeColor="#1e3a5f")
            col_items = []
            for j, item in enumerate(items):
                iy = start_y + 40 + j * (box_h + 15)
                el = self.add_rect(cx, iy, box_w, box_h, item,
                                   semantic="secondary" if j % 2 == 0 else "primary",
                                   fontSize=13)
                col_items.append(el)
            created.append(col_items)
        return created

    def pattern_gap(self, x, y, w, h=2):
        """间隔/分隔线：视觉段落分隔"""
        return self.add_line([[x, y], [x+w, y]], strokeColor="#cbd5e1", strokeWidth=1,
                             strokeStyle="dashed")

    # ── Evidence Artifacts ──

    def add_code_block(self, x, y, code_text, label="代码示例", box_w=400, box_h=100):
        """代码片段证据（带代码框）"""
        # 代码背景框
        self.add_rect(x, y, box_w, box_h, "", fill="#f8f9fa", stroke="#e2e8f0",
                      fontSize=12, strokeWidth=1, fontFamily=2)
        # 标题
        if label:
            self.add_text(x+10, y-25, label, font_size=14, strokeColor="#64748b")
        # 代码内容
        self.add_text(x+10, y+10, code_text, font_size=11, font_family=2,
                      textAlign="left", strokeColor="#334155", w=box_w-20)
        return None

    def add_json_block(self, x, y, json_data, label="JSON", box_w=420, box_h=120):
        """JSON 数据证据块"""
        text = json.dumps(json_data, indent=2, ensure_ascii=False) if isinstance(json_data, dict) else str(json_data)
        # 限制行数显示
        lines = text.split("\n")[:8]
        display_text = "\n".join(lines)
        if len(lines) < len(text.split("\n")):
            display_text += "\n..."
        return self.add_code_block(x, y, display_text, label=label, box_w=box_w, box_h=box_h)

    def add_event_sequence(self, x, y, events, box_w=500):
        """事件序列证据
        events = [(actor, action, detail), ...]
        """
        y_offset = y
        created = []
        for i, (actor, action, detail) in enumerate(events):
            # 角色
            a = self.add_ellipse(x, y_offset, 60, 30, actor, semantic="primary", fontSize=11)
            # 动作
            arrow = self.add_arrow(x+70, y_offset+15, x+150, y_offset+15,
                                    action, semantic="neutral", fontSize=10)
            # 详情
            d = self.add_rect(x+160, y_offset-5, box_w-180, 40, detail,
                              semantic="secondary", fontSize=11)
            y_offset += 55
            created.extend([a, arrow, d])
        return created

    # ── 快速图型模板 ──

    def quick_flowchart(self, nodes, title=None):
        """快速流程图: nodes = [(label, type), ...]  type='proc'|'dec'|'start'|'end'
           自动纵向排列并连线，使用语义配色
        """
        if title:
            self.add_text(50, 20, title, font_size=28).strokeColor = "#333"

        start_x, start_y = 100, 80
        box_w, box_h = 180, 60
        gap = 40
        prev = None

        for i, (label, nt) in enumerate(nodes):
            y = start_y + i * (box_h + gap)

            if nt == "dec":
                el = self.add_diamond(start_x + box_w//2, y, box_w, box_h, label,
                                       semantic="decision")
            elif nt in ("start",):
                el = self.add_ellipse(start_x + box_w//4, y, box_w, box_h//2 + 20, label,
                                       semantic="start")
            elif nt == "end":
                el = self.add_ellipse(start_x + box_w//4, y, box_w, box_h//2 + 20, label,
                                       semantic="end")
            else:
                el = self.add_rect(start_x, y, box_w, box_h, label, semantic="primary")

            if prev:
                self.connect(prev, el, semantic="neutral")
            prev = el

        return prev

    def quick_mindmap(self, center, branches, center_x=400, center_y=300):
        """快速思维导图: center=中心词, branches=[(子词, 子分支), ...]"""
        center_el = self.add_ellipse(center_x-60, center_y-30, 120, 60, center,
                                      semantic="primary", fontSize=24, fontFamily=3)

        n = len(branches)
        radius = 180
        for i, (word, sub_words) in enumerate(branches):
            angle = 2 * math.pi * i / n - math.pi/2
            bx = center_x + radius * math.cos(angle) - 70
            by = center_y + radius * math.sin(angle) - 25

            branch_el = self.add_rect(bx, by, 140, 50, word,
                                       semantic="secondary", fontSize=16)
            self.connect(center_el, branch_el, semantic="neutral")

            if sub_words:
                for j, sw in enumerate(sub_words):
                    sx = bx + 160
                    sy = by + j * 35
                    if len(sw) < 15:
                        self.add_text(sx, sy, sw, font_size=14)
                    else:
                        self.add_rect(sx, sy-10, max(len(sw)*8, 100), 30, sw,
                                      fill="#f8f9fa", fontSize=12)

    # ── 保存 ──

    def _make_app_state(self):
        return {
            "gridSize": None,
            "viewBackgroundColor": "#ffffff",
            "currentItemStrokeColor": self.palette["line"],
        }

    def save(self, vault_path):
        """保存到 .excalidraw.md 文件（Obsidian Excalidraw 原生 Markdown 格式）
        相对 vault 路径或绝对路径均可
        """
        full_path = vault_path
        vault = r"D:\Documents_Learn\Personal\Obsidian\Codex Vitae"
        if not os.path.isabs(full_path) and not full_path.startswith(vault):
            full_path = os.path.join(vault, full_path)

        # 确保扩展名正确
        if not full_path.endswith(".excalidraw.md"):
            full_path = full_path.replace(".excalidraw", "") if ".excalidraw" in full_path else full_path
            if not full_path.endswith(".md"):
                full_path += ".excalidraw.md"

        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        drawing_data = {
            "type": "excalidraw",
            "version": 2,
            "source": "https://excalidraw.com",
            "elements": [el.to_dict() for el in self.elements],
            "appState": self._make_app_state(),
            "files": {}
        }

        drawing_json = json.dumps(drawing_data, indent=2, ensure_ascii=False)

        # 收集文本元素用于 # Text Elements 节
        text_lines = []
        for el in self.elements:
            if hasattr(el, 'text') and el.text and el.text.strip():
                txt = el.text.strip()
                if len(txt) > 60:
                    txt = txt[:57] + "..."
                text_lines.append(f"- {txt}")

        md_content = "---\n"
        md_content += "excalidraw-plugin: parsed\n"
        md_content += "---\n\n"
        md_content += "==⚠  Switch to EXCALIDRAW VIEW in the MORE OPTIONS menu of this document. ⚠==\n\n"
        md_content += "本文件由 GenericAgent 自动生成。\n\n"

        if text_lines:
            md_content += "# Text Elements\n"
            md_content += "\n".join(text_lines) + "\n\n"

        md_content += "## Drawing\n"
        md_content += f"```json\n{drawing_json}\n```\n\n"
        md_content += "%%\n"

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        return full_path


# ─── 便捷入口 ──────────────────────────────────────

def demo():
    """生成示例图用于测试"""
    c = Canvas("示例流程图", semantic=True)
    c.quick_flowchart([
        ("开始", "start"),
        ("分析需求", "proc"),
        ("是否可行？", "dec"),
        ("设计方案", "proc"),
        ("结束", "end"),
    ])
    return c

def demo_semantic():
    """语义化配色示例"""
    c = Canvas("语义配色示例", semantic=True)
    y = 50
    for name, sc in SEMANTIC_COLORS.items():
        c.add_rect(50, y, 160, 35, f"{name}({sc['desc']})",
                    fill=sc["fill"], stroke=sc["stroke"], fontSize=12)
        y += 45
    return c

def demo_patterns():
    """视觉模式示例"""
    c = Canvas("视觉模式示例", semantic=True)
    c.pattern_fan_out(300, 200, [
        ("中心", []),
        ("分支A", []), ("分支B", []), ("分支C", []), ("分支D", []),
    ])
    c.pattern_timeline([
        ("Phase 1", "需求"), ("Phase 2", "设计"),
        ("Phase 3", "开发"), ("Phase 4", "测试"),
    ], start_x=50, start_y=400)
    return c
