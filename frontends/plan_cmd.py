"""`/plan` command: enter plan mode — like CC/Codex plan workflow.

Usage:
    /plan [goal]        — enter plan mode with a goal
    /plan status        — show current plan mode status
    /plan exit          — exit plan mode
    /plan show          — show current plan.md content
    /plan               — show plan mode help

Plan SOP is loaded via system prompt/working memory — no need to dump it again.
"""
import os, time

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PLAN_WORK_DIR = os.path.join(_PROJECT_ROOT, 'temp')

# ── Plan Mode State ──────────────────────────────────────────────
# Tracks whether agent is currently in plan mode, and which phase.
# This state is module-level (single-process chatapp).

_plan_state = {
    "active": False,       # is plan mode active?
    "goal": "",            # current goal
    "phase": "idle",       # idle → explore → plan → execute → verify
    "plan_file": "",       # path to plan.md
    "work_dir": "",        # working directory
    "started_at": "",      # timestamp when activated
}

_PHASE_NAMES = {
    "idle": "空闲（未激活）",
    "explore": "探索中（只读调研）",
    "plan": "规划中（生成计划）",
    "execute": "执行中（逐步实施）",
    "verify": "验证中（终止检查）",
}


def get_plan_state():
    """Return a copy of current plan state (read-only for external use)."""
    return dict(_plan_state)


def _set_phase(phase: str):
    """Update current phase."""
    _plan_state["phase"] = phase


# ── Help Text ────────────────────────────────────────────────────

_HELP_TEXT = (
    "📋 <b>Plan Mode</b> — 类似 CC/Codex 的计划模式\n\n"
    "用法：\n"
    "  /plan [目标描述] — 为指定目标创建执行计划\n"
    "  /plan status    — 查看当前 plan 模式状态\n"
    "  /plan exit      — 退出 plan 模式\n"
    "  /plan show      — 显示当前 plan.md 内容\n"
    "  /plan help      — 显示此帮助\n\n"
    "示例：\n"
    "  /plan 重构 tgapp.py 的命令分发逻辑\n"
    "  /plan 给 vault 添加日记自动归档功能\n\n"
    "触发后唧会：\n"
    "  1. 评估任务复杂度\n"
    "  2. 探索环境与依赖\n"
    "  3. 生成分步计划并请你确认\n"
    "  4. 逐步执行并跟踪进度\n"
    "  5. 验证所有步骤完成"
)


# ── Core Logic ───────────────────────────────────────────────────

def _build_plan_prompt(goal):
    """Build the planning prompt to inject into agent conversation."""
    stamp = time.strftime('%Y%m%d_%H%M%S')
    work_dir = os.path.join(_PLAN_WORK_DIR, f'plan_{stamp}')
    os.makedirs(work_dir, exist_ok=True)

    # Update state
    _plan_state.update({
        "active": True,
        "goal": goal,
        "phase": "explore",
        "plan_file": os.path.join(work_dir, 'plan.md'),
        "work_dir": work_dir,
        "started_at": stamp,
    })

    prompt_parts = [
        "### [PLAN MODE ACTIVATED]",
        f"**Goal**: {goal}",
        f"**Work dir**: {work_dir}",
        f"**Plan file**: {work_dir}/plan.md",
        f"**Timestamp**: {stamp}",
        "",
        "### 硬性约束（进入plan模式必读）",
        "1. 当前处于 **探索态** —— 只读工具(file_read/web_scan/code_run只读)调研，禁止写入/执行",
        "2. 探索完毕后生成 plan.md，然后 **暂停等用户确认**",
        "3. 用户确认后才进入执行态，逐步执行并标记 [✓]/[✗]",
        "4. 最后一步标记后必须 file_read(plan.md) 全文扫描确认0个 [ ] 残留",
        "5. 每步执行前必须 file_read(plan.md)，禁止凭记忆执行",
        "",
        "请严格按 Plan SOP 执行。",
        f"在 `{work_dir}/plan.md` 中记录计划。",
        "现在开始：先评估任务复杂度，再进行环境探索。",
    ]
    return '\n'.join(prompt_parts)


def _build_status_text():
    """Build status report text."""
    s = _plan_state
    if not s["active"]:
        return "📋 当前没有活跃的 Plan 模式。\n用 `/plan [目标]` 开始新计划。"

    elapsed = ""
    if s["started_at"]:
        try:
            start_ts = time.mktime(time.strptime(s["started_at"], "%Y%m%d_%H%M%S"))
            mins = int((time.time() - start_ts) / 60)
            elapsed = f"\n⏱️ 已进行 {mins} 分钟"
        except Exception:
            pass

    phase_name = _PHASE_NAMES.get(s["phase"], s["phase"])
    plan_exists = os.path.exists(s["plan_file"]) if s["plan_file"] else False
    plan_status = "📄 plan.md 已创建" if plan_exists else "⏳ 尚未创建 plan.md"

    return (
        f"📋 <b>Plan Mode Status</b>\n\n"
        f"🎯 目标: {s['goal']}\n"
        f"📍 阶段: {phase_name}\n"
        f"📁 工作目录: {os.path.basename(s['work_dir'])}\n"
        f"📝 计划文件: {plan_status}"
        f"{elapsed}"
    )


def _build_show_text():
    """Read and return plan.md content, or a placeholder."""
    s = _plan_state
    if not s["active"] or not s["plan_file"]:
        return "📋 当前没有活跃的 Plan 模式。"
    if not os.path.exists(s["plan_file"]):
        return f"📄 plan.md 尚未创建。\n路径: {s['plan_file']}"
    try:
        with open(s["plan_file"], 'r', encoding='utf-8') as f:
            content = f.read()
        return f"📄 <b>plan.md</b>\n\n<pre>{content}</pre>"
    except Exception as e:
        return f"❌ 读取 plan.md 失败: {e}"


def _build_exit_text():
    """Exit plan mode and return confirmation."""
    if not _plan_state["active"]:
        return "📋 当前没有活跃的 Plan 模式。"
    goal = _plan_state["goal"]
    phase = _plan_state["phase"]
    _plan_state.update({
        "active": False, "goal": "", "phase": "idle",
        "plan_file": "", "work_dir": "", "started_at": "",
    })
    phase_name = _PHASE_NAMES.get(phase, phase)
    return f"📋 Plan Mode 已退出。\n原目标: {goal}\n退出时阶段: {phase_name}\n\n工作目录和 plan.md 仍保留在磁盘上，可随时重新进入。"


def handle_plan_command(cmd_text):
    """Handle /plan command. Returns (prompt_to_inject, reply_text).

    Returns:
        (None, reply_text) for help/status/exit/show (no agent injection)
        (prompt, confirm_text) for new plan goal
    """
    parts = cmd_text.strip().split(None, 1)
    args = parts[1].strip() if len(parts) > 1 else ''

    # ── Sub-commands ──
    if not args or args.lower() in ('help', 'h', '?'):
        return None, _HELP_TEXT

    if args.lower() == 'status':
        return None, _build_status_text()

    if args.lower() == 'exit':
        return None, _build_exit_text()

    if args.lower() == 'show':
        return None, _build_show_text()

    # ── New plan goal ──
    # If already in plan mode, warn but allow re-entry
    warn = ""
    if _plan_state["active"]:
        warn = f"⚠️ 当前已有活跃 Plan（目标: {_plan_state['goal']}），将覆盖。\n\n"

    prompt = _build_plan_prompt(args)
    confirm = (
        f"{warn}"
        f"📋 <b>Plan Mode 已启动！</b>\n\n"
        f"🎯 目标: {args}\n"
        f"📁 工作目录: {os.path.basename(_plan_state['work_dir'])}/\n"
        f"📍 阶段: 探索中\n\n"
        f"唧现在开始评估任务复杂度并探索环境…"
    )
    return prompt, confirm


def handle_frontend_command(agent, cmd):
    """Entry point for chatapp_common dispatcher. Returns reply text.

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
