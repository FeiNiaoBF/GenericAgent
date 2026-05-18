#!/usr/bin/env python3
"""Excalidraw绘图 - 创建Excalidraw图表

SOP: excalidraw_draw_diagram_sop.md
用途: 生成Excalidraw图表JSON，支持常见图类型
DIY: 一个脚本只做图表生成
"""

import json, sys

def create_diagram(elements=None):
    """创建Excalidraw图表"""
    diagram = {
        'type': 'excalidraw',
        'version': 2,
        'source': 'chii',
        'elements': elements or [],
    }
    return diagram

def add_rectangle(x, y, width, height, label='', color='#1971c2'):
    """添加矩形元素"""
    return {
        'type': 'rectangle',
        'x': x, 'y': y,
        'width': width, 'height': height,
        'strokeColor': color,
        'backgroundColor': f'{color}20',
        'fillStyle': 'solid',
        'strokeWidth': 2,
        'roughness': 1,
        'opacity': 100,
        'angle': 0,
        'id': f'rect_{x}_{y}',
        'boundElements': [{'type': 'text', 'id': f'text_{x}_{y}'}] if label else [],
    }

def add_text(x, y, text, font_size=16, color='#000'):
    """添加文本元素"""
    return {
        'type': 'text',
        'x': x, 'y': y,
        'text': text,
        'fontSize': font_size,
        'strokeColor': color,
        'textAlign': 'center',
        'verticalAlign': 'middle',
        'id': f'text_{x}_{y}',
    }

def add_arrow(x1, y1, x2, y2, label=''):
    """添加箭头"""
    return {
        'type': 'arrow',
        'x': x1, 'y': y1,
        'points': [[0, 0], [x2-x1, y2-y1]],
        'strokeColor': '#000',
        'startArrowhead': None,
        'endArrowhead': 'arrow',
        'label': {'text': label} if label else None,
    }

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Excalidraw图表生成')
    parser.add_argument('-o', '--output', default='diagram.excalidraw', help='输出文件')
    parser.add_argument('--type', choices=['flow', 'mindmap', 'blank'], default='flow', help='图表类型')
    args = parser.parse_args()

    elements = []
    if args.type == 'flow':
        # 简单流程图示例
        rects = [
            ('开始', 100, 100, 120, 60, '#1971c2'),
            ('处理', 100, 200, 120, 60, '#2f9e44'),
            ('结束', 100, 300, 120, 60, '#e03131'),
        ]
        for i, (label, x, y, w, h, color) in enumerate(rects):
            elements.append(add_rectangle(x, y, w, h, label, color))
            elements.append(add_text(x + w//2 - 20, y + 15, label))
        # 箭头
        for i in range(len(rects)-1):
            _, x1, y1, w1, h1, _ = rects[i]
            _, x2, y2, _, _, _ = rects[i+1]
            elements.append(add_arrow(x1 + w1//2, y1 + h1, x2 + w1//2, y2))

    diagram = create_diagram(elements)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(diagram, f, ensure_ascii=False, indent=2)
    print(f'✅ 图表已保存: {args.output} ({len(elements)}个元素)')

if __name__ == '__main__':
    main()
