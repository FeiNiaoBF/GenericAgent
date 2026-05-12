#!/usr/bin/env python3
"""项目文档管理助手：阅读/创建/更新项目文档"""
import paths  # ga常用路径
from pathlib import Path

def read_doc(doc_name: str) -> str:
    """读取项目文档"""
    doc_path = paths.DOCS / doc_name
    if not doc_path.exists():
        return f"❌ 文档不存在: {doc_name}"
    return doc_path.read_text(encoding='utf-8')

def create_doc(doc_name: str, content: str) -> bool:
    """创建新项目文档"""
    doc_path = paths.DOCS / doc_name
    if doc_path.exists():
        return False
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.write_text(content, encoding='utf-8')
    return True

def update_doc(doc_name: str, new_content: str) -> bool:
    """更新已有项目文档"""
    doc_path = paths.DOCS / doc_name
    if not doc_path.exists():
        return False
    doc_path.write_text(new_content, encoding='utf-8')
    return True
