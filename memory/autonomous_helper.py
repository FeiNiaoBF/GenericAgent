# -*- coding: utf-8 -*-
import sys, io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
"""
autonomous_helper.py - 自主行动任务管理API
放置: memory/autonomous_helper.py
用法: from autonomous_helper import * (或 import autonomous_helper)

4个函数:
  get_todo()        → 返回TODO内容
  get_history(n)    → 返回最近n条历史
  complete_task()   → 移报告+编号+写history+返回改TODO指令
  set_todo(content) → 写入TODO内容(content), 无参时返回路径
"""

import os
import re
import shutil
from pathlib import Path
from datetime import datetime

# ── 路径计算（基于模块自身在 memory/ 下） ──
_MODULE_DIR = Path(__file__).resolve().parent          # memory/
_AGENT_DIR = _MODULE_DIR.parent                        # GenericAgent/
_TEMP_DIR = _AGENT_DIR / "temp"                        # GenericAgent/temp/
_REPORTS_DIR = _TEMP_DIR / "autonomous_reports"
_HISTORY_FILE = _REPORTS_DIR / "history.txt"
_TODO_FILE = _TEMP_DIR / "TODO.txt"

def _next_report_number() -> int:
    """扫 history.txt 第一行提取最大 RXX 编号，返回下一个"""
    if not _HISTORY_FILE.exists():
        return 1
    with open(_HISTORY_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    nums = [int(m) for m in re.findall(r'R(\d+)', content)]
    if not nums:
        return 1
    return max(nums) + 1


def get_todo() -> str:
    """返回 TODO.txt 的内容。若文件不存在返回提示。"""
    if not _TODO_FILE.exists():
        return f"[autonomous_helper] TODO.txt 不存在，路径: {_TODO_FILE}"
    with open(_TODO_FILE, "r", encoding="utf-8") as f:
        return f.read()

def get_history(n: int = 20) -> str:
    if not _HISTORY_FILE.exists():
        return f"[autonomous_helper] history.txt 不存在，路径: {_HISTORY_FILE}"
    with open(_HISTORY_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return "".join(lines[:n])


def set_todo(content: str = None) -> str:
    if content is None:
        return f'路径: {str(_TODO_FILE)}'

    _TEMP_DIR.mkdir(parents=True, exist_ok=True)
    with open(_TODO_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    return f'✅ TODO已写入: {_TODO_FILE}'


def complete_task(taskname: str, historyline: str, report_path: str) -> str:
    """
    完成任务的原子操作：
    1. 移动 report_path → autonomous_reports/R{XX}_{taskname}.md（自动编号）
    2. prepend historyline 到 history.txt（校验必须单行）
    3. 返回字符串指示 agent 自己去改 TODO
    Args:
        taskname: 任务简短名称（用于报告文件名，如 "晨间简报"）
        historyline: 历史记录内容（必须单行，日期自动添加，如 "工程 | 晨间简报 | 完成7模块聚合"）
        report_path: agent 已写好的报告文件路径（绝对或相对于cwd）
    Returns:
        成功消息 + 改TODO指令，或错误消息
    """
    errors = []

    if "\n" in historyline.strip():
        return "[ERROR] historyline 必须是单行，不能包含换行符"

    report = Path(report_path).resolve()
    if not report.exists():
        return f"[ERROR] 报告文件不存在: {report_path}"

    if not _REPORTS_DIR.exists():
        _REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    rnum = _next_report_number()
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', taskname).strip()
    dest_name = f"R{rnum}_{safe_name}.md"
    dest_path = _REPORTS_DIR / dest_name

    try:
        shutil.move(str(report), str(dest_path))
    except Exception as e:
        return f"[ERROR] 移动报告失败: {e}"

    line = historyline.strip()
    line = re.sub(r'^R\d+\s*\|\s*', '', line)
    line = re.sub(r'^\d{4}-\d{2}-\d{2}\s*\|\s*', '', line)
    today = datetime.now().strftime('%Y-%m-%d')
    line = f"R{rnum} | {today} | {line}"

    try:
        existing = ""
        if _HISTORY_FILE.exists():
            with open(_HISTORY_FILE, "r", encoding="utf-8") as f:
                existing = f.read()
        with open(_HISTORY_FILE, "w", encoding="utf-8") as f:
            f.write(line + "\n" + existing)
    except Exception as e:
        try:
            shutil.move(str(dest_path), str(report))
        except:
            pass
        return f"[ERROR] 写入 history 失败: {e}（报告已回滚）"

    return (
        f"✅ 完成！报告已保存: {dest_name}\n"
        f"历史已记录: {line}\n"
        f"👉 请在 {_TODO_FILE} 中将对应任务标记为 [x] R{rnum}，然后结束，**其他TODO下次再干**"
    )


# ── 快速自检 ──
if __name__ == "__main__":
    print(f"TEMP_DIR:    {_TEMP_DIR}")
    print(f"REPORTS_DIR: {_REPORTS_DIR}")
    print(f"HISTORY:     {_HISTORY_FILE}")
    print(f"TODO:        {_TODO_FILE}")
    print(f"Next R#:     R{_next_report_number()}")
    print(f"\n--- TODO ---\n{get_todo()[:200]}")
    print(f"\n--- History (5) ---\n{get_history(5)}")