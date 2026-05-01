#!/usr/bin/env python3
"""
Feishu Incoming Webhook -- zero OAuth, zero SDK, only needs a Webhook URL.

Usage:
  1. Add a Custom Bot in a Feishu group chat, get the webhook URL
  2. Write URL to llmcore/mykeys.py: fs_webhook_url = "https://open.feishu.cn..."
  3. Send:

      from frontends.feishu_webhook import send_text, send_card, send_post
      send_text("Hello from GenericAgent!")
      send_card("## Task done\n> details...")
      send_post(title="Daily", lines=["Task 1", "Task 2"])

Compared to fsapp.py (SDK):
  - fsapp.py:   two-way, needs OAuth App ID + Secret, depends on lark_oapi
  - webhook:    one-way send, only needs Webhook URL, zero external deps
"""

import json
import os as _os
import sys

_PROJECT_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
sys.path.insert(0, _PROJECT_ROOT)

import urllib.request
import urllib.error


def _get_webhook_url():
    try:
        from llmcore import mykeys
        url = str(mykeys.get("fs_webhook_url", "") or "").strip()
        return url
    except Exception:
        return ""

WEBHOOK_URL = _get_webhook_url()


def _post_json(payload):
    if not WEBHOOK_URL:
        return {"ok": False, "msg": "Webhook URL not configured (set fs_webhook_url in mykeys)", "data": None}
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        WEBHOOK_URL,
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            code = body.get("code", -1)
            if code == 0:
                return {"ok": True, "msg": "OK", "data": body}
            return {"ok": False, "msg": "API error: code=" + str(code) + ", msg=" + str(body.get("msg","")), "data": body}
    except urllib.error.HTTPError as e:
        return {"ok": False, "msg": "HTTP " + str(e.code) + ": " + str(e.reason), "data": None}
    except Exception as e:
        return {"ok": False, "msg": "Network error: " + str(e), "data": None}


def send_text(text):
    """Send plain text message"""
    return _post_json({"msg_type": "text", "content": {"text": str(text)}})


def send_card(markdown, title=""):
    """Send interactive card with Markdown content"""
    return _post_json({
        "msg_type": "interactive",
        "card": {
            "header": {"title": {"tag": "plain_text", "content": title or "Notice"}, "template": "blue"},
            "elements": [{"tag": "markdown", "content": str(markdown)}]
        }
    })


def send_card_full(card_dict):
    """Send full custom card (pass Feishu card JSON directly)"""
    return _post_json({"msg_type": "interactive", "card": card_dict})


def send_post(title, lines, lang="zh_cn"):
    """Send rich text (post) message"""
    content_lines = []
    for line in lines:
        if isinstance(line, list):
            content_lines.append(line)
        else:
            content_lines.append([{"tag": "text", "text": str(line)}])
    return _post_json({
        "msg_type": "post",
        "content": {"post": {lang: {"title": title, "content": content_lines}}}
    })


def status():
    return {
        "configured": bool(WEBHOOK_URL),
        "url_masked": (WEBHOOK_URL[:40] + "..." + WEBHOOK_URL[-10:]) if WEBHOOK_URL else "(not set)",
        "mode": "Incoming Webhook (one-way, no OAuth required)",
    }


# --- Card Builder Helpers (Schema 2.0) ---

def card_builder_progress(title, steps, template="blue"):
    """
    Build a progress card with collapsible panels (like _TaskCard in fsapp.py).
    steps: [{"title": "...", "content": "...", "done": bool}, ...]
    """
    elements = []
    for i, s in enumerate(steps):
        prefix = "✅ " if s.get("done") else "🔄 "
        elements.append({
            "tag": "collapsible_panel",
            "expanded": not s.get("done", False),  # expand current step
            "header": {
                "title": {"tag": "plain_text", "content": prefix + s.get("title", "")}
            },
            "elements": [
                {"tag": "markdown", "content": s.get("content", "_processing..._")}
            ]
        })
    elements.append({"tag": "hr"})
    done_count = sum(1 for s in steps if s.get("done"))
    elements.append({
        "tag": "note",
        "elements": [{"tag": "plain_text", "content": f"Progress: {done_count}/{len(steps)} completed"}]
    })
    return {
        "header": {"title": {"tag": "plain_text", "content": title}, "template": template},
        "elements": elements
    }


def card_builder_sections(title, sections, template="blue"):
    """
    Build a report card with collapsible sections.
    sections: [{"title": "...", "content": "..."}, ...]
    """
    elements = []
    for sec in sections:
        elements.append({
            "tag": "collapsible_panel",
            "expanded": False,
            "header": {
                "title": {"tag": "plain_text", "content": sec.get("title", "")}
            },
            "elements": [
                {"tag": "markdown", "content": sec.get("content", "")}
            ]
        })
    return {
        "header": {"title": {"tag": "plain_text", "content": title}, "template": template},
        "elements": elements
    }


def card_builder_action(title, text, buttons, template="blue"):
    """
    Build a card with action buttons.
    buttons: [{"text": "...", "url": "...", "type": "default"|"primary"|"danger"}, ...]
    """
    elements = [{"tag": "markdown", "content": text}, {"tag": "hr"}]
    action_buttons = []
    for btn in buttons:
        action_buttons.append({
            "tag": "button",
            "text": {"tag": "plain_text", "content": btn.get("text", "")},
            "type": btn.get("type", "default"),
            "url": btn.get("url", ""),
            "value": {}
        })
    elements.append({
        "tag": "action",
        "actions": action_buttons
    })
    return {
        "header": {"title": {"tag": "plain_text", "content": title}, "template": template},
        "elements": elements
    }


# --- Convenience send wrappers ---

def send_progress_card(title, steps):
    """Send a progress card (builds + sends via send_card_full)."""
    return send_card_full(card_builder_progress(title, steps))


def send_sections_card(title, sections):
    """Send a report card with collapsible sections."""
    return send_card_full(card_builder_sections(title, sections))


def send_action_card(title, text, buttons):
    """Send a card with action buttons."""
    return send_card_full(card_builder_action(title, text, buttons))


def dry_run():
    saved = WEBHOOK_URL
    globals()["WEBHOOK_URL"] = "https://open.feishu.cn/open-apis/bot/v2/hook/DRY-RUN"
    tests = [
        ("text", send_text("Hello World")),
        ("card", send_card("## Progress\n> 3/5 done", title="Report")),
        ("post", send_post("Daily Tasks", ["Item 1", "Item 2"])),
        ("progress_card", send_progress_card("Task Progress", [
            {"title": "Step 1: Initialize", "content": "Environment setup and config loading...", "done": True},
            {"title": "Step 2: Process", "content": "Processing data and generating output...", "done": False},
            {"title": "Step 3: Finalize", "content": "Final result pending...", "done": False},
        ])),
        ("sections_card", send_sections_card("Weekly Report", [
            {"title": "Summary", "content": "This week we completed 3 major features."},
            {"title": "Details", "content": "- Feature A: done\n- Feature B: in progress\n- Feature C: planned"},
            {"title": "Risks", "content": "No blocking issues identified."},
        ])),
        ("action_card", send_action_card("Confirm Action", "Do you want to proceed with the deployment?",
            [{"text": "Approve", "url": "https://example.com/approve", "type": "primary"},
             {"text": "Deny", "url": "https://example.com/deny", "type": "danger"}]))
    ]
    globals()["WEBHOOK_URL"] = saved
    return tests


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Feishu Webhook sender (zero OAuth)")
    p.add_argument("--text", type=str, help="Send plain text")
    p.add_argument("--card", type=str, help="Send Markdown card")
    p.add_argument("--title", type=str, default="Notice", help="Card title")
    p.add_argument("--dry-run", action="store_true", help="Print payloads without sending")
    p.add_argument("--status", action="store_true", help="Show status")
    p.add_argument("--progress", type=str, help="JSON: progress card steps")
    p.add_argument("--sections", type=str, help="JSON: sections card")
    p.add_argument("--action", type=str, help="JSON: action card [text, buttons]")
    args = p.parse_args()
    if args.status:
        print(json.dumps(status(), ensure_ascii=False, indent=2))
    elif args.dry_run:
        for name, r in dry_run():
            print("\n=== " + name + " ===")
            print(json.dumps(r, ensure_ascii=False, indent=2))
    elif args.text:
        print(send_text(args.text))
    elif args.card:
        print(send_card(args.card, title=args.title))
    elif args.progress:
        import ast
        print(send_progress_card(args.title, ast.literal_eval(args.progress)))
    elif args.sections:
        import ast
        print(send_sections_card(args.title, ast.literal_eval(args.sections)))
    elif args.action:
        import ast
        data = ast.literal_eval(args.action)
        print(send_action_card(args.title, data[0], data[1]))
    else:
        p.print_help()
