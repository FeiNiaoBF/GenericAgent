import json
import os
import random

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DEFAULT_PHRASE_PATH = os.path.join(_PROJECT_ROOT, "assets", "chii_phrases.json")
_FALLBACK_POOL = {
    "thinking": ["处理中... 请稍等，なの"],
    "empty": ["...没有可显示内容"],
    "file": ["文件准备好了，なの"],
    "error": ["处理失败了，抱歉"],
    "wake": ["唧、ちぃ起来了！✨"],
    "sleep": ["ちぃ、おやすみなさい 💤"],
    "stopping": ["⏹️ 正在停止，稍等一下"],
    "stop": ["⏹️ 已停止"],
    "status_running": ["🔴 正在运行中"],
    "status_idle": ["🟢 当前空闲"],
}
_POOL_CACHE = {}


def _normalize_pool(pool):
    normalized = {}
    if not isinstance(pool, dict):
        return dict(_FALLBACK_POOL)

    for key, values in pool.items():
        if isinstance(values, str):
            items = [values.strip()] if values.strip() else []
        elif isinstance(values, (list, tuple)):
            items = [str(item).strip() for item in values if str(item).strip()]
        else:
            items = []
        if items:
            normalized[str(key)] = items

    merged = dict(_FALLBACK_POOL)
    merged.update(normalized)
    if "think" in merged and "thinking" not in merged:
        merged["thinking"] = list(merged["think"])
    if "thinking" in merged and "think" not in merged:
        merged["think"] = list(merged["thinking"])
    return merged



def load_phrase_pool(file_path=None):
    path = file_path or _DEFAULT_PHRASE_PATH
    if path in _POOL_CACHE:
        return _POOL_CACHE[path]
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        pool = _normalize_pool(data)
    except Exception as exc:
        print(f"[persona_pool] load error: {exc}", flush=True)
        pool = dict(_FALLBACK_POOL)
    _POOL_CACHE[path] = pool
    return pool


def reload_phrase_pool(file_path=None):
    path = file_path or _DEFAULT_PHRASE_PATH
    _POOL_CACHE.pop(path, None)
    return load_phrase_pool(file_path=path)


def get_phrase(key, default="...", file_path=None, pool=None):
    phrase_pool = pool if pool is not None else load_phrase_pool(file_path=file_path)
    values = phrase_pool.get(key) or []
    if not values:
        return default
    return random.choice(values)
