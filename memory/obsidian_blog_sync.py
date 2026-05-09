#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
"""
Obsidian → Hugo Blog 同步脚本
用法:
  python obsidian_blog_sync.py              # 全量同步
  python obsidian_blog_sync.py --preview     # 预览模式(只读不写)
  python obsidian_blog_sync.py --file "标题" # 只同步特定笔记
"""
import os
import re
import shutil
import argparse
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

# === 配置 ===
VAULT = r"D:\Documents_Learn\Personal\Obsidian\Codex Vitae"
BLOG = r"D:\Creative_Studio\WorkSpace\yeekox-blog"

# Tag → Blog目录映射
TAG_MAP = {
    "blog/tech":    "content/blog/",
    "blog/essay":   "content/essay/",
    "blog/project": "content/projects/",
    "blog/novel":   "content/novel/",
    "blog/gaming":  "content/gaming/",
    "blog":         "content/blog/",  # 默认fallback
}

def parse_frontmatter(content):
    """解析Obsidian frontmatter"""
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
    if not m:
        return None, content
    if yaml is None:
        return None, content
    try:
        fm = yaml.safe_load(m.group(1))
    except:
        return None, content
    return fm or {}, m.group(2)

def detect_blog_target(fm):
    """根据tags检测blog发布目标目录"""
    tags = fm.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]
    
    # 优先匹配最具体的tag
    for tag in sorted(tags, key=len, reverse=True):
        if tag in TAG_MAP:
            return TAG_MAP[tag]
    return None

def convert_to_hugo_frontmatter(fm, body):
    """转换为Hugo Hextra兼容的frontmatter"""
    hugo_fm = {
        "title": fm.get("title", "Untitled"),
        "date": fm.get("created_date", datetime.now().strftime("%Y-%m-%d")),
        "draft": False,
    }
    
    # tags处理：去掉 blog/ 前缀
    tags = fm.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]
    clean_tags = [t.replace("blog/", "") for t in tags if not t.startswith("blog")]
    if clean_tags:
        hugo_fm["tags"] = clean_tags
    
    # 清理Obsidian-only语法
    body = re.sub(r'```dataview.*?```', '', body, flags=re.DOTALL)
    body = re.sub(r'\[\[([^\]]+)\]\]', r'\1', body)  # 双链→纯文本
    body = re.sub(r'^---\s*$', '', body, flags=re.MULTILINE)
    
    return hugo_fm, body.strip()

def write_hugo_post(hugo_fm, body, target_dir, slug):
    """写入Hugo post"""
    blog_path = Path(BLOG) / target_dir
    blog_path.mkdir(parents=True, exist_ok=True)
    
    # 文件名: slug.zh-cn.md
    filename = f"{slug}.zh-cn.md"
    filepath = blog_path / filename
    
    # 组装Hugo frontmatter
    fm_lines = ["---"]
    for k, v in hugo_fm.items():
        if k == "title":
            fm_lines.append(f'{k}: "{v}"')
        elif k == "tags" and v:
            fm_lines.append(f"tags:")
            for t in v:
                fm_lines.append(f"  - {t}")
        elif k == "date":
            if isinstance(v, datetime):
                fm_lines.append(f'{k}: {v.strftime("%Y-%m-%dT%H:%M:%S+08:00")}')
            else:
                fm_lines.append(f'{k}: {v}')
        elif k == "draft":
            fm_lines.append(f"{k}: {str(v).lower()}")
        else:
            fm_lines.append(f"{k}: {v}")
    fm_lines.append("---")
    
    content = "\n".join(fm_lines) + "\n\n" + body + "\n"
    
    return filepath, content

def scan_notes(preview=False, specific_file=None):
    """扫描Obsidian vault中可发布的笔记"""
    results = {"published": [], "skipped": [], "errors": []}
    
    for root, dirs, files in os.walk(VAULT):
        # 跳过系统目录
        if any(skip in root for skip in [".obsidian", "99.System", "00.Chronicles", "88"]):
            continue
        # 跳过Library（图书不直接发布）
        if "\\03.Library\\" in root or "/03.Library/" in root:
            continue
            
        for f in files:
            if not f.endswith(".md"):
                continue
                
            filepath = Path(root) / f
            rel_path = filepath.relative_to(VAULT)
            
            # 如果指定了特定文件，只处理匹配的
            if specific_file and specific_file not in str(filepath.stem):
                continue
            
            content = filepath.read_text(encoding="utf-8")
            fm, body = parse_frontmatter(content)
            
            if not fm:
                continue
            
            # 检查发布条件
            status = fm.get("status", "")
            tags = fm.get("tags", [])
            if isinstance(tags, str):
                tags = [tags]
            
            if status != "published":
                continue
            if not any("blog" in t for t in tags):
                continue
            if "archived" in tags:
                results["skipped"].append({"file": str(rel_path), "reason": "archived"})
                continue
            
            # 检测目标目录
            target_dir = detect_blog_target(fm)
            if not target_dir:
                results["skipped"].append({"file": str(rel_path), "reason": "no matching tag"})
                continue
            
            # 生成slug
            title = fm.get("title", filepath.stem)
            slug = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff_-]', '-', title).strip('-').lower()
            
            # 转换
            hugo_fm, clean_body = convert_to_hugo_frontmatter(fm, body)
            blog_filepath, hugo_content = write_hugo_post(hugo_fm, clean_body, target_dir, slug)
            
            if preview:
                results["published"].append({
                    "file": str(rel_path),
                    "blog_target": str(blog_filepath.relative_to(BLOG)),
                    "preview": hugo_content[:200] + "..."
                })
            else:
                blog_filepath.write_text(hugo_content, encoding="utf-8")
                results["published"].append({
                    "file": str(rel_path),
                    "blog_target": str(blog_filepath.relative_to(BLOG)),
                    "status": "written"
                })
    
    return results

def print_report(results):
    print(f"\n{'='*50}")
    print(f"[报告] 发布报告")
    print(f"{'='*50}")
    print(f"[OK] 已发布: {len(results['published'])}")
    for r in results['published']:
        print(f"   [FILE] {r['file']}")
        print(f"      -> {r['blog_target']}")
        if 'preview' in r:
            print(f"      [PREVIEW] {r['preview']}")
    print(f"[SKIP] 跳过: {len(results['skipped'])}")
    for r in results['skipped']:
        print(f"   {r['file']} ({r['reason']})")
    print(f"[ERR] 错误: {len(results['errors'])}")
    for r in results['errors']:
        print(f"   {r}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Obsidian → Blog同步工具")
    parser.add_argument("--preview", action="store_true", help="预览模式")
    parser.add_argument("--file", type=str, help="只处理特定笔记(标题关键词)")
    args = parser.parse_args()
    
    print(f"{'预览模式: 只读不写' if args.preview else '执行模式: 写入Blog'}")
    results = scan_notes(preview=args.preview, specific_file=args.file)
    print_report(results)
    
    if not args.preview and results["published"]:
        print(f"\n💡 提示: 在 Blog 目录运行 'hugo server' 预览效果")