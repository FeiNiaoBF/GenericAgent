#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
anki_connect_utils.py — AnkiConnect API 封装库
唧的工具脚本，简化SOP中的重复操作

用法:
    from anki_connect_utils import Anki
    anki = Anki()
    anki.check_connection()
    anki.add_note("公基错题", "公基错题卡片", {"id":"0001", "question":"...", ...})
"""
from _encoding import setup_utf8; setup_utf8()
import os, sys

import json
import urllib.request
from typing import Optional


class Anki:
    """AnkiConnect API 封装"""
    
    def __init__(self, url: str = "http://localhost:8765", version: int = 6):
        self.url = url
        self.version = version
    
    def invoke(self, action: str, params: Optional[dict] = None) -> dict:
        """基础调用：AnkiConnect JSON-RPC"""
        req = {
            "action": action,
            "version": self.version,
            "params": params or {}
        }
        data = json.dumps(req).encode('utf-8')
        try:
            with urllib.request.urlopen(self.url, data=data, timeout=10) as resp:
                result = json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            raise ConnectionError(f"AnkiConnect连接失败: {e}\n请确认Anki已打开，AnkiConnect已安装")
        
        if result.get('error'):
            raise RuntimeError(f"AnkiConnect错误: {result['error']}")
        return result.get('result')
    
    # ===== 连接 & 牌组 =====
    
    def check_connection(self) -> bool:
        """检查AnkiConnect是否可用"""
        try:
            ver = self.invoke("version")
            print(f"✅ AnkiConnect v{ver} 已连接")
            return True
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False
    
    def list_decks(self) -> list:
        """列出所有牌组名"""
        return self.invoke("deckNames")
    
    def create_deck(self, name: str) -> int:
        """创建牌组（已存在则返回ID）"""
        return self.invoke("createDeck", {"deck": name})
    
    def deck_stats(self, deck_name: str) -> dict:
        """牌组统计信息（返回新卡/学习中/复习计数）"""
        result = self.invoke("getDeckStats", {"decks": [deck_name]})
        # 返回第一个牌组的统计
        if isinstance(result, dict):
            return result
        return result
    
    # ===== 模型 =====
    
    def list_models(self) -> list:
        """列出所有模型名"""
        return self.invoke("modelNames")
    
    def model_fields(self, model_name: str) -> list:
        """列出模型字段名"""
        return self.invoke("modelFieldNames", {"modelName": model_name})
    
    def create_model(self, name: str, fields: list, templates: dict, css: str = "") -> dict:
        """
        创建自定义模型
        templates格式: {"Front": html, "Back": html}
        """
        template_list = []
        for tmpl_name, tmpl_html in templates.items():
            template_list.append({
                "Name": tmpl_name,
                "Front": tmpl_html,
                "Back": tmpl_html if tmpl_name != "Back" else tmpl_html  # 后面会覆盖
            })
        # 修正：分别取Front和Back
        if len(templates) == 2:
            keys = list(templates.keys())
            template_list = [{
                "Name": keys[0],
                "Front": templates[keys[0]],
                "Back": templates[keys[1]]
            }]
        
        return self.invoke("createModel", {
            "modelName": name,
            "inOrderFields": " ".join(fields),
            "css": css,
            "cardTemplates": template_list,
            "isCloze": False
        })
    
    def update_model_templates(self, model_name: str, templates: list) -> None:
        """更新模型模板（含CSS嵌入）"""
        self.invoke("updateModelTemplates", {
            "model": {"name": model_name, "templates": {t["Name"]: t for t in templates}}
        })
        print(f"✅ 模板已更新")
    
    def update_model_styling(self, model_name: str, css: str) -> None:
        """更新模型样式"""
        self.invoke("updateModelStyling", {
            "model": {"name": model_name, "css": css}
        })
        print(f"✅ CSS已更新")
    
    # ===== 笔记操作 =====
    
    def add_note(self, deck_name: str, model_name: str, fields: dict, tags: list = None) -> Optional[int]:
        """
        添加单张笔记
        fields: {"字段名": "值", ...}
        返回: note_id 或 None
        """
        note = {
            "deckName": deck_name,
            "modelName": model_name,
            "fields": fields,
            "tags": tags or []
        }
        try:
            note_id = self.invoke("addNote", {"note": note})
            return note_id
        except RuntimeError as e:
            print(f"❌ 添加失败: {e}")
            return None
    
    def add_notes_batch(self, notes: list) -> list:
        """
        批量添加笔记
        notes: [{"deckName":..., "modelName":..., "fields":..., "tags":...}, ...]
        返回: 成功添加的note_id列表
        """
        note_list = []
        for n in notes:
            note_list.append({
                "deckName": n["deckName"],
                "modelName": n["modelName"],
                "fields": n["fields"],
                "tags": n.get("tags", [])
            })
        result = self.invoke("addNotes", {"notes": note_list})
        success = [r for r in result if r is not None]
        failed = len(result) - len(success)
        print(f"📊 批量添加: {len(success)}成功, {failed}失败")
        return success
    
    def update_note_fields(self, note_id: int, fields: dict) -> None:
        """更新笔记字段"""
        self.invoke("updateNoteFields", {
            "note": {"id": note_id, "fields": fields}
        })
    
    def find_notes(self, query: str) -> list:
        """查询笔记ID列表"""
        return self.invoke("findNotes", {"query": query})
    
    def notes_info(self, note_ids: list) -> list:
        """获取笔记详细信息"""
        return self.invoke("notesInfo", {"notes": note_ids})
    
    def get_max_note_id(self) -> int:
        """获取当前最大笔记ID"""
        notes = self.invoke("findNotes", {"query": ""})
        return max(notes) if notes else 0
    
    def delete_notes(self, note_ids: list) -> None:
        """删除笔记"""
        self.invoke("deleteNotes", {"notes": note_ids})
        print(f"🗑️ 已删除 {len(note_ids)} 张卡片")
    
    # ===== 便捷方法 =====
    
    def verify_note(self, note_id: int, expected_fields: dict = None) -> bool:
        """验证笔记是否添加成功且字段完整"""
        info = self.notes_info([note_id])
        if not info:
            print(f"❌ note_id={note_id} 不存在")
            return False
        note = info[0]
        fields = note.get('fields', {})
        for k, v in fields.items():
            if not v.strip():
                print(f"⚠️ 字段 [{k}] 为空")
                if expected_fields:
                    return False
        if expected_fields:
            for k, v in expected_fields.items():
                actual = fields.get(k, '')
                if actual != v:
                    print(f"❌ 字段 [{k}] 不匹配: 期望='{v[:30]}' 实际='{actual[:30]}'")
                    return False
        print(f"✅ note_id={note_id} 验证通过 ({len(fields)}字段)")
        return True
    
    def add_and_verify(self, deck_name: str, model_name: str, fields: dict, tags: list = None) -> Optional[int]:
        """添加笔记并立即验证（推荐用于单张卡片）"""
        note_id = self.add_note(deck_name, model_name, fields, tags)
        if note_id:
            if self.verify_note(note_id):
                return note_id
            else:
                print(f"⚠️ note_id={note_id} 添加成功但验证未通过")
                return note_id
        return None


# ===== CLI 入口 =====
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AnkiConnect 工具箱")
    parser.add_argument("action", choices=["check", "decks", "models", "stats", "find"],
                        help="执行动作")
    parser.add_argument("--deck", help="牌组名")
    parser.add_argument("--query", help="搜索查询")
    args = parser.parse_args()
    
    anki = Anki()
    
    if args.action == "check":
        anki.check_connection()
    elif args.action == "decks":
        for d in anki.list_decks():
            print(f"  📚 {d}")
    elif args.action == "models":
        for m in anki.list_models():
            print(f"  📋 {m}")
    elif args.action == "stats":
        if not args.deck:
            print("❌ 需要 --deck 参数")
            sys.exit(1)
        stats = anki.deck_stats(args.deck)
        print(json.dumps(stats, indent=2, ensure_ascii=False))
    elif args.action == "find":
        if not args.query:
            print("❌ 需要 --query 参数")
            sys.exit(1)
        notes = anki.find_notes(args.query)
        print(f"找到 {len(notes)} 条: {notes[:10]}...")
