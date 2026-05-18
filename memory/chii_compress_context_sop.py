#!/usr/bin/env python3
"""Chii压缩 - 压缩归档Chii记忆

SOP: chii_compress_context_sop.md
用途: 压缩记忆/日志文件，保留最近内容，归档旧数据
DIY: 一个脚本只做压缩归档
"""

import os, json, gzip, shutil, datetime

DEFAULT_ARCHIVE_DIR = 'D:\Creative_Studio\WorkSpace\Github\GenericAgent\memory\archives'

def compress_file(filepath, archive_dir=None):
    """压缩单个文件到归档目录"""
    if not os.path.exists(filepath):
        print(f'❌ 文件不存在: {filepath}')
        return None
    
    archive_dir = archive_dir or DEFAULT_ARCHIVE_DIR
    os.makedirs(archive_dir, exist_ok=True)
    
    basename = os.path.basename(filepath)
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    archive_name = f'{basename}_{timestamp}.gz'
    archive_path = os.path.join(archive_dir, archive_name)
    
    with open(filepath, 'rb') as f_in:
        with gzip.open(archive_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    
    orig_size = os.path.getsize(filepath)
    comp_size = os.path.getsize(archive_path)
    ratio = comp_size / orig_size * 100 if orig_size > 0 else 0
    
    print(f'✅ 压缩完成: {archive_name}')
    print(f'   {orig_size} bytes → {comp_size} bytes ({ratio:.1f}%)')
    return archive_path

def compress_memory():
    """压缩global_mem等记忆文件"""
    mem_dir = 'D:\Creative_Studio\WorkSpace\Github\GenericAgent\memory'
    targets = ['global_mem.txt', 'global_mem_insight.txt']
    
    for f in targets:
        fpath = os.path.join(mem_dir, f)
        if os.path.exists(fpath):
            compress_file(fpath)
    
    print('✨ 记忆压缩完成!')

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Chii记忆压缩工具')
    parser.add_argument('file', nargs='?', help='单个文件路径(留空则压缩默认记忆文件)')
    parser.add_argument('--archive-dir', help='归档目录')
    args = parser.parse_args()

    if args.file:
        compress_file(args.file, args.archive_dir)
    else:
        compress_memory()

if __name__ == '__main__':
    main()
