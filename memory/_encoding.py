"""
_encoding.py — UTF-8 stdout encoding setup (shared utility)
所有脚本统一导入此模块，避免重复编码设置代码
"""
import sys
import io


def setup_utf8():
    """Configure stdout for UTF-8 output (safe for both script and piped contexts)
    使用reconfigure()原地修改，避免TextIOWrapper __del__关闭底层buffer
    """
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')
