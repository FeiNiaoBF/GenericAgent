# AnkiConnect SOP (v3.0 · 2026-05-11)

> 前提：Anki已安装AnkiConnect插件，端口8765
> **首选工具**：`anki_connect_utils.py`（封装完整API，所有操作优先用它）

## 1. 快速上手（utils）

```python
import sys; sys.path.insert(0, r"D:\Creative_Studio\WorkSpace\Github\GenericAgent\memory")
from anki_connect_utils import Anki

anki = Anki()
anki.check_connection()        # 检查连接
anki.list_decks()              # 列牌组
anki.list_models()             # 列模型
anki.model_fields("公基错题")   # 查字段
anki.find_notes("deck:公基错题") # 查笔记
anki.add_note(deck, model, fields, tags)  # 添加笔记
anki.update_model_styling(model, css)      # 推送CSS
anki.update_model_templates(model, templates) # 推送模板
anki.deck_stats("公基错题")     # 牌组统计
```

## 2. 核心原则：三步闭环

```
① 读当前状态 → ② 修改推送 → ③ 读回验证（必须！）
```

- 读回验证：推送后立即用读API重新获取，对比确认内容已变更
- 跳过验证 = 半盲操作，禁止
- API偶发返回null → 重试而非报错

## 3. CSS 推送要点

- CSS必须裸写，**不用** `<style>` 包裹
- 选择器class名必须与模板HTML中的class**完全匹配**（先读模板再写CSS）
- 模板内可能有内联`<style>`标签，两种来源都要检查，避免冲突

## 4. 响应式设计（Anki WebView特化）

### 居中（双重保险，缺一不可）
```css
.card { max-width:600px; width:100%; margin:0 auto; box-sizing:border-box; }
```

### 选择题模板关键class
- `.option-item` 选项容器（需设 `display: block` 确保可见）
- `.option-text` 选项文字（**不能遗漏此规则，否则选项不显示**）

### 通用规则
- 子元素用百分比/rem，**禁用固定px宽度**
- 手机+电脑都要测试

## 5. 典型坑

| 坑 | 解法 |
|---|------|
| CSS推送成功但不生效 | 检查class名匹配 + 有无`<style>`包裹 |
| 选项不显示 | 确保 `.option-text` 有完整CSS规则 |
| 卡片不居中 | body flex + .card margin:auto 双重保险 |
| 卡片大小不统一 | 统一 max-width:600px + width:100% |
| API返回null | AnkiConnect偶发，重试而非报错 |

## 🛑 验证门禁
用utils而非裸HTTP？| 三步闭环？| class名匹配模板？| option-text规则完整？
`VERDICT: PASS` / `VERDICT: FAIL`
