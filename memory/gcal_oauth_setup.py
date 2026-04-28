"""
Google Calendar API OAuth 设置向导
=================================
你需要做3步：
1. 在 Google Cloud Console 创建 OAuth 凭据
2. 下载 client_secret_xxx.json 到 ../memory/gcal_credentials.json
3. 运行本脚本完成首次授权
"""

import os, sys, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MEMORY = ROOT / "memory"
CREDENTIALS_FILE = MEMORY / "gcal_credentials.json"
TOKEN_FILE = MEMORY / "gcal_token.json"
SCOPES = ["https://www.googleapis.com/auth/calendar"]

def print_step(step, desc):
    print(f"\n{'='*60}")
    print(f"  Step {step}: {desc}")
    print(f"{'='*60}")

def check_prerequisites():
    """检查前置条件"""
    print_step(0, "检查前置条件")
    
    # Check packages
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        print("  ✅ Google API 包已安装")
        return True
    except ImportError as e:
        print(f"  ❌ 缺少包: {e}")
        print("  请运行: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
        return False

def check_credentials():
    """检查凭据文件"""
    print_step(1, "检查 OAuth 凭据文件")
    
    if CREDENTIALS_FILE.exists():
        try:
            with open(CREDENTIALS_FILE) as f:
                data = json.load(f)
            if data.get("installed") or data.get("web"):
                print(f"  ✅ 凭据文件存在: {CREDENTIALS_FILE}")
                return True
            else:
                print("  ❌ 凭据文件格式不正确")
                return False
        except:
            print("  ❌ 凭据文件无法读取")
            return False
    else:
        print(f"  ❌ 未找到凭据文件: {CREDENTIALS_FILE}")
        print()
        print("  📋 请按以下步骤操作：")
        print("  1. 打开 https://console.cloud.google.com/apis/credentials")
        print("  2. 创建项目（如没有）→ 启用 Google Calendar API")
        print("  3. 创建凭据 → OAuth 客户端 ID → 桌面应用")
        print("  4. 下载 JSON → 重命名为 gcal_credentials.json")
        print(f"  5. 放到目录: {MEMORY}")
        print()
        return False

def run_oauth():
    """执行 OAuth 授权"""
    print_step(2, "执行首次 OAuth 授权")
    
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    
    creds = None
    
    # Check existing token
    if TOKEN_FILE.exists():
        print("  发现已有 token 文件，尝试刷新...")
        with open(TOKEN_FILE) as f:
            creds = Credentials.from_authorized_user_info(json.load(f), SCOPES)
    
    if creds and creds.expired and creds.refresh_token:
        print("  Token 已过期，刷新中...")
        creds.refresh(Request())
        print("  ✅ Token 刷新成功!")
    elif not creds or not creds.valid:
        print("  需要浏览器授权...")
        flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
        creds = flow.run_local_server(port=0)
        print("  ✅ 授权成功!")
    
    # Save token
    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())
    print(f"  ✅ Token 已保存: {TOKEN_FILE}")

def test_calendar():
    """测试日历访问"""
    print_step(3, "测试 Google Calendar API 访问")
    
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    
    with open(TOKEN_FILE) as f:
        creds = Credentials.from_authorized_user_info(json.load(f), SCOPES)
    
    service = build("calendar", "v3", credentials=creds)
    
    # List next 5 events
    from datetime import datetime, timedelta
    now = datetime.utcnow().isoformat() + "Z"
    events_result = service.events().list(
        calendarId="primary",
        timeMin=now,
        maxResults=5,
        orderBy="startTime"
    ).execute()
    events = events_result.get("items", [])
    
    if events:
        print(f"  找到 {len(events)} 个未来事件:")
        for e in events:
            start = e["start"].get("dateTime", e["start"].get("date"))
            print(f"    📅 {start} | {e['summary']}")
    else:
        print("  ✅ API 连接正常，暂无未来事件")
    
    return service

def create_event(service):
    """创建测试事件"""
    print_step(4, "创建测试事件")
    
    from datetime import datetime, timedelta
    
    tomorrow = datetime.now() + timedelta(days=1)
    event = {
        "summary": "🐾 唧の测试事件",
        "description": "这是唧通过API创建的测试事件 ✨",
        "start": {
            "dateTime": tomorrow.replace(hour=10, minute=0, second=0).isoformat(),
            "timeZone": "Asia/Shanghai",
        },
        "end": {
            "dateTime": tomorrow.replace(hour=10, minute=30, second=0).isoformat(),
            "timeZone": "Asia/Shanghai",
        },
    }
    
    event = service.events().insert(calendarId="primary", body=event).execute()
    print(f"  ✅ 测试事件已创建!")
    print(f"  链接: {event.get('htmlLink')}")
    return event

def add_gcal_event_api(title, description, date_str, time_str, duration_min=30):
    """API方式添加Google Calendar事件"""
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    
    with open(TOKEN_FILE) as f:
        creds = Credentials.from_authorized_user_info(json.load(f), SCOPES)
    
    service = build("calendar", "v3", credentials=creds)
    
    # Parse time
    from datetime import datetime
    parts = time_str.split(":")
    hour, minute = int(parts[0]), int(parts[1])
    
    start_dt = datetime.strptime(f"{date_str} {hour:02d}:{minute:02d}:00", "%Y-%m-%d %H:%M:%S")
    from datetime import timedelta
    end_dt = start_dt + timedelta(minutes=duration_min)
    
    event = {
        "summary": title,
        "description": description,
        "start": {
            "dateTime": start_dt.isoformat(),
            "timeZone": "Asia/Shanghai",
        },
        "end": {
            "dateTime": end_dt.isoformat(),
            "timeZone": "Asia/Shanghai",
        },
    }
    
    event = service.events().insert(calendarId="primary", body=event).execute()
    return {"ok": True, "event_id": event["id"], "link": event.get("htmlLink")}


if __name__ == "__main__":
    print("🐾 Google Calendar API OAuth 设置向导")
    print("=" * 60)
    
    if not check_prerequisites():
        sys.exit(1)
    
    if not check_credentials():
        sys.exit(1)
    
    run_oauth()
    
    try:
        service = test_calendar()
        yn = input("\n📝 要不要创建一个测试事件? (y/n): ")
        if yn.lower() == "y":
            create_event(service)
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("  🎉 OAuth 设置完成!")
    print("  gcal_helper 现在可以使用 API 方式操作日历了")
    print("=" * 60)
