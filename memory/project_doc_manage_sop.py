#!/usr/bin/env python3
"""项目文档管理助手：阅读/创建/更新项目文档"""
from pathlib import Path

try:
    import paths  # ga常用路径
    DOCS_DIR = Path(paths.DOCS)
except Exception:
    DOCS_DIR = Path(__file__).resolve().parents[1] / 'docs'

def read_doc(doc_name: str) -> str:
    """读取项目文档"""
    doc_path = DOCS_DIR / doc_name
    if not doc_path.exists():
        return f"❌ 文档不存在: {doc_name}"
    return doc_path.read_text(encoding='utf-8')

def create_doc(doc_name: str, content: str) -> bool:
    """创建新项目文档"""
    doc_path = DOCS_DIR / doc_name
    if doc_path.exists():
        return False
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.write_text(content, encoding='utf-8')
    return True

def update_doc(doc_name: str, new_content: str) -> bool:
    """更新已有项目文档"""
    doc_path = DOCS_DIR / doc_name
    if not doc_path.exists():
        return False
    doc_path.write_text(new_content, encoding='utf-8')
    return True
