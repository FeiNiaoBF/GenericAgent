#!/usr/bin/env python3
"""Yeekox博客风格格式化：将笔记转换为博客发布格式"""
import re
from pathlib import Path

def apply_yeekox_style(content: str) -> str:
    """应用Yeekox博客风格"""
    # 标题风格转换
    content = re.sub(r'^# (.*?)$', r'# ✨ ', content, flags=re.MULTILINE)
    # 代码块添加语言标注风
    content = re.sub(r'```(\w*)\n', r'```\1  # 🖥️\n', content)
    # 列表美化
    content = re.sub(r'^- ', '• ', content, flags=re.MULTILINE)
    return content

def format_note_to_blog(note_path: str) -> str:
    """从笔记文件读取并格式化"""
    path = Path(note_path)
    if not path.exists():
        return "❌ 文件不存在"
    content = path.read_text(encoding='utf-8')
    return apply_yeekox_style(content)

def export_blog(note_path: str, output_path: str = None) -> Path:
    """格式化并导出博客"""
    formatted = format_note_to_blog(note_path)
    if output_path is None:
        output_path = str(Path(note_path).stem) + '_blog.md'
    out = Path(output_path)
    out.write_text(formatted, encoding='utf-8')
    return out
