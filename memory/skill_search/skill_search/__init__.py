# -*- coding: utf-8 -*-
from _encoding import setup_utf8; setup_utf8()
"""skill_search — Skill 检索 API 客户端"""
from .engine import (
    SkillIndex, SearchResult, SkillSearchError,
    search, get_stats, detect_environment,
)

__all__ = ["SkillIndex", "SearchResult", "SkillSearchError",
           "search", "get_stats", "detect_environment"]