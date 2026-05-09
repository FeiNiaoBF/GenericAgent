# -*- coding: utf-8 -*-
import sys, io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
"""skill_search — Skill 检索 API 客户端"""
from .engine import (
    SkillIndex, SearchResult, SkillSearchError,
    search, get_stats, detect_environment,
)

__all__ = ["SkillIndex", "SearchResult", "SkillSearchError",
           "search", "get_stats", "detect_environment"]