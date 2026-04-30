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


def dry_run():
    saved = WEBHOOK_URL
    globals()["WEBHOOK_URL"] = "https://open.feishu.cn/open-apis/bot/v2/hook/DRY-RUN"
    tests = [
        ("text", send_text("Hello World")),
        ("card", send_card("## Progress\n> 3/5 done", title="Report")),
        ("post", send_post("Daily Tasks", ["Item 1", "Item 2"])),
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
    else:
        p.print_help()
