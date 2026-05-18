#!/usr/bin/env python3
"""学习辅导 - 学习辅导工具

SOP: learning_tutor_study_sop.md
用途: 生成学习计划、知识点讲解、题目练习
DIY: 一个脚本只做学习辅导
"""

import sys

def explain_concept(concept, detail='basic'):
    """讲解概念"""
    print('📚 概念讲解: %s' % concept)
    print('   详细程度: %s' % detail)
    print('   唧会帮主人理解这个概念的~')
    return True

def generate_practice(topic, count=3):
    """生成练习题"""
    print('✏️ 练习题 (%s):' % topic)
    for i in range(1, count + 1):
        print('  %d. (题目待生成)' % i)
    print()
    print('💡 提示: 唧的知识库在 memory/目录')
    print('   主人可以指定具体问题,唧来解答~')

def make_study_plan(subjects, days=7):
    """制定学习计划"""
    print('📅 学习计划 (%d天)' % days)
    for i, subject in enumerate(subjects):
        print('  Day %d: %s' % (i % days + 1, subject))
    return {'subjects': subjects, 'days': days}

def main():
    import argparse
    parser = argparse.ArgumentParser(description='学习辅导工具')
    parser.add_argument('action', choices=['explain', 'practice', 'plan'], help='操作')
    parser.add_argument('--concept', help='要讲解的概念')
    parser.add_argument('--topic', default='general', help='主题')
    parser.add_argument('--count', type=int, default=3, help='题目数量')
    parser.add_argument('--subject', action='append', help='学习科目')
    parser.add_argument('--days', type=int, default=7, help='计划天数')
    args = parser.parse_args()

    if args.action == 'explain':
        explain_concept(args.concept or '未指定')
    elif args.action == 'practice':
        generate_practice(args.topic, args.count)
    elif args.action == 'plan':
        subjects = args.subject or ['Python', '笔记整理']
        make_study_plan(subjects, args.days)

if __name__ == '__main__':
    main()
