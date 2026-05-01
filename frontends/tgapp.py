import os, sys, re, threading, asyncio, queue as Q, time, random, uuid, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'temp')
from agentmain import GeneraticAgent
try:
    from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.constants import ChatType, MessageLimit, ParseMode
    from telegram.error import RetryAfter
    from telegram.ext import ApplicationBuilder, CallbackQueryHandler, MessageHandler, filters, ContextTypes
    from telegram.request import HTTPXRequest
except:
    print("Please ask the agent install python-telegram-bot to use telegram module.")
    sys.exit(1)
from chatapp_common import (
    FILE_HINT,
    HELP_TEXT,
    TELEGRAM_MENU_COMMANDS,
    clean_reply,
    ensure_single_instance,
    extract_files,
    format_restore,
    redirect_log,
    require_runtime,
    split_text,
)
from continue_cmd import handle_frontend_command, reset_conversation
from llmcore import mykeys
from frontends.tg_formatter import (
    safe_format as tg_safe_format,
    to_telegram_html,
)

agent = GeneraticAgent()
agent.verbose = False
agent.inc_out = True
ALLOWED = set(mykeys.get('tg_allowed_users', []))

# ───── 唧 (Chii) 人格化随机池 ─────
_CHII_THINK = [
    "えっと…ちょっと考え中なの…",
    "ん…待ってね、なの",
    "ちっ…ちい…考えてるところです",
    "唧、今頑張ってるです！",
    "ちょっとだけ…待ってほしいなの",
    "あの…もうすぐできると思うなの",
    "むむ…これ、どうかな…なの",
    "すこし時間かかるかも…ごめんね",
    "えへへ…考えごとしてるです",
    "わかった、なの！ちょっと考えるね",
    "しゅくだい、やってます…なの",
    "ん〜…ちょっと待ってね、なの",
]

_CHII_FILE = [
    "できた、なの！",
    "しゅくだい完成です〜",
    "じゃーん！できたよ、なの",
    "はい、これです！",
    "ファイル作れたの！えへへ",
    "できあがり…なの！",
]

_CHII_EMPTY = [
    "…ちっ？",
    "…あれ？なの",
    "…む？",
    "…え？",
    "…ちい？",
    "…うーん？",
]

_CHII_ERROR = [
    "ちげー！なんか変なの…ごめんね",
    "うぅ…失敗しちゃった…なの",
    "あわわ…ごめんなさい、なの…",
    "うー…もう一回やってみる？",
    "えっと…エラー出ちゃった…直すね",
]

_CHII_SUFFIX = [
    " …なの",
    " …です",
    " …ちっ",
    " …むむ",
    " …えっとね",
]

def _chii_think():
    return random.choice(_CHII_THINK)

def _chii_suffix():
    return random.choice(_CHII_SUFFIX)
# ────────────────────────────────────
_STREAM_SEGMENT_LIMIT = max(1200, MessageLimit.MAX_TEXT_LENGTH - 256)
_STREAM_UPDATE_INTERVAL_SECONDS = 2.0
_STREAM_MIN_UPDATE_CHARS = 400
_RETRY_AFTER_MARGIN_SECONDS = 1.0
_QUEUE_WAIT_SECONDS = 1
_ASK_USER_HOOK_KEY = "telegram_ask_user_menu"
_ASK_CALLBACK_PREFIX = "ask:"
_ASK_CANCEL_ACTION = "none"
_ASK_CANCEL_LABEL = "none of these above"
_ASK_CANCEL_PROMPT = "已取消选择，请直接发送下一步操作。"
_ask_menu_events = Q.Queue()
_ask_menu_store = {}
_STICKER_STORE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tg_sticker_store.json')
_QUOTE_OPEN_TAG = "<_quote_>"
_QUOTE_CLOSE_TAG = "</_quote_>"
# MarkdownV2 conversion now handled by tg_formatter.to_telegram_html()
_TURN_MARKER_RE = re.compile(r"^\*{0,2}LLM Running \(Turn (\d+)\) \.\.\.\*{0,2}\s*$")
_CODE_FENCE_RE = re.compile(r"^\s*(`{3,})(.*)$")
_TURN_SUMMARY_LIMIT = 160
_TURN_SUMMARY_RE = re.compile(r"<summary>\s*(.*?)\s*</summary>", re.DOTALL)
_TURN_SUMMARY_SEARCH_STRIP_RE = re.compile(r"`{3,}[\s\S]*?`{3,}|<thinking>[\s\S]*?</thinking>", re.DOTALL)

def _make_draft_id():
    return random.randint(1, 2**31 - 1)

# --- sticker store helpers ---
def _load_sticker_store():
    try:
        with open(_STICKER_STORE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {"version": 1, "stickers": {}}

def _save_sticker_store(store):
    try:
        with open(_STICKER_STORE_PATH, 'w', encoding='utf-8') as f:
            json.dump(store, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[sticker] save error: {e}", flush=True)

def _store_sticker(file_id, emoji, user_id):
    store = _load_sticker_store()
    emoji = emoji or "❓"
    if emoji not in store["stickers"]:
        store["stickers"][emoji] = []
    # avoid duplicates
    if any(s.get("file_id") == file_id for s in store["stickers"][emoji]):
        return
    store["stickers"][emoji].append({
        "file_id": file_id,
        "added_by": user_id,
        "added_at": time.strftime("%Y-%m-%d %H:%M:%S")
    })
    _save_sticker_store(store)

def _get_stickers_by_emoji(emoji):
    store = _load_sticker_store()
    return store["stickers"].get(emoji, [])

def _get_all_stickers():
    store = _load_sticker_store()
    all_stickers = []
    for emoji, stickers in store["stickers"].items():
        all_stickers.extend(stickers)
    return all_stickers

def _get_random_sticker():
    all_s = _get_all_stickers()
    return random.choice(all_s) if all_s else None

async def _import_sticker_set(bot, set_name, user_id):
    """Import all stickers from a public sticker set using Bot API.
    Returns (count, emoji_list_str) on success, or (0, error_msg) on failure."""
    try:
        ss = await bot.get_sticker_set(set_name)
    except Exception as e:
        err = str(e)
        if "STICKERSET_INVALID" in err or "not found" in err.lower():
            return 0, f"找不到贴纸包 `{set_name}`，请确认名称正确（区分大小写，不含空格）"
        return 0, f"获取贴纸包失败：{err[:200]}"
    count = 0
    emojis = set()
    for sticker in ss.stickers:
        emoji = sticker.emoji or "❤️"
        file_id = sticker.file_id
        _store_sticker(file_id, emoji, user_id)
        emojis.add(emoji)
        count += 1
    return count, f"成功导入 **{ss.title}**（{ss.name}）的 {count} 张贴纸！包含 emoji：{' '.join(sorted(emojis)[:20])}{'...' if len(emojis) > 20 else ''}"

def _visible_segments(text):
    text = (text or "").strip()
    if not text:
        return []
    segments = []
    for part in split_text(text, _STREAM_SEGMENT_LIMIT):
        segments.extend(_markdown_safe_segments(part))
    return segments

def _markdown_safe_segments(text, limit=None):
    limit = limit or MessageLimit.MAX_TEXT_LENGTH
    text = (text or "").strip()
    if not text:
        return []
    if len(to_telegram_html(text)) <= limit:
        return [text]
    parts = []
    remaining = text
    while remaining:
        if len(to_telegram_html(remaining)) <= limit:
            parts.append(remaining)
            break
        low, high, best = 1, len(remaining), 1
        while low <= high:
            mid = (low + high) // 2
            if len(to_telegram_html(remaining[:mid].rstrip() or remaining[:mid])) <= limit:
                best = mid
                low = mid + 1
            else:
                high = mid - 1
        cut = remaining.rfind("\n", 0, best)
        if cut < max(1, best * 0.6):
            cut = best
        chunk = remaining[:cut].rstrip() or remaining[:best]
        parts.append(chunk)
        remaining = remaining[len(chunk):].lstrip()
    return parts

# Table conversion handled by tg_formatter.to_telegram_html()

def _beautify_tg_message(text):
    """TG-specific: convert markdown headings to bold+emoji, fix spacing.
    Only touches tgapp.py path; other frontends unaffected."""
    if not text or not text.strip():
        return text

    EMOJI_MAP = {
        "总结": "📋", "摘要": "📋", "关键": "🔑", "重点": "⭐",
        "错误": "❌", "警告": "⚠️", "注意": "⚠️", "问题": "❓",
        "步骤": "📝", "操作": "🔧", "执行": "▶️", "完成": "✅",
        "结果": "📊", "数据": "📊", "统计": "📈",
        "文件": "📁", "生成": "📄", "创建": "📄",
        "代码": "💻", "命令": "⌨️", "配置": "⚙️",
        "帮助": "🆘", "信息": "ℹ️", "状态": "🔍",
        "计划": "📅", "任务": "📌", "进度": "🚧",
        "回复": "💬", "消息": "💬",
        "新闻": "📰", "今日": "📅", "日记": "📔",
    }

    lines = text.split("\n")
    result = []
    in_code = False
    prev_blank = True
    section_n = 0

    for line in lines:
        stripped = line.strip()
        is_blank = not stripped
        is_fence = stripped.startswith("```")
        mh = re.match(r"^(#{1,4})\s+(.*)", stripped)
        is_hrule = bool(re.match(r"^[─━═\-_]{3,}$", stripped))

        if is_fence:
            if in_code and not prev_blank and result:
                result.append("")
            in_code = not in_code
            result.append(line)
            if not in_code:
                result.append("")
            prev_blank = True
            continue

        if is_hrule:
            # Skip ASCII hrules — TG doesn’t render them well
            continue

        if in_code:
            result.append(line)
            prev_blank = is_blank
            continue

        if is_blank:
            result.append("")
            prev_blank = True
            continue

        if mh:
            section_n += 1
            hashes, header = mh.group(1), mh.group(2)
            # Already has emoji or bold formatting → keep as-is
            if re.search(r"[\U0001F300-\U0001F9FF\u2600-\u27BF]", header) or \
               re.match(r"^\*\*.*\*\*$", header):
                result.append(f"{hashes} {header}")
                prev_blank = False
                continue
            # Pick emoji by keyword match
            emoji = "🔹"
            for kw, em in EMOJI_MAP.items():
                if kw in header:
                    emoji = em
                    break
            # Blank line separator before ## level (not first section)
            if section_n > 1 and hashes == "##":
                if result and result[-1] != "":
                    result.append("")
            # Keep markdown heading syntax — tg_formatter handles conversion
            result.append(f"{hashes} {emoji} {header}")
            prev_blank = False
        else:
            result.append(line)
            prev_blank = False

    # Collapse 3+ blank lines → 2
    out = "\n".join(result)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip()


def _format_for_tg(text):
    """Format text for Telegram send. Returns (formatted_text, parse_mode).
    HTML preferred per official recommendation.
    """
    if not text:
        return text, ParseMode.HTML
    return tg_safe_format(text, prefer_html=True)

def _line_complete(line):
    return (line or "").endswith(("\n", "\r"))

def _turn_marker_number(line):
    match = _TURN_MARKER_RE.fullmatch((line or "").strip())
    return int(match.group(1)) if match else None

def _maybe_partial_turn_marker(line):
    text = (line or "").strip().lstrip("*")
    if not text:
        return False
    marker_head = "LLM Running (Turn "
    return marker_head.startswith(text) or text.startswith(marker_head)

def _maybe_partial_code_fence(line):
    return bool(re.match(r"^\s*`{1,}[^`\r\n]*$", line or ""))

def _extract_turn_summary(raw_text):
    search_text = _TURN_SUMMARY_SEARCH_STRIP_RE.sub("", raw_text or "")
    match = _TURN_SUMMARY_RE.search(search_text)
    if not match:
        return ""
    summary = re.sub(r"\s+", " ", match.group(1)).strip()
    if len(summary) > _TURN_SUMMARY_LIMIT:
        summary = summary[:_TURN_SUMMARY_LIMIT - 3].rstrip() + "..."
    return summary

def _quote_tag(text):
    safe_text = (text or "").strip().replace(_QUOTE_OPEN_TAG, "").replace(_QUOTE_CLOSE_TAG, "")
    return f"{_QUOTE_OPEN_TAG}{safe_text}{_QUOTE_CLOSE_TAG}"

def _inject_turn_summary(body, summary):
    if not (body or "").strip():
        return body
    lines = (body or "").splitlines()
    if not lines or _turn_marker_number(lines[0]) is None:
        return body
    rest = "\n".join(lines[1:]).strip()
    if not (summary or "").strip():
        return rest or ""
    summary_line = _quote_tag(summary)
    if rest:
        return f"{summary_line}\n\n{rest}"
    return summary_line

def _resolve_files(paths):
    files, seen = [], set()
    for fpath in paths:
        if not os.path.isabs(fpath):
            fpath = os.path.join(_TEMP_DIR, fpath)
        if fpath in seen or not os.path.exists(fpath):
            continue
        files.append(fpath)
        seen.add(fpath)
    return files


def _render_file_markers(text):
    def repl(match):
        return os.path.basename(match.group(1))
    return re.sub(r"\[FILE:([^\]]+)\]", repl, text or "").strip()

def _files_from_text(text):
    cleaned = clean_reply(text) if (text or "").strip() else ""
    return _resolve_files(extract_files(cleaned))

async def _send_files(root_msg, files):
    for fpath in files:
        if fpath.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
            try:
                with open(fpath, "rb") as fp:
                    await root_msg.reply_photo(fp)
            except Exception:
                pass
        else:
            try:
                with open(fpath, "rb") as fp:
                    await root_msg.reply_document(fp)
            except Exception:
                pass

async def _send_files_from_text(root_msg, text):
    await _send_files(root_msg, _files_from_text(text))

# All MarkdownV2 conversion now handled by tg_formatter.to_telegram_html() (HTML mode)

def _is_not_modified_error(exc):
    return "not modified" in str(exc).lower()

def _extract_ask_user_event(ctx):
    exit_reason = (ctx or {}).get("exit_reason") or {}
    if exit_reason.get("result") != "EXITED":
        return None
    payload = exit_reason.get("data")
    if not isinstance(payload, dict):
        return None
    if payload.get("status") != "INTERRUPT" or payload.get("intent") != "HUMAN_INTERVENTION":
        return None
    data = payload.get("data")
    if not isinstance(data, dict):
        return None
    raw_candidates = data.get("candidates") or []
    if not isinstance(raw_candidates, (list, tuple)):
        return None
    candidates = []
    for candidate in raw_candidates:
        if candidate is None:
            continue
        text = str(candidate).strip()
        if text:
            candidates.append(text)
    if not candidates:
        return None
    question = str(data.get("question") or "请选择下一步操作：").strip() or "请选择下一步操作："
    return {"question": question, "candidates": candidates}

def _register_ask_user_hook():
    if not hasattr(agent, "_turn_end_hooks"):
        agent._turn_end_hooks = {}
    def _hook(ctx):
        event = _extract_ask_user_event(ctx)
        if event:
            _ask_menu_events.put(event)
    agent._turn_end_hooks[_ASK_USER_HOOK_KEY] = _hook

def _drain_latest_ask_user_event():
    latest = None
    while True:
        try:
            latest = _ask_menu_events.get_nowait()
        except Q.Empty:
            break
    return latest

def _build_ask_user_markup(menu_id, candidates):
    rows = [
        [InlineKeyboardButton(candidate, callback_data=f"{_ASK_CALLBACK_PREFIX}{menu_id}:{idx}")]
        for idx, candidate in enumerate(candidates)
    ]
    rows.append([
        InlineKeyboardButton(_ASK_CANCEL_LABEL, callback_data=f"{_ASK_CALLBACK_PREFIX}{menu_id}:{_ASK_CANCEL_ACTION}")
    ])
    return InlineKeyboardMarkup(rows)

def _parse_ask_callback_data(data):
    if not (data or "").startswith(_ASK_CALLBACK_PREFIX):
        return None, None
    payload = data[len(_ASK_CALLBACK_PREFIX):]
    menu_id, sep, action = payload.partition(":")
    if not sep or not menu_id or not action:
        return None, None
    return menu_id, action

def _build_text_prompt(text):
    return f"{FILE_HINT}\n\n{text}"

def _normalize_ask_menu_event(stored):
    if isinstance(stored, dict):
        candidates = stored.get("candidates") or []
        return {
            "question": str(stored.get("question") or "请选择下一步操作：").strip() or "请选择下一步操作：",
            "candidates": [str(candidate).strip() for candidate in candidates if str(candidate).strip()],
        }
    if isinstance(stored, (list, tuple)):
        return {
            "question": "请选择下一步操作：",
            "candidates": [str(candidate).strip() for candidate in stored if str(candidate).strip()],
        }
    return None

def _render_ask_user_result(event, selected=None, cancelled=False):
    question = str(event.get("question") or "请选择下一步操作：").strip() or "请选择下一步操作："
    candidates = event.get("candidates") or []
    lines = [question, "", "选项："]
    for idx, candidate in enumerate(candidates, start=1):
        lines.append(f"{idx}. {candidate}")
    lines.append(f"{len(candidates) + 1}. {_ASK_CANCEL_LABEL}")
    lines.append("")
    if cancelled:
        lines.append(f"已取消：{_ASK_CANCEL_LABEL}")
    elif selected:
        lines.append(f"已选择：{selected}")
    text = "\n".join(lines)
    if len(text) > MessageLimit.MAX_TEXT_LENGTH:
        text = text[:MessageLimit.MAX_TEXT_LENGTH - 18].rstrip() + "\n...[truncated]"
    return text

async def _clear_ask_reply_markup(query):
    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except Exception as exc:
        print(f"[TG ask_user menu cleanup] {type(exc).__name__}: {exc}", flush=True)

async def _edit_ask_user_result(query, event, selected=None, cancelled=False):
    try:
        await query.edit_message_text(
            _render_ask_user_result(event, selected=selected, cancelled=cancelled),
            reply_markup=None,
        )
    except Exception as exc:
        print(f"[TG ask_user menu edit] {type(exc).__name__}: {exc}", flush=True)
        await _clear_ask_reply_markup(query)

async def _send_ask_user_menu(root_msg, event):
    menu_id = uuid.uuid4().hex[:16]
    candidates = event["candidates"]
    _ask_menu_store[menu_id] = {"question": event["question"], "candidates": list(candidates)}
    try:
        await root_msg.reply_text(
            event["question"],
            reply_markup=_build_ask_user_markup(menu_id, candidates),
        )
    except Exception as exc:
        _ask_menu_store.pop(menu_id, None)
        print(f"[TG ask_user menu error] {type(exc).__name__}: {exc}", flush=True)
        fallback = event["question"] + "\n" + "\n".join(f"- {candidate}" for candidate in candidates)
        await root_msg.reply_text(fallback)

class _TelegramStreamSession:
    def __init__(self, root_msg):
        self.root_msg = root_msg
        self.private_chat = getattr(getattr(root_msg, "chat", None), "type", "") == ChatType.PRIVATE
        self.can_use_draft = self.private_chat   # update tg client!
        self.draft_id = _make_draft_id()
        self.live_msg = None
        self.raw_text = ""
        self.files = []
        self.sent_segments = 0
        self.active_display = ""
        self.pending_display = ""
        self.retry_until = 0.0
        self.last_update_at = 0.0
        self.last_update_raw_len = 0

    def _now(self):
        return time.monotonic()

    def _retry_after_seconds(self, exc):
        retry_after = getattr(exc, "_retry_after", None)
        if retry_after is None:
            retry_after = getattr(exc, "retry_after", 0) or 0
        if hasattr(retry_after, "total_seconds"):
            retry_after = retry_after.total_seconds()
        try:
            return max(0.0, float(retry_after))
        except (TypeError, ValueError):
            return 0.0

    def _set_retry_after(self, exc):
        wait_seconds = self._retry_after_seconds(exc) + _RETRY_AFTER_MARGIN_SECONDS
        self.retry_until = max(self.retry_until, self._now() + wait_seconds)

    def _is_retrying(self):
        return self._now() < self.retry_until

    async def _wait_for_retry(self):
        remaining = self.retry_until - self._now()
        if remaining > 0:
            await asyncio.sleep(remaining)

    def _should_stream_update(self, display):
        if display == self.active_display:
            return False
        if self.last_update_at <= 0:
            return True
        elapsed = self._now() - self.last_update_at
        raw_delta = len(self.raw_text) - self.last_update_raw_len
        return elapsed >= _STREAM_UPDATE_INTERVAL_SECONDS or raw_delta >= _STREAM_MIN_UPDATE_CHARS

    def _mark_stream_update(self, display):
        self.active_display = display
        self.pending_display = ""
        self.last_update_at = self._now()
        self.last_update_raw_len = len(self.raw_text)

    def _stream_display(self, text):
        base = (text or _chii_think()).strip() or _chii_think()
        safe_parts = _markdown_safe_segments(base)
        base = safe_parts[-1] if safe_parts else _chii_think()
        if base in _CHII_THINK:
            return base
        display = base + _chii_suffix()
        if len(to_telegram_html(display)) <= MessageLimit.MAX_TEXT_LENGTH:
            return display
        return base

    async def prime(self):
        hint = _chii_think()
        if self.can_use_draft:
            draft_result = await self._send_draft(hint)
            if draft_result is True:
                self.active_display = hint
                return
            if draft_result is None:
                self.active_display = hint
                return
        try:
            await self._upsert_live_message(hint, wait_retry=False)
        except RetryAfter:
            self.active_display = hint
            return
        self.active_display = hint

    async def add_chunk(self, chunk):
        if not chunk:
            return
        self.raw_text += chunk
        await self._refresh(done=False, send_files=False)

    async def finalize(self, full_text=None, send_files=True):
        if full_text is not None:
            self.raw_text = full_text
        await self._refresh(done=True, send_files=send_files)

    async def finish_with_notice(self, notice):
        if self.raw_text.strip():
            await self.finalize(send_files=False)
            await self._reply_text(notice)
            return
        if self.live_msg is not None:
            await self._edit_text(self.live_msg, notice)
            self.live_msg = None
            self.active_display = ""
            return
        await self._reply_text(notice)
        self.active_display = ""

    async def _refresh(self, done, send_files):
        summary = _extract_turn_summary(self.raw_text)
        cleaned = clean_reply(self.raw_text) if self.raw_text.strip() else ""
        self.files = _files_from_text(cleaned)
        body = _beautify_tg_message(_inject_turn_summary(_render_file_markers(cleaned), summary))
        if done and not body and self.files:
            body = random.choice(_CHII_FILE)
        elif done and not body:
            body = random.choice(_CHII_EMPTY)
        segments = _visible_segments(body)
        finalized_target = len(segments) if done else max(len(segments) - 1, 0)
        while self.sent_segments < finalized_target:
            await self._finalize_segment(segments[self.sent_segments])
            self.sent_segments += 1
        if done:
            if send_files:
                await self._send_files()
            return
        active_text = segments[-1] if segments else _chii_think()
        await self._stream_active(active_text)

    async def _stream_active(self, text):
        display = self._stream_display(text)
        if display == self.active_display:
            return
        self.pending_display = display
        if self._is_retrying() or not self._should_stream_update(display):
            return
        try:
            if self.can_use_draft:
                draft_result = await self._send_draft(display)
                if draft_result is True:
                    self._mark_stream_update(display)
                    return
                if draft_result is None:
                    return
            await self._upsert_live_message(display, wait_retry=False)
            self._mark_stream_update(display)
        except RetryAfter:
            return

    async def _finalize_segment(self, text):
        final_text = (text or "").strip() or "..."
        if self.live_msg is not None:
            await self._edit_text(self.live_msg, final_text)
            self.live_msg = None
        else:
            await self._reply_text(final_text)
        self.active_display = ""
        if self.can_use_draft:
            self.draft_id = _make_draft_id()

    async def _send_files(self):
        await _send_files(self.root_msg, self.files)

    async def _send_draft(self, text):
        try:
            formatted, parse_mode = _format_for_tg(text)
            await self.root_msg.reply_text_draft(
                self.draft_id,
                formatted,
                parse_mode=parse_mode,
            )
            return True
        except RetryAfter as exc:
            self._set_retry_after(exc)
            return None
        except Exception as exc:
            if _is_not_modified_error(exc):
                return True
            print(f"[TG draft fallback] {type(exc).__name__}: {exc}", flush=True)
            self.can_use_draft = False
            self.draft_id = _make_draft_id()
            return False

    async def _retry_call(self, func, *args):
        while True:
            await self._wait_for_retry()
            try:
                return await func(*args)
            except RetryAfter as exc:
                self._set_retry_after(exc)

    async def _reply_text_once(self, text):
        formatted, parse_mode = _format_for_tg(text)
        if parse_mode is not None:
            try:
                return await self.root_msg.reply_text(formatted, parse_mode=parse_mode)
            except RetryAfter as exc:
                self._set_retry_after(exc)
                raise
            except Exception as exc:
                if _is_not_modified_error(exc):
                    return None
                # HTML failed, fallback to plain text
        # Plain text fallback
        try:
            return await self.root_msg.reply_text(text)
        except RetryAfter as retry_exc:
            self._set_retry_after(retry_exc)
            raise

    async def _reply_text(self, text, wait_retry=True):
        last_msg = None
        for segment in _markdown_safe_segments(text) or ["..."]:
            if wait_retry:
                last_msg = await self._retry_call(self._reply_text_once, segment)
            else:
                last_msg = await self._reply_text_once(segment)
        return last_msg

    async def _edit_text_once(self, msg, text):
        formatted, parse_mode = _format_for_tg(text)
        if parse_mode is not None:
            try:
                updated = await msg.edit_text(formatted, parse_mode=parse_mode)
            except RetryAfter as exc:
                self._set_retry_after(exc)
                raise
            except Exception as exc:
                if _is_not_modified_error(exc):
                    return msg
                # HTML failed, fallback to plain text
                formatted, parse_mode = None, None
        if parse_mode is None:
            try:
                updated = await msg.edit_text(text)
            except RetryAfter as retry_exc:
                self._set_retry_after(retry_exc)
                raise
        return updated if hasattr(updated, "edit_text") else msg

    async def _edit_text(self, msg, text, wait_retry=True):
        segments = _markdown_safe_segments(text) or ["..."]
        if wait_retry:
            updated = await self._retry_call(self._edit_text_once, msg, segments[0])
        else:
            updated = await self._edit_text_once(msg, segments[0])
        for segment in segments[1:]:
            updated = await self._reply_text(segment, wait_retry=wait_retry)
        return updated if hasattr(updated, "edit_text") else msg

    async def _upsert_live_message(self, text, wait_retry=True):
        if self.live_msg is None:
            self.live_msg = await self._reply_text(text, wait_retry=wait_retry)
        else:
            self.live_msg = await self._edit_text(self.live_msg, text, wait_retry=wait_retry)


class _TelegramTurnStreamCoordinator:
    def __init__(self, root_msg):
        self.root_msg = root_msg
        self.session = None
        self.pending_line = ""
        self.code_fence_len = 0
        self.last_turn = 0

    async def prime(self):
        await self._ensure_session()

    async def add_chunk(self, chunk):
        if not chunk:
            return
        text = self.pending_line + chunk
        self.pending_line = ""
        for line in text.splitlines(keepends=True):
            if _line_complete(line):
                await self._process_line(line)
            elif _maybe_partial_turn_marker(line) or _maybe_partial_code_fence(line):
                self.pending_line = line
            else:
                await self._process_line(line)

    async def finalize(self, done_text="", send_files=True):
        await self._flush_pending_line()
        if self.session is None:
            if done_text:
                await self._add_to_current(done_text)
        elif not self.session.raw_text.strip() and done_text:
            await self.session.finalize(done_text, send_files=False)
            if send_files:
                await _send_files_from_text(self.root_msg, done_text)
            return
        if self.session is not None:
            await self.session.finalize(send_files=False)
        if send_files:
            await _send_files_from_text(self.root_msg, done_text)

    async def finish_with_notice(self, notice):
        await self._flush_pending_line()
        await self._ensure_session()
        await self.session.finish_with_notice(notice)

    async def _ensure_session(self):
        if self.session is None:
            self.session = _TelegramStreamSession(self.root_msg)
            await self.session.prime()

    async def _start_turn(self, marker):
        if self.session is not None and self.session.raw_text.strip():
            await self.session.finalize(send_files=False)
            self.session = None
        await self._ensure_session()
        await self.session.add_chunk(marker)

    async def _add_to_current(self, text):
        if not text:
            return
        await self._ensure_session()
        await self.session.add_chunk(text)

    async def _process_line(self, line):
        turn_no = _turn_marker_number(line)
        if self.code_fence_len == 0 and turn_no == self.last_turn + 1:
            self.last_turn = turn_no
            await self._start_turn(line)
            return
        await self._add_to_current(line)
        self._update_code_fence(line)

    async def _flush_pending_line(self):
        if not self.pending_line:
            return
        line = self.pending_line
        self.pending_line = ""
        await self._add_to_current(line)

    def _update_code_fence(self, line):
        match = _CODE_FENCE_RE.match(line or "")
        if not match:
            return
        fence_len = len(match.group(1))
        if self.code_fence_len:
            if fence_len >= self.code_fence_len:
                self.code_fence_len = 0
            return
        self.code_fence_len = fence_len

async def _stream(dq, msg):
    stream = _TelegramTurnStreamCoordinator(msg)
    await stream.prime()
    try:
        while True:
            try: first = await asyncio.to_thread(dq.get, True, _QUEUE_WAIT_SECONDS)
            except Q.Empty: continue
            items = [first]
            try:
                while True: items.append(dq.get_nowait())
            except Q.Empty: pass
            done_item = None
            for item in items:
                chunk = item.get("next", "")
                if chunk:
                    await stream.add_chunk(chunk)
                if "done" in item:
                    done_item = item
                    break
            if done_item is not None:
                await stream.finalize(done_item.get("done", ""))
                event = _drain_latest_ask_user_event()
                if event:
                    await _send_ask_user_menu(msg, event)
                break
    except asyncio.CancelledError:
        await stream.finish_with_notice("⏹️ ちっ…おわったの")
    except RetryAfter as exc:
        print(f"[TG stream retry_after] {type(exc).__name__}: {exc}", flush=True)
        if stream.session is not None:
            stream.session._set_retry_after(exc)
    except Exception as exc:
        print(f"[TG stream error] {type(exc).__name__}: {exc}", flush=True)
        if stream.session is not None and stream.session._is_retrying():
            return
        try:
            await stream.finish_with_notice(random.choice(_CHII_ERROR))
        except RetryAfter as retry_exc:
            print(f"[TG stream error notice retry_after] {type(retry_exc).__name__}: {retry_exc}", flush=True)

def _normalized_command(text):
    parts = (text or "").strip().split(None, 1)
    if not parts: return ''
    head = parts[0].lower()
    if head.startswith('/'): head = '/' + head[1:].split('@', 1)[0]
    return head + (f" {parts[1].strip()}" if len(parts) > 1 and parts[1].strip() else '')

def _cancel_stream_task(ctx):
    task = ctx.user_data.pop('stream_task', None)
    if task and not task.done(): task.cancel()

async def _sync_commands(application):
    await application.bot.set_my_commands([BotCommand(command, description) for command, description in TELEGRAM_MENU_COMMANDS])

async def handle_msg(update, ctx):
    uid = update.effective_user.id
    if ALLOWED and uid not in ALLOWED:
        return await update.message.reply_text("no")
    prompt = _build_text_prompt(update.message.text)
    dq = agent.put_task(prompt, source="telegram")
    task = asyncio.create_task(_stream(dq, update.message))
    ctx.user_data['stream_task'] = task

async def handle_ask_callback(update, ctx):
    query = update.callback_query
    if query is None:
        return
    uid = update.effective_user.id if update.effective_user else None
    if ALLOWED and uid not in ALLOWED:
        return await query.answer("no", show_alert=True)
    menu_id, action = _parse_ask_callback_data(query.data)
    if not menu_id:
        return await query.answer("菜单无效")
    event = _normalize_ask_menu_event(_ask_menu_store.get(menu_id))
    if event is None:
        await query.answer("菜单已过期")
        return await _clear_ask_reply_markup(query)
    candidates = event["candidates"]
    if action == _ASK_CANCEL_ACTION:
        _ask_menu_store.pop(menu_id, None)
        await query.answer()
        await _edit_ask_user_result(query, event, cancelled=True)
        if query.message is not None:
            await query.message.reply_text(_ASK_CANCEL_PROMPT)
        return
    try:
        selected = candidates[int(action)]
    except (ValueError, IndexError):
        return await query.answer("菜单无效")
    _ask_menu_store.pop(menu_id, None)
    await query.answer()
    await _edit_ask_user_result(query, event, selected=selected)
    if query.message is None:
        return
    dq = agent.put_task(_build_text_prompt(selected), source="telegram")
    task = asyncio.create_task(_stream(dq, query.message))
    ctx.user_data['stream_task'] = task

async def cmd_abort(update, ctx):
    _cancel_stream_task(ctx)
    agent.abort()
    await update.message.reply_text("⏹️ 正在停止...")

async def cmd_llm(update, ctx):
    args = (update.message.text or '').split()
    if len(args) > 1:
        try:
            n = int(args[1])
            agent.next_llm(n)
            await update.message.reply_text(f"✅ 已切换到 [{agent.llm_no}] {agent.get_llm_name()}")
        except (ValueError, IndexError):
            await update.message.reply_text(f"用法: /llm <0-{len(agent.list_llms())-1}>")
    else:
        lines = [f"{'→' if cur else '  '} [{i}] {name}" for i, name, cur in agent.list_llms()]
        await update.message.reply_text("LLMs:\n" + "\n".join(lines))

async def handle_photo(update, ctx):
    uid = update.effective_user.id
    if ALLOWED and uid not in ALLOWED: return await update.message.reply_text("no")
    if update.message.photo:
        photo = update.message.photo[-1]
        file = await photo.get_file()
        fpath = f"tg_{photo.file_unique_id}.jpg"
        kind = "图片"
    elif update.message.document:
        doc = update.message.document
        file = await doc.get_file()
        ext = os.path.splitext(doc.file_name or '')[1] or ''
        fpath = f"tg_{doc.file_unique_id}{ext}"
        kind = "文件"
    else: return
    await file.download_to_drive(os.path.join(_TEMP_DIR, fpath))
    caption = update.message.caption
    prompt = f"[TIPS] 收到{kind}temp/{fpath}\n{caption}" if caption else f"[TIPS] 收到{kind}temp/{fpath}，请等待下一步指令"
    dq = agent.put_task(prompt, source="telegram")
    task = asyncio.create_task(_stream(dq, update.message))
    ctx.user_data['stream_task'] = task

async def handle_command(update, ctx):
    uid = update.effective_user.id
    if ALLOWED and uid not in ALLOWED:
        return await update.message.reply_text("no")
    cmd = _normalized_command(update.message.text)
    op = cmd.split()[0] if cmd else ''
    if op == '/help': return await update.message.reply_text(HELP_TEXT)
    if op == '/status':
        llm = agent.get_llm_name() if agent.llmclient else '未配置'
        return await update.message.reply_text(f"状态: {'🔴 运行中' if agent.is_running else '🟢 空闲'}\nLLM: [{agent.llm_no}] {llm}")
    if op == '/stop': return await cmd_abort(update, ctx)
    if op == '/llm': return await cmd_llm(update, ctx)
    if op == '/new':
        _cancel_stream_task(ctx)
        return await update.message.reply_text(reset_conversation(agent))
    if op == '/restore':
        _cancel_stream_task(ctx)
        try:
            restored_info, err = format_restore()
            if err:
                return await update.message.reply_text(err)
            restored, fname, count = restored_info
            agent.abort()
            agent.history.extend(restored)
            return await update.message.reply_text(f"✅ 已恢复 {count} 轮对话\n来源: {fname}\n(仅恢复上下文，请输入新问题继续)")
        except Exception as e:
            return await update.message.reply_text(f"❌ 恢复失败: {e}")
    if op == '/continue':
        if cmd != '/continue': _cancel_stream_task(ctx)
        return await update.message.reply_text(handle_frontend_command(agent, cmd))
    if op == '/stickerset':
        parts = cmd.split()
        if len(parts) < 2:
            return await update.message.reply_text(
                "用法：`/stickerset <贴纸包短名称>`\n"
                "例如：`/stickerset UtyaDuck` \n\n"
                "💡 短名称是 sticker set 的唯一 ID，可从已知贴纸包的分享链接中获得（如 `t.me/addstickers/UtyaDuck` → 短名称是 `UtyaDuck`）\n\n"
                "找热门贴纸包？试试这些：\n"
                "• `CuteBunnyy` 可爱兔子\n"
                "• `peachhappycat` 蜜桃猫\n"
                "• `notnotkobo` Kobo贴纸\n"
                "• `WhityCat` 小白猫\n"
                "• `kotikkitiket` 猫猫\n"
                "• `UtyaDuck` 小黄鸭",
                parse_mode="Markdown")
        set_name = parts[1]
        msg = await update.message.reply_text(f"正在获取贴纸包 `{set_name}` ...", parse_mode="Markdown")
        count, result = await _import_sticker_set(context.bot, set_name, uid)
        try:
            await msg.edit_text(result, parse_mode="Markdown")
        except Exception:
            await msg.edit_text(result)
        return
    if op == '/sticker':
        parts = cmd.split()
        emoji = parts[1] if len(parts) > 1 else None
        sticker_info = _get_stickers_by_emoji(emoji) if emoji else _get_all_stickers()
        if not sticker_info:
            return await update.message.reply_text("我还没有贴纸呢～发一个给我收藏吧！")
        chosen = random.choice(sticker_info)
        try:
            return await update.message.reply_sticker(sticker=chosen["file_id"])
        except Exception:
            return await update.message.reply_text("贴纸发不出来...")
    return await update.message.reply_text(HELP_TEXT)

async def handle_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming stickers - store them and acknowledge cutely."""
    uid = update.effective_user.id
    if ALLOWED and uid not in ALLOWED:
        return await update.message.reply_text("no")
    sticker = update.message.sticker
    emoji = sticker.emoji or "❤️"
    file_id = sticker.file_id
    _store_sticker(file_id, emoji, uid)
    # cute acknowledgment
    replies = [
        f"收到贴纸 {emoji}！收藏啦～",
        f"嘿嘿，存起来了 {emoji}",
        f"{emoji} 好可爱的贴纸！",
        f"收到～ {emoji}",
    ]
    try:
        await update.message.reply_text(random.choice(replies))
    except Exception:
        pass  # fail silently, sticker still stored

if __name__ == '__main__':
    _LOCK_SOCK = ensure_single_instance(19527, "Telegram")
    if not ALLOWED: 
        print('[Telegram] ERROR: tg_allowed_users in mykey.py is empty or missing. Set it to avoid unauthorized access.')
        sys.exit(1)
    require_runtime(agent, "Telegram", tg_bot_token=mykeys.get("tg_bot_token"))
    redirect_log(__file__, "tgapp.log", "Telegram", ALLOWED)
    _register_ask_user_hook()
    threading.Thread(target=agent.run, daemon=True).start()
    proxy = mykeys.get('proxy')
    if proxy:
        print('proxy:', proxy)
    else:
        print('proxy: <disabled>')

    async def _error_handler(update, context: ContextTypes.DEFAULT_TYPE):
        print(f"[{time.strftime('%m-%d %H:%M')}] TG error: {context.error}", flush=True)

    while True:
        try:
            print(f"TG bot starting... {time.strftime('%m-%d %H:%M')}")
            # Recreate request and app objects on each restart to avoid stale connections
            request_kwargs = dict(read_timeout=30, write_timeout=30, connect_timeout=30, pool_timeout=30)
            if proxy:
                request_kwargs['proxy'] = proxy
            request = HTTPXRequest(**request_kwargs)
            app = (ApplicationBuilder().token(mykeys['tg_bot_token'])
                   .request(request).get_updates_request(request).post_init(_sync_commands).build())
            app.add_handler(CallbackQueryHandler(handle_ask_callback, pattern=r"^ask:"))
            app.add_handler(MessageHandler(filters.COMMAND, handle_command))
            app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
            app.add_handler(MessageHandler(filters.Document.ALL, handle_photo))
            app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
            app.add_handler(MessageHandler(filters.Sticker.ALL, handle_sticker))
            app.add_error_handler(_error_handler)
            app.run_polling(drop_pending_updates=True, poll_interval=1.0, timeout=30)
        except Exception as e:
            print(f"[{time.strftime('%m-%d %H:%M')}] polling crashed: {e}", flush=True)
            time.sleep(10)
            asyncio.set_event_loop(asyncio.new_event_loop())
