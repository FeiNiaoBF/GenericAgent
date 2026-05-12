#!/usr/bin/env python3
"""SOP重构工具：优化/合并/拆分SOP文件"""
from pathlib import Path
import re

MEM_DIR = Path(__file__).parent

def read_sop(name: str) -> str:
    """读取SOP"""
    path = MEM_DIR / f"{name}_sop.md"
    if not path.exists():
        return None
    return path.read_text(encoding='utf-8')

def merge_sops(target: str, sources: list) -> str:
    """合并多个SOP到目标文件"""
    merged = []
    for src in sources:
        content = read_sop(src)
        if content:
            merged.append(f"# {src}\n{content}")
    return "\n\n---\n\n".join(merged)

def rename_sop(old_name: str, new_name: str) -> bool:
    """重命名SOP文件"""
    old = MEM_DIR / f"{old_name}_sop.md"
    new = MEM_DIR / f"{new_name}_sop.md"
    if not old.exists() or new.exists():
        return False
    old.rename(new)
    return True
