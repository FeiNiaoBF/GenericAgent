# 📮 Telegram 统一操作 SOP (v1.1)

> 合并自：notification / send_file / html_rendering / sticker

## 执行摘要
1. 判断类型：消息/文件/HTML渲染/贴纸 → 对应API
2. 所有调用需 `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` 环境变量 → 🛑 门禁

## §1 消息推送
```python
import requests, os
TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
CHAT_ID = os.environ['TELEGRAM_CHAT_ID']

def send_message(text, parse_mode='Markdown'):
    requests.post(f'https://api.telegram.org/bot{TOKEN}/sendMessage',
        json={'chat_id': CHAT_ID, 'text': text, 'parse_mode': parse_mode})
```
- 长消息(>4096)自动分段 | Markdown: `*bold*` `_italic_` `` `code` `` | HTML: `<b>` `<i>` `<code>`

## §2 文件发送
```python
def send_file(file_path, caption=''):
    with open(file_path, 'rb') as f:
        requests.post(f'https://api.telegram.org/bot{TOKEN}/sendDocument',
            files={'document': f}, data={'chat_id': CHAT_ID, 'caption': caption})
```
- 任意类型，≤50MB | 图片`sendPhoto` | 视频`sendVideo`

## §3 HTML渲染
HTML→截图→`sendPhoto`。工具：playwright优先，备用imgkit/wkhtmltoimage。
```python
from playwright.sync_api import sync_playwright
def html_to_png(html_str, output_path):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': 800, 'height': 600})
        page.set_content(html_str)
        page.screenshot(path=output_path, full_page=True)
        browser.close()
```

## §4 贴纸包管理
规格：512×512px / PNG(静态)或WEBM(动图) / 透明背景 / ≤512KB
```python
def create_sticker_set(name, title, emoji, png_path):
    """包名必须 _by_<bot_username> 后缀"""
    with open(png_path, 'rb') as f:
        resp = requests.post(f'https://api.telegram.org/bot{TOKEN}/uploadStickerFile',
            data={'user_id': OWNER_ID}, files={'png_sticker': f})
    file_id = resp.json()['result']['file_id']
    requests.post(f'https://api.telegram.org/bot{TOKEN}/addStickerToSet',
        json={'user_id': OWNER_ID, 'name': name, 'emojis': emoji, 'png_sticker': file_id})
```
已知包：`ChiChiStickers_by_ohchii_bot` (20枚, 2026-04-30) → `t.me/addstickers/包名` 安装

## 🛑 验证门禁
| 检查项 | 状态 |
|--------|------|
| BOT_TOKEN + CHAT_ID 已设置？ | |
| 消息≤4096(或已分段)？ | |
| 文件≤50MB？ | |
| 贴纸512×512 PNG透明？ | |
| 包名 `_by_<bot>` 后缀？ | |

最终裁定：`VERDICT: PASS` / `VERDICT: FAIL`
