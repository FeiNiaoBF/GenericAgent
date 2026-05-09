# -*- coding: utf-8 -*-
import sys, io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
"""
capture_window.py - 截取指定窗口截图 (纯ctypes实现)
API: capture_by_keyword("Chrome", save_path="chrome.png") → (img, title)
     capture_by_hwnd(0x123456) → img
     list_windows() → [(hwnd, title, w, h), ...]
CLI: python capture_window.py "Chrome" → 输出 Chrome.jpg
设计: 纯ctypes, 零第三方依赖(仅Pillow保存), 支持DWM窗口
⚠️ 标题模糊匹配, 最小化窗口可能空白, 先 activate 再截图
"""
import ctypes
from ctypes import wintypes
from PIL import Image
from pathlib import Path
import time

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
dwmapi = ctypes.windll.dwmapi

WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

def list_windows():
    """列出所有可见窗口"""
    result = []
    def callback(hwnd, lparam):
        length = user32.GetWindowTextLengthW(hwnd) + 1
        buffer = ctypes.create_unicode_buffer(length)
        user32.GetWindowTextW(hwnd, buffer, length)
        title = buffer.value
        if title and user32.IsWindowVisible(hwnd):
            rect = wintypes.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rect))
            w, h = rect.right - rect.left, rect.bottom - rect.top
            result.append((hwnd, title, w, h))
        return True
    user32.EnumWindows(WNDENUMPROC(callback), 0)
    return sorted(result, key=lambda x: x[1])

def find_window(keyword):
    """按标题关键词找窗口"""
    for hwnd, title, w, h in list_windows():
        if keyword.lower() in title.lower():
            return hwnd, title, w, h
    return None, None, 0, 0

def capture_window(hwnd):
    """截取指定窗口内容"""
    # Bring to foreground
    user32.ShowWindow(hwnd, 9)  # SW_RESTORE
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.3)

    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    left, top, right, bottom = rect.left, rect.top, rect.right, rect.bottom
    w, h = right - left, bottom - top
    print(f"  \U0001f4cf 窗口: ({left},{top}) {w}x{h}")

    # Capture screen area via GDI
    hdc_screen = user32.GetDC(None)
    hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
    hbitmap = gdi32.CreateCompatibleBitmap(hdc_screen, w, h)
    gdi32.SelectObject(hdc_mem, hbitmap)
    gdi32.BitBlt(hdc_mem, 0, 0, w, h, hdc_screen, left, top, 0x00CC0020)  # SRCCOPY

    # Extract bits
    bmp_info = wintypes.BITMAPINFO()
    bmp_info.bmiHeader.biSize = ctypes.sizeof(wintypes.BITMAPINFOHEADER)
    bmp_info.bmiHeader.biWidth = w
    bmp_info.bmiHeader.biHeight = -h  # top-down
    bmp_info.bmiHeader.biPlanes = 1
    bmp_info.bmiHeader.biBitCount = 32
    bmp_info.bmiHeader.biCompression = 0  # BI_RGB

    buf_size = w * h * 4
    pixels = ctypes.create_string_buffer(buf_size)
    gdi32.GetDIBits(hdc_mem, hbitmap, 0, h, pixels, ctypes.byref(bmp_info), 0)

    # Convert to PIL Image
    img = Image.frombuffer('RGBA', (w, h), pixels, 'raw', 'BGRA', 0, 1)
    img = img.convert('RGB')

    # Cleanup
    gdi32.DeleteObject(hbitmap)
    gdi32.DeleteDC(hdc_mem)
    user32.ReleaseDC(None, hdc_screen)

    return img

def capture_by_keyword(keyword, save_dir=None):
    """按关键词截取窗口"""
    hwnd, title, w, h = find_window(keyword)
    if not hwnd:
        print(f"\u274c 未找到包含 '{keyword}' 的窗口")
        return None
    print(f"\U0001f4cc 找到: {title} [{w}x{h}]")
    img = capture_window(hwnd)
    if save_dir:
        path = Path(save_dir) / f"{keyword.replace(' ', '_')}.jpg"
        img.save(path, 'JPEG', quality=85)
        print(f"\U0001f4be 保存: {path}")
    return img, title

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        img, title = capture_by_keyword(sys.argv[1])
        if img:
            img.save(f"{sys.argv[1]}.jpg")
            print(f"Saved {sys.argv[1]}.jpg")
    else:
        print("=== 当前可见窗口 ===")
        for hwnd, title, w, h in list_windows():
            print(f"  [{w}x{h}] 0x{hwnd:X} {title}")
