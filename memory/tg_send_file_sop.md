# [TG Send File SOP · L3] (v1.0)

## 执行摘要（≥1步执行前必读）
1. `from llmcore import mykeys; TOKEN = mykeys.get('tg_bot_token'); CHAT_ID = 8195469192`
2. 选方法：图片 `sendPhoto` / 文件 `sendDocument` / 消息 `sendMessage`，urllib+multipart零依赖
3. POST 后检查 `resp.read().decode()` 返回 `{"ok":true}` → 🛑 过验证门禁

## §1 概述
通过 urllib + multipart 直接调用 Telegram Bot API 发送文件/图片/消息，**零依赖**（无需 python-telegram-bot），可在 code_run 环境中直接使用。

## §2 凭据
- **Token**: `mykeys.get('tg_bot_token')` （mykey.py）
- **Chat ID**: `8195469192` （主人 @yeekox）
- **Bot**: @ohchii_bot

## §3 发送图片 (sendPhoto)

```python
import sys, urllib.request, urllib.error, os
sys.path.insert(0, r'D:\Creative_Studio\WorkSpace\Github\GenericAgent')
from llmcore import mykeys

TOKEN = mykeys.get('tg_bot_token')
CHAT_ID = 8195469192
IMG_PATH = "path/to/image.png"

boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
with open(IMG_PATH, 'rb') as f:
    img_data = f.read()

body = (
    f'--{boundary}\r\n'
    f'Content-Disposition: form-data; name="chat_id"\r\n\r\n{CHAT_ID}\r\n'
    f'--{boundary}\r\n'
    f'Content-Disposition: form-data; name="caption"\r\n\r\n📸 唧の截屏\r\n'
    f'--{boundary}\r\n'
    f'Content-Disposition: form-data; name="photo"; filename="{os.path.basename(IMG_PATH)}"\r\n'
    f'Content-Type: image/png\r\n\r\n'
).encode() + img_data + f'\r\n--{boundary}--\r\n'.encode()

req = urllib.request.Request(
    f'https://api.telegram.org/bot{TOKEN}/sendPhoto',
    data=body,
    headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
)
with urllib.request.urlopen(req, timeout=30) as resp:
    print(resp.read().decode())
```

## §4 发送文档 (sendDocument)

将上面代码中 `sendPhoto` → `sendDocument`，`photo` → `document`，`image/png` → `application/octet-stream`。

## §5 发送文本 (sendMessage)

```python
import urllib.parse
text = urllib.parse.quote("消息内容")
url = f'https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={text}'
with urllib.request.urlopen(url) as resp:
    print(resp.read().decode())
```

## §6 避坑
- 图片 ≤10MB (Telegram Bot API 限制)
- 大文件 (>5MB) 用 sendDocument 而非 sendPhoto
- chat_id 必须是整数，不是字符串
- code_run 环境无 PTB，必须用 urllib 方案

## 🛑 验证门禁（必须执行，否则流程未完成）

| # | 验证动作 | 工具 | 预期结果 | PASS/FAIL |
|---|----------|------|----------|-----------|
| 1 | 凭据有效 | code_run(python) | `TOKEN` 和 `CHAT_ID` 非空，长度合理 | |
| 2 | API可达 | code_run(python) | `urlopen(getMe)` 返回 `{"ok":true}` | |
| 3 | 发送成功 | code_run(python) | POST返回 `{"ok":true}`，含 `message_id` | |
| 4 | 接收确认 | 肉眼(TG客户端) | 目标聊天中收到发送的文件/消息 | |

最终裁定：`VERDICT: PASS` / `VERDICT: FAIL`