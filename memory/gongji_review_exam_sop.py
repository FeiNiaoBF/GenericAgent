#!/usr/bin/env python3
"""公基考试复习 - 公共基础知识考试复习工具

SOP: gongji_review_exam_sop.md
用途: 管理和复习公共基础知识题目
DIY: 一个脚本只做考试复习
"""

import json, os, random, sys

DATA_FILE = 'D:\Creative_Studio\WorkSpace\Github\GenericAgent\memory\gongji_questions.json'

def load_questions():
    """加载题目库"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def random_quiz(topic=None, count=5):
    """随机出题"""
    questions = load_questions()
    if topic:
        questions = [q for q in questions if q.get('topic') == topic]
    
    if not questions:
        print('⚠️ 题库为空')
        return []
    
    selected = random.sample(questions, min(count, len(questions)))
    print(f'📝 随机抽题 ({len(selected)}道)')
    for i, q in enumerate(selected, 1):
        print(f'\n{i}. {q["question"]}')
        for j, opt in enumerate(q.get('options', []), 1):
            print(f'   {chr(64+j)}. {opt}')
    return selected

def add_question(question, answer, options=None, topic='general'):
    """添加题目"""
    questions = load_questions()
    q = {
        'id': len(questions) + 1,
        'question': question,
        'answer': answer,
        'options': options or [],
        'topic': topic
    }
    questions.append(q)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)
    print(f'✅ 已添加题目 #{q["id"]}')
    return q

def main():
    import argparse
    parser = argparse.ArgumentParser(description='公基复习工具')
    parser.add_argument('action', choices=['quiz', 'add', 'stats'], help='操作')
    parser.add_argument('--topic', help='题目主题')
    parser.add_argument('--count', type=int, default=5, help='出题数量')
    parser.add_argument('--question', help='题目内容')
    parser.add_argument('--answer', help='答案')
    args = parser.parse_args()

    if args.action == 'quiz':
        random_quiz(args.topic, args.count)
    elif args.action == 'add':
        if not args.question or not args.answer:
            print('❌ add需要 --question 和 --answer')
            sys.exit(1)
        add_question(args.question, args.answer, topic=args.topic or 'general')
    elif args.action == 'stats':
        questions = load_questions()
        topics = {}
        for q in questions:
            topics[q.get('topic', 'general')] = topics.get(q.get('topic', 'general'), 0) + 1
        print(f'📊 题库统计: 共{len(questions)}题')
        for t, c in sorted(topics.items()):
            print(f'  {t}: {c}题')

if __name__ == '__main__':
    main()
