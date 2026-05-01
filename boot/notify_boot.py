"""Notify boot status to configured bots instead of Windows popup."""
import os, sys, json, argparse, urllib.request, urllib.error
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

def read_mykey_token():
    mykey_path = os.path.join(PROJECT_ROOT, 'mykey.py')
    if not os.path.exists(mykey_path):
        return None
    with open(mykey_path, 'r', encoding='utf-8') as f:
        content = f.read()
    import re
    m = re.search(r"tg_bot_token\s*=\s*['\"]([^'\"]+)['\"]", content)
    return m.group(1) if m else None

def read_boot_config():
    config_path = os.path.join(PROJECT_ROOT, 'config', 'boot_config.json')
    if not os.path.exists(config_path):
        return {}
    with open(config_path, 'r', encoding='utf-8-sig') as f:
        return json.load(f)

def send_telegram(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = json.dumps({
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"[notify_boot] TG error: {e}", file=sys.stderr)
        return None

def main():
    parser = argparse.ArgumentParser(description='Send boot notification via bots')
    parser.add_argument('-Ok', '--ok', default='', help='Comma-separated list of started bots')
    parser.add_argument('-Fail', '--fail', default='', help='Comma-separated list of failed bots')
    args = parser.parse_args()

    ok_list = [b.strip() for b in args.ok.split(',') if b.strip()]
    fail_list = [b.strip() for b in args.fail.split(',') if b.strip()]

    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    lines = [f"<b>\U0001F423 GenericAgent \u542f\u52a8\u62a5\u544a</b>  <i>{now}</i>", ""]
    if ok_list:
        lines.append(f"\U0001F7E2 <b>\u5df2\u542f\u52a8:</b> {', '.join(ok_list)}")
    if fail_list:
        lines.append(f"\U0001F534 <b>\u542f\u52a8\u5931\u8d25:</b> {', '.join(fail_list)}")
    if not ok_list and not fail_list:
        lines.append("\u26a0\ufe0f \u65e0\u542f\u52a8\u4fe1\u606f")
    message = '\n'.join(lines)

    token = read_mykey_token()
    config = read_boot_config()
    tg_config = config.get('bots', {}).get('tg', {})
    tg_chat_id = tg_config.get('notify_chat_id', '')

    if token and tg_chat_id:
        result = send_telegram(token, tg_chat_id, message)
        if result and result.get('ok'):
            print(f"[notify_boot] TG notification sent to {tg_chat_id}")
        else:
            print(f"[notify_boot] TG send failed: {result}", file=sys.stderr)
    else:
        missing = []
        if not token: missing.append("TG token")
        if not tg_chat_id: missing.append("TG notify_chat_id")
        print(f"[notify_boot] Skipped TG: missing {', '.join(missing)}", file=sys.stderr)

if __name__ == '__main__':
    main()
