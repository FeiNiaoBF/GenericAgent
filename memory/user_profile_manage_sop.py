#!/usr/bin/env python3
"""用户画像管理：记录/更新用户偏好、习惯、特征"""
from pathlib import Path
import json

PROFILE_PATH = Path(__file__).parent / '..' / 'memory' / 'user_profile.json'

def load_profile() -> dict:
    """加载用户画像"""
    if not PROFILE_PATH.exists():
        return {"preferences": {}, "habits": {}, "traits": {}}
    return json.loads(PROFILE_PATH.read_text(encoding='utf-8'))

def update_preference(key: str, value) -> bool:
    """更新偏好设置"""
    profile = load_profile()
    profile['preferences'][key] = value
    PROFILE_PATH.write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding='utf-8')
    return True

def add_habit(name: str, description: str) -> bool:
    """添加习惯记录"""
    profile = load_profile()
    from datetime import datetime
    habit = {"name": name, "desc": description, "added": datetime.now().isoformat()}
    profile['habits'][name] = habit
    PROFILE_PATH.write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding='utf-8')
    return True

def get_profile_summary() -> str:
    """获取画像摘要"""
    profile = load_profile()
    prefs = profile.get('preferences', {})
    habits = profile.get('habits', {})
    return f"🧑 偏好: {len(prefs)}项 | 习惯: {len(habits)}项"
