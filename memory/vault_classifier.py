#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from _encoding import setup_utf8; setup_utf8()
"""
vault_classifier.py — Obsidian Vault 内容分类器 (v2)
基于文件内容特征自动推断 type/status/tags，不再依赖目录位置。

用法:
  python vault_classifier.py                    # 全量扫描+写入
  python vault_classifier.py --dry-run           # 预览不写入
  python vault_classifier.py --file "标题"       # 只处理特定文件

输出:
  - 为每个.md文件补充/修正 frontmatter 中的 type, status, tags
  - 无frontmatter的文件跳过(非笔记文件)
"""

import os, re, yaml
from collections import Counter
from pathlib import Path

VAULT = r"D:\Documents_Learn\Personal\Obsidian\Codex Vitae"

# ── 类型优先级（数字越小优先级越高，高优先级优先判定） ──
TYPE_PRIORITY = {
    'template': 0,
    'daily':    1,
    'book':     2,
    'moc':      3,
    'project':  4,
    'technique':5,
    'area':     6,
    'resource': 7,
    'note':     9,   # 兜底
}

def classify_type(body: str, rel: str) -> str:
    """基于内容+路径特征推断类型"""
    rel_norm = rel.replace('\\', '/')
    body_lower = body.lower()
    first_200 = body[:200].strip()
    # 同时匹配H2和H3，用于检测标题层级
    h2_tags = set(re.findall(r'^##\s+(.+)$', body, re.MULTILINE))
    h3_tags = set(re.findall(r'^###\s+(.+)$', body, re.MULTILINE))
    
    candidates = {}
    
    # template
    if '/Templates/' in rel_norm or '{{date:' in body or '{{title}}' in body:
        candidates['template'] = TYPE_PRIORITY['template']
    
    # daily
    if '/Daily/' in rel_norm or re.match(r'^# \d{4}年\d{1,2}月\d{1,2}日', body):
        candidates['daily'] = TYPE_PRIORITY['daily']
    
    # book: Books目录 + 特定H2标题或字段
    if '/Books/' in rel_norm:
        book_sigs = {'核心摘要', '书摘与批注', '书评', '概要', '读书笔记'}
        if h2_tags & book_sigs or 'isbn:' in body_lower or 'dewey:' in body_lower:
            candidates['book'] = TYPE_PRIORITY['book']
    
    # moc: Maps目录 或 含DATAVIEW+多双链
    if '/Maps/' in rel_norm:
        double_links = body.count('[[')
        if double_links >= 3 or 'dataview' in body_lower:
            candidates['moc'] = TYPE_PRIORITY['moc']
    
    # project: Quests目录 或 项目相关H2
    if '/Quests/' in rel_norm:
        candidates['project'] = TYPE_PRIORITY['project']
    project_h2s = {'项目定义', '项目规划', '功能拆解', '架构拆解', '系统设计'}
    if h2_tags & project_h2s:
        candidates['project'] = min(candidates.get('project', 99), TYPE_PRIORITY['project'])
    
    # technique: 方法/算法/技术类H2标题
    tech_h2s = {'步骤', '方法', '流程', '技巧', '操作', '实现方式', '操作步骤', '实施',
                '解答', '题目', '解决方案', 'Solution',
                '原理', '实现', '复杂度', '算法', '数据结构'}
    if h2_tags & tech_h2s:
        candidates['technique'] = TYPE_PRIORITY['technique']
    # 也检查H3（解决部分三级标题的算法笔记）
    tech_h3s = {'步骤', '使用方法', '技巧', '实现', '算法', '解法',
                '代码', '伪代码', '公式', '证明', '参数', '返回值',
                '复杂度分析', '时间复杂度', '空间复杂度', '示例代码', 'Solution',
                '题目', '解答', 'description', 'solution', 'test', 'approach',
                '原理'}
    if h3_tags & tech_h3s:
        candidates['technique'] = TYPE_PRIORITY['technique']
    # 内容中包含明确的技术/算法关键词（补标题检测覆盖不到的）
    tech_content_keywords = ['时间复杂度', '空间复杂度', '复杂度分析',
                             'AC自动机', 'KMP', '字符串匹配', '自动机',
                             'BFS', 'DFS', '动态规划', '滑动窗口', '双指针', '位运算',
                             '前缀和', '差分', '单调栈', '单调队列',
                             '并查集', '拓扑排序', '最短路径', '最小生成树',
                             '二分图', '背包问题', '快速幂', '矩阵快速幂',
                             '组合数', '排列数', '筛法',
                             '线段树', '树状数组', '红黑树', '字典树',
                             '阻塞队列', '线程池', '连接池',
                             'Trie', 'LRU', 'LFU', 'AVL',
                             'algorithm', 'complexity',
                             'protobuf', 'thrift', 'grpc',
                             'leetcode', '力扣', 'codeforces', 'atcoder',
                             'API设计', '系统设计', 'design pattern', '设计模式']
    if any(kw in body_lower for kw in tech_content_keywords):
        candidates['technique'] = TYPE_PRIORITY['technique']
    # 文件名含算法竞赛/LeetCode/代码题模式
    fname = rel.replace('\\', '/').rsplit('/', 1)[-1]
    fname_lower = fname.lower() if fname else ''
    tech_fname_patterns = ['lc_', 'leet', 'code_', 'cf_', 'at_', 'sol_',
                           'solution_', '题解', '算法', '题目']
    if any(p in fname_lower for p in tech_fname_patterns):
        candidates['technique'] = TYPE_PRIORITY['technique']
    
    # area: Domains目录 + 多双链
    if '/Domains/' in rel_norm and body.count('[[') >= 3:
        candidates['area'] = TYPE_PRIORITY['area']
    
    # resource: Library子目录(排除Books/Notes/Maps—它们有各自类型)
    if rel_norm.startswith('03.Library/') and not any(p in rel_norm for p in ['/Books/', '/Notes/', '/Maps/']):
        candidates['resource'] = TYPE_PRIORITY['resource']
    
    if not candidates:
        return 'note'
    
    # 按优先级选最高的
    return min(candidates, key=candidates.get)


def classify_status(body: str, rel: str, ftype: str, existing_status: str = None) -> str:
    """基于内容特征推断状态"""
    rel_norm = rel.replace('\\', '/')
    
    # 公共检测：in-review (适用于note/resource/technique/area/moc)
    # 正文含#review/需整理，或已有的status是review/in-review则保留
    in_review_types = {'note', 'resource', 'technique', 'area', 'moc'}
    if ftype in in_review_types:
        if '#review' in body or '需整理' in body or existing_status in ('in-review', 'review'):
            return 'in-review'
    
    if ftype == 'daily':
        checkboxes = re.findall(r'- \[([ xX])\]', body)
        if not checkboxes:
            return 'completed'
        if any(c in 'xX' for c in checkboxes):
            completed = sum(1 for c in checkboxes if c in 'xX')
            if completed == len(checkboxes):
                return 'completed'
            else:
                return 'in-progress'
        return 'in-progress'
    
    if ftype == 'book':
        if 'finished_reading' in body or 'rating:' in body:
            rating_m = re.search(r'rating:\s*(\d)', body)
            if rating_m and int(rating_m.group(1)) > 0:
                return 'finished'
        if 'started_reading' in body or '## 随笔' in body:
            return 'reading'
        return 'to-read'
    
    if ftype == 'project':
        checkboxes = re.findall(r'- \[([ xX])\]', body)
        if checkboxes:
            if all(c in 'xX' for c in checkboxes):
                return 'completed'
            return 'in-progress'
        return 'draft'
    
    if ftype == 'resource':
        return 'processed'
    
    if ftype in ('moc', 'area'):
        if body.count('[[') >= 5 and len(body) > 500:
            return 'evergreen'
        return 'draft'
    
    # note / technique / template
    if body.count('[[') >= 3 and len(body) > 500:
        return 'evergreen'
    return 'draft'


def classify_tags(body: str, rel: str, ftype: str) -> list:
    """基于内容+路径推断tags"""
    rel_norm = rel.replace('\\', '/')
    body_lower = body.lower()
    tags = set()
    
    # 1. 目录上下文tag（只取中间目录段，杜绝文件名当标签）
    dir_tags = []
    parts = rel_norm.split('/')
    # parts[1:-1] 排除根目录(parts[0])和文件名(parts[-1])
    for p in parts[1:-1]:
        p_lower = p.lower()
        if p_lower not in ('domains', 'library', 'books', 'daily', 'chronicles', 
                          'quests', 'system', 'templates', 'mocs', 'clippings'):
            dir_tags.append(p_lower)
    
    dir_map = {
        'cs': 'cs', 'computer science': 'cs', 'computer-science': 'cs',
        'ai': 'ai', 'artificial intelligence': 'ai',
        'english': 'english', 'language': 'english',
        'history': 'history',
        'health': 'health',
        'reading': 'reading',
        'game': 'game', 'gaming': 'game',
        'development': 'development', 'dev': 'development',
        'technology': 'tech', 'tech': 'tech',
        'business': 'business',
        'culture': 'culture',
        'psychology': 'psychology',
        'productivity': 'productivity',
        'philosophy': 'philosophy',
        'library': 'library',
        'blog': 'blog',
        'network': 'networking', 'networking': 'networking',
        'rust': 'rust',
        'database': 'database',
    }
    
    # 层级化标签映射 — 扁平tag → 二级tag
    hierarchy_map = {
        # tech/ 父级
        'cs': 'tech/cs',
        'development': 'tech/development',
        'ai': 'tech/ai',
        'algorithm': 'tech/algorithm',
        'rust': 'tech/rust',
        'math': 'tech/math',
        'database': 'tech/database',
        'network': 'tech/network',
        'networking': 'tech/network',
        'computer': 'tech/computer',
        'cs144': 'tech/cs144',
        'technology': 'tech/technology',
        # english/ 父级
        'phonetics': 'english/phonetics',
        '音标': 'english/phonetics',
        '英语': 'english',
    }
    for dt in dir_tags:
        mapped = dir_map.get(dt, dt)
        tags.add(mapped)
    
    # 2. 内容关键词tag
    content_keywords = {
        'ai': ['machine learning', 'deep learning', 'llm', 'gpt', 'transformer', 
               'neural network', '人工智能', '大模型', 'chatgpt', 'claude', 'agent'],
        'cs': ['algorithm', 'data structure', 'tcp', 'http', 'api', 'database',
               '操作系统', '编译', '网络协议', '编程', '代码', '函数'],
        'english': ['vocabulary', 'grammar', 'pronunciation', 'phrasal verb',
                    '单词', '语法', '发音', '口语', '音标', '英语'],
        'phonetics': ['音标', 'phonetic', 'pronunciation', '发音', 'ipa'],
        'reading': ['book', 'reading', '读书', '阅读', '笔记', '书评'],
        'game': ['game', 'gaming', '游戏', 'rpg', 'rts'],
        'development': ['project', 'build', 'develop', 'code', 'github', 'git',
                       '项目', '开发', '部署', '工程'],
        'productivity': ['method', 'workflow', '效率', '方法', '工作流', 'gtd',
                        'para', '习惯', '时间管理'],
        'psychology': ['psychology', '心理', '认知', '行为', '思维', '情绪'],
        'history': ['history', '历史', '古代', '帝国', '战争', '王朝'],
        'philosophy': ['哲学', 'philosophy', 'stoic', '存在主义', '伦理学'],
    }
    
    for tag, keywords in content_keywords.items():
        if any(kw in body_lower for kw in keywords):
            tags.add(tag)
    
    # 3. 类型特有tag — 不添加冗余type标签（type字段已表达）
    if ftype == 'daily':
        tags.add('journal')  # journal 是daily的附加语义, 保留
    elif ftype == 'book':
        tags.add('reading')
    elif ftype == 'resource':
        tags.add('library')
    # NOTE: daily/project/moc/note 不生成标签 — 与type字段重复
    
    # 4. 扁平tag → 层级化tag (tech/cs, english/phonetics, ...)
    hierarchy_map = {
        'cs': 'tech/cs', 'development': 'tech/development',
        'ai': 'tech/ai', 'algorithm': 'tech/algorithm',
        'rust': 'tech/rust', 'math': 'tech/math',
        'database': 'tech/database', 'computer': 'tech/computer',
        'network': 'tech/network', 'networking': 'tech/network',
        'cs144': 'tech/cs144', 'technology': 'tech/technology',
        'phonetics': 'english/phonetics', '音标': 'english/phonetics',
        '英语': 'english',
    }
    converted = set()
    for t in tags:
        if t in hierarchy_map:
            converted.add(hierarchy_map[t])
        else:
            converted.add(t)
    
    return sorted(converted)


def classify_file(fp: str) -> dict:
    """对单个文件执行完整分类"""
    with open(fp, 'r', encoding='utf-8') as f:
        content = f.read()
    
    fm = {}
    if content.startswith('---'):
        m = re.match(r'^---\s*\n(.*?)\n(?:---|\.\.\.)\n', content, re.DOTALL)
        if m:
            try:
                fm = yaml.safe_load(m.group(1)) or {}
            except:
                pass
    
    rel = os.path.relpath(fp, VAULT)
    body = content
    
    if not content.startswith('---') or not fm:
        return None
    
    ftype = classify_type(body, rel)
    fstatus = classify_status(body, rel, ftype, fm.get('status'))
    ftags = classify_tags(body, rel, ftype)
    
    return {
        'rel': rel,
        'type': ftype,
        'status': fstatus,
        'tags': ftags,
        'old_type': fm.get('type'),
        'old_status': fm.get('status'),
        'old_tags': fm.get('tags', []),
    }


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--file', type=str)
    parser.add_argument('--stats-only', action='store_true')
    args = parser.parse_args()
    
    types = Counter()
    statuses = Counter()
    changed = 0
    errors = 0
    skipped = 0
    
    for root, dirs, files in os.walk(VAULT):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '.git']
        for f in files:
            if not f.endswith('.md'):
                continue
            fp = os.path.join(root, f)
            
            if args.file and args.file not in f:
                continue
            
            result = classify_file(fp)
            if result is None:
                skipped += 1
                continue
            
            types[result['type']] += 1
            statuses[result['status']] += 1
            
            changed_or_skip = result['old_type'] != result['type'] or \
                             result['old_status'] != result['status'] or \
                             result['old_tags'] != result['tags']
            
            if not changed_or_skip and not args.stats_only:
                continue
            
            if args.dry_run or args.stats_only:
                print(f"📄 {result['rel']}")
                print(f"   type: {result['old_type']} → {result['type']}")
                print(f"   status: {result['old_status']} → {result['status']}")
                print(f"   tags: {result['old_tags']} → {result['tags']}")
                continue
            
            try:
                with open(fp, 'r', encoding='utf-8') as fh:
                    orig = fh.read()
                if not orig.startswith('---'):
                    continue
                m = re.match(r'^---\s*\n(.*?)\n(?:---|\.\.\.)\n', orig, re.DOTALL)
                if not m: continue
                old_fm_str = m.group(1)
                old_fm = yaml.safe_load(old_fm_str) or {}
                old_fm['type'] = result['type']
                old_fm['status'] = result['status']
                old_fm['tags'] = result['tags']
                new_fm_str = yaml.dump(old_fm, allow_unicode=True, sort_keys=False,
                                      default_flow_style=False).strip()
                new_content = f'---\n{new_fm_str}\n---\n' + orig[m.end():]
                with open(fp, 'w', encoding='utf-8') as fh:
                    fh.write(new_content)
                changed += 1
            except Exception as e:
                errors += 1
                print(f"  ❌ {result['rel']}: {e}")
    
    print(f"\n📊 {'预览' if args.dry_run else '写入'}完成:")
    print(f"   Type: {dict(types)}")
    print(f"   Status: {dict(statuses)}")
    print(f"   修改: {changed} | 跳过: {skipped} | 错误: {errors}")


if __name__ == '__main__':
    main()