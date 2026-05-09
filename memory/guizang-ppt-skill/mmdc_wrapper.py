#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
"""
mmdc_wrapper.py — Mermaid图表渲染器 for Guizang PPT
用途: 将Mermaid代码转为SVG，可直接嵌入PPT HTML模板
依赖: mmdc (npm global: @mermaid-js/mermaid-cli >= 11.x)
系统Chrome路径已在 %LOCALAPPDATA%/mermaid/puppeteer-config.json

用法:
  from mmdc_wrapper import mermaid_to_svg
  svg = mermaid_to_svg("graph TD\n  A-->B", type="flowchart")
  # 直接嵌入 <section class="slide ..."> ... {{svg}} ... </section>
"""

import subprocess
import os
import tempfile
import re
import json

PUPPETEER_CONFIG = os.path.expandvars(r"%LOCALAPPDATA%\mermaid\puppeteer-config.json")

SUPPORTED_TYPES = {
    "flowchart": "graph TD",
    "sequence": "sequenceDiagram",
    "class": "classDiagram",
    "state": "stateDiagram-v2",
    "er": "erDiagram",
    "gantt": "gantt",
    "pie": "pie",
    "git": "gitGraph",
    "mindmap": "mindmap",
    "timeline": "timeline",
}


def _ensure_puppeteer_config():
    """确保puppeteer config存在，否则自动创建"""
    if os.path.exists(PUPPETEER_CONFIG):
        return True
    # Auto-detect Chrome
    chrome_candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]
    for chrome in chrome_candidates:
        if os.path.exists(chrome):
            os.makedirs(os.path.dirname(PUPPETEER_CONFIG), exist_ok=True)
            cfg = {
                "args": ["--no-sandbox", "--disable-setuid-sandbox"],
                "executablePath": chrome,
                "headless": "new"
            }
            with open(PUPPETEER_CONFIG, 'w') as f:
                json.dump(cfg, f, indent=2)
            return True
    return False


GRAPH_VARIANTS = ("graph TD", "graph LR", "graph RL", "graph BT", "graph TB",
                  "flowchart TD", "flowchart LR", "flowchart RL", "flowchart BT", "flowchart TB")

def _validate_mermaid(code: str, diagram_type: str = None) -> str:
    """验证并规范化Mermaid代码"""
    code = code.strip()
    if not code:
        raise ValueError("Mermaid code cannot be empty")

    if diagram_type and diagram_type in SUPPORTED_TYPES:
        prefix = SUPPORTED_TYPES[diagram_type]
        # Check if code already starts with any known Mermaid directive
        all_prefixes = list(SUPPORTED_TYPES.values()) + list(GRAPH_VARIANTS)
        if not any(code.startswith(p) for p in all_prefixes):
            code = f"{prefix}\n{code}"

    return code


def _clean_svg(svg: str) -> str:
    """清理SVG使其适合HTML内嵌"""
    # 移除XML声明
    svg = re.sub(r'<\?xml[^>]*\?>', '', svg)
    # 移除DOCTYPE
    svg = re.sub(r'<!DOCTYPE[^>]*>', '', svg)
    # 移除外层注释
    svg = re.sub(r'<!--.*?-->', '', svg, flags=re.DOTALL)
    return svg.strip()


def mermaid_to_svg(code: str, diagram_type: str = None,
                   width: int = None, height: int = None,
                   theme: str = "default",
                   bg_color: str = "transparent",
                   scale: int = 2) -> dict:
    """
    将Mermaid代码转为SVG

    Args:
        code: Mermaid代码字符串
        diagram_type: 图表类型 (flowchart|sequence|class|state|er|gantt|pie|git|mindmap|timeline)
        width: 宽度(px), None=自适应
        height: 高度(px), None=自适应
        theme: 主题 (default|forest|dark|neutral)
        bg_color: 背景色 (transparent|white|#HEX)
        scale: 渲染缩放比例 (1-4, 越大越清晰)

    Returns:
        dict: {"svg": "<svg>...</svg>", "width": int, "height": int, "type": str, "ok": bool, "error": str}
    """
    if not _ensure_puppeteer_config():
        raise RuntimeError(
            "找不到Chrome浏览器。请安装Chrome或手动创建 "
            f"{PUPPETEER_CONFIG} 指定executablePath"
        )

    code = _validate_mermaid(code, diagram_type)

    # 写入临时文件
    tmp_mmd = tempfile.NamedTemporaryFile(
        mode='w', suffix='.mmd', delete=False, encoding='utf-8'
    )
    tmp_svg = tempfile.NamedTemporaryFile(
        mode='w', suffix='.svg', delete=False, encoding='utf-8'
    )
    tmp_mmd.write(code)
    tmp_mmd.close()
    tmp_svg.close()

    try:
        cmd = [
            "mmdc",
            "-i", tmp_mmd.name,
            "-o", tmp_svg.name,
            "-p", PUPPETEER_CONFIG,
            "-t", theme,
            "-b", bg_color,
            "-s", str(scale),
        ]
        if width:
            cmd.extend(["-w", str(width)])
        if height:
            cmd.extend(["-H", str(height)])

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30, shell=True
        )

        if result.returncode != 0:
            return {
                "svg": "",
                "ok": False,
                "error": result.stderr.strip() or "mmdc failed with no output",
                "type": diagram_type or "unknown",
                "width": 0, "height": 0,
            }

        with open(tmp_svg.name, 'r', encoding='utf-8') as f:
            svg_raw = f.read()

        svg_clean = _clean_svg(svg_raw)

        # 提取viewBox尺寸
        vb_match = re.search(r'viewBox="([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)"', svg_clean)
        if vb_match:
            w, h = int(float(vb_match.group(3))), int(float(vb_match.group(4)))
        else:
            w, h = width or 800, height or 600

        return {
            "svg": svg_clean,
            "ok": True,
            "error": "",
            "type": diagram_type or "auto",
            "width": w,
            "height": h,
        }

    except subprocess.TimeoutExpired:
        return {"svg": "", "ok": False, "error": "mmdc timed out (30s)", "type": diagram_type or "unknown", "width": 0, "height": 0}
    except FileNotFoundError:
        raise RuntimeError(
            "mmdc 未安装。请运行: npm install -g @mermaid-js/mermaid-cli"
        )
    finally:
        for f in [tmp_mmd.name, tmp_svg.name]:
            try:
                os.unlink(f)
            except OSError:
                pass


def mermaid_to_html_component(code: str, diagram_type: str = None,
                              max_height_vh: int = 60,
                              theme: str = "default",
                              caption: str = "") -> str:
    """
    一站式: Mermaid代码 → HTML组件(可直接嵌入 <section>)

    Returns:
        HTML片段字符串，可粘贴到 guizang-ppt 模板的 <section> 中
    """
    result = mermaid_to_svg(code, diagram_type=diagram_type, theme=theme)

    if not result["ok"]:
        return f'<div class="img-placeholder"><i class="lucide-alert-triangle"></i><br/>Mermaid渲染失败: {result["error"]}</div>'

    svg = result["svg"]
    # 使用max-height限制但不拉伸
    style = f'max-height:{max_height_vh}vh;width:auto;object-fit:contain'

    html = f'<div class="mermaid-diagram mt-1">\n'
    if caption:
        html += f'  <div class="kicker mb-1">{caption}</div>\n'
    html += f'  <div style="{style}">\n{svg}\n  </div>\n'
    html += f'</div>'

    return html


# ===== CLI =====
if __name__ == "__main__":
    import sys
    print("mmdc_wrapper self-test")
    print("=" * 40)

    tests = [
        ("flowchart", "graph TD\n    A[Start] --> B{Decision}\n    B -->|Yes| C[OK]\n    B -->|No| D[Fail]"),
        ("sequence", "sequenceDiagram\n    Alice->>Bob: Hello\n    Bob-->>Alice: Hi"),
        ("class", "classDiagram\n    Animal <|-- Duck\n    Animal : +String name\n    Duck : +quack()"),
    ]

    for dtype, code in tests:
        r = mermaid_to_svg(code, diagram_type=dtype)
        status = "OK" if r["ok"] else "FAIL"
        print(f"  {status} {dtype}: {r['width']}x{r['height']}px | SVG: {len(r['svg'])}B")
        if not r["ok"]:
            print(f"       Error: {r['error']}")

    # Test HTML component
    html = mermaid_to_html_component(
        "graph LR\n    A-->B-->C",
        diagram_type="flowchart",
        caption="Simple Pipeline",
        max_height_vh=30
    )
    print(f"\n  HTML component generated: {len(html)}B")
    print(f"  Preview: {html[:150]}...")
    print("\nSelf-test complete")