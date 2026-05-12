#!/usr/bin/env python3
"""UI设计工具：帮助生成/管理UI设计文件（Excalidraw等）"""
import subprocess, json
from pathlib import Path

EXCALIDRAW_DIR = Path(__file__).parent / '..' / 'excalidraw'

def open_excalidraw():
    """启动Excalidraw编辑"""
    # 使用excalidraw_draw工具
    from excalidraw_draw_sop import launch_editor
    launch_editor()

def create_design_template(name: str, elements: list) -> Path:
    """创建Excalidraw设计模板"""
    EXCALIDRAW_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "type": "excalidraw",
        "elements": elements,
        "name": name
    }
    path = EXCALIDRAW_DIR / f"{name}.excalidraw"
    path.write_text(json.dumps(data, indent=2), encoding='utf-8')
    return path

def list_designs() -> list:
    """列出所有UI设计文件"""
    if not EXCALIDRAW_DIR.exists():
        return []
    return [f.stem for f in EXCALIDRAW_DIR.glob("*.excalidraw")]
