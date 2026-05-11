"""Official-style `/plan` command support.

Plan mode is planning-only: explore with read-only tools, ask for missing
decisions, and emit a single <proposed_plan> block. It never executes changes.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass


@dataclass
class PlanState:
    active: bool = False
    goal: str = ""
    scope_id: str = "default"
    status: str = "idle"
    started_at: str = ""
    updated_at: str = ""
    last_plan: str = ""
    last_response: str = ""


@dataclass
class PlanCommandResult:
    kind: str
    reply_text: str
    prompt: str = ""
    scope_id: str = "default"
    metadata: dict | None = None

    def __str__(self) -> str:
        return self.reply_text


_PLAN_BLOCK_RE = re.compile(
    r"<proposed_plan>\s*[\s\S]*?\s*</proposed_plan>",
    re.IGNORECASE,
)

_HELP_TEXT = (
    "📋 <b>Plan Mode</b>\n\n"
    "用法：\n"
    "  /plan 目标      — 只读探索并生成官方式计划\n"
    "  /plan status   — 查看当前计划状态\n"
    "  /plan show     — 显示最近一次 proposed_plan\n"
    "  /plan exit     — 退出当前计划模式\n\n"
    "规则：计划模式只做探索、提问、产出计划；不会执行文件修改。"
)


def _now_stamp() -> str:
    return time.strftime("%Y%m%d_%H%M%S")


def _ensure_plan_sessions(agent) -> dict:
    sessions = getattr(agent, "plan_sessions", None)
    if not isinstance(sessions, dict):
        sessions = {}
        setattr(agent, "plan_sessions", sessions)
    return sessions


def _state(agent, scope_id: str) -> PlanState:
    sessions = _ensure_plan_sessions(agent)
    state = sessions.get(scope_id)
    if not isinstance(state, PlanState):
        state = PlanState(scope_id=scope_id)
        sessions[scope_id] = state
    return state


def _parse_args(cmd_text: str) -> str:
    parts = (cmd_text or "").strip().split(None, 1)
    return parts[1].strip() if len(parts) > 1 else ""


def _build_plan_prompt(goal: str) -> str:
    return f"""### [OFFICIAL PLAN MODE]
Goal: {goal}

You are in planning-only mode.

Hard rules:
1. Do not implement, modify files, run formatters, run migrations, or perform destructive actions.
2. First ground yourself in the environment with read-only exploration.
3. Use only non-mutating actions while planning. Prefer `file_read`, read-only `code_run`, `web_scan`, and `ask_user`.
4. If high-impact ambiguity remains after exploration, call `ask_user` before finalizing.
5. Final answer must contain exactly one `<proposed_plan>` block and no implementation.
6. The plan must be decision-complete enough for another engineer or agent to implement immediately.

Required final shape:
<proposed_plan>
# Clear Title

## Summary
...

## Key Changes
...

## Public Interfaces
...

## Test Plan
...

## Assumptions
...
</proposed_plan>

Begin by inspecting the environment. Then either ask needed questions or output the final plan."""


def _metadata(goal: str, scope_id: str) -> dict:
    return {
        "plan_mode": True,
        "plan_only": True,
        "plan_goal": goal,
        "plan_scope_id": scope_id,
        "plan_started_at": _now_stamp(),
    }


def _status_text(state: PlanState) -> str:
    if not state.active:
        return "📋 当前没有活跃的 Plan Mode。用 `/plan 目标` 开始。"
    plan_state = "已有 proposed_plan" if state.last_plan else "尚未生成 proposed_plan"
    return (
        "📋 <b>Plan Mode Status</b>\n\n"
        f"目标: {state.goal}\n"
        f"状态: {state.status}\n"
        f"范围: {state.scope_id}\n"
        f"计划: {plan_state}\n"
        f"开始: {state.started_at or '-'}"
    )


def handle_plan_command(agent, cmd_text: str, scope_id: str = "default") -> PlanCommandResult:
    scope_id = str(scope_id or "default")
    args = _parse_args(cmd_text)
    low = args.lower()
    state = _state(agent, scope_id)

    if not args or low in {"help", "h", "?"}:
        return PlanCommandResult("help", _HELP_TEXT, scope_id=scope_id, metadata={})

    if low == "status":
        return PlanCommandResult("status", _status_text(state), scope_id=scope_id, metadata={})

    if low == "show":
        if state.last_plan:
            return PlanCommandResult("show", state.last_plan, scope_id=scope_id, metadata={})
        if state.active:
            return PlanCommandResult(
                "show",
                "📋 当前 Plan Mode 尚未生成 `<proposed_plan>`。",
                scope_id=scope_id,
                metadata={},
            )
        return PlanCommandResult("show", "📋 当前没有活跃的 Plan Mode。", scope_id=scope_id, metadata={})

    if low == "exit":
        if not state.active:
            return PlanCommandResult("exit", "📋 当前没有活跃的 Plan Mode。", scope_id=scope_id, metadata={})
        old_goal = state.goal
        state.active = False
        state.status = "idle"
        state.updated_at = _now_stamp()
        return PlanCommandResult(
            "exit",
            f"📋 Plan Mode 已退出。\n原目标: {old_goal}",
            scope_id=scope_id,
            metadata={},
        )

    stamp = _now_stamp()
    state.active = True
    state.goal = args
    state.scope_id = scope_id
    state.status = "planning"
    state.started_at = stamp
    state.updated_at = stamp
    state.last_plan = ""
    state.last_response = ""
    meta = _metadata(args, scope_id)
    return PlanCommandResult(
        "start_plan",
        f"📋 Plan Mode 已启动：{args}",
        prompt=_build_plan_prompt(args),
        scope_id=scope_id,
        metadata=meta,
    )


def handle_frontend_command(agent, cmd: str, scope_id: str = "default") -> PlanCommandResult:
    return handle_plan_command(agent, cmd, scope_id=scope_id)


def record_plan_result(agent, metadata: dict | None, response_text: str) -> None:
    metadata = metadata or {}
    scope_id = str(metadata.get("plan_scope_id") or "default")
    state = _state(agent, scope_id)
    state.last_response = response_text or ""
    match = _PLAN_BLOCK_RE.search(state.last_response)
    if match:
        state.last_plan = match.group(0).strip()
        state.status = "ready"
    elif state.active:
        state.status = "waiting"
    state.updated_at = _now_stamp()


def active_plan_metadata(agent, scope_id: str = "default") -> dict | None:
    state = _state(agent, str(scope_id or "default"))
    if not state.active:
        return None
    return _metadata(state.goal, state.scope_id)


def build_plan_followup_prompt(answer: str) -> str:
    return (
        "### [PLAN MODE USER ANSWER]\n"
        f"User answer: {answer}\n\n"
        "Continue planning-only mode. Use read-only exploration if needed. "
        "If enough information is available, output exactly one `<proposed_plan>` block. "
        "Do not implement."
    )
