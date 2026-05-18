#!/usr/bin/env python3
"""归藏PPT构建 - 构建归藏风格的PPT

SOP: guizang_build_ppt_sop.md
用途: 基于模板和数据构建PPT文件
DIY: 一个脚本只做PPT构建(需要pptx/guizang模板)
"""

import json, os, sys

DEFAULT_OUTPUT = 'output.pptx'

def build_from_template(data, template='default'):
    """从模板和数据构建PPT"""
    print('📊 构建PPT (模板: %s)' % template)
    print('   数据: %s...' % json.dumps(data, ensure_ascii=False)[:100])
    print()
    print('⚠️ 需要安装 python-pptx: pip install python-pptx')
    print('⚠️ 需要模板文件: guizang_template.pptx')
    return DEFAULT_OUTPUT

def create_outline(slides):
    """创建PPT大纲"""
    print('📋 PPT大纲 (%d页):' % len(slides))
    for i, slide in enumerate(slides, 1):
        print('  %d. %s' % (i, slide.get('title', '无标题')))
    return slides

def main():
    import argparse
    parser = argparse.ArgumentParser(description='归藏PPT构建')
    parser.add_argument('action', choices=['build', 'outline'], help='操作')
    parser.add_argument('--data', help='数据文件(JSON)')
    parser.add_argument('--template', default='default', help='模板名称')
    parser.add_argument('--output', default=DEFAULT_OUTPUT, help='输出路径')
    parser.add_argument('--title', action='append', help='幻灯片标题(用于outline)')
    args = parser.parse_args()

    if args.action == 'outline':
        slides = [{'title': t} for t in (args.title or ['封面', '目录', '正文', '结尾'])]
        create_outline(slides)
    elif args.action == 'build':
        if args.data:
            with open(args.data, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {'title': '未命名PPT'}
        build_from_template(data, args.template)

if __name__ == '__main__':
    main()
