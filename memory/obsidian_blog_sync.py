#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from _encoding import setup_utf8; setup_utf8()
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

# Obsidian 侧博客专用目录：主人指定放在 00.Chronicles —— 时间日志里单独管理
BLOG_SOURCE_DIR = "00.Chronicles/Blog"

# 默认跳过区域；默认只扫描 BLOG_SOURCE_DIR，--legacy 才会扫其它历史位置
SKIP_DIR_NAMES = {".obsidian", "99.System", "88", "03.Library"}

# Tag → Blog目录映射
TAG_MAP = {
    "blog/tech":    "content/blog/",
    "blog/essay":   "content/essay/",
    "blog/project": "content/projects/",
    "blog/novel":   "content/novel/",
    "blog/gaming":  "content/gaming/",
    "blog":         "content/blog/",  # 默认fallback
}

def normalize_tags(tags):
    """把frontmatter里的tags统一成list[str]"""
    if tags is None:
        return []
    if isinstance(tags, str):
        return [tags]
    if isinstance(tags, (list, tuple, set)):
        return [str(t) for t in tags if t]
    return [str(tags)]


def has_blog_tag(tags):
    """只接受 blog 或 blog/xxx，不把非博客tag误判为博客"""
    return any(t == "blog" or t.startswith("blog/") for t in tags)


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
    tags = normalize_tags(fm.get("tags", []))
    
    # 优先匹配最具体的tag
    for tag in sorted(tags, key=len, reverse=True):
        if tag in TAG_MAP:
            return TAG_MAP[tag]
    return None


def validate_frontmatter(fm):
    """发布前校验必要frontmatter字段，返回错误原因列表"""
    errors = []
    if not fm.get("title"):
        errors.append("missing title")
    if fm.get("status") != "published":
        errors.append("status is not published")
    tags = normalize_tags(fm.get("tags", []))
    if not has_blog_tag(tags):
        errors.append("missing blog tag")
    if "archived" in tags:
        errors.append("archived")
    return errors

def convert_to_hugo_frontmatter(fm, body):
    """转换为Hugo Hextra兼容的frontmatter"""
    hugo_fm = {
        "title": fm.get("title", "Untitled"),
        "date": fm.get("created_date", datetime.now().strftime("%Y-%m-%d")),
        "draft": False,
    }
    
    # tags处理：去掉 blog/ 前缀，Hugo侧只保留内容标签，不保留路由标签
    tags = normalize_tags(fm.get("tags", []))
    clean_tags = [t.replace("blog/", "") for t in tags if t and not t.startswith("blog")]
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

def should_skip_dir(path: Path, source_root: Path):
    """判断目录是否应被os.walk跳过，避免误伤 00.Chronicles/Blog"""
    try:
        rel_parts = path.relative_to(source_root).parts
    except ValueError:
        rel_parts = path.parts
    return any(part in SKIP_DIR_NAMES for part in rel_parts)


def iter_markdown_files(source_root: Path):
    """遍历source_root下的Markdown文件，并原地剪枝跳过系统目录"""
    if not source_root.exists():
        return
    for root, dirs, files in os.walk(source_root):
        root_path = Path(root)
        dirs[:] = [d for d in dirs if not should_skip_dir(root_path / d, source_root)]
        for f in files:
            if f.endswith(".md"):
                yield root_path / f


def build_source_roots(include_legacy=False):
    """默认只扫描主人指定的博客目录；legacy模式兼容历史散落博客"""
    vault = Path(VAULT)
    roots = [vault / BLOG_SOURCE_DIR]
    if include_legacy:
        roots.append(vault)
    # 去重并保持顺序
    unique = []
    seen = set()
    for root in roots:
        resolved = root.resolve()
        if resolved not in seen:
            unique.append(root)
            seen.add(resolved)
    return unique


def scan_notes(preview=False, specific_file=None, include_legacy=False):
    """扫描Obsidian vault中可发布的笔记"""
    results = {"published": [], "skipped": [], "errors": []}
    vault = Path(VAULT)
    blog_source = (vault / BLOG_SOURCE_DIR).resolve()
    processed = set()

    for source_root in build_source_roots(include_legacy=include_legacy):
        if not source_root.exists():
            results["errors"].append(f"source not found: {source_root}")
            continue

        for filepath in iter_markdown_files(source_root):
            try:
                resolved = filepath.resolve()
                if resolved in processed:
                    continue
                processed.add(resolved)

                rel_path = filepath.relative_to(vault)

                # legacy模式下仍跳过 00.Chronicles 的非Blog内容，避免发布日记
                if include_legacy:
                    try:
                        is_blog_source = resolved.is_relative_to(blog_source)
                    except AttributeError:
                        is_blog_source = str(resolved).startswith(str(blog_source))
                    if rel_path.parts and rel_path.parts[0] == "00.Chronicles" and not is_blog_source:
                        continue

                # 如果指定了特定文件，只处理匹配的
                if specific_file and specific_file not in str(filepath.stem):
                    continue

                content = filepath.read_text(encoding="utf-8")
                fm, body = parse_frontmatter(content)

                if not fm:
                    continue

                # 发布前校验frontmatter完整性
                validation_errors = validate_frontmatter(fm)
                if validation_errors:
                    tags = normalize_tags(fm.get("tags", []))
                    is_blog_candidate = has_blog_tag(tags)
                    # 普通草稿/非博客笔记不进入报告；只有疑似博客笔记才提示修复原因
                    if not is_blog_candidate or validation_errors == ["status is not published"]:
                        continue
                    results["skipped"].append({"file": str(rel_path), "reason": "; ".join(validation_errors)})
                    continue

                # 检测目标目录
                target_dir = detect_blog_target(fm)
                if not target_dir:
                    results["skipped"].append({"file": str(rel_path), "reason": "no matching tag"})
                    continue

                # 生成slug
                title = fm.get("title", filepath.stem)
                slug = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff_-]', '-', title).strip('-').lower()
                if not slug:
                    results["skipped"].append({"file": str(rel_path), "reason": "empty slug"})
                    continue

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
            except Exception as e:
                try:
                    rel = filepath.relative_to(vault)
                except Exception:
                    rel = filepath
                results["errors"].append(f"{rel}: {type(e).__name__}: {e}")

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
    parser.add_argument("--legacy", action="store_true", help="兼容旧模式：扫描全Vault中带blog标签的历史笔记")
    args = parser.parse_args()
    
    print(f"{'预览模式: 只读不写' if args.preview else '执行模式: 写入Blog'}")
    print(f"扫描范围: {BLOG_SOURCE_DIR}{' + legacy全库兼容' if args.legacy else ''}")
    results = scan_notes(preview=args.preview, specific_file=args.file, include_legacy=args.legacy)
    print_report(results)
    
    if not args.preview and results["published"]:
        print(f"\n提示: 在 Blog 目录运行 'hugo server' 预览效果")