# Vision API SOP

## 执行摘要（≥1步执行前必读）
1. 分级决策：窗口标题可读→不截图 | 本地OCR→不调API | 局部截图→不截整窗口
2. 调API：`ask_vision(image, prompt, backend="claude")` ← 最后手段
3. 结果验证：检查返回非`Error:` + 内容与prompt对齐 → 🛑 过验证门禁

## `<contract>`
```
需要看图/识别 →
├─ 窗口标题能读到 → 不截图
├─ 本地OCR能读到 → 不调API
├─ 能截局部(标题栏/按钮区) → 不截整窗口
└─ 以上都不行 → vision_api.py (最后手段)
```

### `<guardrails>`
```
❌ 禁全屏截图 — 任何场景下都不允许
❌ 禁不枚举窗口直接截图 — 先 pygetwindow.getWindowsWithTitle()
✅ 截图前确认窗口在前台 — ljqCtrl 激活
✅ max_pixels ≤ 1,440,000
```

## ⚠️ 前置规则（必须遵守）

1. **先枚举窗口**：调用 vision 前必须先用 `pygetwindow` 枚举窗口标题，确认目标窗口存在且已激活到前台。窗口不存在就不要截图。
2. **🚫 禁止全屏截图**：必须先利用ljqCtrl截取窗口区域。能截局部（如标题栏）就不截整窗口，能截窗口就绝不全屏。全屏截图在任何场景下都不允许。
3. **能不用 vision 就不用**：如果窗口标题/本地 OCR（`ocr_utils.py`）能获取所需信息，就不要调用 vision API，省 token 且更可靠。Vision 是最后手段。

## 快速用法

```python
from vision_api import ask_vision
result = ask_vision(image, prompt="描述图片内容", backend="claude", timeout=60, max_pixels=1_440_000)
# image: 文件路径(str/Path) 或 PIL Image
# backend: 'claude'(默认) | 'openai' | 'modelscope'
# 返回 str：成功为模型回复，失败为 'Error: ...'
```

## 如果没有 `vision_api.py`，初次构建vision能力

1. 复制 `memory/vision_api.template.py` → `memory/vision_api.py`
2. 只改头部"用户配置区"：去 `mykey.py` 里扫描变量名（⚠️ 只看名字，禁止输出 apikey 值），尝试找能用配置名填入 `CLAUDE_CONFIG_KEY` / `OPENAI_CONFIG_KEY`，`DEFAULT_BACKEND` 选后端，并测试
3. 保底：没有可用 config 时去 `https://modelscope.cn/my/myaccesstoken` 申请 token 填入 `MODELSCOPE_API_KEY`

## 🛑 验证门禁
| 检查项 | PASS条件 | FAIL处理 | 状态 |
|--------|---------|---------|------|
| 分级决策已执行 | 窗口标题/本地OCR/局部截图三关已试 | 回退到前一级 | |
| API调用合法 | 返回非`Error:`开头 | 检查backend/token | |
| 结果与prompt对齐 | 返回内容回答了prompt问题 | 调整prompt重试 | |

最终裁定：`VERDICT: PASS` / `VERDICT: FAIL`
