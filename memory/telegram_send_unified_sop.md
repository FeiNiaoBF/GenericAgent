---
name: telegram_send_unified
description: Telegram统一发送消息、文件、HTML渲染与贴纸操作
---
# Telegram 统一发送 SOP

## 门禁
- 仅引用环境变量：`TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID`；不读取密钥文件。
- 消息≤4096，超长分段；文件≤50MB；贴纸512×512透明且≤512KB。

## 消息/文件
```python
import os, requests
TOKEN=os.environ['TELEGRAM_BOT_TOKEN']; CHAT_ID=os.environ['TELEGRAM_CHAT_ID']
API=f'https://api.telegram.org/bot{TOKEN}'

def send_message(text, parse_mode='Markdown'):
    for i in range(0, len(text), 4096):
        requests.post(f'{API}/sendMessage', json={'chat_id':CHAT_ID,'text':text[i:i+4096],'parse_mode':parse_mode})

def send_file(path, caption=''):
    with open(path,'rb') as f:
        requests.post(f'{API}/sendDocument', files={'document':f}, data={'chat_id':CHAT_ID,'caption':caption})
```
- Markdown: `*bold*` `_italic_` `` `code` ``；HTML: `<b>` `<i>` `<code>`。
- 图片可用 `sendPhoto`；视频可用 `sendVideo`。

## HTML渲染
HTML→PNG截图→`sendPhoto`；`playwright`优先，`imgkit/wkhtmltoimage`备用。
```python
from playwright.sync_api import sync_playwright
def html_to_png(html, out):
    with sync_playwright() as p:
        b=p.chromium.launch(); page=b.new_page(viewport={'width':800,'height':600})
        page.set_content(html); page.screenshot(path=out, full_page=True); b.close()
```

## 贴纸
- 静态PNG或动图WEBM；透明背景；512×512；≤512KB。
- 包名必须 `_by_<bot_username>` 后缀。
- 流程：`uploadStickerFile` 得 `file_id` → `addStickerToSet`/`createNewStickerSet`。
- 已知包：`ChiChiStickers_by_ohchii_bot`，安装 `t.me/addstickers/包名`。

## 验证
环境变量 | 分段 | 文件大小 | 贴纸规格 | 包名后缀

`VERDICT: PASS` / `VERDICT: FAIL`
