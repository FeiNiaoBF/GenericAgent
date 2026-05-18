#!/usr/bin/env python3
"""Chi格式化 - 应用Chi格式规则到文本

SOP: chii_format_response_sop.md
用途: 统一格式化风格，确保文本符合唧的格式规范
DIY: 一个脚本只做格式统一
"""

import re, sys

def format_chi_text(text):
    """应用Chi格式化规则"""
    # 1. 统一换行
    text = re.sub(r'\r\n|\r', '\n', text)
    
    # 2. 中文与英文之间加空格
    text = re.sub(r'([\u4e00-\u9fff])([a-zA-Z])', r'\1 \2', text)
    text = re.sub(r'([a-zA-Z])([\u4e00-\u9fff])', r'\1 \2', text)
    
    # 3. 中文与数字之间加空格
    text = re.sub(r'([\u4e00-\u9fff])(\d)', r'\1 \2', text)
    text = re.sub(r'(\d)([\u4e00-\u9fff])', r'\1 \2', text)
    
    # 4. 统一标点
    text = text.replace('...', '…')
    
    # 5. 去除行尾多余空格
    text = re.sub(r' +\n', '\n', text)
    
    # 6. 缩进统一为2空格
    lines = text.split('\n')
    result = []
    for line in lines:
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        new_indent = (indent // 2) * 2  # 保持2的倍数
        result.append(' ' * new_indent + stripped)
    
    return '\n'.join(result)

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Chi文本格式化')
    parser.add_argument('input', nargs='?', help='输入文件路径(留空则读stdin)')
    parser.add_argument('-o', '--output', help='输出文件路径(留空则写stdout)')
    args = parser.parse_args()

    if args.input:
        with open(args.input, 'r', encoding='utf-8') as f:
            text = f.read()
    else:
        text = sys.stdin.read()

    formatted = format_chi_text(text)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(formatted)
        print(f'✅ 格式化结果已写入: {args.output}')
    else:
        print(formatted)

if __name__ == '__main__':
    main()
