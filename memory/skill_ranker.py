"""
skill_ranker.py - 对抓取的skill/资源自动评分排名
用法: python skill_ranker.py <input.json> [--top N] [--keyword 关键词]
"""
import json, sys, os, re
from collections import Counter

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'temp')

# 评分权重
WEIGHTS = {
    'relevance': 3,    # 与需求相关度
    'quality': 2,      # 内容质量
    'practicality': 2, # 实用性/可操作性
    'uniqueness': 1,   # 独特性(与现有SOP不重合)
}

# 质量信号词
QUALITY_SIGNALS = [
    'step', 'example', 'guide', 'tutorial', 'pattern',
    'practice', 'workflow', 'best', 'tip', 'trick',
    '步骤', '示例', '教程', '实践', '最佳'
]


def score_item(item: dict, keywords: list = None, existing_sops: list = None) -> dict:
    """对单个skill评分"""
    content = (item.get('content', '') + ' ' + item.get('title', '')).lower()
    title = item.get('title', '').lower()

    # 相关性: 关键词命中数
    relevance = 5
    if keywords:
        hits = sum(1 for kw in keywords if kw.lower() in content)
        relevance = min(5, max(1, hits))

    # 质量: 内容长度 + 结构信号词
    content_len = len(item.get('content', ''))
    quality = min(5, max(1, content_len // 1000 + 1))
    signal_hits = sum(1 for s in QUALITY_SIGNALS if s in content)
    quality = min(5, quality + signal_hits // 2)

    # 实用性: 是否有代码块/命令/具体步骤
    code_blocks = content.count('```')
    numbered_steps = len(re.findall(r'\d+[\.\)]\s', content))
    practicality = min(5, max(1, code_blocks + numbered_steps // 3))

    # 独特性: 检查与现有SOP的重合度
    uniqueness = 5
    if existing_sops:
        overlap = sum(1 for sop in existing_sops if any(w in content for w in sop.split()[:20]))
        uniqueness = max(1, 5 - overlap)

    scores = {
        'relevance': relevance,
        'quality': quality,
        'practicality': practicality,
        'uniqueness': uniqueness,
    }

    total = sum(scores[k] * WEIGHTS[k] for k in WEIGHTS)
    scores['total'] = total
    return scores


def rank_items(items: list, keywords: list = None, existing_sops: list = None, top_n: int = 10) -> list:
    """批量评分并排名"""
    for item in items:
        item['scores'] = score_item(item, keywords, existing_sops)

    ranked = sorted(items, key=lambda x: x['scores']['total'], reverse=True)
    return ranked[:top_n]


def print_ranking(ranked: list):
    """打印排名表"""
    print(f'\n{"="*70}')
    print(f'{"排名":<4} {"总分":<6} {"标题":<40} {"相关":<4} {"质量":<4} {"实用":<4} {"独特":<4}')
    print(f'{"-"*70}')
    for i, item in enumerate(ranked, 1):
        s = item['scores']
        title = item.get('title', 'N/A')[:38]
        print(f'{i:<4} {s["total"]:<6} {title:<40} {s["relevance"]:<4} {s["quality"]:<4} {s["practicality"]:<4} {s["uniqueness"]:<4}')
    print(f'{"="*70}')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='对skill列表评分排名')
    parser.add_argument('input', help='JSON文件路径(由skill_scraper生成)')
    parser.add_argument('--top', '-n', type=int, default=10, help='显示TOP N')
    parser.add_argument('--keyword', '-k', action='append', help='相关性关键词(可多次)')
    parser.add_argument('--output', '-o', help='排名结果输出文件')
    args = parser.parse_args()

    with open(args.input, 'r', encoding='utf-8') as f:
        items = json.load(f)

    # 加载现有SOP摘要(用于去重)
    sop_dir = os.path.join(os.path.dirname(__file__))
    existing = []
    for fname in os.listdir(sop_dir):
        if fname.endswith('_sop.md'):
            with open(os.path.join(sop_dir, fname), 'r', encoding='utf-8') as f:
                existing.append(f.read()[:500])

    ranked = rank_items(items, args.keyword, existing, args.top)
    print_ranking(ranked)

    if args.output:
        path = os.path.join(OUTPUT_DIR, args.output)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(ranked, f, ensure_ascii=False, indent=2)
        print(f'\n✅ 排名结果已保存到 {path}')
