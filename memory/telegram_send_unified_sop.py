#!/usr/bin/env python3
"""Telegram统一发送：通过TG发送消息/文件/通知"""
import requests
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / '..' / 'config' / 'tg_bot.json'

def load_config() -> dict:
    """加载TG配置"""
    import json
    return json.loads(CONFIG_PATH.read_text(encoding='utf-8'))

def send_message(text: str, chat_id: str = None) -> bool:
    """发送文本消息"""
    cfg = load_config()
    url = f"https://api.telegram.org/bot{cfg['token']}/sendMessage"
    payload = {"chat_id": chat_id or cfg['default_chat'], "text": text}
    resp = requests.post(url, json=payload, timeout=10)
    return resp.ok

def send_file(file_path: str, chat_id: str = None) -> bool:
    """发送文件"""
    cfg = load_config()
    url = f"https://api.telegram.org/bot{cfg['token']}/sendDocument"
    with open(file_path, 'rb') as f:
        files = {'document': f}
        data = {"chat_id": chat_id or cfg['default_chat']}
        resp = requests.post(url, files=files, data=data, timeout=30)
    return resp.ok
