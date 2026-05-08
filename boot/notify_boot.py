"""Notify boot/shutdown status to configured bots with personified messages."""
import os, sys, json, argparse, urllib.request, urllib.error, random
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# ──── 人格化消息池 ────
_CHII_WAKE_BRIEF = [
    "唧、ちぃ起来了！✨",
    "ちぃ〜おはよー、なの！",
    "むむ…起きたです！",
    "ちぃ、準備万端！",
]
_CHII_SLEEP_BRIEF = [
    "ちぃ、おやすみなさい 💤",
    "ふわぁ…寝ます、なの！",
    "ちぃ、また明日ね〜 🌙",
    "おやすみ、なの…✨",
]


def read_mykey_token():
    mykey_path = os.path.join(PROJECT_ROOT, 'mykey.py')
    if not os.path.exists(mykey_path):
        return None
    with open(mykey_path, 'r', encoding='utf-8') as f:
        content = f.read()
    m = __import__('re').search(r'tg_bot_token\s*=\s*["\']([^"\']+)["\']', content)
    return m.group(1) if m else None


def read_boot_config():
    config_path = os.path.join(SCRIPT_DIR, 'boot_config.json')
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def send_tg_message(token, chat_id, text):
    """Send message via Telegram Bot API (direct HTTP, no library dependency)."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = resp.read().decode('utf-8')
            return json.loads(result)
    except urllib.error.URLError as e:
        return {"ok": False, "description": str(e)}


def build_status_msg(ok_list, fail_list):
    """Build human-readable status line."""
    parts = []
    if ok_list:
        parts.append(f"✅ {', '.join(ok_list)}")
    if fail_list:
        parts.append(f"❌ {', '.join(fail_list)}")
    return "  ".join(parts) if parts else ""


def main():
    parser = argparse.ArgumentParser(description='Send boot/shutdown notification via bots')
    parser.add_argument('--event', choices=['boot', 'shutdown'], default='boot',
                        help='Event type: boot or shutdown (default: boot)')
    parser.add_argument('-Ok', '--ok', default='', help='Comma-separated list of started bots')
    parser.add_argument('-Fail', '--fail', default='', help='Comma-separated list of failed bots')
    args = parser.parse_args()

    ok_list = [b.strip() for b in args.ok.split(',') if b.strip()]
    fail_list = [b.strip() for b in args.fail.split(',') if b.strip()]

    # --- 构造拟人化消息 ---
    if args.event == 'shutdown':
        header = random.choice(_CHII_SLEEP_BRIEF)
        status = build_status_msg(ok_list, fail_list)
        if status:
            text = f"{header}\n{status}"
        else:
            text = header
        print(f"[notify_boot] shutdown: \"{text}\"")
    else:
        header = random.choice(_CHII_WAKE_BRIEF)
        status = build_status_msg(ok_list, fail_list)
        if status:
            text = f"{header}\n{status}"
        else:
            text = header
        print(f"[notify_boot] boot: \"{text}\"")

    # --- 发送到 TG ---
    token = read_mykey_token()
    config = read_boot_config()
    tg_chat_id = config.get('notify_chat_id', '') \
                 or (config.get('bots', {}).get('tg', {}).get('notify_chat_id', '')) \
                 or os.environ.get('GA_NOTIFY_CHAT_ID', '')

    if token and tg_chat_id:
        result = send_tg_message(token, tg_chat_id, text)
        if result.get('ok'):
            print(f"[notify_boot] TG send OK to {tg_chat_id}")
        else:
            print(f"[notify_boot] TG send failed: {result}", file=sys.stderr)
    else:
        missing = []
        if not token:
            missing.append("TG token")
        if not tg_chat_id:
            missing.append("TG notify_chat_id")
        print(f"[notify_boot] Skipped TG: missing {', '.join(missing)}", file=sys.stderr)


if __name__ == '__main__':
    main()