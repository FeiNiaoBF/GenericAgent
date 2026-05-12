#!/usr/bin/env python3
"""Obsidian博客同步 - 将Obsidian笔记同步到博客

SOP: obsidian_blog_sync_sop.md
用途: 将Obsidian中标记的笔记同步发布到yeekox博客
DIY: 一个脚本只做博客同步
"""

import os, sys, json

VAULT_BLOG_DIR = 'D:\Creative_Studio\WorkSpace\Github\GenericAgent\05.Knowledge\05.Blog'

def sync_post(filepath):
    """同步单篇博文"""
    if not os.path.exists(filepath):
        print('❌ 文件不存在: %s' % filepath)
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取frontmatter
    lines = content.split('\n')
    frontmatter = {}
    if lines[0].strip() == '---':
        end = 1
        while end < len(lines) and lines[end].strip() != '---':
            end += 1
        for line in lines[1:end]:
            if ':' in line:
                key, val = line.split(':', 1)
                frontmatter[key.strip()] = val.strip()
    
    title = frontmatter.get('title', os.path.basename(filepath).replace('.md', ''))
    print('📤 同步博文: %s' % title)
    print('   标签: %s' % frontmatter.get('tags', '无'))
    print('   状态: %s' % ('📝 草稿' if frontmatter.get('draft') == 'true' else '✅ 发布就绪'))
    print()
    print('⚠️ 需要配置博客API信息')
    return True

def list_pending():
    """列出待同步的博文"""
    if not os.path.exists(VAULT_BLOG_DIR):
        print('⚠️ 博客目录不存在: %s' % VAULT_BLOG_DIR)
        return []
    
    posts = []
    for f in os.listdir(VAULT_BLOG_DIR):
        if f.endswith('.md'):
            posts.append(f)
    
    print('📋 待同步博文 (%d篇):' % len(posts))
    for p in posts:
        print('  📄 %s' % p)
    return posts

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Obsidian博客同步')
    parser.add_argument('action', choices=['sync', 'list'], help='操作')
    parser.add_argument('--file', help='文件路径')
    args = parser.parse_args()

    if args.action == 'list':
        list_pending()
    elif args.action == 'sync':
        if not args.file:
            print('❌ sync需要 --file')
            sys.exit(1)
        sync_post(args.file)

if __name__ == '__main__':
    main()
