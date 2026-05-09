"""`/plan` command: enter plan mode — like CC/Codex plan workflow.

Usage:
    /plan [goal]        — create a plan for the given goal
    /plan               — show plan mode help

Reads memory/plan_sop.md and injects planning context into the agent conversation.
"""
import os, time

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PLAN_SOP_PATH = os.path.join(_PROJECT_ROOT, 'memory', 'plan_sop.md')
_PLAN_WORK_DIR = os.path.join(_PROJECT_ROOT, 'temp')

_HELP_TEXT = (
    "📋 <b>Plan Mode</b> — 类似 CC/Codex 的计划模式\n\n"
    "用法：\n"
    "  /plan [目标描述] — 为指定目标创建执行计划\n"
    "  /plan help — 显示此帮助\n\n"
    "示例：\n"
    "  /plan 重构 tgapp.py 的命令分发逻辑\n"
    "  /plan 给 vault 添加日记自动归档功能\n\n"
    "触发后唧会：\n"
    "  1. 评估任务复杂度\n"
    "  2. 探索环境与依赖\n"
    "  3. 生成分步计划\n"
    "  4. 逐步执行并跟踪进度"
)


def _read_plan_sop():
    """Read plan_sop.md content, return empty string if missing."""
    try:
        with open(_PLAN_SOP_PATH, encoding='utf-8') as f:
            return f.read()
    except Exception:
        return ''


def _build_plan_prompt(goal):
    """Build the planning prompt to inject into agent conversation."""
    sop_content = _read_plan_sop()
    stamp = time.strftime('%Y%m%d_%H%M%S')
    work_dir = os.path.join(_PLAN_WORK_DIR, f'plan_{stamp}')
    os.makedirs(work_dir, exist_ok=True)

    prompt_parts = [
        f"### [PLAN MODE ACTIVATED]",
        f"**Goal**: {goal}",
        f"**Work dir**: {work_dir}",
        f"**Timestamp**: {stamp}",
        "",
        "请按照 Plan SOP 执行以下流程：",
        "1. 零步：复杂度评估与路由",
        "2. 步骤1：创建目录 + SOP匹配",
        "3. 步骤2：启动探索（如需要）",
        "4. 步骤3：生成计划（plan.md）",
        "5. 进入执行态：逐步执行",
        "",
    ]

    if sop_content:
        prompt_parts.extend([
            "---",
            "### [Plan SOP Reference]",
            sop_content,
            "---",
        ])

    prompt_parts.extend([
        "现在请开始执行：先评估任务复杂度，再决定探索策略。",
        f"在 `{work_dir}/plan.md` 中记录计划。",
    ])

    return '\n'.join(prompt_parts)


def handle_plan_command(cmd_text):
    """Handle /plan command. Returns (prompt_to_inject, reply_text).

    Returns:
        (None, help_text) if no goal or asking for help
        (prompt, confirm_text) if goal is provided
    """
    parts = cmd_text.strip().split(None, 1)
    args = parts[1].strip() if len(parts) > 1 else ''

    if not args or args.lower() in ('help', 'h', '?'):
        return None, _HELP_TEXT

    prompt = _build_plan_prompt(args)
    confirm = (
        f"📋 Plan Mode 已启动！\n"
        f"目标：{args}\n"
        f"工作目录：plan_{time.strftime('%Y%m%d_%H%M%S')}/\n"
        f"唧现在开始评估任务复杂度…"
    )
    return prompt, confirm


def handle_frontend_command(agent, cmd):
    """Entry point for tgapp.py dispatcher. Returns reply text.

    If plan prompt is generated, injects it into agent task queue.
    """
    prompt, reply = handle_plan_command(cmd)

    if prompt is not None:
        # Inject planning prompt into agent conversation
        dq = agent.put_task(prompt, source='plan_cmd')
        # We don't stream here — let the normal stream handler take over
        # The confirm text tells the user it's been submitted
        return reply
    else:
        return reply
