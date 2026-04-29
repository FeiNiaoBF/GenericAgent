"""
autonomous_task.py - 自主行动任务管理API (v2)
放置: memory/autonomous_operation_sop/
用法: from autonomous_operation_sop.helper import *

5个函数 + 1个模块变量:
  get_todo()        → 返回TODO内容
  get_history(n)    → 返回最近n条历史
  complete_task()   → 移报告+编号+写history+auto-mark TODO
  set_todo(keyword) → 将匹配TODO项标记为[x]（真改写文件）
  validate_l1()     → 扫描L1索引，验证所有指针有效性
  _done_hooks       → 模块级列表，agent可在收尾时append校验指令后手动执行
"""

import os
import re
import shutil
from pathlib import Path
from datetime import datetime

# 显式导出（含 _done_hooks），确保 from helper import * 可用
__all__ = ['get_todo', 'get_history', 'complete_task', 'set_todo', 'validate_l1', '_done_hooks']

# ── 路径计算（基于模块自身位置） ──
_MODULE_DIR = Path(__file__).resolve().parent          # memory/autonomous_operation_sop/
_MEMORY_DIR = _MODULE_DIR.parent                       # memory/
_AGENT_DIR = _MEMORY_DIR.parent                        # GenericAgent/
_TEMP_DIR = _AGENT_DIR / "temp"                        # GenericAgent/temp/
_REPORTS_DIR = _TEMP_DIR / "autonomous_reports"
_HISTORY_FILE = _REPORTS_DIR / "history.txt"
_TODO_FILE = _TEMP_DIR / "TODO.txt"
_L1_FILE = _MEMORY_DIR / "global_mem_insight.txt"

# ── 模块级 _done_hooks：agent 自主追加收尾校验指令 ──
_done_hooks = []  # agent: helper._done_hooks.append("指令描述"); 收尾时手动 for h in helper._done_hooks: execute(h)

def _next_report_number() -> int:
    """扫 history.txt 提取最大 RXX 编号，返回下一个"""
    if not _HISTORY_FILE.exists():
        return 1
    with open(_HISTORY_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    nums = [int(m) for m in re.findall(r'R(\d+)', content)]
    return max(nums) + 1 if nums else 1


def get_todo() -> str:
    """返回 TODO.txt 的完整内容。若文件不存在返回提示。"""
    if not _TODO_FILE.exists():
        return f"[helper] TODO.txt 不存在，路径: {_TODO_FILE}"
    with open(_TODO_FILE, "r", encoding="utf-8") as f:
        return f.read()


def get_history(n: int = 20) -> str:
    """返回 history.txt 的前 n 行（最新在前）"""
    if not _HISTORY_FILE.exists():
        return f"[helper] history.txt 不存在，路径: {_HISTORY_FILE}"
    with open(_HISTORY_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return "".join(lines[:n])


def set_todo(keyword: str = "") -> str:
    """
    将 TODO.txt 中第一个含 keyword 的未完成条目标记为 [x]。
    
    Args:
        keyword: 匹配关键词（大小写不敏感）。为空则仅返回路径。
    Returns:
        操作结果描述
    """
    if not keyword:
        return f'路径: {str(_TODO_FILE)} (使用 set_todo("关键词") 标记完成)'
    
    if not _TODO_FILE.exists():
        return f"[ERROR] TODO.txt 不存在: {_TODO_FILE}"
    
    with open(_TODO_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    kw_lower = keyword.lower()
    for i, line in enumerate(lines):
        if kw_lower in line.lower() and line.strip().startswith('- [ ]'):
            old_line = lines[i]
            lines[i] = line.replace('- [ ]', '- [x]', 1)
            with open(_TODO_FILE, "w", encoding="utf-8") as f:
                f.writelines(lines)
            return f"✅ 已标记完成: {old_line.strip()} → {lines[i].strip()}"
    
    # 未找到未完成项，检查是否已经 [x]
    for i, line in enumerate(lines):
        if kw_lower in line.lower() and line.strip().startswith('- [x]'):
            return f"⚠️ 该任务已标记完成: {line.strip()}"
    
    return f"⚠️ 未找到含 '{keyword}' 的待办项"


def complete_task(taskname: str, historyline: str, report_path: str) -> str:
    """
    完成任务原子收尾：移动报告 + 写历史 + 自动标记 TODO。
    
    Args:
        taskname:   任务简短名称（用于报告文件名）
        historyline: 历史单行（格式: "类型 | 主题 | 结论"）
        report_path: agent已写好的报告路径
    Returns:
        成功/失败消息
    """
    errors = []

    # ── 校验 ──
    if "\n" in historyline.strip():
        return "[ERROR] historyline 必须是单行，不能包含换行符"

    report = Path(report_path).resolve()
    if not report.exists():
        return f"[ERROR] 报告文件不存在: {report_path}"

    if not _REPORTS_DIR.exists():
        _REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # ── 1. 移动报告 ──
    rnum = _next_report_number()
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', taskname).strip()
    dest_name = f"R{rnum}_{safe_name}.md"
    dest_path = _REPORTS_DIR / dest_name

    try:
        shutil.move(str(report), str(dest_path))
    except Exception as e:
        return f"[ERROR] 移动报告失败: {e}"

    # ── 2. prepend history ──
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
        # 回滚
        try:
            shutil.move(str(dest_path), str(report))
        except:
            pass
        return f"[ERROR] 写入 history 失败: {e}（报告已回滚）"

    # ── 3. 自动标记 TODO ──
    todo_result = set_todo(taskname)

    return (
        f"✅ 完成！报告: {dest_name}\n"
        f"📝 历史: {line}\n"
        f"📋 TODO: {todo_result}"
    )


# ── Fix #3: L1 指针有效性验证 ──
def validate_l1() -> str:
    """
    扫描 L1 (global_mem_insight.txt)，验证所有引用指针有效性。
    Returns: 验证报告（含失效指针列表）
    """
    if not _L1_FILE.exists():
        return f"[ERROR] L1 文件不存在: {_L1_FILE}"

    with open(_L1_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # 提取所有 | 分隔的指针 token（如 obsidian_blog_sync、tmwebdriver_sop）
    # 格式: key:value|key:value 或 word|word
    tokens = re.findall(r'[\w_]+_sop|[\w_]+\.py|[\w_]+\.md|[\w_]+_library|[\w_]+_sync|[\w_]+_draw|[\w_]+_sop\.md', content)
    # 更通用的提取：所有看起来像文件/模块引用的 token
    # 匹配模式: xxx_sop, xxx.py, xxx.md, xxx_library, xxx_sync, xxx_draw, xxx_map 等
    pointer_patterns = re.findall(
        r'\b([a-z_]+_(?:sop|py|md|sync|draw|map|library|cleanup|ctrl|format))(?:\b|\|)',
        content
    )

    _MEMORY = _MEMORY_DIR  # alias for closure
    results = []
    for token in set(pointer_patterns):
        # 构建可能的文件路径
        candidates = [
            (_MEMORY / f"{token}.md"),
            (_MEMORY / f"{token}.py"),
            (_MEMORY / f"{token}"),
            (_MEMORY / f"{token.replace('_sop', '')}_sop.md"),
        ]
        found = any(c.exists() for c in candidates)
        status = "✅" if found else "❌ 失效"
        results.append(f"  {status} {token}")

    # 额外检查 common knowledge pointers
    extra_checks = {
        'memory_management': _MEMORY / 'memory_management_sop.md',
        'autonomous_operation': _MEMORY / 'autonomous_operation_sop.md',
        'plan_sop': _MEMORY / 'plan_sop.md',
        'verify_sop': _MEMORY / 'verify_sop.md',
        'web_setup_sop': _MEMORY / 'web_setup_sop.md',
    }
    for name, path in extra_checks.items():
        if name not in ''.join(results):
            if path.exists():
                results.append(f"  ✅ {name} (额外)")

    header = f"L1 验证: {_L1_FILE}\n行数: {len(content.splitlines())}\n"
    return header + "\n".join(sorted(results))


# ── 快速自检 ──
if __name__ == "__main__":
    print(f"TEMP_DIR:    {_TEMP_DIR}")
    print(f"REPORTS_DIR: {_REPORTS_DIR}")
    print(f"HISTORY:     {_HISTORY_FILE}")
    print(f"TODO:        {_TODO_FILE}")
    print(f"L1:          {_L1_FILE}")
    print(f"Next R#:     R{_next_report_number()}")
    print(f"\n--- TODO ---\n{get_todo()[:300]}")
    print(f"\n--- History (5) ---\n{get_history(5)}")
    print(f"\n--- L1 Validate ---\n{validate_l1()}")