# [TG Sticker SOP · L3] (v1.0)

## 执行摘要（≥1步执行前必读）
① 准备512x512 PNG贴纸→② Bot API上传(包名必须`_by_<bot_username>`后缀)→③ 公开包通过`t.me/addstickers`安装 → 🛑 过验证门禁

## §1 概述
Telegram 贴纸包可通过 Bot API 直接创建/管理（不使用 @Stickers 机器人）。包名后缀必须 `_by_<bot_username>`，公开贴纸包通过 `t.me/addstickers/<pack_name>` 安装。

## §2 贴纸规格要求
| 维度 | 要求 | 验证方法 |
|------|------|----------|
| 格式 | PNG (RGBA) | PIL `img.mode == 'RGBA'` |
| 尺寸 | 必须 512×512 px | PIL `img.size` |
| 大小 | ≤ 512KB (Telegram limit) | `os.path.getsize()` |
| 一侧尺寸 | 严格512px，非512则缩放 | PIL `img.resize((512,512))` |

## §3 PTB 22.7 贴纸 API
### 3.1 创建贴纸包
```python
from telegram import Bot, InputSticker
from telegram.constants import StickerFormat, StickerType

bot = Bot(token)
# InputSticker: format 参数必须显式传入（PTB 22.7 required）
stickers = [InputSticker(sticker=file_bytes, emoji_list=["😉"], format=StickerFormat.STATIC)]

await bot.create_new_sticker_set(
    user_id=user_id,          # 用户数字ID（非@username）
    name=pack_name,           # 如 "MyPack_by_mybot"
    title=pack_title,         # 显示名称如 "My Stickers"
    stickers=stickers,        # 一次性上传全部（≤120张）
    sticker_type=StickerType.REGULAR,
)
```
### 3.2 检查已有包
```python
try:
    existing = await bot.get_sticker_set(pack_name)
    print(f"Found: {len(existing.stickers)} stickers")
except Exception:
    print("Pack not found")
```

## §4 避坑清单
### 4.1 API 参数坑（PTB 22.7）
- ❌ `InputSticker` **必须**传 `format=StickerFormat.STATIC`（required pos arg）
- ❌ `create_new_sticker_set` **不接受** `sticker_format` 参数（format由InputSticker推断）
- ❌ 不能分步：TG API要求首次创建一次性传完所有贴纸

### 4.2 PEER_ID_INVALID 错误
- 原因：bot 从未与目标用户交互过
- 解决：用户先给 bot 发送 `/start`

### 4.3 文件名匹配陷阱
- **优先用动态扫描**，不硬编码文件名
- `repr()` 检查隐藏字符（Unicode省略号 `…` vs ASCII点 `...` 肉眼不可区分）
- 策略：`os.listdir()` → `sorted()` → 按索引匹配映射

## §5 标准创建流程
1. **验证图片**：PIL 检查尺寸/格式/大小，不符合则 resize
2. **确定包名**：`<name>_by_<bot_username>`，检查是否已被占用
3. **映射 emoji**：按文件排序后，逐张指定 emoji（每个贴纸 1-3 个）
4. **上传**：一次性 `create_new_sticker_set`
5. **验证**：`get_sticker_set` 确认数量
6. **发布链接**：`t.me/addstickers/<pack_name>`

## §6 tgapp.py 集成
已有 `/stickerset <pack_name>` 命令，调用 `_import_sticker_set` 从公开贴纸包导入到 `/addstickers` 快捷安装。实现在 `tgapp.py` handle_command 中。

## §7 已知包
| 包名 | 标题 | 数量 | 创建日期 |
|------|------|------|----------|
| `ChiChiStickers_by_ohchii_bot` | ChiChi Stickers | 20 | 2026-04-30 |

## 🛑 验证门禁（执行前/后强制检查）

| 检查项 | 状态 |
|--------|------|
| 贴纸512x512 PNG透明背景？ | |
| 包名以`_by_<bot_username>`结尾？ | |
| emoji映射已设置？ | |
| 公开包可通过t.me/addstickers安装？ | |

最终裁定：`VERDICT: PASS` / `VERDICT: FAIL`