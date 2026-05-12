#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from _encoding import setup_utf8; setup_utf8()
"""
anki_export.py — 从 Obsidian Vault 提取公基错题，生成 Anki .apkg 文件

用法:
  python anki_export.py                     # 扫描所有错题 → 生成错题卡片.apkg
  python anki_export.py --dry-run           # 预览卡片，不生成文件
  python anki_export.py --output "自定义.apkg"  # 指定输出文件名

错题笔记格式 (SOP):
  - 笔记tags含 #公基 和 #错题
  - 正文含 ##🐛错题 section
  - 每条错题格式:
    ### 📋 题目
    题目内容...
    ✅ **答案**: A/B/C/D
    📝 **逐项解析**:
    - A. ✅ 正确/❌ 错误 解析...
    💡 **延伸**: 知识点扩展...
"""

import os
import re
import sys
import argparse
from pathlib import Path

try:
    import genanki
except ImportError:
    print("❌ genanki 未安装，请先: pip install genanki")
    sys.exit(1)

VAULT = r"D:\Documents_Learn\Personal\Obsidian\Codex Vitae"

# ── Anki Model ──
MODEL_ID = 1607392319  # 固定ID，避免重复生成
DECK_ID = 2059400110   # 固定ID

QUIZ_MODEL = genanki.Model(
    MODEL_ID,
    '公基错题卡片',
    fields=[
        {'name': 'Question'},
        {'name': 'Answer'},
        {'name': 'Explanation'},
        {'name': 'Extension'},
        {'name': 'SourceNote'},
    ],
    templates=[{
        'name': '错题卡片',
        'qfmt': '''
<div class="source">{{SourceNote}}</div>
<div class="question">{{Question}}</div>
''',
        'afmt': '''
{{FrontSide}}
<hr id="answer">
<div class="answer">✅ {{Answer}}</div>
<div class="explanation">📝 {{Explanation}}</div>
{{#Extension}}
<div class="extension">💡 {{Extension}}</div>
{{/Extension}}
''',
    }],
    css='''
.card {
    font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
    font-size: 16px;
    color: #2e3338;
    padding: 20px;
    max-width: 600px;
}
.source {
    font-size: 12px;
    color: #888;
    margin-bottom: 10px;
    padding: 4px 8px;
    background: #f0f0f0;
    border-radius: 4px;
    display: inline-block;
}
.question {
    font-size: 18px;
    font-weight: bold;
    margin: 15px 0;
    line-height: 1.6;
}
.answer {
    font-size: 16px;
    font-weight: bold;
    color: #2d8cf0;
    margin: 10px 0;
}
.explanation {
    font-size: 15px;
    line-height: 1.8;
    margin: 10px 0;
    padding: 12px;
    background: #f8f9fa;
    border-left: 3px solid #2d8cf0;
    border-radius: 4px;
}
.extension {
    font-size: 14px;
    color: #666;
    margin-top: 12px;
    padding: 10px;
    background: #fff8e1;
    border-left: 3px solid #ffb300;
    border-radius: 4px;
}
'''
)


def find_quiz_notes(vault_path: str) -> list:
    """扫描vault中所有含 #公基 和 #错题 标签的 .md 文件"""
    vault = Path(vault_path)
    quiz_notes = []
    for md in vault.rglob("*.md"):
        try:
            content = md.read_text(encoding="utf-8")
        except Exception:
            continue
        # 检查frontmatter中的tags
        tags_block = ""
        if content.startswith("---"):
            end = content.find("---", 3)
            if end > 0:
                tags_block = content[3:end].lower()
        # 也检查正文中的 #错题 标签
        has_gongji = "公基" in tags_block or "#公基" in content[:200]
        has_quiz = "错题" in tags_block or "#错题" in content[:200]
        if has_gongji and has_quiz:
            quiz_notes.append((md, content))
    return quiz_notes


def parse_quiz_items(content: str, source_name: str) -> list:
    """从错题笔记中提取每条错题，返回卡片数据列表
    
    支持两种格式:
    1. ### 📋 题目 格式（详细卡片式）
    2. Markdown表格格式（简洁记录式）
    """
    cards = []
    
    # 找 ## 🐛 错题 section（兼容有无空格）
    quiz_section_match = re.search(
        r'##\s*🐛\s*错题\s*\n(.*?)(?=\n##\s|\Z)',
        content, re.DOTALL
    )
    if not quiz_section_match:
        return cards
    
    section = quiz_section_match.group(1)
    
    # 检查是否包含 ### 📋 题目 格式
    if '### 📋 题目' in section:
        # 按 ### 📋 题目 分割每条错题
        items = re.split(r'###\s*📋\s*题目\s*\n', section)
        
        for item in items:
            item = item.strip()
            if not item:
                continue
            
            # 提取题目（到第一个 ✅ 或 📝 之前）
            question_match = re.match(r'(.*?)(?=✅|📝)', item, re.DOTALL)
            question = question_match.group(1).strip() if question_match else item.split('\n')[0]
            
            # 提取答案
            answer_match = re.search(r'✅\s*\*?\*?答案\*?\*?\s*[:：]\s*(.+?)(?=\n|$)', item)
            answer = answer_match.group(1).strip() if answer_match else "?"
            
            # 提取解析（✅ 答案行之后到 💡 之间）
            explanation = ""
            expl_match = re.search(
                r'📝\s*\*?\*?逐项解析\*?\*?\s*[:：]?\s*\n(.*?)(?=💡|\Z)',
                item, re.DOTALL
            )
            if expl_match:
                explanation = expl_match.group(1).strip()
            
            # 提取延伸
            extension = ""
            ext_match = re.search(r'💡\s*\*?\*?延伸\*?\*?\s*[:：]?\s*\n?(.*?)(?=\Z)', item, re.DOTALL)
            if ext_match:
                extension = ext_match.group(1).strip()
            
            if question:
                # 清理Markdown格式（保留基本结构）
                question = re.sub(r'\*\*(.+?)\*\*', r'\1', question)
                cards.append({
                    'question': question,
                    'answer': answer,
                    'explanation': explanation or "暂无解析",
                    'extension': extension,
                    'source': source_name,
                })
    else:
        # 解析Markdown表格格式
        # 匹配表格行：| 日期 | 题目关键词 | 错因 | 来源 |
        table_rows = re.findall(
            r'\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|',
            section
        )
        
        for date, keyword, reason, source_ref in table_rows:
            # 跳过表头分隔行
            if '---' in date or '日期' in date:
                continue
            
            # 构造卡片：用笔记标题+关键词作为题目，原因作为答案
            question = f"[{source_name}] {keyword}"
            answer = reason
            explanation = f"日期：{date}\n来源：{source_ref}"
            
            cards.append({
                'question': question.strip(),
                'answer': answer.strip(),
                'explanation': explanation.strip(),
                'extension': '',
                'source': source_name,
            })
    
    return cards


def build_deck(cards: list, deck_name: str = "公基错题集") -> genanki.Deck:
    """构建Anki Deck"""
    deck = genanki.Deck(DECK_ID, deck_name)
    for i, card in enumerate(cards):
        # 用内容哈希生成稳定ID，避免重复
        note_id = abs(hash(card['question'][:50])) % (10**10)
        note = genanki.Note(
            model=QUIZ_MODEL,
            fields=[
                card['question'],
                card['answer'],
                card['explanation'],
                card['extension'],
                card['source'],
            ],
            guid=genanki.guid_for(card['question'][:50] + card['answer'])
        )
        deck.add_note(note)
    return deck


def main():
    parser = argparse.ArgumentParser(description="Obsidian 公基错题 → Anki")
    parser.add_argument("--dry-run", action="store_true", help="预览不生成文件")
    parser.add_argument("--output", "-o", default="公基错题卡片.apkg", help="输出文件名")
    parser.add_argument("--vault", default=VAULT, help="Vault路径")
    args = parser.parse_args()

    print(f"🔍 扫描 Vault: {args.vault}")
    notes = find_quiz_notes(args.vault)
    print(f"📄 找到 {len(notes)} 个错题笔记")

    all_cards = []
    for md_path, content in notes:
        source = md_path.stem  # 文件名作来源
        cards = parse_quiz_items(content, source)
        if cards:
            print(f"  ✅ {source}: {len(cards)} 条错题")
        else:
            print(f"  ⚠️ {source}: 未找到标准格式错题")
        all_cards.extend(cards)

    print(f"\n📊 共提取 {len(all_cards)} 条错题卡片")

    if args.dry_run:
        print("\n--- 预览前3条 ---")
        for c in all_cards[:3]:
            print(f"\n📋 {c['question'][:80]}...")
            print(f"✅ {c['answer']}")
            print(f"📝 {c['explanation'][:100]}...")
        return

    deck = build_deck(all_cards)
    output_path = Path(args.output)
    genanki.Package(deck).write_to_file(str(output_path))
    print(f"\n🎉 已生成: {output_path.resolve()}")
    print(f"   共 {len(all_cards)} 张卡片，双击 .apkg 导入 Anki")


if __name__ == "__main__":
    main()
