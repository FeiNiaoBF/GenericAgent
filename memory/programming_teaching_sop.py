#!/usr/bin/env python3
"""编程教学 - 编程教学辅助工具

SOP: programming_teaching_sop.md
用途: 提供编程教学, 包括代码讲解/练习/检查
DIY: 一个脚本只做编程教学
"""

import sys, ast, textwrap

def check_code(code, language='python'):
    """检查代码语法"""
    if language == 'python':
        try:
            ast.parse(code)
            print('✅ Python代码语法正确!')
            return True
        except SyntaxError as e:
            print('❌ 语法错误: %s' % e)
            return False
    else:
        print('⚠️ 不支持的语言: %s' % language)
        return False

def explain_code(code):
    """解释代码功能"""
    print('📖 代码讲解:')
    lines = code.strip().split('\n')
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith('def '):
            func_name = stripped.split('def ')[1].split('(')[0]
            print('  L%d: 定义函数 `%s()`' % (i, func_name))
        elif stripped.startswith('class '):
            cls_name = stripped.split('class ')[1].split(':')[0].split('(')[0]
            print('  L%d: 定义类 `%s`' % (i, cls_name))
        elif stripped.startswith('import ') or stripped.startswith('from '):
            print('  L%d: 导入模块' % i)
        elif stripped.startswith('if ') or stripped.startswith('elif '):
            print('  L%d: 条件判断' % i)
        elif stripped.startswith('for ') or stripped.startswith('while '):
            print('  L%d: 循环' % i)
        elif stripped.startswith('return '):
            print('  L%d: 返回值' % i)
        elif stripped.startswith('#'):
            print('  L%d: 注释: %s' % (i, stripped[1:].strip()))
    return True

def main():
    import argparse
    parser = argparse.ArgumentParser(description='编程教学工具')
    parser.add_argument('action', choices=['check', 'explain'], help='操作')
    parser.add_argument('--code', help='代码字符串')
    parser.add_argument('--file', help='代码文件')
    parser.add_argument('--lang', default='python', help='编程语言')
    args = parser.parse_args()

    code = args.code
    if args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            code = f.read()
    
    if not code:
        print('❌ 需要 --code 或 --file')
        sys.exit(1)

    if args.action == 'check':
        check_code(code, args.lang)
    elif args.action == 'explain':
        explain_code(code)

if __name__ == '__main__':
    main()
